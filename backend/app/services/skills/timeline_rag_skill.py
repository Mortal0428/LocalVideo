"""
Timeline RAG Skill (时间轴语义解构技能)
负责分集台词字幕解析、时间轴对齐、语义检索与当前播放位置的上下文动态召回。
绝不捏造虚假字幕或自动插入虚构台词。
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.video import VideoEpisode, VideoSubtitleTimeline

class TimelineRAGSkill:
    def __init__(self):
        pass

    def ensure_episode_subtitles(self, db: Session, episode: VideoEpisode) -> List[VideoSubtitleTimeline]:
        """
        获取分集真实时间轴台词切片。若无数据，诚实返回空列表，绝不自动插入捏造数据。
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
        检索当前播放时间窗口（前30s ~ 后30s）与查询相关的高能台词语义切片
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

        # 1. 寻找当前播放时间切片 (Immediate scene)
        immediate = None
        for s in subs:
            if s.start_seconds <= current_playback_time <= s.end_seconds + 5:
                immediate = s
                break

        # 2. 文本关键词与语义匹配
        query_words = [w for w in user_query.strip() if len(w) > 0]
        scored_chunks = []
        for s in subs:
            score = 0.0
            # 距离当前时间越近，时间局部性权重越高
            time_diff = abs(s.start_seconds - current_playback_time)
            if time_diff < 40:
                score += 3.0
            
            # 内容词频重合评分
            for char in query_words:
                if char in s.content or (s.speaker and char in s.speaker):
                    score += 1.0

            if s.is_climax:
                score += 1.5

            scored_chunks.append((score, s))

        # 按得分从高到低排序取 top_k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [item[1] for item in scored_chunks[:top_k]]

        # 格式化组装为 RAG Prompt 上下文
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
        获取本集的官方高能冲突看点清单
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

timeline_skill = TimelineRAGSkill()
