# -*- coding: utf-8 -*-
"""
==============================================================================
【核心模块】：backend/app/core/config.py
【业务定位】：全平台全局系统配置、环境变量与数据驱动中心
【核心功能】：
  基于 Pydantic 的 BaseSettings 集中管理系统运行的所有关键环境变量：
  1. MySQL 数据库连接（主机、端口、账号、密码、库名）；
  2. 磁盘与本地媒体资源目录（上传缓冲、HLS 切片目录、向量数据库存储）；
  3. OpenList 网盘网关配置（夸克云盘、联通沃家云盘挂载路径与接口）；
  4. LangSmith 与 LangChain 全链路可观测性 Tracing 配置；
  5. 本地 Ollama 与云端小米 MiMo / DeepSeek 底座调用端点与模型名；
  6. 提供单例 settings 实例供全系统任意文件导入使用。
==============================================================================
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    【全局动态配置类】
    自动优先读取项目根目录下的 .env 环境变量文件，未配置时无缝采用安全的本地开发默认值。
    """
    PROJECT_NAME: str = "Video Platform & Agent API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # ================= MySQL 关系型数据库配置 =================
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "Cyx.chen27"
    MYSQL_DATABASE: str = "video_platform_db"
    
    # 双引擎兜底：若 MySQL 服务未启动，是否允许自动降级为本地 SQLite 文件
    USE_SQLITE_FALLBACK: bool = False
    SQLITE_PATH: str = os.path.join(os.getcwd(), "video_platform.db")
    
    # ================= 本地与云存储目录配置 =================
    # 用户上传视频原始缓冲目录
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "storage", "uploads")
    # 转码切片后的 HLS (m3u8 + ts) 流媒体存储目录
    PROCESSED_VIDEO_DIR: str = os.path.join(os.getcwd(), "storage", "hls")
    # 本地向量检索数据库持久化目录
    VECTOR_DB_DIR: str = os.path.join(os.getcwd(), "storage", "chroma")
    
    # 存储引擎类型：local(本地磁盘), oss(阿里云OSS), s3(AWS S3), cos(腾讯云COS)
    STORAGE_TYPE: str = "local"
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    
    # ================= OpenList 网盘网关配置 (夸克网盘与联通沃家云盘) =================
    OPENLIST_BASE_URL: str = "http://127.0.0.1:5244"
    OPENLIST_USERNAME: str = "admin"
    OPENLIST_PASSWORD: str = "123456"
    OPENLIST_MOUNT_PATH: str = "/kuake/短剧资源目录"
    OPENLIST_FALLBACK_PATHS: str = "/kuake/短剧资源目录,/kuake,/liantong"

    # ================= LangSmith 可观测性链路追踪 =================
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = "Personal"

    # ================= 本地大模型引擎配置 (Ollama / DeepSeek-R1) =================
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_LLM_MODEL: str = "deepseek-r1:1.5b"
    DEFAULT_EMBEDDING_MODEL: str = "qwen3-embedding:0.6b"

    # ================= 云端大模型配置 (小米 MiMo / 云端 DeepSeek) =================
    MIMO_BASE_URL: str = "https://api.xiaomimimo.com/v1"
    MIMO_API_KEY: Optional[str] = os.getenv("MIMO_API_KEY", "")
    MIMO_DEFAULT_MODEL: str = "mimo-v1"
    ACTIVE_PROVIDER: str = "ollama"  # 默认活跃提供商："ollama" 或 "mimo"

    # ================= 10号智能体 Coze 开放生态配置 =================
    COZE_API_TOKEN: str = "pat_51xmlLWv4i35xiWHMjLx6X16g5hBcpwwR5G3Ujf6lSP8PEhuuN73GlLpY42G2yxo"
    COZE_BOT_ID: str = "7700811095929323554"
    COZE_BASE_URL: str = "https://api.coze.cn"
    COZE_TIMEOUT: int = 30
    
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        """根据当前配置动态组装 MySQL SQLAlchemy 异步/同步连接字符串"""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"

    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = True

# 全局单例配置实例
settings = Settings()
