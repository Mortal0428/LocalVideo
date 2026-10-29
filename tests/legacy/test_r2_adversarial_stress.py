# -*- coding: utf-8 -*-
"""
Adversarial Stress & Component Robustness Test Suite for Milestone 2 (R2: Admin & Creator UI/UX Cohesion)

Tests:
1. Telemetry Error Resilience & Graceful Degradation (500 Error, Timeout, Malformed JSON, Degraded/Down states, Latency boundaries)
2. Theme Switching Stress & Edge Cases (Rapid cycling, invalid localStorage values, empty strings)
3. Z-Index Layering, Drawer Collisions, and Overlay Mutual Exclusivity
4. Creator Studio View Header Isolation & Apple HIG Visual Consistency
"""

import os
import sys
import time
import json
import traceback
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://127.0.0.1:5173"
BACKEND_URL = "http://127.0.0.1:8000"
SCREENSHOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage", "test_screenshots"))
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


class AdversarialTestRunner:
    def __init__(self):
        self.results = []

    def record(self, code: str, title: str, status: str, detail: str = "", duration: float = 0.0):
        self.results.append({
            "code": code,
            "title": title,
            "status": status,
            "detail": detail,
            "duration": duration
        })
        badge = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f"  {badge} {code}: {title} ({duration:.2f}s)")
        if detail and status == "FAIL":
            print(f"         Reason: {detail}")

    def summary(self) -> int:
        print("\n" + "=" * 90)
        print("MILESTONE 2 (R2) ADVERSARIAL STRESS TEST SUMMARY")
        print("=" * 90)
        print(f"{'Code':<8} | {'Title':<50} | {'Status':<10} | {'Time (s)':<8}")
        print("-" * 90)
        failed = 0
        for r in self.results:
            if r["status"] == "FAIL":
                failed += 1
            print(f"{r['code']:<8} | {r['title'][:50]:<50} | {r['status']:<10} | {r['duration']:<8.2f}")
        print("-" * 90)
        total = len(self.results)
        passed = total - failed
        print(f"Total Tests: {total} | Passed: {passed} | Failed: {failed}")
        print("=" * 90)
        return 1 if failed > 0 else 0


def ensure_admin_logged_in(page):
    """Logs into admin console if not already authenticated."""
    page.goto(f"{FRONTEND_URL}/#/admin", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1000)

    # Check if redirected to login
    if "#/login" in page.url or page.locator("#input-login-username").count() > 0:
        if page.locator("#input-login-username").count() > 0:
            page.fill("#input-login-username", "admin")
            page.fill("#input-login-password", "password123")
            page.click("#btn-submit-login")
            page.wait_for_timeout(1500)
            page.goto(f"{FRONTEND_URL}/#/admin", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1000)


def run_adversarial_suite():
    runner = AdversarialTestRunner()

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)

        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Capture uncaught page errors
        page_errors = []
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        print("\n>>> Stage 1: Telemetry Error Resilience & Fallback Degradation...")

        # ----------------------------------------------------------------------
        # Test ADV-R2-01: Telemetry 500 Internal Server Error Graceful Degradation
        # ----------------------------------------------------------------------
        t0 = time.time()
        try:
            page_errors.clear()
            # Intercept telemetry with 500
            def handle_telemetry_500(route):
                route.fulfill(status=500, content_type="application/json", body=json.dumps({"detail": "Internal Server Outage"}))

            page.route("**/api/v1/system/telemetry", handle_telemetry_500)
            ensure_admin_logged_in(page)

            # Click refresh button inside telemetry or wait for fetch
            assert page.locator("#admin-header").is_visible(), "AdminHeader must be visible even when telemetry fails"
            assert page.locator("#system-health-indicator").is_visible(), "Telemetry capsule must be visible on 500"

            # Check that page did not crash
            assert len(page_errors) == 0, f"Uncaught page errors on 500: {page_errors}"

            capsule_text = page.locator("#system-health-indicator").inner_text()
            assert "系统" in capsule_text or "CLOSED" in capsule_text, f"Capsule missing fallback text: {capsule_text}"

            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "adv_r2_telemetry_500_resilience.png"))
            runner.record("ADV-R2-01", "Telemetry HTTP 500 Resilience & Fallback", "PASS", duration=time.time() - t0)
        except Exception as e:
            runner.record("ADV-R2-01", "Telemetry HTTP 500 Resilience & Fallback", "FAIL", str(e), duration=time.time() - t0)
        finally:
            page.unroute("**/api/v1/system/telemetry")

        # ----------------------------------------------------------------------
        # Test ADV-R2-02: Telemetry Network Abort / Timeout Resilience
        # ----------------------------------------------------------------------
        t0 = time.time()
        try:
            page_errors.clear()
            def handle_telemetry_abort(route):
                route.abort("failed")

            page.route("**/api/v1/system/telemetry", handle_telemetry_abort)
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

            assert page.locator("#admin-header").is_visible(), "AdminHeader must remain functional on network abort"
            assert page.locator("#system-health-indicator").is_visible(), "Telemetry capsule must render on abort"
            assert len(page_errors) == 0, f"Uncaught page error on network abort: {page_errors}"

            runner.record("ADV-R2-02", "Telemetry Network Abort / Timeout Graceful Handling", "PASS", duration=time.time() - t0)
        except Exception as e:
            runner.record("ADV-R2-02", "Telemetry Network Abort / Timeout Graceful Handling", "FAIL", str(e), duration=time.time() - t0)
        finally:
            page.unroute("**/api/v1/system/telemetry")

        # ----------------------------------------------------------------------
        # Test ADV-R2-03: Telemetry Degraded & Down State Indicators
        # ----------------------------------------------------------------------
        t0 = time.time()
        try:
            # 1. Test degraded status
            degraded_payload = {
                "status": "degraded",
                "circuit_state": "HALF-OPEN",
                "active_provider": "ollama",
                "active_model": "deepseek-r1:1.5b",
                "latency_ms": 780.0,
                "uptime_seconds": 3600,
                "pending_reviews_count": 4,
                "consecutive_failures": 2,
                "recovery_countdown_seconds": 15.0
            }
            page.route("**/api/v1/system/telemetry", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(degraded_payload)))
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

            capsule = page.locator("#system-health-indicator")
            assert "is-degraded" in (capsule.get_attribute("class") or ""), "Capsule must have class is-degraded"
            assert "降级" in capsule.inner_text(), "Capsule must display degraded status text"
            assert "HALF-OPEN" in capsule.inner_text(), "Capsule must display HALF-OPEN state"

            # 2. Test down status
            page.unroute("**/api/v1/system/telemetry")
            down_payload = {
                "status": "down",
                "circuit_state": "OPEN",
                "active_provider": "ollama",
                "active_model": "deepseek-r1:1.5b",
                "latency_ms": 0.0,
                "uptime_seconds": 3600,
                "pending_reviews_count": 0,
                "consecutive_failures": 5,
                "recovery_countdown_seconds": 30.0
            }
            page.route("**/api/v1/system/telemetry", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(down_payload)))
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

            assert "is-down" in (capsule.get_attribute("class") or ""), "Capsule must have class is-down"
            assert "离线" in capsule.inner_text() or "故障" in capsule.inner_text(), "Capsule must display down text"
            assert "OPEN" in capsule.inner_text(), "Capsule must display OPEN state"

            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "adv_r2_telemetry_down_state.png"))
            runner.record("ADV-R2-03", "Telemetry Degraded (HALF-OPEN) & Down (OPEN) Visuals", "PASS", duration=time.time() - t0)
        except Exception as e:
            runner.record("ADV-R2-03", "Telemetry Degraded (HALF-OPEN) & Down (OPEN) Visuals", "FAIL", str(e), duration=time.time() - t0)
        finally:
            page.unroute("**/api/v1/system/telemetry")

        # ----------------------------------------------------------------------
        # Test ADV-R2-04: Boundary Latency and Null Field Formatting
        # ----------------------------------------------------------------------
        t0 = time.time()
        try:
            boundary_payload = {
                "status": "healthy",
                "circuit_state": None,
                "active_provider": "ollama",
                "active_model": "deepseek-r1:1.5b",
                "latency_ms": -5.0,
                "uptime_seconds": 0,
                "pending_reviews_count": None
            }
            page.route("**/api/v1/system/telemetry", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(boundary_payload)))
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

            capsule_text = page.locator("#system-health-indicator").inner_text()
            assert "NaN" not in capsule_text, f"Capsule rendered NaN: {capsule_text}"
            assert "CLOSED" in capsule_text, "Missing fallback CLOSED circuit state"

            runner.record("ADV-R2-04", "Boundary Latency & Null Fields Safe Formatting", "PASS", duration=time.time() - t0)
        except Exception as e:
            runner.record("ADV-R2-04", "Boundary Latency & Null Fields Safe Formatting", "FAIL", str(e), duration=time.time() - t0)
        finally:
            page.unroute("**/api/v1/system/telemetry")

        print("\n>>> Stage 2: Theme Switching Stress & Edge Cases...")

        # ----------------------------------------------------------------------
        # Test ADV-R2-05: Rapid Theme Toggle Stress (60 rapid clicks)
        # ----------------------------------------------------------------------
        t0 = time.time()
        try:
            ensure_admin_logged_in(page)
            light_btn = page.locator("#btn-theme-light")
            dark_btn = page.locator("#btn-theme-dark")
            system_btn = page.locator("#btn-theme-system")

            assert light_btn.is_visible(), "Light theme button must be visible"
            assert dark_btn.is_visible(), "Dark theme button must be visible"
            assert system_btn.is_visible(), "System theme button must be visible"

            # Perform 60 rapid cycles
            for i in range(20):
                light_btn.click()
                dark_btn.click()
                system_btn.click()

            # Finish on dark mode
            dark_btn.click()
            page.wait_for_timeout(200)

            theme_val = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
            local_val = page.evaluate("() => localStorage.getItem('cinema_theme')")
            assert theme_val == "dark", f"Expected dark theme after rapid toggles, got {theme_val}"
            assert local_val == "dark", f"Expected localStorage cinema_theme=dark, got {local_val}"

            # Now switch to light mode
            light_btn.click()
            page.wait_for_timeout(200)
            theme_val2 = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
            local_val2 = page.evaluate("() => localStorage.getItem('cinema_theme')")
            assert theme_val2 == "light", f"Expected light theme, got {theme_val2}"
            assert local_val2 == "light", f"Expected localStorage cinema_theme=light, got {local_val2}"

            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "adv_r2_theme_rapid_stress.png"))
            runner.record("ADV-R2-05", "Rapid 60x Theme Toggles & Persistence Stress", "PASS", duration=time.time() - t0)
        except Exception as e:
            runner.record("ADV-R2-05", "Rapid 60x Theme Toggles & Persistence Stress", "FAIL", str(e), duration=time.time() - t0)

        # ----------------------------------------------------------------------
        # Test ADV-R2-06: Corrupted / Invalid localStorage Theme Fallback
        # ----------------------------------------------------------------------
        t0 = time.time()
        try:
            # Set corrupted theme
            page.evaluate("() => localStorage.setItem('cinema_theme', 'CORRUPT_XSS_INJECTION_<script>')")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(800)

            current_theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
            assert current_theme in ["light", "dark"], f"Expected fallback to light/dark, got '{current_theme}'"

            # Set empty string
            page.evaluate("() => localStorage.setItem('cinema_theme', '')")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(800)
            empty_theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
            assert empty_theme in ["light", "dark"], f"Expected fallback from empty string, got '{empty_theme}'"

            runner.record("ADV-R2-06", "Corrupted localStorage Theme Value Sanitization", "PASS", duration=time.time() - t0)
        except Exception as e:
            runner.record("ADV-R2-06", "Corrupted localStorage Theme Value Sanitization", "FAIL", str(e), duration=time.time() - t0)

        print("\n>>> Stage 3: Z-Index Layering, Drawer Collisions, and Mutual Exclusivity...")

        # ----------------------------------------------------------------------
        # Test ADV-R2-07: Telemetry Popover Z-Index & Non-Clipping Verification
        # ----------------------------------------------------------------------
        t0 = time.time()
        try:
            ensure_admin_logged_in(page)
            # Open telemetry popover
            page.click("#system-health-indicator")
            page.wait_for_timeout(500)

            popover = page.locator("#telemetry-popover-card")
            assert popover.is_visible(), "Telemetry popover card must be visible on click"

            z_index = page.evaluate("() => window.getComputedStyle(document.getElementById('telemetry-popover-card')).zIndex")
            assert int(z_index) >= 1010, f"Expected popover z-index >= 1010, got {z_index}"

            # Hit-test element at center of popover
            box = popover.bounding_box()
            assert box is not None, "Popover bounding box is None"
            cx = box["x"] + box["width"] / 2
            cy = box["y"] + box["height"] / 2

            hit_tag = page.evaluate(f"() => {{ const el = document.elementFromPoint({cx}, {cy}); return el ? (el.id || el.className || el.tagName) : 'null'; }}")
            # Element hit must be part of popover
            is_descendant = page.evaluate(f"() => {{ const el = document.elementFromPoint({cx}, {cy}); return document.getElementById('telemetry-popover-card').contains(el); }}")
            assert is_descendant, f"Popover covered by another element! Hit element: {hit_tag}"

            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "adv_r2_telemetry_popover_layering.png"))
            runner.record("ADV-R2-07", "Telemetry Popover Z-Index (1010) & Hit-Test Isolation", "PASS", duration=time.time() - t0)
        except Exception as e:
            runner.record("ADV-R2-07", "Telemetry Popover Z-Index (1010) & Hit-Test Isolation", "FAIL", str(e), duration=time.time() - t0)

        # ----------------------------------------------------------------------
        # Test ADV-R2-08: Notification Skylight Drawer Layering & Hit-Test
        # ----------------------------------------------------------------------
        t0 = time.time()
        try:
            # Click skylight notification button
            page.click("#admin-notification-skylight-btn")
            page.wait_for_timeout(500)

            drawer = page.locator("#notification-skyway-drawer")
            assert drawer.is_visible(), "Notification skylight drawer must be visible on button click"

            z_index = page.evaluate("() => window.getComputedStyle(document.getElementById('notification-skyway-drawer')).zIndex")
            assert int(z_index) >= 1010, f"Expected drawer z-index >= 1010, got {z_index}"

            box = drawer.bounding_box()
            assert box is not None, "Drawer bounding box is None"
            cx = box["x"] + box["width"] / 2
            cy = box["y"] + min(box["height"] / 2, 200)

            is_descendant = page.evaluate(f"() => {{ const el = document.elementFromPoint({cx}, {cy}); return document.getElementById('notification-skyway-drawer').contains(el); }}")
            assert is_descendant, "Notification drawer covered by another element!"

            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "adv_r2_skylight_drawer_layering.png"))
            runner.record("ADV-R2-08", "Notification Skylight Drawer Z-Index (1010) & Layering", "PASS", duration=time.time() - t0)
        except Exception as e:
            runner.record("ADV-R2-08", "Notification Skylight Drawer Z-Index (1010) & Layering", "FAIL", str(e), duration=time.time() - t0)

        # ----------------------------------------------------------------------
        # Test ADV-R2-09: Overlay Mutual Exclusivity and Backdrop Dismissal
        # ----------------------------------------------------------------------
        t0 = time.time()
        try:
            # 1. Open drawer
            page.click("#admin-notification-skylight-btn")
            page.wait_for_timeout(300)
            assert page.locator("#notification-skyway-drawer").is_visible(), "Drawer should be open"
            assert page.locator("#telemetry-popover-card").count() == 0, "Popover should be closed when drawer is open"

            # 2. Open popover -> drawer must close
            page.click("#system-health-indicator")
            page.wait_for_timeout(300)
            assert page.locator("#telemetry-popover-card").is_visible(), "Popover should be open"
            assert page.locator("#notification-skyway-drawer").count() == 0, "Drawer must close when popover is opened"

            # 3. Open profile menu -> popover must close
            page.click("#admin-profile-chip")
            page.wait_for_timeout(300)
            assert page.locator("#admin-profile-dropdown").is_visible(), "Profile dropdown should be open"
            assert page.locator("#telemetry-popover-card").count() == 0, "Popover must close when profile is opened"

            # 4. Click backdrop -> all overlays close
            assert page.locator(".admin-header-backdrop").is_visible(), "Backdrop must be present when overlay is open"
            page.click(".admin-header-backdrop", position={"x": 50, "y": 300})
            page.wait_for_timeout(300)

            assert page.locator("#admin-profile-dropdown").count() == 0, "Profile dropdown must close on backdrop click"
            assert page.locator("#telemetry-popover-card").count() == 0, "Popover must close on backdrop click"
            assert page.locator("#notification-skyway-drawer").count() == 0, "Drawer must close on backdrop click"

            runner.record("ADV-R2-09", "Overlays Mutual Exclusivity & Backdrop Dismissal", "PASS", duration=time.time() - t0)
        except Exception as e:
            runner.record("ADV-R2-09", "Overlays Mutual Exclusivity & Backdrop Dismissal", "FAIL", str(e), duration=time.time() - t0)

        print("\n>>> Stage 4: Creator Studio View & Spectator Isolation...")

        # ----------------------------------------------------------------------
        # Test ADV-R2-10: CreatorStudioView Mounts AdminHeader & Zero Spectator Nav
        # ----------------------------------------------------------------------
        t0 = time.time()
        try:
            page.goto(f"{FRONTEND_URL}/#/creator", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1500)

            assert page.locator("#admin-header").is_visible(), "CreatorStudioView must mount AdminHeader"
            badge_title = page.locator("#admin-brand-badge .brand-title").inner_text()
            assert "创作者" in badge_title, f"Expected creator branding in badge, got '{badge_title}'"

            # Check absolute absence of spectator nav
            prohibited_ids = ["#header-search-bar", "#btn-creator-upload", "#nav-logo-link", "#home-search-input"]
            for pid in prohibited_ids:
                assert page.locator(pid).count() == 0, f"Spectator element {pid} leaked into CreatorStudioView"

            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "adv_r2_creator_studio_isolation.png"))
            runner.record("ADV-R2-10", "Creator Studio AdminHeader Mount & Spectator Stripping", "PASS", duration=time.time() - t0)
        except Exception as e:
            runner.record("ADV-R2-10", "Creator Studio AdminHeader Mount & Spectator Stripping", "FAIL", str(e), duration=time.time() - t0)

        browser.close()

    return runner.summary()


if __name__ == "__main__":
    sys.exit(run_adversarial_suite())
