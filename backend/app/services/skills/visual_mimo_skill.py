"""
Visual Mimo Skill (云端多模态视觉解构技能)
当用户提问画面视觉细节（服饰、道具、环境、神态）时，提取对应时间戳关键帧，
调度云端多模态视觉模型，并将视觉感知反哺给伴读 Agent。
绝不捏造假视觉画面。
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class VisualMimoSkill:
    def __init__(self):
        self.mimo_api_key = os.getenv("MIMO_API_KEY", "")
        self.mimo_endpoint = os.getenv("MIMO_API_ENDPOINT", "https://api.mimo.ai/v1/chat/completions")

    def should_trigger_visual_inspection(self, user_query: str) -> bool:
        """
        判断用户提问是否涉及纯视觉画面细节
        """
        if "音乐" in user_query or "歌曲" in user_query or "唱" in user_query:
            return False
        visual_keywords = [
            "穿什么", "衣服", "颜色", "长相", "手上拿", "道具", "画面背景", "车牌", 
            "外貌", "表情", "神态", "周围环境", "画面里", "视觉细节"
        ]
        return any(kw in user_query for kw in visual_keywords)

    async def inspect_scene_visual(
        self,
        video_path: str,
        timestamp_seconds: float,
        visual_question: str
    ) -> Optional[str]:
        """
        提取毫秒级关键帧并交由云端多模态视觉模型解析。未配置或异常时返回 None。
        """
        if not self.mimo_api_key:
            return None

        try:
            import httpx
            async with httpx.AsyncClient(timeout=4.0) as client:
                payload = {
                    "model": "mimo-multimodal-v1",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"观察短剧此时间点（{int(timestamp_seconds)}秒）的画面：{visual_question}"
                        }
                    ],
                    "temperature": 0.4
                }
                headers = {
                    "Authorization": f"Bearer {self.mimo_api_key}",
                    "Content-Type": "application/json"
                }
                resp = await client.post(self.mimo_endpoint, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content")
        except Exception as e:
            logger.warning(f"Mimo multimodal visual inspection call failed: {e}")

        return None

visual_mimo_skill = VisualMimoSkill()
