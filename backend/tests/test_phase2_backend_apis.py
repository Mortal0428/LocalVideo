"""
Phase 2 Milestone 1 Comprehensive Backend Integration Test Suite.
Verifies all 13 Features:
1. Two-Tier Comments DB Model & Relationships
2. Comment Likes DB Model & Persistence Deduplication
3. Two-Tier Comments APIs (GET nested tree, POST reply with notifications)
4. Video Likes Persistence & Heat Score Recalculation
5. Coin Economy Models (Wallet, Ledger, Initial Bonus)
6. Video Coin Tip Model & Heat Score Recalculation
7. Coin Economy APIs (Wallet, Transactions, Sign-in, Ad, VIP exchange)
8. Video Tip APIs (1 or 2 coins, max 2 limit, wallet deduction, heat_score update)
9. System Announcements Models & Admin CRUD/Retract APIs
10. User Notifications Models & APIs (List, Unread Counter, Read Single/All)
11. Admin Full User CRUD APIs (Create, Edit profile/coins/VIP, Hard Delete)
12. Local Secure Image Upload API & Static /storage Mount Check
13. User History & Likes 500 Bug Fixes & Profile Coins/VIP Fields
"""

import io
import os
import sys
import uuid
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from main import app
from app.core.database import SessionLocal, init_db
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.video import Video, VideoEpisode
from app.models.interaction import UserComment, UserLike, CommentLike, UserWatchHistory
from app.models.coin import UserCoinWallet, UserCoinTransaction, VideoCoinTip
from app.models.notification import SystemAnnouncement, UserNotification

@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)

@pytest.fixture(scope="module")
def admin_user():
    init_db()
    with SessionLocal() as db:
        username = f"admin_{uuid.uuid4().hex[:8]}"
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=get_password_hash("AdminPass123!"),
            nickname="超级管理员",
            role="ADMIN",
            status="ACTIVE"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(data={"sub": user.id})
        yield {"id": user.id, "username": username, "token": token}

@pytest.fixture(scope="module")
def user_a():
    init_db()
    with SessionLocal() as db:
        username = f"user_a_{uuid.uuid4().hex[:8]}"
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=get_password_hash("Password123!"),
            nickname="观众小张",
            role="USER",
            status="ACTIVE"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(data={"sub": user.id})
        yield {"id": user.id, "username": username, "token": token}

@pytest.fixture(scope="module")
def user_b():
    init_db()
    with SessionLocal() as db:
        username = f"user_b_{uuid.uuid4().hex[:8]}"
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=get_password_hash("Password123!"),
            nickname="剧迷小李",
            role="USER",
            status="ACTIVE"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(data={"sub": user.id})
        yield {"id": user.id, "username": username, "token": token}

@pytest.fixture(scope="module")
def sample_drama(admin_user):
    init_db()
    with SessionLocal() as db:
        drama = Video(
            id=str(uuid.uuid4()),
            title=f"测试微短剧_{uuid.uuid4().hex[:6]}",
            summary="这是一部用于 Phase 2 自动化测试的短剧",
            cover_url="/storage/test_cover.jpg",
            category="现代都市",
            status="PUBLISHED",
            creator_id=admin_user["id"],
            view_count=100,
            like_count=10,
            coin_count=0,
            heat_score=150.0
        )
        db.add(drama)
        db.flush()

        ep1 = VideoEpisode(
            id=str(uuid.uuid4()),
            video_id=drama.id,
            episode_num=1,
            title="第1集 龙王归来",
            raw_file_path="/storage/test.mp4",
            duration_seconds=120,
            transcode_status="READY"
        )
        ep2 = VideoEpisode(
            id=str(uuid.uuid4()),
            video_id=drama.id,
            episode_num=2,
            title="第2集 风云突变",
            raw_file_path="/storage/test2.mp4",
            duration_seconds=115,
            transcode_status="READY"
        )
        db.add(ep1)
        db.add(ep2)
        db.commit()

        yield {"id": drama.id, "title": drama.title, "ep1_id": ep1.id, "ep2_id": ep2.id}


# =========================================================
# 1. Coin Economy Tests (Features 5, 7)
# =========================================================
def test_coin_wallet_initial_bonus_and_query(client, user_a):
    headers = {"Authorization": f"Bearer {user_a['token']}"}
    res = client.get("/api/v1/user/coins/wallet", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["balance"] == 50
    assert data["total_earned"] == 50
    assert data["total_spent"] == 0
    assert data["has_signed_today"] is False

def test_daily_sign_in_and_idempotency(client, user_a):
    headers = {"Authorization": f"Bearer {user_a['token']}"}
    # First sign-in: +10 coins
    res1 = client.post("/api/v1/user/coins/sign-in", headers=headers)
    assert res1.status_code == 200
    assert res1.json()["data"]["balance"] == 60
    assert res1.json()["data"]["has_signed_today"] is True

    # Duplicate sign-in attempt on same day must be rejected
    res2 = client.post("/api/v1/user/coins/sign-in", headers=headers)
    assert res2.status_code == 400
    assert "今日已完成签到" in res2.json()["detail"]

def test_watch_ad_reward(client, user_a):
    headers = {"Authorization": f"Bearer {user_a['token']}"}
    # Watch ad: +5 coins
    res = client.post("/api/v1/user/coins/watch-ad", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["balance"] == 65

def test_coin_transactions_ledger(client, user_a):
    headers = {"Authorization": f"Bearer {user_a['token']}"}
    res = client.get("/api/v1/user/coins/transactions", headers=headers)
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    types = [t["transaction_type"] for t in items]
    assert "REGISTER_BONUS" in types
    assert "SIGN_IN" in types
    assert "AD_REWARD" in types

def test_exchange_vip_insufficient_and_success(client, user_a, admin_user):
    headers_a = {"Authorization": f"Bearer {user_a['token']}"}
    headers_admin = {"Authorization": f"Bearer {admin_user['token']}"}

    # Current balance is 65, 7 days VIP requires 100 coins -> should fail
    res_fail = client.post("/api/v1/user/coins/exchange-vip", json={"days": 7}, headers=headers_a)
    assert res_fail.status_code == 400
    assert "金币余额不足" in res_fail.json()["detail"]

    # Admin adjusts User A coins to 350
    res_adjust = client.put(
        f"/api/v1/admin/users/{user_a['id']}",
        json={"coins": 350},
        headers=headers_admin
    )
    assert res_adjust.status_code == 200
    assert res_adjust.json()["data"]["coins"] == 350

    # User A exchanges 7 days VIP (costs 100 coins)
    res_vip7 = client.post("/api/v1/user/coins/exchange-vip", json={"days": 7}, headers=headers_a)
    assert res_vip7.status_code == 200
    assert res_vip7.json()["data"]["balance"] == 250
    vip_expire_1 = res_vip7.json()["data"]["vip_expire_at"]
    assert vip_expire_1 != ""

    # User A exchanges 30 days VIP (costs 200 coins)
    res_vip30 = client.post("/api/v1/user/coins/exchange-vip", json={"days": 30}, headers=headers_a)
    assert res_vip30.status_code == 200
    assert res_vip30.json()["data"]["balance"] == 50
    vip_expire_2 = res_vip30.json()["data"]["vip_expire_at"]
    assert vip_expire_2 > vip_expire_1


# =========================================================
# 2. Two-Tier Comments & Comment Likes Tests (Features 1, 2, 3)
# =========================================================
def test_two_tier_comment_tree_and_notifications(client, user_a, user_b, sample_drama):
    headers_a = {"Authorization": f"Bearer {user_a['token']}"}
    headers_b = {"Authorization": f"Bearer {user_b['token']}"}
    ep_id = sample_drama["ep1_id"]

    # 1. User A posts a root comment (Level 1)
    res_c1 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "这是小张发表的主楼评论，剧情真好看！"},
        headers=headers_a
    )
    assert res_c1.status_code == 200
    root_id = res_c1.json()["data"]["id"]
    assert root_id != ""

    # 2. User B replies to User A's root comment (Level 2)
    res_c2 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={
            "content": "小李回复小张：确实，男主出场很帅！",
            "parent_id": root_id,
            "root_id": root_id,
            "reply_to_user_id": user_a["id"]
        },
        headers=headers_b
    )
    assert res_c2.status_code == 200
    reply1_id = res_c2.json()["data"]["id"]

    # 3. User A replies to User B's reply (nested Level 2, should flatten root_id to root_id)
    res_c3 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={
            "content": "@剧迷小李 听说第二集更有意思呢！",
            "parent_id": reply1_id,
            "reply_to_user_id": user_b["id"]
        },
        headers=headers_a
    )
    assert res_c3.status_code == 200
    reply2_data = res_c3.json()["data"]
    assert reply2_data["root_id"] == root_id
    assert reply2_data["parent_id"] == reply1_id

    # 4. Query comments tree: verify root comment contains nested replies
    res_tree = client.get(f"/api/v1/interactions/episodes/{ep_id}/comments", headers=headers_a)
    assert res_tree.status_code == 200
    tree_data = res_tree.json()["data"]
    items = tree_data["items"]
    target_root = next((item for item in items if item["id"] == root_id), None)
    assert target_root is not None
    assert target_root["reply_count"] >= 2
    reply_ids = [r["id"] for r in target_root["replies"]]
    assert reply1_id in reply_ids
    assert reply2_data["id"] in reply_ids

    # 5. Verify User A received a REPLY notification from User B
    res_notif = client.get("/api/v1/notifications?category=REPLY", headers=headers_a)
    assert res_notif.status_code == 200
    notif_items = res_notif.json()["data"]["items"]
    assert any(
        n["category"] == "REPLY" and ("回复" in n["title"] or "回复" in n["content"])
        for n in notif_items
    )

def test_comment_like_toggle_and_deduplication(client, user_a, user_b, sample_drama):
    headers_a = {"Authorization": f"Bearer {user_a['token']}"}
    headers_b = {"Authorization": f"Bearer {user_b['token']}"}
    ep_id = sample_drama["ep1_id"]

    # User A creates a comment
    res_c = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "点赞测试评论"},
        headers=headers_a
    )
    comment_id = res_c.json()["data"]["id"]

    # User B likes comment: like_count -> 1
    res_like1 = client.post(f"/api/v1/interactions/comments/{comment_id}/like", headers=headers_b)
    assert res_like1.status_code == 200
    assert res_like1.json()["data"]["is_liked"] is True
    assert res_like1.json()["data"]["like_count"] == 1

    # User B likes comment again: toggle off, like_count -> 0
    res_like2 = client.post(f"/api/v1/interactions/comments/{comment_id}/like", headers=headers_b)
    assert res_like2.status_code == 200
    assert res_like2.json()["data"]["is_liked"] is False
    assert res_like2.json()["data"]["like_count"] == 0

    # User B likes again to leave it liked
    client.post(f"/api/v1/interactions/comments/{comment_id}/like", headers=headers_b)
    res_check = client.get(f"/api/v1/interactions/episodes/{ep_id}/comments", headers=headers_b)
    comment_item = next(c for c in res_check.json()["data"]["items"] if c["id"] == comment_id)
    assert comment_item["is_liked"] is True


# =========================================================
# 3. Video Likes & Heat Score Recalculation (Feature 4)
# =========================================================
def test_video_like_status_and_heat_score(client, user_a, sample_drama):
    headers = {"Authorization": f"Bearer {user_a['token']}"}
    ep_id = sample_drama["ep1_id"]

    # Initial like status
    res_status = client.get(f"/api/v1/interactions/episodes/{ep_id}/like-status", headers=headers)
    assert res_status.status_code == 200
    initial_likes = res_status.json()["data"]["like_count"]

    # Toggle like -> True
    res_toggle1 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/like",
        json={},
        headers=headers
    )
    assert res_toggle1.status_code == 200
    assert res_toggle1.json()["data"]["is_liked"] is True
    assert res_toggle1.json()["data"]["like_count"] == initial_likes + 1
    assert res_toggle1.json()["data"]["heat_score"] > 0

    # Toggle like -> False
    res_toggle2 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/like",
        json={},
        headers=headers
    )
    assert res_toggle2.status_code == 200
    assert res_toggle2.json()["data"]["is_liked"] is False
    assert res_toggle2.json()["data"]["like_count"] == initial_likes


# =========================================================
# 4. Video Coin Tipping & Boundary Checks (Features 6, 8)
# =========================================================
def test_video_coin_tipping_and_max_limit(client, user_b, sample_drama):
    headers = {"Authorization": f"Bearer {user_b['token']}"}
    ep_id = sample_drama["ep1_id"]

    # Check initial tip status
    res_init = client.get(f"/api/v1/interactions/episodes/{ep_id}/tip-status", headers=headers)
    assert res_init.status_code == 200
    assert res_init.json()["data"]["tipped_count"] == 0
    assert res_init.json()["data"]["max_allowed"] == 2

    # 0. Unauthenticated attempt -> MUST be rejected with 401
    res_unauth = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/tip",
        json={"coin_amount": 1}
    )
    assert res_unauth.status_code == 401

    # Tip 1 coin
    res_tip1 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/tip",
        json={"coin_amount": 1},
        headers=headers
    )
    assert res_tip1.status_code == 200
    data1 = res_tip1.json()["data"]
    assert data1["tipped_count"] == 1
    assert data1["video_coin_count"] >= 1
    heat_score_1 = data1["heat_score"]

    # Tip second coin
    res_tip2 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/tip",
        json={"coin_amount": 1},
        headers=headers
    )
    assert res_tip2.status_code == 200
    data2 = res_tip2.json()["data"]
    assert data2["tipped_count"] == 2
    assert data2["heat_score"] > heat_score_1

    # Attempt to tip a 3rd coin -> MUST be rejected with 400
    res_tip3 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/tip",
        json={"coin_amount": 1},
        headers=headers
    )
    assert res_tip3.status_code == 400
    assert "最多打赏 2 枚金币" in res_tip3.json()["detail"] or "每部短剧" in res_tip3.json()["detail"]


# =========================================================
# 5. System Announcements & User Notifications (Features 9, 10)
# =========================================================
def test_announcements_and_notifications_lifecycle(client, admin_user, user_a):
    headers_admin = {"Authorization": f"Bearer {admin_user['token']}"}
    headers_a = {"Authorization": f"Bearer {user_a['token']}"}

    # 1. Admin creates announcement
    res_create = client.post(
        "/api/v1/admin/announcements",
        json={
            "title": "系统维护通知",
            "content": "我们将于本周日凌晨进行数据库优化维护。",
            "tag": "维护通知"
        },
        headers=headers_admin
    )
    assert res_create.status_code == 200
    announcement_id = res_create.json()["data"]["id"]

    # 2. User A receives announcement notification
    res_notifs = client.get("/api/v1/notifications", headers=headers_a)
    assert res_notifs.status_code == 200
    items = res_notifs.json()["data"]["items"]
    target_notif = next((n for n in items if n["announcement_id"] == announcement_id), None)
    assert target_notif is not None
    assert target_notif["category"] == "ANNOUNCEMENT"
    notif_id = target_notif["id"]

    # 3. Check unread count
    res_unread = client.get("/api/v1/notifications/unread-count", headers=headers_a)
    assert res_unread.status_code == 200
    assert res_unread.json()["data"]["total"] >= 1

    # 4. Mark single read
    res_read1 = client.post(f"/api/v1/notifications/{notif_id}/read", headers=headers_a)
    assert res_read1.status_code == 200
    assert res_read1.json()["data"]["is_read"] is True

    # 5. Mark all read
    res_readall = client.post("/api/v1/notifications/read-all", json={}, headers=headers_a)
    assert res_readall.status_code == 200

    # Verify unread count is zero
    res_unread2 = client.get("/api/v1/notifications/unread-count", headers=headers_a)
    assert res_unread2.json()["data"]["total"] == 0

    # 6. Admin retracts announcement
    res_retract = client.post(f"/api/v1/admin/announcements/{announcement_id}/retract", headers=headers_admin)
    assert res_retract.status_code == 200
    assert res_retract.json()["data"]["is_published"] is False

    # 7. Admin deletes announcement
    res_del = client.delete(f"/api/v1/admin/announcements/{announcement_id}", headers=headers_admin)
    assert res_del.status_code == 200


# =========================================================
# 6. Admin Full User CRUD (Feature 11)
# =========================================================
def test_admin_user_crud(client, admin_user):
    headers = {"Authorization": f"Bearer {admin_user['token']}"}
    target_username = f"crud_user_{uuid.uuid4().hex[:6]}"

    # 1. Create user
    res_create = client.post(
        "/api/v1/admin/users",
        json={
            "username": target_username,
            "password": "InitialPass123!",
            "nickname": "新进会员",
            "role": "USER",
            "coins": 88,
            "vip_days": 10
        },
        headers=headers
    )
    assert res_create.status_code == 200
    created_user = res_create.json()["data"]
    created_id = created_user["id"]
    assert created_user["coins"] == 88
    assert created_user["vip_expire_at"] is not None

    # Verify user can log in with initial credentials
    res_login = client.post(
        "/api/v1/auth/login",
        json={"username": target_username, "password": "InitialPass123!"}
    )
    assert res_login.status_code == 200

    # 2. Update user profile, password, status, and coins
    res_update = client.put(
        f"/api/v1/admin/users/{created_id}",
        json={
            "nickname": "高级会员小王",
            "password": "NewSecretPass456!",
            "status": "ACTIVE",
            "coins": 188,
            "vip_days": 20
        },
        headers=headers
    )
    assert res_update.status_code == 200
    updated_data = res_update.json()["data"]
    assert updated_data["nickname"] == "高级会员小王"
    assert updated_data["coins"] == 188

    # Verify new password works
    res_login2 = client.post(
        "/api/v1/auth/login",
        json={"username": target_username, "password": "NewSecretPass456!"}
    )
    assert res_login2.status_code == 200

    # 3. Hard delete user
    res_del = client.delete(f"/api/v1/admin/users/{created_id}", headers=headers)
    assert res_del.status_code == 200
    assert res_del.json()["data"]["id"] == created_id

    # Verify user is deleted
    res_check = client.get(f"/api/v1/admin/users?search={target_username}", headers=headers)
    assert res_check.json()["data"]["total"] == 0


# =========================================================
# 7. Local Secure Image Upload & Static Mount (Feature 12)
# =========================================================
def test_image_upload_and_static_serving(client, admin_user):
    headers = {"Authorization": f"Bearer {admin_user['token']}"}

    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    # 0. Unauthenticated upload attempt -> MUST be rejected with 401
    res_unauth = client.post("/api/v1/upload/image", files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")})
    assert res_unauth.status_code == 401

    # 1. Valid image upload (PNG)
    files = {"file": ("test_poster.png", io.BytesIO(png_bytes), "image/png")}
    res_upload = client.post("/api/v1/upload/image", files=files, headers=headers)
    assert res_upload.status_code == 200
    image_url = res_upload.json()["url"]
    assert image_url.startswith("/storage/uploads/images/")
    assert image_url.endswith(".png")

    # 2. Verify image is accessible via mounted static route /storage
    res_static = client.get(image_url)
    assert res_static.status_code == 200
    assert len(res_static.content) == len(png_bytes)

    # 3. Invalid extension should be rejected
    files_invalid = {"file": ("malicious.exe", io.BytesIO(b"MZ..."), "application/octet-stream")}
    res_invalid = client.post("/api/v1/upload/image", files=files_invalid, headers=headers)
    assert res_invalid.status_code == 400
    assert "不支持的图片格式" in res_invalid.json()["detail"]


# =========================================================
# 8. User Watch History, Likes, and Profile Bug Fixes (Feature 13)
# =========================================================
def test_user_history_and_likes_no_attribute_error(client, user_a, sample_drama):
    headers = {"Authorization": f"Bearer {user_a['token']}"}
    ep_id = sample_drama["ep1_id"]

    # Record heartbeat so user has a watch history
    res_hb = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/heartbeat",
        json={"progress_seconds": 45.0},
        headers=headers
    )
    assert res_hb.status_code == 200

    # Ensure user has a like
    client.post(f"/api/v1/interactions/episodes/{ep_id}/like", json={}, headers=headers)

    # 1. GET /api/v1/user/history -> MUST NOT throw AttributeError 500
    res_hist = client.get("/api/v1/user/history", headers=headers)
    assert res_hist.status_code == 200
    hist_items = res_hist.json()["data"]
    assert len(hist_items) >= 1
    assert "video_id" in hist_items[0]
    assert "episode_id" in hist_items[0]

    # 2. GET /api/v1/user/likes -> MUST NOT throw AttributeError 500
    res_likes = client.get("/api/v1/user/likes", headers=headers)
    assert res_likes.status_code == 200
    like_items = res_likes.json()["data"]
    assert len(like_items) >= 1
    assert "video_id" in like_items[0]
    assert "episode_id" in like_items[0]

    # 3. GET /api/v1/user/profile -> returns coins and vip fields
    res_prof = client.get("/api/v1/user/profile", headers=headers)
    assert res_prof.status_code == 200
    prof_data = res_prof.json()["data"]
    assert "coins" in prof_data
    assert "vip_expire_at" in prof_data
    assert "is_vip" in prof_data
    assert prof_data["coins"] >= 0


# =========================================================
# 9. Admin Drama Edit & Options Dropdown
# =========================================================
def test_admin_drama_edit_and_options(client, admin_user, sample_drama):
    headers = {"Authorization": f"Bearer {admin_user['token']}"}
    drama_id = sample_drama["id"]

    # 1. Update drama metadata
    res_update = client.put(
        f"/api/v1/admin/dramas/{drama_id}",
        json={
            "title": "短剧升级版标题",
            "category": "古装悬疑",
            "summary": "更新后的完整短剧简介内容",
            "cover_url": "/storage/uploads/images/new_cover.jpg",
            "status": "PUBLISHED"
        },
        headers=headers
    )
    assert res_update.status_code == 200
    d = res_update.json()["data"]
    assert d["title"] == "短剧升级版标题"
    assert d["category"] == "古装悬疑"
    assert d["summary"] == "更新后的完整短剧简介内容"
    assert d["cover_url"] == "/storage/uploads/images/new_cover.jpg"

    # 2. Query drama options dropdown
    res_opt = client.get("/api/v1/admin/dramas/options", headers=headers)
    assert res_opt.status_code == 200
    options = res_opt.json()["data"]
    assert len(options) >= 1
    target = next((o for o in options if o["id"] == drama_id), None)
    assert target is not None
    assert target["title"] == "短剧升级版标题"
