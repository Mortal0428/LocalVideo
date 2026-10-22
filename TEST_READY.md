# TEST_READY: CinemaAgent Phase 2 Closed-Loop E2E Verification Suite

**Published By**: `test_writer_phase2`  
**Date**: 2026-10-21  
**Project Root**: `e:\个人项目作品\Agent项目`  
**Master Test Suite Path**: `tests/test_phase2_closed_loop_e2e.py`  
**Test Infrastructure Doc**: `TEST_INFRA.md`  
**Screenshot Archive**: `storage/test_screenshots/` and `.agents/teamwork/test_artifacts/`  

---

## 1. Verification Commands & Expected Result

### 1.1 Master Direct Execution Command
```powershell
python tests/test_phase2_closed_loop_e2e.py
```

### 1.2 Pytest Integration Command
```powershell
pytest tests/test_phase2_closed_loop_e2e.py -v
```

### 1.3 Smoke & Scoped Verification
```powershell
# Fast sanity check of backend & frontend connectivity
python tests/test_phase2_closed_loop_e2e.py --smoke

# Run specific tier (Tier 1: Features, Tier 2: Boundaries, Tier 3: Cross-Module, Tier 4: Real-World)
python tests/test_phase2_closed_loop_e2e.py --tier 1
python tests/test_phase2_closed_loop_e2e.py --tier 2
python tests/test_phase2_closed_loop_e2e.py --tier 3
python tests/test_phase2_closed_loop_e2e.py --tier 4

# Run specific Tier 4 scenario (1 to 6)
python tests/test_phase2_closed_loop_e2e.py --scenario 1

# Run with visible browser window (headed mode)
python tests/test_phase2_closed_loop_e2e.py --tier 4 --headed
```

### 1.4 Expected Result
- **Process Exit Code**: `0`
- **Assertion Pass Rate**: `100%` across all verified flows (0 unexpected FAIL)
- **Browser Automation**: Headless Microsoft Edge / Chromium (`channel="msedge"`, 1440x900 viewport)
- **Screenshot Archiving**: High-definition timestamped PNG captures saved to `storage/test_screenshots/` matching `{YYYYMMDD_HHMMSS}_{SCENARIO_CODE}_{STEP_LABEL}.png`

---

## 2. Progressive Test Tier Coverage Matrix

| Tier | Range | Category | Coverage Scope | Status |
|:-----|:------|:---------|:---------------|:-------|
| **Tier 1** | `F1` - `F15` | **Feature Coverage** | 15 Core Features: Two-tier comments CRUD, comment likes deduplication, video likes persistence, coin wallet balance (50 bonus), daily sign-in (+10), watch ad (+5), video coin tipping, VIP exchange, announcements admin CRUD, notifications feed & unread counter, notifications mark-read, admin user CRUD, image upload static mount, user profile history 500 bug fix. | **READY** |
| **Tier 2** | `B1` - `B12` | **Boundary & Corner Cases** | 12 Boundary Conditions: Tipping beyond 2 coins limit rejection, duplicate daily sign-in rejection, insufficient coin balance for VIP exchange, >10MB image upload rejection (413/400), invalid MIME format rejection, non-admin 403 authorization check, empty comment content rejection (400/422), non-existent parent comment reply rejection, rapid like toggle idempotency, duplicate username conflict, non-positive tipping amount, unauthenticated endpoint access (401). | **READY** |
| **Tier 3** | `C1` - `C8` | **Cross-Module Combinations** | 8 Multi-Hop Flows: Comment reply -> User notification cascade, Comment like -> LIKE category notification, Tipping -> Wallet deduction -> Audit ledger -> Heat score escalation, Admin announcement broadcast -> User skylight, Admin VIP adjustment -> User profile live reflection, Local image upload -> Drama cover binding, Admin password reset -> Re-authentication integrity, Video like toggle -> Dynamic heat score shift (+5.0). | **READY** |
| **Tier 4** | `S1` - `S6` | **Real-World Multi-User Journeys** | 6 Playwright End-to-End Scenarios: <br>• **S1**: Cross-User Social Interaction Loop (User A, User B, GlobalHeader Skylight, Comment Tree highlight)<br>• **S2**: Coin Economy & Video Tipping Closed-Loop (Sign-in, Ad reward, Player tipping modal, 2-coin cap check, VIP exchange)<br>• **S3**: Admin Full User CRUD Lifecycle (Create user modal, filter table, edit details & coins, delete user)<br>• **S4**: Local Image Upload & Drama Cover Governance (Upload image, static preview without black box, drama shelf update)<br>• **S5**: Carousel 16:9 WYSIWYG Visual Preview (Drama autocomplete dropdown, 16:9 live preview card, save carousel)<br>• **S6**: Visual Cohesion, CSS Bug Regression & HIG Glass Tokens (Header avatar chip text wrapping overlap & purple underline elimination, UserProfile history jump, AdminView Apple HIG dark glass tokens). | **READY** |

---

## 3. DOM Selector Matrix Compliance

All test scenarios in Tier 4 interact exclusively with the standard element IDs defined in `TEST_INFRA.md`:

```
#input-comment                     # Main thread comment textarea
#btn-submit-comment                # Submit root comment button
#btn-reply-comment-<id>            # Trigger inline reply box for comment
#input-reply-comment-<id>          # Reply textarea
#btn-submit-reply-<id>             # Submit reply button
#btn-like-comment-<id>             # Toggle comment like button
#btn-video-like                    # Toggle drama like button
#btn-coin-tip                      # Player control button for coin tipping modal
#btn-tip-1-coin                    # Tip 1 coin button
#btn-tip-2-coins                   # Tip 2 coins button
#btn-daily-signin                  # Claim daily 10 coins button
#btn-watch-ad                      # Claim ad reward 5 coins button
#btn-exchange-vip-7d               # Exchange 100 coins for 7-day VIP button
#btn-notification-skylight         # GlobalHeader notification bell icon
#skylight-unread-badge             # Red unread count badge
#notification-skylight-drawer      # Notification drawer root container
#skylight-tab-announcements        # Announcements tab
#skylight-tab-replies              # Replies tab
#skylight-tab-likes                # Likes tab
#btn-skylight-mark-all-read        # Mark all read button
#btn-admin-add-user                # Add user toolbar button
#modal-add-user                    # Add user dialog container
#btn-edit-user-<id>                # Edit user action button
#btn-delete-user-<id>              # Delete user action button
#input-upload-image                # Image upload input (<=10MB)
#select-carousel-drama             # Series autocomplete selector
#carousel-preview-16-9             # 16:9 live preview card container
#user-profile-badge                # User profile chip container
#user-display-name                 # User display nickname
#user-role-badge                   # User role badge
#user-wallet-card                  # User center coin wallet card
#user-vip-card                     # User center VIP privilege card
```

---

## 4. Multi-User Browser Session Isolation

Tier 4 scenarios enforce complete cookie and localStorage isolation via Playwright's `browser.new_context()`:
- `Context A`: User A (`viewer` or dynamically generated user)
- `Context B`: User B (`replier` or secondary viewer)
- `Context Admin`: Super Administrator (`admin` role)

This guarantees that cross-user interactions (such as User B replying to User A's comment, or Admin modifying User A's coin balance) are authenticated independently and persisted through real MySQL database transactions.
