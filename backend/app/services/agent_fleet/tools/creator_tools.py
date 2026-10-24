"""
Agent 5 专用解耦工具: 创作者中心宣发与运营操盘
负责提取前3秒黄金钩子、拟定爆款标题与短剧话题标签 (绝不写分镜)
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.services.agent_fleet.tools.base_tool import BaseDecoupledTool


class ViralPackagingInput(BaseModel):
    story_concept: str = Field(..., description="短剧核心故事梗概或已写好的第1镜头描述")
    genre: str = Field("都市逆袭", description="题材分类: 都市逆袭 | 高能悬疑 | 甜宠战神 | 奇幻穿越")


class ViralPackagingTool(BaseDecoupledTool):
    name = "generate_viral_packaging_tool"
    description = "专门为短剧生成前3秒吸睛视觉钩子、3版高点击率爆款标题与话题标签"
    args_schema = ViralPackagingInput
    category = "creator_growth"

    def execute(self, story_concept: str, genre: str = "都市逆袭") -> Dict[str, Any]:
        # 爆款公式算法模拟
        hook_3s = f"【前3秒致命钩子】开局0.0秒：特写皮鞋踏破水洼与染血合同，直接抛出悬念对白：‘三年之期已到，江城该变天了！’"
        titles = [
            f"《隐龙觉醒：退婚后万亿首富身份藏不住了》",
            f"《暴雨夜归来：我给前妻家族上一堂绝望必修课》",
            f"《开局被沉江，三年后我率十万暗卫踏碎豪门》",
        ]
        tags = ["#爽剧推荐", f"#{genre}", "#高能反转", "#前3秒高潮", "#下沉爆款短剧"]
        poster_advice = "建议主封面采用‘主角冷眼侧颜剪影 + 背景燃烧豪宅’冷暖对比色调，标题大字用烫金粗黑体，视觉冲击力提升 45%。"

        return {
            "golden_3s_hook": hook_3s,
            "recommended_viral_titles": titles,
            "trending_hashtags": tags,
            "poster_layout_strategy": poster_advice,
            "responsible_role": "Agent 5 (宣发与运营总监 - 关键词站岗已触发)",
        }
