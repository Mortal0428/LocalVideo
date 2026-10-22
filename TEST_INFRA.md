# E2E Test Infra: CinemaAgent Phase 2 Dual Track

## 1. Test Philosophy
- **Opaque-Box & Requirement-Driven**: Derived strictly from `ORIGINAL_REQUEST.md` (header `## 2026-10-21T06:18:50Z`) and `PROJECT.md` interface specifications. The test suite exercises the system entirely through external entry points (HTTP REST APIs, multi-user WebSocket events, and browser DOM interactions via Playwright).
- **Zero Mock / Authentic Multi-User Persistence**: Validates real MySQL 8.0 database transactions across user boundaries. Tests multi-user isolation by spinning up independent browser contexts (`browser.new_context()`) for User A (creator/viewer), User B (replier/liker), and Admin, ensuring realistic concurrent workflows and localStorage/cookie separation.
- **Progressive Testability & Deterministic Verification**: Organized into 4 progressive tiers (Feature Coverage, Boundary & Corner Cases, Cross-Module Combinations, and Real-World User Journeys S1-S6), plus Tier 5 adversarial hardening.
- **Fail-Fast & Transparent Telemetry**: Each test flow is atomic, self-contained, cleans up or namespaces test artifacts, records millisecond-precision timing, and automatically archives high-definition timestamped PNG screenshots to `storage/test_screenshots/`.

---

## 2. Feature Inventory & Test Mapping (28 Features)

| # | Feature Description | Milestone | Source Requirement | Tier 1 (F1-F15) | Tier 2 (B1-B12) | Tier 3 (C1-C8) | Tier 4 (S1-S6) |
|---|---------------------|:---------:|:------------------:|:---------------:|:---------------:|:--------------:|:--------------:|
| 1 | Two-Tier Comments DB Model (`UserComment`) | M1 | R1 | F1, F2 | B7, B8 | C1 | S1 |
| 2 | Comment Likes DB Model (`CommentLike`) | M1 | R1 | F3 | B9 | C2 | S1 |
| 3 | Two-Tier Comments APIs (`/interactions/episodes/...`) | M1 | R1 | F1, F2, F3 | B7, B8, B9 | C1, C2 | S1 |
| 4 | Video Like Status & Persistence (`like_count`, `heat_score`) | M1 | R1 | F4 | B9 | C8 | S1 |
| 5 | Coin Wallet & Transactions Models (`user_coin_wallets`) | M1 | R2 | F5, F6, F7 | B2, B3, B11 | C3 | S2 |
| 6 | Video Coin Tip Model & Heat Score (`video_coin_tips`) | M1 | R2 | F8 | B1, B11 | C3 | S2 |
| 7 | Coin Economy APIs (`/user/coins/...`) | M1 | R2 | F5, F6, F7, F9 | B2, B3 | C3, C5 | S2 |
| 8 | Video Tip APIs (`/interactions/episodes/{id}/tip`) | M1 | R2 | F8 | B1, B11 | C3 | S2 |
| 9 | System Announcements Models & APIs (`system_announcements`) | M1 | R3 | F10 | B6 | C4 | S1 |
| 10 | User Notifications Models & APIs (`user_notifications`) | M1 | R3 | F11, F12 | B12 | C1, C2, C4 | S1 |
| 11 | Admin Full User CRUD APIs (`/admin/users/...`) | M1 | R4 | F13 | B6, B10 | C5, C7 | S3 |
| 12 | Local Secure Image Upload API (`/api/v1/upload/image`) | M1 | R4 | F14 | B4, B5 | C6 | S4 |
| 13 | User History & Likes Bug Fixes (`last_episode_id`, 500 fix) | M1 | R5 | F15 | B12 | C5 | S6 |
| 14 | PlayerView Two-Tier Comments UI | M2 | R1 | - | - | C1 | S1 |
| 15 | PlayerView Real Likes Persistence UI | M2 | R1 | - | - | C8 | S1 |
| 16 | GlobalHeader Notification Skylight & Bell | M2 | R3 | - | - | C1 | S1, S6 |
| 17 | NotificationSkylight Drawer Component (3 Tabs, Jump) | M2 | R3 | - | - | C1, C4 | S1 |
| 18 | GlobalHeader CSS Bug Fix (text squeeze & purple underline) | M2 | R5 | - | - | - | S6 |
| 19 | UserProfileView Navigation & History Jump Fix | M2 | R5 | - | - | - | S6 |
| 20 | PlayerView Coin Tip Modal (1-2 coins, max limit, heat) | M3 | R2 | - | B1 | C3 | S2 |
| 21 | UserProfileView Economy Bento Cards (Coins, VIP) | M3 | R2 | - | B3 | C5 | S2, S6 |
| 22 | AdminView Full User CRUD UI (Add, Edit, Reset, Delete) | M3 | R4 | - | B6, B10 | C5, C7 | S3 |
| 23 | AdminView Drama Cover Drag-and-Drop & Multi-Poster | M3 | R4 | - | B4, B5 | C6 | S4 |
| 24 | AdminView Carousel 16:9 WYSIWYG Live Preview | M3 | R4 | - | - | - | S5 |
| 25 | AdminView Visual Cohesion (Apple HIG Dark Glass) | M3 | R5 | - | - | - | S6 |
| 26 | E2E Closed-Loop Multi-User Testing Suite | M4 | R6 | Master Runner | Master Runner | Master Runner | Master Runner |
| 27 | High-Definition Test Screenshot Archiving Pipeline | M4 | R6 | ✓ | ✓ | ✓ | ✓ |
| 28 | Tier 5 Adversarial Coverage Hardening | M4 | R6 | ✓ | ✓ | ✓ | - |

---

## 3. Test Architecture & Directory Layout

### 3.1 Test Architecture
- **Framework**: Python 3.13 + Pytest 9.0.3 + Playwright 1.55.0 (`playwright.sync_api`).
- **Browser Channel**: Microsoft Edge (`channel="msedge"`) with automated fallback to Chromium; Viewport `1440x900`, device scale factor 1.0.
- **Multi-Context Session Orchestration**:
  - `context_a`: Authenticated User A (Primary author / viewer).
  - `context_b`: Authenticated User B (Second viewer / replier / liker).
  - `context_admin`: Administrator session (Governance / CRUD operations).
- **Execution Dual Modes**:
  - Direct execution via Python script: `python tests/test_phase2_closed_loop_e2e.py [--smoke | --tier 1..4 | --scenario 1..6 | --headed]`
  - Pytest runner integration: `pytest tests/test_phase2_closed_loop_e2e.py -v`

### 3.2 Directory Layout
```
Agent项目/
├── backend/
│   ├── app/
│   │   ├── models/                # ORM definitions (coin.py, notification.py, interaction.py)
│   │   └── api/v1/endpoints/      # REST API endpoints (interactions, coins, notifications, upload, admin)
│   └── main.py                    # Static /storage mount and SPA fallback
├── frontend/
│   ├── src/
│   │   ├── views/                 # PlayerView.vue, UserProfileView.vue, AdminView.vue
│   │   └── components/            # GlobalHeader.vue, NotificationSkylight.vue
├── storage/
│   ├── uploads/images/            # Persisted local image assets
│   └── test_screenshots/         # High-definition timestamped test PNG captures
├── .agents/teamwork/
│   └── test_artifacts/            # Mirrored test screenshot audits
├── tests/
│   ├── test_closed_loop_e2e_r1_r5.py    # Phase 1 master regression suite
│   └── test_phase2_closed_loop_e2e.py   # Phase 2 master closed-loop suite
├── TEST_INFRA.md                  # Test infrastructure specification (this document)
└── TEST_READY.md                  # Signal file indicating test suite readiness
```

---

## 4. Real-World Application Scenarios (Tier 4)

| # | Scenario Code & Name | Primary Features Exercised | Multi-User Contexts | Assertions & Flow Overview |
|---|----------------------|----------------------------|---------------------|----------------------------|
| 1 | **S1: Cross-User Social Interaction Loop** | F1, F2, F3, F10, F11, F12, F16, F17 | User A, User B | User A logs in and posts root comment on PlayerView. User B opens player in isolated Context B, verifies User A's comment rendered from DB, posts nested @mention reply, and likes User A's comment. User A in Context A sees GlobalHeader bell red dot `#skylight-unread-badge`, opens `#notification-skylight-drawer`, verifies reply in `#skylight-tab-replies`, clicks notification to auto-route and highlight comment floor. |
| 2 | **S2: Coin Economy & Video Tipping Closed-Loop** | F5, F6, F7, F8, F9, F20, F21 | User C | Fresh user signs in, confirms 50 initial coins balance on `#user-wallet-card`. Clicks `#btn-daily-signin`, gains +10 coins (balance 60), duplicate click rejected. Clicks `#btn-watch-ad`, gains +5 coins (balance 65). Opens PlayerView, clicks `#btn-coin-tip`, tips 2 coins, balance reduces to 63, video coin count increments. Attempts 3rd coin, intercepted by 2-coin maximum rule. Exchanges coins on `#btn-exchange-vip-7d`, verifies `#user-vip-card` expiration date extension. |
| 3 | **S3: Admin Full User CRUD Lifecycle** | F11, F13, F22 | Admin, Test User | Admin navigates to `/#/admin?tab=users`. Clicks `#btn-admin-add-user`, fills `#modal-add-user` form (username, nickname, password, coins). Filters user table, locates created user. Clicks `#btn-edit-user-<id>`, modifies nickname and grants coins, verifies table reflects edits. Clicks `#btn-delete-user-<id>`, confirms dialog, asserts record purged. |
| 4 | **S4: Local Secure Image Upload & Drama Cover Governance** | F12, F14, F23 | Admin | Admin opens drama cover management modal in AdminView. Uploads local JPEG file via `#input-upload-image`. Asserts HTTP 200 with `/storage/uploads/images/...` returned, preview renders immediately without `#000` black box. Saves metadata and confirms updated cover on drama catalog. |
| 5 | **S5: Carousel 16:9 WYSIWYG Visual Preview & Series Binding** | F24 | Admin | Admin navigates to `/#/admin?tab=carousels`, clicks "新增轮播焦点". Uses `#select-carousel-drama` series selector dropdown to pick drama. Asserts `#carousel-preview-16-9` card live renders selected drama poster, title, and tags in true 16:9 aspect ratio. Submits form and confirms carousel table entry. |
| 6 | **S6: Visual Cohesion, CSS Bug Regression & HIG Glass Tokens** | F18, F19, F21, F25 | Viewer, Admin | Inspects GlobalHeader `#user-profile-badge`: computes bounding boxes for `#user-display-name` and `#user-role-badge`, asserting no vertical text squeeze overlap and `text-decoration === 'none'` (no purple underline). Opens UserProfileView, verifies watch history items route to player with `route.query.episodeId`. Inspects AdminView root element, verifying Apple HIG dark glass backdrop-filter tokens. |

---

## 5. Standard DOM Selector Matrix

To ensure 100% deterministic automation and prevent flaky selector queries, frontend implementations adhere strictly to the following DOM ID contracts:

| Domain | Selector ID | Element Role & Interaction |
|---|---|---|
| **Social / Comments** | `#input-comment` | Main thread comment textarea |
| **Social / Comments** | `#btn-submit-comment` | Button to submit main root comment |
| **Social / Comments** | `#btn-reply-comment-<id>` | Button to reveal inline reply box for specific comment |
| **Social / Comments** | `#input-reply-comment-<id>` | Sub-thread reply input textarea |
| **Social / Comments** | `#btn-submit-reply-<id>` | Button to submit sub-thread nested reply |
| **Social / Comments** | `#btn-like-comment-<id>` | Button to toggle like on comment |
| **Social / Likes** | `#btn-video-like` | Button to toggle drama like in player |
| **Coin Economy** | `#btn-coin-tip` | Player control button opening coin tip modal |
| **Coin Economy** | `#btn-tip-1-coin` | Modal option to tip 1 coin |
| **Coin Economy** | `#btn-tip-2-coins` | Modal option to tip 2 coins |
| **Coin Economy** | `#btn-daily-signin` | User center button to claim daily 10 coins |
| **Coin Economy** | `#btn-watch-ad` | User center button to claim ad reward 5 coins |
| **Coin Economy** | `#btn-exchange-vip-7d` | User center button to exchange 100 coins for 7-day VIP |
| **Notification Skylight** | `#btn-notification-skylight` | GlobalHeader bell icon button |
| **Notification Skylight** | `#skylight-unread-badge` | Red unread count badge on bell icon |
| **Notification Skylight** | `#notification-skylight-drawer` | Frosted glass notification drawer root container |
| **Notification Skylight** | `#skylight-tab-announcements` | Tab for System Announcements |
| **Notification Skylight** | `#skylight-tab-replies` | Tab for Comment Replies |
| **Notification Skylight** | `#skylight-tab-likes` | Tab for Received Likes |
| **Notification Skylight** | `#btn-skylight-mark-all-read` | Button to mark all notifications read |
| **Admin Governance** | `#btn-admin-add-user` | Toolbar button to open Add User modal |
| **Admin Governance** | `#modal-add-user` | Dialog container for user creation |
| **Admin Governance** | `#btn-edit-user-<id>` | Action button to open Edit User modal |
| **Admin Governance** | `#btn-delete-user-<id>` | Action button to delete user |
| **Asset Ingestion** | `#input-upload-image` | File input for JPEG/PNG/WEBP upload (<=10MB) |
| **Carousel Governance** | `#select-carousel-drama` | Autocomplete series dropdown selector |
| **Carousel Governance** | `#carousel-preview-16-9` | WYSIWYG 16:9 aspect ratio live preview card |
| **Visual Bug Fixes** | `#user-profile-badge` | Header user avatar chip container |
| **Visual Bug Fixes** | `#user-display-name` | User display nickname span |
| **Visual Bug Fixes** | `#user-role-badge` | User role badge tag |
| **Visual Bug Fixes** | `#user-wallet-card` | User center coin wallet Bento card |
| **Visual Bug Fixes** | `#user-vip-card` | User center VIP privilege Bento card |

---

## 6. Coverage Thresholds & Quality Gates

- **Tier 1 (Feature Coverage)**: ≥5 test cases/assertions per feature across all 15 core features (≥75 assertions total). Validates schema, status codes, and database state.
- **Tier 2 (Boundary & Corner Cases)**: 12 boundary tests (B1-B12) exercising limits (2 coins tipping cap, duplicate daily sign-ins, >10MB upload rejection, non-admin 403 authorization, negative values, and token expiry).
- **Tier 3 (Cross-Module Combinations)**: 8 multi-hop workflow tests (C1-C8) verifying state propagation across distinct system modules (e.g. comment -> notification -> skylight; tip -> wallet deduction -> ledger audit -> heat score boost).
- **Tier 4 (Real-World Application Scenarios)**: 6 comprehensive browser journeys (S1-S6) executed via Playwright with multi-context browser isolation, full DOM assertions, and high-definition screenshot generation.
- **Quality Gate**:
  - Process exit code must be `0`.
  - Zero unhandled exceptions or rejected promises in browser console logs.
  - All captured screenshots archived to `storage/test_screenshots/` matching `{YYYYMMDD_HHMMSS}_{SCENARIO_CODE}_{STEP_LABEL}.png` with size > 20KB.
