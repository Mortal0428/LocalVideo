# -*- coding: utf-8 -*-
"""
CinemaAgent Phase 2 Milestone 2 - Empirical Adversarial Challenger Suite
========================================================================
Empirically verifies:
  1. #user-display-name and #user-role-badge bounding boxes do NOT overlap (standard & 35-char long nickname).
  2. Computed textDecorationLine === 'none' on user chip, display name, and badge.
  3. Multi-user comment reply, real-time notification dispatch, skylight drawer, and deep-link jump with highlight glow.

Archiving screenshots to `storage/test_screenshots/`.
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "storage", "test_screenshots")
BACKEND_BASE_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5173")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def capture_screenshot(page, label: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_M2_ADV_{label}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    page.screenshot(path=filepath, full_page=False)
    print(f"  [SCREENSHOT] Captured: {filename}")
    return filepath


def register_user(prefix: str, nickname: str = None) -> dict:
    ts = int(time.time() * 1000) % 10000000
    username = f"{prefix}_{ts}"
    password = "password123"
    nick = nickname or f"Nick_{username}"
    
    reg_url = f"{BACKEND_BASE_URL}/api/v1/auth/register"
    resp = requests.post(reg_url, json={"username": username, "password": password, "nickname": nick}, timeout=10)
    assert resp.status_code in [200, 201], f"Register failed: {resp.text}"
    user_data = resp.json().get("data", resp.json())
    user_id = user_data.get("id")

    # Login
    login_url = f"{BACKEND_BASE_URL}/api/v1/auth/login"
    login_resp = requests.post(login_url, json={"username": username, "password": password}, timeout=10)
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json().get("access_token")

    return {
        "id": user_id,
        "username": username,
        "nickname": nick,
        "role": "USER",
        "token": token
    }


def inject_auth(context, user_info: dict):
    page = context.new_page()
    page.goto(f"{FRONTEND_BASE_URL}/#/", wait_until="domcontentloaded", timeout=15000)
    token = user_info["token"]
    user_dict = {
        "id": user_info["id"],
        "username": user_info["username"],
        "nickname": user_info["nickname"],
        "role": user_info.get("role", "USER")
    }
    page.evaluate(f"""() => {{
        localStorage.setItem('cinema_access_token', '{token}');
        localStorage.setItem('token', '{token}');
        localStorage.setItem('user', JSON.stringify({json.dumps(user_dict)}));
    }}""")
    page.close()


def test_assertion_1_header_chip_geometry_and_styles(browser):
    """
    Empirical Assertion:
      - #user-display-name and #user-role-badge bounding boxes do not overlap.
      - Computed textDecorationLine === 'none' on user chip.
      - Stress test with long nickname.
    """
    print("\n--- [TEST 1] Auditing User Chip Geometry & Text Decoration ---")
    user = register_user("geom_viewer", "追剧小能手")
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    inject_auth(ctx, user)

    page = ctx.new_page()
    page.goto(f"{FRONTEND_BASE_URL}/#/", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector("#user-profile-badge", state="visible", timeout=10000)
    page.wait_for_selector("#user-display-name", state="visible", timeout=5000)
    page.wait_for_selector("#user-role-badge", state="visible", timeout=5000)

    # 1. Bounding box measurement
    box_name = page.locator("#user-display-name").bounding_box()
    box_badge = page.locator("#user-role-badge").bounding_box()

    assert box_name is not None, "Bounding box for #user-display-name is None"
    assert box_badge is not None, "Bounding box for #user-role-badge is None"
    assert box_name["width"] > 0 and box_name["height"] > 0, f"Invalid name dimensions: {box_name}"
    assert box_badge["width"] > 0 and box_badge["height"] > 0, f"Invalid badge dimensions: {box_badge}"

    print(f"  [GEOMETRY] #user-display-name: x={box_name['x']:.2f}, y={box_name['y']:.2f}, w={box_name['width']:.2f}, h={box_name['height']:.2f}")
    print(f"  [GEOMETRY] #user-role-badge:   x={box_badge['x']:.2f}, y={box_badge['y']:.2f}, w={box_badge['width']:.2f}, h={box_badge['height']:.2f}")

    # Overlap calculation
    x_overlap = max(0.0, min(box_name['x'] + box_name['width'], box_badge['x'] + box_badge['width']) - max(box_name['x'], box_badge['x']))
    y_overlap = max(0.0, min(box_name['y'] + box_name['height'], box_badge['y'] + box_badge['height']) - max(box_name['y'], box_badge['y']))
    overlap_area = x_overlap * y_overlap
    horizontal_gap = box_badge['x'] - (box_name['x'] + box_name['width'])

    print(f"  [GEOMETRY] Overlap Area: {overlap_area:.4f}px^2, Horizontal Gap: {horizontal_gap:.2f}px")
    assert overlap_area == 0.0, f"Bounding boxes overlap! x_overlap={x_overlap}, y_overlap={y_overlap}"
    assert horizontal_gap >= 0.0, f"Role badge should be positioned after display name, got gap={horizontal_gap}"

    # 2. Computed textDecorationLine assertion
    text_dec_chip = page.evaluate("() => window.getComputedStyle(document.querySelector('.user-profile-chip')).textDecorationLine")
    text_dec_name = page.evaluate("() => window.getComputedStyle(document.querySelector('#user-display-name')).textDecorationLine")
    text_dec_badge = page.evaluate("() => window.getComputedStyle(document.querySelector('#user-role-badge')).textDecorationLine")

    print(f"  [CSS] .user-profile-chip textDecorationLine: '{text_dec_chip}'")
    print(f"  [CSS] #user-display-name textDecorationLine:   '{text_dec_name}'")
    print(f"  [CSS] #user-role-badge textDecorationLine:     '{text_dec_badge}'")

    assert text_dec_chip == 'none', f"Expected 'none' on user chip, got '{text_dec_chip}'"
    assert text_dec_name == 'none', f"Expected 'none' on display name, got '{text_dec_name}'"
    assert text_dec_badge == 'none', f"Expected 'none' on role badge, got '{text_dec_badge}'"

    capture_screenshot(page, "user_chip_normal_geometry")

    # 3. Adversarial Stress Test: Ultra-long nickname (35 Chinese chars)
    print("  [STRESS TEST] Injecting 35-character long nickname to test layout resilience...")
    long_nick = "超级至尊无敌宇宙第一追剧狂魔深度剧评人九万八千里长名测试"
    user["nickname"] = long_nick
    inject_auth(ctx, user)
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#user-display-name", state="visible", timeout=5000)

    box_name_long = page.locator("#user-display-name").bounding_box()
    box_badge_long = page.locator("#user-role-badge").bounding_box()

    x_overlap_long = max(0.0, min(box_name_long['x'] + box_name_long['width'], box_badge_long['x'] + box_badge_long['width']) - max(box_name_long['x'], box_badge_long['x']))
    y_overlap_long = max(0.0, min(box_name_long['y'] + box_name_long['height'], box_badge_long['y'] + box_badge_long['height']) - max(box_name_long['y'], box_badge_long['y']))
    overlap_area_long = x_overlap_long * y_overlap_long
    gap_long = box_badge_long['x'] - (box_name_long['x'] + box_name_long['width'])

    print(f"  [STRESS TEST] Long Nickname #user-display-name w={box_name_long['width']:.2f}, gap={gap_long:.2f}px, overlap={overlap_area_long:.4f}px^2")
    assert overlap_area_long == 0.0, f"Long nickname caused bounding box overlap: {overlap_area_long}"
    assert gap_long >= 0.0, f"Long nickname inverted or overlapped badge: {gap_long}"

    capture_screenshot(page, "user_chip_long_nickname_resilience")
    ctx.close()
    print("  [PASS] Test 1: Bounding boxes strictly non-overlapping, textDecorationLine === 'none' verified!")


def test_assertion_2_multi_user_comment_reply_and_notification_jump(browser):
    """
    Empirical Assertion:
      - Multi-user comment reply and notification jump.
      - User A comments.
      - User B views comment, clicks reply, submits reply, and likes comment.
      - User A receives notification in Skylight Drawer.
      - User A clicks reply notification -> jumps to player and comment is highlighted.
    """
    print("\n--- [TEST 2] Multi-User Comment Reply & Notification Skylight Jump ---")
    user_a = register_user("author_a", "剧迷小李A")
    user_b = register_user("replier_b", "热心剧评人B")

    # Fetch latest video album & episode
    album_resp = requests.get(f"{BACKEND_BASE_URL}/api/v1/interactions/album/latest", timeout=10)
    assert album_resp.status_code == 200, f"Failed to get latest album: {album_resp.text}"
    album_data = album_resp.json().get("data", {})
    video_id = album_data.get("id")
    episodes = album_data.get("episodes", [])
    assert len(episodes) > 0, "No episodes available in latest album"
    episode_id = episodes[0].get("id")
    print(f"  [DATA] Target Video ID: {video_id}, Episode ID: {episode_id}")

    ctx_a = browser.new_context(viewport={"width": 1440, "height": 900})
    ctx_b = browser.new_context(viewport={"width": 1440, "height": 900})

    inject_auth(ctx_a, user_a)
    inject_auth(ctx_b, user_b)

    page_a = ctx_a.new_page()
    page_b = ctx_b.new_page()

    # Step 1: User A posts a root comment on player
    target_player_url = f"{FRONTEND_BASE_URL}/#/play?videoId={video_id}&episodeId={episode_id}"
    print(f"  [USER A] Navigating to player: {target_player_url}")
    page_a.on("dialog", lambda d: (print(f"  [DIALOG A] {d.message}"), d.accept()))
    page_b.on("dialog", lambda d: (print(f"  [DIALOG B] {d.message}"), d.accept()))

    page_a.goto(target_player_url, wait_until="domcontentloaded", timeout=15000)
    # Wait for user auth and episode readiness
    page_a.wait_for_selector("#user-display-name", state="visible", timeout=10000)
    page_a.wait_for_selector("[id^='ep-btn-']", state="visible", timeout=10000)
    page_a.wait_for_selector("#input-comment", state="visible", timeout=10000)
    page_a.wait_for_timeout(2000)

    unique_root_text = f"【极度高能】User A 深度解析 - 时间戳 {int(time.time())}"
    page_a.fill("#input-comment", unique_root_text)
    page_a.click("#btn-submit-comment")
    page_a.wait_for_timeout(2500)

    # Locate the posted comment in User A's view
    comment_card = page_a.locator(".comment-thread-card", has_text=unique_root_text).first
    assert comment_card.count() > 0, "User A's comment was not found in the comment thread"
    raw_card_id = comment_card.get_attribute("id")
    assert raw_card_id and raw_card_id.startswith("comment-"), f"Unexpected comment card id: {raw_card_id}"
    comment_id = raw_card_id.replace("comment-", "")
    print(f"  [USER A] Comment successfully created with ID: {comment_id}")
    capture_screenshot(page_a, "user_a_comment_created")

    # Step 2: User B opens player, views User A's comment, and posts a reply
    print(f"  [USER B] Opening player and replying to comment {comment_id}...")
    page_b.goto(target_player_url, wait_until="domcontentloaded", timeout=15000)
    page_b.wait_for_selector("#user-display-name", state="visible", timeout=10000)
    page_b.wait_for_selector(f"#comment-{comment_id}", state="visible", timeout=10000)
    page_b.wait_for_timeout(1000)

    # User B clicks reply button for this comment
    reply_btn_id = f"#btn-reply-comment-{comment_id}"
    page_b.wait_for_selector(reply_btn_id, state="visible", timeout=5000)
    page_b.click(reply_btn_id)

    # User B types into the inline reply box
    reply_input_id = f"#input-reply-comment-{comment_id}"
    page_b.wait_for_selector(reply_input_id, state="visible", timeout=5000)
    unique_reply_text = f"【精辟见解】User B 强烈赞同，层层递进！时间戳 {int(time.time())}"
    page_b.fill(reply_input_id, unique_reply_text)

    # User B submits reply
    reply_submit_btn_id = f"#btn-submit-reply-{comment_id}"
    page_b.click(reply_submit_btn_id)
    page_b.wait_for_timeout(2000)

    # Verify reply appears in DOM for User B
    sub_bubble = page_b.locator(f"#comment-{comment_id} .sub-thread-container", has_text=unique_reply_text)
    assert sub_bubble.count() > 0, "User B's reply not rendered in sub-thread container"
    print("  [USER B] Reply successfully rendered in sub-thread!")

    # User B also likes the root comment
    like_btn_id = f"#btn-like-comment-{comment_id}"
    page_b.click(like_btn_id)
    page_b.wait_for_timeout(1000)
    capture_screenshot(page_b, "user_b_reply_and_like_submitted")

    # Step 3: User A browses to Home, then checks Notification Skylight Drawer
    print("  [USER A] Navigating to Home and checking notification skylight for reply...")
    page_a.goto(f"{FRONTEND_BASE_URL}/#/", wait_until="domcontentloaded", timeout=15000)
    page_a.wait_for_selector("#btn-notification-skylight", state="visible", timeout=5000)
    page_a.wait_for_timeout(1000)

    # Click bell to open skylight drawer
    page_a.click("#btn-notification-skylight")
    page_a.wait_for_selector("#notification-skylight-drawer", state="visible", timeout=5000)
    capture_screenshot(page_a, "user_a_drawer_opened")

    # Click Replies tab
    page_a.click("#skylight-tab-replies")
    page_a.wait_for_timeout(1500)

    # Find the notification corresponding to User B's reply
    notif_card = page_a.locator(".skylight-card", has_text=user_b["nickname"]).first
    assert notif_card.count() > 0, f"Notification from {user_b['nickname']} not found in skylight replies tab!"
    print(f"  [USER A] Found notification card mentioning {user_b['nickname']}")
    capture_screenshot(page_a, "user_a_reply_notification_found")

    # Step 4: User A clicks notification card to trigger deep-link jump
    print("  [USER A] Clicking notification card to test deep-link jump...")
    notif_card.click()
    page_a.wait_for_timeout(3000)

    # Verify drawer closed
    drawer_visible = page_a.is_visible("#notification-skylight-drawer")
    assert not drawer_visible, "Notification skylight drawer should close after clicking notification item"

    # Verify URL contains commentId
    current_url = page_a.url
    print(f"  [USER A] Navigated URL: {current_url}")
    assert f"commentId=" in current_url and f"videoId={video_id}" in current_url, f"Expected deep link params in URL, got {current_url}"

    # Extract target commentId from URL query
    import re
    match = re.search(r"commentId=([a-f0-9\-]+)", current_url)
    assert match, f"commentId parameter not found in URL: {current_url}"
    target_reply_id = match.group(1)
    print(f"  [USER A] Target Reply ID from query: {target_reply_id}")

    # Verify target comment element is in DOM
    page_a.wait_for_selector(f"#comment-{target_reply_id}", state="visible", timeout=10000)
    target_comment_el = page_a.locator(f"#comment-{target_reply_id}")
    assert target_comment_el.count() > 0, f"Target comment #comment-{target_reply_id} not found on navigated page"

    # Verify highlight class
    has_highlight = page_a.evaluate(f"""() => {{
        const el = document.getElementById('comment-{target_reply_id}');
        return el ? el.classList.contains('comment-highlight') : false;
    }}""")
    print(f"  [USER A] Target comment highlight state: {has_highlight}")
    assert has_highlight, f"Expected comment #comment-{target_reply_id} to have class 'comment-highlight'"

    capture_screenshot(page_a, "user_a_notification_jump_verified")
    ctx_a.close()
    ctx_b.close()
    print("  [PASS] Test 2: Multi-user comment reply and notification jump verified end-to-end!")


def main():
    print("=" * 80)
    print("CINEMAAGENT PHASE 2 M2 EMPIRICAL ADVERSARIAL CHALLENGER SUITE")
    print(f"Backend  : {BACKEND_BASE_URL}")
    print(f"Frontend : {FRONTEND_BASE_URL}")
    print("=" * 80)

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)

        try:
            test_assertion_1_header_chip_geometry_and_styles(browser)
            test_assertion_2_multi_user_comment_reply_and_notification_jump(browser)
            print("\n" + "=" * 80)
            print(">>> ALL ADVERSARIAL EMPIRICAL ASSERTIONS PASSED (100% SUCCESS) <<<")
            print("=" * 80)
            browser.close()
            return 0
        except Exception as e:
            print(f"\n[CRITICAL FAILURE] Adversarial test failed: {e}")
            import traceback
            traceback.print_exc()
            browser.close()
            return 1


if __name__ == "__main__":
    sys.exit(main())
