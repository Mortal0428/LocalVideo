# -*- coding: utf-8 -*-
"""
==============================================================================
【核心模块】：backend/app/core/database.py
【业务定位】：SQLAlchemy 数据库连接池、会话生命周期与防御性自动建表打补丁
【核心功能】：
  1. 引擎初始化（create_app_engine）：建立与 MySQL 数据库的高性能连接池，
     配置连接探活（pool_pre_ping=True）与自动重连回收（pool_recycle=3600）；
  2. 请求级会话提供器（get_db）：FastAPI 依赖注入专属，为每个 HTTP 请求分配
     独立的数据库事务 Session，在请求结束时使用 finally 确保 100% 释放关闭，防止连接池泄漏；
  3. 系统防御性初始化（init_db）：服务启动时自动扫描 Base 元数据建表、
     动态检测新字段并防御性添加（Schema Auto-Patching）、清理违规占位数据、
     以及自动引导植入 9 大智能体战队与内置技能库。
==============================================================================
"""
import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """所有 ORM 数据模型的公共基类"""
    pass

def create_app_engine():
    """
    【大白话功能】：创建数据库底层通信引擎。
    优先连接高性能 MySQL 服务，若未启动且开启兜底则平滑切换至本地 SQLite。
    """
    try:
        mysql_engine = create_engine(
            settings.SQLALCHEMY_DATABASE_URL,
            pool_pre_ping=True,      # 每次拿连接前 ping 一下，防止 MySQL 长时间静止自动断开
            pool_recycle=1800,       # 30 分钟主动重置连接，彻底避免 MySQL 8小时 wait_timeout 报错
            pool_size=15,            # 常驻活跃连接池大小提升至 15
            max_overflow=35,         # 高并发突发时允许最大溢出创建的临时连接数提升至 35
            pool_timeout=10          # 连接获取超时由默认 30s 缩减至 10s，快速失败防止请求积压
        )
        # 实测发起一次连接探测
        with mysql_engine.connect() as conn:
            pass
        logger.info(f"Connected successfully to MySQL database '{settings.MYSQL_DATABASE}'.")
        return mysql_engine
    except Exception as e:
        if settings.USE_SQLITE_FALLBACK:
            logger.warning(
                f"MySQL connection failed ({e}). Activating SQLite fallback '{settings.SQLITE_PATH}' "
                "so the application can run immediately. Update MySQL credentials in .env to switch."
            )
            sqlite_url = f"sqlite:///{settings.SQLITE_PATH}"
            return create_engine(sqlite_url, connect_args={"check_same_thread": False})
        else:
            raise e

# 创建全局唯一通信引擎与会话工厂
engine = create_app_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    """
    【大白话功能】：FastAPI 依赖注入专用的数据库 Session 生成器。
    每个请求开始时由该函数发放一个独立的 db 会话；
    无论业务处理成功与否，在 finally 中自动将连接归还连接池，严防死锁与连接耗尽。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    【大白话功能】：系统启动引导程序，保证所有数据库结构齐备。
    【核心步骤】：
      第 1 步：导入所有 models 模型，让 Base.metadata 收集到全部数据表；
      第 2 步：Base.metadata.create_all(bind=engine) 自动创建尚不存在的表；
      第 3 步：防御性补丁检查：对于已有老表，若后续需求新增了字段，自动执行 ALTER TABLE ADD COLUMN；
      第 4 步：清理残留的非法伪造字幕台词，保持数据库干净；
      第 5 步：初始化 9 大智能体战队与预设技能库。
    """
    try:
        import app.models  # 确保所有模型类均已加载注册
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified and initialized successfully.")

        # 防御性补丁：检查存量表中是否缺少最新演进字段
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(engine)
            existing_tables = set(inspector.get_table_names())
            columns_to_patch = {
                "videos": [
                    ("coin_count", "INTEGER DEFAULT 0"),
                    ("heat_score", "FLOAT DEFAULT 0.0"),
                ],
                "users": [
                    ("vip_expire_at", "DATETIME NULL"),
                ],
                "user_comments": [
                    ("root_id", "VARCHAR(36) NULL"),
                    ("parent_id", "VARCHAR(36) NULL"),
                    ("reply_to_user_id", "VARCHAR(36) NULL"),
                ],
            }
            with engine.begin() as conn:
                for tbl_name, cols in columns_to_patch.items():
                    if tbl_name in existing_tables:
                        existing_cols = {c["name"] for c in inspector.get_columns(tbl_name)}
                        for col_name, col_type in cols:
                            if col_name not in existing_cols:
                                try:
                                    conn.execute(text(f"ALTER TABLE {tbl_name} ADD COLUMN {col_name} {col_type}"))
                                    logger.info(f"Defensive DB patch: added column {tbl_name}.{col_name}")
                                except Exception as col_err:
                                    logger.warning(f"Notice adding column {tbl_name}.{col_name}: {col_err}")
        except Exception as patch_err:
            logger.warning(f"Defensive DB schema patching encountered non-fatal error: {patch_err}")

        # 清理可能残留的生造测试字幕台词
        try:
            from app.models.video import VideoSubtitleTimeline
            forbidden_keywords = [
                "三年隐忍", "退婚", "黑卡", "懦夫", "动我兄弟者", "龙王", "草芥", "少主"
            ]
            with SessionLocal() as db:
                all_subs = db.query(VideoSubtitleTimeline).all()
                dirty = False
                for sub in all_subs:
                    content = sub.content or ""
                    if any(kw in content for kw in forbidden_keywords):
                        db.delete(sub)
                        dirty = True
                if dirty:
                    db.commit()
                    logger.info("Defensive DB cleanup: purged residual fabricated subtitles.")

                # 自动引导植入 9 大智能体战队与内置技能库
                try:
                    from app.services.agent_fleet.base_and_telemetry import ensure_agent_fleet_seeded
                    from app.services.agent_fleet.skill_registry import ensure_skills_seeded
                    ensure_agent_fleet_seeded(db)
                    ensure_skills_seeded(db)
                except Exception as fleet_seed_err:
                    logger.warning(f"Agent fleet seed notice: {fleet_seed_err}")
        except Exception as sub_err:
            logger.warning(f"Defensive subtitle purge check encountered non-fatal error: {sub_err}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e
