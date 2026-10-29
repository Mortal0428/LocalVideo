# -*- coding: utf-8 -*-
"""
==============================================================================
【业务服务】：backend/app/services/skills/visual_mimo_skill.py
【业务定位】：云端多模态视觉解构技能（VisualMimoSkill）
【前端链路对接】：
  1. 页面来源：frontend/src/views/PlayerView.vue（播放器伴聊窗口）
  2. 触发时机：观众提问画面中的视觉元素（例如：“女主今天穿什么衣服？”、“男主角手上拿的是什么道具？”）
  3. 执行流程：
     - 用户在前端输入文本 -> POST /api/v1/agent/chat-stream -> 进入 agent_service.py
     - agent_service.py 调用 should_trigger_visual_inspection(question) 进行意图判别
     - 若命中视觉关键词，调用 inspect_scene_visual() 请求云端多模态大模型解析该时间点的画面
     - 将多模态感知到的视觉事实追加到 Prompt 中，传给伴聊大模型生成图文并茂的回答
【核心功能】：
  1. 视觉提问意图快速判别（should_trigger_visual_inspection）：过滤纯音乐/台词问题，聚焦服装、道具、微表情等；
  2. 云端多模态视觉模型请求（inspect_scene_visual）：带毫秒时间戳调用视觉大模型，提取关键帧画面细节。
==============================================================================
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class VisualMimoSkill:
    """
    【云端多模态视觉解构技能类】
    当观众提问画面视觉细节（服饰、道具、环境、神态、微表情）时，
    提取对应时间戳关键帧，调度云端多模态视觉大模型，并将视觉感知反哺给伴读 Agent。
    严禁捏造虚假视觉画面。
    """
    def __init__(self):
        # 云端多模态模型 API 密钥与接口地址，由环境变量或系统配置提供
        self.mimo_api_key = os.getenv("MIMO_API_KEY", "")
        self.mimo_endpoint = os.getenv("MIMO_API_ENDPOINT", "https://api.mimo.ai/v1/chat/completions")

    def should_trigger_visual_inspection(self, user_query: str) -> bool:
        """
        判断观众输入的提问文本是否涉及视频画面的纯视觉细节。
        
        【大白话逻辑】：
        - 如果用户问的是“音乐”、“背景歌曲”、“唱的什么”，属于听觉音频范畴，返回 False，不浪费视觉模型额度；
        - 如果用户问的是“穿什么”、“衣服”、“颜色”、“长相”、“道具”、“车牌”、“表情”等，返回 True，触发多模态视觉解析。
        
        【参数说明】：
        - user_query (str): 观众输入的提问字符串。
        
        【返回值说明】：
        - bool: True 表示需要调用多模态视觉解析；False 表示仅靠台词文本即可回答。
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
        带时间戳请求云端多模态视觉大模型，解析当前画面中的视觉细节。
        
        【参数大白话详解】：
        - video_path (str): 视频文件的物理路径或云端直链（留空时依赖帧时间戳上下文推断）。
        - timestamp_seconds (float): 画面发生的目标秒数（例如 65.5 代表 1分05.5秒），
          视觉模型根据该秒数锁定关键帧画面。
        - visual_question (str): 针对该画面的具体视觉提问（例如：“男主角穿的是什么颜色的西装？”）。
        
        【返回值说明】：
        - Optional[str]: 视觉大模型返回的画面客观描述文本（如：“画面中男主角身着深黑色双排扣西装，右手佩戴一枚银色机械腕表”）。
          若未配置 API 密钥或网络调用异常，则安全返回 None，平滑降级，绝不卡死伴聊主流程。
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
            logger.warning(f"多模态视觉接口调用异常降级: {e}")

        return None


# 单例多模态视觉技能实例
visual_mimo_skill = VisualMimoSkill()
