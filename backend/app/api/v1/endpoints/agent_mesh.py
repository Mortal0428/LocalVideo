"""
CinemaAgent Agent Mesh 升级版统一 API 网关
支持全场景通用智能体聊天 (文件上传/链接抓取/滑动窗口)、动态超时配置、自进化提案管理与圆桌协同
"""

import os
import re
import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.agent_hub import AgentEvolutionProposal
from app.services.agent_fleet.core.backbone_graph import global_state_engine
from app.services.agent_fleet.core.memory_hub import global_memory_hub
from app.services.agent_fleet.core.resilience import (
    load_runtime_governance_config,
    update_runtime_governance_config,
    execute_with_resilience,
)
from app.services.agent_fleet.evolving.dynamic_loader import global_dynamic_loader
from app.services.agent_fleet.evolving.skill_distiller import global_skill_distiller
from app.services.agent_fleet.pods.specialized_pods import FLEET_POD_REGISTRY
from app.services.ocr.ocr_service import ocr_service

router = APIRouter()
logger = logging.getLogger("agent_mesh_api")


class UniversalChatRequest(BaseModel):
    agent_id: str = Field(..., description="目标智能体编号: agent_1 到 agent_9")
    session_id: str = Field(..., description="唯一会话ID，用于物理隔离作用域")
    message: str = Field(..., description="用户输入的自然语言或指令")
    attachment_path: Optional[str] = Field(None, description="上传的剧本文档或字幕文件本地路径")
    external_resource_url: Optional[str] = Field(None, description="外部短剧或网盘链接")
    context_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="业务模块上下文")


ATTACHMENTS_DIR = os.path.join(os.getcwd(), "storage", "agent_attachments")
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

_EMOJI_PATTERN = re.compile(
    "["
    "\U00010000-\U0010ffff"
    "\u2600-\u27bf"
    "\u2300-\u23ff"
    "\u2b50-\u2b55"
    "\u200d"
    "\ufe0f"
    "]+",
    flags=re.UNICODE
)

def strip_emojis(text: str) -> str:
    if not text or not isinstance(text, str):
        return text
    return _EMOJI_PATTERN.sub("", text)


@router.post("/upload-attachment")
async def upload_agent_attachment(file: UploadFile = File(...)):
    """通用 ChatGPT 风格附件/图片上传接口，支持文本提取与多模态解析准备"""
    filename = file.filename or "attachment"
    ext = os.path.splitext(filename)[1].lower()
    allowed_exts = {".txt", ".md", ".json", ".doc", ".docx", ".pdf", ".png", ".jpg", ".jpeg", ".webp"}
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")

    safe_name = f"{uuid.uuid4().hex[:12]}_{filename}"
    file_path = os.path.join(ATTACHMENTS_DIR, safe_name)

    content_bytes = await file.read()
    with open(file_path, "wb") as f:
        f.write(content_bytes)

    is_image = ext in {".png", ".jpg", ".jpeg", ".webp"}
    preview_text = ""

    if not is_image:
        try:
            preview_text = content_bytes[:4000].decode("utf-8", errors="ignore").strip()
        except Exception:
            preview_text = f"[{filename} 文本附件，大小: {len(content_bytes)} 字节]"
    else:
        preview_text = f"[多模态图片附件: {filename}, 大小: {len(content_bytes)} 字节]"

    return {
        "code": 200,
        "message": "附件上传解析成功",
        "data": {
            "file_name": filename,
            "file_path": file_path,
            "file_url": f"/storage/agent_attachments/{safe_name}",
            "file_size": len(content_bytes),
            "is_image": is_image,
            "preview_text": preview_text[:600],
        },
    }


@router.post("/chat")
async def universal_agent_chat(req: UniversalChatRequest, db: Session = Depends(get_db)):
    """通用网页版智能体对话接口 (支持附件、链接、物理隔离滑动窗口与超时断路保护)"""
    agent_id = req.agent_id
    if agent_id not in FLEET_POD_REGISTRY and agent_id != "agent_9":
        agent_id = "agent_9"

    # 将外部链接或附件文本合并入消息提示
    actual_message = req.message
    if req.external_resource_url:
        actual_message = f"{req.external_resource_url} {actual_message}".strip()

    if req.attachment_path and os.path.exists(req.attachment_path):
        ext = os.path.splitext(req.attachment_path)[1].lower()
        if ext in ('.jpg', '.jpeg', '.png', '.webp', '.bmp'):
            # 多模态图像: 经由 RapidOCR 神经网络提取文字与结构化图像属性
            try:
                vis_res = ocr_service.analyze_image(req.attachment_path)
                actual_message = f"{actual_message}{vis_res['formatted_prompt_block']}"
            except Exception as e:
                logger.warning(f"Failed to analyze image with RapidOCR: {e}")
                actual_message = f"{actual_message}\n\n[用户已上传图片附件: {os.path.basename(req.attachment_path)}]"
        else:
            # 文本类剧本文档读取
            try:
                with open(req.attachment_path, "r", encoding="utf-8", errors="ignore") as af:
                    extracted_snippet = af.read(6000).strip()
                    if extracted_snippet:
                        actual_message = f"{actual_message}\n\n[用户已上传文档附件参考内容]\n```text\n{extracted_snippet}\n```"
            except Exception as e:
                logger.warning(f"Failed to read attached file: {e}")

    # 在弹性断路保护下执行
    async def _run():
        return await global_state_engine.dispatch_agent_step(
            agent_id=agent_id,
            session_id=req.session_id,
            user_message=actual_message,
            attachment_path=req.attachment_path,
            context_data=req.context_data,
            db=db,
        )

    res = await execute_with_resilience(_run, task_name=f"chat_{agent_id}")
    if isinstance(res, dict):
        if "reply" in res and isinstance(res["reply"], str):
            res["reply"] = strip_emojis(res["reply"])
        if "thought" in res and isinstance(res["thought"], str):
            res["thought"] = strip_emojis(res["thought"])
    return {"code": 200, "data": res}


@router.get("/history/{agent_id}/{session_id}")
def get_isolated_history(agent_id: str, session_id: str, limit: int = Query(10, ge=1, le=50)):
    """获取指定 Agent 物理隔离的当前滑动窗口历史消息 (绝不与其它 Agent 串通)"""
    msgs = global_memory_hub.get_isolated_messages(agent_id, session_id, limit)
    return {"code": 200, "data": msgs}


@router.get("/governance/config")
def get_runtime_governance():
    """获取当前动态生效的运行时治理参数 (超时时间、滑动窗口大小)"""
    cfg = load_runtime_governance_config()
    return {"code": 200, "data": cfg}


@router.put("/governance/config")
def update_runtime_governance(new_cfg: Dict[str, Any] = Body(...)):
    """前端滑块动态修改超时与滑动窗口参数并持久化"""
    saved = update_runtime_governance_config(new_cfg)
    return {"code": 200, "message": "运行时治理配置已热更新并保存", "data": saved}


@router.get("/roundtable/{session_id}/blackboard")
def get_roundtable_blackboard(session_id: str):
    """查询多智能体协同圆桌的公共只读黑板确定性工件"""
    bb = global_memory_hub.get_full_blackboard(session_id)
    return {"code": 200, "data": bb}


@router.get("/evolution/proposals")
def list_evolution_proposals(db: Session = Depends(get_db)):
    """查询自进化技能候选提案列表"""
    proposals = db.query(AgentEvolutionProposal).order_by(
        AgentEvolutionProposal.created_at.desc()
    ).limit(30).all()

    return {
        "code": 200,
        "data": [
            {
                "id": p.id,
                "title": p.proposal_title,
                "target_agent_id": p.target_agent_id,
                "category": p.category,
                "critic_score": p.critic_score,
                "critic_verdict": p.critic_verdict,
                "skill_content": p.generated_skill_content,
                "status": p.status,
                "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "",
            }
            for p in proposals
        ],
    }


@router.post("/evolution/proposals/{proposal_id}/approve")
def approve_evolution_proposal(proposal_id: str, db: Session = Depends(get_db)):
    """管理员一键审核批准并动态热加载自进化技能"""
    res = global_dynamic_loader.approve_and_hot_load(proposal_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "审核失败"))
    return {"code": 200, "message": res.get("message"), "data": res}


@router.post("/evolution/distill-sample")
def trigger_distill_sample():
    """手动/演示触发一次高质量演练的技能自动蒸馏"""
    res = global_skill_distiller.distill_successful_run(
        session_id="sample-session-roundtable",
        target_agent_id="agent_8",
        task_topic="都市战神雨夜复仇9:16竖屏爆款分镜创作",
        execution_trace={"rounds": 3, "consensus": True},
        critic_score=94.5,
    )
    return {"code": 200, "data": res}


@router.get("/roundtable/sessions")
def list_roundtable_sessions(db: Session = Depends(get_db)):
    """获取圆桌历史研讨会话列表与最新状态"""
    try:
        from app.models.agent_hub import AgentBlackboardSession
        sessions = db.query(AgentBlackboardSession).order_by(AgentBlackboardSession.updated_at.desc()).limit(20).all()
        return {
            "code": 200,
            "data": [
                {
                    "session_id": s.session_id,
                    "turn_count": s.turn_count or 1,
                    "rolling_summary": s.rolling_summary or "多专家沉浸协同研讨",
                    "updated_at": s.updated_at.strftime("%Y-%m-%d %H:%M:%S") if s.updated_at else "",
                }
                for s in sessions
            ]
        }
    except Exception as e:
        logger.warning(f"Error listing roundtable sessions: {e}")
        return {"code": 200, "data": []}


@router.get("/roundtable/session-all/{session_id}")
def get_roundtable_full_session(session_id: str, db: Session = Depends(get_db)):
    """获取指定会话全量消息流 (合并所有智能体发言)"""
    try:
        all_msgs = []
        for ag_id in list(FLEET_POD_REGISTRY.keys()) + ["agent_9"]:
            pod_msgs = global_memory_hub.get_isolated_messages(ag_id, session_id, window_limit=50)
            all_msgs.extend(pod_msgs)
        all_msgs.sort(key=lambda m: m.get("timestamp", ""))
        bb = global_memory_hub.get_full_blackboard(session_id)
        return {
            "code": 200,
            "data": {
                "messages": all_msgs,
                "blackboard": bb
            }
        }
    except Exception as e:
        logger.warning(f"Error fetching full session: {e}")
        return {"code": 200, "data": {"messages": [], "blackboard": {}}}

