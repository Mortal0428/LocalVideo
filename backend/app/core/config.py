import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Video Platform & Agent API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # MySQL Database Config (Configurable via .env)
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "Cyx.chen27"
    MYSQL_DATABASE: str = "video_platform_db"
    
    # Dual-mode support (Default True as fallback safeguard)
    USE_SQLITE_FALLBACK: bool = False
    SQLITE_PATH: str = os.path.join(os.getcwd(), "video_platform.db")
    
    # Storage Configuration (Local buffer / Cloud Storage)
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "storage", "uploads")
    PROCESSED_VIDEO_DIR: str = os.path.join(os.getcwd(), "storage", "hls")
    VECTOR_DB_DIR: str = os.path.join(os.getcwd(), "storage", "chroma")
    
    # Cloud Storage Options (S3 / OSS / COS)
    STORAGE_TYPE: str = "local"  # "local", "oss", "s3", "cos"
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    
    # OpenList Cloud Drive Gateway (Quark Cloud Disk & WoPan)
    OPENLIST_BASE_URL: str = "http://127.0.0.1:5244"
    OPENLIST_USERNAME: str = "admin"
    OPENLIST_PASSWORD: str = "123456"
    OPENLIST_MOUNT_PATH: str = "/kuake/红果项目资源目录"
    OPENLIST_FALLBACK_PATHS: str = "/kuake/红果项目资源目录,/kuake,/liantong"

    # Ollama / Local LLM Config
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_LLM_MODEL: str = "deepseek-r1:1.5b"
    DEFAULT_EMBEDDING_MODEL: str = "qwen3-embedding:0.6b"

    # Xiaomi MiMo Cloud API Config
    MIMO_BASE_URL: str = "https://api.xiaomimimo.com/v1"
    MIMO_API_KEY: Optional[str] = os.getenv("MIMO_API_KEY", "")
    MIMO_DEFAULT_MODEL: str = "mimo-v1"
    ACTIVE_PROVIDER: str = "ollama"  # "ollama" or "mimo"
    
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"

    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = True

settings = Settings()
