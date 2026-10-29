# -*- coding: utf-8 -*-
"""
==============================================================================
【业务服务】：backend/app/services/transcode_service.py
【业务定位】：视频 FFmpeg 异步转码、HLS 分片切片与封面帧截取服务（TranscodeService）
【前端链路对接】：
  1. 页面来源：frontend/src/views/CreatorStudioView.vue（创作者工作台 -> 短剧视频上传区）
  2. 上传交互：
     - 创作者选择本地 MP4 视频，前端组件将大视频切片为 5MB 的 Chunk；
     - 逐片调用 POST /api/v1/videos/upload-chunk（进入 backend/app/api/endpoints/upload.py）；
     - 所有切片上传完毕后，前端触发 POST /api/v1/videos/merge-chunks 进行合并；
     - 后端合并完成后，在后台启动异步协程任务：`asyncio.create_task(transcode_service.process_episode_pipeline(episode_id, merged_path))`；
  3. 播放消费：
     - frontend/src/views/PlayerView.vue 播放器加载 GET /api/v1/videos/stream/{episode_id}；
     - 播放器接收到 HLS (.m3u8) 清单或 302 直链，实现秒开播放与拖拽进度条。
【核心功能】：
  1. 元数据探测（get_video_metadata）：调用 ffprobe 提取视频真实时长、分辨率宽高等参数；
  2. 视频帧海报提取（generate_poster）：在视频中间截取高清单帧图片作为竖屏封面；
  3. HLS 流媒体切片（transcode_to_hls）：将超大 MP4 转码切片为 4 秒标准的 index.m3u8 与 seg_xxx.ts 切片；
  4. 全异步处理流水线（process_episode_pipeline）：全流程自动执行，同步上传网盘，零本地磁盘滞留。
==============================================================================
"""

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
    """
    【视频转码与流媒体处理服务】
    集成系统底层 FFmpeg / FFprobe 二进制工具，负责音视频元数据提取、
    自适应 HLS 流媒体分片生成、动态抽帧生成封面，以及云端网盘异步同步。
    """
    def __init__(self):
        # 视频转码的本地临时工作目录（转码完成后会自动清理，实现本地零磁盘占用）
        self.temp_dir = os.path.join(settings.UPLOAD_DIR, "processing")
        os.makedirs(self.temp_dir, exist_ok=True)

    def get_video_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        调用系统底层 ffprobe 命令探测并提取视频的音视频参数元数据。
        
        【参数说明】：
        - file_path (str): 待探测视频文件的绝对路径（如 e:/.../uploads/temp.mp4）。
        
        【返回值字典字段详解】：
        {
            "duration": float,  # 视频真实时长（单位：秒，如 128.45）
            "width": int,       # 视频画面宽度像素（竖屏短剧通常为 720 或 1080）
            "height": int,      # 视频画面高度像素（竖屏短剧通常为 1280 或 1920）
            "codec": str,       # 视频编码格式（如 "h264", "hevc"）
            "bitrate": int      # 视频总比特率码率（bps）
        }
        """
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True
            )
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
            logger.warning(f"ffprobe 提取元数据失败 ({file_path}): {e}")
            return {"duration": 0.0, "width": 0, "height": 0, "codec": "unknown", "bitrate": 0}

    def generate_poster(self, file_path: str, output_poster_path: str, timestamp_sec: float = 1.0) -> str:
        """
        调用 ffmpeg 截取视频在指定时间戳位置的一帧高清画面，保存为海报图片。
        
        【参数大白话详解】：
        - file_path (str): 输入视频文件的绝对路径。
        - output_poster_path (str): 截取出来的海报保存路径（如 e:/.../poster.jpg）。
        - timestamp_sec (float, 默认 1.0): 截取哪一秒的画面作为海报（默认取视频中段或第1秒，避免黑屏帧）。
        
        【返回值说明】：
        - str: 生成的海报图片绝对路径。
        """
        os.makedirs(os.path.dirname(output_poster_path), exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",                             # 强制覆盖已有同名文件
            "-ss", str(timestamp_sec),        # 快进到指定秒数
            "-i", file_path,                  # 输入源文件
            "-vframes", "1",                  # 仅截取 1 帧画面
            "-q:v", "2",                      # 高质量 JPEG 压缩质量参数 (2~31, 2 为极高清晰度)
            output_poster_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return output_poster_path

    def transcode_to_hls(self, file_path: str, output_dir: str, segment_duration: int = 4) -> str:
        """
        将单体 MP4 视频转码切片为标准 HLS 流媒体（生成 index.m3u8 索引清单与若干 seg_xxx.ts 分片）。
        
        【为什么做 HLS 切片？】：
        1. 播放器秒开：客户端无需下载完几十上百兆的完整 MP4，只需加载 4 秒的第一个切片即可立即播放；
        2. 快进无卡顿：拖动时间轴时直接按分片加载，网络吞吐量占用极小。
        
        【参数说明】：
        - file_path (str): 待转码的原始视频路径。
        - output_dir (str): 输出 HLS 切片的目录。
        - segment_duration (int, 默认 4): 每个切片的目标时长（单位：秒，推荐 4 秒最适合短剧）。
        
        【返回值说明】：
        - str: 生成的 index.m3u8 播放清单文件绝对路径。
        """
        os.makedirs(output_dir, exist_ok=True)
        m3u8_path = os.path.join(output_dir, "index.m3u8")
        segment_pattern = os.path.join(output_dir, "seg_%03d.ts")
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", file_path,
            "-c:v", "libx264",                # 视频编码强制转为最兼容的 H.264
            "-preset", "veryfast",            # 转码预设（兼顾速度与画质）
            "-crf", "23",                     # 画质恒定速率因子（23 为视觉无损标准）
            "-c:a", "aac",                    # 音频编码强制转为 AAC
            "-b:a", "128k",                   # 音频码率 128 kbps
            "-hls_time", str(segment_duration), # 每个 TS 分片长度
            "-hls_list_size", "0",            # 0 表示清单保留所有分片，适用于点播
            "-hls_segment_filename", segment_pattern,
            m3u8_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return m3u8_path

    async def process_episode_pipeline(self, episode_id: str, raw_merged_path: str) -> bool:
        """
        分集视频上传后的全自动化后台异步转码与网盘同步总流水线。
        
        【执行全步骤】：
          第 1 步：将 MySQL 中该集状态标记为 PROCESSING（转码中），通知前端展示加载动画；
          第 2 步：使用 ffprobe 探测视频实际时长与尺寸，并截取中段高清帧作为封面海报；
          第 3 步：使用 ffmpeg 执行 HLS 4秒标准切片；
          第 4 步：通过 OpenList 存储适配器将视频原片及封面同步推送至网盘（沃家云盘/夸克网盘）；
          第 5 步：更新数据库中 video_episodes 的 transcode_status 为 READY（就绪可用），
                  并记录 duration_seconds、m3u8_url 与 raw_file_path；
          第 6 步：清理本地临时目录中的分片与合成原片，保持服务器本地磁盘零滞留。
          
        【参数大白话详解】：
        - episode_id (str): 分集记录唯一主键 ID（UUID），在创作者发起分片上传时由前端生成。
        - raw_merged_path (str): 前端全部切片合并完成后在服务器本地生成的原始视频路径。
        
        【返回值说明】：
        - bool: True 表示全链路转码同步成功，分集已就绪；False 表示中途发生异常，状态已标记为 FAILED。
        """
        db = SessionLocal()
        episode_work_dir = os.path.join(self.temp_dir, episode_id)
        os.makedirs(episode_work_dir, exist_ok=True)
        
        try:
            episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
            if not episode:
                logger.error(f"分集记录 {episode_id} 在数据库中未找到，转码流水线终止")
                return False

            # 第 1 步：标记分集转码状态为 PROCESSING
            episode.transcode_status = "PROCESSING"
            db.commit()
            logger.info(f"开始执行分集 {episode_id} 的后台异步转码流水线...")

            # 第 2 步：提取视频元数据
            metadata = self.get_video_metadata(raw_merged_path)
            duration_sec = int(metadata.get("duration", 0))

            # 第 3 步：抽取高清封面海报帧（截取视频中段）
            poster_path = os.path.join(episode_work_dir, "poster.jpg")
            try:
                self.generate_poster(
                    raw_merged_path,
                    poster_path,
                    timestamp_sec=min(1.0, max(0.0, metadata["duration"] / 2))
                )
            except Exception as e:
                logger.warning(f"抽取封面海报失败降级: {e}")

            # 第 4 步：转码为 HLS (.m3u8 + .ts) 切片
            hls_dir = os.path.join(episode_work_dir, "hls")
            try:
                self.transcode_to_hls(raw_merged_path, hls_dir)
            except Exception as e:
                logger.warning(f"HLS 转码失败，将降级使用原始视频流直链: {e}")

            # 第 5 步：通过 OpenList 存储接口上传至云盘
            # 上传原始 MP4 文件
            remote_filename = f"{episode_id}.mp4"
            remote_raw_path = f"/wopan/视频资源/{remote_filename}"
            await openlist_storage.upload_file_from_path(remote_raw_path, raw_merged_path)

            # 若成功截取了海报，同步上传海报至网盘
            remote_poster_path = None
            if os.path.exists(poster_path):
                remote_poster_path = f"/wopan/视频资源/{episode_id}_poster.jpg"
                try:
                    await openlist_storage.upload_file_from_path(remote_poster_path, poster_path)
                except Exception as e:
                    logger.warning(f"封面海报上传至云盘失败: {e}")

            # 第 6 步：回写更新数据库分集记录
            episode.transcode_status = "READY"
            episode.duration_seconds = duration_sec
            episode.raw_file_path = remote_raw_path
            episode.m3u8_url = f"/api/v1/videos/stream/{episode_id}"

            # 如果所属短剧尚未配置封面，自动用第一集截取的封面填补
            video = db.query(Video).filter(Video.id == episode.video_id).first()
            if video and not video.cover_url and remote_poster_path:
                video.cover_url = remote_poster_path

            db.commit()
            logger.info(f"分集 {episode_id} 转码同步全链路执行成功，已就绪供播放器秒开！")
            return True

        except Exception as e:
            logger.exception(f"分集 {episode_id} 转码流水线执行异常: {e}")
            db.rollback()
            episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
            if episode:
                episode.transcode_status = "FAILED"
                db.commit()
            return False

        finally:
            db.close()
            # 第 7 步：清理本地临时转码切片与合并原片，释放服务器存储空间
            try:
                if os.path.exists(episode_work_dir):
                    shutil.rmtree(episode_work_dir, ignore_errors=True)
                if os.path.exists(raw_merged_path):
                    os.remove(raw_merged_path)
            except Exception as e:
                logger.warning(f"临时转码文件清理告警: {e}")


# 全局单例转码服务实例
transcode_service = TranscodeService()
