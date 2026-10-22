"""
Unit test suite for Milestone 3 Favorites API endpoints.
Tests all 8 REST endpoints + quick default toggle + security & boundaries:
1. GET /api/v1/favorites/folders (auto-creates default folder)
2. POST /api/v1/favorites/folders (create folder, reject empty/duplicate)
3. PUT /api/v1/favorites/folders/{id} (rename, update privacy, protect default)
4. DELETE /api/v1/favorites/folders/{id} (delete custom, protect default)
5. GET /api/v1/favorites/folders/{id}/items (list items with video details)
6. POST /api/v1/favorites/items (add video to folder, idempotent)
7. DELETE /api/v1/favorites/items/{id} (remove item from folder)
8. GET /api/v1/favorites/status/{video_id} (check favorite status)
9. POST /api/v1/favorites/quick-default (1-click toggle default folder)
"""

import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from main import app
from app.core.database import SessionLocal, init_db
from app.core.security import create_access_token
from app.models.user import User
from app.models.video import Video, VideoEpisode
from app.models.favorite import FavoriteFolder, FavoriteItem


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


@pytest.fixture(scope="module")
def test_user():
    init_db()
    with SessionLocal() as db:
        username = f"fav_tester_{uuid.uuid4().hex[:8]}"
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash="testpasshash",
            nickname="收藏测试员",
            role="USER"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id
        token = create_access_token(data={"sub": user_id})
        yield {"id": user_id, "username": username, "token": token}


@pytest.fixture(scope="module")
def test_video(test_user):
    with SessionLocal() as db:
        vid = str(uuid.uuid4())
        video = Video(
            id=vid,
            creator_id=test_user["id"],
            title="测试专属高光短剧",
            summary="这是一部用于收藏夹自动化测试的真实短剧记录",
            cover_url="https://images.unsplash.com/photo-1518173946687-a4c8a383392e",
            category="都市逆袭",
            status="PUBLISHED",
            total_episodes=2
        )
        db.add(video)

        ep1 = VideoEpisode(
            id=str(uuid.uuid4()),
            video_id=vid,
            episode_num=1,
            title="测试第1集：风云际会",
            raw_file_path="/mock/ep1.mp4",
            duration_seconds=120,
            transcode_status="READY"
        )
        ep2 = VideoEpisode(
            id=str(uuid.uuid4()),
            video_id=vid,
            episode_num=2,
            title="测试第2集：绝地反击",
            raw_file_path="/mock/ep2.mp4",
            duration_seconds=150,
            transcode_status="READY"
        )
        db.add(ep1)
        db.add(ep2)
        db.commit()
        db.refresh(video)
        yield {"id": vid, "title": video.title, "ep1_id": ep1.id}


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# --- Test 1: Authentication enforcement ---
def test_unauthenticated_requests_rejected(client, test_video):
    r1 = client.get("/api/v1/favorites/folders")
    assert r1.status_code == 401, f"Expected 401, got {r1.status_code}"

    r2 = client.post("/api/v1/favorites/folders", json={"name": "新收藏夹"})
    assert r2.status_code == 401, f"Expected 401, got {r2.status_code}"

    # Status endpoint with no token returns unauthenticated payload
    r3 = client.get(f"/api/v1/favorites/status/{test_video['id']}")
    assert r3.status_code == 200
    assert r3.json().get("is_favorited") is False


# --- Test 2: List folders auto-creates default folder ---
def test_list_folders_auto_creates_default(client, test_user):
    headers = auth_headers(test_user["token"])
    resp = client.get("/api/v1/favorites/folders", headers=headers)
    assert resp.status_code == 200
    folders = resp.json()
    assert isinstance(folders, list)
    assert len(folders) >= 1

    default_folder = next((f for f in folders if f.get("is_default") is True), None)
    assert default_folder is not None, "Must auto-create a default folder"
    assert default_folder["name"] == "默认收藏夹"
    assert default_folder["is_public"] is False
    assert default_folder["item_count"] == 0


# --- Test 3: Create custom folder & input validation ---
def test_create_folder_success_and_validation(client, test_user):
    headers = auth_headers(test_user["token"])

    # Empty name rejected
    r_empty = client.post("/api/v1/favorites/folders", json={"name": "   "}, headers=headers)
    assert r_empty.status_code in [400, 422], f"Expected 400/422, got {r_empty.status_code}"

    # Valid folder creation
    custom_name = f"神剧精选_{uuid.uuid4().hex[:6]}"
    r_ok = client.post(
        "/api/v1/favorites/folders",
        json={"name": custom_name, "is_public": True, "description": "公开优质短剧列表"},
        headers=headers
    )
    assert r_ok.status_code == 201
    created = r_ok.json()
    assert created["name"] == custom_name
    assert created["is_public"] is True
    assert created["is_default"] is False

    # Duplicate name rejected
    r_dup = client.post(
        "/api/v1/favorites/folders",
        json={"name": custom_name, "is_public": False},
        headers=headers
    )
    assert r_dup.status_code == 400


# --- Test 4: Update custom folder & default folder protection ---
def test_update_folder_and_protection(client, test_user):
    headers = auth_headers(test_user["token"])

    # Get folders
    folders = client.get("/api/v1/favorites/folders", headers=headers).json()
    def_folder = next(f for f in folders if f["is_default"])
    custom_folder = next(f for f in folders if not f["is_default"])

    # Renaming default folder must be rejected
    r_rename_def = client.put(
        f"/api/v1/favorites/folders/{def_folder['id']}",
        json={"name": "尝试篡改默认夹"},
        headers=headers
    )
    assert r_rename_def.status_code == 400

    # Renaming custom folder succeeds
    new_name = f"更新后名称_{uuid.uuid4().hex[:6]}"
    r_up = client.put(
        f"/api/v1/favorites/folders/{custom_folder['id']}",
        json={"name": new_name, "description": "已更新说明"},
        headers=headers
    )
    assert r_up.status_code == 200
    assert r_up.json()["name"] == new_name
    assert r_up.json()["description"] == "已更新说明"


# --- Test 5: Add video to folder & check status ---
def test_add_item_and_check_status(client, test_user, test_video):
    headers = auth_headers(test_user["token"])

    # Initial status: not favorited
    s_init = client.get(f"/api/v1/favorites/status/{test_video['id']}", headers=headers)
    assert s_init.status_code == 200
    assert s_init.json()["is_favorited"] is False

    # Add to default folder
    folders = client.get("/api/v1/favorites/folders", headers=headers).json()
    def_folder = next(f for f in folders if f["is_default"])

    r_add = client.post(
        "/api/v1/favorites/items",
        json={"video_id": test_video["id"], "folder_id": def_folder["id"]},
        headers=headers
    )
    assert r_add.status_code == 201
    assert r_add.json()["success"] is True

    # Check status: now favorited
    s_after = client.get(f"/api/v1/favorites/status/{test_video['id']}", headers=headers)
    assert s_after.status_code == 200
    assert s_after.json()["is_favorited"] is True
    assert def_folder["id"] in s_after.json()["folder_ids"]

    # Re-adding same video is idempotent
    r_add_again = client.post(
        "/api/v1/favorites/items",
        json={"video_id": test_video["id"], "folder_id": def_folder["id"]},
        headers=headers
    )
    assert r_add_again.status_code == 201


# --- Test 6: List folder items with rich video details ---
def test_list_folder_items(client, test_user, test_video):
    headers = auth_headers(test_user["token"])
    folders = client.get("/api/v1/favorites/folders", headers=headers).json()
    def_folder = next(f for f in folders if f["is_default"])

    r_items = client.get(f"/api/v1/favorites/folders/{def_folder['id']}/items", headers=headers)
    assert r_items.status_code == 200
    items = r_items.json()
    assert isinstance(items, list)
    assert len(items) >= 1

    item = next(it for it in items if it["video_id"] == test_video["id"])
    assert item["video"]["id"] == test_video["id"]
    assert item["video"]["title"] == test_video["title"]
    assert item["video"]["first_episode_id"] is not None


# --- Test 7: Remove item from favorites ---
def test_remove_item(client, test_user, test_video):
    headers = auth_headers(test_user["token"])

    # Remove by video_id
    r_del = client.delete(f"/api/v1/favorites/items/{test_video['id']}", headers=headers)
    assert r_del.status_code == 200
    assert r_del.json()["success"] is True

    # Status updates to not favorited
    s_after = client.get(f"/api/v1/favorites/status/{test_video['id']}", headers=headers)
    assert s_after.status_code == 200
    assert s_after.json()["is_favorited"] is False


# --- Test 8: Quick default toggle ---
def test_quick_default_toggle(client, test_user, test_video):
    headers = auth_headers(test_user["token"])

    # Toggle ON
    r_toggle1 = client.post(
        "/api/v1/favorites/quick-default",
        json={"video_id": test_video["id"]},
        headers=headers
    )
    assert r_toggle1.status_code == 200
    assert r_toggle1.json()["is_favorited"] is True

    # Toggle OFF
    r_toggle2 = client.post(
        "/api/v1/favorites/quick-default",
        json={"video_id": test_video["id"]},
        headers=headers
    )
    assert r_toggle2.status_code == 200
    assert r_toggle2.json()["is_favorited"] is False


# --- Test 9: Delete custom folder vs delete default folder ---
def test_delete_folder(client, test_user):
    headers = auth_headers(test_user["token"])
    folders = client.get("/api/v1/favorites/folders", headers=headers).json()
    def_folder = next(f for f in folders if f["is_default"])
    custom_folders = [f for f in folders if not f["is_default"]]

    # Attempt to delete default folder: MUST FAIL (400)
    r_del_def = client.delete(f"/api/v1/favorites/folders/{def_folder['id']}", headers=headers)
    assert r_del_def.status_code == 400

    # Delete custom folder succeeds
    if custom_folders:
        target = custom_folders[0]
        r_del_custom = client.delete(f"/api/v1/favorites/folders/{target['id']}", headers=headers)
        assert r_del_custom.status_code == 200
        assert r_del_custom.json()["success"] is True
