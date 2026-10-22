"""
CinemaAgent RAG 评测裁判模型持久化配置模块 (LLM Judge Config)
支持在 system_configs 表中读写 rag_eval_judge_config 记录，
提供本地 Ollama 裁判与独立云端模型裁判 (DeepSeek-R1 / Qwen / OpenAI) 的双模自由切换。
"""

import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)

DEFAULT_JUDGE_CONFIG: Dict[str, Any] = {
    "mode": "local",  # local 或 cloud
    "local": {
        "provider": "ollama",
        "model_name": "deepseek-r1:1.5b",
        "base_url": "http://localhost:11434"
    },
    "cloud": {
        "provider": "deepseek",
        "model_name": "deepseek-r1",
        "base_url": "https://api.deepseek.com",
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
            return cls._mask(config) if mask_key else config

        try:
            config = json.loads(rec.config_value)
        except Exception:
            config = dict(DEFAULT_JUDGE_CONFIG)

        return cls._mask(config) if mask_key else config

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
            # 如果传入的是掩码，则保留旧 key
            cloud_input = dict(new_config["cloud"])
            k = cloud_input.get("api_key", "")
            if k and "..." in k:
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
