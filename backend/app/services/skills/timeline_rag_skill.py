# -*- coding: utf-8 -*-
"""
==============================================================================
【业务服务】：backend/app/services/skills/timeline_rag_skill.py
【业务定位】：播放器时间轴语义解构技能（TimelineRAGSkill）
【前端链路对接】：
  1. 页面来源：frontend/src/views/PlayerView.vue（短剧播放器主页面）
  2. 触发场景：
     - 场景A：用户在播放器右侧伴聊框提问（handleSendChat() -> POST /api/v1/agent/chat-stream）
       -> 调用 agent_service.py -> 调用本技能的 get_timeline_context()
     - 场景B：播放器进度条初始化高能看点（GET /api/v1/agent/highlights/{episode_id}）
       -> 播放器时间轴下方渲染高能冲突小黄点/名场面打点 -> 调用本技能的 get_highlights()
【核心功能】：
  1. 真实时间轴字幕加载（ensure_episode_subtitles）：从 video_subtitle_timeline 表读取分集每句台词；
  2. 智能局部时空语义匹配（get_timeline_context）：以观众当前播放秒数为中心，
     计算与用户提问的词频重合度、时间相近距离与高潮打标，精准召回最相关上下文；
  3. 官方高能名场面列表提取（get_highlights）：筛选带 is_climax 标记的高能台词，
     转化为带时间戳的跳转卡片数组供前端播放器快速打点。
==============================================================================
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.video import VideoEpisode, VideoSubtitleTimeline


class TimelineRAGSkill:
    """
    【时间轴语义解构技能类】
    负责分集真实台词字幕解析、时间轴对齐、语义检索与当前播放位置的上下文动态召回。
    严禁捏造虚假字幕或自动插入虚构台词。
    """
    def __init__(self):
        pass

    def ensure_episode_subtitles(self, db: Session, episode: VideoEpisode) -> List[VideoSubtitleTimeline]:
        """
        根据分集记录，从 MySQL 数据库的 `video_subtitle_timeline` 表中读取真实的时间轴台词切片。
        
        【参数说明】：
        - db (Session): 数据库会话连接。
        - episode (VideoEpisode): 分集模型实例对象（对应 video_episodes 表记录）。
        
        【返回值说明】：
        - List[VideoSubtitleTimeline]: 按台词起播时间（start_seconds）升序排列的字幕记录列表。
          若数据库中该集尚未导入字幕，则返回空列表 []，绝不无中生有编造假数据。
        """
        existing = db.query(VideoSubtitleTimeline).filter(
            VideoSubtitleTimeline.episode_id == episode.id
        ).order_by(VideoSubtitleTimeline.start_seconds.asc()).all()

        return existing or []

    def get_timeline_context(
        self,
        db: Session,
        episode_id: str,
        current_playback_time: float,
        user_query: str,
        top_k: int = 4
    ) -> Dict[str, Any]:
        """
        结合观众当前播放秒数与提问，动态检索出最相关的剧情台词上下文与即时场景。
        
        【参数大白话详解】：
        - db (Session): 数据库会话。
        - episode_id (str): 分集主键 UUID，告诉函数要查哪一集的字幕。
        - current_playback_time (float): 当前视频播放进度（单位：秒，如 125.0 代表 2分05秒），
          从前端播放器的 videoElement.currentTime 传入。
        - user_query (str): 观众在伴聊框输入的提问内容（如：“刚才男主手里拿的信写了什么？”）。
        - top_k (int, 默认 4): 最多召回的相关片段数量上限。
        
        【返回值字典结构大白话说明】：
        {
            "timeline_context": str,   # 拼接好的格式化多行台词字符串（带时间标签），直接交给 LLM 提示词
            "matched_chunks": [        # 匹配得分最高的相关片段列表，上层用于提取跳转秒数
                {
                    "start": float,      # 台词开始秒数（如 45.2）
                    "end": float,        # 台词结束秒数（如 51.0）
                    "speaker": str,      # 说话人角色名（如 "陆总"、"苏浅"）
                    "content": str,      # 台词对白文本
                    "is_climax": bool    # 是否为高能名场面
                }, ...
            ],
            "immediate_scene": {       # 当前播放时刻正好正在发生的台词片段（用于兜底跳转）
                "start": float,
                "speaker": str,
                "content": str
            } 或 None
        }
        """
        episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
        if not episode:
            return {"timeline_context": "", "matched_chunks": [], "immediate_scene": None}

        subs = self.ensure_episode_subtitles(db, episode)
        if not subs:
            return {
                "timeline_context": "本集暂无已录入的时间轴字幕切片数据，请依据剧集主题和情节背景进行推理解答。",
                "matched_chunks": [],
                "immediate_scene": None
            }

        # ----------------------------------------------------------------------
        # 步骤 1：寻找当前播放时间点切片（Immediate scene 正在发生的场景）
        # ----------------------------------------------------------------------
        immediate = None
        for s in subs:
            # 允许 5 秒缓冲，判断当前播放进度是否处于该台词区间内
            if s.start_seconds <= current_playback_time <= s.end_seconds + 5:
                immediate = s
                break

        # ----------------------------------------------------------------------
        # 步骤 2：文本关键词与局部时空多因子评分匹配
        # ----------------------------------------------------------------------
        query_words = [w for w in user_query.strip() if len(w) > 0]
        scored_chunks = []
        for s in subs:
            score = 0.0
            # 因子 A：时间局部性加权——距离当前播放秒数越近（在 40 秒窗口内），权重大幅提高 +3.0
            time_diff = abs(s.start_seconds - current_playback_time)
            if time_diff < 40:
                score += 3.0
            
            # 因子 B：字词字频重合度——台词内容或说话人名字命中提问关键字
            for char in query_words:
                if char in s.content or (s.speaker and char in s.speaker):
                    score += 1.0

            # 因子 C：名场面高能标记额外加权
            if s.is_climax:
                score += 1.5

            scored_chunks.append((score, s))

        # 按照综合得分从高到低倒序排序，截取前 top_k 个片段
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [item[1] for item in scored_chunks[:top_k]]

        # ----------------------------------------------------------------------
        # 步骤 3：格式化组装为 RAG Prompt 上下文（按台词发生先后时间排序）
        # ----------------------------------------------------------------------
        context_lines = []
        for chunk in sorted(top_chunks, key=lambda c: c.start_seconds):
            m, sec = divmod(int(chunk.start_seconds), 60)
            time_tag = f"{m:02d}:{sec:02d}"
            context_lines.append(f"[{time_tag}] {chunk.speaker}: {chunk.content}")

        return {
            "timeline_context": "\n".join(context_lines),
            "matched_chunks": [
                {
                    "start": c.start_seconds,
                    "end": c.end_seconds,
                    "speaker": c.speaker,
                    "content": c.content,
                    "is_climax": c.is_climax
                }
                for c in top_chunks
            ],
            "immediate_scene": {
                "start": immediate.start_seconds if immediate else current_playback_time,
                "speaker": immediate.speaker if immediate else "场景对峙",
                "content": immediate.content if immediate else ""
            } if immediate else None
        }

    def get_highlights(self, db: Session, episode_id: str) -> List[Dict[str, Any]]:
        """
        获取本集的官方高能冲突看点打点清单。
        
        【前端对应】：
        - 接口路由：GET /api/v1/agent/highlights/{episode_id}
        - 前端使用：PlayerView.vue 拿到后在播放器进度条轴线上打出高能标记点，
          观众鼠标悬停或点击即可查看名场面描述并一键秒级跳转。
        
        【返回值字段详解】：
        - time (float): 名场面开始秒数（播放器直接 seek 的值）
        - timeTag (str): 格式化的分秒文字（如 "01:24"）
        - title (str): 看点主标题（如 "陆总核心冲突名场面"）
        - desc (str): 剧本原汁原味台词对白
        - tag (str): 前端展示的高亮徽章标签（"高能时刻"）
        """
        episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
        if not episode:
            return []

        subs = self.ensure_episode_subtitles(db, episode)
        highlights = []
        for s in subs:
            if s.is_climax:
                m, sec = divmod(int(s.start_seconds), 60)
                time_tag = f"{m:02d}:{sec:02d}"
                highlights.append({
                    "time": s.start_seconds,
                    "timeTag": time_tag,
                    "title": f"{s.speaker}核心冲突名场面",
                    "desc": s.content,
                    "tag": "高能时刻"
                })

        return highlights


# 单例时间轴解构技能实例
timeline_skill = TimelineRAGSkill()
