"""
==============================================================================
【模块名称】：agent.py (播放器 AI 剧情伴聊与高能切片端点)
【业务职能】：
  负责视频主播放器右侧的 AI 伴聊视窗交互。观众在追剧时，可以实时向智能体提问剧情、
  让 AI 分析角色动机、探索伏笔或调取高能切片，支持单轮问答与 SSE 毫秒级打字机流式输出。
【对应前端】：
  - 核心页面：frontend/src/views/PlayerView.vue (播放器 AI 剧情伴侣抽屉)
  - 前端通信：frontend/src/api/video.ts (chatWithVideoAgent, chatStream)
==============================================================================
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.video_rag_service import video_rag_service
from app.services.agent_service import agent_service
from app.services.skills.timeline_rag_skill import timeline_skill

router = APIRouter()

class AgentChatRequest(BaseModel):
    episode_id: str
    question: str
    current_video_time: Optional[float] = 0.0
    drama_id: Optional[str] = None
    model_name: Optional[str] = None

@router.post("/chat")
async def chat_with_video_agent(
    req: AgentChatRequest,
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent] 模块中的 [chat_with_video_agent] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /chat
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        from app.services.rag.online.pipeline import rag_pipeline
        from app.services.rag.core.datatypes import QueryBundle
        from app.models.rag_corpus import RAGChunk
        from app.models.video import VideoEpisode

        ep_num = 1
        drama_id = req.episode_id
        ep_rec = db.query(VideoEpisode).filter(VideoEpisode.id == req.episode_id).first()
        if ep_rec:
            ep_num = ep_rec.episode_num or 1
            drama_id = ep_rec.video_id or req.episode_id

        chunk_exists = db.query(RAGChunk).filter(
            (RAGChunk.drama_id == drama_id) | (RAGChunk.drama_id == req.episode_id)
        ).first()

        if chunk_exists:
            bundle = QueryBundle(
                query_str=req.question.strip(),
                drama_id=drama_id,
                episode_num=ep_num,
                current_sec=req.current_video_time or 0.0,
                top_k=3
            )
            rag_res = await rag_pipeline.aquery(bundle, db)
            return {
                "code": 200,
                "data": {
                    "response": rag_res.answer,
                    "relevant_timestamps": rag_res.time_anchors,
                    "crag_status": rag_res.crag_status,
                    "retrieved_documents": [d.to_dict() for d in rag_res.retrieved_documents]
                }
            }
    except Exception:
        pass

    result = await video_rag_service.generate_companion_answer(
        episode_id=req.episode_id,
        question=req.question.strip(),
        current_video_time=req.current_video_time or 0.0
    )

    return {
        "code": 200,
        "data": result
    }

@router.post("/chat/stream")
async def chat_with_video_agent_stream(
    req: AgentChatRequest,
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent] 模块中的 [chat_with_video_agent_stream] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /chat/stream
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="提问内容不能为空")

    return StreamingResponse(
        agent_service.chat_stream(
            db=db,
            episode_id=req.episode_id,
            question=req.question.strip(),
            current_video_time=req.current_video_time or 0.0,
            drama_id=req.drama_id,
            model_name=req.model_name
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/episodes/{episode_id}/highlights")
def get_episode_highlights(
    episode_id: str,
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent] 模块中的 [get_episode_highlights] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /episodes/{episode_id}/highlights
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    highlights = timeline_skill.get_highlights(db, episode_id)
    return {
        "code": 200,
        "data": highlights
    }

@router.get("/quick-prompts/{episode_id}")
def get_quick_prompts(episode_id: str):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent] 模块中的 [get_quick_prompts] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /quick-prompts/{episode_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    prompts = video_rag_service.get_quick_prompts(episode_id)
    return {
        "code": 200,
        "data": prompts
    }
