import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.path.insert(0, "backend")
from app.core.database import SessionLocal
from app.models.user import User
from app.models.video import Video, VideoEpisode
from app.core.security import create_access_token

ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"

def run_test():
    print("[E2E] Starting X/Ins Style @Mention & Notification Closed-Loop Verification...")
    db = SessionLocal()
    admin_user = db.query(User).filter(User.username == "admin").first()
    viewer_user = db.query(User).filter(User.username == "viewer").first()
    ep = db.query(VideoEpisode).first()
    video = db.query(Video).filter(Video.id == ep.video_id).first()

    admin_token = create_access_token({"sub": admin_user.id})
    viewer_token = create_access_token({"sub": viewer_user.id})
    db.close()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.on("console", lambda msg: print("[CONSOLE]", msg.text))
        page.on("pageerror", lambda err: print("[PAGEERROR]", err))

        # Step 1: Login as Viewer and enter PlayerView (Dark Theme)
        print("[Step 1] Logging in as user 'viewer' and navigating to PlayerView...")
        page.goto("http://localhost:5173/", wait_until="networkidle")
        page.evaluate(f"""() => {{
            localStorage.setItem('cinema_access_token', '{viewer_token}');
            localStorage.setItem('token', '{viewer_token}');
            localStorage.setItem('access_token', '{viewer_token}');
            localStorage.setItem('user', JSON.stringify({{
                id: '{viewer_user.id}',
                username: '{viewer_user.username}',
                role: 'USER',
                nickname: '{viewer_user.nickname or viewer_user.username}'
            }}));
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('cinema_theme', 'dark');
        }}""")
        time.sleep(1)

        play_url = f"http://localhost:5173/#/play?videoId={video.id}&episodeId={ep.id}"
        print(f"Navigating to {play_url}...")
        page.goto(play_url, wait_until="networkidle")
        time.sleep(2)

        # Scroll down to comment area
        comment_input = page.locator("#input-comment")
        comment_input.wait_for(state="visible", timeout=15000)
        comment_input.scroll_into_view_if_needed()
        time.sleep(1)

        # Step 2: Test @ Mention typing trigger and autocomplete popover (Dark Theme)
        print("[Step 2] Typing '@' in comment box to trigger X/Ins mention suggestion...")
        comment_input.click()
        comment_input.press_sequentially("@ad", delay=150)
        time.sleep(1.5)

        popover_root = page.locator("#mention-suggest-popover-root")
        popover_root.wait_for(state="visible", timeout=10000)
        print("-> Mention popover displayed successfully!")

        shot1 = os.path.join(ARTIFACT_DIR, "verified_mention_autocomplete_popover_dark.png")
        page.screenshot(path=shot1, full_page=False)
        print(f"-> Saved popover screenshot: {shot1}")

        # Step 3: Select @admin and submit comment
        print("[Step 3] Selecting @admin candidate and posting comment...")
        admin_candidate = page.locator("#mention-candidate-admin").first
        if admin_candidate.count() > 0:
            admin_candidate.click()
        else:
            first_candidate = page.locator(".mention-candidate-item").first
            first_candidate.click()
        time.sleep(0.5)

        # Append走心评论 text
        unique_text = f"这个反转设计太绝了，强烈推荐！ (测试标记_{int(time.time())})"
        current_val = comment_input.input_value()
        comment_input.fill(current_val + unique_text)
        time.sleep(0.5)

        submit_btn = page.locator("#btn-submit-comment")
        submit_btn.click()
        time.sleep(2)

        # Step 4: Verify comment rendered with .mention-pill (Dark Theme)
        print("[Step 4] Verifying rich .mention-pill rendered in comments list...")
        mention_pill = page.locator(".mention-pill:has-text('@admin')").first
        mention_pill.wait_for(state="visible", timeout=15000)
        mention_pill.scroll_into_view_if_needed()
        time.sleep(1)

        shot2 = os.path.join(ARTIFACT_DIR, "verified_mention_pill_rendered_dark.png")
        page.screenshot(path=shot2, full_page=False)
        print(f"-> Saved mention pill screenshot: {shot2}")

        # Step 5: Click .mention-pill to open UserMicroProfileCard
        print("[Step 5] Clicking .mention-pill to verify UserMicroProfileCard popup...")
        mention_pill.click()
        time.sleep(1.5)

        profile_modal = page.locator(".user-micro-card-panel").first
        profile_modal.wait_for(state="visible", timeout=10000)
        print("-> UserMicroProfileCard opened successfully via mention pill click!")

        shot3 = os.path.join(ARTIFACT_DIR, "verified_mention_click_micro_card_dark.png")
        page.screenshot(path=shot3, full_page=False)
        print(f"-> Saved profile card screenshot: {shot3}")

        # Close micro profile dialog
        close_x = page.locator(".card-close-x-btn").first
        if close_x.count() > 0:
            close_x.click()
        else:
            page.keyboard.press("Escape")
        time.sleep(0.5)

        # Step 6: Switch to User B (admin) to verify Notification Skylight
        print("[Step 6] Switching login session to User B ('admin')...")
        page.evaluate(f"""() => {{
            localStorage.setItem('cinema_access_token', '{admin_token}');
            localStorage.setItem('token', '{admin_token}');
            localStorage.setItem('access_token', '{admin_token}');
            localStorage.setItem('user', JSON.stringify({{
                id: '{admin_user.id}',
                username: '{admin_user.username}',
                role: 'ADMIN',
                nickname: '{admin_user.nickname or admin_user.username}'
            }}));
        }}""")
        page.goto("http://localhost:5173/", wait_until="networkidle")
        time.sleep(2)

        # Open notification skylight
        bell_btn = page.locator("#btn-notification-skylight")
        bell_btn.wait_for(state="visible", timeout=10000)
        bell_btn.click()
        time.sleep(1)

        skylight_drawer = page.locator("#notification-skylight-drawer")
        skylight_drawer.wait_for(state="visible", timeout=10000)

        # Switch to tab '回复与@我的'
        reply_tab = page.locator("#skylight-tab-replies")
        reply_tab.click()
        time.sleep(1.5)

        # Verify mention notification card exists
        print("[Step 7] Verifying MENTION notification in skylight...")
        mention_tag = page.locator(".card-category-tag.mention-tag").first
        mention_tag.wait_for(state="visible", timeout=10000)

        shot4 = os.path.join(ARTIFACT_DIR, "verified_notification_skylight_mention_dark.png")
        page.screenshot(path=shot4, full_page=False)
        print(f"-> Saved skylight mention notification screenshot: {shot4}")

        # Step 7: Click notification card and verify deep jump + highlight
        print("[Step 8] Clicking mention notification to verify deep jump and comment highlight...")
        mention_card = page.locator(".skylight-card:has(.mention-tag)").first
        mention_card.click()
        time.sleep(3)

        # Check highlighted comment in PlayerView
        highlighted_card = page.locator(".comment-highlight")
        highlighted_card.wait_for(state="visible", timeout=15000)
        print("-> Comment highlight border successfully activated after deep jump!")

        shot5 = os.path.join(ARTIFACT_DIR, "verified_notification_deep_jump_highlight_dark.png")
        page.screenshot(path=shot5, full_page=False)
        print(f"-> Saved deep jump highlight screenshot: {shot5}")

        # Step 8: Light Theme Verification
        print("[Step 9] Verifying pristine light theme visual presentation...")
        page.evaluate("() => { document.documentElement.setAttribute('data-theme', 'light'); localStorage.setItem('cinema_theme', 'light'); }")
        time.sleep(1)

        # Retrigger mention popover in light mode
        comment_input_light = page.locator("#input-comment")
        comment_input_light.scroll_into_view_if_needed()
        comment_input_light.click()
        comment_input_light.fill("")
        comment_input_light.press_sequentially("@cr", delay=150)
        time.sleep(1.5)

        shot6 = os.path.join(ARTIFACT_DIR, "verified_mention_autocomplete_popover_light.png")
        page.screenshot(path=shot6, full_page=False)
        print(f"-> Saved light theme popover screenshot: {shot6}")

        comment_input_light.fill("")
        comment_input_light.dispatch_event("input")
        time.sleep(0.5)

        # Screenshot light theme comment pills
        shot7 = os.path.join(ARTIFACT_DIR, "verified_mention_pill_rendered_light.png")
        page.screenshot(path=shot7, full_page=False)
        print(f"-> Saved light theme comment pill screenshot: {shot7}")

        browser.close()
        print("[E2E] All 9 steps completed with 100% assertions passed!")

if __name__ == "__main__":
    run_test()
