# -*- coding: utf-8 -*-
"""
==============================================================================
【模块名称】：CinemaAgent RAG 裁判模型持久化管理器 (LLM Judge Config)
【业务定位】：为 RAG 知识评测跑分大屏（雷达图）配置专属的裁判打分大模型
【全链路调用位置】：
  管理中台 -> POST /api/v1/rag-admin/judge/config (endpoints/rag_admin.py) -> 本模块 save_config()
【核心机制】：
  1. 双模自由切换：支持选择本地 Ollama 裁判（完全免费离线）或云端独立裁判（如 DeepSeek-R1 / 通义千问 / MiMo）；
  2. 数据库持久化：保存在 MySQL system_configs 表的 rag_eval_judge_config 键中，重启不丢失；
  3. API 密钥脱敏：前端读取时自动将密钥中间部分替换为 ***，防止敏感信息泄露。
==============================================================================
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)

DEFAULT_PROVIDERS = {
    "mimo": {
        "name": "小米 MiMo 官方 API",
        "base_url": "https://api.xiaomimimo.com/v1",
        "default_model": "mimo-v2.5-flash",
        "env_key": "MIMO_API_KEY"
    },
    "deepseek": {
        "name": "DeepSeek 官方 API",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-r1",
        "env_key": "DEEPSEEK_API_KEY"
    },
    "openai": {
        "name": "OpenAI 官方 API",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY"
    },
    "qwen": {
        "name": "阿里云百炼 Qwen API",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-max",
        "env_key": "DASHSCOPE_API_KEY"
    }
}

DEFAULT_JUDGE_CONFIG: Dict[str, Any] = {
    "mode": "local",  # local 或 cloud
    "enable_stream": True,  # 裁判模型流式输出开关 (支持则逐 token 流式读取，不支持自动平滑降级)
    "local": {
        "provider": "ollama",
        "model_name": "deepseek-r1:1.5b",
        "base_url": "http://localhost:11434"
    },
    "cloud": {
        "provider": "mimo",
        "model_name": "mimo-v2.5-flash",
        "base_url": "https://api.xiaomimimo.com/v1",
        "api_key": ""
    },
    "temperature": 0.0,
    "timeout_seconds": 30.0
}


class JudgeConfigManager:
    """
    持久化裁判配置管理器
    """
    CONFIG_KEY = "rag_eval_judge_config"

    @classmethod
    def get_config(cls, db: Session, mask_key: bool = True) -> Dict[str, Any]:
        """获取当前裁判配置，如无记录则自动初始化默认值"""
        rec = db.query(SystemConfig).filter(SystemConfig.config_key == cls.CONFIG_KEY).first()
        if not rec or not rec.config_value:
            config = dict(DEFAULT_JUDGE_CONFIG)
            try:
                new_rec = SystemConfig(
                    config_key=cls.CONFIG_KEY,
                    config_value=json.dumps(config, ensure_ascii=False),
                    description="RAG 四维评测 LLM Judge 裁判配置 (双模独立持久化)",
                    updated_by="system"
                )
                db.add(new_rec)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"初始化裁判配置记录异常: {e}")
        else:
            try:
                config = json.loads(rec.config_value)
            except Exception:
                config = dict(DEFAULT_JUDGE_CONFIG)

        prov = config.get("cloud", {}).get("provider", "mimo")
        if prov in DEFAULT_PROVIDERS:
            env_key_name = DEFAULT_PROVIDERS[prov]["env_key"]
            env_val = os.getenv(env_key_name, "")
            config["cloud"]["env_key_name"] = env_key_name
            config["cloud"]["env_key_present"] = bool(env_val)
            if not config["cloud"].get("api_key") and env_val:
                config["cloud"]["api_key"] = env_val
                config["cloud"]["is_inherited_env"] = True
            else:
                config["cloud"]["is_inherited_env"] = False

        res = cls._mask(config) if mask_key else config
        res["supported_providers"] = DEFAULT_PROVIDERS
        return res

    @classmethod
    def save_config(cls, db: Session, new_config: Dict[str, Any], updated_by: str = "admin") -> Dict[str, Any]:
        """保存裁判配置并持久化写入数据库"""
        rec = db.query(SystemConfig).filter(SystemConfig.config_key == cls.CONFIG_KEY).first()
        
        # 合并已有配置以防丢失明文 key
        existing_raw = dict(DEFAULT_JUDGE_CONFIG)
        if rec and rec.config_value:
            try:
                existing_raw = json.loads(rec.config_value)
            except Exception:
                pass

        merged = dict(existing_raw)
        if "mode" in new_config:
            merged["mode"] = new_config["mode"]
        if "local" in new_config and isinstance(new_config["local"], dict):
            merged["local"].update(new_config["local"])
        if "cloud" in new_config and isinstance(new_config["cloud"], dict):
            cloud_input = dict(new_config["cloud"])
            k = cloud_input.get("api_key", "")
            inherit_env = cloud_input.get("inherit_env", False)
            prov = cloud_input.get("provider", "mimo")

            if inherit_env and prov in DEFAULT_PROVIDERS:
                env_key_name = DEFAULT_PROVIDERS[prov]["env_key"]
                cloud_input["api_key"] = os.getenv(env_key_name, "")
            elif k and ("..." in k or "***" in k):
                cloud_input["api_key"] = existing_raw.get("cloud", {}).get("api_key", "")
            
            merged["cloud"].update(cloud_input)
        if "temperature" in new_config:
            merged["temperature"] = float(new_config["temperature"])
        if "timeout_seconds" in new_config:
            merged["timeout_seconds"] = float(new_config["timeout_seconds"])

        val_str = json.dumps(merged, ensure_ascii=False)
        if rec:
            rec.config_value = val_str
            rec.updated_by = updated_by
        else:
            rec = SystemConfig(
                config_key=cls.CONFIG_KEY,
                config_value=val_str,
                description="RAG 四维评测 LLM Judge 裁判配置 (双模独立持久化)",
                updated_by=updated_by
            )
            db.add(rec)

        db.commit()
        db.refresh(rec)
        return cls._mask(merged)

    @classmethod
    def _mask(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        c = json.loads(json.dumps(config))
        cloud = c.get("cloud", {})
        key = cloud.get("api_key", "")
        if key:
            cloud["masked_api_key"] = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
        else:
            cloud["masked_api_key"] = ""
        c["cloud"] = cloud
        return c


judge_config_mgr = JudgeConfigManager()
