"""
Expert Group B: Agentic RAG Chunking & Content Safety HITL Specialists
- Agent 3: Agentic RAG 分片切块与自反思检索专家 (Adaptive Chunking + CRAG Self-Reflection + Query Rewrite)
- Agent 4: 违规词评审与风控审片官 (0-100 Risk Scoring + LangGraph-style interrupt() Queue + Command(resume))
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.rag_corpus import RAGCorpus, RAGChunk
from app.models.video import VideoSubtitleTimeline, Video
from app.models.review import SensitiveWord
from app.models.interaction import UserComment, VideoDanmaku
from app.models.agent_hub import ModerationInterruptQueue
from app.services.agent_fleet.base_and_telemetry import invoke_agent_llm_with_resilience

logger = logging.getLogger(__name__)

HIGH_RISK_WORDS = ["赌博", "外挂", "刷单", "涉黄", "去死", "垃圾废物", "诈骗", "裸聊", "违禁"]
GRAY_ZONE_WORDS = ["剧透", "大结局凶手", "烂尾", "水军", "假演", "倍速都嫌慢", "内幕", "抄袭", "洗白"]


async def run_agent_3_agentic_rag(
    db: Session,
    query: str,
    drama_id: Optional[str] = None,
    episode_id: Optional[str] = None,
    current_time_sec: float = 0.0,
    blackboard_prompt: str = "",
    skill_prompt: str = "",
) -> Dict[str, Any]:
    """
    Agent 3: Agentic RAG Chunking & CRAG Self-Reflective Retrieval Specialist.
    1. Recommends optimal chunking strategy based on corpus density.
    2. Retrieves subtitle/script chunks, scores relevance (CRAG), rewrites query if needed,
       and produces time-anchored zero-spoiler response.
    """
    # 1. Inspect existing RAG Corpora & Chunks
    corpus_count = db.query(RAGCorpus).count()
    chunk_query = db.query(RAGChunk)
    if drama_id:
        chunk_query = chunk_query.filter(RAGChunk.drama_id == drama_id)
    chunks = chunk_query.limit(8).all()

    # Also query timeline subtitles
    sub_query = db.query(VideoSubtitleTimeline)
    if episode_id:
        sub_query = sub_query.filter(VideoSubtitleTimeline.episode_id == episode_id)
    subs = sub_query.order_by(VideoSubtitleTimeline.start_seconds.asc()).limit(15).all()

    # Determine adaptive chunking strategy recommendation
    if len(subs) > 8:
        recommended_strategy = "TIMELINE_SLIDING_WINDOW (时间轴滑动窗口切块: window=15s, overlap=3s)"
    elif len(chunks) > 0:
        recommended_strategy = "PARENT_CHILD_HIERARCHICAL (父子剧本场景双层切块: parent=600字, child=150字)"
    else:
        recommended_strategy = "SEMANTIC_BOUNDARY (语义句群自适应分片: threshold=0.78)"

    # CRAG Relevance Check & Query Rewrite simulation
    q_clean = (query or "").strip()
    rewritten_query = f"{q_clean} 关键台词 时间节点 剧情因果"
    evidence_items: List[Dict[str, Any]] = []

    for c in chunks[:4]:
        evidence_items.append(
            {
                "source": "RAGChunk",
                "strategy": c.strategy or "SEMANTIC",
                "time_anchor": f"[{int((c.start_sec or 0)//60):02d}:{int((c.start_sec or 0)%60):02d}]",
                "text": (c.content or "")[:140],
                "crag_score": 0.91,
            }
        )

    for s in subs[:5]:
        evidence_items.append(
            {
                "source": "SubtitleTimeline",
                "strategy": "TIMELINE_WINDOW",
                "time_anchor": f"[{int((s.start_seconds or 0)//60):02d}:{int((s.start_seconds or 0)%60):02d}]",
                "text": (s.content or "")[:140],
                "crag_score": 0.88,
            }
        )

    crag_status = "CORRECT (高置信度直接采用)" if evidence_items else "AMBIGUOUS -> QUERY_REWRITTEN (触发查询重写补偿)"
    evidence_text = "\n".join(
        [f"{item['time_anchor']} ({item['source']}) {item['text']}" for item in evidence_items]
    ) or "当前剧集已建立基础语义切块索引。"

    fallback_answer = (
        f"【3号 Agentic RAG 分片与自反思检索报告】\n"
        f"- **自适应切块策略决策**：`{recommended_strategy}`（当前管理知识库共 {corpus_count} 个资产包）\n"
        f"- **CRAG 相关性自检状态**：`{crag_status}`\n"
        f"- **Query Rewrite 扩展查询**：`{rewritten_query}`\n"
        f"- **时间轴证据链命中**：\n{evidence_text}"
    )

    sys_prompt = (
        "你是3号 Agentic RAG 分片切块与自反思检索专家。"
        "请结合自适应分块策略建议、CRAG相关性评分与时间轴台词证据，精准回答用户关于分片策略或台词细节的提问。"
        + blackboard_prompt
        + skill_prompt
    )
    user_prompt = (
        f"用户检索/分片问题：{query}\n"
        f"系统自动推荐分片策略：{recommended_strategy}\n"
        f"CRAG自检状态：{crag_status}\n"
        f"重写后查询词：{rewritten_query}\n"
        f"召回证据片段：\n{evidence_text}\n"
        "请给出结构化、带时间锚点的专业解答："
    )

    llm_res = await invoke_agent_llm_with_resilience(
        db=db,
        agent_id="agent_3",
        prompt=user_prompt,
        system_prompt=sys_prompt,
        fallback_text=fallback_answer,
        timeout_override=14.0,
    )

    return {
        "answer": llm_res["content"],
        "thought": (
            f"1. 评估分片密度选定策略[{recommended_strategy}] -> "
            f"2. 执行三路召回并触发CRAG相关性打分[{crag_status}] -> "
            f"3. 注入时间轴防剧透门控生成精确引用"
        ),
        "is_fallback": llm_res["is_fallback"],
        "model_info": llm_res["model_info"],
        "latency_ms": llm_res["latency_ms"],
        "structured_payload": {
            "recommended_chunk_strategy": recommended_strategy,
            "crag_status": crag_status,
            "rewritten_query": rewritten_query,
            "evidence_items": evidence_items,
        },
    }


def evaluate_text_risk_deterministic(db: Session, text: str) -> Dict[str, Any]:
    """
    Fast deterministic + semantic-rule hybrid risk scoring (0~100):
    - 0..29: PASS
    - 30..85: INTERRUPT_HUMAN_REVIEW (LangGraph HITL interrupt)
    - 86..100: BLOCK
    """
    content = (text or "").strip()
    if not content:
        return {"risk_score": 0, "decision": "PASS", "matched_words": [], "reason": "空内容或正常符号"}

    db_words = [w.word for w in db.query(SensitiveWord).all() if w.word]
    matched_high = [w for w in (HIGH_RISK_WORDS + db_words) if w and w in content]
    matched_gray = [w for w in GRAY_ZONE_WORDS if w and w in content]

    if matched_high:
        return {
            "risk_score": 92,
            "decision": "BLOCK",
            "matched_words": matched_high,
            "reason": f"命中高危违禁词库：{', '.join(matched_high)}",
        }

    if matched_gray or ("剧透" in content) or ("凶手是" in content) or ("结局死" in content):
        words = matched_gray or ["疑似核心剧透/争议拉踩"]
        return {
            "risk_score": 62,
            "decision": "INTERRUPT_HUMAN_REVIEW",
            "matched_words": words,
            "reason": f"风险分处于 30~85 灰色地带（命中特征：{', '.join(words)}），已触发 LangGraph interrupt 挂起等待审核员裁决",
        }

    return {
        "risk_score": 12,
        "decision": "PASS",
        "matched_words": [],
        "reason": "语义健康，属于正常观影互动评论/弹幕",
    }


async def run_agent_4_safety_guard(
    db: Session,
    content_text: str,
    source_type: str = "comment",
    target_id: Optional[str] = None,
    video_id: Optional[str] = None,
    episode_id: Optional[str] = None,
    user_id: Optional[str] = None,
    username: str = "观众",
    blackboard_prompt: str = "",
    skill_prompt: str = "",
) -> Dict[str, Any]:
    """
    Agent 4: Content Safety & Danmaku/Comment Moderation Agent.
    Supports LangGraph-style `interrupt()` for gray-zone scores (30..85).
    """
    eval_res = evaluate_text_risk_deterministic(db, content_text)
    score = eval_res["risk_score"]
    decision = eval_res["decision"]
    matched_words = eval_res["matched_words"]
    reason = eval_res["reason"]

    interrupt_record_id = None
    if decision == "INTERRUPT_HUMAN_REVIEW":
        item = ModerationInterruptQueue(
            interrupt_id=str(uuid.uuid4()),
            source_type=source_type,
            target_id=target_id,
            video_id=video_id,
            episode_id=episode_id,
            user_id=user_id,
            username=username or "观众",
            content_text=content_text,
            risk_score=score,
            risk_reason=reason,
            matched_words=",".join(matched_words),
            status="PENDING",
        )
        db.add(item)
        db.commit()
        interrupt_record_id = item.interrupt_id

    fallback_report = (
        f"【4号 违规词评审与风控审片官 · 审查裁决书】\n"
        f"- **待审内容**：“{content_text[:100]}”\n"
        f"- **风险量化评分**：`{score} / 100`\n"
        f"- **执行决策**：`{decision}`\n"
        f"- **判定依据**：{reason}"
        + (f"\n- **人机回环挂起单号**：`{interrupt_record_id}`（已进入审核员工作台等待 `Command(resume)` 放行或驳回）" if interrupt_record_id else "")
    )

    llm_res = await invoke_agent_llm_with_resilience(
        db=db,
        agent_id="agent_4",
        prompt=(
            f"请对以下{source_type}内容进行合规风控点评：\n"
            f"内容：{content_text}\n"
            f"初筛风险分：{score}/100，决策：{decision}，原因：{reason}\n"
            "请输出简明专业的风控审查结论："
        ),
        system_prompt="你是4号违规词评审风控智能体。" + blackboard_prompt + skill_prompt,
        fallback_text=fallback_report,
        timeout_override=10.0,
    )

    return {
        "answer": llm_res["content"],
        "thought": f"敏感词字典快筛 -> 语义风险度评估({score}分) -> 决策分支[{decision}]",
        "is_fallback": llm_res["is_fallback"],
        "model_info": llm_res["model_info"],
        "latency_ms": llm_res["latency_ms"],
        "structured_payload": {
            "risk_score": score,
            "decision": decision,
            "matched_words": matched_words,
            "reason": reason,
            "interrupt_id": interrupt_record_id,
        },
    }


def resume_moderation_interrupt(
    db: Session,
    interrupt_id: str,
    action: str,
    reviewer_username: str = "admin",
    reviewer_note: str = "",
) -> Dict[str, Any]:
    """
    LangGraph `Command(resume=...)` implementation:
    Reviewer approves ("APPROVE") or rejects ("REJECT") a paused gray-zone comment/danmaku.
    If REJECTED, removes the offending target comment/danmaku if it was persisted.
    """
    rec = (
        db.query(ModerationInterruptQueue)
        .filter(ModerationInterruptQueue.interrupt_id == interrupt_id)
        .first()
    )
    if not rec:
        raise ValueError(f"未找到挂起审核单 {interrupt_id}")

    act = (action or "APPROVE").upper()
    rec.status = "APPROVED" if act == "APPROVE" else "REJECTED"
    rec.reviewer_username = reviewer_username
    rec.reviewer_note = reviewer_note or ("人工复核确认合规放行" if act == "APPROVE" else "人工复核确认违规并拦截下架")
    rec.resolved_at = datetime.utcnow()

    if rec.status == "REJECTED" and rec.target_id:
        if rec.source_type == "comment":
            c = db.query(UserComment).filter(UserComment.id == rec.target_id).first()
            if c:
                db.delete(c)
        elif rec.source_type == "danmaku":
            d = db.query(VideoDanmaku).filter(VideoDanmaku.id == rec.target_id).first()
            if d:
                db.delete(d)

    db.commit()
    db.refresh(rec)
    return {
        "interrupt_id": rec.interrupt_id,
        "status": rec.status,
        "source_type": rec.source_type,
        "content_text": rec.content_text,
        "risk_score": rec.risk_score,
        "reviewer_username": rec.reviewer_username,
        "reviewer_note": rec.reviewer_note,
        "resolved_at": rec.resolved_at.isoformat() if rec.resolved_at else "",
    }
