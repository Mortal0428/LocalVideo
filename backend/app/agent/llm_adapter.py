import logging
from typing import Optional
from app.services.llm_gateway import llm_gateway

logger = logging.getLogger(__name__)

class LLMAdapter:
    """
    Unified LLM Adapter delegating to singleton LLMGateway.
    Zero fake fallback texts; outputs transparent system diagnostics on failure.
    """
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url
        self.model = model

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call LLMGateway with circuit breaker, rate limiter, and transparent diagnostics."""
        result = await llm_gateway.generate(prompt=prompt, system_prompt=system_prompt)
        return result.get("content", "")

llm_adapter = LLMAdapter()
