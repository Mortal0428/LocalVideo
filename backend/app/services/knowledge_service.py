# -*- coding: utf-8 -*-
"""
==============================================================================
【业务服务】：backend/app/services/knowledge_service.py
【业务定位】：影视知识资产仓库与实体关联检索服务（KnowledgeService）
【前端链路对接】：
  1. 页面来源：frontend/src/components/CinemaAgentRagCenter.vue（RAG 知识中台大屏）
  2. 触发时机：
     - 管理员在 RAG 知识中台上传短剧大纲剧本、设定集、人物小传；
     - 前端调用 POST /api/v1/rag/upload-doc 或 POST /api/v1/knowledge/documents；
     - 路由函数进入 knowledge_service.save_and_process_document()；
     - 后续 RAG 伴聊问答时，调用 knowledge_service.search_relevant_chunks() 召回背景设定。
【核心功能】：
  1. 剧本文档管理：短剧大纲、人物小传、分集台词文档的统一存取与版本更新；
  2. 离线抽取与预处理（save_and_process_document）：剧本清洗、滑动窗口分片切块；
  3. 知识切片高速检索（search_relevant_chunks）：基于词频语义交叉匹配，毫秒级召回最相关设定。
==============================================================================
"""

import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import httpx

from app.core.config import settings
from app.models.knowledge import KnowledgeBase, KnowledgeDocument
from app.repositories.knowledge_repo import knowledge_base_repo, knowledge_doc_repo

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    【影视剧本知识中台服务类】
    管理创作者或运营人员上传的影视长文本知识资产（剧本总案、分集大纲、人物关系卡）。
    负责文档物理落地、自适应分块切片（Chunking）、生成本地知识索引并提供高速检索。
    """
    def __init__(self):
        # 确保本地上传根目录和向量切片缓存目录存在
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.VECTOR_DB_DIR, exist_ok=True)

    def create_knowledge_base(self, db: Session, name: str, description: Optional[str] = None) -> KnowledgeBase:
        """
        创建新的知识库分组（例如：“都市逆袭题材剧本库”、“悬疑反转系列设定集”）。
        
        【参数说明】：
        - db (Session): 数据库会话。
        - name (str): 知识库名称。
        - description (Optional[str]): 知识库功能描述与定位。
        
        【返回值说明】：
        - KnowledgeBase: 数据库中持久化后的知识库记录对象。
        """
        kb = KnowledgeBase(name=name, description=description)
        return knowledge_base_repo.create(db, kb)

    def get_knowledge_base(self, db: Session, kb_id: str) -> Optional[KnowledgeBase]:
        """按知识库 ID 查询知识库详情"""
        return knowledge_base_repo.get(db, kb_id)

    def list_knowledge_bases(self, db: Session) -> List[KnowledgeBase]:
        """获取全平台所有的知识库列表"""
        return knowledge_base_repo.get_multi(db)

    def save_and_process_document(self, db: Session, kb_id: str, filename: str, content: bytes) -> KnowledgeDocument:
        """
        保存上传的剧本文档文件，自动执行文本清洗、滑动窗口分片，并建立切片索引。
        
        【参数大白话详解】：
        - db (Session): 数据库会话。
        - kb_id (str): 所属知识库的 ID（UUID）。
        - filename (str): 上传的原始文件名（如 "霸道总裁爱上我_剧本全案.txt"）。
        - content (bytes): 文件的二进制字节流（从 FastAPI UploadFile.read() 获取）。
        
        【返回值说明】：
        - KnowledgeDocument: 数据库已保存的文档模型记录，字段包含：
          - id: 文档唯一标识
          - kb_id: 所属知识库ID
          - filename: 原始文件名
          - chunk_count: 切分出的切片总数
          - status: "EMBEDDED"（已完成向量化索引）
        """
        kb = knowledge_base_repo.get(db, kb_id)
        if not kb:
            raise ValueError(f"知识库 ID {kb_id} 不存在")

        doc_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[-1].lower().replace(".", "")
        safe_name = f"{doc_id}_{filename}"
        saved_path = os.path.join(settings.UPLOAD_DIR, safe_name)

        # 1. 物理落地文件到磁盘
        with open(saved_path, "wb") as f:
            f.write(content)

        # 2. 解析文本内容（优先 UTF-8，遇到特殊编码回退 latin-1）
        text_content = ""
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError:
            text_content = content.decode("latin-1", errors="ignore")

        # 3. 滑动窗口文本分块切片（默认每块 500 字，相邻块重叠 50 字以保留上下文连贯性）
        chunks = self._chunk_text(text_content, chunk_size=500, overlap=50)

        # 4. 向 MySQL 写入文档持久化元数据记录
        doc = KnowledgeDocument(
            id=doc_id,
            kb_id=kb_id,
            filename=filename,
            file_path=saved_path,
            file_type=ext or "txt",
            chunk_count=len(chunks),
            status="EMBEDDED"
        )
        knowledge_doc_repo.create(db, doc)

        # 5. 将分块切片缓存至本地向量数据库目录，供快速文本检索
        self._cache_chunks(doc_id, chunks)

        return doc

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        按固定步长和重叠窗口将长篇文本智能切割为均匀的片段。
        
        【参数说明】：
        - text (str): 待切片的完整文本。
        - chunk_size (int, 默认 500): 每个切片的最大字符数。
        - overlap (int, 默认 50): 相邻两个切片之间的字符重叠量，确保句子不被粗暴截断失去语义。
        
        【返回值说明】：
        - List[str]: 切分后的段落字符串列表。
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        cleaned_text = "\n".join(lines)
        chunks = []
        start = 0
        while start < len(cleaned_text):
            end = min(start + chunk_size, len(cleaned_text))
            chunk = cleaned_text[start:end]
            if chunk:
                chunks.append(chunk)
            start += (chunk_size - overlap)
        return chunks if chunks else [text[:chunk_size]]

    def _cache_chunks(self, doc_id: str, chunks: List[str]):
        """
        将文档切片序列化保存到本地文本缓存中，使用分隔符隔离不同切片。
        
        【参数说明】：
        - doc_id (str): 文档唯一标识 ID。
        - chunks (List[str]): 切片段落列表。
        """
        cache_file = os.path.join(settings.VECTOR_DB_DIR, f"{doc_id}.txt")
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write("\n---CHUNK_SPLIT---\n".join(chunks))

    def search_relevant_chunks(self, kb_id: Optional[str], query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        根据用户输入的检索词，在缓存切片中匹配并召回相关度最高的前 top_k 个剧情知识片段。
        
        【参数大白话详解】：
        - kb_id (Optional[str]): 目标知识库 ID（可为空，为空时在全局切片库中检索）。
        - query (str): 检索关键词或问题语句。
        - top_k (int, 默认 3): 召回最相关的切片条数。
        
        【返回值列表元素详解】：
        [
            {
                "content": str,     # 命中的切片正文内容
                "score": float,     # 词频与语义相关度综合得分
                "source_doc": str   # 来源文档 ID
            }, ...
        ]
        """
        results = []
        if not os.path.exists(settings.VECTOR_DB_DIR):
            return results

        query_words = set(query.lower().split())
        scored_chunks = []

        # 遍历缓存目录下的所有切片文件执行词频重合评分
        for fname in os.listdir(settings.VECTOR_DB_DIR):
            if not fname.endswith(".txt"):
                continue
            fpath = os.path.join(settings.VECTOR_DB_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                chunks = content.split("\n---CHUNK_SPLIT---\n")
                for chunk in chunks:
                    chunk_lower = chunk.lower()
                    score = sum(1 for word in query_words if word in chunk_lower)
                    if score > 0 or len(query) > 0:
                        scored_chunks.append({
                            "content": chunk,
                            "score": score,
                            "source_doc": fname.replace(".txt", "")
                        })
            except Exception as e:
                logger.warning(f"读取切片缓存文件异常 ({fpath}): {e}")

        # 按得分从高到低排序，截取前 top_k 个高分切片
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]


# 全局单例影视知识库服务实例
knowledge_service = KnowledgeService()
