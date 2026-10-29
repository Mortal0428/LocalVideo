import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router

# 同步 LangSmith 环境变量到操作系统运行时
os.environ["LANGCHAIN_TRACING_V2"] = str(settings.LANGCHAIN_TRACING_V2).lower()
os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CinemaAgent Platform application...")
    try:
        init_db()
        logger.info("Database schemas initialized.")
    except Exception as e:
        logger.warning(f"Could not connect to MySQL at startup: {e}. Please ensure MySQL is running and database exists.")

    # Auto-sync cloud dramas in background task on startup
    import asyncio
    async def auto_sync_dramas():
        try:
            from app.services.cloud_drama_sync import cloud_drama_sync
            await asyncio.sleep(2)
            res = await cloud_drama_sync.scan_and_sync_all()
            logger.info(f"Startup cloud drama sync completed: {res.get('total_synced_dramas', 0)} dramas mapped.")
        except Exception as e:
            logger.warning(f"Startup cloud drama sync notice: {e}")

    asyncio.create_task(auto_sync_dramas())

    yield
    logger.info("Shutting down CinemaAgent Platform application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration for Vue 3 frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/dist"))
assets_dir = os.path.join(frontend_dist, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Mount /storage directory for user uploads and media assets
storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage"))
if not os.path.exists(storage_dir):
    storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "storage"))
os.makedirs(storage_dir, exist_ok=True)
app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")

@app.get("/")
def root():
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

@app.get("/{full_path:path}")
def catch_all_spa(full_path: str):
    # Don't hijack API routes, docs, or storage
    if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json") or full_path.startswith("storage/"):
        raise HTTPException(status_code=404, detail="API route not found")
    candidate = os.path.join(frontend_dist, full_path)
    if os.path.isfile(candidate):
        return FileResponse(candidate)
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"detail": "Not Found"}

if __name__ == "__main__":
    import uvicorn
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # 在 PyCharm 点击运行小三角（运行 main.py）时，自动并行检测并拉起全套依赖服务 (带独立控制台日志)
    try:
        from app.core.cluster_bootstrapper import launch_cluster_dependencies
        launch_cluster_dependencies()
    except Exception as e:
        logger.warning(f"Cluster bootstrapper notice: {e}")

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, app_dir=backend_dir)
