from fastapi import APIRouter
from app.api.v1.endpoints import stream, upload, interactions, danmaku, review, agent, auth, models, creator, admin, user, system, favorites, coins, notifications, rag_admin, agent_hub, agent_mesh, mcp_admin
from app.mcp.server.router import router as mcp_router

api_router = APIRouter()

api_router.include_router(models.router, prefix="/models", tags=["Engine & Model Discovery"])
api_router.include_router(system.router, prefix="/system", tags=["System Telemetry & Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["User Authentication & Roles"])
api_router.include_router(user.router, prefix="/user", tags=["User Profile & Space"])
api_router.include_router(creator.router, prefix="/creator", tags=["Creator Cloud Disk & Studio"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin User Moderation & Overview"])
api_router.include_router(agent.router, prefix="/agent", tags=["Video Companion Agent RAG"])
api_router.include_router(rag_admin.router, prefix="/rag-admin", tags=["Modular RAG Knowledge & Eval"])
api_router.include_router(agent_hub.router, prefix="/agent-hub", tags=["Nine-Agent Fleet & Integrator"])
api_router.include_router(agent_mesh.router, prefix="/agent-mesh", tags=["Agent Mesh & Roundtable Orchestrator"])
api_router.include_router(mcp_router)
api_router.include_router(mcp_admin.router)
api_router.include_router(interactions.router, prefix="/interactions", tags=["Video Interactions & Album"])
api_router.include_router(danmaku.router, prefix="/danmaku", tags=["Real-time Danmaku & WebSocket"])
api_router.include_router(review.router, prefix="/review", tags=["Content Safety & Review Queue"])
api_router.include_router(upload.router, prefix="/upload", tags=["Video Chunk Upload & Transcode"])
api_router.include_router(stream.router, prefix="/videos", tags=["Video Streaming & Cloud Files"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
api_router.include_router(coins.router, prefix="/user/coins", tags=["Coin Economy & VIP Exchange"])
api_router.include_router(coins.router, prefix="/coins", tags=["Coin Economy Alias"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["User Notifications & Skylight"])
