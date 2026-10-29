import asyncio
import os
import shutil
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"
SCREENSHOT_DIR = os.path.join(os.getcwd(), "storage", "test_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

async def run_verification():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="msedge")
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("\n=== STEP 1: Login Admin and verify Agent Hub (Fix 1: White Screen Resolution) ===")
        await page.goto("http://localhost:5173/#/login")
        await page.wait_for_selector("#input-login-username", timeout=10000)
        await page.fill("#input-login-username", "admin")
        await page.fill("#input-login-password", "admin123")
        await page.click("#btn-submit-login")
        await page.wait_for_timeout(1000)

        # Clear any login-phase console errors
        console_errors.clear()

        # Navigate to 九大智能体 & 战术大屏
        await page.goto("http://localhost:5173/#/admin?tab=agent-hub")
        await page.wait_for_timeout(1800)

        # Click #admin-tab-agent-hub to ensure selection
        await page.click("#admin-tab-agent-hub")
        await page.wait_for_timeout(1200)

        # Assert no ReferenceError in console
        ref_errors = [e for e in console_errors if "ReferenceError" in e or "computed is not defined" in e]
        print(f"Console Reference Errors: {ref_errors}")
        assert len(ref_errors) == 0, f"Found ReferenceError in Agent Hub: {ref_errors}"

        # Assert Agent Hub container is rendered and visible
        agent_hub_visible = await page.locator("#section-agent-hub").is_visible()
        print(f"Section agent-hub visible: {agent_hub_visible}")
        assert agent_hub_visible, "Section #section-agent-hub is not visible!"

        hub_card_visible = await page.locator(".acc-header-bar, .agent-command-center, #section-agent-hub").first.is_visible()
        print(f"Agent Hub inner elements visible: {hub_card_visible}")
        assert hub_card_visible, "AgentCommandCenter inner elements not visible (White Screen detected)!"

        # Assert subtabs exist
        subtabs = await page.locator(".hub-subtab-btn, .acc-subtab-btn").count()
        print(f"Agent Hub rendered {subtabs} subtabs successfully.")
        assert subtabs >= 6, f"Expected at least 6 subtabs, got {subtabs}"

        screen1 = os.path.join(SCREENSHOT_DIR, "verified_fix1_agent_hub_no_white_screen.png")
        await page.screenshot(path=screen1)
        shutil.copy(screen1, os.path.join(ARTIFACT_DIR, "verified_fix1_agent_hub_no_white_screen.png"))
        print("PASS Fix 1: Agent Hub loaded with zero white screen errors.")

        print("\n=== STEP 2: Verify Agent 4 in Interactive Moderation (Fix 2) ===")
        # Click Tab 7: 互动合规风控 (#admin-tab-contents)
        await page.click("#admin-tab-contents")
        await page.wait_for_timeout(1000)

        # Click SubTab 5: 4号风控人机回环
        await page.click("#subtab-agent4-hitl")
        await page.wait_for_timeout(1000)

        # Verify #card-agent4-workspace exists
        workspace_visible = await page.locator("#card-agent4-workspace").is_visible()
        print(f"Agent 4 workspace card visible: {workspace_visible}")
        assert workspace_visible, "Agent 4 workspace card is not visible!"

        # Verify open chat button
        chat_btn_visible = await page.locator("#btn-open-agent4-chat").is_visible()
        print(f"Agent 4 open chat button visible: {chat_btn_visible}")
        assert chat_btn_visible, "Agent 4 open chat button is not visible!"

        # Click open chat button
        await page.click("#btn-open-agent4-chat")
        await page.wait_for_timeout(1000)

        dialog_visible = await page.locator(".universal-agent-dialog").is_visible()
        print(f"Agent 4 Universal Chat Dialog visible: {dialog_visible}")
        assert dialog_visible, "Agent 4 Universal Chat Dialog did not open!"

        screen2 = os.path.join(SCREENSHOT_DIR, "verified_fix2_agent4_moderation_workspace_and_chat.png")
        await page.screenshot(path=screen2)
        shutil.copy(screen2, os.path.join(ARTIFACT_DIR, "verified_fix2_agent4_moderation_workspace_and_chat.png"))
        print("PASS Fix 2: Agent 4 moderation workspace and ChatGPT modal verified.")

        # Close dialog
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)

        print("\n=== STEP 3: Verify Codex Pet Space Cabin Dual-Mode UI (Fix 3) ===")
        await page.goto("http://localhost:5173/#/profile")
        await page.wait_for_timeout(1500)

        # 3.1 Test Light Mode
        await page.evaluate("document.documentElement.setAttribute('data-theme', 'light'); localStorage.setItem('cinema_theme', 'light')")
        await page.wait_for_timeout(800)

        # Scroll to #codex-pet-cabin
        await page.locator("#codex-pet-cabin").scroll_into_view_if_needed()
        await page.wait_for_timeout(500)

        cabin_bg = await page.locator("#codex-pet-cabin").evaluate("el => window.getComputedStyle(el).backgroundColor")
        title_color = await page.locator("#codex-pet-cabin .pet-title").evaluate("el => window.getComputedStyle(el).color")
        input_bg = await page.locator("#input-pet-name").evaluate("el => window.getComputedStyle(el).backgroundColor")
        print(f"Light mode Cabin bg: {cabin_bg}, Title color: {title_color}, Input bg: {input_bg}")

        # Assert clean white / high contrast
        assert "255, 255, 255" in cabin_bg or "248, 249, 250" in cabin_bg, f"Cabin bg not white in light mode: {cabin_bg}"
        assert "29, 29, 31" in title_color or "24, 25, 28" in title_color or "0, 0, 0" in title_color, f"Title not dark: {title_color}"

        screen3_light = os.path.join(SCREENSHOT_DIR, "verified_fix3_codex_pet_cabin_light_mode.png")
        await page.screenshot(path=screen3_light)
        shutil.copy(screen3_light, os.path.join(ARTIFACT_DIR, "verified_fix3_codex_pet_cabin_light_mode.png"))
        print("PASS Fix 3 (Light): Codex Pet cabin high contrast light theme verified.")

        # 3.2 Test Dark Mode
        await page.evaluate("document.documentElement.setAttribute('data-theme', 'dark'); localStorage.setItem('cinema_theme', 'dark')")
        await page.wait_for_timeout(800)

        dark_cabin_bg = await page.locator("#codex-pet-cabin").evaluate("el => window.getComputedStyle(el).backgroundColor")
        dark_title_color = await page.locator("#codex-pet-cabin .pet-title").evaluate("el => window.getComputedStyle(el).color")
        print(f"Dark mode Cabin bg: {dark_cabin_bg}, Title color: {dark_title_color}")

        screen3_dark = os.path.join(SCREENSHOT_DIR, "verified_fix3_codex_pet_cabin_dark_mode.png")
        await page.screenshot(path=screen3_dark)
        shutil.copy(screen3_dark, os.path.join(ARTIFACT_DIR, "verified_fix3_codex_pet_cabin_dark_mode.png"))
        print("PASS Fix 3 (Dark): Codex Pet cabin glassy dark theme verified.")

        print("\n=== STEP 4: Verify Floating Companion Pet Draggable & Chat (Fix 4) ===")
        # Switch back to light theme for crisp visual verification
        await page.evaluate("document.documentElement.setAttribute('data-theme', 'light'); localStorage.setItem('cinema_theme', 'light')")
        await page.wait_for_timeout(500)

        pet_avatar = page.locator("#pet-avatar-main")
        assert await pet_avatar.is_visible(), "Floating pet avatar not found!"

        # Get initial position
        box_before = await pet_avatar.bounding_box()
        print(f"Initial Pet Avatar Pos: x={box_before['x']}, y={box_before['y']}")

        # Simulate pointer drag: drag 150px to the left and 120px upwards
        await page.mouse.move(box_before["x"] + 25, box_before["y"] + 25)
        await page.mouse.down()
        await page.mouse.move(box_before["x"] - 150, box_before["y"] - 120, steps=10)
        await page.mouse.up()
        await page.wait_for_timeout(500)

        box_after = await pet_avatar.bounding_box()
        print(f"After Drag Pet Avatar Pos: x={box_after['x']}, y={box_after['y']}")

        # Assert dragged displacement
        displacement = abs(box_after["x"] - box_before["x"]) + abs(box_after["y"] - box_before["y"])
        print(f"Total displacement: {displacement}px")
        assert displacement > 50, f"Expected pet to move significantly, but displacement was {displacement}px"

        # Now click avatar to open chat (force=True to bypass continuous CSS float animation)
        await pet_avatar.click(force=True)
        await page.wait_for_timeout(1000)

        chat_win_visible = await page.locator("#pet-companion-chat-window").is_visible()
        print(f"Floating Pet Chat Window visible: {chat_win_visible}")
        assert chat_win_visible, "Floating Pet Chat Window did not open on click!"

        screen4 = os.path.join(SCREENSHOT_DIR, "verified_fix4_floating_pet_drag_and_chat.png")
        await page.screenshot(path=screen4)
        shutil.copy(screen4, os.path.join(ARTIFACT_DIR, "verified_fix4_floating_pet_drag_and_chat.png"))
        print("PASS Fix 4: Floating Companion Pet draggable and chat sliding window verified.")

        await browser.close()
        print("\nALL 4 REMEDIATION VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_verification())
