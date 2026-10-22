from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

class ProspectTaskCreate(BaseModel):
    target_name: str
    target_domain: Optional[str] = None
    target_industry: Optional[str] = None
    requirement_desc: str
    kb_id: Optional[str] = None

class AgentLogOut(BaseModel):
    id: str
    step_name: str
    status: str
    input_payload: Optional[Dict[str, Any]] = None
    output_payload: Optional[Dict[str, Any]] = None
    latency_ms: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProspectTaskOut(BaseModel):
    id: str
    target_name: str
    target_domain: Optional[str] = None
    target_industry: Optional[str] = None
    requirement_desc: str
    status: str
    persona_analysis: Optional[Dict[str, Any]] = None
    pain_points: Optional[Dict[str, Any]] = None
    generated_proposals: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
