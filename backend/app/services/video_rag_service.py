import logging
from typing import List, Dict, Any, Optional
from app.services.llm_gateway import llm_gateway

logger = logging.getLogger(__name__)

class VideoPlotChunk:
    def __init__(self, start_sec: float, end_sec: float, text: str, character: str = "", scene: str = ""):
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.text = text
        self.character = character
        self.scene = scene

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start_sec,
            "end": self.end_sec,
            "text": self.text,
            "character": self.character,
            "scene": self.scene
        }

class VideoRAGService:
    """
    RAG service for video plots and timeline subtitles.
    Delegates inference strictly to LLMGateway without canned fallback answers.
    """
    def __init__(self):
        self._init_knowledge_store()

    def _init_knowledge_store(self):
        # Structured knowledge index for episodes
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
        return self.episode_knowledge.get(episode_id, self.episode_knowledge["default"])

    def retrieve_relevant_chunks(self, episode_id: str, query: str, top_k: int = 2) -> List[VideoPlotChunk]:
        """Retrieve most relevant plot/dialogue chunks based on query terms."""
        chunks = self.get_chunks_for_episode(episode_id)
        if not chunks:
            return []

        scored_chunks = []
        for chunk in chunks:
            content = (chunk.text + " " + chunk.scene + " " + chunk.character).lower()
            score = 0.0
            for term in ["相遇", "初次", "初见", "什么时候", "哪一秒", "见面", "开头"]:
                if term in query.lower() and (chunk.start_sec <= 5.0 or "初遇" in chunk.scene):
                    score += 5.0
            for term in ["歌", "雨爱", "音乐", "唱", "对白", "台词"]:
                if term in query.lower() and ("歌" in chunk.text or "雨爱" in chunk.text):
                    score += 5.0
            for term in ["高能", "高潮", "甜", "好看", "精彩", "爆发"]:
                if term in query.lower() and ("高潮" in chunk.scene or "同框" in chunk.text):
                    score += 5.0
            
            # Substring matching
            for t in query.split():
                if t.lower() in content:
                    score += 2.0
                    
            scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c for score, c in scored_chunks[:top_k]]

    async def generate_companion_answer(
        self,
        episode_id: str,
        question: str,
        current_video_time: float = 0.0
    ) -> Dict[str, Any]:
        """Generate companion agent response with clickable video jump timestamps."""
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
        return [
            "两人初次相遇是在第几秒？",
            "这一集最甜的高能看点在哪里？",
            "背景音乐唱的是什么歌曲？"
        ]

video_rag_service = VideoRAGService()
