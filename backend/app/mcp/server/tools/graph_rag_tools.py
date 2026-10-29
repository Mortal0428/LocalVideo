"""
CinemaAgent MCP 剧情图谱与人物关系领域工具
基于 Neo4j 知识图谱 (与嵌入式图存储降级) 查询人物实体与情感/冲突网络
"""

from typing import Dict, Any, Optional
from app.services.rag.core.neo4j_client import graph_service


async def mcp_query_character_relations(
    character_name: str,
    drama_title: Optional[str] = None,
    depth: int = 2
) -> Dict[str, Any]:
    """
    查询短剧知识图谱，提取人物之间的'恩怨、暗恋、结盟、背叛'等实体关系三元组路径。

    Args:
        character_name: 人物角色名称（如 '沈清霜', '陆沉', '林薇'）
        drama_title: 短剧名称（可选，用于圈定剧目范围）
        depth: 关系遍历深度 (1~3)
    """
    if not character_name or not character_name.strip():
        return {
            "status": "ERROR",
            "message": "角色名称不能为空"
        }

    c_name = character_name.strip()
    safe_depth = max(1, min(3, depth))

    try:
        subgraph = graph_service.query_subgraph(
            entity_name=c_name,
            depth=safe_depth
        )

        nodes = subgraph.get("nodes", [])
        edges = subgraph.get("edges", [])

        # 整理为人机友好的结构化三元组摘要
        triples = []
        for e in edges:
            triples.append({
                "source": e.get("source"),
                "relation": e.get("type"),
                "target": e.get("target"),
                "attributes": e.get("properties", {})
            })

        return {
            "status": "SUCCESS",
            "target_character": c_name,
            "connected_entities_count": len(nodes),
            "relation_triples_count": len(triples),
            "triples": triples,
            "entities": [n.get("name") for n in nodes if n.get("name")]
        }
    except Exception as e:
        return {
            "status": "FALLBACK",
            "target_character": c_name,
            "message": f"图谱遍历受限: {e}",
            "triples": []
        }
