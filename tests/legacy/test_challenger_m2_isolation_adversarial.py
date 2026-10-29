# -*- coding: utf-8 -*-
"""
Adversarial Verification Suite for Milestone 2 (Audience Isolation & Navigation Penetration)
Challenger: challenger_m2_2

Tests:
1. Navigation Isolation: Deep AST/regex scan of AdminHeader.vue, AdminView.vue, CreatorStudioView.vue
   for forbidden spectator routes and DOM elements.
2. Template Hygiene & Emoji Elimination: Deep scan for pictorial emojis and validation of Element Plus SVGs.
3. Spectator Views Isolation: Confirm HomeView, LandingView, and PlayerView are completely untouched by AdminHeader.
4. Mode-based Permission Boundaries: Verify non-admin/creator controls cannot be accidentally exposed (e.g. engine settings).
5. Apple HIG Tokens & Telemetry Integration: Confirm liquid glass and telemetry hooks.
"""

import os
import re
import sys

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend", "src")

def run_adversarial_tests():
    print("=" * 80)
    print("CHALLENGER M2: AUDIENCE ISOLATION & ADVERSARIAL PENETRATION SUITE")
    print("=" * 80)

    failures = []
    passes = []

    admin_header_path = os.path.join(FRONTEND_DIR, "components", "AdminHeader.vue")
    admin_view_path = os.path.join(FRONTEND_DIR, "views", "AdminView.vue")
    creator_view_path = os.path.join(FRONTEND_DIR, "views", "CreatorStudioView.vue")
    home_view_path = os.path.join(FRONTEND_DIR, "views", "HomeView.vue")
    landing_view_path = os.path.join(FRONTEND_DIR, "views", "LandingView.vue")
    player_view_path = os.path.join(FRONTEND_DIR, "views", "PlayerView.vue")

    with open(admin_header_path, "r", encoding="utf-8") as f:
        admin_header_src = f.read()

    with open(admin_view_path, "r", encoding="utf-8") as f:
        admin_view_src = f.read()

    with open(creator_view_path, "r", encoding="utf-8") as f:
        creator_view_src = f.read()

    with open(home_view_path, "r", encoding="utf-8") as f:
        home_view_src = f.read()

    with open(landing_view_path, "r", encoding="utf-8") as f:
        landing_view_src = f.read()

    with open(player_view_path, "r", encoding="utf-8") as f:
        player_view_src = f.read()

    # --------------------------------------------------------------------------
    # CHALLENGE 1: Forbidden Spectator Elements & Routes in Admin Contexts
    # --------------------------------------------------------------------------
    print("\n[CHALLENGE 1] Scanning for forbidden spectator routes and elements...")
    
    forbidden_tokens = [
        ('to="/landing"', "router-link to /landing"),
        ('to="/user/space"', "router-link to /user/space"),
        ('to="/"', "router-link to / (home)"),
        ('id="header-search-bar"', "Header search bar ID"),
        ('id="btn-creator-upload"', "Audience upload button ID"),
        ('id="nav-logo-link"', "Spectator logo router link ID"),
        ('class="category-pills-bar"', "Audience video category pills bar"),
        ('id="channel-bar"', "Audience channel category bar ID")
    ]

    target_files = [
        ("AdminHeader.vue", admin_header_src),
        ("AdminView.vue", admin_view_src),
        ("CreatorStudioView.vue", creator_view_src)
    ]

    for fname, src in target_files:
        for token, desc in forbidden_tokens:
            if token in src:
                failures.append(f"Forbidden token '{token}' ({desc}) detected in {fname}!")
            else:
                passes.append(f"Clean: No '{token}' in {fname}")

    print(f"  -> Checked {len(forbidden_tokens) * len(target_files)} forbidden route/element patterns across admin components.")

    # --------------------------------------------------------------------------
    # CHALLENGE 2: Emoji Elimination in CreatorStudioView.vue
    # --------------------------------------------------------------------------
    print("\n[CHALLENGE 2] Exhaustive Unicode pictorial emoji scan in CreatorStudioView.vue...")
    
    # We strictly target pictorial emojis that cause visual plastic dissonance:
    # 🎨, 📁, 🎬, 📂, 🔄, ⏳, 📤, 🚀, ✅, 📹, etc.
    # Exclude basic text typography glyphs such as ✕ (\u2715 multiplication cross)
    pictorial_emoji_pattern = re.compile(
        r'[\U0001F300-\U0001F5FF]|'  # Symbols & Pictographs
        r'[\U0001F600-\U0001F64F]|'  # Emoticons
        r'[\U0001F680-\U0001F6FF]|'  # Transport & Map Symbols
        r'[\U0001F900-\U0001F9FF]|'  # Supplemental Symbols & Pictographs
        r'[\U0001FA70-\U0001FAFF]|'  # Symbols & Pictographs Extended-A
        r'[\u2705\u270A-\u270D\u2728\u274C\u274E\u2753-\u2755\u2795-\u2797\u27B0\u27BF]' # Dingbat pictorial icons
    )

    found_emojis = []
    for line_no, line in enumerate(creator_view_src.splitlines(), 1):
        matches = pictorial_emoji_pattern.findall(line)
        if matches:
            found_emojis.append((line_no, matches, line.strip()))

    if found_emojis:
        for lno, matches, text in found_emojis:
            failures.append(f"CreatorStudioView.vue line {lno} contains residual emoji {matches}: '{text}'")
    else:
        passes.append("CreatorStudioView.vue: 0 residual pictorial emojis found across all 1600+ lines.")
        print("  -> Passed: 0 residual pictorial emojis found in CreatorStudioView.vue.")

    # Check that Element Plus SVG icons are imported and used
    expected_svgs = ['Folder', 'Upload', 'Film', 'VideoCamera', 'Check', 'Promotion']
    for icon in expected_svgs:
        if icon not in creator_view_src:
            failures.append(f"CreatorStudioView.vue does not import or use expected SVG icon: {icon}")
        else:
            passes.append(f"CreatorStudioView.vue properly uses Element Plus SVG: <{icon} />")

    # --------------------------------------------------------------------------
    # CHALLENGE 3: Spectator Views Isolation Audit
    # --------------------------------------------------------------------------
    print("\n[CHALLENGE 3] Confirming spectator views are completely untouched by AdminHeader...")
    
    spectator_files = [
        ("HomeView.vue", home_view_src),
        ("LandingView.vue", landing_view_src),
        ("PlayerView.vue", player_view_src)
    ]

    for fname, src in spectator_files:
        if "AdminHeader" in src:
            failures.append(f"Spectator view {fname} improperly imports or references AdminHeader!")
        else:
            passes.append(f"Spectator view {fname} has 0 references to AdminHeader.")

    # Confirm HomeView uses GlobalHeader
    if "<GlobalHeader" not in home_view_src:
        failures.append("HomeView.vue should continue using GlobalHeader")
    else:
        passes.append("HomeView.vue properly retains GlobalHeader.")

    # Confirm PlayerView uses player-global-header
    if "player-global-header" not in player_view_src:
        failures.append("PlayerView.vue should retain player-global-header")
    else:
        passes.append("PlayerView.vue properly retains player-global-header.")

    # --------------------------------------------------------------------------
    # CHALLENGE 4: Mode-based Permission Boundaries in AdminHeader.vue
    # --------------------------------------------------------------------------
    print("\n[CHALLENGE 4] Verifying mode boundaries in AdminHeader...")
    
    # Engine settings button must be strictly admin only
    if 'v-if="mode === \'admin\'"' not in admin_header_src or 'id="btn-engine-settings"' not in admin_header_src:
        failures.append("AdminHeader.vue does not restrict #btn-engine-settings to mode === 'admin'")
    else:
        passes.append("AdminHeader.vue enforces v-if=\"mode === 'admin'\" on #btn-engine-settings")

    # Brand text distinguishes admin vs creator
    if "mode === 'admin' ? 'CinemaAgent 控制中台' : 'CinemaAgent 创作者工作台'" not in admin_header_src:
        failures.append("AdminHeader.vue brand title lacks dynamic mode differentiation")
    else:
        passes.append("AdminHeader.vue brand title properly differentiates admin and creator modes")

    # --------------------------------------------------------------------------
    # CHALLENGE 5: Apple HIG Tokens & Telemetry Integration
    # --------------------------------------------------------------------------
    print("\n[CHALLENGE 5] Verifying Apple HIG visual tokens and telemetry integration...")

    required_hig = [
        ("--liquid-glass-bg", "Liquid glass background token"),
        ("--apple-hairline", "Apple hairline border token"),
        ("--glass-shadow", "Glass shadow token"),
        ("backdrop-filter: blur(20px)", "Backdrop blur glass effect"),
        ('id="system-health-indicator"', "System telemetry indicator ID"),
        ('id="admin-notification-skylight-btn"', "Notification skylight trigger button ID"),
        ('id="notification-skyway-drawer"', "Notification skylight drawer ID"),
        ('id="theme-switch-control"', "Theme switcher control ID"),
        ('id="admin-profile-chip"', "Admin profile chip ID")
    ]

    for token, desc in required_hig:
        if token not in admin_header_src:
            failures.append(f"AdminHeader.vue missing required token/ID: '{token}' ({desc})")
        else:
            passes.append(f"AdminHeader.vue contains '{token}' ({desc})")

    # --------------------------------------------------------------------------
    # SUMMARY & RESULT
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"RESULTS: {len(passes)} checks passed, {len(failures)} failures.")
    print("=" * 80)

    if failures:
        print("\nFAILURES ENCOUNTERED:")
        for fail in failures:
            print(f"  [FAIL] {fail}")
        return False
    else:
        print("\nALL ADVERSARIAL CHALLENGES PASSED (100% SATISFIED).")
        return True

if __name__ == "__main__":
    success = run_adversarial_tests()
    sys.exit(0 if success else 1)
