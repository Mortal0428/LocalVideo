from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeBase, KnowledgeDocument
from app.repositories.base import BaseRepository

class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    def __init__(self):
        super().__init__(KnowledgeBase)

    def get_by_name(self, db: Session, name: str) -> Optional[KnowledgeBase]:
        return db.query(KnowledgeBase).filter(KnowledgeBase.name == name).first()

class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument]):
    def __init__(self):
        super().__init__(KnowledgeDocument)

    def get_by_kb_id(self, db: Session, kb_id: str) -> List[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(KnowledgeDocument.kb_id == kb_id).all()

knowledge_base_repo = KnowledgeBaseRepository()
knowledge_doc_repo = KnowledgeDocumentRepository()
