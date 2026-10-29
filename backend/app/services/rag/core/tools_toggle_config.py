# -*- coding: utf-8 -*-
"""
==============================================================================
【模块名称】：CinemaAgent RAG 检索算子热插拔开关管理器 (ToolsToggleManager)
【业务定位】：管理中台 RAG 算法实验室的核心开关控制板，持久化于 system_configs 表
==============================================================================
"""

import json
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)

DEFAULT_TOOLS_TOGGLE_CONFIG: Dict[str, Any] = {
    # 检索通道类工具
    "enable_dense": True,
    "enable_bm25": True,
    "enable_neo4j": True,

    # 算法处理与反思类工具
    "enable_rrf": True,
    "enable_rerank": True,
    "enable_crag": True,
    "enable_self_rag": True,

    # 智能体调度类工具
    "enable_plot_companion_agent": True,
    "enable_director_jump_agent": True,

    # 超时与熔断阈值（秒）
    "step_timeout_sec": 2.0,
    "total_timeout_sec": 8.0
}


class ToolsToggleConfigManager:
    """
    RAG 工具与智能体热插拔配置管理器
    """
    CONFIG_KEY = "rag_tools_toggle_config"

    @classmethod
    def get_config(cls, db: Session) -> Dict[str, Any]:
        """获取当前工具开关配置，若不存在则持久化初始化默认值"""
        rec = db.query(SystemConfig).filter(SystemConfig.config_key == cls.CONFIG_KEY).first()
        if not rec or not rec.config_value:
            config = dict(DEFAULT_TOOLS_TOGGLE_CONFIG)
            try:
                new_rec = SystemConfig(
                    config_key=cls.CONFIG_KEY,
                    config_value=json.dumps(config, ensure_ascii=False),
                    description="RAG 原子工具与智能体生命周期热插拔开关矩阵",
                    updated_by="system"
                )
                db.add(new_rec)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"初始化 RAG 工具开关配置记录异常: {e}")
            return config

        try:
            config = json.loads(rec.config_value)
            # 补齐缺省键
            for k, v in DEFAULT_TOOLS_TOGGLE_CONFIG.items():
                if k not in config:
                    config[k] = v
        except Exception:
            config = dict(DEFAULT_TOOLS_TOGGLE_CONFIG)

        return config

    @classmethod
    def save_config(cls, db: Session, new_config: Dict[str, Any], updated_by: str = "admin") -> Dict[str, Any]:
        """保存工具开关配置并持久化写入 MySQL 数据库"""
        rec = db.query(SystemConfig).filter(SystemConfig.config_key == cls.CONFIG_KEY).first()

        existing = dict(DEFAULT_TOOLS_TOGGLE_CONFIG)
        if rec and rec.config_value:
            try:
                existing.update(json.loads(rec.config_value))
            except Exception:
                pass

        for k, v in new_config.items():
            if k in DEFAULT_TOOLS_TOGGLE_CONFIG:
                existing[k] = v

        val_str = json.dumps(existing, ensure_ascii=False)
        if rec:
            rec.config_value = val_str
            rec.updated_by = updated_by
        else:
            rec = SystemConfig(
                config_key=cls.CONFIG_KEY,
                config_value=val_str,
                description="RAG 原子工具与智能体生命周期热插拔开关矩阵",
                updated_by=updated_by
            )
            db.add(rec)

        db.commit()
        db.refresh(rec)
        return existing


tools_config_mgr = ToolsToggleConfigManager()
