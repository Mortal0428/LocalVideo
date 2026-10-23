"""
CinemaAgent 工业级模块化 RAG 离线切片引擎 (Chunker)
实现 4 种专业切片策略：
1. 固定大小切片 (Fixed-Size Chunking)
2. 滑动窗口切片 (Sliding-Window Chunking)
3. 基于时间轴与字幕的句子窗口切片 (Sentence-Window / Subtitle Chunking)
4. 父子层级分块策略 (Parent-Child Hierarchical Chunking)
"""

import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from app.services.rag.core.datatypes import Document


def parse_srt_time(time_str: str) -> float:
    """解析 SRT 时间戳 '00:01:25,500' -> 85.5 秒"""
    try:
        clean_str = time_str.strip().replace(',', '.')
        parts = clean_str.split(':')
        if len(parts) == 3:
            h = float(parts[0])
            m = float(parts[1])
            s = float(parts[2])
            return h * 3600.0 + m * 60.0 + s
    except Exception:
        pass
    return 0.0


def parse_srt_subtitles(srt_text: str) -> List[Dict[str, Any]]:
    """解析标准 SRT 字幕内容为结构化条目"""
    entries = []
    # 匹配标准 SRT 块: 序号 \n 00:00:01,000 --> 00:00:04,000 \n 文本
    pattern = re.compile(
        r'(\d+)\s*\r?\n(\d{2}:\d{2}:\d{2}[,\.]\d{1,3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{1,3})\s*\r?\n(.*?)(?=\r?\n\r?\n\d+|\Z)',
        re.DOTALL
    )
    for match in pattern.finditer(srt_text):
        idx_str, start_str, end_str, content_str = match.groups()
        start_sec = parse_srt_time(start_str)
        end_sec = parse_srt_time(end_str)
        clean_text = " ".join([line.strip() for line in content_str.splitlines() if line.strip()])
        if clean_text:
            entries.append({
                "index": int(idx_str),
                "start_sec": start_sec,
                "end_sec": end_sec,
                "text": clean_text
            })
    return entries


class TextChunker:
    """
    短剧多策略文本切片器
    """
    def __init__(self):
        pass

    def chunk(
        self,
        text: str,
        strategy: str = "fixed",
        chunk_size: int = 250,
        chunk_overlap: int = 40,
        episode_num: int = 1,
        drama_id: Optional[str] = None,
        **kwargs
    ) -> List[Document]:
        strategy = (strategy or "fixed").lower()
        if strategy == "fixed":
            return self.chunk_fixed(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap, episode_num=episode_num, drama_id=drama_id)
        elif strategy == "sliding_window":
            return self.chunk_sliding_window(text, window_size=chunk_size, step_size=max(50, chunk_size - chunk_overlap), episode_num=episode_num, drama_id=drama_id)
        elif strategy == "sentence_window":
            return self.chunk_sentence_window(text, episode_num=episode_num, drama_id=drama_id)
        elif strategy == "parent_child":
            return self.chunk_parent_child(text, parent_size=chunk_size * 3, child_size=chunk_size, episode_num=episode_num, drama_id=drama_id)
        else:
            return self.chunk_fixed(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap, episode_num=episode_num, drama_id=drama_id)

    def chunk_fixed(
        self,
        text: str,
        chunk_size: int = 250,
        chunk_overlap: int = 40,
        episode_num: int = 1,
        drama_id: Optional[str] = None
    ) -> List[Document]:
        """策略1: 固定大小分块，结合句末标点截断"""
        docs: List[Document] = []
        if not text or not text.strip():
            return docs

        # 尝试按段落或句子自然切分
        paragraphs = [p.strip() for p in re.split(r'\n+', text) if p.strip()]
        current_chunk = ""
        chunk_idx = 0

        for p in paragraphs:
            if len(current_chunk) + len(p) <= chunk_size:
                current_chunk += ("\n" if current_chunk else "") + p
            else:
                if current_chunk:
                    doc = Document(
                        id=str(uuid.uuid4()),
                        text=current_chunk,
                        chunk_strategy="fixed",
                        episode_num=episode_num,
                        start_sec=float(chunk_idx * 30),  # 估算相对时间轴
                        end_sec=float((chunk_idx + 1) * 30),
                        metadata={"drama_id": drama_id, "chunk_index": chunk_idx}
                    )
                    docs.append(doc)
                    chunk_idx += 1
                    # 保留重叠文本
                    overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else ""
                    current_chunk = overlap_text + ("\n" if overlap_text else "") + p
                else:
                    # 单段过长，强制截断
                    for i in range(0, len(p), chunk_size - chunk_overlap):
                        sub_text = p[i:i + chunk_size]
                        doc = Document(
                            id=str(uuid.uuid4()),
                            text=sub_text,
                            chunk_strategy="fixed",
                            episode_num=episode_num,
                            start_sec=float(chunk_idx * 30),
                            end_sec=float((chunk_idx + 1) * 30),
                            metadata={"drama_id": drama_id, "chunk_index": chunk_idx}
                        )
                        docs.append(doc)
                        chunk_idx += 1
                    current_chunk = ""

        if current_chunk.strip():
            doc = Document(
                id=str(uuid.uuid4()),
                text=current_chunk.strip(),
                chunk_strategy="fixed",
                episode_num=episode_num,
                start_sec=float(chunk_idx * 30),
                end_sec=float((chunk_idx + 1) * 30),
                metadata={"drama_id": drama_id, "chunk_index": chunk_idx}
            )
            docs.append(doc)

        return docs

    def chunk_sliding_window(
        self,
        text: str,
        window_size: int = 300,
        step_size: int = 150,
        episode_num: int = 1,
        drama_id: Optional[str] = None
    ) -> List[Document]:
        """策略2: 字符/词汇滑动窗口切片"""
        docs: List[Document] = []
        if not text:
            return docs

        clean_text = text.strip()
        n = len(clean_text)
        chunk_idx = 0
        start = 0

        while start < n:
            end = min(start + window_size, n)
            window_slice = clean_text[start:end].strip()
            if window_slice:
                doc = Document(
                    id=str(uuid.uuid4()),
                    text=window_slice,
                    chunk_strategy="sliding_window",
                    episode_num=episode_num,
                    start_sec=float(chunk_idx * 25),
                    end_sec=float(chunk_idx * 25 + 30),
                    metadata={"drama_id": drama_id, "chunk_index": chunk_idx, "window_start": start, "window_end": end}
                )
                docs.append(doc)
                chunk_idx += 1
            if end >= n:
                break
            start += step_size

        return docs

    def chunk_sentence_window(
        self,
        text: str,
        window_radius: int = 2,
        episode_num: int = 1,
        drama_id: Optional[str] = None
    ) -> List[Document]:
        """
        策略3: 基于时间轴/字幕的句子窗口切片 (Sentence-Window)
        核心句子携带精准时间轴 [start_sec, end_sec]，同时扩展上下文前后 N 句。
        """
        docs: List[Document] = []
        srt_entries = parse_srt_subtitles(text)

        if srt_entries:
            # 严格按照 SRT 字幕逐条构建带上下文窗口的句子块
            total = len(srt_entries)
            for idx, entry in enumerate(srt_entries):
                # 提取前后窗口
                start_w = max(0, idx - window_radius)
                end_w = min(total, idx + window_radius + 1)
                context_lines = [srt_entries[i]["text"] for i in range(start_w, end_w)]
                expanded_context = " ".join(context_lines)

                doc = Document(
                    id=str(uuid.uuid4()),
                    text=entry["text"],
                    parent_text=expanded_context,
                    chunk_strategy="sentence_window",
                    episode_num=episode_num,
                    start_sec=entry["start_sec"],
                    end_sec=entry["end_sec"],
                    metadata={
                        "drama_id": drama_id,
                        "chunk_index": idx,
                        "subtitle_index": entry["index"],
                        "window_size": len(context_lines)
                    }
                )
                docs.append(doc)
            return docs

        # 若非标准 SRT，则按标点拆句
        sentences = [s.strip() for s in re.split(r'([。！？!?\n]+)', text) if s.strip()]
        # 重新拼接标点
        merged_sentences = []
        temp = ""
        for s in sentences:
            if all(c in "。！？!?\n" for c in s):
                temp += s
                merged_sentences.append(temp.strip())
                temp = ""
            else:
                if temp:
                    merged_sentences.append(temp.strip())
                temp = s
        if temp:
            merged_sentences.append(temp.strip())

        total = len(merged_sentences)
        for idx, sent in enumerate(merged_sentences):
            start_w = max(0, idx - window_radius)
            end_w = min(total, idx + window_radius + 1)
            ctx = " ".join(merged_sentences[start_w:end_w])
            doc = Document(
                id=str(uuid.uuid4()),
                text=sent,
                parent_text=ctx,
                chunk_strategy="sentence_window",
                episode_num=episode_num,
                start_sec=float(idx * 5),
                end_sec=float((idx + 1) * 5),
                metadata={"drama_id": drama_id, "chunk_index": idx}
            )
            docs.append(doc)

        return docs

    def chunk_parent_child(
        self,
        text: str,
        parent_size: int = 750,
        child_size: int = 200,
        episode_num: int = 1,
        drama_id: Optional[str] = None
    ) -> List[Document]:
        """
        策略4: 父子分块策略 (Parent-Child Chunking)
        大块 Parent 保存完整上下文，小块 Child 用于向量及关键词精准召回。
        """
        docs: List[Document] = []
        if not text:
            return docs

        # 1. 先生成父块
        parents = self.chunk_fixed(text, chunk_size=parent_size, chunk_overlap=80, episode_num=episode_num, drama_id=drama_id)
        
        child_global_idx = 0
        for p_idx, parent_doc in enumerate(parents):
            # 对每个父块再切出若干子块
            children = self.chunk_fixed(parent_doc.text, chunk_size=child_size, chunk_overlap=30, episode_num=episode_num, drama_id=drama_id)
            for c_idx, child in enumerate(children):
                child.parent_text = parent_doc.text
                child.chunk_strategy = "parent_child"
                child.start_sec = parent_doc.start_sec + float(c_idx * 10)
                child.end_sec = child.start_sec + 15.0
                child.metadata.update({
                    "parent_id": parent_doc.id,
                    "parent_index": p_idx,
                    "child_index": c_idx,
                    "global_index": child_global_idx
                })
                docs.append(child)
                child_global_idx += 1

        return docs


chunker = TextChunker()
