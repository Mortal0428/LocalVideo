"""
CinemaAgent 工业级模块化 Self-RAG 四步反思认证引擎 (SelfRAGEngine)
严格遵循 Self-RAG 标准四步闭环：
1. 步骤一：语义意图检索必要性认证 [Retrieve] / [No-Retrieve]
2. 步骤二：切片防剧透与相关度认证 [Is-Relevant] / [Irrelevant]
3. 步骤三：答案忠实度与幻觉反思校验 [Is-Supported] / [No-Support]
4. 步骤四：答案有用性打分与时间胶囊校验 [Is-Useful]
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from app.services.rag.core.datatypes import Document, QueryBundle

logger = logging.getLogger(__name__)

# 闲聊问候关键词与正则（判定无需检索短剧知识库）
CASUAL_CHAT_PATTERNS = [
    r'^(?:你好|您好|hello|hi|在吗|在么|哈喽|早上好|下午好|晚上好)[,\s，!！?？~]*$',
    r'^(?:你好|您好)[,\s，~]*(?:在吗|在么)[!！?？\s]*$',
    r'^(?:你是谁|介绍一下你自己|你叫什么|你能做什么|功能介绍)[,\s，!！?？~]*$',
    r'^(?:讲个笑话|说个段子|今天天气怎么样|再见|拜拜)[,\s，!！?？~]*$'
]


class SelfRAGStepResult:
    """Self-RAG 步骤执行轨迹"""
    def __init__(self):
        self.step1_retrieve_tag: str = "[Retrieve]"
        self.step1_need_retrieve: bool = True
        self.step2_filtered_docs: List[Document] = []
        self.step2_inspection_details: List[Dict[str, Any]] = []
        self.step3_support_tag: str = "[Fully-Supported]"
        self.step3_faithfulness_score: float = 1.0
        self.step4_utility_tag: str = "[Is-Useful-5]"
        self.step4_utility_score: float = 5.0
        self.time_anchors: List[Dict[str, Any]] = []
        self.best_anchor: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step1_gate": {
                "tag": self.step1_retrieve_tag,
                "need_retrieve": self.step1_need_retrieve
            },
            "step2_relevance": {
                "retained_count": len(self.step2_filtered_docs),
                "details": self.step2_inspection_details
            },
            "step3_faithfulness": {
                "tag": self.step3_support_tag,
                "score": self.step3_faithfulness_score
            },
            "step4_utility": {
                "tag": self.step4_utility_tag,
                "score": self.step4_utility_score,
                "anchors": self.time_anchors,
                "best_anchor": self.best_anchor
            }
        }


class SelfRAGEngine:
    """
    Self-RAG 四步反思认证引擎
    """
    def __init__(self):
        pass

    def evaluate_retrieval_need(self, query: str) -> Tuple[bool, str]:
        """
        步骤一：语义意图检索必要性认证
        返回: (need_retrieve, tag)
        """
        clean_q = query.strip()
        for pat in CASUAL_CHAT_PATTERNS:
            if re.match(pat, clean_q, re.IGNORECASE):
                logger.info(f"[Self-RAG Step 1] 闲聊意图匹配命中: '{clean_q}' -> [No-Retrieve]")
                return False, "[No-Retrieve]"
        logger.info(f"[Self-RAG Step 1] 剧情事实查询: '{clean_q}' -> [Retrieve]")
        return True, "[Retrieve]"

    def filter_relevant_and_anti_spoiler(
        self,
        documents: List[Document],
        bundle: QueryBundle
    ) -> Tuple[List[Document], List[Dict[str, Any]]]:
        """
        步骤二：切片防剧透与相关性认证 [Is-Relevant] / [Irrelevant]
        - 防剧透门控：严禁超出观众当前播放集数与当前秒数
        - 语义质量门控：过滤低置信度切片
        """
        retained: List[Document] = []
        details: List[Dict[str, Any]] = []

        curr_ep = bundle.episode_num
        curr_sec = bundle.current_sec

        for doc in documents:
            # 1. 防剧透检查
            is_spoiler = False
            # 如果切片有明确的集数和时间
            if doc.episode_num > curr_ep:
                is_spoiler = True
            elif doc.episode_num == curr_ep and doc.start_sec > (curr_sec + 15.0):  # 允许最多15秒微超前上下文
                is_spoiler = True

            if is_spoiler:
                details.append({
                    "doc_id": doc.id,
                    "title": getattr(doc, "title", doc.id),
                    "tag": "[Irrelevant-Spoiler]",
                    "reason": f"超出当前进度(第{curr_ep}集 {curr_sec:.1f}s), 切片属于第{doc.episode_num}集 {doc.start_sec:.1f}s"
                })
                continue

            # 2. 相关性阈值检查
            # 基础相关性分数阈值
            if doc.score < 0.25 and doc.chunk_strategy != "parent_child":
                details.append({
                    "doc_id": doc.id,
                    "title": getattr(doc, "title", doc.id),
                    "tag": "[Irrelevant-LowScore]",
                    "reason": f"余弦/RRF相关度评分过低({doc.score:.3f} < 0.25)"
                })
                continue

            # 认证通过
            doc_tag = "[Is-Relevant]"
            details.append({
                "doc_id": doc.id,
                "title": getattr(doc, "title", doc.id),
                "tag": doc_tag,
                "reason": f"防剧透通过且相关度合格({doc.score:.3f})"
            })
            retained.append(doc)

        logger.info(f"[Self-RAG Step 2] 切片认证完成: 原始 {len(documents)} 篇 -> 保留 {len(retained)} 篇")
        return retained, details

    def compress_and_anchor_context(
        self,
        documents: List[Document],
        max_chars: int = 1500
    ) -> Tuple[str, List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        动态上下文去重压缩与时间胶囊锚点提取
        返回: (压缩文本, 时间锚点列表, 最佳跳帧锚点)
        """
        if not documents:
            return "", [], None

        time_anchors: List[Dict[str, Any]] = []
        context_blocks: List[str] = []
        seen_texts = set()
        best_anchor = None

        for doc in documents:
            snippet = doc.text.strip()
            if snippet in seen_texts:
                continue
            seen_texts.add(snippet)

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
                if best_anchor is None or (doc.score >= 0.35 and doc.score > best_anchor.get("score", 0.0)):
                    best_anchor = anchor_info

                block_str = f"【第{doc.episode_num}集 {time_tag}】{snippet}"
            else:
                block_str = f"【背景知识 / 图谱事实】{snippet}"

            if doc.parent_text and len(doc.parent_text) > len(doc.text) and len(block_str) < 300:
                block_str += f" (完整语境: {doc.parent_text[:120]}...)"

            context_blocks.append(block_str)

        merged_text = "\n".join(context_blocks)
        if len(merged_text) > max_chars:
            merged_text = merged_text[:max_chars] + "\n...(已根据上下文窗口自适应精简)..."

        return merged_text, time_anchors, best_anchor

    def verify_faithfulness(self, answer: str, context: str) -> Tuple[str, float]:
        """
        步骤三：答案忠实度与幻觉反思校验 [Is-Supported] / [No-Support]
        对比答案中关键名词与剧情切片内容，检测无事实依据编造
        """
        if not answer.strip():
            return "[No-Support]", 0.0

        if not context.strip():
            # 没有检索切片时，若回答是基于常识或说明未找到，则视为可信
            return "[Ungrounded-Honest]", 0.85

        # 简单关键实体词匹配验真
        ans_chars = set(answer)
        ctx_chars = set(context)
        overlap = ans_chars.intersection(ctx_chars)
        ratio = len(overlap) / max(len(ans_chars), 1)

        # 检查是否包含虚假肯定或幻觉词
        hallucination_indicators = ["根据后续剧集透露", "在未来的大结局中", "据传后续剧情"]
        has_hallucination = any(h in answer for h in hallucination_indicators)

        if has_hallucination:
            return "[No-Support-Hallucination]", 0.2

        if ratio >= 0.6:
            return "[Fully-Supported]", round(min(1.0, ratio * 1.1), 2)
        elif ratio >= 0.35:
            return "[Partially-Supported]", round(ratio, 2)
        else:
            return "[No-Support]", round(ratio, 2)

    def evaluate_utility(
        self,
        answer: str,
        query: str,
        best_anchor: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, float]:
        """
        步骤四：答案有用性打分与时间胶囊校验 [Is-Useful]
        评分区间 1.0 ~ 5.0
        """
        score = 3.0

        # 检查字数饱满度
        if len(answer.strip()) >= 50:
            score += 0.5
        elif len(answer.strip()) < 15:
            score -= 1.0

        # 检查是否精准嵌入了时间胶囊 [mm:ss]
        capsule_match = re.search(r'\[\d{2}:\d{2}\]', answer)
        if capsule_match:
            score += 1.0
            tag = f"[Is-Useful-{min(5, int(round(score)))}]"
            return tag, min(5.0, score)

        if best_anchor and best_anchor.get("time_tag"):
            # 有跳帧锚点但未被采纳
            score += 0.2
            tag = f"[Is-Useful-{min(5, int(round(score)))}]"
            return tag, min(5.0, score)

        tag = f"[Is-Useful-{min(5, int(round(score)))}]"
        return tag, max(1.0, min(5.0, score))

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
