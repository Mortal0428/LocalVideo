# -*- coding: utf-8 -*-
"""
==============================================================================
【模型文件】：backend/app/models/system_config.py
【业务定位】：全平台全局动态热配置表（SystemConfig）
【对应表名】：system_configs
【核心功能】：
  采用键值对（Key-Value）持久化全平台的动态配置：
  - llm_engine_config: 大模型底座热重载参数（Ollama/DeepSeek/OpenAI/Mimo 配置）
  - rag_eval_judge_config: RAG 评测裁判大模型独立配置
  - login_wallpaper_config: 登录页动态背景与沉浸式纯净壁纸开关
  支持在管理后台随时保存，无需重启后端服务毫秒级单例动态热重载！
【对应前端】：
  - 大模型底座配置：frontend/src/components/EngineSettingsModal.vue
  - 登录页动态壁纸：frontend/src/views/LoginView.vue
==============================================================================
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base

class SystemConfig(Base):
    """
    【全局动态配置 ORM 实体】
    以 key-value 方式持久化系统热配置，支持管理员在线动态修改。
    """
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增配置主键 ID")
    
    # 配置唯一键名：如 llm_engine_config, rag_eval_judge_config, login_wallpaper_config
    config_key = Column(String(64), unique=True, nullable=False, index=True, comment="配置项唯一键")
    
    # 配置正文：以 JSON 格式字符串序列化持久化各种复杂配置字典
    config_value = Column(Text, nullable=False, comment="配置正文 (通常为 JSON 格式)")
    
    # 人类可读配置说明
    description = Column(String(255), nullable=True, comment="配置说明")
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="最后更新时间")
