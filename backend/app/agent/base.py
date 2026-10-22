from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncIterator
from pydantic import BaseModel

class AgentContext(BaseModel):
    task_id: str
    target_name: str
    target_domain: Optional[str] = None
    target_industry: Optional[str] = None
    requirement_desc: str
    kb_id: Optional[str] = None
    extra_params: Optional[Dict[str, Any]] = None

class AgentStepEvent(BaseModel):
    step_name: str
    status: str  # RUNNING, COMPLETED, FAILED
    message: str
    payload: Optional[Dict[str, Any]] = None

class AgentResult(BaseModel):
    task_id: str
    persona_analysis: Dict[str, Any]
    pain_points: Dict[str, Any]
    generated_proposals: Dict[str, Any]
    confidence_score: float
    logs: List[Dict[str, Any]]

class BaseAgent(ABC):
    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """Execute the agent task synchronously/asynchronously and return full results."""
        pass

    @abstractmethod
    async def stream_run(self, context: AgentContext) -> AsyncIterator[AgentStepEvent]:
        """Stream execution events and intermediate outputs."""
        pass
