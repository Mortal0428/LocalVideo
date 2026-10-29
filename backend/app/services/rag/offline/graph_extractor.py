# -*- coding: utf-8 -*-
"""
==============================================================================
【模块名称】：CinemaAgent 工业级短剧知识图谱关系抽取器 (DramaGraphExtractor)
【业务定位】：从短剧剧本与分镜对白中抽取 SPO 人物关系三元组，自动写入 Neo4j 拓扑网
==============================================================================
"""

import re
import logging
from typing import List, Dict, Any, Optional
from app.services.rag.core.neo4j_client import graph_service

logger = logging.getLogger(__name__)

# 预设短剧常用关系类型词典
RELATION_PATTERNS = [
    # 情感与婚约
    (r'([^\s，。]+)\s*(?:是|为)\s*([^\s，。]+)\s*的(?:未婚妻|未婚夫|妻子|丈夫|配偶)', '婚约关系'),
    (r'([^\s，。]+)\s*(?:深爱|暗恋|倾心于|钟情于|守护)\s*([^\s，。]+)', '深情守护'),
    (r'([^\s，。]+)\s*(?:向|与)\s*([^\s，。]+)\s*(?:求婚|订婚|联姻)', '求婚订婚'),
    (r'([^\s，。]+)\s*(?:背叛|抛弃|出轨|退婚)\s*([^\s，。]+)', '背叛退婚'),

    # 亲缘血统
    (r'([^\s，。]+)\s*(?:是|为)\s*([^\s，。]+)\s*的(?:亲生女儿|亲女|生女|千金)', '亲生父女'),
    (r'([^\s，。]+)\s*(?:是|为)\s*([^\s，。]+)\s*的(?:养女|假千金|假千金养女)', '收养抱错'),
    (r'([^\s，。]+)\s*(?:是|为)\s*([^\s，。]+)\s*的(?:父亲|母亲|母亲大人|生父)', '血缘父母'),
    (r'([^\s，。]+)\s*(?:是|为)\s*([^\s，。]+)\s*的(?:哥哥|弟弟|姐姐|妹妹)', '兄弟姐妹'),

    # 敌对与打脸反转
    (r'([^\s，。]+)\s*(?:打脸|当众拆穿|惩治|揭露)\s*([^\s，。]+)', '打脸惩治'),
    (r'([^\s，。]+)\s*(?:陷害|算计|诬陷|嫉恨|谋害)\s*([^\s，。]+)', '敌对陷害'),
    (r'([^\s，。]+)\s*(?:视|把)\s*([^\s，。]+)\s*(?:为死敌|为仇敌|为眼中钉)', '宿命仇敌'),

    # 势力与道具掌控
    (r'([^\s，。]+)\s*(?:掌控|掌管|执掌|继承)\s*([^\s，。]+)', '掌控执掌'),
    (r'([^\s，。]+)\s*(?:持有|亮出|拥有|手握)\s*([^\s，。]+)', '持有道具'),
    (r'([^\s，。]+)\s*(?:效忠|效力于|投靠|归附)\s*([^\s，。]+)', '效忠从属')
]


class DramaGraphExtractor:
    """
    短剧知识图谱三元组抽取器
    """
    def __init__(self):
        pass

    def extract_triples_from_text(self, text: str) -> List[Dict[str, Any]]:
        """从剧本段落中匹配提取三元组"""
        triples = []
        if not text:
            return triples

        lines = re.split(r'[。！？\n]+', text)
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            for pattern, rel_type in RELATION_PATTERNS:
                matches = re.findall(pattern, line_str)
                for m in matches:
                    if len(m) == 2:
                        subj = self._clean_entity_name(m[0])
                        obj = self._clean_entity_name(m[1])
                        if subj and obj and subj != obj and len(subj) <= 15 and len(obj) <= 20:
                            triples.append({
                                "source": subj,
                                "relation": rel_type,
                                "target": obj,
                                "evidence": line_str[:60]
                            })
        return triples

    def _clean_entity_name(self, raw: str) -> str:
        clean = re.sub(r'^[“"‘\'（(\s]+|[”"’\'）)\s]+$', '', raw)
        clean = re.sub(r'^(?:这个|那个|这位|那位|此时|随后|只见)', '', clean)
        return clean.strip()

    def extract_and_store(
        self,
        text: str,
        drama_id: Optional[str] = None,
        custom_entities: Optional[List[Dict[str, Any]]] = None,
        custom_relations: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        全流程抽取并持久化写入 Neo4j/嵌入式图存储
        """
        all_triples = self.extract_triples_from_text(text)
        
        # 补充自定义三元组（如有）
        if custom_relations:
            for r in custom_relations:
                all_triples.append({
                    "source": r.get("source"),
                    "relation": r.get("relation") or r.get("type", "RELATED_TO"),
                    "target": r.get("target"),
                    "evidence": r.get("evidence", "自定义关系定义")
                })

        # 写入实体与关系
        seen_entities = set()
        for t in all_triples:
            s = t["source"]
            target = t["target"]
            rel = t["relation"]
            
            # 推断实体标签
            s_label = "Character"
            t_label = "Character"
            if any(kw in target for kw in ["卡", "玉佩", "文件", "鉴定", "项链", "信物"]):
                t_label = "Item"
            elif any(kw in target for kw in ["集团", "世家", "豪门", "门派", "府", "宗"]):
                t_label = "Faction"

            if s not in seen_entities:
                graph_service.add_entity(s_label, s, {"drama_id": drama_id}, drama_id=drama_id)
                seen_entities.add(s)

            if target not in seen_entities:
                graph_service.add_entity(t_label, target, {"drama_id": drama_id}, drama_id=drama_id)
                seen_entities.add(target)

            graph_service.add_relation(
                source_name=s,
                rel_type=rel,
                target_name=target,
                properties={"evidence": t.get("evidence", ""), "drama_id": drama_id},
                drama_id=drama_id
            )

        # 补充预设关键实体
        if custom_entities:
            for ent in custom_entities:
                graph_service.add_entity(
                    label=ent.get("label", "Character"),
                    name=ent.get("name"),
                    properties=ent.get("properties", {}),
                    drama_id=drama_id
                )

        logger.info(f"成功抽取并写入 {len(all_triples)} 组三元组至知识图谱 (短剧ID: {drama_id})")
        return all_triples


graph_extractor = DramaGraphExtractor()
