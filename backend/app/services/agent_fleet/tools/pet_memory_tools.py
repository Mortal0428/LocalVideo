# -*- coding: utf-8 -*-
"""
==============================================================================
【模块名称】：CinemaAgent 智能体专属工具 - 灵宠空间记忆与养成工具 (pet_memory_tools.py)
【业务定位】：支持智能体读取灵宠太空舱状态、金币喂食扣减与人格切换
==============================================================================
"""
"""
Agent 2 专用解耦工具: 网页交互动态灵宠专属记忆与自我进化
独立维护每个用户的持久化记忆档案 (storage/pet_memories/user_{user_id}_memory.json)
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.agent_fleet.tools.base_tool import BaseDecoupledTool


class PetMemoryInput(BaseModel):
    user_id: str = Field(..., description="归属用户ID")
    action: str = Field("read", description="操作类型: read | update_preference | record_moment | evolve")
    new_preference: Optional[str] = Field(None, description="新记录的主人偏好，例如'喜欢都市逆袭爽剧'")
    memorable_moment: Optional[str] = Field(None, description="记录与主人的精彩陪伴瞬间")


class PetMemoryTool(BaseDecoupledTool):
    name = "manage_pet_soul_memory_tool"
    description = "读写用户专属动态灵宠独立记忆档案，持久化记录主人的观影偏好并推进灵宠自我进化"
    args_schema = PetMemoryInput
    category = "companion_pet"

    def _get_file_path(self, user_id: str) -> str:
        base_dir = os.path.join(os.getcwd(), "storage", "pet_memories")
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, f"user_{user_id}_memory.json")

    def execute(
        self,
        user_id: str,
        action: str = "read",
        new_preference: Optional[str] = None,
        memorable_moment: Optional[str] = None,
    ) -> Dict[str, Any]:
        file_path = self._get_file_path(user_id)

        # 默认档案
        data = {
            "user_id": user_id,
            "pet_name": "星瞳 (影伴小灵宠)",
            "persona": "sharp_critic",
            "growth_level": 1,
            "companion_days": 1,
            "favorite_genres": ["都市逆袭", "高能反转"],
            "disliked_tropes": ["狗血误会", "无脑降智"],
            "memorable_moments": ["首次与主人建立观影契约！"],
            "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass

        if action == "update_preference" and new_preference:
            if new_preference not in data.get("favorite_genres", []):
                data.setdefault("favorite_genres", []).append(new_preference)

        elif action == "record_moment" and memorable_moment:
            data.setdefault("memorable_moments", []).append(memorable_moment)

        elif action == "evolve":
            data["growth_level"] = data.get("growth_level", 1) + 1
            data.setdefault("memorable_moments", []).append(
                f"灵宠在主人的陪伴下成功进化至 Lv.{data['growth_level']}！解锁新动效！"
            )

        data["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # 真实持久化写回文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {
            "status": "SUCCESS",
            "memory_file": file_path,
            "pet_profile": data,
            "message": f"灵宠专属记忆已平滑同步！当前成长等级: Lv.{data['growth_level']}",
        }
