"""
Script to purge all historical fabricated mock subtitle records from MySQL table video_subtitle_timelines.
CinemaAgent Milestone 1 Remediation.
"""

import os
import sys

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.core.database import SessionLocal
from app.models.video import VideoSubtitleTimeline

FORBIDDEN_KEYWORDS = [
    "三年隐忍",
    "退婚",
    "黑卡",
    "懦夫",
    "动我兄弟者",
    "龙王",
    "草芥",
    "少主",
    "至尊黑卡",
    "十万将士"
]

def purge_fake_subtitles() -> int:
    with SessionLocal() as db:
        all_subs = db.query(VideoSubtitleTimeline).all()
        print(f"Total subtitle records before purge: {len(all_subs)}")

        deleted_count = 0
        for sub in all_subs:
            content = sub.content or ""
            if any(keyword in content for keyword in FORBIDDEN_KEYWORDS):
                print(f"Deleting fake subtitle [{sub.id}]: speaker='{sub.speaker}', content='{content[:40]}...'")
                db.delete(sub)
                deleted_count += 1
            else:
                # If there are any other legacy mock subtitles in video_subtitle_timelines
                print(f"Inspecting non-keyword subtitle [{sub.id}]: {content[:40]}")

        db.commit()
        print(f"Purged {deleted_count} fake subtitle records.")

        # Double check remaining rows
        remaining = db.query(VideoSubtitleTimeline).all()
        print(f"Remaining subtitle records after purge: {len(remaining)}")
        assert len(remaining) == 0, f"Expected 0 subtitle rows, got {len(remaining)}"
        print("DATABASE PURGE VERIFIED: 0 fake subtitles remain in video_subtitle_timelines.")
        return deleted_count

if __name__ == "__main__":
    purge_fake_subtitles()
