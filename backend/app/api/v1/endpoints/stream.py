import httpx
import time
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.video import VideoEpisode, Video
from app.models.interaction import VideoDanmaku
from app.services.openlist_storage import openlist_storage

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory lease cache for direct cloud stream URLs
# Format: { episode_id: {"url": str, "expire_at": float} }
STREAM_URL_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 1200  # 20 minutes lease window

@router.get("/direct-url/{episode_id}")
@router.get("/stream/direct-url/{episode_id}")
async def get_direct_stream_url(
    episode_id: str,
    db: Session = Depends(get_db)
):
    """
    Get high-speed direct stream URL from Cloud Disk with lease caching.
    Bypasses FastAPI proxy bandwidth and offloads streaming directly to cloud CDN.
    Provides fallback_proxy_url if direct stream encounters client-side network issues.
    """
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Video episode not found")

    file_path = episode.raw_file_path
    if not file_path:
        raise HTTPException(status_code=400, detail="Episode has no file path configured")

    current_time = time.time()
    cached = STREAM_URL_CACHE.get(episode_id)

    # Return cached URL if valid with at least 60s remaining buffer
    if cached and cached.get("expire_at", 0) > current_time + 60:
        return {
            "code": 200,
            "message": "success (cached)",
            "data": {
                "episode_id": episode_id,
                "direct_url": cached["url"],
                "expires_in": int(cached["expire_at"] - current_time),
                "fallback_proxy_url": f"/api/v1/videos/stream/{episode_id}"
            }
        }

    try:
        raw_url, file_info = await openlist_storage.get_stream_url(file_path)
    except Exception as e:
        logger.error(f"Failed to get direct stream url for {file_path}: {e}")
        # Fallback gracefully to proxy stream endpoint
        return {
            "code": 200,
            "message": f"Direct stream fallback: {str(e)}",
            "data": {
                "episode_id": episode_id,
                "direct_url": f"/api/v1/videos/stream/{episode_id}",
                "expires_in": CACHE_TTL_SECONDS,
                "fallback_proxy_url": f"/api/v1/videos/stream/{episode_id}"
            }
        }

    # Store lease in cache
    STREAM_URL_CACHE[episode_id] = {
        "url": raw_url,
        "expire_at": current_time + CACHE_TTL_SECONDS
    }

    return {
        "code": 200,
        "message": "success",
        "data": {
            "episode_id": episode_id,
            "direct_url": raw_url,
            "expires_in": CACHE_TTL_SECONDS,
            "fallback_proxy_url": f"/api/v1/videos/stream/{episode_id}"
        }
    }

@router.get("/redirect/{episode_id}")
@router.get("/stream/redirect/{episode_id}")
async def stream_video_episode_redirect(
    episode_id: str,
    db: Session = Depends(get_db)
):
    """
    302 Redirect directly to Cloud Disk CDN stream for seamless native video elements.
    """
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Video episode not found")

    file_path = episode.raw_file_path
    if not file_path:
        raise HTTPException(status_code=400, detail="Episode has no file path configured")

    current_time = time.time()
    cached = STREAM_URL_CACHE.get(episode_id)
    if cached and cached.get("expire_at", 0) > current_time + 60:
        return RedirectResponse(url=cached["url"], status_code=302)

    try:
        raw_url, _ = await openlist_storage.get_stream_url(file_path)
        STREAM_URL_CACHE[episode_id] = {
            "url": raw_url,
            "expire_at": current_time + CACHE_TTL_SECONDS
        }
        return RedirectResponse(url=raw_url, status_code=302)
    except Exception as e:
        logger.error(f"Direct redirect failed for {file_path}: {e}, falling back to proxy stream")
        return RedirectResponse(url=f"/api/v1/videos/stream/{episode_id}", status_code=302)

@router.get("/cloud-files")
async def list_cloud_files(path: Optional[str] = None):
    """Lists files directly from Cloud Disk via OpenList with automatic failover."""
    try:
        files, active_path = await openlist_storage.list_files_with_failover(path)
        return {
            "code": 200,
            "message": "success",
            "active_path": active_path,
            "data": files
        }
    except Exception as e:
        logger.error(f"Error listing cloud files: {e}")
        return {
            "code": 200,
            "message": f"Storage notice: {e}",
            "active_path": path or "/kuake",
            "data": []
        }

@router.get("/stream/{episode_id}")
async def stream_video_episode(
    episode_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Stream video chunk by chunk with HTTP Range (206) support.
    Fetches high-speed direct stream from China Unicom Cloud Disk without taking local bandwidth or disk space.
    """
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Video episode not found")

    file_path = episode.raw_file_path
    if not file_path:
        raise HTTPException(status_code=400, detail="Episode has no file path configured")

    try:
        raw_url, file_info = await openlist_storage.get_stream_url(file_path)
    except Exception as e:
        logger.error(f"Failed to get stream url for {file_path}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch cloud stream: {e}")

    range_header = request.headers.get("range")
    req_headers = {"User-Agent": "Mozilla/5.0"}
    if range_header:
        req_headers["Range"] = range_header

    client = httpx.AsyncClient(timeout=60.0)
    try:
        upstream_req = client.build_request("GET", raw_url, headers=req_headers)
        upstream_resp = await client.send(upstream_req, stream=True)

        async def stream_generator():
            try:
                async for chunk in upstream_resp.aiter_bytes(chunk_size=524288):
                    yield chunk
            finally:
                await upstream_resp.aclose()
                await client.aclose()

        response_headers = {
            "Accept-Ranges": "bytes",
            "Content-Type": upstream_resp.headers.get("Content-Type", "video/mp4"),
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Range, Accept-Ranges, Content-Length",
        }
        if "Content-Range" in upstream_resp.headers:
            response_headers["Content-Range"] = upstream_resp.headers["Content-Range"]
        if "Content-Length" in upstream_resp.headers:
            response_headers["Content-Length"] = upstream_resp.headers["Content-Length"]

        return StreamingResponse(
            stream_generator(),
            status_code=upstream_resp.status_code,
            headers=response_headers,
            media_type="video/mp4"
        )
    except Exception as e:
        await client.aclose()
        logger.error(f"Error streaming video from cloud: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/home-feed")
async def get_home_feed(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns Bilibili-style home portal feed:
    - carousel banners
    - channel categories
    - rich video cards with stats, duration, and creator metadata
    """
    db_videos = db.query(Video).all()
    
    # 1. Categories
    categories = [
        {"id": "all", "name": "全部"},
        {"id": "hot", "name": "🔥 热门"},
        {"id": "short-drama", "name": "微短剧"},
        {"id": "reversal", "name": "逆袭爽剧"},
        {"id": "eighties", "name": "年代逆袭"},
        {"id": "anime", "name": "动漫番剧"},
        {"id": "tech-ai", "name": "科技AI"},
        {"id": "soundtrack", "name": "影视原声"},
    ]

    # Query published and visible videos from database (exclude HIDDEN)
    published_videos = db.query(Video).filter(Video.status != "HIDDEN").all()
    if not published_videos:
        published_videos = db.query(Video).all()

    # Build dynamic cards from database
    raw_cards = []
    import json
    for v in published_videos:
        first_ep = db.query(VideoEpisode).filter(VideoEpisode.video_id == v.id).order_by(VideoEpisode.episode_num.asc()).first()
        ep_id = first_ep.id if first_ep else "default_ep"
        duration_display = f"{v.total_episodes}集全" if v.total_episodes > 1 else "03:45"

        views = v.view_count or 0
        view_str = f"{views / 10000:.1f}万" if views >= 10000 else str(views)
        danmaku_count = db.query(VideoDanmaku).join(VideoEpisode, VideoEpisode.id == VideoDanmaku.episode_id).filter(VideoEpisode.video_id == v.id).count()
        danmaku_str = f"{danmaku_count / 10000:.1f}万" if danmaku_count >= 10000 else str(danmaku_count)

        creator_name = "红果星芒剧场"
        creator_avatar = "https://api.dicebear.com/7.x/bottts/svg?seed=hg_creator"
        if v.creator:
            creator_name = v.creator.nickname or v.creator.username
            creator_avatar = v.creator.avatar_url or creator_avatar

        badge = "爆款连载"
        if v.total_episodes >= 100:
            badge = f"{v.total_episodes}集全"
        elif "逆袭" in (v.category or ""):
            badge = "爽剧 Top 1"

        effective_cover = v.custom_cover_url or v.cover_url or "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=640&q=80"
        extra_imgs = []
        if v.extra_images:
            try:
                extra_imgs = json.loads(v.extra_images)
            except Exception:
                extra_imgs = []

        raw_cards.append({
            "id": v.id,
            "episode_id": ep_id,
            "title": v.title,
            "cover_url": effective_cover,
            "extra_images": extra_imgs,
            "category": v.category or "微短剧",
            "duration_str": duration_display,
            "play_count_str": view_str,
            "danmaku_count_str": danmaku_str,
            "creator_name": creator_name,
            "creator_avatar": creator_avatar,
            "pub_date": v.created_at.strftime("%m-%d") if v.created_at else "10-20",
            "badge": badge
        })

    # Build hero carousels (First check SystemCarousel table configured by Admin)
    carousels = []
    from app.models.video import SystemCarousel
    db_carousels = db.query(SystemCarousel).filter(SystemCarousel.is_active == True).order_by(SystemCarousel.sort_order.asc()).all()
    default_duration = 5
    if db_carousels:
        for sc in db_carousels:
            target_vid = sc.video_id or (published_videos[0].id if published_videos else "default_vid")
            first_ep = db.query(VideoEpisode).filter(VideoEpisode.video_id == target_vid).order_by(VideoEpisode.episode_num.asc()).first()
            dur = getattr(sc, 'duration_seconds', 5) or 5
            default_duration = dur
            target_v = db.query(Video).filter(Video.id == target_vid).first()
            v_views = (target_v.view_count or 0) if target_v else 0
            p_str = f"{v_views / 10000:.1f}万次播放" if v_views >= 10000 else f"{v_views}次播放"
            dmk_cnt = db.query(VideoDanmaku).join(VideoEpisode, VideoEpisode.id == VideoDanmaku.episode_id).filter(VideoEpisode.video_id == target_vid).count()
            d_str = f"{dmk_cnt / 10000:.1f}万条弹幕" if dmk_cnt >= 10000 else f"{dmk_cnt}条弹幕"
            carousels.append({
                "id": sc.id,
                "video_id": target_vid,
                "episode_id": first_ep.id if first_ep else "default_ep",
                "title": sc.title,
                "subtitle": sc.subtitle or "夸克原盘极速直连 · 平滑自动轮播",
                "cover_url": sc.cover_url,
                "tag": sc.tag or "今日焦点",
                "duration_seconds": dur,
                "play_count_str": p_str,
                "danmaku_count_str": d_str
            })
    else:
        # Fallback to dynamic hero carousels from top database dramas with VALID covers
        carousel_candidates = [
            v for v in published_videos 
            if (v.total_episodes or 0) > 1 
            and (v.custom_cover_url or v.cover_url) 
            and not "测试" in (v.title or "")
        ]
        if not carousel_candidates:
            carousel_candidates = [v for v in published_videos if (v.custom_cover_url or v.cover_url)]

        for idx, cv in enumerate(carousel_candidates[:4]):
            first_ep = db.query(VideoEpisode).filter(VideoEpisode.video_id == cv.id).order_by(VideoEpisode.episode_num.asc()).first()
            carousels.append({
                "id": f"c_{cv.id}",
                "video_id": cv.id,
                "episode_id": first_ep.id if first_ep else "default_ep",
                "title": f"【热播焦点】{cv.title}",
                "subtitle": cv.summary or f"🔥 全网热播短剧 · 共{cv.total_episodes}集 · 9:16 / 16:9 双模态极速畅享",
                "cover_url": cv.custom_cover_url or cv.cover_url,
                "tag": cv.category or "微短剧",
                "duration_seconds": 5
            })

    # Filter by category if specified
    cards = raw_cards
    if category and category != "all" and category != "hot":
        cat_map = {
            "short-drama": "微短剧",
            "tech-ai": "科技AI",
            "sweet-love": "现代甜宠",
            "reversal": "逆袭爽剧",
            "soundtrack": "影视原声",
            "variety": "微综艺"
        }
        target_name = cat_map.get(category, category)
        cards = [c for c in raw_cards if c["category"] == target_name]

    # Filter by search keyword
    if keyword:
        kw = keyword.lower()
        cards = [c for c in cards if kw in c["title"].lower() or kw in c["category"].lower()]

    return {
        "code": 200,
        "data": {
            "categories": categories,
            "carousels": carousels,
            "carousel_duration_seconds": default_duration,
            "videos": cards
        }
    }
