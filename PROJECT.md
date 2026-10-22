# Project: CinemaAgent Phase 2 Core Upgrades & Closed-Loop Architecture

## Architecture
CinemaAgent Phase 2 builds upon Phase 1's Apple HIG visual foundation and LLM resilience gateway, completing the transition from frontend mock states to a full-stack, production-grade social video platform. The architecture connects MySQL data models, FastAPI REST endpoints, and Vue 3 frontend components across five key pillars: real multi-user social interaction, a closed-loop coin economy, frosted-glass notification skylight, comprehensive admin governance with local asset ingestion, and visual bug eradication.

### Data Flow & Module Boundaries
1. **Social Interaction & Two-Tier Comments (R1)**:
   - `UserComment` (`backend/app/models/interaction.py`) upgraded with `root_id`, `parent_id`, and `reply_to_user_id` for two-tier comment trees.
   - `CommentLike` (`backend/app/models/interaction.py`) provides atomic deduplicated likes for comments.
   - `UserLike` (`backend/app/models/interaction.py`) persists drama likes and dynamically recalculates drama `heat_score`.
   - `PlayerView.vue` completely eliminates in-memory mock arrays, rendering two-tier tree bubbles and sub-thread indentations with `@username` mentions and inline reply bars.
   - Comment replies and likes trigger asynchronous generation of `UserNotification` entries.

2. **Coin Economy & Video Tipping (R2)**:
   - `UserCoinWallet` (`backend/app/models/coin.py`) stores balance (default 50 registration bonus) and `last_sign_in_date`.
   - `UserCoinTransaction` (`backend/app/models/coin.py`) maintains double-entry audit logs.
   - `VideoCoinTip` (`backend/app/models/coin.py`) enforces strict max 2-coin tipping limit per user per drama.
   - `Video` (`backend/app/models/video.py`) persists `coin_count` and `heat_score` formula: `view*1.0 + like*5.0 + coin*10.0 + danmaku*2.0`.
   - `User` (`backend/app/models/user.py`) tracks `vip_expire_at` for seamless 7-day (100 coins) and 30-day (200 coins) VIP card extensions.
   - `PlayerView.vue` features a frosted glass tipping modal; `UserProfileView.vue` features an Apple HIG Bento dual-card economy center.

3. **Notification Skylight & Announcements (R3)**:
   - `SystemAnnouncement` (`backend/app/models/notification.py`) supports admin publishing, tagging, and retraction.
   - `UserNotification` (`backend/app/models/notification.py`) tracks user-specific notifications categorized as `ANNOUNCEMENT`, `REPLY`, or `LIKE`.
   - `GlobalHeader.vue` mounts `#btn-notification-skylight` with unread badge and launches `NotificationSkylight.vue`.
   - `NotificationSkylight.vue` displays 3 category tabs, supports mark-single-read and mark-all-read, and routes directly to target dramas and highlighted comment floors.

4. **Admin Full CRUD & Asset Ingestion (R4)**:
   - `backend/app/api/v1/endpoints/admin.py` provides full user CRUD (`POST /admin/users`, `PUT /admin/users/{id}`, `DELETE /admin/users/{id}`).
   - `backend/app/api/v1/endpoints/upload.py` implements `/api/v1/upload/image` (JPEG/PNG/WEBP <=10MB) with static `/storage` directory mounting in `backend/main.py`.
   - `AdminView.vue` eliminates black-screen cover preview bugs, adds local drag-and-drop image uploads, drama metadata editing, and multi-poster shelf management.
   - Carousel governance provides drama autocomplete selection with a 16:9 WYSIWYG live visual preview card.

5. **Visual Cohesion & CSS Bug Eradication (R5)**:
   - Global link reset in `frontend/src/App.vue` and hardened CSS on `.user-profile-chip` in `GlobalHeader.vue` eliminate browser `a:visited` purple underline pollution and flex text-wrapping squeeze.
   - `user.py` endpoints fixed by querying `last_episode_id` and `video_id`, resolving fatal 500 crashes; `PlayerView.vue` correctly parses `route.query.episodeId` for direct episode playback.
   - `AdminView.vue` styling fully converges onto Apple HIG dark glass design tokens.

6. **Dual Track E2E Verification & Adversarial Hardening (R6)**:
   - `tests/test_phase2_closed_loop_e2e.py` exercises multi-user interactions (User A, User B, Admin) across 4 tiers.
   - 100% assertions pass and timestamped screenshot artifacts are archived to `storage/test_screenshots/`.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Two-Tier Comments DB Model | `UserComment` with `root_id`, `reply_to_user_id`, `parent_id` foreign keys | M1 | survey_backend |
| 2 | Comment Likes DB Model | `CommentLike` table with unique constraint `(user_id, comment_id)` | M1 | survey_backend |
| 3 | Two-Tier Comments APIs | `GET /episodes/{id}/comments` tree aggregation, `POST /episodes/{id}/comments`, `POST /comments/{id}/like` | M1 | survey_backend |
| 4 | Video Like Status & Persistence | `GET /episodes/{id}/like-status`, `POST /episodes/{id}/like`, updating `video.like_count` and `heat_score` | M1 | survey_backend |
| 5 | Coin Wallet & Transactions Models | `user_coin_wallets` (50 coins initial bonus), `user_coin_transactions` double-entry ledger | M1 | survey_backend |
| 6 | Video Coin Tip Model & Heat Score | `video_coin_tips` (max 2 per video per user), `Video.coin_count`, `Video.heat_score` formula | M1 | survey_backend |
| 7 | Coin Economy APIs | `GET /user/coins/wallet`, `GET /user/coins/transactions`, `POST /user/coins/sign-in` (+10), `POST /user/coins/watch-ad` (+5), `POST /user/coins/exchange-vip` | M1 | survey_backend |
| 8 | Video Tip APIs | `POST /interactions/episodes/{id}/tip`, `GET /interactions/episodes/{id}/tip-status` | M1 | survey_backend |
| 9 | System Announcements Models & APIs | `system_announcements` table, admin CRUD and retract APIs | M1 | survey_backend |
| 10 | User Notifications Models & APIs | `user_notifications` table (ANNOUNCEMENT, REPLY, LIKE), unread count API, mark read / mark all read APIs | M1 | survey_backend |
| 11 | Admin Full User CRUD APIs | `POST /admin/users` (create), `PUT /admin/users/{id}` (edit profile/coins/VIP), `DELETE /admin/users/{id}` (hard delete) | M1 | survey_backend |
| 12 | Local Secure Image Upload API & Static Mount | `POST /api/v1/upload/image` (<=10MB, JPG/PNG/WEBP), mount `/storage` directory in FastAPI | M1 | survey_backend |
| 13 | User History & Likes Bug Fixes | Fix `user.py` AttributeError on `h.episode_id` and `l.episode_id`, return complete models with coins and VIP | M1 | survey_backend |
| 14 | PlayerView Two-Tier Comments UI | Replace mock `comments.value` & `unshift` with real API, render main thread & indented sub-thread, @user tag, inline reply box | M2 | survey_frontend |
| 15 | PlayerView Real Likes Persistence | Bind like button to API, query like status on episode switch | M2 | survey_frontend |
| 16 | GlobalHeader Notification Skylight & Bell | Bell icon, unread red dot badge, mount `NotificationSkylight.vue` | M2 | survey_frontend |
| 17 | NotificationSkylight Drawer Component | 3 tabs (Announcements, Replies, Likes), mark single/all read, click to navigate to video/comment | M2 | survey_frontend |
| 18 | GlobalHeader CSS Bug Fix | Eliminate text squeeze and purple underline on `.user-profile-chip` via global link reset and strict CSS hardening | M2 | survey_frontend |
| 19 | UserProfileView Navigation & History Fix | Fix `last_episode_id` vs `episode_id` route params, enable PlayerView `route.query.episodeId` parsing | M2 | survey_frontend |
| 20 | PlayerView Coin Tip Modal | Frosted glass tipping modal (1 or 2 coins, max 2 limit check, live wallet balance, heat score boost, gold particle micro-interaction) | M3 | survey_frontend |
| 21 | UserProfileView Economy Bento Cards | Coin wallet card (balance, daily sign-in button, simulated ad button), VIP privilege card (7-day/30-day exchange buttons) | M3 | survey_frontend |
| 22 | AdminView Full User CRUD UI | Filter toolbar, create user modal, edit user & assets modal, reset password modal, delete confirm | M3 | survey_frontend |
| 23 | AdminView Drama Cover Drag-and-Drop & Multi-Poster | Fix `#000` black box, support local image upload, multi-poster shelf with "set as main cover" | M3 | survey_frontend |
| 24 | AdminView Carousel 16:9 WYSIWYG Live Preview | Drama autocomplete selector, live 16:9 preview card rendering cover, title, subtitle, badges | M3 | survey_frontend |
| 25 | AdminView Visual Cohesion | Replace flat cold grays with Apple HIG dark glass and subtle glow variables | M3 | survey_frontend |
| 26 | E2E Closed-Loop Multi-User Testing Suite | `tests/test_phase2_closed_loop_e2e.py` covering Tiers 1-4 with Playwright multi-context automation | M4 | survey_testing |
| 27 | High-Definition Test Screenshot Archiving | Capture and archive all scenario screenshots to `storage/test_screenshots/` with timestamps | M4 | survey_testing |
| 28 | Tier 5 Adversarial Coverage Hardening | White-box stress testing and boundary condition hardening | M4 | survey_testing |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Backend Foundation, Data Persistence & Core APIs | Features 1-13 (Models, migrations, comment tree APIs, likes persistence, coin economy APIs, notification APIs, admin user CRUD, image upload, user.py 500 bug fix) | none | DONE (Gate PASS: 34 tests passed) |
| 2 | M2: Frontend Social Interactions, Notifications & Visual Bug Fixes | Features 14-19 (PlayerView two-tier comment tree, real likes persistence, GlobalHeader bell & NotificationSkylight, header CSS bug fix, UserProfile history mapping & player episode jump) | M1 | DONE (Gate PASS: build + S1/S6 + adversarial pass) |
| 3 | M3: Frontend Coin Economy, User Bento & Admin Governance Overhaul | Features 20-25 (PlayerView coin tipping modal, UserProfile coin wallet & VIP exchange Bento cards, AdminView user CRUD modals, drama cover drag-and-drop upload & multi-poster shelf, carousel 16:9 WYSIWYG preview, Apple HIG dark glass styles) | M1, M2 | DONE (Gate PASS: build 0 errors, Challenger2 4/4 PASS, S2/S4/S5/S6 PASS, CLEAN audit) |
| 4 | M4: Dual Track E2E Verification & Adversarial Hardening | Features 26-28 (Playwright multi-user closed-loop suite Tiers 1-4, screenshot archiving to storage/test_screenshots/, Tier 5 adversarial hardening) | M1, M2, M3, TEST_READY | DONE (Gate PASS: 41/41 E2E tests, 18/18 Tier 5 tests, 21 screenshots archived, CLEAN audit) |

---

## Interface Contracts

### 1. Two-Tier Comments APIs (`/api/v1/interactions`)
- `GET /api/v1/interactions/episodes/{episode_id}/comments`: Returns two-tier nested comment tree:
  ```json
  {
    "code": 200,
    "data": {
      "items": [
        {
          "id": "uuid",
          "user_id": "uuid",
          "username": "string",
          "nickname": "string",
          "avatar_url": "string",
          "content": "string",
          "like_count": 0,
          "is_liked": false,
          "created_at": "ISO-8601",
          "replies": [
            {
              "id": "uuid",
              "root_id": "uuid",
              "parent_id": "uuid",
              "user_id": "uuid",
              "username": "string",
              "nickname": "string",
              "avatar_url": "string",
              "reply_to_user_id": "uuid",
              "reply_to_username": "string",
              "reply_to_nickname": "string",
              "content": "string",
              "like_count": 0,
              "is_liked": false,
              "created_at": "ISO-8601"
            }
          ],
          "reply_count": 1
        }
      ],
      "total": 1
    }
  }
  ```
- `POST /api/v1/interactions/episodes/{episode_id}/comments`:
  ```json
  {
    "content": "string",
    "root_id": "uuid (optional)",
    "parent_id": "uuid (optional)",
    "reply_to_user_id": "uuid (optional)"
  }
  ```
- `POST /api/v1/interactions/comments/{comment_id}/like`: Toggle comment like with deduplication.
- `GET /api/v1/interactions/episodes/{episode_id}/like-status`: Returns `{"is_liked": bool, "like_count": int}`.
- `POST /api/v1/interactions/episodes/{episode_id}/like`: Toggle drama like with deduplication.

### 2. Coin Economy APIs (`/api/v1/user/coins` & `/api/v1/interactions`)
- `GET /api/v1/user/coins/wallet`: Returns `{"balance": int, "total_earned": int, "total_spent": int, "has_signed_today": bool, "ad_watch_count_today": int}`.
- `GET /api/v1/user/coins/transactions`: Paginated transaction history.
- `POST /api/v1/user/coins/sign-in`: Claim daily sign-in reward (+10 coins).
- `POST /api/v1/user/coins/watch-ad`: Reward for simulated ad watch (+5 coins).
- `POST /api/v1/user/coins/exchange-vip`: `{"days": 7 | 30, "cost": 100 | 200}` -> extends `vip_expire_at`.
- `POST /api/v1/interactions/episodes/{episode_id}/tip`: `{"coin_amount": 1 | 2}` -> deducts wallet, increments `video_coin_tips`, updates `video.coin_count` and `heat_score`. Returns 400 if user exceeds 2 coins for this drama.
- `GET /api/v1/interactions/episodes/{episode_id}/tip-status`: Returns `{"tipped_count": int, "max_allowed": 2, "video_coin_count": int, "heat_score": float}`.

### 3. Notification & Announcement APIs (`/api/v1/notifications` & `/api/v1/admin/announcements`)
- `GET /api/v1/notifications`: List notifications with filter `?category=ANNOUNCEMENT|REPLY|LIKE`.
- `GET /api/v1/notifications/unread-count`: Returns `{"total": int, "announcements": int, "replies": int, "likes": int}`.
- `POST /api/v1/notifications/{id}/read`: Mark single notification read.
- `POST /api/v1/notifications/read-all`: Mark all notifications read.
- `GET /api/v1/admin/announcements`: Admin list announcements.
- `POST /api/v1/admin/announcements`: Publish announcement (`title`, `content`, `tag`).
- `PUT /api/v1/admin/announcements/{id}`: Edit announcement.
- `POST /api/v1/admin/announcements/{id}/retract`: Retract announcement.

### 4. Admin CRUD & Asset Upload APIs
- `POST /api/v1/upload/image`: Multipart form-data image upload (JPG/PNG/WEBP <=10MB). Returns `{"url": "/storage/uploads/images/{uuid}.{ext}"}`.
- `POST /api/v1/admin/users`: Create user (`username`, `password`, `nickname`, `role`, `coins`, `vip_days`).
- `PUT /api/v1/admin/users/{id}`: Edit user (`nickname`, `password (optional)`, `role`, `status`, `coins_adjustment`, `vip_expire_at`).
- `DELETE /api/v1/admin/users/{id}`: Hard delete user and cascade dependencies.
- `PUT /api/v1/admin/dramas/{id}`: Edit drama metadata (`title`, `category`, `summary`, `cover_url`, `status`).
- `GET /api/v1/admin/dramas/options`: Lightweight list for carousel series dropdown (`id`, `title`, `cover_url`, `extra_images`).

---

## Code Layout
- **Backend**:
  - `backend/app/models/coin.py` — `UserCoinWallet`, `UserCoinTransaction`, `VideoCoinTip` ORM models
  - `backend/app/models/notification.py` — `SystemAnnouncement`, `UserNotification` ORM models
  - `backend/app/models/interaction.py` — `UserComment` (two-tier), `CommentLike`, `UserLike` ORM models
  - `backend/app/models/video.py` — `Video` (`coin_count`, `heat_score`)
  - `backend/app/models/user.py` — `User` (`vip_expire_at`)
  - `backend/app/core/database.py` — `init_db()` defensive column auto-patching
  - `backend/app/api/v1/endpoints/interactions.py` — Comment tree, comment likes, drama tip & like endpoints
  - `backend/app/api/v1/endpoints/coins.py` — Coin wallet, sign-in, ad, VIP exchange endpoints
  - `backend/app/api/v1/endpoints/notifications.py` — Notification feed & unread counter endpoints
  - `backend/app/api/v1/endpoints/upload.py` — Local image upload endpoint (`/api/v1/upload/image`)
  - `backend/app/api/v1/endpoints/admin.py` — Admin user CRUD, announcements CRUD, drama options endpoints
  - `backend/app/api/v1/endpoints/user.py` — User profile, watch history, and like history fixes
  - `backend/main.py` — Static `/storage` directory mounting
- **Frontend**:
  - `frontend/src/views/PlayerView.vue` — Two-tier comments, real likes, coin tipping modal, route episode jump
  - `frontend/src/views/UserProfileView.vue` — Economy Bento cards (coin wallet, VIP cards), history link fix
  - `frontend/src/components/GlobalHeader.vue` — Notification bell trigger, badge, hardened profile chip CSS
  - `frontend/src/components/NotificationSkylight.vue` — Frosted glass notification drawer (3 tabs, mark read, jump)
  - `frontend/src/views/AdminView.vue` — User CRUD modals, drag-drop cover upload, carousel 16:9 WYSIWYG preview, Apple HIG styling
  - `frontend/src/api/video.ts`, `frontend/src/api/user.ts`, `frontend/src/api/admin.ts` — Updated API clients
  - `frontend/src/App.vue` — Global link reset
- **Tests & Artifacts**:
  - `tests/test_phase2_closed_loop_e2e.py` — Master Phase 2 E2E test suite (Tiers 1-4, Multi-User Playwright)
  - `storage/test_screenshots/` — High-definition execution screenshot artifacts
