import os
import shutil
import json
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.video import VideoEpisode, Video
from app.services.openlist_storage import openlist_storage

logger = logging.getLogger(__name__)

class TranscodeService:
    def __init__(self):
        self.temp_dir = os.path.join(settings.UPLOAD_DIR, "processing")
        os.makedirs(self.temp_dir, exist_ok=True)

    def get_video_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract duration, resolution, codecs via ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", check=True)
            info = json.loads(result.stdout)
            
            format_info = info.get("format", {})
            duration = float(format_info.get("duration", 0.0))
            
            video_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
            width = int(video_stream.get("width", 0))
            height = int(video_stream.get("height", 0))
            codec = video_stream.get("codec_name", "unknown")
            
            return {
                "duration": duration,
                "width": width,
                "height": height,
                "codec": codec,
                "bitrate": int(format_info.get("bit_rate", 0))
            }
        except Exception as e:
            logger.warning(f"ffprobe extraction failed for {file_path}: {e}")
            return {"duration": 0.0, "width": 0, "height": 0, "codec": "unknown", "bitrate": 0}

    def generate_poster(self, file_path: str, output_poster_path: str, timestamp_sec: float = 1.0) -> str:
        """Extract a frame at timestamp_sec as poster image."""
        os.makedirs(os.path.dirname(output_poster_path), exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(timestamp_sec),
            "-i", file_path,
            "-vframes", "1",
            "-q:v", "2",
            output_poster_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return output_poster_path

    def transcode_to_hls(self, file_path: str, output_dir: str, segment_duration: int = 4) -> str:
        """Convert video to HLS (.m3u8 and .ts slices)."""
        os.makedirs(output_dir, exist_ok=True)
        m3u8_path = os.path.join(output_dir, "index.m3u8")
        segment_pattern = os.path.join(output_dir, "seg_%03d.ts")
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", file_path,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-hls_time", str(segment_duration),
            "-hls_list_size", "0",
            "-hls_segment_filename", segment_pattern,
            m3u8_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return m3u8_path

    async def process_episode_pipeline(self, episode_id: str, raw_merged_path: str) -> bool:
        """
        Execute full asynchronous transcode & sync pipeline:
        1. Set status to PROCESSING
        2. Extract metadata & generate poster
        3. Transcode to HLS
        4. Upload poster & raw video / HLS to Unicom Cloud Disk (WoPan)
        5. Update episode status to READY
        6. Clean up temporary local files
        """
        db = SessionLocal()
        episode_work_dir = os.path.join(self.temp_dir, episode_id)
        os.makedirs(episode_work_dir, exist_ok=True)
        
        try:
            episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
            if not episode:
                logger.error(f"Episode {episode_id} not found in database.")
                return False

            episode.transcode_status = "PROCESSING"
            db.commit()
            logger.info(f"Processing episode {episode_id} pipeline...")

            # 1. Metadata extraction
            metadata = self.get_video_metadata(raw_merged_path)
            duration_sec = int(metadata.get("duration", 0))

            # 2. Poster extraction
            poster_path = os.path.join(episode_work_dir, "poster.jpg")
            try:
                self.generate_poster(raw_merged_path, poster_path, timestamp_sec=min(1.0, max(0.0, metadata["duration"] / 2)))
            except Exception as e:
                logger.warning(f"Poster extraction failed: {e}")

            # 3. Transcode to HLS
            hls_dir = os.path.join(episode_work_dir, "hls")
            try:
                self.transcode_to_hls(raw_merged_path, hls_dir)
            except Exception as e:
                logger.warning(f"HLS transcoding error, falling back to raw video stream: {e}")

            # 4. Upload to China Unicom Cloud Disk via OpenList
            # Upload raw file
            remote_filename = f"{episode_id}.mp4"
            remote_raw_path = f"/wopan/视频资源/{remote_filename}"
            await openlist_storage.upload_file_from_path(remote_raw_path, raw_merged_path)

            # Upload poster if available
            remote_poster_path = None
            if os.path.exists(poster_path):
                remote_poster_path = f"/wopan/视频资源/{episode_id}_poster.jpg"
                try:
                    await openlist_storage.upload_file_from_path(remote_poster_path, poster_path)
                except Exception as e:
                    logger.warning(f"Poster upload to cloud failed: {e}")

            # 5. Update Database Record
            episode.transcode_status = "READY"
            episode.duration_seconds = duration_sec
            episode.raw_file_path = remote_raw_path
            episode.m3u8_url = f"/api/v1/videos/stream/{episode_id}"

            # Also update parent video's cover if not set
            video = db.query(Video).filter(Video.id == episode.video_id).first()
            if video and not video.cover_url and remote_poster_path:
                video.cover_url = remote_poster_path

            db.commit()
            logger.info(f"Episode {episode_id} pipeline completed successfully and synced to Unicom Cloud Disk!")
            return True

        except Exception as e:
            logger.exception(f"Error during episode {episode_id} pipeline: {e}")
            db.rollback()
            episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
            if episode:
                episode.transcode_status = "FAILED"
                db.commit()
            return False

        finally:
            db.close()
            # Clean up local temporary working files to preserve zero local disk footprint
            try:
                if os.path.exists(episode_work_dir):
                    shutil.rmtree(episode_work_dir, ignore_errors=True)
                if os.path.exists(raw_merged_path):
                    os.remove(raw_merged_path)
            except Exception as e:
                logger.warning(f"Temporary file cleanup warning: {e}")

transcode_service = TranscodeService()
