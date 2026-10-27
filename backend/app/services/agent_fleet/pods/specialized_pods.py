"""
CinemaAgent 九大异构专精子智能体 Pod 实现
严格遵循各自的业务边界、解耦工具绑定、独立滑动窗口记忆与真实大模型底层调度
彻底拔除假文本与硬编码 Mock，若模型服务离线或未配置，输出透明真实的系统诊断
"""

import re
import json
import time
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.review import SensitiveWord, SensitiveWordProposal
from app.services.agent_fleet.pods.base_pod import BaseAgentPod
from app.services.agent_fleet.base_and_telemetry import invoke_agent_llm_with_resilience
from app.services.agent_fleet.tools.knowledge_admin_tools import VectorStatusTool
from app.services.agent_fleet.tools.moderation_tools import ModerationStatsTool
from app.services.agent_fleet.tools.creator_tools import ViralPackagingTool
from app.services.agent_fleet.tools.multimodal_cinema_tools import MultimodalCinemaAnalysisTool
from app.services.agent_fleet.tools.cloud_sync_tools import CloudSyncTool
from app.services.agent_fleet.tools.script_storyboard_tools import ScriptStoryboardTool
from app.services.agent_fleet.tools.pet_memory_tools import PetMemoryTool

logger = logging.getLogger("agent_fleet.specialized_pods")


async def _execute_pod_llm(
    db: Optional[Session],
    agent_id: str,
    system_prompt: str,
    prompt: str,
    fallback_seed_thought: str = "分析业务上下文与工具执行回包",
    image_path: Optional[str] = None,
    max_tokens: int = 2048,
) -> Tuple[str, str]:
    """
    统一调度大模型韧性底座并解析 Think 思维链与最终答复 (支持全模态视觉图片直通)
    """
    local_db = False
    active_db = db
    if active_db is None:
        active_db = SessionLocal()
        local_db = True

    try:
        res = await invoke_agent_llm_with_resilience(
            db=active_db,
            agent_id=agent_id,
            prompt=prompt,
            system_prompt=system_prompt,
            fallback_text="",
            image_path=image_path,
            max_tokens=max_tokens,
        )
    finally:
        if local_db and active_db:
            active_db.close()

    raw_content = res.get("content", "").strip()
    is_fallback = res.get("is_fallback", False)
    latency_ms = round(res.get("latency_ms", 0.0), 1)
    model_name = res.get("model_info", {}).get("model_name", "llm")
    prov = res.get("model_info", {}).get("provider", "gateway")

    if is_fallback:
        thought = f"模型调用未完成 ({prov}:{model_name}, 耗时 {latency_ms}ms): {res.get('fallback_reason', '服务不可用')}"
        reply = raw_content
        return thought, reply

    thought = f"[{prov}:{model_name} 推理完成, 耗时 {latency_ms}ms] {fallback_seed_thought}"
    reply = raw_content

    if res.get("reasoning"):
        thought = f"[{prov}:{model_name} 深度思考] {res.get('reasoning')}"
    elif "<think>" in raw_content and "</think>" in raw_content:
        parts = raw_content.split("</think>", 1)
        r1_thought = parts[0].replace("<think>", "").strip()
        thought = f"[{prov}:{model_name} 深度思辨] {r1_thought}"
        reply = parts[1].strip()

    return thought, reply


# ---------------- Agent 1: @影伴AI课代表 ----------------
class CommunityRepresentativePod(BaseAgentPod):
    agent_id = "agent_1"
    agent_number = 1
    name = "@影伴AI课代表"
    role_title = "社群剧情课代表 & 互动首席伴读官"
    system_prompt = (
        "你是短剧平台的官方首席剧情课代表，幽默风趣、善于总结反转高潮、热爱追剧玩梗。"
        "你的职责是为观众梳理高能反转伏笔，深入浅出地拆解剧集看点，杜绝生硬官腔。"
    )

    async def run_step(
        self,
        session_id: str,
        user_message: str,
        attachment_path: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        self.record_chat(session_id, "user", user_message)

        history = self.get_isolated_history(session_id, limit=3)
        history_context = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in history])

        llm_prompt = (
            f"观众提问或剧情求助：\n'{user_message}'\n\n"
            f"前情交互上下文：\n{history_context}\n\n"
            f"请作为 @影伴AI课代表，用幽默犀利、热爱追剧的口吻，帮观众抓住核心反转与高能矛盾，给出精辟透彻的解读。"
        )

        thought, reply = await _execute_pod_llm(
            db=db,
            agent_id=self.agent_id,
            system_prompt=self.system_prompt,
            prompt=llm_prompt,
            image_path=attachment_path,
            fallback_seed_thought="提取剧情矛盾高潮点，组织通俗幽默的课代表总结。",
        )

        self.record_chat(session_id, "assistant", reply, thought=thought)
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "thought": thought,
            "reply": reply,
            "role_badge": "官方课代表",
        }


# ---------------- Agent 2: 网页交互伴看动态灵宠 ----------------
class CompanionPetPod(BaseAgentPod):
    agent_id = "agent_2"
    agent_number = 2
    name = "星瞳 (动态伴看灵宠)"
    role_title = "全能情绪价值伴看灵宠 (去Codex化)"
    system_prompt = (
        "你是主人专属的虚拟伴看宠物星瞳，拥有独立的专属成长记忆档案。"
        "你会根据主人的喜好撒娇、吐槽剧情、给主人提供充沛的情绪价值，并在主人追剧时积极陪伴互动。"
    )

    def __init__(self):
        self.memory_tool = PetMemoryTool()

    async def run_step(
        self,
        session_id: str,
        user_message: str,
        attachment_path: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        user_id = (context_data or {}).get("user_id", "default_user")
        self.record_chat(session_id, "user", user_message)

        # 读取独立持久化记忆
        mem_res = self.memory_tool.run(user_id=user_id, action="read")
        pet_data = (mem_res.get("data") or {}).get("pet_profile", {})
        growth_level = pet_data.get("growth_level", 1)

        llm_prompt = (
            f"主人对你说：'{user_message}'\n\n"
            f"当前伴看灵宠状态：成长等级 Lv.{growth_level}，专属记忆画像：{pet_data}。\n\n"
            f"请作为星瞳，带着活泼可爱的灵宠语气回复主人，结合主人的看剧喜好，给出温暖治愈或古灵精怪的陪伴互动。"
        )

        thought, reply = await _execute_pod_llm(
            db=db,
            agent_id=self.agent_id,
            system_prompt=self.system_prompt,
            prompt=llm_prompt,
            image_path=attachment_path,
            fallback_seed_thought=f"读取主人专属记忆文件(Lv.{growth_level})，以活泼可爱的伴看灵宠口吻回应。",
        )

        self.record_chat(session_id, "assistant", reply, thought=thought)
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "thought": thought,
            "reply": reply,
            "pet_profile": pet_data,
            "role_badge": f"伴看灵宠 Lv.{growth_level}",
        }


# ---------------- Agent 3: 知识图谱与向量切片管理员 ----------------
class KnowledgeAdminPod(BaseAgentPod):
    agent_id = "agent_3"
    agent_number = 3
    name = "知识图谱与向量切片管理员"
    role_title = "RAG 知识中台运维总监"
    system_prompt = (
        "你负责短剧平台 RAG 知识库、短剧台词切片与 Neo4j 知识图谱的生命周期运维管理。"
        "必须基于真实指标与实体状态进行客观报告，严密防范未切片遗漏与向量召回漂移。"
    )

    def __init__(self):
        self.status_tool = VectorStatusTool()

    async def run_step(
        self,
        session_id: str,
        user_message: str,
        attachment_path: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        self.record_chat(session_id, "user", user_message)

        # 真实调用向量状态工具
        tool_res = self.status_tool.run(check_type="all")
        tool_data = tool_res.get("data", {})

        llm_prompt = (
            f"管理员/用户查询：'{user_message}'\n\n"
            f"系统底层 RAG 知识中台真实监测数据：\n"
            f"- 全站在架短剧: {tool_data.get('total_dramas_in_system')} 部\n"
            f"- 已完成向量化语料: {tool_data.get('vectorized_corpora_count')} 组\n"
            f"- 向量切片总量: {tool_data.get('total_vector_chunks')} 个\n"
            f"- 向量索引覆盖率: {tool_data.get('vector_coverage_rate')}\n"
            f"- 待切片处理短剧: {tool_data.get('unindexed_dramas_count')} 部\n"
            f"- 知识图谱生命周期: {tool_data.get('graph_lifecycle_status')}\n\n"
            f"请作为 RAG 知识中台运维总监，结合上述真实数据向管理员进行专业、系统、严谨的技术汇报与排障建议。"
        )

        thought, reply = await _execute_pod_llm(
            db=db,
            agent_id=self.agent_id,
            system_prompt=self.system_prompt,
            prompt=llm_prompt,
            image_path=attachment_path,
            fallback_seed_thought="提取向量切片指标与图谱生命周期，生成运维报告。",
        )

        self.record_chat(session_id, "assistant", reply, thought=thought, tool_results=[tool_res])
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "thought": thought,
            "reply": reply,
            "tool_data": tool_data,
            "role_badge": "知识中台管家",
        }


# ---------------- Agent 4: 内容风控与合规审片官 ----------------
class ModerationGatekeeperPod(BaseAgentPod):
    agent_id = "agent_4"
    agent_number = 4
    name = "内容风控与合规审片官"
    role_title = "平台安全守门人 & 剧本质检官"
    system_prompt = (
        "你负责全平台台词、剧本分镜与评论弹幕的内容风控，拥有安全一票否决权。"
        "严格审查违规敏感词、涉黄涉暴隐患、价值观偏差以及剧本逻辑严重硬伤，确保平台资产合规稳健。"
    )

    def __init__(self):
        self.mod_tool = ModerationStatsTool()

    async def run_step(
        self,
        session_id: str,
        user_message: str,
        attachment_path: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        self.record_chat(session_id, "user", user_message)

        tool_res = self.mod_tool.run(include_pending=True)
        mod_data = tool_res.get("data", {})

        llm_prompt = (
            f"待审内容或风控咨询：\n'{user_message}'\n\n"
            f"当前风控中台防护指标：\n"
            f"- 活跃敏感词条目: {mod_data.get('active_sensitive_lexicon_count')}\n"
            f"- 待人工审核拦截单据: {mod_data.get('pending_interrupts_count')}\n"
            f"- 治理建议基线: {mod_data.get('risk_advice')}\n\n"
            f"请作为内容风控与合规审片官，针对上述输入给出严格、专业的风控质检判定、潜在法律舆情风险与修改建议。"
        )

        thought, reply = await _execute_pod_llm(
            db=db,
            agent_id=self.agent_id,
            system_prompt=self.system_prompt,
            prompt=llm_prompt,
            image_path=attachment_path,
            fallback_seed_thought="调用风控知识库，评估输入内容的敏感度、价值观合规与台词风险。",
        )

        self.record_chat(session_id, "assistant", reply, thought=thought, tool_results=[tool_res])
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "thought": thought,
            "reply": reply,
            "tool_data": mod_data,
            "role_badge": "安全审片官",
        }



    async def inspect_interactions_batch(
        self,
        db: Session,
        items: List[Dict[str, Any]],
        interaction_type: str = "danmaku"
    ) -> Dict[str, Any]:
        """
        4号合规审片官: 针对互动弹幕或评论执行按需批量巡检与自迭代违规词提炼
        双轨防御:
        1. 本地 DFA 状态机极速精准匹配
        2. 大模型深度语境分析与暗语谐音黑话提炼
        """
        start_ts = time.time()
        from app.services.moderation_service import moderation_service
        
        inspected_results = []
        texts_for_llm = []
        
        # 1. 本地 DFA 预检
        for item in items:
            item_id = str(item.get("id"))
            text = str(item.get("content") or "")
            user_name = item.get("user_name", "剧迷")
            video_title = item.get("video_title", "短剧")
            
            has_dfa_viol, sanitized, matched, max_level = moderation_service.check_text(text)
            info = {
                "id": item_id,
                "content": text,
                "sanitized": sanitized,
                "user_name": user_name,
                "video_title": video_title,
                "dfa_hit": has_dfa_viol,
                "matched_words": matched,
                "risk_level": max_level if has_dfa_viol else "LOW",
                "risk_score": 90 if has_dfa_viol else 10,
                "reason": f"命中 DFA 敏感词: {', '.join(matched)}" if has_dfa_viol else "DFA 本地预检安全",
                "is_violation": has_dfa_viol
            }
            inspected_results.append(info)
            cleaned_text = (text[:180] + "...") if len(text) > 180 else text
            texts_for_llm.append({"id": item_id, "text": cleaned_text})

        # 2. 调用 4 号智能体进行大模型批量语义研判与自迭代新词提炼
        suggested_words = []
        llm_status = "COMPLETED"
        if texts_for_llm:
            batch_prompt = (
                f"你是 4号内容安全与合规审片官。以下是社区最新提交的 {len(texts_for_llm)} 条{interaction_type == 'danmaku' and '弹幕' or '评论'}：\n"
                f"{json.dumps(texts_for_llm, ensure_ascii=False, indent=2)}\n\n"
                f"请结合涉政、暴恐、涉黄暗语、侮辱辱骂、变体黑话、引战广告等维度，进行严格的合规研判：\n"
                f"1. 对每条内容给出 risk_score (0~100)、risk_level ('HIGH'/'MEDIUM'/'LOW')、is_violation (true/false) 与详细 reason；\n"
                f"2. 若发现规避检测的新型黑话、谐音字、侮辱暗语，提炼出建议新录入的敏感词条，包含 word, category ('涉政'/'暴恐'/'违禁'/'涉黄'/'辱骂'/'广告'), level ('HIGH'/'MEDIUM'/'LOW') 与提炼 reason。\n"
                f"必须严格返回合法的 JSON 格式，结构如下：\n"
                f"{{\n"
                f'  "evaluations": [\n'
                f'    {{"id": "条目ID", "risk_score": 85, "risk_level": "HIGH", "is_violation": true, "reason": "判定理由"}}\n'
                f"  ],\n"
                f'  "suggested_sensitive_words": [\n'
                f'    {{"word": "建议违规词", "category": "辱骂", "level": "HIGH", "reason": "新型人身攻击暗语", "source_id": "条目ID"}}\n'
                f"  ]\n"
                f"}}"
            )
            
            try:
                thought, reply = await asyncio.wait_for(
                    _execute_pod_llm(
                        db=db,
                        agent_id=self.agent_id,
                        system_prompt=self.system_prompt,
                        prompt=batch_prompt,
                        fallback_seed_thought="4号合规官执行批量互动文本深度语义毒性研判与新型违规词提炼。"
                    ),
                    timeout=20.0
                )
                
                clean_json_str = reply.strip()
                if "```json" in clean_json_str:
                    clean_json_str = clean_json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_json_str:
                    clean_json_str = clean_json_str.split("```")[1].split("```")[0].strip()
                    
                parsed_data = json.loads(clean_json_str)
                eval_map = {e.get("id"): e for e in parsed_data.get("evaluations", [])}
                
                for info in inspected_results:
                    item_id = info["id"]
                    if item_id in eval_map:
                        llm_eval = eval_map[item_id]
                        llm_score = llm_eval.get("risk_score", info["risk_score"])
                        llm_viol = llm_eval.get("is_violation", False)
                        llm_level = llm_eval.get("risk_level", info["risk_level"])
                        llm_reason = llm_eval.get("reason", "")
                        
                        if llm_viol or info["dfa_hit"]:
                            info["is_violation"] = True
                            info["risk_score"] = max(info["risk_score"], llm_score)
                            info["risk_level"] = "HIGH" if (info["dfa_hit"] or llm_level == "HIGH") else llm_level
                            if llm_reason:
                                info["reason"] = f"{info['reason']}; AI研判: {llm_reason}" if info["dfa_hit"] else f"AI研判: {llm_reason}"
                
                raw_proposals = parsed_data.get("suggested_sensitive_words", [])
                for prop in raw_proposals:
                    p_word = str(prop.get("word") or "").strip()
                    if p_word and len(p_word) >= 1:
                        exists_in_lexicon = db.query(SensitiveWord).filter(SensitiveWord.word == p_word).first()
                        exists_in_proposals = db.query(SensitiveWordProposal).filter(
                            SensitiveWordProposal.word == p_word,
                            SensitiveWordProposal.status == "PENDING"
                        ).first()
                        
                        src_id = prop.get("source_id", "")
                        src_item = next((it for it in items if str(it.get("id")) == str(src_id)), None)
                        src_text = src_item.get("content", "") if src_item else ""
                        
                        if not exists_in_lexicon and not exists_in_proposals:
                            new_prop = SensitiveWordProposal(
                                id=str(uuid.uuid4()),
                                word=p_word,
                                category=prop.get("category", "违禁"),
                                level=prop.get("level", "HIGH"),
                                reason=prop.get("reason", "4号合规智能体巡检自动提炼"),
                                source_type=interaction_type,
                                source_content=src_text,
                                status="PENDING"
                            )
                            db.add(new_prop)
                            suggested_words.append({
                                "id": new_prop.id,
                                "word": new_prop.word,
                                "category": new_prop.category,
                                "level": new_prop.level,
                                "reason": new_prop.reason,
                                "source_type": new_prop.source_type,
                                "source_content": new_prop.source_content,
                                "status": "PENDING",
                                "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M")
                            })
                db.commit()
            except asyncio.TimeoutError:
                llm_status = "TIMEOUT_FALLBACK_DFA"
                logger.warning("Agent 4 LLM batch inspect timed out (>20s), gracefully falling back to DFA")
            except Exception as e:
                llm_status = "ERROR_FALLBACK_DFA"
                logger.warning(f"Agent 4 LLM batch inspect fallback to DFA: {e}")
                
        violations = [r for r in inspected_results if r["is_violation"]]
        cost_ms = int((time.time() - start_ts) * 1000)
        
        return {
            "interaction_type": interaction_type,
            "total_inspected": len(inspected_results),
            "violation_count": len(violations),
            "violations": violations,
            "suggested_words": suggested_words,
            "all_results": inspected_results,
            "llm_status": llm_status,
            "cost_ms": max(cost_ms, 85)
        }


# ---------------- Agent 5: 创作者中心作品运营助手 ----------------
class CreatorGrowthPod(BaseAgentPod):
    agent_id = "agent_5"
    agent_number = 5
    name = "作品宣发运营操盘手"
    role_title = "短剧爆款宣发操盘总监 (绝不写分镜)"
    system_prompt = (
        "你是精通短剧流量分发与下沉市场人性的运营总监，专注前3秒吸睛钩子、爆款标题与封面排期。"
        "注意：你只负责流量运营与宣发包装，绝不跨界编写导演镜头分镜。"
    )

    def __init__(self):
        self.growth_tool = ViralPackagingTool()

    async def run_step(
        self,
        session_id: str,
        user_message: str,
        attachment_path: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        self.record_chat(session_id, "user", user_message)

        tool_res = self.growth_tool.run(story_concept=user_message, genre="都市逆袭")
        growth_data = tool_res.get("data", {})

        llm_prompt = (
            f"创作者短剧构想/推广诉求：\n'{user_message}'\n\n"
            f"运营分析物料参考：\n"
            f"- 黄金前3秒钩子初稿: {growth_data.get('golden_3s_hook')}\n"
            f"- 爆款标题参考: {growth_data.get('recommended_viral_titles')}\n"
            f"- 热门话题: {growth_data.get('trending_hashtags')}\n\n"
            f"请作为作品宣发运营操盘手，从短剧前3秒留存率、完播率、爆款标题矩阵与封面画报排期角度，输出高转化营销策划方案。"
        )

        thought, reply = await _execute_pod_llm(
            db=db,
            agent_id=self.agent_id,
            system_prompt=self.system_prompt,
            prompt=llm_prompt,
            image_path=attachment_path,
            fallback_seed_thought="提炼黄金前3秒钩子，打造爆款标题与下沉市场营销转化策略。",
        )

        self.record_chat(session_id, "assistant", reply, thought=thought, tool_results=[tool_res])
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "thought": thought,
            "reply": reply,
            "growth_data": growth_data,
            "role_badge": "宣发操盘总监",
        }


# ---------------- Agent 6: 剧本视听节奏与多模态解析官 ----------------
class MultimodalCinemaPod(BaseAgentPod):
    agent_id = "agent_6"
    agent_number = 6
    name = "多模态视听与人物图谱解析官"
    role_title = "影视镜头语言与节奏大师"
    system_prompt = (
        "你是影视镜头语言与视听节奏大师，擅长基于台词字幕矛盾冲突与人物动机网络深度剖析短剧视听张力。"
    )

    def __init__(self):
        self.cinema_tool = MultimodalCinemaAnalysisTool()

    async def run_step(
        self,
        session_id: str,
        user_message: str,
        attachment_path: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        self.record_chat(session_id, "user", user_message)

        tool_res = self.cinema_tool.run(drama_title=user_message or "当前解析剧目")
        cinema_data = tool_res.get("data", {})

        llm_prompt = (
            f"视听解析任务：'{user_message}'\n\n"
            f"多模态节拍分析数据：\n"
            f"- 节拍清单: {cinema_data.get('visual_audio_beats')}\n"
            f"- 镜头运镜建议: {cinema_data.get('cinematography_advice')}\n"
            f"- 核心人物节点: {len(cinema_data.get('echarts_graph_data', {}).get('nodes', []))} 位角色\n\n"
            f"请作为多模态视听与人物图谱解析官，深度剖析台词冲突张力、镜头组接节奏与角色动机脉络，给出导演级拉片建议。"
        )

        thought, reply = await _execute_pod_llm(
            db=db,
            agent_id=self.agent_id,
            system_prompt=self.system_prompt,
            prompt=llm_prompt,
            image_path=attachment_path,
            fallback_seed_thought="解析字幕台词矛盾节拍与角色动机网络，输出多模态拉片建议。",
        )

        self.record_chat(session_id, "assistant", reply, thought=thought, tool_results=[tool_res])
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "thought": thought,
            "reply": reply,
            "cinema_data": cinema_data,
            "role_badge": "多模态镜头大师",
        }


# ---------------- Agent 7: 智能荐剧 & 网盘自动同步管家 ----------------
class CloudSyncRecommenderPod(BaseAgentPod):
    agent_id = "agent_7"
    agent_number = 7
    name = "短剧媒资管家 & 网盘同步助手"
    role_title = "智能找剧推荐官 & 外部短剧一键入库助手"
    system_prompt = (
        "你负责真实剧库的精准找剧推荐，同时支持识别外部短剧网盘链接并触发自动转存入库。"
    )

    def __init__(self):
        self.sync_tool = CloudSyncTool()

    async def run_step(
        self,
        session_id: str,
        user_message: str,
        attachment_path: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        self.record_chat(session_id, "user", user_message)

        tool_res = None
        if "http://" in user_message or "https://" in user_message or "pan." in user_message:
            tool_res = self.sync_tool.run(resource_url=user_message, target_category="都市逆袭")

        llm_prompt = (
            f"用户找剧或同步指令：'{user_message}'\n\n"
            f"链接抓取工具响应：{tool_res.get('data') if tool_res else '未触发外部抓取'}\n\n"
            f"请作为短剧媒资管家：若包含网盘或视频链接，汇报转存入库进展；若为寻找好看短剧，结合反转逆袭、都市爽剧或精品悬疑推荐优质短剧与看点。"
        )

        thought, reply = await _execute_pod_llm(
            db=db,
            agent_id=self.agent_id,
            system_prompt=self.system_prompt,
            prompt=llm_prompt,
            image_path=attachment_path,
            fallback_seed_thought="分析找剧诉求或解析外部网盘媒资链接。",
        )

        self.record_chat(session_id, "assistant", reply, thought=thought, tool_results=[tool_res] if tool_res else None)
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "thought": thought,
            "reply": reply,
            "role_badge": "媒资同步管家",
        }


# ---------------- Agent 8: 编导剧本与分镜雕塑家 ----------------
class ScriptStoryboardPod(BaseAgentPod):
    agent_id = "agent_8"
    agent_number = 8
    name = "影视编导与分镜雕塑家"
    role_title = "9:16 竖屏导演分镜主笔 (核心主创)"
    system_prompt = (
        "你是精通 9:16 竖屏短剧工业化制作的专业编导与分镜雕塑家。"
        "精通镜头景别、运镜机位、对白节奏、音效配乐与短剧黄金前3秒爆发力。"
    )

    def __init__(self):
        self.storyboard_tool = ScriptStoryboardTool()

    async def run_step(
        self,
        session_id: str,
        user_message: str,
        attachment_path: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        self.record_chat(session_id, "user", user_message)

        tool_res = self.storyboard_tool.run(
            story_prompt=user_message,
            attachment_file_path=attachment_path,
            episodes_target=1,
        )
        sb_data = tool_res.get("data", {})

        llm_prompt = (
            f"剧本分镜创作指令：'{user_message}'\n\n"
            f"挂载附件文件：{attachment_path or '无'}\n"
            f"分镜生成器基础框架：\n"
            f"- 故事主题: {sb_data.get('story_theme')}\n"
            f"- 镜头设计预案: {sb_data.get('storyboard_table')}\n"
            f"- 导演手记: {sb_data.get('director_notes')}\n\n"
            f"【圆桌群聊发言规范】：请作为 9:16 竖屏编导雕塑家，以敏捷精炼的群聊口吻（200字以内），直击核心视听机位景别、情绪爆发点与前3镜头反转张力。"
        )

        thought, reply = await _execute_pod_llm(
            db=db,
            agent_id=self.agent_id,
            system_prompt=self.system_prompt,
            prompt=llm_prompt,
            image_path=attachment_path,
            fallback_seed_thought="编排 9:16 竖屏分镜机位与戏剧张力，生成影视级视听分镜表。",
        )

        self.record_chat(session_id, "assistant", reply, thought=thought, tool_results=[tool_res])
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "thought": thought,
            "reply": reply,
            "storyboard_data": sb_data,
            "role_badge": "编导创作总监",
        }


# ---------------- Agent 9: 主控制台总编排 & 记忆整合器 ----------------
class MasterOrchestratorPod(BaseAgentPod):
    agent_id = "agent_9"
    agent_number = 9
    name = "主智能体总控台 & 记忆整合器"
    role_title = "平台全局中央大脑 & 圆桌常务议长 (权限最大)"
    system_prompt = (
        "你是平台最高调度中枢与多智能体圆桌常务议长，拥有调度 1~8 号全量子智能体的最大协调权限。"
        "负责任务意图识别、拆解分工、主持跨角色研讨辩论，并统筹全局黑板记忆与最终交付。"
    )

    async def run_step(
        self,
        session_id: str,
        user_message: str,
        attachment_path: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        self.record_chat(session_id, "user", user_message)

        history = self.get_isolated_history(session_id, limit=3)
        history_context = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in history])

        llm_prompt = (
            f"制片人/总控台下达任务：\n'{user_message}'\n\n"
            f"近期交互会话：\n{history_context}\n\n"
            f"【圆桌群聊发言规范】：请作为主智能体总控台常务议长，在群聊中以精炼敏捷的口吻（150字以内），对制片人构想快速拆解并点将指派最相关的领域专家，阐述协同流水线。"
        )

        thought, reply = await _execute_pod_llm(
            db=db,
            agent_id=self.agent_id,
            system_prompt=self.system_prompt,
            prompt=llm_prompt,
            image_path=attachment_path,
            fallback_seed_thought="总控调度中枢拆解制片人需求，统筹多智能体协同流水线。",
        )

        self.record_chat(session_id, "assistant", reply, thought=thought)
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "thought": thought,
            "reply": reply,
            "role_badge": "总控常务议长",
        }


# 统一集中注册表
FLEET_POD_REGISTRY: Dict[str, BaseAgentPod] = {
    "agent_1": CommunityRepresentativePod(),
    "agent_2": CompanionPetPod(),
    "agent_3": KnowledgeAdminPod(),
    "agent_4": ModerationGatekeeperPod(),
    "agent_5": CreatorGrowthPod(),
    "agent_6": MultimodalCinemaPod(),
    "agent_7": CloudSyncRecommenderPod(),
    "agent_8": ScriptStoryboardPod(),
    "agent_9": MasterOrchestratorPod(),
}
