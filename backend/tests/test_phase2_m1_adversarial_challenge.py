"""
Phase 2 Milestone 1 Adversarial Empirical Challenge Test Suite (Challenger 2).

Adversarial testing targets:
1. Two-tier comment tree aggregation and deep reply flattening (replying to reply, depth 4).
2. Comment tree multi-root isolation & empty content input validation.
3. Comment like deduplication under rapid toggling (21x alternation) and multi-user isolation.
4. Image upload security: invalid extensions matrix (.exe, .sh, .bat, .php, .svg, double extensions, uppercase).
5. Image upload payload boundary limits (exactly 10MB accepted, 10MB + 1 byte rejected, 15MB rejected).
6. Image upload path traversal defense & UUID filename sanitization.
7. User hard deletion cascade integrity across all child tables (comments, replies, likes, tips, transactions, notifications, history, favorites) without foreign key violations or 500 crashes.
8. Admin self-deletion defense and non-existent user handling.
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
from app.models.interaction import UserComment, UserLike, CommentLike, UserWatchHistory, VideoDanmaku
from app.models.coin import UserCoinWallet, UserCoinTransaction, VideoCoinTip
from app.models.notification import UserNotification
from app.models.favorite import FavoriteFolder, FavoriteItem


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def create_test_user(role="USER", nickname="测试用户", prefix="adv_user"):
    with SessionLocal() as db:
        unique_name = f"{prefix}_{uuid.uuid4().hex[:8]}"
        user = User(
            id=str(uuid.uuid4()),
            username=unique_name,
            password_hash=get_password_hash("AdvPass123!"),
            nickname=nickname,
            role=role,
            status="ACTIVE"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(data={"sub": user.id})
        return {"id": user.id, "username": unique_name, "nickname": nickname, "token": token}


@pytest.fixture(scope="module")
def admin_user():
    init_db()
    return create_test_user(role="ADMIN", nickname="测试超级管理员", prefix="admin")


@pytest.fixture(scope="module")
def user_a():
    return create_test_user(role="USER", nickname="挑刺小张", prefix="user_a")


@pytest.fixture(scope="module")
def user_b():
    return create_test_user(role="USER", nickname="测试小李", prefix="user_b")


@pytest.fixture(scope="module")
def user_c():
    return create_test_user(role="USER", nickname="挑刺小王", prefix="user_c")


@pytest.fixture(scope="module")
def user_d():
    return create_test_user(role="USER", nickname="测试小赵", prefix="user_d")


@pytest.fixture(scope="module")
def sample_drama(admin_user):
    init_db()
    with SessionLocal() as db:
        drama = Video(
            id=str(uuid.uuid4()),
            title=f"对抗测试短剧_{uuid.uuid4().hex[:6]}",
            summary="用于 Challenger 2 对抗性测试的短剧专辑",
            cover_url="/storage/test_cover.jpg",
            category="悬疑推理",
            status="PUBLISHED",
            creator_id=admin_user["id"],
            view_count=50,
            like_count=5,
            coin_count=0,
            heat_score=75.0
        )
        db.add(drama)
        db.flush()

        ep1 = VideoEpisode(
            id=str(uuid.uuid4()),
            video_id=drama.id,
            episode_num=1,
            title="第1集 对抗启幕",
            raw_file_path="/storage/adv_test1.mp4",
            duration_seconds=90,
            transcode_status="READY"
        )
        db.add(ep1)
        db.commit()

        return {"id": drama.id, "title": drama.title, "ep1_id": ep1.id}


# ==============================================================================
# 1. Two-Tier Comment Tree & Deep Reply Flattening Tests (R1)
# ==============================================================================
def test_adv_comment_deep_reply_flattening_depth_4(client, user_a, user_b, user_c, user_d, sample_drama):
    """
    Stress-test deep reply chain flattening:
    - User A posts Root comment (Level 1)
    - User B replies to Root (Level 2)
    - User C replies to User B's reply (Level 3 logical -> flattened to Level 2)
    - User D replies to User C's reply (Level 4 logical -> flattened to Level 2)
    Verify:
    1. All replies have root_id locked to User A's root comment ID.
    2. parent_id correctly chains to the immediate parent.
    3. reply_to_user_id correctly reflects the immediate target user.
    4. Aggregated tree returns exactly 1 root item with 3 ordered replies.
    5. Notifications are accurately dispatched to the immediate parent user.
    """
    ep_id = sample_drama["ep1_id"]
    h_a = {"Authorization": f"Bearer {user_a['token']}"}
    h_b = {"Authorization": f"Bearer {user_b['token']}"}
    h_c = {"Authorization": f"Bearer {user_c['token']}"}
    h_d = {"Authorization": f"Bearer {user_d['token']}"}

    # Step 1: User A posts Root comment
    res_c0 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "【深度测试】User A发表的主楼根评论"},
        headers=h_a
    )
    assert res_c0.status_code == 200
    c0 = res_c0.json()["data"]
    root_id = c0["id"]
    assert c0["root_id"] is None
    assert c0["parent_id"] is None

    # Step 2: User B replies to User A (Level 2)
    res_c1 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={
            "content": "User B回复User A的根评论",
            "parent_id": root_id,
            "root_id": root_id,
            "reply_to_user_id": user_a["id"]
        },
        headers=h_b
    )
    assert res_c1.status_code == 200
    c1 = res_c1.json()["data"]
    assert c1["root_id"] == root_id
    assert c1["parent_id"] == root_id
    assert c1["reply_to_user_id"] == user_a["id"]

    # Step 3: User C replies to User B's reply (Deep reply Level 3)
    # Notice: C only passes parent_id=c1["id"] without root_id; backend must automatically collapse root_id
    res_c2 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={
            "content": "User C回复User B的回复（第3层嵌套）",
            "parent_id": c1["id"],
            "reply_to_user_id": user_b["id"]
        },
        headers=h_c
    )
    assert res_c2.status_code == 200
    c2 = res_c2.json()["data"]
    assert c2["root_id"] == root_id, "Backend MUST defensively flatten root_id to top-level comment"
    assert c2["parent_id"] == c1["id"]
    assert c2["reply_to_user_id"] == user_b["id"]
    assert c2["reply_to_username"] == user_b["username"]

    # Step 4: User D replies to User C's reply (Deep reply Level 4)
    res_c3 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={
            "content": "User D回复User C的回复（第4层嵌套，完全扁平化）",
            "parent_id": c2["id"],
            "reply_to_user_id": user_c["id"]
        },
        headers=h_d
    )
    assert res_c3.status_code == 200
    c3 = res_c3.json()["data"]
    assert c3["root_id"] == root_id, "Backend MUST collapse Level 4 reply's root_id to top-level root_id"
    assert c3["parent_id"] == c2["id"]
    assert c3["reply_to_user_id"] == user_c["id"]
    assert c3["reply_to_username"] == user_c["username"]

    # Step 5: Query aggregated comment tree
    res_tree = client.get(f"/api/v1/interactions/episodes/{ep_id}/comments", headers=h_a)
    assert res_tree.status_code == 200
    tree_items = res_tree.json()["data"]["items"]

    target_root = next((item for item in tree_items if item["id"] == root_id), None)
    assert target_root is not None
    assert target_root["reply_count"] == 3
    assert len(target_root["replies"]) == 3

    replies_by_id = {r["id"]: r for r in target_root["replies"]}
    assert set(replies_by_id.keys()) == {c1["id"], c2["id"], c3["id"]}

    # Check reply c1 (User B)
    r1 = replies_by_id[c1["id"]]
    assert r1["root_id"] == root_id
    assert r1["parent_id"] == root_id
    assert r1["user_id"] == user_b["id"]
    assert r1["reply_to_user_id"] == user_a["id"]

    # Check reply c2 (User C replying to B)
    r2 = replies_by_id[c2["id"]]
    assert r2["root_id"] == root_id
    assert r2["parent_id"] == c1["id"]
    assert r2["user_id"] == user_c["id"]
    assert r2["reply_to_user_id"] == user_b["id"]
    assert r2["reply_to_username"] == user_b["username"]

    # Check reply c3 (User D replying to C)
    r3 = replies_by_id[c3["id"]]
    assert r3["root_id"] == root_id
    assert r3["parent_id"] == c2["id"]
    assert r3["user_id"] == user_d["id"]
    assert r3["reply_to_user_id"] == user_c["id"]
    assert r3["reply_to_username"] == user_c["username"]

    # Step 6: Verify notifications are accurately targeted
    # User B should have received a REPLY notification from User C
    res_notif_b = client.get("/api/v1/notifications?category=REPLY", headers=h_b)
    assert res_notif_b.status_code == 200
    b_notifs = res_notif_b.json()["data"]["items"]
    assert any(n["sender_id"] == user_c["id"] and "User C" in n["content"] for n in b_notifs)

    # User C should have received a REPLY notification from User D
    res_notif_c = client.get("/api/v1/notifications?category=REPLY", headers=h_c)
    assert res_notif_c.status_code == 200
    c_notifs = res_notif_c.json()["data"]["items"]
    assert any(n["sender_id"] == user_d["id"] and "User D" in n["content"] for n in c_notifs)


def test_adv_comment_independent_trees_isolation(client, user_a, user_b, sample_drama):
    """
    Verify two distinct root comment trees do not cross-pollinate replies.
    """
    ep_id = sample_drama["ep1_id"]
    h_a = {"Authorization": f"Bearer {user_a['token']}"}
    h_b = {"Authorization": f"Bearer {user_b['token']}"}

    # Root Alpha
    r_alpha = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "Root Alpha Tree"},
        headers=h_a
    ).json()["data"]["id"]

    # Root Beta
    r_beta = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "Root Beta Tree"},
        headers=h_b
    ).json()["data"]["id"]

    # Reply to Alpha
    client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "Reply to Alpha 1", "parent_id": r_alpha},
        headers=h_b
    )
    client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "Reply to Alpha 2", "parent_id": r_alpha},
        headers=h_a
    )

    # Reply to Beta
    client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "Reply to Beta 1", "parent_id": r_beta},
        headers=h_a
    )

    res_tree = client.get(f"/api/v1/interactions/episodes/{ep_id}/comments", headers=h_a)
    assert res_tree.status_code == 200
    items = {item["id"]: item for item in res_tree.json()["data"]["items"]}

    assert items[r_alpha]["reply_count"] == 2
    assert len(items[r_alpha]["replies"]) == 2
    assert all(r["root_id"] == r_alpha for r in items[r_alpha]["replies"])

    assert items[r_beta]["reply_count"] == 1
    assert len(items[r_beta]["replies"]) == 1
    assert items[r_beta]["replies"][0]["root_id"] == r_beta


def test_adv_comment_empty_and_whitespace_rejection(client, user_a, sample_drama):
    """
    Verify empty or whitespace-only comment submissions are rejected with HTTP 400.
    """
    ep_id = sample_drama["ep1_id"]
    h = {"Authorization": f"Bearer {user_a['token']}"}

    res1 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": ""},
        headers=h
    )
    assert res1.status_code == 400

    res2 = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "   \n\t   "},
        headers=h
    )
    assert res2.status_code == 400


# ==============================================================================
# 2. Comment Like Rapid Toggling & Idempotency Tests (R1)
# ==============================================================================
def test_adv_comment_like_rapid_toggling_21_times(client, user_a, user_b, sample_drama):
    """
    Rapid toggling stress test (21 sequential flips).
    Assert like_count never drifts, alternates cleanly between (True, 1) and (False, 0),
    and correctly reflects in the comments query.
    """
    ep_id = sample_drama["ep1_id"]
    h_a = {"Authorization": f"Bearer {user_a['token']}"}
    h_b = {"Authorization": f"Bearer {user_b['token']}"}

    # User A creates a comment
    res_c = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "高频点赞切换对抗测试评论"},
        headers=h_a
    )
    assert res_c.status_code == 200
    comment_id = res_c.json()["data"]["id"]

    # Toggle 21 times sequentially
    for i in range(1, 22):
        res = client.post(f"/api/v1/interactions/comments/{comment_id}/like", headers=h_b)
        assert res.status_code == 200
        data = res.json()["data"]

        expected_liked = (i % 2 == 1)
        expected_count = 1 if expected_liked else 0

        assert data["is_liked"] == expected_liked, f"Failed at toggle iteration {i}: expected is_liked={expected_liked}"
        assert data["like_count"] == expected_count, f"Failed at toggle iteration {i}: expected like_count={expected_count}"

    # After 21 toggles, state should be liked (count=1)
    res_tree = client.get(f"/api/v1/interactions/episodes/{ep_id}/comments", headers=h_b)
    target = next(c for c in res_tree.json()["data"]["items"] if c["id"] == comment_id)
    assert target["is_liked"] is True
    assert target["like_count"] == 1

    # 22nd toggle should revert to unliked (count=0)
    res_22 = client.post(f"/api/v1/interactions/comments/{comment_id}/like", headers=h_b)
    assert res_22.status_code == 200
    assert res_22.json()["data"]["is_liked"] is False
    assert res_22.json()["data"]["like_count"] == 0


def test_adv_comment_like_multi_user_isolation(client, user_a, user_b, user_c, sample_drama):
    """
    Test multi-user like isolation and decrement boundary safety.
    """
    ep_id = sample_drama["ep1_id"]
    h_a = {"Authorization": f"Bearer {user_a['token']}"}
    h_b = {"Authorization": f"Bearer {user_b['token']}"}
    h_c = {"Authorization": f"Bearer {user_c['token']}"}

    res_c = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "多人点赞隔离测试评论"},
        headers=h_a
    )
    comment_id = res_c.json()["data"]["id"]

    # User A likes -> 1
    r_a1 = client.post(f"/api/v1/interactions/comments/{comment_id}/like", headers=h_a)
    assert r_a1.json()["data"]["like_count"] == 1

    # User B likes -> 2
    r_b1 = client.post(f"/api/v1/interactions/comments/{comment_id}/like", headers=h_b)
    assert r_b1.json()["data"]["like_count"] == 2

    # User C likes -> 3
    r_c1 = client.post(f"/api/v1/interactions/comments/{comment_id}/like", headers=h_c)
    assert r_c1.json()["data"]["like_count"] == 3

    # User A unlikes -> 2
    r_a2 = client.post(f"/api/v1/interactions/comments/{comment_id}/like", headers=h_a)
    assert r_a2.json()["data"]["like_count"] == 2
    assert r_a2.json()["data"]["is_liked"] is False

    # Check that User B and User C still see is_liked=True
    tree_b = client.get(f"/api/v1/interactions/episodes/{ep_id}/comments", headers=h_b)
    item_b = next(c for c in tree_b.json()["data"]["items"] if c["id"] == comment_id)
    assert item_b["is_liked"] is True
    assert item_b["like_count"] == 2

    # User B unlikes -> 1
    client.post(f"/api/v1/interactions/comments/{comment_id}/like", headers=h_b)
    # User C unlikes -> 0
    r_c2 = client.post(f"/api/v1/interactions/comments/{comment_id}/like", headers=h_c)
    assert r_c2.json()["data"]["like_count"] == 0
    assert r_c2.json()["data"]["is_liked"] is False


# ==============================================================================
# 3. Image Upload Security & Payload Boundary Tests (R4)
# ==============================================================================
def test_adv_image_upload_invalid_extensions_matrix(client, admin_user):
    """
    Adversarial matrix of invalid and dangerous extensions.
    Every one MUST be rejected with HTTP 400.
    """
    headers = {"Authorization": f"Bearer {admin_user['token']}"}

    forbidden_filenames = [
        "malware.exe",
        "shell.sh",
        "script.bat",
        "webshell.php",
        "backdoor.py",
        "vector.svg",
        "index.html",
        "payload.js",
        "library.dll",
        "no_extension_file",
        "sneaky.jpg.exe",
        "sneaky.png.sh",
        "UPPERCASE_MALWARE.EXE",
        "test.php5",
        "script.vbs"
    ]

    for fname in forbidden_filenames:
        files = {"file": (fname, io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00"), "application/octet-stream")}
        res = client.post("/api/v1/upload/image", files=files, headers=headers)
        assert res.status_code == 400, f"Expected 400 rejection for forbidden file '{fname}', got {res.status_code}"
        assert "不支持的图片格式" in res.json()["detail"]


def test_adv_image_upload_payload_boundary_and_size_limits(client, admin_user):
    """
    Test exact 10MB boundary and oversized payloads:
    1. Exactly 10MB (10 * 1024 * 1024 bytes) -> Accepted (200).
    2. 10MB + 1 byte -> Rejected (400, '图片大小超出限制').
    3. 12MB -> Rejected (400).
    """
    headers = {"Authorization": f"Bearer {admin_user['token']}"}

    # 1. Exactly 10MB payload
    exact_10mb = 10 * 1024 * 1024
    content_10mb = b"X" * exact_10mb
    files_10mb = {"file": ("exact_10mb.jpg", io.BytesIO(content_10mb), "image/jpeg")}
    res_10mb = client.post("/api/v1/upload/image", files=files_10mb, headers=headers)
    assert res_10mb.status_code == 200, f"Expected 200 for exact 10MB, got {res_10mb.status_code}"
    url_10mb = res_10mb.json()["url"]
    assert url_10mb.startswith("/storage/uploads/images/")

    # Verify static serving can retrieve it
    res_get_10mb = client.get(url_10mb)
    assert res_get_10mb.status_code == 200
    assert len(res_get_10mb.content) == exact_10mb

    # 2. 10MB + 1 byte payload
    oversized_1byte = exact_10mb + 1
    content_over_1byte = b"X" * oversized_1byte
    files_over = {"file": ("over_1byte.jpg", io.BytesIO(content_over_1byte), "image/jpeg")}
    res_over = client.post("/api/v1/upload/image", files=files_over, headers=headers)
    assert res_over.status_code == 400, f"Expected 400 for 10MB + 1 byte, got {res_over.status_code}"
    assert "图片大小超出限制" in res_over.json()["detail"]

    # 3. 12MB payload
    content_12mb = b"X" * (12 * 1024 * 1024)
    files_12mb = {"file": ("large_12mb.png", io.BytesIO(content_12mb), "image/png")}
    res_12mb = client.post("/api/v1/upload/image", files=files_12mb, headers=headers)
    assert res_12mb.status_code == 400
    assert "图片大小超出限制" in res_12mb.json()["detail"]


def test_adv_image_upload_security_filename_sanitization(client, admin_user):
    """
    Test path traversal in filename parameter (e.g. '../../etc/passwd.jpg' or '..\\win.png').
    Verify uploaded asset is safely isolated with a UUID-based name and does not leak outside uploads directory.
    """
    headers = {"Authorization": f"Bearer {admin_user['token']}"}

    traversal_filenames = [
        "../../../../etc/passwd.jpg",
        "..\\..\\..\\windows\\system32\\cmd.png",
        "sub/folder/trick.webp"
    ]

    for fname in traversal_filenames:
        files = {"file": (fname, io.BytesIO(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01"), "image/jpeg")}
        res = client.post("/api/v1/upload/image", files=files, headers=headers)
        assert res.status_code == 200

        data = res.json()["data"]
        returned_filename = data["filename"]
        returned_url = data["url"]

        # Filename MUST NOT contain traversal characters
        assert ".." not in returned_filename
        assert "/" not in returned_filename
        assert "\\" not in returned_filename
        assert returned_url.startswith("/storage/uploads/images/")


# ==============================================================================
# 4. User Hard Deletion Cascade Integrity & RBAC Tests (R4)
# ==============================================================================
def test_adv_user_hard_delete_complex_cascade(client, admin_user, sample_drama):
    """
    Stress-test user hard deletion with an intricate relational dependency graph:
    - User has wallet, coin transactions, tips
    - User has video like, watch history
    - User has favorite folder + items
    - User has danmaku
    - User has root comments and replies
    - Other users have commented on User's comments
    - Other users have liked User's comments
    - User has liked other users' comments
    - User has incoming and outgoing notifications
    Verify:
    1. DELETE /api/v1/admin/users/{id} completes with HTTP 200 without raising DB Foreign Key violation or 500 error.
    2. User is cleanly purged from users table.
    3. Associated private records (wallet, tips, history, favorites) are purged.
    4. Surviving peer comments can still be queried via GET /comments without 500 crashes.
    """
    admin_headers = {"Authorization": f"Bearer {admin_user['token']}"}
    ep_id = sample_drama["ep1_id"]

    # 1. Create Victim User and Peer User
    victim = create_test_user(role="USER", nickname="受害测试用户", prefix="victim")
    peer = create_test_user(role="USER", nickname="旁观同行用户", prefix="peer")
    v_headers = {"Authorization": f"Bearer {victim['token']}"}
    p_headers = {"Authorization": f"Bearer {peer['token']}"}

    # 2. Populate Victim: Coin wallet and tip
    res_tip = client.post(f"/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 1}, headers=v_headers)
    assert res_tip.status_code == 200

    # 3. Populate Victim: Video like
    client.post(f"/api/v1/interactions/episodes/{ep_id}/like", json={}, headers=v_headers)

    # 4. Populate Victim: Watch history
    client.post(f"/api/v1/interactions/episodes/{ep_id}/heartbeat", json={"progress_seconds": 45.0}, headers=v_headers)

    # 5. Populate Victim: Favorite folder & item
    with SessionLocal() as db:
        folder = FavoriteFolder(
            id=str(uuid.uuid4()),
            user_id=victim["id"],
            name="受害者专属收藏夹",
            is_default=True
        )
        db.add(folder)
        db.flush()
        item = FavoriteItem(
            id=str(uuid.uuid4()),
            folder_id=folder.id,
            video_id=sample_drama["id"],
            user_id=victim["id"]
        )
        db.add(item)

        # 6. Danmaku
        danmaku = VideoDanmaku(
            id=str(uuid.uuid4()),
            episode_id=ep_id,
            user_id=victim["id"],
            time_offset=12.5,
            content="受害者发送的弹幕"
        )
        db.add(danmaku)
        db.commit()

    # 7. Comments & Cross-User Interactions:
    # Victim posts Root comment C_v
    res_cv = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "受害者发表的主楼评论"},
        headers=v_headers
    )
    assert res_cv.status_code == 200
    c_v_id = res_cv.json()["data"]["id"]

    # Peer posts Root comment C_p
    res_cp = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "同行用户发表的主楼评论"},
        headers=p_headers
    )
    assert res_cp.status_code == 200
    c_p_id = res_cp.json()["data"]["id"]

    # Peer replies to Victim's comment (reply_to_user_id = victim)
    res_p_reply = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "同行回复受害者", "parent_id": c_v_id, "reply_to_user_id": victim["id"]},
        headers=p_headers
    )
    assert res_p_reply.status_code == 200
    p_reply_id = res_p_reply.json()["data"]["id"]

    # Victim replies to Peer's comment (reply_to_user_id = peer)
    res_v_reply = client.post(
        f"/api/v1/interactions/episodes/{ep_id}/comments",
        json={"content": "受害者回复同行", "parent_id": c_p_id, "reply_to_user_id": peer["id"]},
        headers=v_headers
    )
    assert res_v_reply.status_code == 200

    # Peer likes Victim's comment C_v
    client.post(f"/api/v1/interactions/comments/{c_v_id}/like", headers=p_headers)

    # Victim likes Peer's comment C_p
    client.post(f"/api/v1/interactions/comments/{c_p_id}/like", headers=v_headers)

    # Verify both have notifications
    notif_v = client.get("/api/v1/notifications", headers=v_headers).json()["data"]["items"]
    assert len(notif_v) > 0

    notif_p = client.get("/api/v1/notifications", headers=p_headers).json()["data"]["items"]
    assert len(notif_p) > 0

    # 8. NOW EXECUTE HARD DELETION AS ADMIN
    res_del = client.delete(f"/api/v1/admin/users/{victim['id']}", headers=admin_headers)
    assert res_del.status_code == 200, f"Admin delete failed with status {res_del.status_code}: {res_del.text}"
    del_data = res_del.json()
    assert del_data["code"] == 200
    assert del_data["data"]["id"] == victim["id"]

    # 9. Verify DB consistency:
    with SessionLocal() as db:
        # Victim user should be gone
        v_user = db.query(User).filter(User.id == victim["id"]).first()
        assert v_user is None

        # Victim wallet & transactions should be gone
        assert db.query(UserCoinWallet).filter(UserCoinWallet.user_id == victim["id"]).count() == 0
        assert db.query(UserCoinTransaction).filter(UserCoinTransaction.user_id == victim["id"]).count() == 0
        assert db.query(VideoCoinTip).filter(VideoCoinTip.user_id == victim["id"]).count() == 0
        assert db.query(UserLike).filter(UserLike.user_id == victim["id"]).count() == 0
        assert db.query(UserWatchHistory).filter(UserWatchHistory.user_id == victim["id"]).count() == 0
        assert db.query(FavoriteFolder).filter(FavoriteFolder.user_id == victim["id"]).count() == 0
        assert db.query(FavoriteItem).filter(FavoriteItem.user_id == victim["id"]).count() == 0
        assert db.query(VideoDanmaku).filter(VideoDanmaku.user_id == victim["id"]).count() == 0
        assert db.query(UserComment).filter(UserComment.user_id == victim["id"]).count() == 0
        # Child reply to victim's root comment must also be deleted (no orphaned comments)
        assert db.query(UserComment).filter(UserComment.id == p_reply_id).count() == 0

    # 10. Query comments tree after victim deletion: MUST NOT 500 crash
    res_tree_after = client.get(f"/api/v1/interactions/episodes/{ep_id}/comments", headers=p_headers)
    assert res_tree_after.status_code == 200
    remaining_items = res_tree_after.json()["data"]["items"]
    # Peer's root comment should still be intact
    assert any(c["id"] == c_p_id for c in remaining_items)


def test_adv_admin_delete_self_and_nonexistent(client, admin_user):
    """
    Verify RBAC safeguards on admin hard deletion:
    1. Admin cannot delete their own account (HTTP 400).
    2. Deleting nonexistent user returns HTTP 404.
    """
    admin_headers = {"Authorization": f"Bearer {admin_user['token']}"}

    # 1. Admin attempts self deletion
    res_self = client.delete(f"/api/v1/admin/users/{admin_user['id']}", headers=admin_headers)
    assert res_self.status_code == 400
    assert "管理员不能删除当前登录的管理员账号" in res_self.json()["detail"]

    # 2. Admin attempts nonexistent user deletion
    non_existent_id = str(uuid.uuid4())
    res_non = client.delete(f"/api/v1/admin/users/{non_existent_id}", headers=admin_headers)
    assert res_non.status_code == 404
    assert "目标用户不存在" in res_non.json()["detail"]
