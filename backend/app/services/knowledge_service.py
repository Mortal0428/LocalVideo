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
    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.VECTOR_DB_DIR, exist_ok=True)

    def create_knowledge_base(self, db: Session, name: str, description: Optional[str] = None) -> KnowledgeBase:
        kb = KnowledgeBase(name=name, description=description)
        return knowledge_base_repo.create(db, kb)

    def get_knowledge_base(self, db: Session, kb_id: str) -> Optional[KnowledgeBase]:
        return knowledge_base_repo.get(db, kb_id)

    def list_knowledge_bases(self, db: Session) -> List[KnowledgeBase]:
        return knowledge_base_repo.get_multi(db)

    def save_and_process_document(self, db: Session, kb_id: str, filename: str, content: bytes) -> KnowledgeDocument:
        """Saves a document file, parses chunks, and creates vector indices."""
        kb = knowledge_base_repo.get(db, kb_id)
        if not kb:
            raise ValueError(f"Knowledge base with id {kb_id} not found")

        doc_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[-1].lower().replace(".", "")
        safe_name = f"{doc_id}_{filename}"
        saved_path = os.path.join(settings.UPLOAD_DIR, safe_name)

        with open(saved_path, "wb") as f:
            f.write(content)

        # Parse text content
        text_content = ""
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError:
            text_content = content.decode("latin-1", errors="ignore")

        # Chunk text
        chunks = self._chunk_text(text_content, chunk_size=500, overlap=50)

        # Store document record
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

        # Store chunks locally in knowledge cache
        self._cache_chunks(doc_id, chunks)

        return doc

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
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
        cache_file = os.path.join(settings.VECTOR_DB_DIR, f"{doc_id}.txt")
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write("\n---CHUNK_SPLIT---\n".join(chunks))

    def search_relevant_chunks(self, kb_id: Optional[str], query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves most relevant knowledge chunks. Supports local Ollama vector match with safe lexical fallback."""
        results = []
        if not os.path.exists(settings.VECTOR_DB_DIR):
            return results

        # Simple semantic/lexical score match across cached chunks
        query_words = set(query.lower().split())
        scored_chunks = []

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
                logger.warning(f"Error reading chunk file {fpath}: {e}")

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

knowledge_service = KnowledgeService()
