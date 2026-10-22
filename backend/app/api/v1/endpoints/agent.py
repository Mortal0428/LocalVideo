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
    model_name: Optional[str] = None

@router.post("/chat")
async def chat_with_video_agent(req: AgentChatRequest):
    """Interact with in-player Video Companion Agent (Legacy Sync)."""
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

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
    Streaming companion agent conversation with Timeline Subtitle RAG & Multimodal Skills.
    Streams SSE tokens and SEEK action cards.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="提问内容不能为空")

    return StreamingResponse(
        agent_service.chat_stream(
            db=db,
            episode_id=req.episode_id,
            question=req.question.strip(),
            current_video_time=req.current_video_time or 0.0,
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
    """Fetch high-energy dramatic highlight turning points extracted by Timeline Skill."""
    highlights = timeline_skill.get_highlights(db, episode_id)
    return {
        "code": 200,
        "data": highlights
    }

@router.get("/quick-prompts/{episode_id}")
def get_quick_prompts(episode_id: str):
    """Fetch suggested starter questions for this episode."""
    prompts = video_rag_service.get_quick_prompts(episode_id)
    return {
        "code": 200,
        "data": prompts
    }
