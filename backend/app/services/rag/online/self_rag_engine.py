"""
CinemaAgent 工业级模块化 Self-RAG 反思门控与时间轴上下文动态压缩引擎 (SelfRAGEngine)
遵循《03_05_05_01 Self-RAG》规范：
1. [Retrieve] 自适应检索门控（识别闲聊问候 vs 剧情推理解析）
2. 上下文动态去重压缩与时间胶囊锚点 [mm:ss] 注入
3. 结构化 Prompt 合成与时间戳跳转卡片提取
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from app.services.rag.core.datatypes import Document, QueryBundle

logger = logging.getLogger(__name__)

# 基础日常闲聊词表，触发 [No-Retrieve]
CASUAL_CHAT_PATTERNS = [
    r'^(?:你好|您好|hello|hi|在吗|在么|哈喽|早上好|下午好|晚上好)[,\s，!！?？~]*$',
    r'^(?:你好|您好)[,\s，~]*(?:在吗|在么)[!！?？\s]*$',
    r'^(?:你是谁|介绍一下你自己|你叫什么|你能做什么|功能介绍)[,\s，!！?？~]*$',
    r'^(?:讲个笑话|说个段子|今天天气怎么样|再见|拜拜)[,\s，!！?？~]*$'
]


class SelfRAGEngine:
    """
    Self-RAG 反思门控与上下文压缩引擎
    """
    def __init__(self):
        pass

    def evaluate_retrieval_need(self, query: str) -> bool:
        """
        [Retrieve] 门控判定：
        返回 True 表示需要触发短剧知识检索；
        返回 False 表示日常闲聊问候，无需检索知识库。
        """
        clean_q = query.strip()
        for pat in CASUAL_CHAT_PATTERNS:
            if re.match(pat, clean_q, re.IGNORECASE):
                return False
        return True

    def compress_and_anchor_context(
        self,
        documents: List[Document],
        max_chars: int = 1200
    ) -> Tuple[str, List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        动态上下文压缩与时间胶囊锚点提取
        返回: (压缩后上下文文本, 时间锚点列表, 最佳跳帧锚点)
        """
        if not documents:
            return "", [], None

        time_anchors: List[Dict[str, Any]] = []
        context_blocks: List[str] = []
        seen_texts = set()
        best_anchor = None

        for doc in documents:
            # 文本去重
            snippet = doc.text.strip()
            if snippet in seen_texts:
                continue
            seen_texts.add(snippet)

            # 提取或格式化时间胶囊
            if doc.start_sec > 0 or doc.chunk_strategy == "sentence_window":
                m, s = divmod(int(doc.start_sec), 60)
                time_tag = f"{m:02d}:{s:02d}"
                anchor_info = {
                    "timestamp": doc.start_sec,
                    "time_tag": time_tag,
                    "scene": snippet[:35],
                    "score": doc.score
                }
                time_anchors.append(anchor_info)
                if best_anchor is None:
                    best_anchor = anchor_info
                elif doc.score >= 0.4 and doc.score > best_anchor.get("score", 0.0):
                    best_anchor = anchor_info

                block_str = f"【第{doc.episode_num}集 {time_tag}】{snippet}"
            else:
                block_str = f"【背景知识 / 图谱事实】{snippet}"

            # 父级上下文扩展
            if doc.parent_text and len(doc.parent_text) > len(doc.text) and len(block_str) < 300:
                block_str += f" (完整语境: {doc.parent_text[:120]}...)"

            context_blocks.append(block_str)

        # 动态长度截断
        merged_text = "\n".join(context_blocks)
        if len(merged_text) > max_chars:
            merged_text = merged_text[:max_chars] + "\n...(已动态精简上下文)..."

        return merged_text, time_anchors, best_anchor

    def build_inference_prompt(
        self,
        bundle: QueryBundle,
        compressed_context: str,
        crag_reason: str,
        best_anchor: Optional[Dict[str, Any]] = None
    ) -> str:
        """组装带反思与跳转约束的最终 LLM 推理 Prompt"""
        current_tag = bundle.current_time_tag
        anchor_prompt_clause = ""
        if best_anchor:
            anchor_prompt_clause = f"在分析剧情关键转折点时，请在答案中嵌入时间胶囊按钮标记 `[{best_anchor['time_tag']}]` 以供观众实时点击跳帧。"

        prompt = (
            f"你是一位精通短剧剧情脉络、节奏把控与人物关系的 AI 影视伴读助手。\n"
            f"【观众当前观影进度】：第 {bundle.episode_num} 集，约 {current_tag}。\n"
            f"【CRAG 知识质检诊断】：{crag_reason}\n\n"
            f"【严格已验证的剧情时间轴与知识事实】：\n"
            f"{compressed_context or '（暂无前序匹配剧情切片，请根据通用短剧背景进行诚实解答）'}\n\n"
            f"【防剧透硬性要求】：\n"
            f"严禁透露第 {bundle.episode_num} 集 {current_tag} 之后的未发生反转或大结局剧情！只能根据观众已看进度与上述已知知识进行合理剖析。\n\n"
            f"【观众提问】：{bundle.query_str}\n"
            f"【回答规范】：\n"
            f"1. 语言亲切生动、富有戏剧张力，紧扣观众的观影情绪；\n"
            f"2. {anchor_prompt_clause}\n"
            f"3. 保持回答紧凑精炼，突出核心剧情逻辑。"
        )
        return prompt


self_rag_engine = SelfRAGEngine()
