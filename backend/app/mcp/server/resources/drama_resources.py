"""
CinemaAgent MCP 结构化只读数据源 (Resources)
向大模型提供标准化、只读、上下文注入数据
"""

import json
from app.core.database import SessionLocal
from app.models.video import Video


def get_trending_dramas_resource() -> str:
    """
    全站热播短剧 Top 5 只读数据源 (cinema://dramas/trending-top5)
    返回实时投币量与综合热度排名前 5 的短剧快照
    """
    db = SessionLocal()
    try:
        videos = (
            db.query(Video)
            .filter(Video.status != "DELETED")
            .order_by(Video.coin_count.desc(), Video.heat_score.desc())
            .limit(5)
            .all()
        )
        res = []
        for idx, v in enumerate(videos, start=1):
            res.append({
                "rank": idx,
                "video_id": v.id,
                "title": v.title,
                "category": v.category or "微短剧",
                "coin_count": v.coin_count or 0,
                "heat_score": v.heat_score or 0,
                "total_episodes": v.total_episodes or 1
            })
        return json.dumps({
            "resource_uri": "cinema://dramas/trending-top5",
            "updated_at": "实时最新",
            "top5_dramas": res
        }, ensure_ascii=False, indent=2)
    finally:
        db.close()


def get_graph_ontology_resource() -> str:
    """
    短剧剧情图谱本体结构定义 (graph://schema/ontology)
    定义实体类型与关系边语义规则
    """
    ontology = {
        "resource_uri": "graph://schema/ontology",
        "entity_types": [
            {"type": "Character", "description": "短剧登场人物角色"},
            {"type": "Faction", "description": "豪门世家/商业财团/宗门势力"},
            {"type": "KeyItem", "description": "核心剧情信物或关键道具"}
        ],
        "relation_types": [
            {"name": "ALLY_WITH", "description": "结盟/扶持关系"},
            {"name": "RIVAL_OF", "description": "死敌/商战对抗关系"},
            {"name": "SECRET_CRUSH", "description": "单向暗恋/情感纠葛"},
            {"name": "BETRAYED_BY", "description": "背叛/高能反转冲突"},
            {"name": "BELONGS_TO", "description": "归属势力门派"}
        ]
    }
    return json.dumps(ontology, ensure_ascii=False, indent=2)
