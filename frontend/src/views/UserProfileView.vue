<template>
  <div class="user-space-page" id="user-space-root">
    <!-- Top Global Apple HIG Header -->
    <GlobalHeader />

    <!-- Ambient Backdrop Glow -->
    <div class="space-ambient-glow glow-top"></div>
    <div class="space-ambient-glow glow-bottom"></div>

    <div class="space-container">
      <!-- 1. Header Hero Bento Card -->
      <header class="space-hero-card" id="user-hero-card">
        <div class="hero-avatar-wrap clickable" @click="triggerHeroAvatarPick" title="点击直接更换头像">
          <img :src="profile?.avatar_url || defaultAvatar" class="hero-avatar" />
          <div class="avatar-hover-overlay">
            <svg class="camera-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
              <circle cx="12" cy="13" r="4"></circle>
            </svg>
            <span class="overlay-text">{{ isUploadingHeroAvatar ? '上传中...' : '更换头像' }}</span>
          </div>
          <span class="role-badge" :class="'role-' + (profile?.role?.toLowerCase() || 'user')">
            {{ getRoleBadgeText(profile?.role) }}
          </span>
          <input
            type="file"
            ref="heroAvatarFileInput"
            accept="image/png,image/jpeg,image/webp"
            style="display: none;"
            @change="handleHeroAvatarSelected"
          />
        </div>

        <div class="hero-info">
          <div class="hero-name-row">
            <h1 class="hero-nickname" id="profile-nickname">{{ profile?.nickname || profile?.username || '剧迷朋友' }}</h1>
            <span class="hero-username">@{{ profile?.username }}</span>
            <span class="status-pill status-active">● 状态正常</span>
          </div>
          <p class="hero-bio">{{ profile?.creator_bio || '这个人很低调，还没有写个人简介~' }}</p>

          <div class="hero-stats-row">
            <div class="stat-item" id="stat-history-tab" @click="activeTab = 'history'" style="cursor: pointer;">
              <span class="stat-val" id="stat-history-count">{{ profile?.stats?.history_count || historyList.length || 0 }}</span>
              <span class="stat-lbl">观看历史</span>
            </div>
            <div class="stat-sep">/</div>
            <div class="stat-item" id="stat-likes-tab" @click="activeTab = 'likes'" style="cursor: pointer;">
              <span class="stat-val" id="stat-likes-count">{{ profile?.stats?.likes_count || likesList.length || 0 }}</span>
              <span class="stat-lbl">点赞记录</span>
            </div>
            <div class="stat-sep">/</div>
            <div class="stat-item" id="stat-favorites-tab" @click="activeTab = 'favorites'" style="cursor: pointer;">
              <span class="stat-val" id="stat-favorites-count">{{ totalFavoritesCount }}</span>
              <span class="stat-lbl">多级收藏</span>
            </div>
            <div class="stat-sep">/</div>
            <div class="stat-item" id="stat-followings-btn" @click="openFollowModal('followings')" style="cursor: pointer;">
              <span class="stat-val" id="stat-following-count">{{ profile?.stats?.following_count || followingsList.length || 0 }}</span>
              <span class="stat-lbl">我的关注</span>
            </div>
            <div class="stat-sep">/</div>
            <div class="stat-item" id="stat-followers-btn" @click="openFollowModal('followers')" style="cursor: pointer;">
              <span class="stat-val" id="stat-followers-count">{{ profile?.stats?.followers_count || followersList.length || 0 }}</span>
              <span class="stat-lbl">我的粉丝</span>
            </div>
            <div class="stat-sep">/</div>
            <div class="stat-item">
              <span class="stat-val">{{ profile?.stats?.creator_videos_count || 0 }}</span>
              <span class="stat-lbl">发布短剧</span>
            </div>
          </div>
        </div>

        <div class="hero-actions">
          <button class="action-btn-secondary" @click="activeTab = 'profile'" title="编辑个人资料">
            <span>编辑资料</span>
          </button>
        </div>
      </header>

      <!-- 2. Economy Bento Grid (金币经济与VIP特权中心 Feature 21) -->
      <section class="economy-bento-grid" id="economy-bento-section">
        <!-- Card 1: Coin Wallet Card -->
        <div class="economy-card glass-panel" id="user-wallet-card">
          <div class="card-header-row">
            <div class="header-icon-title">
              <div class="card-coin-badge"><GoldCoinIcon :size="28" /></div>
              <div>
                <h3 class="card-heading">金币钱包与任务中心</h3>
                <span class="card-subheading">新用户默认赠送 50 金币，支持每日签到与观看激励广告</span>
              </div>
            </div>
            <div class="wallet-badge-pill">
              <span class="balance-num">{{ walletData.balance }}</span>
              <span class="balance-unit">金币</span>
            </div>
          </div>

          <div class="wallet-stats-strip">
            <div class="wallet-stat-item">
              <span class="wstat-label">累计获取</span>
              <span class="wstat-value">+{{ walletData.total_earned }}</span>
            </div>
            <div class="wallet-stat-sep"></div>
            <div class="wallet-stat-item">
              <span class="wstat-label">累计消耗</span>
              <span class="wstat-value">-{{ walletData.total_spent }}</span>
            </div>
            <div class="wallet-stat-sep"></div>
            <div class="wallet-stat-item">
              <span class="wstat-label">今日签到</span>
              <span class="wstat-value" :class="{ 'text-success': walletData.has_signed_today }">
                {{ walletData.has_signed_today ? '已完成' : '待领取' }}
              </span>
            </div>
          </div>

          <div class="economy-actions-row">
            <button
              class="apple-bento-btn btn-signin"
              id="btn-daily-signin"
              :disabled="walletData.has_signed_today || isSigningIn"
              @click="handleDailySignIn"
            >
              <span v-if="walletData.has_signed_today">今日已签到 ✓</span>
              <span v-else-if="isSigningIn">签到中...</span>
              <span v-else>每日签到领 10 币</span>
            </button>

            <button
              class="apple-bento-btn btn-ad"
              id="btn-watch-ad"
              :disabled="isWatchingAd"
              @click="handleWatchAd"
            >
              <span v-if="isWatchingAd">{{ adCountdownText }}</span>
              <span v-else>看广告得 5 币</span>
            </button>
          </div>
        </div>

        <!-- Card 2: VIP Privilege Card -->
        <div class="economy-card glass-panel" id="user-vip-card" :class="{ 'is-vip-active': isUserVip }">
          <div class="card-header-row">
            <div class="header-icon-title">
              <div class="card-crown-badge">
            <svg class="crown-svg" width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path d="M5 16L3 5L8.5 10L12 4L15.5 10L21 5L19 16H5Z" fill="url(#crownGrad)" stroke="#B45309" stroke-width="1.2" stroke-linejoin="round"/>
              <path d="M5 19H19V17H5V19Z" fill="#F59E0B" stroke="#92400E" stroke-width="1"/>
              <circle cx="12" cy="4" r="1.5" fill="#FEF3C7"/>
              <circle cx="3" cy="5" r="1.2" fill="#FEF3C7"/>
              <circle cx="21" cy="5" r="1.2" fill="#FEF3C7"/>
              <defs>
                <linearGradient id="crownGrad" x1="3" y1="4" x2="21" y2="19" gradientUnits="userSpaceOnUse">
                  <stop stop-color="#FDE68A"/>
                  <stop offset="0.5" stop-color="#F59E0B"/>
                  <stop offset="1" stop-color="#D97706"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
              <div>
                <h3 class="card-heading">VIP 会员尊享特权</h3>
                <span class="card-subheading">原画超清播放、多级收藏夹扩容、独家免广跳集权益</span>
              </div>
            </div>
            <div class="vip-status-pill" :class="{ active: isUserVip }">
              {{ isUserVip ? 'VIP 会员生效中' : '普通用户' }}
            </div>
          </div>

          <div class="vip-expiry-box">
            <span class="vip-expiry-label">VIP 到期时间：</span>
            <span class="vip-expiry-val">{{ vipExpiryDisplay }}</span>
          </div>

          <div class="vip-tiers-grid">
            <div class="vip-tier-card">
              <div class="tier-info">
                <span class="tier-name">7天 VIP体验卡</span>
                <span class="tier-cost">100 金币</span>
              </div>
              <button
                class="apple-bento-btn mini btn-exchange"
                id="btn-exchange-vip-7d"
                :disabled="walletData.balance < 100 || isExchangingVip"
                @click="handleExchangeVip(7, 100)"
              >
                {{ walletData.balance < 100 ? '金币不足' : '立即兑换' }}
              </button>
            </div>

            <div class="vip-tier-card">
              <div class="tier-info">
                <span class="tier-name">30天 VIP月度畅享卡</span>
                <span class="tier-cost">200 金币</span>
              </div>
              <button
                class="apple-bento-btn mini btn-exchange"
                id="btn-exchange-vip-30d"
                :disabled="walletData.balance < 200 || isExchangingVip"
                @click="handleExchangeVip(30, 200)"
              >
                {{ walletData.balance < 200 ? '金币不足' : '立即兑换' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Card 3: Redemption Voucher Card (金币兑换码 & 会员兑换码核销) -->
        <div class="economy-card glass-panel redemption-bento-card" id="user-redemption-card" style="grid-column: 1 / -1;">
          <div class="redemption-card-inner">
            <div class="header-icon-title">
              <div class="card-voucher-badge">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                  <rect x="2" y="5" width="20" height="14" rx="3" stroke="#0071e3" stroke-width="1.8" fill="rgba(0, 113, 227, 0.12)"/>
                  <path d="M9 5V19" stroke="#0071e3" stroke-width="1.5" stroke-dasharray="2.5 2.5"/>
                  <path d="M13 10H18M13 14H16" stroke="#0071e3" stroke-width="1.8" stroke-linecap="round"/>
                </svg>
              </div>
              <div>
                <h3 class="card-heading">卡密与权益兑换中心</h3>
                <span class="card-subheading">支持核销官方发放的金币充值兑换码 (COIN-XXXX) 与 VIP 尊享会员兑换码 (VIP-XXXX)，一码一用</span>
              </div>
            </div>

            <div class="redemption-input-group">
              <input
                v-model="redeemCodeInput"
                type="text"
                class="redemption-code-input"
                id="input-redeem-code"
                placeholder="请输入金币兑换码或会员兑换码 (如 COIN-XXXX-XXXX-XXXX)"
                @keyup.enter="handleRedeemCode"
              />
              <button
                type="button"
                class="apple-bento-btn btn-redeem-submit"
                id="btn-submit-redeem"
                :disabled="isRedeemingCode || !redeemCodeInput.trim()"
                @click="handleRedeemCode"
              >
                {{ isRedeemingCode ? '正在核销...' : '立即核销兑换' }}
              </button>
            </div>
          </div>

          <transition name="fade">
            <div
              v-if="redeemFeedback.message"
              id="redeem-feedback-msg"
              class="redeem-feedback-banner"
              :class="redeemFeedback.type === 'success' ? 'is-success' : 'is-error'"
            >
              <span>{{ redeemFeedback.message }}</span>
            </div>
          </transition>
        </div>
      </section>

      <!-- 3. Dual Qualification Center (创作者与审核员双轨入驻与直通) -->
      <section class="creator-qualification-grid" id="dual-qualification-box">
        <!-- Card 1: Creator Qualification -->
        <div class="qual-card glass-panel" :class="{ 'is-active': profile?.role === 'ADMIN' || profile?.role === 'CREATOR' || profile?.is_creator }">
          <div class="qual-content">
            <div class="qual-icon-box creator-box">
          <svg class="clapper-svg" width="30" height="30" viewBox="0 0 24 24" fill="none">
            <rect x="2" y="7" width="20" height="14" rx="2.5" fill="#3B82F6" stroke="#1D4ED8" stroke-width="1.2"/>
            <path d="M2 11H22" stroke="#1E40AF" stroke-width="1.2"/>
            <path d="M2.5 7L5 3H8.5L6 7" fill="#60A5FA"/>
            <path d="M9.5 7L12 3H15.5L13 7" fill="#60A5FA"/>
            <path d="M16.5 7L19 3H21.5L19 7" fill="#60A5FA"/>
          </svg>
        </div>
            <div class="qual-text">
              <template v-if="profile?.role === 'ADMIN' || profile?.role === 'CREATOR' || profile?.is_creator">
                <h3>您已具备平台创作者权限！</h3>
                <p>享有夸克网盘短剧映射、剧集批量管理、专属播放数据看板与审核流直推特权。</p>
              </template>
              <template v-else-if="profile?.creator_application_status === 'PENDING'">
                <h3>创作者资质申请审批中...</h3>
                <p>已提交创作者入驻申请，管理员正在管理大厅审批，请稍后关注状态更新。</p>
              </template>
              <template v-else>
                <h3>申请成为平台认证创作者</h3>
                <p>开启属于您的短剧创作生态！一键挂载您的夸克网盘，自动提取多集短剧并呈现在大厅。</p>
              </template>
            </div>
            <div class="qual-action-wrap">
              <router-link v-if="profile?.role === 'ADMIN' || profile?.role === 'CREATOR' || profile?.is_creator" to="/creator" class="qual-action-btn btn-enter-creator" id="btn-enter-studio">
                进入创作者工作室 →
              </router-link>
              <button v-else-if="profile?.creator_application_status === 'PENDING'" class="qual-action-btn btn-pending" disabled>
                ⏳ 审批中
              </button>
              <button v-else class="qual-action-btn btn-apply-creator" id="btn-apply-creator" @click="openApplyModal">
                申请创作者
              </button>
            </div>
          </div>
        </div>

        <!-- Card 2: Reviewer Qualification -->
        <div class="qual-card glass-panel" :class="{ 'is-active': profile?.role === 'ADMIN' || profile?.role === 'REVIEWER' || profile?.is_reviewer }">
          <div class="qual-content">
            <div class="qual-icon-box reviewer-box">
          <svg class="shield-svg" width="30" height="30" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L4 5V11C4 16.5 7.5 20.5 12 22C16.5 20.5 20 16.5 20 11V5L12 2Z" fill="url(#shieldGrad)" stroke="#047857" stroke-width="1.2"/>
            <path d="M9 11.5L11 13.5L15 9.5" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <defs>
              <linearGradient id="shieldGrad" x1="4" y1="2" x2="20" y2="22" gradientUnits="userSpaceOnUse">
                <stop stop-color="#34D399"/>
                <stop offset="1" stop-color="#059669"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
            <div class="qual-text">
              <template v-if="profile?.role === 'ADMIN' || profile?.role === 'REVIEWER' || profile?.is_reviewer">
                <h3>您已认证为内容审核员/管理员！</h3>
                <p>具备机审人审中台权限，巡检平台短剧、违规弹幕与恶意评论合规处理。</p>
              </template>
              <template v-else-if="profile?.reviewer_application_status === 'PENDING'">
                <h3>审核员资质申请审批中...</h3>
                <p>已提交审核员申请，管理员正在管理大厅审批，核准后将解锁审核中台。</p>
              </template>
              <template v-else>
                <h3>申请成为平台内容审核员</h3>
                <p>参与社区内容合规生态共建，获得审核中台操作权限与专属审核员认证徽章。</p>
              </template>
            </div>
            <div class="qual-action-wrap">
              <router-link v-if="profile?.role === 'ADMIN' || profile?.role === 'REVIEWER' || profile?.is_reviewer" to="/admin?tab=contents" class="qual-action-btn btn-enter-reviewer" id="btn-enter-reviewer-space">
                进入审核中台 →
              </router-link>
              <button v-else-if="profile?.reviewer_application_status === 'PENDING'" class="qual-action-btn btn-pending" disabled>
                ⏳ 审批中
              </button>
              <button v-else class="qual-action-btn btn-apply-reviewer" id="btn-apply-reviewer" @click="openReviewerModal">
                申请审核员
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- 3. Main Content Tabs (Watch History / Likes / Profile Settings) -->
      <section class="space-tabs-section">
        <div class="space-tab-bar" id="space-tab-bar">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'history' }"
            id="tab-btn-space-history"
            @click="activeTab = 'history'"
          >
            <span>⏱️ 观看历史 ({{ historyList.length }})</span>
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'likes' }"
            id="tab-btn-space-likes"
            @click="activeTab = 'likes'"
          >
            <span class="tab-label-flex"><el-icon><Check /></el-icon> 点赞记录 ({{ likesList.length }})</span>
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'favorites' }"
            id="tab-btn-space-favorites"
            @click="activeTab = 'favorites'"
          >
            <span class="tab-label-flex"><el-icon><Star /></el-icon> 多级收藏夹 ({{ totalFavoritesCount }})</span>
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'comments' }"
            id="tab-btn-space-comments"
            @click="activeTab = 'comments'"
          >
            <span class="tab-label-flex"><el-icon><ChatDotRound /></el-icon> 我的评论 ({{ commentsList.length }})</span>
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'profile' }"
            id="tab-btn-space-profile"
            @click="activeTab = 'profile'"
          >
            <span>⚙️ 资料设置</span>
          </button>
        </div>

        <!-- Tab 1: Watch History with Breakpoint Continue-Play -->
        <div v-if="activeTab === 'history'" class="tab-pane" id="pane-history">
          <div v-if="historyList.length === 0" class="empty-state-box">
            <div class="empty-icon-wrap"><el-icon :size="40"><VideoCamera /></el-icon></div>
            <div class="empty-title">暂无观看历史记录</div>
            <p class="empty-sub">快去大厅探索精彩短剧吧，支持毫秒级断点记忆播放！</p>
            <router-link to="/" class="action-btn-primary">前往视听大厅</router-link>
          </div>
          <div v-else class="history-grid" id="history-items-grid">
            <div
              v-for="item in historyList"
              :key="item.history_id"
              class="history-card"
            >
              <div class="history-cover-wrap">
                <img :src="item.cover_url || defaultCover" class="history-cover" />
                <div class="progress-bar-wrap">
                  <div class="progress-bar-fill" :style="{ width: item.progress_pct + '%' }"></div>
                </div>
                <span class="ep-badge">第 {{ item.episode_num }} 集</span>
              </div>
              <div class="history-details">
                <h4 class="history-drama-title">{{ item.drama_title }}</h4>
                <div class="history-ep-title">{{ item.episode_title }}</div>
                <div class="history-progress-text">
                  已观看到 {{ formatDuration(item.progress_seconds) }} / {{ formatDuration(item.duration_seconds) }} ({{ item.progress_pct }}%)
                </div>
                <div class="history-footer">
                  <span class="history-time">{{ item.updated_at }}</span>
                  <router-link
                    :to="'/play?videoId=' + item.video_id + '&episodeId=' + (item.episode_id || item.last_episode_id) + '&time=' + (item.progress_seconds || 0)"
                    class="continue-play-btn"
                  >
                    ▶ 继续观看
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 2: Liked Videos -->
        <div v-else-if="activeTab === 'likes'" class="tab-pane" id="pane-likes">
          <div v-if="likesList.length === 0" class="empty-state-box">
            <div class="empty-icon-wrap"><el-icon :size="40"><Check /></el-icon></div>
            <div class="empty-title">暂无点赞或收藏剧集</div>
            <p class="empty-sub">在播放器为喜欢的短剧点赞，这里将为您长久珍藏！</p>
            <router-link to="/" class="action-btn-primary">去大厅逛逛</router-link>
          </div>
          <div v-else class="likes-grid">
            <div
              v-for="like in likesList"
              :key="like.like_id"
              class="like-card"
            >
              <img :src="like.cover_url || defaultCover" class="like-cover" />
              <div class="like-info">
                <h4>{{ like.drama_title }}</h4>
                <p>{{ like.episode_title }}</p>
                <div class="like-footer">
                  <span class="like-time">{{ like.created_at }}</span>
                  <router-link :to="'/play?videoId=' + like.video_id" class="play-link">
                    立即播放 →
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: Multi-level Named Favorites -->
        <div v-else-if="activeTab === 'favorites'" class="tab-pane" id="pane-favorites">
          <!-- Folder Management Toolbar -->
          <div class="favorites-toolbar">
            <div class="toolbar-left">
              <h3 class="pane-section-title">我的剧单收藏夹</h3>
              <span class="pane-section-sub">按剧单分类管理心仪短剧，支持公开分享与私密珍藏</span>
            </div>
            <div class="toolbar-right">
              <button class="action-btn-primary mini" id="btn-open-create-folder" @click="openCreateFolderModal">
                <span>+ 新建收藏夹</span>
              </button>
            </div>
          </div>

          <!-- Folders Capsule Navigation Bar -->
          <div class="folders-pill-nav" id="folders-pill-nav">
            <button
              v-for="folder in foldersList"
              :key="folder.id"
              class="folder-pill-btn"
              :class="{ active: currentFolderId === folder.id }"
              :id="'pill-folder-' + folder.id"
              @click="selectFolder(folder.id)"
            >
              <span class="folder-pill-name">{{ folder.name }}</span>
              <span v-if="folder.is_default" class="folder-pill-badge default">默认</span>
              <span class="folder-pill-badge" :class="folder.is_public ? 'public' : 'private'">
                {{ folder.is_public ? '公开' : '私密' }}
              </span>
              <span class="folder-pill-count">{{ folder.item_count }}</span>
            </button>
          </div>

          <!-- Active Folder Meta & Controls -->
          <div v-if="currentFolder" class="active-folder-header">
            <div class="folder-meta-text">
              <div class="folder-title-line">
                <h4 class="current-folder-title" id="current-folder-title">{{ currentFolder.name }}</h4>
                <span v-if="currentFolder.is_default" class="tag-default-capsule">系统默认</span>
                <span class="tag-privacy-capsule" :class="currentFolder.is_public ? 'public' : 'private'">
                  {{ currentFolder.is_public ? '公开剧单' : '私密珍藏' }}
                </span>
                <span class="folder-updated-date" v-if="currentFolder.updated_at">更新于 {{ formatDate(currentFolder.updated_at) }}</span>
              </div>
              <p class="current-folder-desc">{{ currentFolder.description || '暂无简介' }}</p>
            </div>
            <div class="folder-header-actions" v-if="!currentFolder.is_default">
              <button class="btn-folder-action edit" id="btn-edit-folder" @click="openEditFolderModal(currentFolder)">
                编辑
              </button>
              <button class="btn-folder-action delete" id="btn-delete-folder" @click="handleDeleteFolder(currentFolder.id)">
                删除
              </button>
            </div>
          </div>

          <!-- Folder Items Grid -->
          <div v-if="folderItemsLoading" class="loading-state-box">
            <span>正在加载收藏短剧...</span>
          </div>
          <div v-else-if="folderItems.length === 0" class="empty-state-box" id="empty-folder-items">
            <div class="empty-icon-wrap"><el-icon :size="40"><Folder /></el-icon></div>
            <div class="empty-title">当前收藏夹为空</div>
            <p class="empty-sub">前往播放器，点击短剧下方的 收藏即可将短剧归档至此夹！</p>
            <router-link to="/" class="action-btn-primary">探索精彩短剧</router-link>
          </div>
          <div v-else class="favorites-drama-grid" id="favorites-items-grid">
            <div
              v-for="item in folderItems"
              :key="item.id"
              class="fav-drama-card"
              :id="'fav-item-' + item.video_id"
            >
              <div class="fav-cover-wrap">
                <img :src="item.video?.cover_url || defaultCover" class="fav-cover-img" />
                <span class="fav-episodes-badge">全 {{ item.video?.total_episodes || 1 }} 集</span>
                <span class="fav-category-badge">{{ item.video?.category || '短剧' }}</span>
              </div>
              <div class="fav-card-body">
                <h4 class="fav-drama-title">{{ item.video?.title }}</h4>
                <p class="fav-drama-desc">{{ item.video?.summary || '精选优质短剧' }}</p>
                <div class="fav-card-meta-line">
                  <span class="fav-author">创作者: {{ item.video?.author || '官方精选' }}</span>
                </div>
                <div class="fav-card-actions">
                  <button
                    class="btn-remove-fav"
                    id="btn-remove-favorite"
                    @click.stop="handleRemoveFromFolder(item.video_id)"
                    title="从当前收藏夹移出"
                  >
                    移出
                  </button>
                  <router-link
                    :to="'/video/' + item.video_id"
                    class="btn-play-direct"
                    id="btn-direct-play"
                    title="立即打开播放器播放"
                  >
                    ▶ 立即播放
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 4: My Comments -->
        <div v-else-if="activeTab === 'comments'" class="tab-pane" id="pane-comments">
          <div v-if="commentsLoading" class="loading-state-box">
            <span>正在加载我的评论历史...</span>
          </div>
          <div v-else-if="commentsList.length === 0" class="empty-state-box" id="empty-comments-box">
            <div class="empty-icon-wrap"><el-icon :size="40"><ChatDotRound /></el-icon></div>
            <div class="empty-title">暂无发表过的评论记录</div>
            <p class="empty-sub">在播放器发表精彩观点或回复他人，即可在此集中查看与管理！</p>
            <router-link to="/" class="action-btn-primary">前往视听大厅</router-link>
          </div>
          <div v-else class="user-comments-grid" id="user-comments-items-grid">
            <div
              v-for="item in commentsList"
              :key="item.comment_id"
              class="user-comment-card glass-panel"
              :id="'user-comment-' + item.comment_id"
            >
              <div class="comment-card-header">
                <div class="comment-drama-badge">
                  <span class="badge-drama-title">《{{ item.drama_title }}》</span>
                  <span v-if="item.is_reply" class="badge-reply-target">回复 @{{ item.reply_to_user_name || '剧迷' }}</span>
                </div>
                <span class="comment-pub-date">{{ item.created_at }}</span>
              </div>

              <div class="comment-card-body">
                <p class="comment-content-text">{{ item.content }}</p>
              </div>

              <div class="comment-card-footer">
                <div class="comment-stats-tag">
                  <span>点赞数: {{ item.like_count }}</span>
                </div>
                <div class="comment-action-btns">
                  <button
                    class="btn-delete-comment"
                    :id="'btn-del-comment-' + item.comment_id"
                    @click="handleDeleteComment(item.comment_id)"
                  >
                    删除
                  </button>
                  <router-link
                    :to="'/play?videoId=' + item.video_id + (item.episode_id ? '&episodeId=' + item.episode_id : '')"
                    class="btn-goto-drama"
                  >
                    前往短剧播放 →
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 3: Profile Settings -->
        <div v-else class="tab-pane" id="pane-profile">
          <div class="profile-edit-box">
            <h3 class="edit-title">编辑个人资料</h3>
            <form @submit.prevent="saveProfile" class="profile-form">
              <div class="form-group">
                <label class="form-label">用户名 (不可修改)</label>
                <input type="text" class="form-input readonly" :value="profile?.username" readonly />
              </div>

              <div class="form-group">
                <label class="form-label">用户昵称</label>
                <input
                  v-model="editForm.nickname"
                  type="text"
                  class="form-input"
                  id="input-edit-nickname"
                  placeholder="请输入您的昵称"
                  required
                />
              </div>

              <div class="form-group">
                <label class="form-label">个人简介</label>
                <textarea
                  v-model="editForm.bio"
                  class="form-textarea"
                  id="input-edit-bio"
                  rows="3"
                  placeholder="介绍一下自己，或者分享喜欢的短剧类型..."
                ></textarea>
              </div>

              <div class="form-group">
                <label class="form-label">用户头像 (支持本地上传自定义头像)</label>
                <div class="avatar-custom-upload-box">
                  <div class="current-avatar-preview">
                    <img :src="editForm.avatar_url || defaultAvatar" class="avatar-preview-img" />
                    <div class="upload-trigger-col">
                      <input
                        type="file"
                        ref="avatarFileInput"
                        accept="image/png,image/jpeg,image/webp"
                        style="display: none;"
                        @change="handleAvatarFileSelected"
                      />
                      <button
                        type="button"
                        class="apple-bento-btn mini btn-upload-avatar"
                        id="btn-upload-local-avatar"
                        :disabled="isUploadingAvatar"
                        @click="triggerAvatarFilePick"
                      >
                        <span>{{ isUploadingAvatar ? '正在上传图片...' : '上传本地自定义头像' }}</span>
                      </button>
                      <span class="upload-tip-text">支持 JPG/PNG/WEBP，限制 10MB。上传后点击保存资料立即全局生效。</span>
                    </div>
                  </div>
                </div>

                <div class="avatar-presets-label">或者选择经典预设：</div>
                <div class="avatar-presets-row">
                  <img
                    v-for="seed in avatarSeeds"
                    :key="seed"
                    :src="'https://api.dicebear.com/7.x/bottts/svg?seed=' + seed"
                    class="avatar-preset-item"
                    :class="{ selected: editForm.avatar_url.includes(seed) }"
                    @click="editForm.avatar_url = 'https://api.dicebear.com/7.x/bottts/svg?seed=' + seed"
                  />
                </div>
              </div>

              <div class="edit-actions-row">
                <button type="submit" class="auth-primary-btn" id="btn-save-profile" :disabled="isSaving">
                  {{ isSaving ? '保存中...' : '保存资料修改' }}
                </button>
                <span v-if="saveNotice" class="save-notice">{{ saveNotice }}</span>
              </div>
            </form>
          </div>
        </div>
      </section>
    </div>

    <!-- Creator Apply Modal -->
    <transition name="fade">
      <div v-if="showApplyModal" class="modal-overlay" id="creator-apply-modal">
        <div class="modal-card">
          <div class="modal-header">
            <h3>申请成为认证创作者</h3>
            <button class="modal-close-btn" @click="showApplyModal = false">×</button>
          </div>
          <div class="modal-body">
            <p class="modal-desc">
              成为认证创作者后，您将拥有网盘专属目录挂载、短剧批量映射与发布特权。
            </p>
            <div class="form-group">
              <label class="form-label">创作者名称 / 厂牌名</label>
              <input
                v-model="applyForm.creator_name"
                type="text"
                class="form-input"
                id="input-apply-creator-name"
                placeholder="例如：星芒微影工作室"
                required
              />
            </div>
            <div class="form-group">
              <label class="form-label">创作方向 / 简介</label>
              <textarea
                v-model="applyForm.bio"
                class="form-textarea"
                id="input-apply-creator-bio"
                rows="2"
                placeholder="例如：专注逆袭爽剧与年代励志题材创作"
              ></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showApplyModal = false">取消</button>
            <button class="btn-confirm" id="btn-confirm-apply-creator" @click="submitCreatorApplication" :disabled="isApplying">
              {{ isApplying ? '正在提交...' : '提交创作者申请' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Reviewer Application Modal -->
    <transition name="modal-fade">
      <div v-if="showReviewerModal" class="modal-overlay" @click.self="showReviewerModal = false" id="modal-reviewer-overlay">
        <div class="modal-content glass-panel" id="modal-reviewer-box">
          <div class="modal-header">
            <h3>申请成为平台内容审核员</h3>
            <button class="btn-close" @click="showReviewerModal = false">✕</button>
          </div>
          <div class="modal-body">
            <p class="modal-desc">
              成为认证审核员后，您将拥有【机审人审中台】权限，协助平台对短剧镜头、弹幕与评论合规治理。
            </p>
            <div class="form-group">
              <label class="form-label">审核员称呼 / 昵称</label>
              <input
                v-model="reviewerForm.reviewer_name"
                type="text"
                class="form-input"
                id="input-apply-reviewer-name"
                placeholder="例如：影视合规专员"
                required
              />
            </div>
            <div class="form-group">
              <label class="form-label">专业经验 / 申请阐述</label>
              <textarea
                v-model="reviewerForm.bio"
                class="form-textarea"
                id="input-apply-reviewer-bio"
                rows="2"
                placeholder="例如：具备2年短视频内容风控与版权审核经验"
              ></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showReviewerModal = false">取消</button>
            <button class="btn-confirm" id="btn-confirm-apply-reviewer" @click="submitReviewerApplication" :disabled="isApplyingReviewer">
              {{ isApplyingReviewer ? '正在提交...' : '提交审核员入驻申请' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Create / Edit Folder Modal -->
    <transition name="modal-fade">
      <div v-if="showFolderModal" class="modal-overlay" @click.self="showFolderModal = false" id="modal-create-folder">
        <div class="modal-content glass-panel" id="modal-folder-box">
          <div class="modal-header">
            <h3>{{ editingFolderId ? '编辑收藏夹' : '新建剧单收藏夹' }}</h3>
            <button class="btn-close" id="btn-close-folder-modal" @click="showFolderModal = false">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label class="form-label">收藏夹名称 <span style="color: #ff453a;">*</span></label>
              <input
                v-model="folderForm.name"
                type="text"
                class="form-input"
                id="input-folder-name"
                placeholder="例如：高能反转爽剧合集"
                maxlength="50"
                required
              />
            </div>
            <div class="form-group">
              <label class="form-label">简介描述 (选填)</label>
              <textarea
                v-model="folderForm.description"
                class="form-textarea"
                id="input-folder-desc"
                rows="2"
                placeholder="简要描述此收藏夹收录的短剧主题..."
                maxlength="200"
              ></textarea>
            </div>
            <div class="form-group-switch">
              <label class="switch-container">
                <input type="checkbox" v-model="folderForm.is_public" id="checkbox-create-public" />
                <span class="switch-slider"></span>
              </label>
              <div class="switch-labels">
                <span class="switch-title">{{ folderForm.is_public ? '公开收藏夹' : '私密收藏夹' }}</span>
                <span class="switch-desc">{{ folderForm.is_public ? '所有人可在您的主页探索此收藏夹' : '仅自己登录可见' }}</span>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showFolderModal = false">取消</button>
            <button
              class="btn-confirm"
              id="btn-submit-create-folder"
              @click="submitFolderForm"
              :disabled="!folderForm.name.trim() || isSubmittingFolder"
            >
              {{ isSubmittingFolder ? '正在处理...' : (editingFolderId ? '保存修改' : '立即创建') }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Follow / Following List Modal -->
    <transition name="modal-fade">
      <div v-if="showFollowModal" class="modal-overlay" @click.self="showFollowModal = false" id="modal-follow-list">
        <div class="modal-content glass-panel" id="modal-follow-box">
          <div class="modal-header">
            <h3>{{ followModalType === 'followings' ? '我的关注列表' : '我的粉丝列表' }}</h3>
            <button class="btn-close" id="btn-close-follow-modal" @click="showFollowModal = false">✕</button>
          </div>
          <div class="modal-body">
            <div v-if="followListLoading" class="loading-state-box">
              <span>正在加载社交关系...</span>
            </div>
            <div v-else-if="currentFollowDisplayList.length === 0" class="empty-state-box">
              <div class="empty-icon-wrap"><el-icon :size="40"><UserFilled /></el-icon></div>
              <div class="empty-title">{{ followModalType === 'followings' ? '暂无关注任何用户' : '暂无粉丝' }}</div>
              <p class="empty-sub">在短剧评论区或创作者名片点击关注即可连接彼此！</p>
            </div>
            <div v-else class="follow-user-items-wrap">
              <div
                v-for="u in currentFollowDisplayList"
                :key="u.user_id"
                class="follow-user-card"
                :id="'follow-user-' + u.user_id"
              >
                <img :src="u.avatar_url || defaultAvatar" class="follow-user-avatar" />
                <div class="follow-user-info">
                  <div class="follow-user-name">
                    <span class="user-nick">{{ u.nickname || u.username }}</span>
                    <span class="user-role-badge">{{ u.role }}</span>
                  </div>
                  <span class="follow-user-bio">{{ u.bio || '暂无个人简介' }}</span>
                </div>
                <button
                  class="btn-toggle-follow-item"
                  @click="handleToggleFollowInModal(u.user_id)"
                >
                  {{ followModalType === 'followings' ? '取消关注' : (u.is_following_back ? '互相关注' : '回关') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import GoldCoinIcon from '../components/GoldCoinIcon.vue'
import { Star, Film, VideoCamera, Folder, ChatDotRound, Check, Setting, Upload, UserFilled } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import GlobalHeader from '../components/GlobalHeader.vue'
import { userApi, type UserFullProfile, type WatchHistoryItem, type UserLikeItem, type UserCoinWalletData } from '../api/user'
import { favoritesApi, type FavoriteFolder, type FavoriteItem } from '../api/favorites'

const router = useRouter()
const userStore = useUserStore()

const profile = ref<UserFullProfile | null>(null)
const historyList = ref<WatchHistoryItem[]>([])
const likesList = ref<UserLikeItem[]>([])
const commentsList = ref<any[]>([])
const commentsLoading = ref(false)
const followingsList = ref<any[]>([])
const followersList = ref<any[]>([])
const showFollowModal = ref(false)
const followModalType = ref<'followings' | 'followers'>('followings')
const followListLoading = ref(false)
const avatarFileInput = ref<HTMLInputElement | null>(null)
const heroAvatarFileInput = ref<HTMLInputElement | null>(null)
const isUploadingAvatar = ref(false)
const isUploadingHeroAvatar = ref(false)

const activeTab = ref<'history' | 'likes' | 'favorites' | 'comments' | 'profile' | 'edit'>('history')

const currentFollowDisplayList = computed(() => {
  return followModalType.value === 'followings' ? followingsList.value : followersList.value
})

// Economy & VIP Center State (Feature 21)
const walletData = ref<UserCoinWalletData>({
  balance: 50,
  total_earned: 50,
  total_spent: 0,
  has_signed_today: false,
  ad_watch_count_today: 0
})
const isSigningIn = ref(false)
const isWatchingAd = ref(false)
const adCountdownText = ref('')
const isExchangingVip = ref(false)

const isUserVip = computed(() => {
  if (!profile.value) return false
  if (profile.value.is_vip) return true
  if (profile.value.vip_expire_at) {
    return new Date(profile.value.vip_expire_at).getTime() > Date.now()
  }
  return false
})

const vipExpiryDisplay = computed(() => {
  if (!profile.value?.vip_expire_at) return '未开通'
  const d = new Date(profile.value.vip_expire_at)
  if (d.getTime() <= Date.now()) return '已到期'
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

async function loadWalletData() {
  try {
    const res = await userApi.getCoinWallet()
    if (res?.data) {
      walletData.value = res.data
    }
  } catch (err) {
    console.warn('Failed to load coin wallet:', err)
  }
}

async function handleDailySignIn() {
  if (walletData.value.has_signed_today || isSigningIn.value) return
  isSigningIn.value = true
  try {
    const res = await userApi.dailySignIn()
    if (res?.data) {
      walletData.value.balance = res.data.balance
      walletData.value.has_signed_today = true
      walletData.value.total_earned += res.data.reward || 10
    }
  } catch (err: any) {
    alert(err?.response?.data?.detail || err?.message || '签到失败')
  } finally {
    isSigningIn.value = false
  }
}

async function handleWatchAd() {
  if (isWatchingAd.value) return
  isWatchingAd.value = true
  adCountdownText.value = '正在观看广告 (5s)...'
  
  // Call reward API immediately to ensure instant persistence
  try {
    const res = await userApi.watchAdReward()
    if (res?.data) {
      walletData.value.balance = res.data.balance
      walletData.value.total_earned += res.data.reward || 5
    }
  } catch (err: any) {
    console.warn('Ad reward API error:', err)
  }

  // Visual countdown
  let left = 4
  const timer = setInterval(() => {
    if (left > 0) {
      adCountdownText.value = `正在观看广告 (${left}s)...`
      left--
    } else {
      clearInterval(timer)
      isWatchingAd.value = false
      adCountdownText.value = ''
    }
  }, 1000)
}

async function handleExchangeVip(days: number, cost: number) {
  if (walletData.value.balance < cost || isExchangingVip.value) return
  isExchangingVip.value = true
  try {
    const res = await userApi.exchangeVip({ days, cost })
    if (res?.data) {
      walletData.value.balance = res.data.balance
      walletData.value.total_spent += cost
      if (profile.value) {
        profile.value.vip_expire_at = res.data.vip_expire_at
        profile.value.is_vip = true
      }
    }
  } catch (err: any) {
    alert(err?.response?.data?.detail || err?.message || 'VIP 兑换失败')
  } finally {
    isExchangingVip.value = false
  }
}

const redeemCodeInput = ref('')
const isRedeemingCode = ref(false)
const redeemFeedback = reactive<{ type: 'success' | 'error'; message: string }>({
  type: 'success',
  message: ''
})

async function handleRedeemCode() {
  const code = redeemCodeInput.value.trim().toUpperCase()
  if (!code || isRedeemingCode.value) return
  isRedeemingCode.value = true
  redeemFeedback.message = ''
  try {
    const res = await userApi.redeemCode(code)
    if (res?.data) {
      walletData.value.balance = res.data.balance
      if (res.data.total_earned !== undefined) {
        walletData.value.total_earned = res.data.total_earned
      }
      if (res.data.vip_expire_at && profile.value) {
        profile.value.vip_expire_at = res.data.vip_expire_at
        profile.value.is_vip = true
      }
      redeemFeedback.type = 'success'
      redeemFeedback.message = res.message || `兑换成功！`
      redeemCodeInput.value = ''
    }
  } catch (err: any) {
    redeemFeedback.type = 'error'
    redeemFeedback.message = err?.response?.data?.detail || err?.message || '兑换码无效或已被使用'
  } finally {
    isRedeemingCode.value = false
  }
}

// Multi-level Favorites State
const foldersList = ref<FavoriteFolder[]>([])
const currentFolderId = ref<string>('')
const currentFolder = computed(() => foldersList.value.find(f => f.id === currentFolderId.value))
const folderItems = ref<FavoriteItem[]>([])
const folderItemsLoading = ref(false)
const totalFavoritesCount = computed(() => {
  return foldersList.value.reduce((sum, f) => sum + (f.item_count || 0), 0)
})

const showFolderModal = ref(false)
const editingFolderId = ref<string | null>(null)
const isSubmittingFolder = ref(false)
const folderForm = reactive({
  name: '',
  description: '',
  is_public: false
})

const defaultAvatar = 'https://api.dicebear.com/7.x/bottts/svg?seed=default_viewer'
const defaultCover = 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=640&q=80'

const avatarSeeds = ['viewer_1', 'creator_pro', 'drama_queen', 'cyber_cat', 'speed_stream']

const editForm = reactive({
  nickname: '',
  bio: '',
  avatar_url: ''
})

const applyForm = reactive({
  creator_name: '',
  bio: ''
})

const showApplyModal = ref(false)
const isApplying = ref(false)
const isSaving = ref(false)
const saveNotice = ref('')

onMounted(async () => {
  await loadUserData()
  await loadFoldersData()
  await loadWalletData()
  await loadComments()
  await loadFollowData()
})

async function loadUserData() {
  try {
    const pRes: any = await userApi.getProfile()
    const pData = pRes?.data || pRes
    profile.value = pData
    editForm.nickname = pData?.nickname || ''
    editForm.bio = pData?.creator_bio || ''
    editForm.avatar_url = pData?.avatar_url || ''
    applyForm.creator_name = (pData?.nickname || pData?.username) + '的创作空间'

    // Load history and likes
    const hRes: any = await userApi.getHistory()
    historyList.value = hRes?.data || []

    const lRes: any = await userApi.getLikes()
    likesList.value = lRes?.data || []
  } catch (err) {
    console.warn('Failed to load user profile, checking local auth state:', err)
    const localUser = localStorage.getItem('user')
    if (localUser) {
      try {
        const u = JSON.parse(localUser)
        profile.value = {
          ...u,
          stats: { history_count: 0, likes_count: 0, creator_videos_count: 0 }
        }
      } catch (e) {}
    } else {
      router.push('/login?redirect=/user/space')
    }
  }
}

async function loadFoldersData() {
  try {
    const res: any = await favoritesApi.getFolders()
    const data = res?.data || res
    foldersList.value = Array.isArray(data) ? data : []
    if (foldersList.value.length > 0) {
      if (!currentFolderId.value || !foldersList.value.some(f => f.id === currentFolderId.value)) {
        currentFolderId.value = foldersList.value[0].id
      }
      await loadFolderItems(currentFolderId.value)
    }
  } catch (err) {
    console.warn('Failed to load favorite folders:', err)
  }
}

async function selectFolder(folderId: string) {
  currentFolderId.value = folderId
  await loadFolderItems(folderId)
}

async function loadFolderItems(folderId: string) {
  if (!folderId) return
  folderItemsLoading.value = true
  try {
    const res: any = await favoritesApi.getFolderItems(folderId)
    const data = res?.data || res
    folderItems.value = Array.isArray(data) ? data : []
  } catch (err) {
    console.warn('Failed to load folder items:', err)
    folderItems.value = []
  } finally {
    folderItemsLoading.value = false
  }
}

function openCreateFolderModal() {
  editingFolderId.value = null
  folderForm.name = ''
  folderForm.description = ''
  folderForm.is_public = false
  showFolderModal.value = true
}

function openEditFolderModal(f: FavoriteFolder) {
  editingFolderId.value = f.id
  folderForm.name = f.name
  folderForm.description = f.description || ''
  folderForm.is_public = f.is_public
  showFolderModal.value = true
}

async function submitFolderForm() {
  const name = folderForm.name.trim()
  if (!name) return
  isSubmittingFolder.value = true
  try {
    if (editingFolderId.value) {
      await favoritesApi.updateFolder(editingFolderId.value, {
        name,
        description: folderForm.description,
        is_public: folderForm.is_public
      })
    } else {
      const res: any = await favoritesApi.createFolder({
        name,
        description: folderForm.description,
        is_public: folderForm.is_public
      })
      const created = res?.data || res
      if (created && created.id) {
        currentFolderId.value = created.id
      }
    }
    showFolderModal.value = false
    await loadFoldersData()
  } catch (err: any) {
    alert(err?.response?.data?.detail || '操作失败，请重试')
  } finally {
    isSubmittingFolder.value = false
  }
}

async function handleDeleteFolder(folderId: string) {
  if (!confirm('确认删除该收藏夹？其中的收藏短剧将被清空。')) return
  try {
    await favoritesApi.deleteFolder(folderId)
    currentFolderId.value = ''
    await loadFoldersData()
  } catch (err: any) {
    alert(err?.response?.data?.detail || '删除失败')
  }
}

async function handleRemoveFromFolder(videoId: string) {
  if (!currentFolderId.value) return
  try {
    await favoritesApi.removeFolderItem(currentFolderId.value, videoId)
    await loadFolderItems(currentFolderId.value)
    const f = foldersList.value.find(f => f.id === currentFolderId.value)
    if (f && f.item_count > 0) {
      f.item_count -= 1
    }
  } catch (err: any) {
    alert(err?.response?.data?.detail || '移除失败')
  }
}

function formatDate(isoStr: string) {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
  } catch (e) {
    return isoStr
  }
}

function getRoleBadgeText(role?: string) {
  switch (role) {
    case 'CREATOR': return '认证创作者'
    case 'ADMIN': return '超级管理员'
    case 'REVIEWER': return '内容审核员'
    default: return '普通观众'
  }
}

function formatDuration(seconds: number) {
  if (!seconds || seconds <= 0) return '00:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function openApplyModal() {
  showApplyModal.value = true
}

const showReviewerModal = ref(false)
const isApplyingReviewer = ref(false)
const reviewerForm = reactive({
  reviewer_name: '',
  bio: ''
})

function openReviewerModal() {
  reviewerForm.reviewer_name = (profile.value?.nickname || profile.value?.username || '') + '（内容审核）'
  reviewerForm.bio = ''
  showReviewerModal.value = true
}

async function submitCreatorApplication() {
  isApplying.value = true
  try {
    const res: any = await userApi.applyCreator({
      creator_name: applyForm.creator_name,
      bio: applyForm.bio
    })
    alert(res?.message || '创作者资质申请已成功提交！请等待管理员在管理中台审核。')
    showApplyModal.value = false
    await loadUserData()
  } catch (err: any) {
    alert('申请提交失败: ' + (err?.message || '网络错误'))
  } finally {
    isApplying.value = false
  }
}

async function submitReviewerApplication() {
  isApplyingReviewer.value = true
  try {
    const res: any = await userApi.applyReviewer({
      reviewer_name: reviewerForm.reviewer_name,
      bio: reviewerForm.bio
    })
    alert(res?.message || '审核员资质申请已成功提交！请等待管理员在管理中台审核通过。')
    showReviewerModal.value = false
    await loadUserData()
  } catch (err: any) {
    alert('审核员申请失败: ' + (err?.message || '网络错误'))
  } finally {
    isApplyingReviewer.value = false
  }
}

async function loadComments() {
  commentsLoading.value = true
  try {
    const res: any = await userApi.getComments(1, 50)
    commentsList.value = res?.data?.items || []
  } catch (err) {
    console.warn('Failed to load user comments:', err)
    commentsList.value = []
  } finally {
    commentsLoading.value = false
  }
}

async function handleDeleteComment(commentId: string) {
  if (!confirm('确认删除这条评论？删除后不可恢复。')) return
  try {
    await userApi.deleteComment(commentId)
    commentsList.value = commentsList.value.filter(c => c.comment_id !== commentId)
  } catch (err: any) {
    alert(err?.response?.data?.detail || '删除评论失败')
  }
}

async function loadFollowData() {
  try {
    const [resFollowings, resFollowers] = await Promise.all([
      userApi.getFollowings(),
      userApi.getFollowers()
    ])
    followingsList.value = resFollowings?.data?.items || []
    followersList.value = resFollowers?.data?.items || []
  } catch (err) {
    console.warn('Failed to load follow data:', err)
  }
}

function openFollowModal(type: 'followings' | 'followers') {
  followModalType.value = type
  showFollowModal.value = true
  loadFollowData()
}

async function handleToggleFollowInModal(targetUserId: string) {
  try {
    const res: any = await userApi.toggleFollow(targetUserId)
    await loadFollowData()
    await loadUserData()
  } catch (err: any) {
    alert(err?.response?.data?.detail || '操作失败')
  }
}

function triggerHeroAvatarPick() {
  heroAvatarFileInput.value?.click()
}

async function handleHeroAvatarSelected(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return
  const file = target.files[0]

  if (file.size > 10 * 1024 * 1024) {
    alert('所选图片超出 10MB 限制，请重新选择')
    target.value = ''
    return
  }

  const formData = new FormData()
  formData.append('file', file)

  isUploadingHeroAvatar.value = true
  try {
    const res: any = await userApi.uploadImage(formData)
    const uploadedUrl = res?.url || res?.data?.url
    if (uploadedUrl) {
      await userApi.updateProfile({
        avatar_url: uploadedUrl
      })
      if (profile.value) {
        profile.value.avatar_url = uploadedUrl
      }
      editForm.avatar_url = uploadedUrl
      if (userStore.currentUser) {
        (userStore.currentUser as any).avatar_url = uploadedUrl
      }
      alert('头像更换成功！')
    } else {
      alert(res?.message || '图片上传失败')
    }
  } catch (err: any) {
    alert(err?.response?.data?.detail || '更换头像失败')
  } finally {
    isUploadingHeroAvatar.value = false
    target.value = ''
  }
}

function triggerAvatarFilePick() {
  avatarFileInput.value?.click()
}

async function handleAvatarFileSelected(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return
  const file = target.files[0]

  if (file.size > 10 * 1024 * 1024) {
    alert('所选图片超出 10MB 限制，请重新选择')
    target.value = ''
    return
  }

  const formData = new FormData()
  formData.append('file', file)

  isUploadingAvatar.value = true
  try {
    const res: any = await userApi.uploadImage(formData)
    if (res?.url || res?.data?.url) {
      const uploadedUrl = res.url || res.data.url
      editForm.avatar_url = uploadedUrl
      saveNotice.value = '图片已上传成功，点击下方“保存资料修改”即可生效'
    } else {
      alert(res?.message || '图片上传失败')
    }
  } catch (err: any) {
    alert(err?.response?.data?.detail || '上传头像图片失败')
  } finally {
    isUploadingAvatar.value = false
    target.value = ''
  }
}

async function saveProfile() {
  isSaving.value = true
  saveNotice.value = ''
  try {
    const res: any = await userApi.updateProfile({
      nickname: editForm.nickname,
      bio: editForm.bio,
      avatar_url: editForm.avatar_url
    })
    saveNotice.value = '资料修改已生效'
    await loadUserData()

    // Sync to local storage and dispatch global event
    try {
      const stored = localStorage.getItem('user')
      if (stored) {
        const u = JSON.parse(stored)
        u.nickname = editForm.nickname
        u.avatar_url = editForm.avatar_url
        u.creator_bio = editForm.bio
        localStorage.setItem('user', JSON.stringify(u))
      }
      window.dispatchEvent(new Event('user-updated'))
    } catch (e) {}

    setTimeout(() => { saveNotice.value = '' }, 3000)
  } catch (err: any) {
    saveNotice.value = '保存失败: ' + (err?.message || '网络错误')
  } finally {
    isSaving.value = false
  }
}

function handleLogout() {
  localStorage.removeItem('cinema_access_token')
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  window.location.href = '/'
}
</script>

<style scoped>
.user-space-page {
  position: relative;
  min-height: 100vh;
  width: 100%;
  background: var(--bg-main, #0b0f19);
  color: var(--apple-text-primary, #f8fafc);
  padding: 0 0 80px 0;
  box-sizing: border-box;
  overflow-x: hidden;
}

.space-ambient-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(140px);
  opacity: 0.25;
  pointer-events: none;
}
.glow-top {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #00aeec, #6366f1);
  top: -100px;
  right: -50px;
}
.glow-bottom {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, #fb7299, #8b5cf6);
  bottom: 0;
  left: -100px;
}

.space-container {
  position: relative;
  z-index: 1;
  max-width: 1100px;
  margin: 24px auto 0 auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

/* 1. Header Hero Card */
.space-hero-card {
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 32px;
  background: rgba(18, 24, 38, 0.75);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4);
}

.hero-avatar-wrap {
  position: relative;
  width: 96px;
  height: 96px;
  flex-shrink: 0;
}
.hero-avatar-wrap.clickable {
  cursor: pointer;
}
.hero-avatar-wrap.clickable:hover .avatar-hover-overlay {
  opacity: 1;
}
.avatar-hover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.25s ease;
  z-index: 2;
}
.camera-icon-svg {
  width: 22px;
  height: 22px;
  stroke: #ffffff;
}
.overlay-text {
  font-size: 11px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.5px;
}
.hero-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 3px solid #00aeec;
  object-fit: cover;
  background: rgba(255, 255, 255, 0.05);
}

.role-badge {
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 12px;
  white-space: nowrap;
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
}
.role-badge.role-creator { color: #f472b6; border-color: #ec4899; }
.role-badge.role-admin { color: #c084fc; border-color: #a855f7; }
.role-badge.role-reviewer { color: #fcd34d; border-color: #f59e0b; }
.role-badge.role-user { color: #38bdf8; border-color: #0284c7; }

.hero-info {
  flex: 1;
}

.hero-name-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}
.hero-nickname {
  font-size: 26px;
  font-weight: 800;
  margin: 0;
  color: #ffffff;
}
.hero-username {
  font-size: 14px;
  color: #64748b;
}
.status-pill {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.hero-bio {
  font-size: 13px;
  color: #94a3b8;
  margin: 8px 0 16px 0;
  line-height: 1.5;
}

.hero-stats-row {
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.stat-val {
  font-size: 20px;
  font-weight: 800;
  color: #f1f5f9;
}
.stat-lbl {
  font-size: 12px;
  color: #64748b;
}
.stat-sep {
  color: rgba(255, 255, 255, 0.15);
}

.hero-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.action-btn-secondary {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  color: #e2e8f0;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
}
.action-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}

.action-btn-danger {
  padding: 8px 16px;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 12px;
  color: #fca5a5;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.action-btn-danger:hover {
  background: rgba(239, 68, 68, 0.25);
}

/* 2. Dual Qualification Center (Creator & Reviewer) */
.creator-qualification-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
  gap: 20px;
}
.qual-card {
  padding: 20px 24px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  transition: all 0.25s ease;
}
.qual-card.is-active {
  border-color: rgba(0, 174, 236, 0.3);
  background: rgba(0, 174, 236, 0.04);
}
.qual-content {
  display: flex;
  align-items: center;
  gap: 18px;
}
.qual-icon {
  font-size: 32px;
}
.qual-text {
  flex: 1;
}
.qual-text h3 {
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 4px 0;
  color: #ffffff;
}
.qual-text p {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}
.qual-action-wrap {
  flex-shrink: 0;
}
.qual-action-btn {
  padding: 10px 18px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  border: none;
  white-space: nowrap;
  transition: all 0.2s ease;
  display: inline-block;
}
.btn-enter-creator {
  background: linear-gradient(135deg, #ec4899, #db2777);
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(236, 72, 153, 0.35);
}
.btn-enter-reviewer {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.35);
}
.btn-apply-creator {
  background: linear-gradient(135deg, #00aeec, #0284c7);
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(0, 174, 236, 0.35);
}
.btn-apply-reviewer {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(245, 158, 11, 0.35);
}
.btn-pending {
  background: rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
  border: 1px solid rgba(255, 255, 255, 0.2);
  cursor: not-allowed;
}
.qual-action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

/* 3. Space Tab Section */
.space-tabs-section {
  background: rgba(18, 24, 38, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  padding: 24px;
}

.space-tab-bar {
  display: flex;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 16px;
  margin-bottom: 24px;
}
.tab-btn {
  padding: 8px 18px;
  border-radius: 12px;
  background: transparent;
  border: 1px solid transparent;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.tab-btn.active {
  background: rgba(0, 174, 236, 0.15);
  border-color: rgba(0, 174, 236, 0.4);
  color: #38bdf8;
}

/* History Cards */
.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 18px;
}
.history-card {
  display: flex;
  gap: 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 12px;
  transition: all 0.2s ease;
}
.history-card:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(0, 174, 236, 0.3);
  transform: translateY(-2px);
}
.history-cover-wrap {
  position: relative;
  width: 110px;
  height: 72px;
  flex-shrink: 0;
  border-radius: 10px;
  overflow: hidden;
}
.history-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.progress-bar-wrap {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: rgba(0, 0, 0, 0.5);
}
.progress-bar-fill {
  height: 100%;
  background: #00aeec;
}
.ep-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 10px;
  font-weight: 600;
  background: rgba(0, 0, 0, 0.7);
  padding: 1px 6px;
  border-radius: 6px;
  color: #ffffff;
}

.history-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.history-drama-title {
  font-size: 13px;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.history-ep-title {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
}
.history-progress-text {
  font-size: 11px;
  color: #64748b;
}
.history-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
}
.history-time {
  font-size: 11px;
  color: #64748b;
}
.continue-play-btn {
  font-size: 11px;
  font-weight: 700;
  color: #38bdf8;
  text-decoration: none;
  background: rgba(0, 174, 236, 0.15);
  padding: 3px 8px;
  border-radius: 8px;
}

/* Likes Grid */
.likes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.like-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
}
.like-cover {
  width: 80px;
  height: 60px;
  border-radius: 8px;
  object-fit: cover;
}
.like-info h4 {
  font-size: 13px;
  font-weight: 700;
  margin: 0 0 4px 0;
  color: #f1f5f9;
}
.like-info p {
  font-size: 11px;
  color: #94a3b8;
  margin: 0 0 6px 0;
}
.like-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
}
.like-time {
  color: #64748b;
}
.play-link {
  color: #00aeec;
  text-decoration: none;
  font-weight: 600;
}

/* Empty State */
.empty-state-box {
  text-align: center;
  padding: 60px 20px;
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.empty-title {
  font-size: 16px;
  font-weight: 700;
  color: #e2e8f0;
  margin-bottom: 6px;
}
.empty-sub {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 20px;
}
.action-btn-primary {
  display: inline-block;
  padding: 10px 24px;
  background: #00aeec;
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 174, 236, 0.35);
}

/* Profile Edit Box */
.profile-edit-box {
  max-width: 560px;
}
.edit-title {
  font-size: 16px;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 20px;
}
.profile-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-label {
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e1;
}
.form-input, .form-textarea {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  padding: 10px 14px;
  color: #ffffff;
  font-size: 14px;
  outline: none;
}
.form-input.readonly {
  opacity: 0.6;
  cursor: not-allowed;
}
.avatar-presets-row {
  display: flex;
  gap: 12px;
}
.avatar-preset-item {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.06);
  transition: all 0.2s ease;
}
.avatar-preset-item.selected {
  border-color: #00aeec;
  transform: scale(1.1);
}
.auth-primary-btn {
  padding: 10px 24px;
  background: #00aeec;
  border: none;
  border-radius: 12px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}
.save-notice {
  font-size: 13px;
  color: #4ade80;
}
.edit-actions-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 8px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(12px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-card {
  width: 100%;
  max-width: 460px;
  background: #141c2e;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.modal-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: #f8fafc;
  margin: 0;
}
.modal-close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 20px;
  cursor: pointer;
}
.modal-desc {
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
  margin-bottom: 16px;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
.btn-cancel {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.08);
  border: none;
  border-radius: 10px;
  color: #cbd5e1;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.btn-confirm {
  padding: 8px 18px;
  background: #00aeec;
  border: none;
  border-radius: 10px;
  color: #ffffff;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

/* Favorites Tab & Folders Styling */
.favorites-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.pane-section-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 4px 0;
  color: #f8fafc;
}
.pane-section-sub {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}
.folders-pill-nav {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 8px;
  margin-bottom: 20px;
}
.folder-pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 980px;
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
  white-space: nowrap;
}
.folder-pill-btn:hover {
  background: rgba(255, 255, 255, 0.12);
}
.folder-pill-btn.active {
  background: #0071e3;
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 4px 14px rgba(0, 113, 227, 0.35);
}
.folder-pill-badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.14);
}
.folder-pill-badge.default {
  background: rgba(0, 113, 227, 0.4);
  color: #64b5f6;
}
.folder-pill-count {
  font-size: 11px;
  opacity: 0.85;
  background: rgba(0, 0, 0, 0.25);
  padding: 1px 7px;
  border-radius: 8px;
}
.active-folder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  margin-bottom: 24px;
}
.folder-title-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.current-folder-title {
  font-size: 16px;
  font-weight: 700;
  margin: 0;
  color: #ffffff;
}
.tag-default-capsule {
  font-size: 11px;
  background: rgba(0, 113, 227, 0.3);
  color: #64b5f6;
  padding: 2px 8px;
  border-radius: 8px;
}
.tag-privacy-capsule {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
}
.folder-updated-date {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
}
.current-folder-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.65);
  margin: 0;
}
.folder-header-actions {
  display: flex;
  gap: 8px;
}
.btn-folder-action {
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  border: none;
  font-weight: 500;
  transition: all 0.2s ease;
}
.btn-folder-action.edit {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}
.btn-folder-action.edit:hover {
  background: rgba(255, 255, 255, 0.2);
}
.btn-folder-action.delete {
  background: rgba(255, 69, 58, 0.15);
  color: #ff453a;
}
.btn-folder-action.delete:hover {
  background: rgba(255, 69, 58, 0.25);
}
.favorites-drama-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 18px;
}
.fav-drama-card {
  display: flex;
  gap: 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 14px;
  transition: all 0.2s ease;
}
.fav-drama-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.18);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
}
.fav-cover-wrap {
  position: relative;
  width: 80px;
  height: 112px;
  flex-shrink: 0;
  border-radius: 10px;
  overflow: hidden;
}
.fav-cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.fav-episodes-badge {
  position: absolute;
  bottom: 4px;
  left: 4px;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
}
.fav-category-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(0, 113, 227, 0.85);
  color: #fff;
}
.fav-card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.fav-drama-title {
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 6px 0;
  color: #ffffff;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.fav-drama-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 8px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}
.fav-card-meta-line {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  margin-bottom: 10px;
}
.fav-card-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
}
.btn-remove-fav {
  padding: 5px 10px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-remove-fav:hover {
  background: rgba(255, 69, 58, 0.2);
  color: #ff453a;
}
.btn-play-direct {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 600;
  background: #0071e3;
  color: #ffffff;
  border-radius: 980px;
  text-decoration: none;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 113, 227, 0.4);
}
.btn-play-direct:hover {
  background: #0077ed;
  transform: translateY(-1px);
}
.form-group-switch {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 14px;
}
.switch-container {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}
.switch-container input {
  opacity: 0;
  width: 0;
  height: 0;
}
.switch-slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  transition: 0.3s;
}
.switch-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background: #ffffff;
  border-radius: 50%;
  transition: 0.3s;
}
.switch-container input:checked + .switch-slider {
  background: #34c759;
}
.switch-container input:checked + .switch-slider:before {
  transform: translateX(20px);
}
.switch-labels {
  display: flex;
  flex-direction: column;
}
.switch-title {
  font-size: 13px;
  font-weight: 600;
  color: #ffffff;
}
.switch-desc {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}
.loading-state-box {
  text-align: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}

/* ========================================================================== */
/* Economy Bento Grid (Feature 21)                                             */
/* ========================================================================== */
.economy-bento-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

@media (max-width: 900px) {
  .economy-bento-grid {
    grid-template-columns: 1fr;
  }
}

.economy-card {
  padding: 24px;
  border-radius: 20px;
  background: rgba(22, 22, 26, 0.8) !important;
  backdrop-filter: blur(24px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 16px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
}

.economy-card:hover {
  border-color: rgba(255, 255, 255, 0.18) !important;
  transform: translateY(-2px);
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.header-icon-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-emoji {
  font-size: 28px;
}

.card-heading {
  font-size: 16px;
  font-weight: 700;
  color: #f5f5f7;
  margin-bottom: 4px;
}

.card-subheading {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  display: block;
}

.wallet-badge-pill {
  background: rgba(255, 214, 10, 0.12);
  border: 1px solid rgba(255, 214, 10, 0.3);
  padding: 6px 14px;
  border-radius: 999px;
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.balance-num {
  font-size: 20px;
  font-weight: 800;
  color: #ffd60a;
}

.balance-unit {
  font-size: 12px;
  color: #ffd60a;
}

.wallet-stats-strip {
  display: flex;
  align-items: center;
  justify-content: space-around;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 10px 14px;
}

.wallet-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.wstat-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}

.wstat-value {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.wstat-value.text-success {
  color: #30d158;
}

.wallet-stat-sep {
  width: 1px;
  height: 24px;
  background: rgba(255, 255, 255, 0.1);
}

.economy-actions-row {
  display: flex;
  gap: 12px;
}

.apple-bento-btn {
  flex: 1;
  padding: 10px 16px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.12);
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.apple-bento-btn.mini {
  flex: none;
  padding: 6px 14px;
  font-size: 12px;
}

.btn-signin {
  background: linear-gradient(135deg, rgba(255, 214, 10, 0.2), rgba(255, 159, 10, 0.2));
  color: #ffd60a;
  border-color: rgba(255, 214, 10, 0.4);
}

.btn-signin:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(255, 214, 10, 0.3), rgba(255, 159, 10, 0.3));
  box-shadow: 0 4px 14px rgba(255, 214, 10, 0.25);
  transform: translateY(-1px);
}

.btn-signin:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.4);
  border-color: rgba(255, 255, 255, 0.08);
}

.btn-ad {
  background: linear-gradient(135deg, rgba(0, 113, 227, 0.2), rgba(88, 86, 214, 0.2));
  color: #2997ff;
  border-color: rgba(0, 113, 227, 0.4);
}

.btn-ad:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(0, 113, 227, 0.3), rgba(88, 86, 214, 0.3));
  box-shadow: 0 4px 14px rgba(0, 113, 227, 0.25);
  transform: translateY(-1px);
}

.btn-ad:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.vip-status-pill {
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.vip-status-pill.active {
  background: linear-gradient(135deg, rgba(255, 69, 58, 0.2), rgba(255, 159, 10, 0.2));
  color: #ff9f0a;
  border-color: rgba(255, 159, 10, 0.4);
}

.vip-expiry-box {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 10px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.vip-expiry-label {
  color: rgba(255, 255, 255, 0.6);
}

.vip-expiry-val {
  font-weight: 600;
  color: #f5f5f7;
}

.vip-tiers-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.vip-tier-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
}

.tier-info {
  display: flex;
  flex-direction: column;
}

.tier-name {
  font-size: 13px;
  font-weight: 600;
  color: #f5f5f7;
}

.tier-cost {
  font-size: 11px;
  color: #ffd60a;
}

.btn-exchange {
  background: linear-gradient(135deg, rgba(175, 82, 222, 0.2), rgba(255, 45, 85, 0.2));
  color: #bf5af2;
  border-color: rgba(175, 82, 222, 0.4);
}

.btn-exchange:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(175, 82, 222, 0.3), rgba(255, 45, 85, 0.3));
  box-shadow: 0 4px 14px rgba(175, 82, 222, 0.25);
  transform: translateY(-1px);
}

.btn-exchange:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.4);
  border-color: rgba(255, 255, 255, 0.08);
}

/* Unified SVG Badges for User Profile */
.card-coin-badge,
.card-crown-badge,
.qual-icon-box {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-right: 12px;
  flex-shrink: 0;
}

.creator-box {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.25);
}

.reviewer-box {
  background: rgba(16, 185, 129, 0.12);
  border-color: rgba(16, 185, 129, 0.25);
}

.empty-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.3);
  margin-bottom: 12px;
}

.tab-label-flex {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}


/* Redemption Voucher Bento Card Styles */
.redemption-bento-card {
  padding: 20px 24px !important;
}

.redemption-card-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.card-voucher-badge {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 113, 227, 0.12);
  border: 1px solid rgba(0, 113, 227, 0.28);
  flex-shrink: 0;
}

.redemption-input-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 320px;
  max-width: 520px;
}

.redemption-code-input {
  flex: 1;
  height: 42px;
  padding: 0 16px;
  border-radius: 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.18);
  color: var(--text-primary, #f5f5f7);
  outline: none;
  transition: all 0.2s ease;
}

.redemption-code-input:focus {
  border-color: #0071e3;
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.2);
}

[data-theme="light"] .redemption-code-input {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #0f172a;
}

.btn-redeem-submit {
  height: 42px;
  padding: 0 22px !important;
  background: linear-gradient(135deg, #0071e3, #0284c7) !important;
  color: #ffffff !important;
  font-weight: 700 !important;
  border-radius: 12px !important;
  border: none !important;
  white-space: nowrap;
  cursor: pointer;
}

.btn-redeem-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.redeem-feedback-banner {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
}

.redeem-feedback-banner.is-success {
  background: rgba(16, 185, 129, 0.14);
  border: 1px solid rgba(16, 185, 129, 0.35);
  color: #10b981;
}

[data-theme="light"] .redeem-feedback-banner.is-success {
  background: #ecfdf5;
  border-color: #6ee7b7;
  color: #047857;
}

.redeem-feedback-banner.is-error {
  background: rgba(239, 68, 68, 0.14);
  border: 1px solid rgba(239, 68, 68, 0.35);
  color: #ef4444;
}

[data-theme="light"] .redeem-feedback-banner.is-error {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #b91c1c;
}
</style>

<style>
/* User Space Page - Comprehensive Light Theme Overrides (Apple HIG Unified) */
[data-theme="light"] .user-space-page {
  background: #f5f6f8 !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .space-ambient-glow {
  opacity: 0.12 !important;
}

[data-theme="light"] .space-hero-card {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05) !important;
}

[data-theme="light"] .hero-nickname {
  color: #1d1d1f !important;
}

[data-theme="light"] .hero-username,
[data-theme="light"] .hero-bio,
[data-theme="light"] .stat-lbl {
  color: #6e6e73 !important;
}

[data-theme="light"] .stat-val {
  color: #1d1d1f !important;
}

[data-theme="light"] .stat-sep {
  color: rgba(0, 0, 0, 0.15) !important;
}

[data-theme="light"] .hero-actions .action-btn-secondary {
  background: rgba(0, 0, 0, 0.04) !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .hero-actions .action-btn-secondary:hover {
  background: rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .economy-card.glass-panel,
[data-theme="light"] .qual-card.glass-panel {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
}

[data-theme="light"] .card-heading,
[data-theme="light"] .qual-text h3 {
  color: #1d1d1f !important;
}

[data-theme="light"] .card-subheading,
[data-theme="light"] .qual-text p {
  color: #6e6e73 !important;
}

[data-theme="light"] .wallet-badge-pill {
  background: rgba(255, 214, 10, 0.15) !important;
  border: 1px solid rgba(255, 214, 10, 0.3) !important;
}

[data-theme="light"] .balance-num,
[data-theme="light"] .balance-unit {
  color: #b45309 !important;
}

[data-theme="light"] .wallet-stats-strip {
  background: rgba(0, 0, 0, 0.02) !important;
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .wallet-stat-sep {
  background: rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .wstat-label,
[data-theme="light"] .vip-status-sub,
[data-theme="light"] .vip-expiry-label {
  color: #6e6e73 !important;
}

[data-theme="light"] .wstat-value,
[data-theme="light"] .vip-expiry-val,
[data-theme="light"] .tier-name,
[data-theme="light"] .option-name {
  color: #1d1d1f !important;
}

[data-theme="light"] .tier-cost {
  color: #b45309 !important;
}

[data-theme="light"] .vip-status-pill {
  background: rgba(255, 149, 0, 0.12) !important;
  color: #c2410c !important;
  border: 1px solid rgba(255, 149, 0, 0.25) !important;
}

[data-theme="light"] .vip-expiry-box,
[data-theme="light"] .vip-tier-card {
  background: rgba(0, 0, 0, 0.02) !important;
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .btn-pending {
  background: rgba(0, 0, 0, 0.04) !important;
  color: #86868b !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .space-tabs-section {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05) !important;
}

[data-theme="light"] .space-tab-bar {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .tab-btn {
  color: #6e6e73 !important;
}

[data-theme="light"] .tab-btn:hover {
  color: #1d1d1f !important;
}

[data-theme="light"] .tab-btn.active {
  color: #0071e3 !important;
  background: rgba(0, 113, 227, 0.08) !important;
  border-color: rgba(0, 113, 227, 0.22) !important;
}

[data-theme="light"] .empty-title {
  color: #1d1d1f !important;
}

[data-theme="light"] .empty-sub {
  color: #6e6e73 !important;
}

[data-theme="light"] .card-title,
[data-theme="light"] .metric-val,
[data-theme="light"] .priv-title,
[data-theme="light"] .edit-title,
[data-theme="light"] .pane-section-title {
  color: #1d1d1f !important;
}

[data-theme="light"] .card-sub,
[data-theme="light"] .metric-label,
[data-theme="light"] .priv-desc,
[data-theme="light"] .rule-desc,
[data-theme="light"] .pane-section-sub {
  color: #6e6e73 !important;
}

[data-theme="light"] .user-space-page .wallet-val {
  color: #d97706 !important;
}

[data-theme="light"] .user-space-page .wallet-unit {
  color: #b45309 !important;
}

[data-theme="light"] .flow-metric-item,
[data-theme="light"] .privilege-item,
[data-theme="light"] .status-bar,
[data-theme="light"] .rule-item {
  background: rgba(0, 0, 0, 0.03) !important;
  border-color: rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .profile-tabs-content {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
}

[data-theme="light"] .profile-tab-btn {
  color: #6e6e73 !important;
}

[data-theme="light"] .profile-tab-btn.active {
  color: #0071e3 !important;
  border-bottom-color: #0071e3 !important;
}

[data-theme="light"] .history-card,
[data-theme="light"] .like-card,
[data-theme="light"] .favorite-card {
  background: rgba(0, 0, 0, 0.02) !important;
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .history-card:hover,
[data-theme="light"] .like-card:hover,
[data-theme="light"] .favorite-card:hover {
  background: #ffffff !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08) !important;
  border-color: rgba(0, 113, 227, 0.3) !important;
}

[data-theme="light"] .history-drama-title,
[data-theme="light"] .like-info h4,
[data-theme="light"] .fav-drama-title {
  color: #1d1d1f !important;
}

[data-theme="light"] .history-ep-title,
[data-theme="light"] .like-info p,
[data-theme="light"] .fav-ep-title {
  color: #6e6e73 !important;
}

[data-theme="light"] .history-progress-text {
  color: #86868b !important;
}

[data-theme="light"] .form-input {
  background: rgba(0, 0, 0, 0.04) !important;
  border: 1px solid rgba(0, 0, 0, 0.12) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .form-label {
  color: #1d1d1f !important;
}

[data-theme="light"] .btn-action-outline {
  background: transparent !important;
  border: 1px solid rgba(0, 0, 0, 0.12) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .btn-action-outline:hover {
  background: rgba(0, 0, 0, 0.05) !important;
}

/* High Contrast Light Theme Styles for Economy Action Buttons */
[data-theme="light"] .btn-signin {
  background: linear-gradient(135deg, rgba(255, 159, 10, 0.12), rgba(255, 149, 0, 0.18)) !important;
  border: 1px solid rgba(245, 158, 11, 0.45) !important;
  color: #8a4b00 !important; /* Deep warm amber for >= 6.8:1 contrast */
  font-weight: 600 !important;
}

[data-theme="light"] .btn-signin:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(255, 159, 10, 0.22), rgba(255, 149, 0, 0.28)) !important;
  border-color: rgba(245, 158, 11, 0.65) !important;
  color: #6c3a00 !important;
}

[data-theme="light"] .btn-signin:disabled,
[data-theme="light"] .btn-signin:disabled span {
  background: #e2e8f0 !important;
  color: #1e293b !important;
  border-color: #cbd5e1 !important;
  opacity: 1 !important;
  cursor: not-allowed !important;
  font-weight: 700 !important;
}

[data-theme="light"] .btn-ad {
  background: linear-gradient(135deg, rgba(0, 113, 227, 0.1), rgba(88, 86, 214, 0.1)) !important;
  border: 1px solid rgba(0, 113, 227, 0.35) !important;
  color: #0055b3 !important; /* Deep navy blue for >= 7.2:1 contrast */
  font-weight: 600 !important;
}

[data-theme="light"] .btn-ad:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(0, 113, 227, 0.18), rgba(88, 86, 214, 0.18)) !important;
  border-color: rgba(0, 113, 227, 0.5) !important;
  color: #003d80 !important;
}

[data-theme="light"] .btn-ad:disabled,
[data-theme="light"] .btn-ad:disabled span {
  background: #e2e8f0 !important;
  color: #1e293b !important;
  border-color: #cbd5e1 !important;
  opacity: 1 !important;
  cursor: not-allowed !important;
  font-weight: 700 !important;
}

[data-theme="dark"] .btn-signin:disabled,
[data-theme="dark"] .btn-signin:disabled span,
[data-theme="dark"] .btn-ad:disabled,
[data-theme="dark"] .btn-ad:disabled span {
  background: rgba(255, 255, 255, 0.12) !important;
  color: #f8fafc !important;
  border-color: rgba(255, 255, 255, 0.22) !important;
  opacity: 1 !important;
  cursor: not-allowed !important;
  font-weight: 700 !important;
}

[data-theme="light"] .btn-exchange {
  background: #0071e3 !important;
  color: #ffffff !important;
}

[data-theme="light"] .btn-exchange:disabled {
  background: rgba(0, 0, 0, 0.04) !important;
  color: #8e8e93 !important;
  border-color: rgba(0, 0, 0, 0.08) !important;
  opacity: 1 !important;
}

/* User Comments Tab Styling */
.user-comments-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.user-comment-card {
  padding: 20px 24px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.comment-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.badge-drama-title {
  font-size: 13px;
  font-weight: 600;
  color: #2997ff;
}
.badge-reply-target {
  font-size: 12px;
  color: #bf5af2;
  margin-left: 8px;
}
.comment-pub-date {
  font-size: 12px;
  color: #86868b;
}
.comment-content-text {
  font-size: 14px;
  color: #f5f5f7;
  line-height: 1.6;
  margin: 0;
}
.comment-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}
.comment-stats-tag {
  font-size: 12px;
  color: #ff375f;
}
.comment-action-btns {
  display: flex;
  gap: 12px;
  align-items: center;
}
.btn-delete-comment {
  font-size: 12px;
  color: #ff453a;
  background: transparent;
  border: 1px solid rgba(255, 69, 58, 0.3);
  padding: 4px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-delete-comment:hover {
  background: rgba(255, 69, 58, 0.15);
}
.btn-goto-drama {
  font-size: 12px;
  color: #2997ff;
  text-decoration: none;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(0, 113, 227, 0.1);
  border: 1px solid rgba(0, 113, 227, 0.25);
}
.btn-goto-drama:hover {
  background: rgba(0, 113, 227, 0.2);
}

/* Local Avatar Upload Styling */
.avatar-custom-upload-box {
  margin-bottom: 16px;
}
.current-avatar-preview {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px dashed rgba(255, 255, 255, 0.15);
}
.avatar-preview-img {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.2);
}
.upload-trigger-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.btn-upload-avatar {
  align-self: flex-start;
  padding: 6px 14px;
  font-size: 12px;
  cursor: pointer;
}
.upload-tip-text {
  font-size: 11px;
  color: #86868b;
}
.avatar-presets-label {
  font-size: 12px;
  color: #86868b;
  margin-bottom: 8px;
}

/* Follow List Modal Styling */
.follow-user-items-wrap {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}
.follow-user-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.follow-user-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
}
.follow-user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.follow-user-name {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-nick {
  font-size: 14px;
  font-weight: 600;
  color: #f5f5f7;
}
.user-role-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.08);
  color: #86868b;
}
.follow-user-bio {
  font-size: 12px;
  color: #86868b;
}
.btn-toggle-follow-item {
  font-size: 12px;
  padding: 5px 12px;
  border-radius: 20px;
  background: rgba(0, 113, 227, 0.15);
  border: 1px solid rgba(0, 113, 227, 0.3);
  color: #2997ff;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-toggle-follow-item:hover {
  background: rgba(0, 113, 227, 0.3);
}

[data-theme="light"] .user-comment-card,
[data-theme="light"] .current-avatar-preview,
[data-theme="light"] .follow-user-card {
  background: #ffffff !important;
  border-color: rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}
[data-theme="light"] .comment-content-text,
[data-theme="light"] .user-nick {
  color: #1d1d1f !important;
}
[data-theme="light"] .badge-drama-title {
  color: #0071e3 !important;
}
[data-theme="light"] .badge-reply-target {
  color: #7c3aed !important;
}
[data-theme="light"] .comment-pub-date {
  color: #6e6e73 !important;
}
[data-theme="light"] .comment-stats-tag {
  color: #d70035 !important;
}
[data-theme="light"] .btn-goto-drama {
  color: #0071e3 !important;
  background: rgba(0, 113, 227, 0.08) !important;
  border-color: rgba(0, 113, 227, 0.25) !important;
}
[data-theme="light"] .btn-delete-comment {
  color: #d70015 !important;
  border-color: rgba(215, 0, 21, 0.3) !important;
  background: rgba(215, 0, 21, 0.04) !important;
}
[data-theme="light"] .btn-delete-comment:hover {
  background: rgba(215, 0, 21, 0.12) !important;
}
[data-theme="light"] .current-avatar-preview {
  border-color: rgba(0, 0, 0, 0.15) !important;
}
</style>
