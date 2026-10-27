import time
import httpx
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.llm_gateway import llm_gateway

router = APIRouter()

@router.get("/telemetry")
async def get_system_telemetry(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns real-time system health, LLM circuit status, active model, and telemetry.
    Adheres strictly to PROJECT.md interface contract.
    """
    health = llm_gateway.get_health_status()
    cfg = llm_gateway.get_active_config()
    raw_cfg = llm_gateway.get_raw_config()

    # Measure latency to active provider endpoint (probe with short timeout)
    latency_ms = 1.0
    start_t = time.time()
    try:
        base_url = cfg.get("base_url", "http://localhost:11434")
        provider = cfg.get("provider", "ollama")
        api_key = raw_cfg.get("api_key", "")
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        async with httpx.AsyncClient(timeout=2.0) as client:
            if provider == "ollama":
                resp = await client.get(f"{base_url.rstrip('/')}/api/tags")
                if resp.status_code == 200:
                    latency_ms = round((time.time() - start_t) * 1000, 1)
            else:
                resp = await client.get(f"{base_url.rstrip('/')}/models", headers=headers)
                latency_ms = round((time.time() - start_t) * 1000, 1)
    except Exception:
        latency_ms = round((time.time() - start_t) * 1000, 1)

    # Query pending review tasks count
    pending_count = 0
    try:
        from app.models.review import ContentReview
        pending_count = db.query(ContentReview).filter(ContentReview.review_status == "PENDING").count()
    except Exception:
        pending_count = 0

    return {
        "status": health["status"],
        "circuit_state": health["circuit_state"],
        "active_provider": health["active_provider"],
        "active_model": health["active_model"],
        "latency_ms": latency_ms,
        "uptime_seconds": health["uptime_seconds"],
        "pending_reviews_count": pending_count,
        "consecutive_failures": health.get("consecutive_failures", 0),
        "recovery_countdown_seconds": health.get("recovery_countdown_seconds", 0.0)
    }
