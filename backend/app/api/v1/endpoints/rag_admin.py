"""
CinemaAgent 工业级模块化 RAG 管理中台端点 (RAG Admin Endpoints)
提供知识资产库管理、多策略分块调试、Neo4j 知识图谱状态监控、
LLM Judge 裁判持久化配置与 RAGAS 四维雷达评测大屏全套 API。
"""

import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.rag_corpus import RAGCorpus, RAGChunk, RAGEvalRun
from app.services.rag.core.neo4j_client import graph_service
from app.services.rag.core.judge_config import judge_config_mgr
from app.services.rag.core.tools_toggle_config import tools_config_mgr
from app.services.rag.core.health_probe import probe_neo4j_service, probe_llm_service
from app.services.rag.offline.chunker import chunker
from app.services.rag.offline.embedder import embedder
from app.services.rag.offline.sample_assets import seed_sample_assets, SAMPLE_DRAMA_ID
from app.services.rag.evaluation.ragas_evaluator import ragas_evaluator
from app.services.rag.online.hybrid_retriever import hybrid_retriever
from app.services.rag.online.pipeline import rag_pipeline
from app.services.rag.core.datatypes import QueryBundle

router = APIRouter()


class CreateCorpusRequest(BaseModel):
    title: str
    doc_type: str = "script"  # script, srt_subtitle, biography
    content: str
    drama_id: Optional[str] = "drama-qianjin-001"
    strategy: Optional[str] = "fixed"


class ChunkDebugRequest(BaseModel):
    text: str
    strategy: str = "fixed"
    chunk_size: int = 250
    chunk_overlap: int = 40
    episode_num: int = 1


class RunEvalRequest(BaseModel):
    name: Optional[str] = None
    max_samples: int = 20


@router.get("/stats")
def get_rag_overview_stats(db: Session = Depends(get_db)):
    """获取 RAG 知识中台大屏全局统计指标"""
    total_corpora = db.query(RAGCorpus).count()
    total_chunks = db.query(RAGChunk).count()
    total_evals = db.query(RAGEvalRun).count()
    
    # 最近一次评测跑分
    latest_eval = db.query(RAGEvalRun).order_by(RAGEvalRun.created_at.desc()).first()
    latest_score = latest_eval.f1_score if latest_eval else 0.0

    # Neo4j 连通性状态
    graph_status = graph_service.get_status()

    # 裁判配置
    judge_cfg = judge_config_mgr.get_config(db, mask_key=True)

    return {
        "code": 200,
        "data": {
            "total_corpora": total_corpora,
            "total_chunks": total_chunks,
            "total_evals": total_evals,
            "latest_eval_score": latest_score,
            "latest_eval": {
                "id": latest_eval.id,
                "name": latest_eval.name,
                "judge_model": latest_eval.judge_model,
                "faithfulness": latest_eval.faithfulness,
                "answer_relevance": latest_eval.answer_relevance,
                "context_precision": latest_eval.context_precision,
                "context_recall": latest_eval.context_recall,
                "f1_score": latest_eval.f1_score,
                "created_at": str(latest_eval.created_at)
            } if latest_eval else None,
            "graph_status": graph_status,
            "judge_config": judge_cfg,
            "tools_config": tools_config_mgr.get_config(db)
        }
    }


@router.get("/corpora")
def list_corpora(
    drama_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """查询知识库文档列表"""
    q = db.query(RAGCorpus)
    if drama_id:
        q = q.filter(RAGCorpus.drama_id == drama_id)
    items = q.order_by(RAGCorpus.created_at.desc()).limit(limit).all()

    return {
        "code": 200,
        "data": [
            {
                "id": c.id,
                "drama_id": c.drama_id,
                "title": c.title,
                "doc_type": c.doc_type,
                "chunk_count": c.chunk_count,
                "content_preview": (c.content or "")[:120],
                "created_at": str(c.created_at),
                "updated_at": str(c.updated_at)
            }
            for c in items
        ]
    }


@router.post("/corpora/init-sample")
def init_sample_drama_assets(
    force: bool = False,
    db: Session = Depends(get_db)
):
    """一键灌入《千金归来》内置示范剧本、SRT字幕及 Neo4j 图谱"""
    result = seed_sample_assets(db, force=force)
    hybrid_retriever.invalidate_cache(SAMPLE_DRAMA_ID)
    return {
        "code": 200,
        "data": result
    }


@router.post("/corpora/create")
def create_corpus(
    req: CreateCorpusRequest,
    db: Session = Depends(get_db)
):
    """新建知识文档并自动分块索引"""
    corpus = RAGCorpus(
        drama_id=req.drama_id,
        title=req.title.strip(),
        doc_type=req.doc_type,
        content=req.content.strip(),
        metadata_json=json.dumps({"strategy": req.strategy}, ensure_ascii=False)
    )
    db.add(corpus)
    db.commit()
    db.refresh(corpus)

    # 自动切片
    docs = chunker.chunk(
        text=req.content,
        strategy=req.strategy or "fixed",
        drama_id=req.drama_id
    )
    for idx, doc in enumerate(docs):
        vec = embedder.embed_text(doc.text)
        chunk_rec = RAGChunk(
            corpus_id=corpus.id,
            drama_id=req.drama_id,
            episode_num=doc.episode_num,
            start_sec=doc.start_sec,
            end_sec=doc.end_sec,
            chunk_index=idx,
            chunk_strategy=doc.chunk_strategy,
            content=doc.text,
            parent_content=doc.parent_text,
            embedding_json=json.dumps(vec),
            token_count=len(doc.text)
        )
        db.add(chunk_rec)
    
    corpus.chunk_count = len(docs)
    db.commit()
    hybrid_retriever.invalidate_cache(req.drama_id)

    return {
        "code": 200,
        "data": {
            "corpus_id": corpus.id,
            "title": corpus.title,
            "chunks_created": len(docs)
        }
    }


@router.delete("/corpora/{corpus_id}")
def delete_corpus(corpus_id: str, db: Session = Depends(get_db)):
    """删除知识库文档及其对应切片"""
    c = db.query(RAGCorpus).filter(RAGCorpus.id == corpus_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="文档不存在")

    target_drama = c.drama_id
    db.query(RAGChunk).filter(RAGChunk.corpus_id == corpus_id).delete()
    db.delete(c)
    db.commit()
    hybrid_retriever.invalidate_cache(target_drama)

    return {"code": 200, "message": "知识库文档及关联切片删除成功"}


@router.get("/chunks")
def list_chunks(
    corpus_id: Optional[str] = None,
    drama_id: Optional[str] = None,
    limit: int = 60,
    db: Session = Depends(get_db)
):
    """查询知识切片明细"""
    q = db.query(RAGChunk)
    if corpus_id:
        q = q.filter(RAGChunk.corpus_id == corpus_id)
    if drama_id:
        q = q.filter(RAGChunk.drama_id == drama_id)
    chunks = q.order_by(RAGChunk.created_at.desc()).limit(limit).all()

    return {
        "code": 200,
        "data": [
            {
                "id": ch.id,
                "corpus_id": ch.corpus_id,
                "drama_id": ch.drama_id,
                "episode_num": ch.episode_num,
                "start_sec": ch.start_sec,
                "end_sec": ch.end_sec,
                "time_tag": f"{int(ch.start_sec // 60):02d}:{int(ch.start_sec % 60):02d}",
                "chunk_strategy": ch.chunk_strategy,
                "content": ch.content,
                "parent_content": ch.parent_content,
                "token_count": ch.token_count
            }
            for ch in chunks
        ]
    }


@router.post("/chunks/debug")
def debug_chunk_strategies(req: ChunkDebugRequest):
    """在线切片策略实验与预览 (Fixed / Sliding / Sentence-Window / Parent-Child)"""
    docs = chunker.chunk(
        text=req.text,
        strategy=req.strategy,
        chunk_size=req.chunk_size,
        chunk_overlap=req.chunk_overlap,
        episode_num=req.episode_num
    )
    return {
        "code": 200,
        "data": {
            "strategy": req.strategy,
            "total_chunks": len(docs),
            "chunks": [d.to_dict() for d in docs]
        }
    }


@router.get("/graph/status")
def get_graph_status():
    """获取 Neo4j 图数据库在线连通状态与实体关系统计"""
    return {
        "code": 200,
        "data": graph_service.get_status()
    }


@router.get("/graph/subgraph")
def get_graph_subgraph(
    entity_name: Optional[str] = None,
    drama_id: Optional[str] = None,
    limit: int = 80
):
    """查询知识图谱子图或全图"""
    if entity_name and entity_name.strip():
        data = graph_service.query_entity_subgraph(entity_name.strip(), depth=2, drama_id=drama_id)
    else:
        data = graph_service.get_drama_graph(drama_id=drama_id, limit=limit)

    return {
        "code": 200,
        "data": data
    }


@router.post("/graph/reconnect")
def reconnect_neo4j():
    """主动探测并尝试重连本地 Neo4j 服务"""
    is_live = graph_service.check_connectivity(force=True)
    return {
        "code": 200,
        "data": {
            "is_connected": is_live,
            "status": graph_service.get_status()
        }
    }


@router.get("/eval/judge-config")
def get_eval_judge_config(db: Session = Depends(get_db)):
    """获取当前持久化的 LLM Judge 评测裁判配置"""
    cfg = judge_config_mgr.get_config(db, mask_key=True)
    return {
        "code": 200,
        "data": cfg
    }


@router.post("/eval/judge-config")
def save_eval_judge_config(
    new_cfg: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """更新并持久化 LLM Judge 评测裁判配置 (支持本地与独立云端大模型)"""
    saved = judge_config_mgr.save_config(db, new_cfg, updated_by="admin")
    return {
        "code": 200,
        "data": saved,
        "message": "评测裁判模型配置已持久化更新"
    }


@router.post("/eval/run")
def trigger_benchmark_evaluation(
    req: RunEvalRequest,
    db: Session = Depends(get_db)
):
    """触发 RAGAS 四维基准评测跑分"""
    result = ragas_evaluator.run_benchmark(
        db=db,
        benchmark_name=req.name,
        max_samples=req.max_samples
    )
    return {
        "code": 200,
        "data": result
    }


@router.get("/eval/history")
def list_eval_runs(limit: int = 20, db: Session = Depends(get_db)):
    """获取历史四维评测跑分记录"""
    runs = db.query(RAGEvalRun).order_by(RAGEvalRun.created_at.desc()).limit(limit).all()
    return {
        "code": 200,
        "data": [
            {
                "id": r.id,
                "name": r.name,
                "judge_model": r.judge_model,
                "faithfulness": r.faithfulness,
                "answer_relevance": r.answer_relevance,
                "context_precision": r.context_precision,
                "context_recall": r.context_recall,
                "f1_score": r.f1_score,
                "sample_count": r.sample_count,
                "latency_ms": r.latency_ms,
                "created_at": str(r.created_at)
            }
            for r in runs
        ]
    }


@router.get("/tools-config")
def get_rag_tools_config(db: Session = Depends(get_db)):
    """获取 RAG 原子检索工具、重排与反思组件的热插拔开关配置"""
    return {
        "code": 200,
        "data": tools_config_mgr.get_config(db)
    }


@router.post("/tools-config")
def save_rag_tools_config(
    new_cfg: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """更新并持久化 RAG 原子工具与智能体热插拔开关状态"""
    saved = tools_config_mgr.save_config(db, new_cfg, updated_by="admin")
    return {
        "code": 200,
        "data": saved,
        "message": "RAG 工具与智能体热插拔配置已持久化更新"
    }


@router.post("/probe/neo4j")
async def probe_neo4j_live(timeout_sec: float = 2.5):
    """独立心跳探测本地 Neo4j 连通性、连接耗时与节点关系统计 (防 504 熔断保护)"""
    res = await probe_neo4j_service(timeout_sec=timeout_sec)
    return {
        "code": 200,
        "data": res
    }


@router.post("/probe/llm")
async def probe_llm_live(
    req: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """独立心跳探测大模型底座的 HTTP 连通性与首字延迟 (防 504 熔断保护)"""
    provider = req.get("provider", "ollama")
    model_name = req.get("model_name", "deepseek-r1:1.5b")
    base_url = req.get("base_url", "http://localhost:11434")
    api_key = req.get("api_key", "")
    timeout_sec = float(req.get("timeout_sec", 4.0))

    res = await probe_llm_service(
        provider=provider,
        model_name=model_name,
        base_url=base_url,
        api_key=api_key,
        timeout_sec=timeout_sec
    )
    return {
        "code": 200,
        "data": res
    }


@router.post("/preset/import-all")
def import_all_preset_assets(
    force: bool = True,
    db: Session = Depends(get_db)
):
    """一键装载短剧标准知识库（制作规范、平台分账规则、人物关系图谱）"""
    result = seed_sample_assets(db, force=force)
    hybrid_retriever.invalidate_cache(SAMPLE_DRAMA_ID)
    return {
        "code": 200,
        "data": result,
        "message": "短剧行业标准知识资产与人物关系图谱已全量装载就绪"
    }


class PipelineTraceRequest(BaseModel):
    query: str
    drama_id: Optional[str] = "drama-qianjin-001"
    episode_num: int = 1
    current_sec: float = 60.0


class ChunkPreviewRequest(BaseModel):
    content: str
    strategy: str = "fixed"
    chunk_size: int = 250
    chunk_overlap: int = 40
    drama_id: Optional[str] = "drama-qianjin-001"
    episode_num: int = 1


@router.post("/trace/debug")
def debug_pipeline_trace(
    req: PipelineTraceRequest,
    db: Session = Depends(get_db)
):
    """可观测性沙盒：执行真实检索打点链路，返回每一步算子耗时与跳过状态"""
    bundle = QueryBundle(
        query_str=req.query.strip(),
        drama_id=req.drama_id,
        episode_num=req.episode_num,
        current_sec=req.current_sec,
        top_k=5
    )
    trace_data = rag_pipeline.trace_query(bundle, db)
    return {
        "code": 200,
        "data": trace_data
    }


@router.post("/chunk/preview")
def preview_chunk_strategy(req: ChunkPreviewRequest):
    """切片实验室：纯内存模拟分块效果与统计指标，不写入数据库"""
    docs = chunker.chunk(
        text=req.content,
        strategy=req.strategy,
        chunk_size=req.chunk_size,
        chunk_overlap=req.chunk_overlap,
        drama_id=req.drama_id,
        episode_num=req.episode_num
    )
    chunks_data = []
    total_chars = 0
    max_len = 0
    min_len = 999999 if docs else 0
    for idx, d in enumerate(docs):
        c_len = len(d.text)
        total_chars += c_len
        if c_len > max_len:
            max_len = c_len
        if c_len < min_len:
            min_len = c_len
        chunks_data.append({
            "id": f"preview-{idx+1}",
            "chunk_index": idx + 1,
            "content": d.text,
            "char_count": c_len,
            "start_sec": d.start_sec,
            "end_sec": d.end_sec,
            "time_tag": f"{int(d.start_sec // 60):02d}:{int(d.start_sec % 60):02d}",
            "strategy": d.chunk_strategy,
            "parent_content": d.parent_text
        })
    avg_len = round(total_chars / len(docs), 1) if docs else 0
    if not docs:
        min_len = 0
    return {
        "code": 200,
        "data": {
            "strategy": req.strategy,
            "total_chunks": len(docs),
            "stats": {
                "total_chunks": len(docs),
                "total_chars": total_chars,
                "avg_chunk_size": avg_len,
                "max_chunk_size": max_len,
                "min_chunk_size": min_len
            },
            "chunks": chunks_data
        }
    }

