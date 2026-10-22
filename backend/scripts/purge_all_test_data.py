import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.abspath('backend'))
from app.core.database import SessionLocal

GENUINE_DRAMA_IDS = (
    'f1a94b85-5493-4faf-8968-47a97cd7111f',  # 高冷千金的贴身高手
    '790b8f13-21a0-42ff-9e3a-8c243536a8e2',  # 高冷千金的贴身高手 第2季
    '2b575454-7946-4f28-a9d6-7bb043f01fac',  # 离婚后我在八零赚钱养家
    '48128d34-df76-4530-a1c0-c605293cf062',  # 离婚后我在八零赚钱养家 第2季
    '54d52ebd-f7e7-4979-8bc6-d1041a423276',  # 傲娇小厨师和他的吃货大明星
    '9fa190f0-0f82-42df-b825-1f5ce3c2beee',  # 穿成炮灰，我抢了原书男主的白月光
    '5f586a0c-294b-49ac-a25d-31ac131f12b7',  # 我推的孩子 第一季
    'b5eb0595-d16c-4f76-ae2b-1d5f5b49c7ca',  # 不时轻声用俄语遮羞的邻桌艾莉同学
    '03d2e4bb-1bd4-4f93-bfec-a4d4a4f28e5b',  # 自制合集 - 第2集：端到端分片上传与转码自测
    '11bc7906-0980-498a-9b98-8cc541a8cbb2',  # 乘风2026精彩时刻
)

GENUINE_USERNAMES = ('admin', 'creator', 'reviewer', 'viewer', 'mortal')

def purge_all_test_data():
    db = SessionLocal()
    try:
        print("Starting comprehensive database purge of all test data...")
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))

        # 1. Purge test users
        user_rows = db.execute(
            text(f"SELECT id FROM users WHERE username NOT IN {GENUINE_USERNAMES}")
        ).fetchall()
        del_user_ids = [r[0] for r in user_rows]
        print(f"Found {len(del_user_ids)} test users to delete.")

        if del_user_ids:
            chunk_size = 300
            for i in range(0, len(del_user_ids), chunk_size):
                chunk = tuple(del_user_ids[i:i + chunk_size])
                in_clause = f"({','.join([repr(x) for x in chunk])})"
                db.execute(text(f"DELETE FROM user_coin_transactions WHERE user_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM user_coin_wallets WHERE user_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM video_coin_tips WHERE user_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM user_comments WHERE user_id IN {in_clause} OR reply_to_user_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM user_likes WHERE user_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM comment_likes WHERE user_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM user_watch_histories WHERE user_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM user_notifications WHERE user_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM favorite_items WHERE user_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM favorite_folders WHERE user_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM content_reviews WHERE reviewer_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM video_danmakus WHERE user_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM users WHERE id IN {in_clause}"))

        # 2. Purge test dramas
        drama_rows = db.execute(
            text(f"SELECT id FROM videos WHERE id NOT IN {GENUINE_DRAMA_IDS}")
        ).fetchall()
        del_drama_ids = [r[0] for r in drama_rows]
        print(f"Found {len(del_drama_ids)} test dramas to delete.")

        if del_drama_ids:
            chunk_size = 300
            for i in range(0, len(del_drama_ids), chunk_size):
                chunk = tuple(del_drama_ids[i:i + chunk_size])
                in_clause = f"({','.join([repr(x) for x in chunk])})"

                ep_rows = db.execute(text(f"SELECT id FROM video_episodes WHERE video_id IN {in_clause}")).fetchall()
                del_ep_ids = [r[0] for r in ep_rows]
                if del_ep_ids:
                    ep_in_clause = f"({','.join([repr(x) for x in del_ep_ids])})"
                    db.execute(text(f"DELETE FROM video_subtitle_timelines WHERE episode_id IN {ep_in_clause}"))
                    db.execute(text(f"DELETE FROM video_danmakus WHERE episode_id IN {ep_in_clause}"))

                db.execute(text(f"DELETE FROM user_comments WHERE video_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM user_watch_histories WHERE video_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM user_likes WHERE video_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM video_coin_tips WHERE video_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM favorite_items WHERE video_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM system_carousels WHERE video_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM video_episodes WHERE video_id IN {in_clause}"))
                db.execute(text(f"DELETE FROM videos WHERE id IN {in_clause}"))

        # 3. Clean orphaned records
        db.execute(text("DELETE FROM user_notifications WHERE user_id NOT IN (SELECT id FROM users)"))
        db.execute(text("DELETE FROM user_comments WHERE user_id NOT IN (SELECT id FROM users)"))
        db.execute(text("DELETE FROM user_likes WHERE user_id NOT IN (SELECT id FROM users)"))
        db.execute(text("DELETE FROM video_coin_tips WHERE user_id NOT IN (SELECT id FROM users)"))
        db.execute(text("DELETE FROM user_coin_transactions WHERE user_id NOT IN (SELECT id FROM users)"))
        db.execute(text("DELETE FROM user_coin_wallets WHERE user_id NOT IN (SELECT id FROM users)"))

        # 4. Clean system carousels: Ensure 3 high-quality carousels pointing to genuine dramas
        db.execute(text("DELETE FROM system_carousels"))
        carousel_inserts = [
            (
                "car-top-01",
                "【绝美焦点】高冷千金的贴身高手",
                "全网热播超清画质，支持 16:9 与 9:16 自适应沉浸播放",
                "爆款推荐",
                "http://127.0.0.1:5244/p/kuake/项目开源目录/1000/1000_1.jpg",
                "f1a94b85-5493-4faf-8968-47a97cd7111f",
                1,
                6,
                1
            ),
            (
                "car-top-02",
                "【八零年代】离婚后我在八零赚钱养家",
                "时代年代逆袭巨作，120集完整剧集原画直连",
                "年代逆袭",
                "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1280&q=80",
                "2b575454-7946-4f28-a9d6-7bb043f01fac",
                2,
                5,
                1
            ),
            (
                "car-top-03",
                "【都市逆袭】傲娇小厨师和他的吃货大明星",
                "甜宠美食爆笑逆袭，AI 伴读与高能看点精准解析",
                "高分热榜",
                "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1280&q=80",
                "54d52ebd-f7e7-4979-8bc6-d1041a423276",
                3,
                5,
                1
            )
        ]
        for cid, title, subtitle, tag, cover_url, vid, order, duration, active in carousel_inserts:
            db.execute(text(f"""
                INSERT INTO system_carousels (id, title, subtitle, tag, cover_url, video_id, sort_order, duration_seconds, is_active, created_at, updated_at)
                VALUES ('{cid}', '{title}', '{subtitle}', '{tag}', '{cover_url}', '{vid}', {order}, {duration}, {active}, NOW(), NOW())
            """))

        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.commit()
        print("Database purge & carousel seed completed successfully!")

        # Final verification
        users = db.execute(text("SELECT id, username, role FROM users")).fetchall()
        dramas = db.execute(text("SELECT id, title, category FROM videos")).fetchall()
        carousels = db.execute(text("SELECT id, title, duration_seconds FROM system_carousels")).fetchall()

        print(f"\nFinal Verified State:")
        print(f"Users ({len(users)}):")
        for u in users:
            print(f"  {u[1]} ({u[2]}) - {u[0]}")
        print(f"Dramas ({len(dramas)}):")
        for d in dramas:
            print(f"  {d[1]} ({d[2]}) - {d[0]}")
        print(f"Carousels ({len(carousels)}):")
        for c in carousels:
            print(f"  {c[1]} - duration: {c[2]}s")

    except Exception as e:
        db.rollback()
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        print(f"Error: {e}")
        raise e
    finally:
        db.close()

if __name__ == '__main__':
    purge_all_test_data()
