import uuid
from app.core.database import SessionLocal, init_db
from app.models.user import User
from app.models.video import Video, VideoEpisode

def seed():
    init_db()
    db = SessionLocal()
    try:
        # 1. Ensure a default creator user exists
        creator = db.query(User).filter(User.username == "admin").first()
        if not creator:
            creator = User(
                id=str(uuid.uuid4()),
                username="admin",
                password_hash="pbkdf2:dummy",
                role="ADMIN",
                nickname="系统创作者"
            )
            db.add(creator)
            db.commit()
            db.refresh(creator)
            print(f"Created creator user: {creator.username} (id: {creator.id})")

        # 2. Check if the video record exists
        video_title = "乘风2026精彩时刻"
        video = db.query(Video).filter(Video.title == video_title).first()
        if not video:
            video = Video(
                id=str(uuid.uuid4()),
                creator_id=creator.id,
                title=video_title,
                summary="中国联通云盘直链高码率短剧测试集（来自乘风2026精彩时刻-雨爱）",
                category="精选短剧",
                status="PUBLISHED",
                total_episodes=1,
                view_count=100
            )
            db.add(video)
            db.commit()
            db.refresh(video)
            print(f"Created video: {video.title} (id: {video.id})")

        # 3. Check if episode exists
        episode = db.query(VideoEpisode).filter(VideoEpisode.video_id == video.id).first()
        if not episode:
            episode = VideoEpisode(
                id=str(uuid.uuid4()),
                video_id=video.id,
                episode_num=1,
                title="第1集：雨爱初相遇",
                raw_file_path="/wopan/乘风2026精彩时刻-雨爱.mp4",
                duration_seconds=185,
                transcode_status="READY"
            )
            db.add(episode)
            db.commit()
            db.refresh(episode)
            print(f"Created episode: {episode.title} (id: {episode.id})")
        else:
            print(f"Existing episode found: {episode.title} (id: {episode.id})")

        return episode.id
    finally:
        db.close()

if __name__ == "__main__":
    ep_id = seed()
    print("SEED_COMPLETE_EPISODE_ID:", ep_id)
