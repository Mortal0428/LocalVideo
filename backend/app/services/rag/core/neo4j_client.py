"""
CinemaAgent 工业级模块化 RAG 图谱服务适配层 (Neo4j Client & Embedded Fallback)
提供本地 Neo4j 官方驱动接入与嵌入式图存储自动降级双模能力。
本地 Neo4j 默认配置：bolt://localhost:7687，用户 neo4j，密码 12345678。
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
DEFAULT_NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
DEFAULT_NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")
STORAGE_GRAPH_DIR = os.path.join(os.getcwd(), "storage", "rag_graph")


class EmbeddedGraphStore:
    """
    轻量级嵌入式图存储引擎（JSON 持久化兜底）。
    当本地 Neo4j 实例处于停止状态时自动启用，实现零报错无感降级。
    """
    def __init__(self, storage_dir: str = STORAGE_GRAPH_DIR):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(self.storage_dir, "embedded_graph.json")
        self.nodes: Dict[str, Dict[str, Any]] = {}  # key: f"{label}:{name}" or name
        self.edges: List[Dict[str, Any]] = []
        os.makedirs(self.storage_dir, exist_ok=True)
        self._load_from_disk()

    def _load_from_disk(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.nodes = data.get("nodes", {})
                    self.edges = data.get("edges", [])
            except Exception as e:
                logger.warning(f"加载嵌入式图存储异常，初始化为空图: {e}")
                self.nodes = {}
                self.edges = []

    def _save_to_disk(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({"nodes": self.nodes, "edges": self.edges}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"持久化嵌入式图存储失败: {e}")

    def add_node(self, label: str, name: str, properties: Optional[Dict[str, Any]] = None, drama_id: Optional[str] = None) -> Dict[str, Any]:
        key = name.strip()
        props = properties or {}
        node = {
            "key": key,
            "name": key,
            "label": label,
            "drama_id": drama_id or props.get("drama_id", ""),
            "properties": props
        }
        self.nodes[key] = node
        self._save_to_disk()
        return node

    def add_relationship(
        self,
        source_name: str,
        rel_type: str,
        target_name: str,
        properties: Optional[Dict[str, Any]] = None,
        drama_id: Optional[str] = None
    ) -> Dict[str, Any]:
        s_key = source_name.strip()
        t_key = target_name.strip()
        props = properties or {}
        edge = {
            "source": s_key,
            "target": t_key,
            "type": rel_type.strip(),
            "drama_id": drama_id or props.get("drama_id", ""),
            "properties": props
        }
        # 避免完全重复边
        for idx, exist_e in enumerate(self.edges):
            if (exist_e["source"] == s_key and 
                exist_e["target"] == t_key and 
                exist_e["type"] == edge["type"]):
                self.edges[idx] = edge
                self._save_to_disk()
                return edge
        self.edges.append(edge)
        self._save_to_disk()
        return edge

    def query_subgraph(self, entity_name: str, depth: int = 1, drama_id: Optional[str] = None) -> Dict[str, Any]:
        name = entity_name.strip()
        matched_keys = {k for k in self.nodes.keys() if name in k}
        if not matched_keys:
            # 尝试在边中寻找
            for e in self.edges:
                if name in e["source"] or name in e["target"]:
                    matched_keys.add(e["source"])
                    matched_keys.add(e["target"])

        collected_nodes = set(matched_keys)
        collected_edges = []

        current_frontier = set(matched_keys)
        for _ in range(depth):
            next_frontier = set()
            for edge in self.edges:
                if drama_id and edge.get("drama_id") and edge["drama_id"] != drama_id:
                    continue
                s = edge["source"]
                t = edge["target"]
                if s in current_frontier or t in current_frontier:
                    collected_edges.append(edge)
                    collected_nodes.add(s)
                    collected_nodes.add(t)
                    next_frontier.add(s)
                    next_frontier.add(t)
            current_frontier = next_frontier

        nodes_data = [self.nodes.get(k, {"name": k, "label": "Entity", "properties": {}}) for k in collected_nodes]
        # 去重边
        unique_edges = []
        seen_edges = set()
        for e in collected_edges:
            sig = (e["source"], e["type"], e["target"])
            if sig not in seen_edges:
                seen_edges.add(sig)
                unique_edges.append(e)

        return {
            "nodes": nodes_data,
            "edges": unique_edges,
            "count_nodes": len(nodes_data),
            "count_edges": len(unique_edges)
        }

    def get_all(self, drama_id: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        nodes_list = []
        for n in self.nodes.values():
            if drama_id and n.get("drama_id") and n["drama_id"] != drama_id:
                continue
            nodes_list.append(n)
            if len(nodes_list) >= limit:
                break

        edges_list = []
        for e in self.edges:
            if drama_id and e.get("drama_id") and e["drama_id"] != drama_id:
                continue
            edges_list.append(e)
            if len(edges_list) >= limit:
                break

        return {
            "nodes": nodes_list,
            "edges": edges_list,
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges)
        }

    def clear(self, drama_id: Optional[str] = None):
        if drama_id:
            self.nodes = {k: v for k, v in self.nodes.items() if v.get("drama_id") != drama_id}
            self.edges = [e for e in self.edges if e.get("drama_id") != drama_id]
        else:
            self.nodes.clear()
            self.edges.clear()
        self._save_to_disk()


class GraphService:
    """
    统一知识图谱服务：
    优先直连真实本地 Neo4j 数据库 (bolt://localhost:7687)；
    若不可达则无缝降级至 EmbeddedGraphStore。
    """
    def __init__(
        self,
        uri: str = DEFAULT_NEO4J_URI,
        user: str = DEFAULT_NEO4J_USER,
        password: str = DEFAULT_NEO4J_PASSWORD
    ):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.embedded_store = EmbeddedGraphStore()
        self._is_neo4j_active = False
        self._init_neo4j_driver()

    def _init_neo4j_driver(self) -> bool:
        try:
            import neo4j
            self.driver = neo4j.GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                connection_timeout=2.0
            )
            self.driver.verify_connectivity()
            self._is_neo4j_active = True
            logger.info(f"成功连接至本地 Neo4j 图数据库: {self.uri}")
            return True
        except Exception as e:
            self._is_neo4j_active = False
            self.driver = None
            logger.info(f"本地 Neo4j 服务未连接 ({e})，系统已平滑切换至嵌入式图存储引擎。")
            return False

    def check_connectivity(self) -> bool:
        if self._is_neo4j_active and self.driver:
            try:
                self.driver.verify_connectivity()
                return True
            except Exception:
                self._is_neo4j_active = False
                return False
        return self._init_neo4j_driver()

    def get_status(self) -> Dict[str, Any]:
        is_live = self.check_connectivity()
        node_count = 0
        edge_count = 0

        if is_live and self.driver:
            try:
                with self.driver.session() as session:
                    res_nodes = session.run("MATCH (n) RETURN count(n) AS c").single()
                    res_edges = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
                    node_count = res_nodes["c"] if res_nodes else 0
                    edge_count = res_edges["c"] if res_edges else 0
            except Exception as e:
                logger.warning(f"Neo4j 统计查询异常: {e}")
                is_live = False
        
        if not is_live:
            node_count = len(self.embedded_store.nodes)
            edge_count = len(self.embedded_store.edges)

        return {
            "is_connected": is_live,
            "backend": "neo4j" if is_live else "embedded_fallback",
            "uri": self.uri,
            "user": self.user,
            "total_nodes": node_count,
            "total_edges": edge_count,
            "message": "Neo4j 图数据库在线运行中" if is_live else "Neo4j 未连通，当前处于嵌入式图存储降级模式"
        }

    def add_entity(
        self,
        label: str,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
        drama_id: Optional[str] = None
    ) -> Dict[str, Any]:
        props = properties or {}
        if drama_id:
            props["drama_id"] = drama_id
        props["name"] = name

        # 始终同步记录到嵌入式缓存，确保双向防灾
        self.embedded_store.add_node(label, name, props, drama_id)

        if self.check_connectivity() and self.driver:
            try:
                clean_label = "".join([c for c in label if c.isalnum() or c == '_']) or "Entity"
                cypher = (
                    f"MERGE (n:{clean_label} {{name: $name}}) "
                    f"SET n += $props "
                    f"RETURN n"
                )
                with self.driver.session() as session:
                    session.run(cypher, name=name, props=props)
            except Exception as e:
                logger.warning(f"Neo4j 写入实体异常，使用嵌入式兜底: {e}")

        return {"label": label, "name": name, "properties": props}

    def add_relation(
        self,
        source_name: str,
        rel_type: str,
        target_name: str,
        properties: Optional[Dict[str, Any]] = None,
        drama_id: Optional[str] = None
    ) -> Dict[str, Any]:
        props = properties or {}
        if drama_id:
            props["drama_id"] = drama_id

        self.embedded_store.add_relationship(source_name, rel_type, target_name, props, drama_id)

        if self.check_connectivity() and self.driver:
            try:
                clean_rel = "".join([c for c in rel_type if c.isalnum() or c == '_']) or "RELATED_TO"
                cypher = (
                    f"MERGE (s {{name: $s_name}}) "
                    f"MERGE (t {{name: $t_name}}) "
                    f"MERGE (s)-[r:{clean_rel}]->(t) "
                    f"SET r += $props "
                    f"RETURN r"
                )
                with self.driver.session() as session:
                    session.run(cypher, s_name=source_name, t_name=target_name, props=props)
            except Exception as e:
                logger.warning(f"Neo4j 写入关系异常，使用嵌入式兜底: {e}")

        return {"source": source_name, "type": rel_type, "target": target_name, "properties": props}

    def query_entity_subgraph(self, entity_name: str, depth: int = 1, drama_id: Optional[str] = None) -> Dict[str, Any]:
        if self.check_connectivity() and self.driver:
            try:
                safe_depth = max(1, min(int(depth), 4))
                cypher = (
                    "MATCH (start {name: $name}) "
                    f"OPTIONAL MATCH path = (start)-[r*1..{safe_depth}]-(other) "
                    "WHERE $drama_id IS NULL OR any(x IN nodes(path) WHERE x.drama_id = $drama_id) "
                    "RETURN path LIMIT 50"
                )
                with self.driver.session() as session:
                    res = session.run(cypher, name=entity_name, drama_id=drama_id)
                    nodes_map = {}
                    edges_list = []
                    seen_edges = set()
                    for record in res:
                        path = record.get("path")
                        if not path:
                            continue
                        for n in path.nodes:
                            n_props = dict(n)
                            node_key = str(n.element_id if hasattr(n, "element_id") else getattr(n, "id", ""))
                            n_name = n_props.get("name", node_key)
                            labels = list(n.labels)
                            lbl = labels[0] if labels else "Entity"
                            nodes_map[n_name] = {"name": n_name, "label": lbl, "properties": n_props}
                        for r in path.relationships:
                            s_name = dict(r.start_node).get("name", "")
                            t_name = dict(r.end_node).get("name", "")
                            sig = (s_name, r.type, t_name)
                            if sig not in seen_edges:
                                seen_edges.add(sig)
                                edges_list.append({
                                    "source": s_name,
                                    "type": r.type,
                                    "target": t_name,
                                    "properties": dict(r)
                                })
                    if nodes_map:
                        return {
                            "nodes": list(nodes_map.values()),
                            "edges": edges_list,
                            "count_nodes": len(nodes_map),
                            "count_edges": len(edges_list)
                        }
            except Exception as e:
                logger.warning(f"Neo4j 子图查询异常，切换嵌入式查询: {e}")

        return self.embedded_store.query_subgraph(entity_name, depth=depth, drama_id=drama_id)

    def get_drama_graph(self, drama_id: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        if self.check_connectivity() and self.driver:
            try:
                cypher = (
                    "MATCH (n) "
                    "WHERE $drama_id IS NULL OR n.drama_id = $drama_id "
                    "OPTIONAL MATCH (n)-[r]->(m) "
                    "RETURN n, r, m LIMIT $limit"
                )
                with self.driver.session() as session:
                    res = session.run(cypher, drama_id=drama_id, limit=limit)
                    nodes_map = {}
                    edges_list = []
                    seen_edges = set()
                    for rec in res:
                        n = rec.get("n")
                        r = rec.get("r")
                        m = rec.get("m")
                        if n:
                            n_props = dict(n)
                            n_key = str(n.element_id if hasattr(n, "element_id") else getattr(n, "id", ""))
                            n_name = n_props.get("name", n_key)
                            lbl = list(n.labels)[0] if n.labels else "Entity"
                            nodes_map[n_name] = {"name": n_name, "label": lbl, "properties": n_props}
                        if m:
                            m_props = dict(m)
                            m_key = str(m.element_id if hasattr(m, "element_id") else getattr(m, "id", ""))
                            m_name = m_props.get("name", m_key)
                            lbl_m = list(m.labels)[0] if m.labels else "Entity"
                            nodes_map[m_name] = {"name": m_name, "label": lbl_m, "properties": m_props}
                        if r and n and m:
                            s_name = dict(n).get("name", "")
                            t_name = dict(m).get("name", "")
                            sig = (s_name, r.type, t_name)
                            if sig not in seen_edges:
                                seen_edges.add(sig)
                                edges_list.append({
                                    "source": s_name,
                                    "type": r.type,
                                    "target": t_name,
                                    "properties": dict(r)
                                })
                    if nodes_map:
                        return {
                            "nodes": list(nodes_map.values()),
                            "edges": edges_list,
                            "total_nodes": len(nodes_map),
                            "total_edges": len(edges_list)
                        }
            except Exception as e:
                logger.warning(f"Neo4j 全图提取异常，切换嵌入式引擎: {e}")

        return self.embedded_store.get_all(drama_id=drama_id, limit=limit)

    def clear_drama(self, drama_id: Optional[str] = None):
        self.embedded_store.clear(drama_id=drama_id)
        if self.check_connectivity() and self.driver:
            try:
                with self.driver.session() as session:
                    if drama_id:
                        session.run("MATCH (n {drama_id: $drama_id}) DETACH DELETE n", drama_id=drama_id)
                    else:
                        session.run("MATCH (n) DETACH DELETE n")
            except Exception as e:
                logger.warning(f"Neo4j 清理图谱异常: {e}")


# 单例导出
graph_service = GraphService()
