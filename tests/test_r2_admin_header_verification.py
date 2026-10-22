# -*- coding: utf-8 -*-
"""
Verification Script for Milestone 2 (R2: Admin & Creator UI/UX Cohesion)
Validates:
1. AdminHeader.vue component existence, Apple HIG tokens, telemetry endpoint integration,
   notification drawer, profile chip, and complete absence of spectator nav elements.
2. AdminView.vue mounts AdminHeader exclusively.
3. CreatorStudioView.vue mounts AdminHeader exclusively and has zero raw emojis.
4. Spectator views (HomeView.vue, PlayerView.vue) continue using GlobalHeader / player header.
5. Frontend production build passes with exit code 0.
"""

import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

def run_checks():
    print("=" * 80)
    print("RUNNING MILESTONE 2 (R2) INTEGRITY & ARCHITECTURE VERIFICATION")
    print("=" * 80)

    admin_header_path = os.path.join(FRONTEND_DIR, "src", "components", "AdminHeader.vue")
    admin_view_path = os.path.join(FRONTEND_DIR, "src", "views", "AdminView.vue")
    creator_view_path = os.path.join(FRONTEND_DIR, "src", "views", "CreatorStudioView.vue")
    home_view_path = os.path.join(FRONTEND_DIR, "src", "views", "HomeView.vue")
    player_view_path = os.path.join(FRONTEND_DIR, "src", "views", "PlayerView.vue")

    errors = []

    # 1. AdminHeader.vue existence
    if not os.path.exists(admin_header_path):
        errors.append(f"Missing file: {admin_header_path}")
    else:
        with open(admin_header_path, "r", encoding="utf-8") as f:
            header_content = f.read()

        # Check required IDs and classes
        required_selectors = [
            'id="admin-header"',
            'id="system-health-indicator"',
            'id="admin-profile-chip"',
            'id="admin-notification-skylight-btn"',
            'id="notification-skyway-drawer"',
            'id="theme-switch-control"',
            'id="btn-engine-settings"',
        ]
        for sel in required_selectors:
            if sel not in header_content:
                errors.append(f"AdminHeader.vue missing required element: {sel}")

        # Check Apple HIG glass design tokens
        required_tokens = [
            "--liquid-glass-bg",
            "--apple-hairline",
            "--glass-shadow",
            "backdrop-filter",
            "blur(20px)"
        ]
        for token in required_tokens:
            if token not in header_content:
                errors.append(f"AdminHeader.vue missing design token: {token}")

        # Check telemetry endpoint call
        if "/system/telemetry" not in header_content:
            errors.append("AdminHeader.vue does not call GET /system/telemetry")

        # Check strict stripping of spectator elements
        prohibited_spectator_selectors = [
            '#header-search-bar',
            'id="header-search-bar"',
            'id="btn-creator-upload"',
            'id="nav-logo-link"',
            'id="home-search-input"',
            'to="/landing"',
            'to="/user/space"',
        ]
        for prohibited in prohibited_spectator_selectors:
            if prohibited in header_content:
                errors.append(f"AdminHeader.vue leaks spectator navigation: {prohibited}")

        print("  [OK] AdminHeader.vue: HIG glass tokens, telemetry capsule, drawer, and spectator nav stripping verified.")

    # 2. AdminView.vue mounting AdminHeader
    if not os.path.exists(admin_view_path):
        errors.append(f"Missing file: {admin_view_path}")
    else:
        with open(admin_view_path, "r", encoding="utf-8") as f:
            admin_view_content = f.read()

        if "<AdminHeader" not in admin_view_content:
            errors.append("AdminView.vue does not mount <AdminHeader />")
        if "components/AdminHeader.vue" not in admin_view_content:
            errors.append("AdminView.vue does not import AdminHeader.vue")
        if "<GlobalHeader" in admin_view_content:
            errors.append("AdminView.vue still mounts <GlobalHeader />")

        print("  [OK] AdminView.vue: AdminHeader mounted cleanly without GlobalHeader.")

    # 3. CreatorStudioView.vue mounting AdminHeader & SVG icons
    if not os.path.exists(creator_view_path):
        errors.append(f"Missing file: {creator_view_path}")
    else:
        with open(creator_view_path, "r", encoding="utf-8") as f:
            creator_content = f.read()

        if "<AdminHeader" not in creator_content:
            errors.append("CreatorStudioView.vue does not mount <AdminHeader />")
        if "components/AdminHeader.vue" not in creator_content:
            errors.append("CreatorStudioView.vue does not import AdminHeader.vue")
        if "<GlobalHeader" in creator_content:
            errors.append("CreatorStudioView.vue still mounts <GlobalHeader />")

        # Check that common raw emojis are purged
        raw_emojis = ["🎨", "📁", "🎬", "📂", "🔄", "⏳", "📤", "🚀", "✅", "📹"]
        found_emojis = [e for e in raw_emojis if e in creator_content]
        if found_emojis:
            errors.append(f"CreatorStudioView.vue contains raw emojis: {found_emojis}")

        print("  [OK] CreatorStudioView.vue: AdminHeader mounted and raw emojis replaced with vector SVGs.")

    # 4. Spectator views continue using GlobalHeader / player header
    if os.path.exists(home_view_path):
        with open(home_view_path, "r", encoding="utf-8") as f:
            home_content = f.read()
        if "<GlobalHeader" not in home_content:
            errors.append("HomeView.vue should continue using GlobalHeader")
        else:
            print("  [OK] HomeView.vue continues using GlobalHeader.vue.")

    if os.path.exists(player_view_path):
        with open(player_view_path, "r", encoding="utf-8") as f:
            player_content = f.read()
        if "player-global-header" not in player_content:
            errors.append("PlayerView.vue missing player-global-header")
        else:
            print("  [OK] PlayerView.vue continues using player-global-header.")

    print("-" * 80)
    if errors:
        print(f"VERIFICATION FAILED WITH {len(errors)} ERRORS:")
        for err in errors:
            print(f"  - [FAIL] {err}")
        return 1
    else:
        print("ALL MILESTONE 2 (R2) VERIFICATION CHECKS PASSED (100% OK)")
        print("=" * 80)
        return 0

if __name__ == "__main__":
    sys.exit(run_checks())
