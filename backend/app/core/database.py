import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

def create_app_engine():
    # Attempt MySQL connection first
    try:
        mysql_engine = create_engine(
            settings.SQLALCHEMY_DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20
        )
        # Test connection
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

engine = create_app_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    """Dependency to provide a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Ensure database tables exist using Base metadata and enforce zero fake subtitles."""
    try:
        import app.models  # Ensure all model tables are registered into Base.metadata
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified and initialized successfully.")

        # Defensive schema auto-patching for new columns in existing tables
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

        # Defensive cleanup: purge any residual fake subtitle records
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
        except Exception as sub_err:
            logger.warning(f"Defensive subtitle purge check encountered non-fatal error: {sub_err}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e
