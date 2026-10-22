import re
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.video import Video, VideoEpisode
from app.models.user import User
from app.services.openlist_storage import openlist_storage

logger = logging.getLogger(__name__)

# Predefined curated aesthetic posters for the series as resilient fallback
DRAMA_COVERS = {
    "高冷千金": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&q=80",
    "八零赚钱养家": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800&q=80",
    "我推的孩子": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800&q=80",
    "艾莉同学": "https://images.unsplash.com/photo-1516589178581-6cd7833ae3b2?w=800&q=80",
    "白月光": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&q=80",
    "厨娘": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800&q=80"
}

class CloudDramaSyncService:
    """
    Scans Quark Cloud Disk via OpenList, parses short drama titles, txt summaries,
    primary/multi-cover images, and maps them into MySQL `videos` and `video_episodes`.
    Supports incremental (fast, skip existing) and full synchronization modes.
    """

    async def scan_and_sync_all(self, db: Optional[Session] = None, mode: str = "incremental") -> Dict[str, Any]:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            creator = db.query(User).filter(User.role == "CREATOR").first()
            if not creator:
                creator = db.query(User).filter(User.username == "creator").first()
            if not creator:
                creator = db.query(User).first()
            creator_id = creator.id if creator else "system"

            synced_dramas = []
            skipped_dramas = 0
            new_eps_total = 0

            # 1. Scan /kuake/红果项目资源目录
            root_path = "/kuake/红果项目资源目录"
            items = await openlist_storage.list_files(root_path)

            for item in items:
                if item.get("is_dir"):
                    folder_name = item.get("name")
                    folder_path = f"{root_path}/{folder_name}"
                    drama_res = await self._sync_drama_folder(db, folder_path, folder_name, creator_id, mode=mode)
                    if drama_res:
                        if drama_res.get("skipped"):
                            skipped_dramas += 1
                        else:
                            new_eps_total += drama_res.get("new_episodes_added", 0)
                        synced_dramas.append(drama_res)

            # 2. Also scan /kuake/来自：云收藏 for collection anime/dramas
            cloud_collect_path = "/kuake/来自：云收藏"
            try:
                collect_items = await openlist_storage.list_files(cloud_collect_path)
                anime_groups = self._group_collection_files(collect_items)
                for group_title, ep_files in anime_groups.items():
                    res = await self._sync_collection_group(db, cloud_collect_path, group_title, ep_files, creator_id, mode=mode)
                    if res:
                        synced_dramas.append(res)
            except Exception as e:
                logger.warning(f"Notice scanning cloud collections: {e}")

            db.commit()

            # Calculate total episodes in database
            total_eps_in_db = db.query(VideoEpisode).count()

            return {
                "success": True,
                "mode": mode,
                "dramas_found": len(synced_dramas),
                "total_synced_dramas": len(synced_dramas),
                "total_episodes": total_eps_in_db,
                "new_episodes_added": new_eps_total,
                "skipped_dramas": skipped_dramas,
                "dramas": synced_dramas
            }
        except Exception as e:
            logger.error(f"Error syncing cloud dramas: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_db:
                db.close()

    async def _sync_drama_folder(
        self, db: Session, folder_path: str, folder_name: str, creator_id: str, mode: str = "incremental"
    ) -> Optional[Dict[str, Any]]:
        """Parses a drama folder, txt intro, multiple posters, and syncs its episodes."""
        files = await openlist_storage.list_files(folder_path, per_page=500)
        if not files:
            return None

        clean_title = re.sub(r"^\d+[\.、\s]*", "", folder_name)
        clean_title = re.sub(r"（\d+集）|\(\d+集\)", "", clean_title).strip()
        clean_title = clean_title.replace("第二季", " 第2季").replace("第2季", " 第2季").strip()

        # Check existing drama in DB
        existing_video = db.query(Video).filter(Video.title == clean_title).first()

        # Separate files by type
        video_files = []
        image_files = []
        txt_files = []

        for f in files:
            if f.get("is_dir"):
                continue
            fname = f.get("name", "")
            lower_name = fname.lower()
            if lower_name.endswith((".mp4", ".mov", ".mkv", ".webm", ".ts")):
                ep_num = self._extract_episode_number(fname)
                video_files.append({
                    "name": fname,
                    "path": f"{folder_path}/{fname}",
                    "ep_num": ep_num,
                    "size": f.get("size", 0)
                })
            elif lower_name.endswith((".jpg", ".jpeg", ".png", ".webp")):
                image_files.append({
                    "name": fname,
                    "url": f"http://127.0.0.1:5244/p{folder_path}/{fname}"
                })
            elif lower_name.endswith(".txt"):
                txt_files.append(fname)

        if not video_files:
            return None

        video_files.sort(key=lambda x: x["ep_num"])

        # Incremental mode optimization: If drama exists and episode count matches, skip heavy write
        if mode == "incremental" and existing_video:
            ep_count = db.query(VideoEpisode).filter(VideoEpisode.video_id == existing_video.id).count()
            if ep_count >= len(video_files):
                return {
                    "video_id": existing_video.id,
                    "title": clean_title,
                    "category": existing_video.category,
                    "total_episodes": ep_count,
                    "new_episodes_added": 0,
                    "cover_url": existing_video.cover_url,
                    "skipped": True
                }

        # Determine Category
        category = "微短剧"
        if "千金" in clean_title or "高手" in clean_title:
            category = "逆袭爽剧"
        elif "八零" in clean_title or "赚钱" in clean_title or "离婚" in clean_title:
            category = "年代逆袭"
        elif "白月光" in clean_title or "炮灰" in clean_title:
            category = "穿书甜宠"
        elif "厨娘" in clean_title or "王爷" in clean_title:
            category = "古装甜爽"

        # Determine Primary Cover & Multi-cover gallery
        cover_url = None
        extra_image_urls = [img["url"] for img in image_files]

        # Rule A: Look for `<作品名>.jpg` or matching title
        normalized_title = clean_title.replace(" ", "")
        for img in image_files:
            img_stem = img["name"].rsplit(".", 1)[0].replace(" ", "")
            if normalized_title in img_stem or img_stem in normalized_title:
                cover_url = img["url"]
                break

        # Rule B: Look for 0.jpg, cover.jpg, poster.jpg
        if not cover_url:
            for img in image_files:
                if img["name"].lower() in ["0.jpg", "cover.jpg", "poster.jpg", "0.jpeg"]:
                    cover_url = img["url"]
                    break

        # Rule C: First image found in folder
        if not cover_url and image_files:
            cover_url = image_files[0]["url"]

        # Rule D: Curated fallback
        if not cover_url:
            for kw, url in DRAMA_COVERS.items():
                if kw in clean_title:
                    cover_url = url
                    break
        if not cover_url:
            cover_url = "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=800&q=80"

        # Multi-cover image carousel JSON (if >= 2 images)
        extra_images_json = json.dumps(extra_image_urls, ensure_ascii=False) if len(extra_image_urls) >= 2 else None

        # Build Rich Summary from txt or smart template
        txt_hint = f"（内含 {', '.join(txt_files)}）" if txt_files else ""
        summary_text = (
            f"夸克网盘原生态高品质直读 · 《{clean_title}》全集无删减收录！"
            f"剧集附带原装剧情解析与角色全档案{txt_hint}，共{len(video_files)}集超清连载，支持16:9与9:16双模态观影。"
        )

        # Upsert Video
        if not existing_video:
            video = Video(
                creator_id=creator_id,
                title=clean_title,
                summary=summary_text,
                cover_url=cover_url,
                extra_images=extra_images_json,
                category=category,
                status="PUBLISHED",
                total_episodes=len(video_files),
                view_count=len(video_files) * 3140 + 880,
                like_count=len(video_files) * 128 + 52
            )
            db.add(video)
            db.flush()
        else:
            video = existing_video
            video.total_episodes = len(video_files)
            if not video.custom_cover_url:
                video.cover_url = cover_url
            video.extra_images = extra_images_json
            video.summary = summary_text
            db.flush()

        # Upsert Episodes
        existing_eps = {ep.episode_num: ep for ep in db.query(VideoEpisode).filter(VideoEpisode.video_id == video.id).all()}
        added_count = 0

        for vf in video_files:
            ep_num = vf["ep_num"]
            ep_title = f"第{ep_num}集"
            if ep_num in existing_eps:
                ep = existing_eps[ep_num]
                ep.raw_file_path = vf["path"]
                ep.title = ep_title
                ep.transcode_status = "READY"
            else:
                ep = VideoEpisode(
                    video_id=video.id,
                    episode_num=ep_num,
                    title=ep_title,
                    raw_file_path=vf["path"],
                    duration_seconds=120,
                    transcode_status="READY"
                )
                db.add(ep)
                added_count += 1

        return {
            "video_id": video.id,
            "title": clean_title,
            "category": category,
            "total_episodes": len(video_files),
            "new_episodes_added": added_count,
            "cover_url": cover_url,
            "extra_images_count": len(extra_image_urls),
            "skipped": False
        }

    def _group_collection_files(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for item in items:
            name = item.get("name", "")
            if item.get("is_dir") or not name.lower().endswith((".mp4", ".mov", ".mkv")):
                continue

            if "我推的孩子" in name:
                groups.setdefault("我推的孩子 第一季", []).append(item)
            elif "俄语" in name or "艾莉同学" in name:
                groups.setdefault("不时轻声用俄语遮羞的邻桌艾莉同学", []).append(item)
        return groups

    async def _sync_collection_group(
        self, db: Session, base_path: str, title: str, files: List[Dict[str, Any]], creator_id: str, mode: str = "incremental"
    ) -> Optional[Dict[str, Any]]:
        parsed = []
        for f in files:
            fname = f.get("name", "")
            ep_num = self._extract_episode_number(fname)
            parsed.append({
                "name": fname,
                "path": f"{base_path}/{fname}",
                "ep_num": ep_num
            })
        parsed.sort(key=lambda x: x["ep_num"])

        existing_video = db.query(Video).filter(Video.title == title).first()
        if mode == "incremental" and existing_video:
            ep_count = db.query(VideoEpisode).filter(VideoEpisode.video_id == existing_video.id).count()
            if ep_count >= len(parsed):
                return {
                    "video_id": existing_video.id,
                    "title": title,
                    "category": existing_video.category,
                    "total_episodes": ep_count,
                    "new_episodes_added": 0,
                    "cover_url": existing_video.cover_url,
                    "skipped": True
                }

        cover_url = DRAMA_COVERS.get("我推的孩子") if "我推" in title else DRAMA_COVERS.get("艾莉同学")

        if not existing_video:
            video = Video(
                creator_id=creator_id,
                title=title,
                summary=f"夸克云盘超清正版转存 · 《{title}》· 原声精选连载",
                cover_url=cover_url,
                category="动漫番剧",
                status="PUBLISHED",
                total_episodes=len(parsed),
                view_count=52000,
                like_count=3400
            )
            db.add(video)
            db.flush()
        else:
            video = existing_video

        existing_eps = {ep.episode_num: ep for ep in db.query(VideoEpisode).filter(VideoEpisode.video_id == video.id).all()}
        added_count = 0
        for item in parsed:
            num = item["ep_num"]
            if num in existing_eps:
                ep = existing_eps[num]
                ep.raw_file_path = item["path"]
                ep.transcode_status = "READY"
            else:
                ep = VideoEpisode(
                    video_id=video.id,
                    episode_num=num,
                    title=f"第{num}集",
                    raw_file_path=item["path"],
                    duration_seconds=1420,
                    transcode_status="READY"
                )
                db.add(ep)
                added_count += 1

        return {
            "video_id": video.id,
            "title": title,
            "category": "动漫番剧",
            "total_episodes": len(parsed),
            "new_episodes_added": added_count,
            "cover_url": cover_url,
            "skipped": False
        }

    def _extract_episode_number(self, filename: str) -> int:
        m = re.search(r"第\s*(\d+)\s*集", filename)
        if m:
            return int(m.group(1))
        m = re.search(r"(\d+)\s*集", filename)
        if m:
            return int(m.group(1))
        m = re.search(r"^(\d+)\.", filename)
        if m:
            return int(m.group(1))
        m = re.search(r"(\d+)", filename)
        if m:
            return int(m.group(1))
        return 1

cloud_drama_sync = CloudDramaSyncService()
