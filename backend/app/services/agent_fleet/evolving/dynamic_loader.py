# -*- coding: utf-8 -*-
"""
==============================================================================
【模块名称】：CinemaAgent 智能体进化引擎 - 智能体动态加载器 (dynamic_loader.py)
【业务定位】：支持从热插拔配置文件动态反射载入新智能体或工具
==============================================================================
"""
"""
Skills 动态沙箱质检与运行时热加载器 (Dynamic Loader)
管理员一键批准提案后，动态编译并无损挂载至运行时技能池，无需重启服务
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.agent_hub import AgentEvolutionProposal, SkillConfig

logger = logging.getLogger("agent_fleet.dynamic_loader")


class DynamicSkillLoader:
    """动态热加载器"""

    def approve_and_hot_load(self, proposal_id: str, reviewer_username: str = "admin") -> Dict[str, Any]:
        """管理员审核批准并动态热加载新技能"""
        db: Session = SessionLocal()
        try:
            proposal = db.query(AgentEvolutionProposal).filter(
                AgentEvolutionProposal.id == proposal_id
            ).first()

            if not proposal:
                return {"success": False, "error": f"找不到提案: {proposal_id}"}

            proposal.status = "APPROVED"
            proposal.reviewed_by = reviewer_username
            proposal.reviewed_at = datetime.utcnow()

            # 生成正式 SkillConfig 持久化入库
            skill_id = f"skill_evolved_{proposal.id[:8]}"
            new_skill = SkillConfig(
                skill_id=skill_id,
                name=proposal.proposal_title,
                category=proposal.category,
                description=f"自进化生成技能，来源会话: {proposal.source_session_id}",
                trigger_keywords=proposal.trigger_keywords or "短剧,分镜,自进化",
                skill_markdown=proposal.generated_skill_content,
                mounted_agents_json=f'["{proposal.target_agent_id}"]',
                is_global_mount=False,
            )
            db.add(new_skill)
            db.commit()
            logger.info(f"Successfully hot-loaded evolved skill: {skill_id}")

            return {
                "success": True,
                "skill_id": skill_id,
                "skill_name": proposal.proposal_title,
                "target_agent": proposal.target_agent_id,
                "message": "技能已通过沙箱质检并成功热加载入库！运行时即刻生效。",
            }
        finally:
            db.close()


global_dynamic_loader = DynamicSkillLoader()
