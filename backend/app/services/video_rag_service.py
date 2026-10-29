# -*- coding: utf-8 -*-
"""
==============================================================================
【业务服务】：backend/app/services/video_rag_service.py
【业务定位】：短剧剧情切片检索与台词高能定位服务（VideoRAGService）
【前端链路对接】：
  1. 页面来源：frontend/src/views/PlayerView.vue（短剧播放器右侧剧情问答面板）
  2. 触发链路：
     - 用户在播放器伴聊框点击快捷预设问题（快捷气泡）或输入剧情提问；
     - 前端调用 POST /api/v1/agent/chat（进入 backend/app/api/endpoints/agent.py）；
     - 路由函数调用 video_rag_service.generate_companion_answer()；
     - 拿到结果后，前端渲染回答正文以及带高亮下划线的时间跳转标签（如 [00:12 跳转]），观众点击后视频播放器立刻跳转到对应秒数。
【核心功能】：
  1. 剧情片段细粒度切片建模（VideoPlotChunk）：管理包含起止秒数、台词对白与人物角色的时间胶囊；
  2. 语义与关键词召回（retrieve_relevant_chunks）：根据观众提问，快速定位剧本中最匹配的情节发生时刻；
  3. 伴读回答生成（generate_companion_answer）：组装剧情上下文并调用 LLMGateway 生成带可跳转时间戳的解说。
==============================================================================
"""

import logging
from typing import List, Dict, Any, Optional
from app.services.llm_gateway import llm_gateway

logger = logging.getLogger(__name__)


class VideoPlotChunk:
    """
    【短剧剧情细粒度切片数据结构】
    将一集短剧按情节高潮、对话场景拆解为一段段携带时间戳的剧情切片。
    """
    def __init__(self, start_sec: float, end_sec: float, text: str, character: str = "", scene: str = ""):
        self.start_sec = start_sec      # 切片开始秒数（如 12.0）
        self.end_sec = end_sec          # 切片结束秒数（如 28.0）
        self.text = text                # 切片台词或情节描述
        self.character = character      # 登场角色或对白主体
        self.scene = scene              # 场景名或高能看点标题（如 "高潮：两人同框与情感顶峰"）

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典格式供前端展示与 JSON 传输"""
        return {
            "start": self.start_sec,
            "end": self.end_sec,
            "text": self.text,
            "character": self.character,
            "scene": self.scene
        }


class VideoRAGService:
    """
    【短剧剧情 RAG 检索与伴读服务】
    管理剧情分片知识库，根据观众提问执行两阶段检索，
    并将推理任务严格交付单例 LLMGateway，生成包含精准跳转时间戳的剧情问答。
    """
    def __init__(self):
        self._init_knowledge_store()

    def _init_knowledge_store(self):
        """初始化剧集结构化剧情切片索引知识库（包含默认剧目高能片段）"""
        self.episode_knowledge: Dict[str, List[VideoPlotChunk]] = {
            "default": [
                VideoPlotChunk(
                    start_sec=0.0,
                    end_sec=4.0,
                    text="开场前奏渐起，蓝调舞台光束汇聚，两位主角在聚光灯下初次相遇凝视，拉开序幕。",
                    character="主角初遇",
                    scene="序章：舞台光影初遇"
                ),
                VideoPlotChunk(
                    start_sec=4.0,
                    end_sec=12.0,
                    text="抒情独唱段落《雨爱》响起：窗外的天气，就像是刚下过雨的星期天，光线柔和交织。",
                    character="深情独唱",
                    scene="看点：经典对白与歌声初现"
                ),
                VideoPlotChunk(
                    start_sec=12.0,
                    end_sec=28.0,
                    text="合唱高潮情感爆发，两人同台互动合唱，眼神交汇，现场氛围与甜度推至最高峰。",
                    character="高潮合唱",
                    scene="高能：两人同框与情感顶峰"
                ),
                VideoPlotChunk(
                    start_sec=28.0,
                    end_sec=45.0,
                    text="尾声余音绕梁，两人默契鞠躬，掌声雷动，留给观众无尽的回味与悬念。",
                    character="谢幕尾声",
                    scene="尾声：经典定格与谢幕"
                )
            ]
        }

    def get_chunks_for_episode(self, episode_id: str) -> List[VideoPlotChunk]:
        """
        获取指定分集的全部剧情切片，若无独立配置则返回默认标准切片集。
        
        【参数说明】：
        - episode_id (str): 分集主键 ID。
        """
        return self.episode_knowledge.get(episode_id, self.episode_knowledge["default"])

    def retrieve_relevant_chunks(self, episode_id: str, query: str, top_k: int = 2) -> List[VideoPlotChunk]:
        """
        根据观众提问匹配召回最相符的剧情对白切片。
        
        【参数大白话详解】：
        - episode_id (str): 分集 ID。
        - query (str): 观众输入的提问内容（例如：“两人是什么时候相遇的？”、“最甜的名场面在哪？”）。
        - top_k (int, 默认 2): 返回匹配得分最高的前 k 个切片。
        
        【返回值说明】：
        - List[VideoPlotChunk]: 匹配到的剧情切片列表，按相关度得分从高到低排序。
        """
        chunks = self.get_chunks_for_episode(episode_id)
        if not chunks:
            return []

        scored_chunks = []
        for chunk in chunks:
            content = (chunk.text + " " + chunk.scene + " " + chunk.character).lower()
            score = 0.0
            # 规则 A：初遇/相遇意图加权
            for term in ["相遇", "初次", "初见", "什么时候", "哪一秒", "见面", "开头"]:
                if term in query.lower() and (chunk.start_sec <= 5.0 or "初遇" in chunk.scene):
                    score += 5.0
            # 规则 B：音乐/歌词意图加权
            for term in ["歌", "雨爱", "音乐", "唱", "对白", "台词"]:
                if term in query.lower() and ("歌" in chunk.text or "雨爱" in chunk.text):
                    score += 5.0
            # 规则 C：高能名场面意图加权
            for term in ["高能", "高潮", "甜", "好看", "精彩", "爆发"]:
                if term in query.lower() and ("高潮" in chunk.scene or "同框" in chunk.text):
                    score += 5.0
            
            # 规则 D：分词子串匹配加权
            for t in query.split():
                if t.lower() in content:
                    score += 2.0
                    
            scored_chunks.append((score, chunk))

        # 按得分从高到低排序取前 top_k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c for score, c in scored_chunks[:top_k]]

    async def generate_companion_answer(
        self,
        episode_id: str,
        question: str,
        current_video_time: float = 0.0
    ) -> Dict[str, Any]:
        """
        生成带有可点击视频跳转时间戳的伴读问答回复。
        
        【参数大白话详解】：
        - episode_id (str): 分集主键 ID。
        - question (str): 观众输入的提问。
        - current_video_time (float, 默认 0.0): 观众当前的播放进度秒数。
        
        【返回值字典结构详解】：
        {
            "answer": str,          # 大模型输出的解说回答正文（包含形如 [00:12 跳转] 的时间标记）
            "target_time": float,   # 推荐跳转的最佳秒数（如 12.0），前端播放器调用 video.currentTime = target_time
            "time_tag": str,        # 格式化的时间文本（如 "00:12"）
            "scene": str,           # 场景名称（如 "高能：两人同框与情感顶峰"）
            "matched_chunks": list  # 召回的相关切片列表字典格式
        }
        """
        matched_chunks = self.retrieve_relevant_chunks(episode_id, question)
        if not matched_chunks:
            all_chunks = self.get_chunks_for_episode(episode_id)
            matched_chunks = all_chunks[:1] if all_chunks else []

        if matched_chunks:
            best_chunk = matched_chunks[0]
            jump_sec = best_chunk.start_sec
            scene_name = best_chunk.scene
            chunk_text = best_chunk.text
        else:
            jump_sec = current_video_time
            scene_name = "当前情节"
            chunk_text = "根据全剧背景与剧情脉络展开分析"

        m = int(jump_sec // 60)
        s = int(jump_sec % 60)
        time_tag = f"{m:02d}:{s:02d}"

        prompt = (
            f"你是一个沉浸式短剧智能伴读 Agent。根据以下剧集片段信息回答用户的问题。\n"
            f"剧集关键片段: {scene_name} (秒数: {time_tag}, 内容: {chunk_text})\n"
            f"用户问题: {question}\n"
            f"请简明扼要地回答，并带上精准跳转提示 '[{time_tag} 跳转]'。"
        )

        res = await llm_gateway.generate(prompt=prompt)
        answer_text = res.get("content", "")

        return {
            "answer": answer_text,
            "target_time": jump_sec,
            "time_tag": time_tag,
            "scene": scene_name,
            "matched_chunks": [c.to_dict() for c in matched_chunks]
        }

    def get_quick_prompts(self, episode_id: str) -> List[str]:
        """
        获取播放器伴聊输入框下方的预设快捷提问胶囊推荐。
        
        【返回值说明】：
        - List[str]: 3 条高频提问文本，前端渲染在伴聊抽屉下方，观众点击直接触发提问。
        """
        return [
            "两人初次相遇是在第几秒？",
            "这一集最甜的高能看点在哪里？",
            "背景音乐唱的是什么歌曲？"
        ]


# 全局单例剧情检索服务实例
video_rag_service = VideoRAGService()
