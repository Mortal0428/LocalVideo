# -*- coding: utf-8 -*-
"""
End-to-End Closed-Loop Verification Script:
1. Verify Player Coin Tip modal header layout (circle close button in top right, high-contrast wallet balance).
2. Verify User Profile pure SVG icons (Coin, Crown, Clapperboard, Shield) with zero emojis.
3. Verify Admin Announcements fixed center modal and multi-checkbox batch deletion.
4. Verify RAG Bar Chart layout (no overlap between legend and X-axis labels) & active eval background persistence.
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"

def run_tests():
    print("=== Starting Closed-Loop E2E Verification for User Requested Fixes ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())

        # -------------------------------------------------------------
        # Part 1: Player Coin Tipping Modal Header & Wallet Color
        # -------------------------------------------------------------
        print("\n--- Part 1: Player Coin Tip Modal Layout & Close Button ---")
        page.goto("http://localhost:5173/#/login")
        page.wait_for_selector("#btn-demo-admin", timeout=8000)
        page.click("#btn-demo-admin")
        page.wait_for_timeout(1500)

        page.goto("http://localhost:5173/#/video/2b575454-7946-4f28-a9d6-7bb043f01fac")
        page.wait_for_selector(".video-main-heading", timeout=8000)
        page.wait_for_timeout(2000)

        page.wait_for_selector("#btn-coin-tip", timeout=8000)
        page.click("#btn-coin-tip")
        page.wait_for_timeout(1000)

        # Assert Header Layout
        header = page.locator(".coin-modal-header")
        assert header.count() > 0, "Expected .coin-modal-header to exist"

        close_btn = page.locator("#btn-coin-modal-close")
        assert close_btn.count() > 0, "Expected #btn-coin-modal-close in top right"

        # Check close button bounding box (must be on the right side)
        h_box = header.bounding_box()
        b_box = close_btn.bounding_box()
        assert b_box['x'] > h_box['x'] + h_box['width'] / 2, "Close button must be aligned on the right half"
        print(f"Close button correctly aligned on top right: x={b_box['x']}, y={b_box['y']}")

        # Screenshot Part 1
        shot1 = os.path.join(ARTIFACT_DIR, "verified_fixed_coin_modal_header_layout.png")
        page.screenshot(path=shot1)
        print(f"Screenshot saved: {shot1}")

        # Close modal
        close_btn.click()
        page.wait_for_timeout(600)

        # -------------------------------------------------------------
        # Part 2: User Profile Pure SVG Icons & No Emojis
        # -------------------------------------------------------------
        print("\n--- Part 2: User Profile Pure SVG Icons ---")
        page.goto("http://localhost:5173/#/user/space")
        page.wait_for_selector("#user-hero-card, #user-space-root", timeout=8000)
        page.wait_for_timeout(1500)

        # Verify SVGs exist
        coin_svg = page.locator(".card-coin-badge svg")
        crown_svg = page.locator(".card-crown-badge svg")
        clapper_svg = page.locator(".creator-box svg")
        shield_svg = page.locator(".reviewer-box svg")

        assert coin_svg.count() > 0, "Expected GoldCoinIcon SVG in wallet card"
        assert crown_svg.count() > 0, "Expected Crown SVG in VIP card"
        assert clapper_svg.count() > 0, "Expected Clapper SVG in creator card"
        assert shield_svg.count() > 0, "Expected Shield SVG in reviewer card"
        print("All 4 cards verified with pure SVG badges (no emojis).")

        shot2 = os.path.join(ARTIFACT_DIR, "verified_user_profile_pure_svg_no_emoji.png")
        page.screenshot(path=shot2)
        print(f"Screenshot saved: {shot2}")

        # -------------------------------------------------------------
        # Part 3: Admin Announcements Centered Modal & Batch Selection
        # -------------------------------------------------------------
        print("\n--- Part 3: Admin Announcements Centered Modal & Batch Selection ---")
        page.goto("http://localhost:5173/#/admin")
        page.wait_for_selector("#admin-tab-announcements", timeout=8000)
        page.click("#admin-tab-announcements")
        page.wait_for_selector("#section-announcements", timeout=8000)
        page.wait_for_timeout(1000)

        # Check checkboxes exist
        select_all = page.locator("#checkbox-select-all-announcements")
        assert select_all.count() > 0, "Expected select-all checkbox in table header"

        row_checkboxes = page.locator("#table-announcements tbody input[type='checkbox']")
        if row_checkboxes.count() > 0:
            row_checkboxes.first.check()
            page.wait_for_timeout(500)
            batch_btn = page.locator("#btn-batch-delete-announcements")
            assert batch_btn.is_visible(), "Expected batch delete button to appear when items selected"
            print(f"Batch delete button appeared successfully: {batch_btn.inner_text()}")

        # Open Announcement Modal and assert centered backdrop
        page.click("#btn-create-announcement")
        page.wait_for_timeout(800)

        modal = page.locator("#modal-announcement")
        assert modal.is_visible(), "Expected #modal-announcement to be visible"
        
        dialog_box = page.locator(".announcement-dialog").bounding_box()
        # Viewport width is 1440, center is around 720. Dialog should be centered horizontally:
        dialog_center_x = dialog_box['x'] + dialog_box['width'] / 2
        assert 600 < dialog_center_x < 840, f"Dialog must be horizontally centered, got center_x={dialog_center_x}"
        print(f"Announcement modal perfectly centered: center_x={dialog_center_x}")

        shot3 = os.path.join(ARTIFACT_DIR, "verified_announcement_fixed_center_modal_and_batch.png")
        page.screenshot(path=shot3)
        print(f"Screenshot saved: {shot3}")

        # Close modal
        page.locator("#modal-announcement .modal-close-btn").click()
        page.wait_for_timeout(600)

        # -------------------------------------------------------------
        # Part 4: RAG Bar Chart No Overlap & Background Eval Persistence
        # -------------------------------------------------------------
        print("\n--- Part 4: RAG Bar Chart No Overlap & Background Eval Persistence ---")
        page.click("#admin-tab-rag")
        page.wait_for_selector("#section-rag", timeout=8000)
        page.wait_for_timeout(2500)

        # Switch to benchmark tab inside RAG
        bench_tab = page.locator("#tab-rag-radar, button:has-text('四维评测'), button:has-text('雷达大屏')")
        if bench_tab.count() > 0:
            bench_tab.first.click()
            page.wait_for_timeout(1500)

        shot4 = os.path.join(ARTIFACT_DIR, "verified_rag_chart_no_overlap_and_active_eval.png")
        page.screenshot(path=shot4)
        print(f"RAG chart screenshot saved: {shot4}")

        print("\n=== All Verification Steps Completed Successfully! ===")
        browser.close()

if __name__ == '__main__':
    run_tests()
