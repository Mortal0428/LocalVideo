"""
CinemaAgent 工业级模块化 RAG 嵌入向量统一适配引擎 (MultiModelEmbedder)
统一对接本地 Ollama (qwen3-embedding 等) 与云端 Embedding API；
支持熔断缓存与 384 维确定性特征哈希 L2 归一化兜底向量算法，
确保在外部模型网络离线时检索运算仍具备连续数学空间与高稳定性。
"""

import time
import math
import hashlib
import asyncio
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_DIMENSION = 384


def compute_deterministic_fallback_embedding(text: str, dim: int = DEFAULT_DIMENSION) -> List[float]:
    """
    确定性离线特征向量哈希算法（L2 归一化单位向量）。
    提取字符 1-gram, 2-gram, 3-gram 特征映射到指定维度空间，
    保证相同与相似字词具有高内积余弦相似度。
    """
    if not text:
        return [0.0] * dim

    vec = [0.0] * dim
    clean_text = text.strip()
    n = len(clean_text)

    # 1. 字符 N-gram 频率投射
    for i in range(n):
        # 1-gram
        h1 = int(hashlib.md5(clean_text[i].encode('utf-8')).hexdigest(), 16)
        idx1 = h1 % dim
        sign1 = 1.0 if (h1 >> 8) % 2 == 0 else -1.0
        vec[idx1] += sign1 * 1.0

        # 2-gram
        if i + 1 < n:
            gram2 = clean_text[i:i+2]
            h2 = int(hashlib.md5(gram2.encode('utf-8')).hexdigest(), 16)
            idx2 = h2 % dim
            sign2 = 1.0 if (h2 >> 8) % 2 == 0 else -1.0
            vec[idx2] += sign2 * 1.5

        # 3-gram
        if i + 2 < n:
            gram3 = clean_text[i:i+3]
            h3 = int(hashlib.md5(gram3.encode('utf-8')).hexdigest(), 16)
            idx3 = h3 % dim
            sign3 = 1.0 if (h3 >> 8) % 2 == 0 else -1.0
            vec[idx3] += sign3 * 2.0

    # 2. L2 范数归一化
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 1e-9:
        return [round(x / norm, 6) for x in vec]
    return [0.0] * dim


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """计算两向量的余弦相似度 [-1.0, 1.0]"""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm_a * norm_b)))


class MultiModelEmbedder:
    """
    统一多模型 Embedding 适配器 (带熔断探测缓存)
    """
    def __init__(self):
        self._last_probe_time = 0.0
        self._service_available = True
        self._probe_cooldown = 15.0  # 离线熔断冷却 15 秒

    async def aembed_text(self, text: str) -> List[float]:
        """异步获取文本嵌入向量，优先调用 LLMGateway，失败快速降级并冷却熔断"""
        now = time.time()
        if not self._service_available and (now - self._last_probe_time < self._probe_cooldown):
            return compute_deterministic_fallback_embedding(text)

        try:
            from app.services.llm_gateway import llm_gateway
            # 尝试生成
            vec = await asyncio.wait_for(llm_gateway.generate_embedding(text), timeout=1.5)
            if vec and len(vec) > 0:
                self._service_available = True
                return vec
        except Exception as e:
            self._service_available = False
            self._last_probe_time = now
            logger.debug(f"Embedding service offline/timeout ({e}), cached fallback for 15s")

        return compute_deterministic_fallback_embedding(text)

    def embed_text(self, text: str) -> List[float]:
        """同步获取文本嵌入向量"""
        now = time.time()
        if not self._service_available and (now - self._last_probe_time < self._probe_cooldown):
            return compute_deterministic_fallback_embedding(text)

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                return compute_deterministic_fallback_embedding(text)
            else:
                return asyncio.run(self.aembed_text(text))
        except Exception:
            return compute_deterministic_fallback_embedding(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量获取嵌入向量"""
        return [self.embed_text(t) for t in texts]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """LangChain/RAG 标准兼容别名：批量获取嵌入向量"""
        return self.embed_batch(texts)


embedder = MultiModelEmbedder()
