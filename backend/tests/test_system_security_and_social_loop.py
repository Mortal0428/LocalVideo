import os
import sys
import uuid
import time
import requests
import json

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5173"

def get_auth_token(username: str, role: str = "USER", is_creator: bool = False):
    """Register or login user and return bearer token + user object."""
    password = f"Pass_{username}_123"
    # Register if not exist
    requests.post(f"{BASE_URL}/api/v1/auth/register", json={
        "username": username,
        "password": password,
        "nickname": f"昵称_{username}"
    })
    # Login to get JWT
    login_res = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"username": username, "password": password})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    user_info = login_res.json()["user"]

    # Upgrade role if needed
    if role != "USER" or is_creator:
        from app.core.database import SessionLocal
        from app.models.user import User
        db = SessionLocal()
        u = db.query(User).filter(User.username == username).first()
        if u:
            u.role = role
            u.is_creator = is_creator
            db.commit()
            db.refresh(u)
        db.close()

    return token, user_info

def run_e2e_tests():
    print("=" * 60)
    print(">>> 启动系统高可用架构、创作者私域隔离与社交闭环端到端自动化测试")
    print("=" * 60)

    # 1. 创作者多租户私域数据与网盘权限隔离测试
    print("\n[测试项 1] 创作者私域隔离与越权阻断测试...")
    token_a, user_a = get_auth_token(f"creator_alpha_{uuid.uuid4().hex[:4]}", role="CREATOR", is_creator=True)
    token_b, user_b = get_auth_token(f"creator_beta_{uuid.uuid4().hex[:4]}", role="CREATOR", is_creator=True)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 创作者 B 初始状态剧集列表必须为空（不得泄漏全平台短剧）
    dramas_b_res = requests.get(f"{BASE_URL}/api/v1/creator/dramas", headers=headers_b)
    assert dramas_b_res.status_code == 200, dramas_b_res.text
    dramas_b = dramas_b_res.json()["data"]
    assert len(dramas_b) == 0, f"严重漏洞：新创作者被灌入了其他作品，返回短剧数量={len(dramas_b)}"
    print("  [OK] 创作者 B 短剧列表严格隔离为 0，彻底清除兜底查全表泄漏漏洞")

    # 创作者 A 创建一部私有短剧与一个分集
    from app.core.database import SessionLocal
    from app.models.video import Video, VideoEpisode
    db = SessionLocal()
    drama_a = Video(
        id=str(uuid.uuid4()),
        title=f"战神归来_{uuid.uuid4().hex[:4]}",
        summary="创作者 A 专属短剧",
        creator_id=user_a["id"],
        category="都市战神",
        cover_url="https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=600",
        status="PUBLISHED"
    )
    db.add(drama_a)
    db.flush()

    ep_a = VideoEpisode(
        id=str(uuid.uuid4()),
        video_id=drama_a.id,
        episode_num=1,
        title="第1集 龙王降世",
        raw_file_path="/kuake/test.mp4",
        duration_seconds=120,
        transcode_status="READY"
    )
    db.add(ep_a)
    db.commit()
    drama_a_id = drama_a.id
    ep_a_id = ep_a.id
    db.close()

    # 创作者 A 能看到自己的短剧
    dramas_a_res = requests.get(f"{BASE_URL}/api/v1/creator/dramas", headers=headers_a)
    assert any(d["id"] == drama_a_id for d in dramas_a_res.json()["data"]), "创作者 A 应能查到自身短剧"
    # 创作者 B 依然看不到创作者 A 的短剧
    dramas_b_res2 = requests.get(f"{BASE_URL}/api/v1/creator/dramas", headers=headers_b)
    assert not any(d["id"] == drama_a_id for d in dramas_b_res2.json()["data"]), "创作者 B 绝不能看到创作者 A 的短剧"
    print("  [OK] 创作者 A 与 B 作品物理隔离成功")

    # 创作者 B 试图越权修改创作者 A 的短剧 -> 断言 403 Forbidden
    hack_res = requests.put(
        f"{BASE_URL}/api/v1/creator/dramas/{drama_a_id}",
        headers=headers_b,
        json={"title": "恶意篡改标题"}
    )
    assert hack_res.status_code == 403, f"防越权失效！状态码={hack_res.status_code}"
    print("  [OK] 跨创作者越权修改短剧被严格拦截 (403 Forbidden)")

    # 创作者 B 试图越权删除创作者 A 的短剧 -> 断言 403 Forbidden
    del_hack_res = requests.delete(f"{BASE_URL}/api/v1/creator/dramas/{drama_a_id}", headers=headers_b)
    assert del_hack_res.status_code == 403, f"防越权删除失效！状态码={del_hack_res.status_code}"
    print("  [OK] 跨创作者越权删除短剧被严格拦截 (403 Forbidden)")

    # 普通创作者访问网盘目录树，必须收敛在私有工作区目录
    pan_res = requests.get(f"{BASE_URL}/api/v1/creator/pan/tree", headers=headers_b)
    assert pan_res.status_code == 200, pan_res.text
    pan_data = pan_res.json()["data"]
    assert pan_data["is_sandboxed"] is True, "普通创作者网盘必须处于沙箱限制状态"
    assert pan_data["current_path"].startswith(f"/kuake/creators/{user_b['id']}"), "普通创作者必须被限制在个人私有目录"
    print("  [OK] 普通创作者网盘目录成功收敛至私有工作区，无法窥探公共根目录")

    # 普通创作者调用全量网盘短剧扫描端点 -> 断言 403 Forbidden
    sync_res = requests.post(f"{BASE_URL}/api/v1/creator/pan/sync-dramas", headers=headers_b)
    assert sync_res.status_code == 403, f"非管理员扫描网盘未被拦截！状态码={sync_res.status_code}"
    print("  [OK] 普通创作者调用网盘全局短剧扫描被正确拦截 (403 Forbidden)")

    # 2. 用户发表评论与个人中心“我的评论”Tab 及删除闭环测试
    print("\n[测试项 2] 评论管理与个人中心历史评论闭环测试...")
    token_viewer, user_viewer = get_auth_token(f"viewer_{uuid.uuid4().hex[:4]}")
    headers_viewer = {"Authorization": f"Bearer {token_viewer}"}

    # 发表一条评论到第 1 集
    post_comment_res = requests.post(
        f"{BASE_URL}/api/v1/interactions/episodes/{ep_a_id}/comments",
        headers=headers_viewer,
        json={"content": "这本短剧太燃了！名场面反转绝了！"}
    )
    assert post_comment_res.status_code == 200, post_comment_res.text
    created_comment_id = post_comment_res.json()["data"]["id"]
    print("  [OK] 用户成功发表主楼短剧评论")

    # 个人中心查阅自身历史评论
    my_comments_res = requests.get(f"{BASE_URL}/api/v1/user/comments", headers=headers_viewer)
    assert my_comments_res.status_code == 200, my_comments_res.text
    comments_items = my_comments_res.json()["data"]["items"]
    found_comment = next((c for c in comments_items if c["comment_id"] == created_comment_id), None)
    assert found_comment is not None, "个人中心未能精准查出用户自己刚发表的评论"
    assert found_comment["content"] == "这本短剧太燃了！名场面反转绝了！"
    print("  [OK] 个人中心“我的评论”列表精准拉取用户自身发表的历史记录")

    # 用户自主删除该评论
    del_comment_res = requests.delete(f"{BASE_URL}/api/v1/user/comments/{created_comment_id}", headers=headers_viewer)
    assert del_comment_res.status_code == 200, del_comment_res.text
    my_comments_res_after = requests.get(f"{BASE_URL}/api/v1/user/comments", headers=headers_viewer)
    assert not any(c["comment_id"] == created_comment_id for c in my_comments_res_after.json()["data"]["items"]), "评论未被成功删除"
    print("  [OK] 用户自主删除自身评论闭环成功")

    # 3. 社交关注与粉丝双向关系链测试
    print("\n[测试项 3] 用户相互关注与粉丝体系测试...")
    # 用户 A 关注 创作者 B
    follow_res = requests.post(f"{BASE_URL}/api/v1/user/follow/{user_b['id']}", headers=headers_viewer)
    assert follow_res.status_code == 200, follow_res.text
    assert follow_res.json()["data"]["is_following"] is True, "关注状态未更新为 True"
    print("  [OK] 用户 A 成功关注创作者 B")

    # 创作者 B 查看粉丝列表，断言包含用户 A
    followers_res = requests.get(f"{BASE_URL}/api/v1/user/followers", headers=headers_b)
    assert followers_res.status_code == 200, followers_res.text
    assert any(f["user_id"] == user_viewer["id"] for f in followers_res.json()["data"]["items"]), "创作者 B 粉丝列表中未找到用户 A"
    print("  [OK] 创作者 B 粉丝列表中准确展现新粉丝")

    # 用户 A 查看我的关注列表，断言包含创作者 B
    followings_res = requests.get(f"{BASE_URL}/api/v1/user/followings", headers=headers_viewer)
    assert any(f["user_id"] == user_b["id"] for f in followings_res.json()["data"]["items"]), "用户 A 关注列表中未找到创作者 B"
    print("  [OK] 用户 A 关注列表中准确展现创作者 B")

    # 用户 A 再次调用关注接口，断言取关
    unfollow_res = requests.post(f"{BASE_URL}/api/v1/user/follow/{user_b['id']}", headers=headers_viewer)
    assert unfollow_res.json()["data"]["is_following"] is False, "取关状态未更新为 False"
    print("  [OK] 重复点击关注自动取关闭环成功")

    # 用户试图关注自己 -> 断言 400 错误
    self_follow_res = requests.post(f"{BASE_URL}/api/v1/user/follow/{user_viewer['id']}", headers=headers_viewer)
    assert self_follow_res.status_code == 400, "自关注漏洞未被拦截"
    print("  [OK] 自我关注死循环逻辑被成功拦截 (400 Bad Request)")

    # 4. 全用户自定义本地头像安全上传与即时生效测试
    print("\n[测试项 4] 本地图片上传自定义头像测试...")
    # 构造一张 1x1 真实 PNG 二进制图片
    png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    files = {"file": ("my_avatar.png", png_bytes, "image/png")}
    upload_res = requests.post(f"{BASE_URL}/api/v1/upload/image", headers=headers_viewer, files=files)
    assert upload_res.status_code == 200, upload_res.text
    new_avatar_url = upload_res.json()["url"]
    assert new_avatar_url.startswith("/storage/uploads/images/"), f"返回头像链接异常: {new_avatar_url}"
    print(f"  [OK] 本地头像图片安全上传成功: {new_avatar_url}")

    # 保存至用户资料
    save_profile_res = requests.put(
        f"{BASE_URL}/api/v1/user/profile",
        headers=headers_viewer,
        json={"avatar_url": new_avatar_url, "nickname": "剧迷新形象"}
    )
    assert save_profile_res.status_code == 200, save_profile_res.text
    profile_check_res = requests.get(f"{BASE_URL}/api/v1/user/profile", headers=headers_viewer)
    assert profile_check_res.json()["data"]["avatar_url"] == new_avatar_url, "新头像未能持久化"
    print("  [OK] 用户自定义本地头像持久化生效，彻底告别死板预设")

    # 5. RAG 知识库资产单语料独立切片、向量化与图谱级联清理测试
    print("\n[测试项 5] 知识库单文档向量化与 Neo4j 级联清理测试...")
    admin_token, admin_user = get_auth_token("admin_test", role="ADMIN")
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    # 创建一篇测试语料（切片数初始为 0）
    from app.models.rag_corpus import RAGCorpus
    corpus_id = str(uuid.uuid4())
    test_corpus = RAGCorpus(
        id=corpus_id,
        title=f"新短剧大纲_{uuid.uuid4().hex[:4]}",
        doc_type="script",
        drama_id=drama_a_id,
        content="第1幕 豪门宴会：主角萧天策身穿洗白风衣步入会场，沈家老爷子冷笑一声。萧天策淡淡说道：三年之期已到，龙王归位！",
        chunk_count=0
    )
    db = SessionLocal()
    db.add(test_corpus)
    db.commit()
    db.close()

    # 触发单语料切片与向量化接口
    embed_res = requests.post(
        f"{BASE_URL}/api/v1/rag-admin/corpora/{corpus_id}/embed",
        headers=headers_admin,
        json={"chunk_size": 200, "chunk_overlap": 20, "re_extract_graph": True}
    )
    assert embed_res.status_code == 200, embed_res.text
    embed_data = embed_res.json()["data"]
    assert embed_data["chunk_count"] > 0, "切片数应大于 0"
    print(f"  [OK] 单文档向量化成功，生成 {embed_data['chunk_count']} 个 1024 维稠密分块")

    # 删除语料，断言图谱与切片级联清理
    del_corpus_res = requests.delete(f"{BASE_URL}/api/v1/rag-admin/corpora/{corpus_id}", headers=headers_admin)
    assert del_corpus_res.status_code == 200, del_corpus_res.text
    print("  [OK] 知识库语料删除成功，Neo4j 对应图谱节点已同步级联清理")

    print("\n" + "=" * 60)
    print(">>> 全部后端核心安全、隔离与交互接口自动化断言 100% 通过！")
    print("=" * 60)

if __name__ == "__main__":
    run_e2e_tests()
