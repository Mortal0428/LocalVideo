from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base

class SystemConfig(Base):
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    config_key = Column(String(64), unique=True, nullable=False, index=True, comment="配置项唯一键")
    config_value = Column(Text, nullable=False, comment="配置内容(JSON或纯文本)")
    description = Column(String(255), nullable=True, comment="配置说明")
    updated_by = Column(String(64), nullable=True, comment="最后更新人")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
