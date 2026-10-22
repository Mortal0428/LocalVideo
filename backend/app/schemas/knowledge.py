from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None

class KnowledgeDocumentOut(BaseModel):
    id: str
    kb_id: str
    filename: str
    file_type: str
    chunk_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class KnowledgeBaseOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    documents: List[KnowledgeDocumentOut] = []

    class Config:
        from_attributes = True
