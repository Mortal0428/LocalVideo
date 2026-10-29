import sys
sys.path.insert(0, "backend")
from app.core.database import SessionLocal
from app.models.rag_corpus import RAGEvalRun

db = SessionLocal()
runs = db.query(RAGEvalRun).all()
print(f"Total runs in DB: {len(runs)}")
for r in runs:
    print(f"ID: {r.id} | Name: {r.name} | drama_id: {r.drama_id} | drama_title: {r.drama_title} | F1: {r.f1_score}")
db.close()
