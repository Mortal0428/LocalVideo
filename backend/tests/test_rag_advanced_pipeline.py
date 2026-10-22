# -*- coding: utf-8 -*-
import os
import sys
import uuid
import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient

current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(current_dir, "..", "backend", "main.py")):
    backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
else:
    backend_dir = os.path.abspath(os.path.join(current_dir, ".."))

if backend_dir in sys.path:
    sys.path.remove(backend_dir)
sys.path.insert(0, backend_dir)

from main import app
from app.core.database import SessionLocal, init_db
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.rag_corpus import RAGCorpus, RAGChunk, RAGEvalRun
from app.services.rag.core.datatypes import Document, QueryBundle, CRAGResult, RAGResponse
from app.services.rag.offline.chunker import TextChunker, parse_srt_subtitles, parse_srt_time
from app.services.rag.offline.embedder import MultiModelEmbedder, cosine_similarity, compute_deterministic_fallback_embedding
from app.services.rag.core.neo4j_client import GraphService, EmbeddedGraphStore, graph_service
from app.services.rag.online.bm25_searcher import bm25_searcher
from app.services.rag.online.rrf_fusion import rrf_fusion
from app.services.rag.online.reranker import CrossEncoderReranker, reranker
from app.services.rag.online.crag_evaluator import CRAGEvaluator, crag_evaluator
from app.services.rag.online.hybrid_retriever import HybridRetriever, hybrid_retriever
from app.services.rag.online.self_rag_engine import SelfRAGEngine, self_rag_engine
from app.services.rag.online.pipeline import ModularRAGPipeline, rag_pipeline
from app.services.rag.evaluation.ragas_evaluator import RagasEvaluator, ragas_evaluator
from app.services.rag.core.judge_config import judge_config_mgr

@pytest.fixture(scope="session")
def setup_database():
    init_db()
    yield

@pytest.fixture(scope="session")
def admin_token(setup_database):
    with SessionLocal() as db:
        username = f"rag_admin_{uuid.uuid4().hex[:6]}"
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=get_password_hash("AdminPass123!"),
            nickname="RAG管理测试员",
            role="ADMIN",
            status="ACTIVE"
        )
        db.add(user)
        db.commit()
        token = create_access_token({"sub": user.id, "role": user.role})
        return token

@pytest.fixture(scope="session")
def client(setup_database):
    return TestClient(app)

class Test1ChunkerStrategies:
    """Test 4 chunking strategies: Fixed, Sliding Window, Sentence Window, Parent-Child"""

    def test_fixed_size_chunker(self):
        sample_text = "段落一：苏倾城重生归来，眼神冰冷如霜。\n段落二：陆家大堂之上，所有人都以为她还是任人欺凌的弃女。\n段落三：真相即将揭晓。"
        chunker = TextChunker()
        chunks = chunker.chunk_fixed(
            text=sample_text,
            chunk_size=35,
            chunk_overlap=5,
            episode_num=1,
            drama_id="test_drama"
        )
        assert len(chunks) >= 2
        for chunk in chunks:
            assert isinstance(chunk, Document)
            assert chunk.chunk_strategy == "fixed"
            assert chunk.text is not None
            assert len(chunk.text) > 0

    def test_sliding_window_chunker(self):
        sample_text = "第一幕开始。第二幕展开。第三幕冲突高潮。第四幕真相揭晓。第五幕大结局完结。"
        chunker = TextChunker()
        chunks = chunker.chunk_sliding_window(
            text=sample_text,
            window_size=20,
            step_size=10,
            episode_num=1,
            drama_id="test_drama"
        )
        assert len(chunks) >= 2
        for chunk in chunks:
            assert chunk.chunk_strategy == "sliding_window"

    def test_sentence_window_with_srt(self):
        srt_content = """1
00:00:01,200 --> 00:00:03,500
苏倾城回到顾家大宅。

2
00:00:04,100 --> 00:00:07,800
顾夜白冷漠地注视着来访者。

3
00:00:08,200 --> 00:00:11,500
合同签署完毕，真相即将大白。
"""
        chunker = TextChunker()
        chunks = chunker.chunk_sentence_window(
            text=srt_content,
            episode_num=1,
            drama_id="test_drama"
        )
        assert len(chunks) >= 3
        first_chunk = chunks[0]
        assert first_chunk.chunk_strategy == "sentence_window"
        assert first_chunk.start_sec == pytest.approx(1.2, abs=0.1)
        assert first_chunk.end_sec == pytest.approx(3.5, abs=0.1)
        assert "00:01" in first_chunk.time_tag

    def test_parent_child_chunker(self):
        long_text = "苏家产业庞大，分布于全国各地。\n" * 15
        chunker = TextChunker()
        chunks = chunker.chunk_parent_child(
            text=long_text,
            parent_size=150,
            child_size=40,
            episode_num=1,
            drama_id="test_drama"
        )
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.chunk_strategy == "parent_child"
            assert chunk.parent_text is not None
            assert len(chunk.parent_text) >= len(chunk.text)

    def test_composite_punctuation_handling(self):
        sample_text = "苏倾城真的离开了吗？！\n是的，她已经启程了。"
        chunker = TextChunker()
        chunks = chunker.chunk_sentence_window(sample_text, episode_num=1)
        texts = [c.text for c in chunks]
        assert any("苏倾城真的离开了吗？！" in t for t in texts)
        assert not any(t == "？！" for t in texts)

class Test2MultiModelEmbedder:
    """Test embedding dims, resilient hash fallback, and cosine similarity"""

    def test_embed_and_similarity(self):
        embedder = MultiModelEmbedder()
        t1 = "苏倾城发誓让仇人付出代价"
        t2 = "顾夜白在商界叱咤风云"
        t3 = "苏倾城决定向陆家展开复仇"

        emb1 = embedder.embed_text(t1)
        emb2 = embedder.embed_text(t2)
        emb3 = embedder.embed_text(t3)

        assert len(emb1) == 384
        assert len(emb2) == 384
        assert len(emb3) == 384

        sim_rel = cosine_similarity(emb1, emb3)
        sim_diff = cosine_similarity(emb1, emb2)
        assert -1.0 <= sim_rel <= 1.0
        assert -1.0 <= sim_diff <= 1.0
        assert sim_rel >= sim_diff

    def test_deterministic_fallback(self):
        v1 = compute_deterministic_fallback_embedding("短剧测试片段A", dim=384)
        v2 = compute_deterministic_fallback_embedding("短剧测试片段A", dim=384)
        assert v1 == v2
        assert len(v1) == 384

class Test3GraphStorageAndFallback:
    """Test GraphService, real Neo4j or Embedded fallback query and storage"""

    def test_graph_triple_and_subgraph(self):
        gs = graph_service
        assert gs is not None

        # Add entity & relation
        gs.add_entity("Character", "苏倾城_测试", {"alias": "千金"}, drama_id="drama_test")
        gs.add_entity("Character", "陆云峰_测试", {"alias": "反派"}, drama_id="drama_test")
        gs.add_relation(
            source_name="苏倾城_测试",
            rel_type="ENEMIES_WITH",
            target_name="陆云峰_测试",
            properties={"conflict": "夺回家族股份"},
            drama_id="drama_test"
        )

        subgraph = gs.query_entity_subgraph("苏倾城_测试", depth=1)
        assert "nodes" in subgraph
        assert "edges" in subgraph
        node_names = [n["name"] for n in subgraph["nodes"]]
        assert "苏倾城_测试" in node_names

        status = gs.get_status()
        assert "backend" in status
        assert "total_nodes" in status

    def test_embedded_store_direct(self):
        store = EmbeddedGraphStore()
        store.add_node("Character", "顾夜白_E", {"alias": "商界帝王"})
        store.add_node("Character", "苏倾城_E", {"alias": "千金归来"})
        store.add_relationship("顾夜白_E", "MARRIED_TO", "苏倾城_E", {"episode": 2})

        subgraph = store.query_subgraph("顾夜白_E", depth=1)
        assert len(subgraph["nodes"]) >= 2
        assert len(subgraph["edges"]) >= 1

class Test4HybridRetrieverAndAntiSpoiling:
    """Test 3-way recall and anti-spoiling temporal gate"""

    def test_anti_spoiling_gate(self):
        retriever = HybridRetriever()
        bundle = QueryBundle(
            query_str="苏倾城和顾夜白后来怎样了？",
            drama_id="sample_drama",
            episode_num=1,
            current_sec=60.0
        )

        # Future episode -> Spoiling
        assert retriever._check_anti_spoiling(ep_num=2, start_sec=10.0, bundle=bundle) is False

        # Same episode, beyond current_sec + 20s -> Spoiling
        assert retriever._check_anti_spoiling(ep_num=1, start_sec=180.0, bundle=bundle) is False

        # Same episode, prior to current_sec + 20s -> Allowed
        assert retriever._check_anti_spoiling(ep_num=1, start_sec=45.0, bundle=bundle) is True

    def test_anti_spoiling_at_zero_seconds(self):
        retriever = HybridRetriever()
        bundle = QueryBundle(
            query_str="顾夜白退婚了吗？",
            drama_id="sample_drama",
            episode_num=1,
            current_sec=0.0
        )
        # At second 0.0, spoiler at 120s in ep 1 must be blocked
        assert retriever._check_anti_spoiling(ep_num=1, start_sec=120.0, bundle=bundle) is False
        # Chunks within first 20 seconds are allowed
        assert retriever._check_anti_spoiling(ep_num=1, start_sec=10.0, bundle=bundle) is True
        # Future episode is blocked
        assert retriever._check_anti_spoiling(ep_num=2, start_sec=5.0, bundle=bundle) is False

    def test_bm25_empty_and_whitespace_docs(self):
        docs = [
            Document(id="e1", text="..."),
            Document(id="e2", text="   "),
            Document(id="e3", text="！？")
        ]
        # Must not raise ZeroDivisionError
        bm25_searcher.index_documents(docs, drama_id="empty_test_drama")
        res = bm25_searcher.search("测试", drama_id="empty_test_drama")
        assert isinstance(res, list)

    def test_hybrid_retriever_execution(self):
        with SessionLocal() as db:
            bundle = QueryBundle(
                query_str="苏倾城身世之谜",
                drama_id="drama_qianjin_sample",
                episode_num=1,
                current_sec=120.0
            )
            docs, crag_res, graph_entities = hybrid_retriever.retrieve(bundle, db)
            assert isinstance(docs, list)
            assert isinstance(crag_res, CRAGResult)
            assert isinstance(graph_entities, list)
            for d in docs:
                assert isinstance(d, Document)

class Test5RerankerAndCRAG:
    """Test CrossEncoderReranker and CRAGEvaluator correctness"""

    def test_cross_encoder_rerank(self):
        reranker = CrossEncoderReranker()
        query = "苏倾城身世真相"
        docs = [
            Document(id="d1", text="无关的花絮和背景乐介绍", score=0.3, episode_num=1),
            Document(id="d2", text="苏倾城身世真相其实是京城苏氏唯一的真千金", score=0.4, episode_num=1)
        ]
        reranked = reranker.rerank(query=query, documents=docs, top_k=2)
        assert len(reranked) == 2
        assert reranked[0].id == "d2"

    def test_crag_evaluator(self):
        evaluator = CRAGEvaluator()
        query = "苏倾城身世"
        docs = [
            Document(id="d1", text="苏倾城的身世在第1集揭露，是苏家真正的大小姐", score=0.8),
            Document(id="d2", text="苏倾城身份被顾夜白确认", score=0.75)
        ]
        crag_res = evaluator.evaluate(query=query, documents=docs)
        assert isinstance(crag_res, CRAGResult)
        assert crag_res.action in ["CORRECT", "AMBIGUOUS", "INCORRECT"]
        assert 0.0 <= crag_res.confidence_score <= 1.0

class Test6SelfRAGAndPipeline:
    """Test SelfRAGGenerator and ModularRAGPipeline sync and streaming"""

    def test_self_rag_gating(self):
        engine = SelfRAGEngine()
        assert engine.evaluate_retrieval_need("你好") is False
        assert engine.evaluate_retrieval_need("在吗？") is False
        assert engine.evaluate_retrieval_need("你好，在吗？") is False
        assert engine.evaluate_retrieval_need("介绍一下你自己") is False
        assert engine.evaluate_retrieval_need("苏倾城为什么会回到顾家？") is True

    def test_context_anchoring(self):
        engine = SelfRAGEngine()
        docs = [
            Document(
                id="doc_srt1",
                text="苏倾城冷笑道：'你们欠我的，今天都要一笔笔算清！'",
                episode_num=1,
                start_sec=45.0,
                end_sec=50.0,
                score=0.85
            )
        ]
        context, anchors, best = engine.compress_and_anchor_context(docs)
        assert "苏倾城冷笑" in context
        assert len(anchors) >= 1
        assert anchors[0]["time_tag"] == "00:45"
        assert best is not None
        assert best["timestamp"] == 45.0

    def test_pipeline_sync_query(self):
        with SessionLocal() as db:
            bundle = QueryBundle(
                query_str="苏倾城为什么回来？",
                drama_id="drama_qianjin_sample",
                episode_num=1,
                current_sec=60.0
            )
            resp = rag_pipeline.query(bundle, db)
            assert isinstance(resp, RAGResponse)
            assert resp.query == "苏倾城为什么回来？"
            assert resp.answer is not None
            assert isinstance(resp.time_anchors, list)

    def test_pipeline_stream_query(self):
        async def _run():
            with SessionLocal() as db:
                bundle = QueryBundle(
                    query_str="顾夜白对苏倾城是什么态度？",
                    drama_id="drama_qianjin_sample",
                    episode_num=1,
                    current_sec=60.0
                )
                events = []
                async for evt in rag_pipeline.query_stream(bundle, db):
                    events.append(evt)
                return events

        events = asyncio.run(_run())
        assert len(events) >= 1
        types = [e.get("type") for e in events]
        assert "done" in types

    def test_pipeline_async_aquery(self):
        async def _test():
            with SessionLocal() as db:
                bundle = QueryBundle(
                    query_str="苏倾城的父亲是谁？",
                    drama_id="drama_qianjin_sample",
                    episode_num=1,
                    current_sec=60.0
                )
                resp = await rag_pipeline.aquery(bundle, db)
                assert isinstance(resp, RAGResponse)
                assert resp.answer is not None
                assert len(resp.answer) > 0
                return resp
        res = asyncio.run(_test())
        assert res.query == "苏倾城的父亲是谁？"

class Test7RagasEvaluatorAndJudgeConfig:
    """Test Ragas golden benchmark run and persistent judge config"""

    def test_judge_config_persistence(self):
        with SessionLocal() as db:
            cfg = judge_config_mgr.get_config(db)
            assert "mode" in cfg
            assert "local" in cfg
            assert "cloud" in cfg

            updated = judge_config_mgr.save_config(db, {
                "mode": "local",
                "local": {
                    "provider": "ollama",
                    "model_name": "deepseek-r1:1.5b",
                    "base_url": "http://localhost:11434"
                },
                "temperature": 0.1
            })
            assert updated["temperature"] == 0.1

    def test_ragas_evaluation_benchmark(self):
        with SessionLocal() as db:
            result = ragas_evaluator.run_benchmark(db, max_samples=3)
            assert "id" in result
            assert "f1_score" in result
            assert "faithfulness" in result
            assert "answer_relevance" in result
            assert "context_precision" in result
            assert "context_recall" in result
            assert 0.0 <= result["f1_score"] <= 1.0

            # Verify in DB
            db_run = db.query(RAGEvalRun).filter_by(id=result["id"]).first()
            assert db_run is not None
            assert db_run.f1_score == result["f1_score"]

class Test8RAGAdminEndpoints:
    """Test FastAPI RAG admin management endpoints"""

    def test_admin_stats(self, client, admin_token):
        resp = client.get("/api/v1/rag-admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        data = body["data"]
        assert "total_corpora" in data
        assert "total_chunks" in data
        assert "graph_status" in data

    def test_admin_corpora_list(self, client, admin_token):
        resp = client.get("/api/v1/rag-admin/corpora", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert isinstance(body["data"], list)

    def test_admin_judge_config_get_and_post(self, client, admin_token):
        get_res = client.get("/api/v1/rag-admin/eval/judge-config", headers={"Authorization": f"Bearer {admin_token}"})
        assert get_res.status_code == 200
        current = get_res.json()["data"]
        assert "mode" in current

        update_payload = {
            "mode": "local",
            "local": {
                "provider": "ollama",
                "model_name": "deepseek-r1:1.5b",
                "base_url": "http://localhost:11434"
            },
            "temperature": 0.05
        }
        post_res = client.post("/api/v1/rag-admin/eval/judge-config", json=update_payload, headers={"Authorization": f"Bearer {admin_token}"})
        assert post_res.status_code == 200
        assert post_res.json()["data"]["temperature"] == 0.05

    def test_admin_neo4j_status(self, client, admin_token):
        resp = client.get("/api/v1/rag-admin/graph/status", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "is_connected" in data
        assert "backend" in data

    def test_admin_benchmark_history(self, client, admin_token):
        resp = client.get("/api/v1/rag-admin/eval/history", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert isinstance(body["data"], list)

    def test_agent_chat_with_rag_endpoint(self, client):
        resp = client.post("/api/v1/agent/chat", json={
            "episode_id": "drama-qianjin-001",
            "question": "苏倾城的父亲是谁？",
            "current_video_time": 30.0
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert "response" in body["data"]
        assert len(body["data"]["response"]) > 0
