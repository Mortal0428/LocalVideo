<template>
  <div
    class="apple-player-page"
    :class="{ 'mode-landscape': displayMode === 'landscape', 'mode-portrait': displayMode === 'portrait' }"
    id="cinema-backdrop"
  >
    <!-- Top Apple HIG Translucent Header -->
    <header class="player-global-header" id="player-top-header">
      <div class="header-inner">
        <!-- Left: Back to Home & Drama Title -->
        <div class="header-left">
          <router-link to="/" class="apple-back-btn" id="btn-back-home" title="返回视听大厅">
            <svg viewBox="0 0 24 24" class="back-svg"><path fill="currentColor" d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
            <span>返回大厅</span>
          </router-link>
          <span class="header-divider">/</span>
          <div class="drama-headline-chip">
            <span class="drama-tag">热播短剧</span>
            <span class="drama-title-text">{{ album?.title || '精彩短剧' }}</span>
            <span class="episode-pill">第 {{ currentEpisode?.episode_num || 1 }} 集</span>
          </div>
        </div>

        <!-- Center: Apple Segmented Dual-Mode Switcher (16:9 vs 9:16) -->
        <div class="header-center">
          <div class="apple-mode-switcher-capsule" id="mode-switcher-container">
            <button
              class="mode-switch-btn"
              :class="{ active: displayMode === 'landscape' }"
              id="btn-mode-landscape"
              @click="displayMode = 'landscape'"
              title="切换为 16:9 极简宽屏影院模式"
            >
              <svg viewBox="0 0 24 24" class="mode-icon"><path fill="currentColor" d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H4V6h16v12z"/></svg>
              <span>16:9 极简宽屏</span>
            </button>
            <button
              class="mode-switch-btn"
              :class="{ active: displayMode === 'portrait' }"
              id="btn-mode-portrait"
              @click="displayMode = 'portrait'"
              title="切换为 9:16 沉浸短剧胶囊模式"
            >
              <svg viewBox="0 0 24 24" class="mode-icon"><path fill="currentColor" d="M17 1.01L7 1c-1.1 0-2 .9-2 2v18c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V3c0-1.1-.9-1.99-2-1.99zM17 19H7V5h10v14z"/></svg>
              <span>9:16 沉浸胶囊</span>
            </button>
          </div>
        </div>

        <!-- Right: Role Control & User State -->
        <div class="header-right">
          <!-- Notification Bell Trigger -->
          <div class="skylight-trigger-wrap">
            <button 
              type="button" 
              class="skylight-bell-btn" 
              id="btn-notification-skylight"
              @click="showSkylightDrawer = !showSkylightDrawer"
              title="通知天窗"
            >
              <el-icon :size="16"><Bell /></el-icon>
              <span 
                v-if="unreadCounts.total > 0" 
                class="skylight-unread-badge" 
                id="skylight-unread-badge"
              >
                {{ unreadCounts.total > 99 ? '99+' : unreadCounts.total }}
              </span>
            </button>
          </div>

          <template v-if="currentUser">
            <router-link to="/user/space" class="user-chip-mini" id="user-profile-badge" title="前往个人中心">
              <img :src="currentUser.avatar_url || defaultAvatar" class="avatar-mini" id="user-avatar-img" />
              <div class="user-info-text">
                <span class="user-name-mini" id="user-display-name">{{ currentUser.nickname || currentUser.username }}</span>
                <span class="user-role-badge-mini" :class="currentUser.role?.toLowerCase()">{{ getRoleLabel(currentUser.role) }}</span>
              </div>
            </router-link>
            <button class="logout-link-mini" id="btn-logout" @click="handleLogout">退出</button>
          </template>
          <template v-else>
            <router-link to="/login" class="apple-primary-btn mini-btn" id="btn-open-login">
              登录 / 注册
            </router-link>
          </template>
        </div>
      </div>
    </header>

    <!-- Auto-Resume Toast Notification -->
    <transition name="apple-toast-slide">
      <div v-if="resumeToast" class="resume-toast-capsule" id="resume-toast-pill">
        <span class="toast-sparkle"><svg viewBox="0 0 24 24" class="time-svg"><path fill="currentColor" d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6l5.2 3.2.8-1.3-4.5-2.7V7z"/></svg></span>
        <span class="toast-msg">{{ resumeToast }}</span>
      </div>
    </transition>

    <!-- ==================================================================== -->
    <!-- UNIFIED RESPONSIVE THEATER (Single Persistent Video Instance)        -->
    <!-- ==================================================================== -->
    <div 
      class="theater-stage-container" 
      :class="['stage-' + displayMode, { 'sidebar-collapsed': isSidebarCollapsed, 'is-web-fullscreen': isWebFullscreen }]" 
      :id="displayMode === 'landscape' ? 'landscape-player-layout' : 'portrait-player-layout'"
    >
      <!-- Left / Center: Dynamic Morphing Video Player Viewport -->
      <div class="theater-player-column">
        <div class="video-viewport-box" id="widescreen-player-box">
          <!-- 9:16 Mobile Notch Header (Visible in Portrait Mode) -->
          <div v-if="displayMode === 'portrait'" class="mobile-notch-bar">
            <div class="notch-speaker"></div>
            <span class="notch-title">CinemaAgent 9:16</span>
          </div>

          <!-- SINGLE PERSISTENT VIDEO ELEMENT (Never unmounted on mode switch) -->
          <div class="video-media-wrapper" @click="togglePlay">
            <video
              ref="videoRef"
              id="player-video"
              class="core-video-element"
              playsinline
              preload="auto"
              :src="currentStreamUrl"
              @timeupdate="onTimeUpdate"
              @loadedmetadata="onLoadedMetadata"
              @ended="onVideoEnded"
              @error="onVideoError"
            ></video>

            <!-- 4-Track High-Speed Danmaku Layer -->
            <div class="danmaku-screen-layer" pointer-events="none">
              <div
                v-for="d in activeDanmakus"
                :key="d.id"
                class="danmaku-flying-bullet"
                :style="{
                  top: (d.track * 26 + 12) + 'px',
                  color: d.color,
                  animationDuration: d.speed + 's'
                }"
              >
                {{ d.content }}
              </div>
            </div>

            <!-- Central Big Play/Pause Splash Icon -->
            <transition name="fade">
              <div v-if="!isPlaying" class="play-splash-circle">
                <svg viewBox="0 0 24 24" class="splash-svg"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>
              </div>
            </transition>
          </div>

          <!-- 5s Frosted Glass Countdown HUD Overlay -->
          <transition name="apple-hud-pop">
            <div
              v-if="showCountdownHud"
              class="autoplay-countdown-hud autoplay-countdown-hud-overlay"
              id="autoplay-countdown-hud"
            >
              <div class="hud-glass-card">
                <div class="hud-header">
                  <span class="hud-sparkle-icon">✨</span>
                  <span class="hud-badge">自动连播倒计时</span>
                </div>
                <div class="hud-body">
                  <div class="hud-timer-circle">
                    <span class="hud-timer-num" id="hud-countdown-seconds">{{ countdownSeconds }}</span>
                    <span class="hud-timer-unit">s</span>
                  </div>
                  <div class="hud-next-info">
                    <div class="hud-next-label">5s后自动播放下一集</div>
                    <div class="hud-next-title" id="hud-next-ep-title">
                      第 {{ nextEpisode?.episode_num || (currentEpisode ? currentEpisode.episode_num + 1 : 1) }} 集：{{ nextEpisode?.title || '精彩下一集' }}
                    </div>
                  </div>
                </div>
                <div class="hud-actions-row">
                  <button
                    class="hud-btn-primary"
                    id="btn-hud-skip-next"
                    @click.stop="executeNextEpisodeImmediately"
                    title="立即播放下一集"
                  >
                    <span id="btn-skip-countdown">立即播放 ({{ countdownSeconds }}s)</span>
                  </button>
                  <button
                    class="hud-btn-secondary"
                    id="btn-hud-cancel-autoplay"
                    @click.stop="cancelCountdownAutoplay"
                    title="取消自动连播"
                  >
                    <span id="btn-cancel-countdown">取消连播</span>
                  </button>
                </div>
              </div>
            </div>
          </transition>

          <!-- In-Player Apple Glass Control Bar -->
          <div class="player-controls-bar">
            <!-- Progress Slider -->
            <div class="progress-track-wrapper" @click="handleSeekClick">
              <div class="progress-bar-bg">
                <div class="progress-bar-fill" :style="{ width: progressPercent + '%' }">
                  <div class="progress-handle"></div>
                </div>
              </div>
            </div>

            <!-- Control Buttons & Danmaku Input -->
            <div class="controls-action-line">
              <div class="ctrl-left">
                <button class="icon-ctrl-btn" @click.stop="togglePlay" title="播放/暂停">
                  <svg v-if="isPlaying" viewBox="0 0 24 24" class="ctrl-svg"><path fill="currentColor" d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
                  <svg v-else viewBox="0 0 24 24" class="ctrl-svg"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>
                </button>
                <span class="timestamp-display">{{ formatSeconds(currentTime) }} / {{ formatSeconds(duration) }}</span>
              </div>

              <!-- Danmaku Send Capsule -->
              <div class="danmaku-send-box">
                <input
                  v-model="danmakuInputText"
                  id="input-danmaku"
                  class="danmaku-pill-input"
                  placeholder="发一条友善弹幕，与全网剧迷实时互动..."
                  maxlength="50"
                  @keyup.enter="sendDanmaku"
                />
                <button class="btn-danmaku-send" id="btn-send-danmaku" @click="sendDanmaku">发送弹幕</button>
              </div>

              <div class="ctrl-right">
                <!-- Autoplay Continuous Toggle -->
                <button
                  class="pill-ctrl-btn autoplay-toggle-btn"
                  :class="{ active: isAutoplayEnabled }"
                  id="btn-toggle-autoplay"
                  @click.stop="toggleAutoplay"
                  :title="isAutoplayEnabled ? '点击关闭自动连播' : '点击开启自动连播'"
                >
                  <span class="autoplay-indicator-dot"></span>
                  <span>连播 {{ isAutoplayEnabled ? '开' : '关' }}</span>
                </button>

                <!-- Playback Rate Selector -->
                <div 
                  class="speed-menu-wrap" 
                  @mouseenter="openSpeedMenu" 
                  @mouseleave="closeSpeedMenuDebounced"
                >
                  <button class="pill-ctrl-btn" @click.stop="showSpeedMenu = !showSpeedMenu" id="btn-playback-rate" title="调节播放倍速">
                    {{ currentRate === 1.0 ? '倍速' : currentRate + 'x' }}
                  </button>
                  <div 
                    v-if="showSpeedMenu" 
                    class="dropdown-popover-glass" 
                    id="menu-playback-speed"
                    @mouseenter="openSpeedMenu" 
                    @mouseleave="closeSpeedMenuDebounced"
                  >
                    <div
                      v-for="r in [2.0, 1.5, 1.25, 1.0, 0.75, 0.5]"
                      :key="r"
                      class="popover-item"
                      :class="{ active: currentRate === r }"
                      @click.stop="setPlaybackRate(r)"
                      :id="'speed-opt-' + r"
                    >
                      {{ r }}x
                    </div>
                  </div>
                </div>

                <!-- Resolution Selector -->
                <div 
                  class="resolution-menu-wrap" 
                  @mouseenter="openResMenu" 
                  @mouseleave="closeResMenuDebounced"
                >
                  <button class="pill-ctrl-btn" @click.stop="showResMenu = !showResMenu" id="btn-resolution" title="清晰度画质选择">
                    {{ currentResolution }}
                  </button>
                  <div 
                    v-if="showResMenu" 
                    class="dropdown-popover-glass" 
                    id="menu-resolution"
                    @mouseenter="openResMenu" 
                    @mouseleave="closeResMenuDebounced"
                  >
                    <div
                      v-for="res in ['4K 原画', '1080P 超清', '720P 高清']"
                      :key="res"
                      class="popover-item"
                      :class="{ active: currentResolution === res }"
                      @click.stop="setResolution(res)"
                    >
                      {{ res }}
                    </div>
                  </div>
                </div>

                <!-- Mode Toggle -->
                <button
                  class="mode-quick-toggle"
                  @click="displayMode = (displayMode === 'landscape' ? 'portrait' : 'landscape')"
                  :title="displayMode === 'landscape' ? '切换为 9:16 沉浸短剧竖屏' : '切换为 16:9 极简宽屏'"
                >
                  {{ displayMode === 'landscape' ? '竖屏' : '横屏' }}
                </button>

                <!-- Web Fullscreen Toggle -->
                <button
                  class="mode-quick-toggle"
                  :class="{ active: isWebFullscreen }"
                  id="btn-web-fullscreen"
                  @click.stop="toggleWebFullscreen"
                  :title="isWebFullscreen ? '退出网页沉浸全屏' : '网页沉浸全屏'"
                >
                  {{ isWebFullscreen ? '还原' : '网页全屏' }}
                </button>

                <!-- Native Physical Fullscreen Toggle -->
                <button
                  class="mode-quick-toggle"
                  id="btn-native-fullscreen"
                  @click.stop="toggleNativeFullscreen"
                  title="物理全屏"
                >
                  全屏
                </button>

                <!-- Right Sidebar Collapsible Toggle -->
                <button
                  class="mode-quick-toggle"
                  :class="{ active: isSidebarCollapsed }"
                  id="btn-toggle-sidebar"
                  @click.stop="isSidebarCollapsed = !isSidebarCollapsed"
                  :title="isSidebarCollapsed ? '展开右侧功能面板 (选集/看点/伴读)' : '收起右侧功能面板，全幅巨幕自适应'"
                >
                  {{ isSidebarCollapsed ? '展开侧栏 ❮' : '收起侧栏 ❯' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Metadata & Interaction Row below Video (Widescreen Mode) -->
        <div class="video-meta-card">
          <div class="meta-titles-row">
            <h1 class="video-main-heading">{{ album?.title }} · 第 {{ currentEpisode?.episode_num }} 集：{{ currentEpisode?.title }}</h1>
            <div class="video-stats-labels">
              <span>▶ {{ formatNumber(album?.view_count || 1280) }} 播放</span>
              <span>💬 {{ formatNumber(activeDanmakus.length || 0) }} 弹幕</span>
              <span>夸克网盘极速直连</span>
            </div>
          </div>

          <!-- Apple Style Interaction Pills (Like, Coin, Fav, Share) -->
          <div class="action-pills-row">
            <button
              class="apple-action-pill btn-like"
              :class="{ active: isLiked }"
              id="btn-video-like"
              @click="handleToggleLike"
            >
              <span class="pill-emoji">❤️</span>
              <span>{{ isLiked ? '已点赞' : '点赞' }} ({{ likeCount }})</span>
            </button>
            <button class="apple-action-pill" id="btn-coin-tip" @click="handleCoin">
              <span class="pill-emoji">🪙</span>
              <span>投币 ({{ videoCoinCount }})</span>
            </button>
            <button
              class="apple-action-pill"
              :class="{ active: isFavorited }"
              id="btn-favorite"
              @click="handleFavoriteClick"
            >
              <span class="pill-emoji">⭐</span>
              <span>{{ isFavorited ? '已收藏' : '收藏' }} ({{ favoriteCount }})</span>
            </button>
            <button class="apple-action-pill" @click="handleShare">
              <span class="pill-emoji">↗️</span>
              <span>分享</span>
            </button>
          </div>
        </div>

        <!-- Comments Section -->
        <div class="comments-bento-card">
          <div class="comments-card-header">
            <h3>剧迷精彩评论 ({{ commentsTotal || comments.length }})</h3>
          </div>

          <!-- Add Root Comment Input Box -->
          <div class="comment-compose-box">
            <img :src="currentUser?.avatar_url || defaultAvatar" class="compose-avatar" alt="头像" />
            <div class="compose-input-area">
              <textarea
                v-model="commentText"
                id="input-comment"
                class="comment-textarea"
                placeholder="发一条走心评论，与剧迷深度探讨高能剧情..."
                rows="2"
                @keyup.ctrl.enter="submitComment"
              ></textarea>
              <button 
                class="apple-primary-btn" 
                id="btn-submit-comment" 
                :disabled="isSubmittingComment || !commentText.trim()"
                @click="submitComment"
              >
                {{ isSubmittingComment ? '发送中...' : '发表评论' }}
              </button>
            </div>
          </div>

          <!-- Two-Tier Comments Flow List -->
          <div class="comments-flow-list" id="comments-flow-list">
            <div v-if="comments.length === 0" class="comments-empty-state">
              <span class="empty-emoji">💬</span>
              <span>暂无评论，快来发表第一条走心剧评吧！</span>
            </div>

            <div 
              v-for="c in comments" 
              :key="c.id" 
              :id="'comment-' + c.id"
              class="comment-thread-card"
              :class="{ 'comment-highlight': highlightedCommentId === c.id }"
            >
              <!-- Main Root Comment Card -->
              <div class="comment-bubble-item root-bubble">
                <img :src="c.avatar_url || defaultAvatar" class="commenter-avatar" alt="头像" />
                <div class="comment-body">
                  <div class="comment-author-line">
                    <span class="comment-name">{{ c.nickname || c.username }}</span>
                    <span class="comment-time">{{ c.created_at || '刚刚' }}</span>
                  </div>
                  <p class="comment-content-text">{{ c.content }}</p>

                  <!-- Action Bar (Like & Reply) -->
                  <div class="comment-actions-bar">
                    <button 
                      type="button"
                      class="comment-action-btn like-btn"
                      :class="{ liked: c.is_liked }"
                      :id="'btn-like-comment-' + c.id"
                      @click="handleToggleCommentLike(c)"
                      title="点赞"
                    >
                      <span class="action-icon">❤️</span>
                      <span class="action-count">{{ c.like_count || 0 }}</span>
                    </button>

                    <button 
                      type="button"
                      class="comment-action-btn reply-btn"
                      :id="'btn-reply-comment-' + c.id"
                      @click="toggleReplyInput(c.id, c.user_id, c.nickname || c.username)"
                    >
                      <span class="action-icon">💬</span>
                      <span>回复</span>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Nested Sub-thread Container (Replies) -->
              <div 
                v-if="c.replies && c.replies.length > 0" 
                class="sub-thread-container"
              >
                <div 
                  v-for="r in c.replies" 
                  :key="r.id" 
                  :id="'comment-' + r.id"
                  class="comment-bubble-item sub-bubble"
                  :class="{ 'comment-highlight': highlightedCommentId === r.id }"
                >
                  <img :src="r.avatar_url || defaultAvatar" class="commenter-avatar sub-avatar" alt="头像" />
                  <div class="comment-body">
                    <div class="comment-author-line">
                      <span class="comment-name">{{ r.nickname || r.username }}</span>
                      <span 
                        v-if="r.reply_to_nickname || r.reply_to_username" 
                        class="mention-target-tag"
                      >
                        回复 @{{ r.reply_to_nickname || r.reply_to_username }}
                      </span>
                      <span class="comment-time">{{ r.created_at || '刚刚' }}</span>
                    </div>
                    <p class="comment-content-text">{{ r.content }}</p>

                    <!-- Reply Action Bar -->
                    <div class="comment-actions-bar">
                      <button 
                        type="button"
                        class="comment-action-btn like-btn"
                        :class="{ liked: r.is_liked }"
                        :id="'btn-like-comment-' + r.id"
                        @click="handleToggleCommentLike(r)"
                        title="点赞"
                      >
                        <span class="action-icon">❤️</span>
                        <span class="action-count">{{ r.like_count || 0 }}</span>
                      </button>

                      <button 
                        type="button"
                        class="comment-action-btn reply-btn"
                        :id="'btn-reply-comment-' + r.id"
                        @click="toggleReplyInput(c.id, r.user_id, r.nickname || r.username)"
                      >
                        <span class="action-icon">💬</span>
                        <span>回复</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Inline Reply Input Box (when activeReplyRootId === c.id) -->
              <transition name="apple-fade">
                <div 
                  v-if="activeReplyRootId === c.id" 
                  class="inline-reply-box"
                >
                  <div class="reply-input-wrap">
                    <span class="replying-to-badge">回复 @{{ replyTargetName }}:</span>
                    <textarea
                      v-model="replyText"
                      :id="'input-reply-comment-' + c.id"
                      class="reply-textarea"
                      placeholder="写下您的理性探讨或精彩补充..."
                      rows="2"
                    ></textarea>
                    <div class="reply-box-footer">
                      <button 
                        type="button" 
                        class="reply-cancel-btn"
                        @click="cancelReply"
                      >
                        取消
                      </button>
                      <button 
                        type="button" 
                        class="apple-primary-btn reply-submit-btn" 
                        :id="'btn-submit-reply-' + c.id"
                        :disabled="isSubmittingReply || !replyText.trim()"
                        @click="submitReply(c.id)"
                      >
                        {{ isSubmittingReply ? '回复中...' : '提交回复' }}
                      </button>
                    </div>
                  </div>
                </div>
              </transition>
            </div>
          </div>
        </div>
      </div>

      <!-- Floating Expand Button when Sidebar is Collapsed -->
      <button 
        v-if="isSidebarCollapsed" 
        class="floating-expand-sidebar-btn" 
        id="btn-expand-sidebar-float"
        @click="isSidebarCollapsed = false"
        title="展开右侧功能栏 (选集/看点/伴读)"
      >
        <span>选集/伴读 ❮</span>
      </button>

      <!-- Right Column: Apple HIG Sidebar (Episodes, Highlights, Companion, Review) -->
      <aside class="theater-sidebar-column">
        <!-- Sidebar Header with Collapse Handle -->
        <div class="sidebar-top-control-bar">
          <span class="sidebar-top-title">视听与伴读交互台</span>
          <button 
            type="button" 
            class="sidebar-collapse-btn" 
            id="btn-collapse-sidebar"
            @click="isSidebarCollapsed = true"
            title="收起右侧面板，独占主屏幕视窗"
          >
            <span>收起 ❯</span>
          </button>
        </div>

        <!-- Tab Segment Switcher -->
        <div class="sidebar-tab-segment">
          <button
            class="side-tab-btn"
            :class="{ active: activeTab === 'episodes' }"
            id="tab-btn-episodes"
            @click="activeTab = 'episodes'"
          >
            选集 ({{ episodes.length }})
          </button>
          <button
            class="side-tab-btn"
            :class="{ active: activeTab === 'highlights' }"
            id="tab-btn-highlights"
            @click="activeTab = 'highlights'"
          >
            🔥 高能看点 ({{ highlights.length }})
          </button>
          <button
            class="side-tab-btn"
            :class="{ active: activeTab === 'agent' }"
            id="tab-btn-agent"
            @click="activeTab = 'agent'"
          >
            💬 剧情伴读
          </button>
          <button
            v-if="currentUser?.role === 'REVIEWER' || currentUser?.role === 'ADMIN'"
            class="side-tab-btn"
            :class="{ active: activeTab === 'review' }"
            id="tab-btn-review"
            @click="activeTab = 'review'"
          >
            🛡️ 机审中台
          </button>
        </div>

        <!-- Tab 1: Episodes Selector Card -->
        <div v-if="activeTab === 'episodes'" class="panel-episodes-wrap">
          <!-- Chunk Selector Tabs (1-50, 51-100, 全部) -->
          <div v-if="episodeChunks.length > 0" class="episode-chunk-tabs-row" id="episode-chunk-tabs">
            <button
              v-for="chunk in episodeChunks"
              :key="chunk.label"
              class="chunk-pill-btn"
              :class="{ active: selectedChunk === chunk.label }"
              @click="selectedChunk = chunk.label"
              :id="'btn-chunk-' + chunk.label"
            >
              {{ chunk.label }}
            </button>
          </div>

          <!-- Scrollable Episodes Window -->
          <div class="episodes-scroll-window" id="episodes-scroll-viewport">
            <div class="episodes-bento-grid">
              <button
                v-for="ep in visibleEpisodes"
                :key="ep.id"
                class="episode-tile-btn"
                :class="{ active: currentEpisode?.id === ep.id }"
                @click="switchEpisode(ep)"
                :id="'ep-btn-' + ep.episode_num"
              >
                <div class="ep-num-line">第 {{ ep.episode_num }} 集</div>
                <div class="ep-title-sub">{{ ep.title }}</div>
              </button>
            </div>
          </div>
        </div>

        <!-- Tab 2: High-Energy Highlights / Timeline Index -->
        <div v-if="activeTab === 'highlights'" class="panel-highlights-wrap" id="panel-highlights">
          <div class="highlights-flow-list">
            <div
              v-for="(h, idx) in highlights"
              :key="idx"
              class="highlight-card-item"
              @click="jumpToTimestamp(h.time, h.title)"
            >
              <div class="highlight-time-badge">
                <span class="time-text">{{ formatSeconds(h.time) }}</span>
                <span class="jump-hint">点击直达 ▶</span>
              </div>
              <div class="highlight-info-box">
                <div class="highlight-title-line">
                  <span class="highlight-title">{{ h.title }}</span>
                  <span class="highlight-tag-pill">{{ h.tag }}</span>
                </div>
                <p class="highlight-desc">{{ h.desc }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 3: Companion Discussion Dock (Cleaned of AI spam) -->
        <div v-if="activeTab === 'agent'" class="panel-agent-dock" id="panel-agent">
          <!-- Quick Starters -->
          <div class="agent-quick-prompts-row">
            <button
              v-for="(p, idx) in quickPrompts"
              :key="idx"
              class="quick-prompt-pill"
              @click="askQuickPrompt(p)"
            >
              {{ p }}
            </button>
          </div>

          <!-- Chat Conversation Scroll Area -->
          <div class="agent-chat-messages-scroll" ref="chatScrollRef">
            <div
              v-for="(msg, idx) in agentMessages"
              :key="idx"
              class="chat-bubble-row"
              :class="msg.sender"
            >
              <div class="bubble-avatar-squircle">
                {{ msg.sender === 'agent' ? '💬' : '👤' }}
              </div>
              <div class="bubble-content-card">
                <div class="bubble-sender-name">{{ msg.sender === 'agent' ? '剧情伴读 (DeepSeek-R1)' : '我' }}</div>

                <!-- Collapsible Thought Process Box (Collapses when final answer arrives) -->
                <div v-if="msg.thought && msg.text" class="thought-collapsible-box">
                  <details>
                    <summary class="thought-summary-badge">深度思考过程 ({{ msg.thought.length }} 字)</summary>
                    <div class="thought-inner-text">{{ msg.thought }}</div>
                  </details>
                </div>

                <div class="bubble-body-text">
                  <template v-for="(seg, sIdx) in parseMessageSegments(msg.text || msg.thought)" :key="sIdx">
                    <button 
                      v-if="seg.isTimeTag" 
                      type="button" 
                      class="inline-time-capsule-btn" 
                      @click.stop="jumpToTimeTag(seg.timeTag!)"
                      :title="'点击立即精准跳帧至 ' + seg.timeTag"
                    >
                      <span class="capsule-icon"><svg viewBox="0 0 24 24" class="time-svg"><path fill="currentColor" d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6l5.2 3.2.8-1.3-4.5-2.7V7z"/></svg></span>
                      <span class="capsule-time">[{{ seg.timeTag }}]</span>
                    </button>
                    <span v-else>{{ seg.content }}</span>
                  </template>
                  <span v-if="msg.isTyping" class="stream-cursor">▌</span>
                </div>

                <!-- Glowing Timestamp Seek Button (Seamless Frame Jump) -->
                <div v-if="msg.targetTime !== undefined" class="timestamp-jump-box">
                  <button
                    class="jump-timestamp-btn"
                    @click="jumpToTimestamp(msg.targetTime, msg.scene)"
                  >
                    <span class="sparkle-icon"><svg viewBox="0 0 24 24" class="time-svg"><path fill="currentColor" d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6l5.2 3.2.8-1.3-4.5-2.7V7z"/></svg></span>
                    <span>{{ msg.timeTag }} 镜头跳转</span>
                  </button>
                  <span class="scene-label">{{ msg.scene }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Question Input -->
          <div class="agent-input-dock">
            <input
              v-model="agentInputText"
              id="input-agent"
              class="agent-pill-input"
              placeholder="提问本集核心反转、台词或画面细节..."
              :disabled="isStreamingAgent"
              @keyup.enter="sendAgentQuestion"
            />
            <button
              class="apple-primary-btn"
              id="btn-send-agent"
              :disabled="isStreamingAgent"
              @click="sendAgentQuestion"
            >
              {{ isStreamingAgent ? '思考中...' : '提问' }}
            </button>
          </div>
        </div>

        <!-- Tab 3: Content Moderation Queue (For Reviewer / Admin) -->
        <div v-if="activeTab === 'review'" class="panel-review-wrap" id="panel-review">
          <div v-if="reviewQueue.length === 0" class="empty-review-state">
            <span>🛡️ 暂无待审违规记录，机审状态良好</span>
          </div>
          <div
            v-for="item in reviewQueue"
            :key="item.id"
            class="review-record-card"
          >
            <div class="record-meta-line">
              <span class="review-badge-red">DFA 阻断</span>
              <span class="violation-reason-tag">{{ item.violation_reason }}</span>
            </div>
            <div class="violating-text-quote">"{{ item.target_id }}"</div>
            <div class="review-actions-row">
              <button class="review-btn approve-btn" @click="handleReviewDecision(item.id, 'APPROVED')">误杀放行</button>
              <button class="review-btn reject-btn" @click="handleReviewDecision(item.id, 'REJECTED')">确认违规</button>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- Apple HIG Glassmorphism Auth Modal -->
    <transition name="apple-modal-fade">
      <div v-if="showAuthModal" class="apple-modal-backdrop" @click.self="showAuthModal = false" id="modal-auth-backdrop">
        <div class="apple-modal-card" id="modal-auth-card">
          <div class="modal-card-header">
            <h3 class="modal-title">{{ authMode === 'login' ? '账号登录' : '注册新账号' }}</h3>
            <button class="modal-close-icon-btn" id="btn-close-auth-modal" @click="showAuthModal = false">✕</button>
          </div>
          <form class="modal-form" @submit.prevent="handleAuthSubmit">
            <div class="form-field-group">
              <label class="field-label">用户名</label>
              <input v-model="authForm.username" type="text" id="input-auth-username" class="apple-form-input" required />
            </div>
            <div class="form-field-group">
              <label class="field-label">密码</label>
              <input v-model="authForm.password" type="password" id="input-auth-password" class="apple-form-input" required />
            </div>
            <button type="submit" class="apple-primary-btn modal-submit-btn" id="btn-submit-auth">
              {{ authMode === 'login' ? '立即登录' : '注册账号' }}
            </button>
          </form>
        </div>
      </div>
    </transition>

    <!-- Apple HIG Multi-level Favorites Modal -->
    <transition name="apple-modal-fade">
      <div
        v-if="showFavoriteModal"
        class="apple-modal-backdrop"
        id="modal-player-favorites"
        @click.self="showFavoriteModal = false"
      >
        <div class="apple-modal-card favorites-modal-card">
          <div class="modal-card-header">
            <div class="modal-header-title">
              <span class="modal-header-icon">⭐</span>
              <h3 class="modal-title">收藏到专属剧单</h3>
            </div>
            <button class="modal-close-icon-btn" id="btn-close-favorite-modal" @click="showFavoriteModal = false">✕</button>
          </div>

          <div class="modal-body favorites-modal-body">
            <div class="drama-mini-preview">
              <img :src="album?.cover_url || defaultCover" class="mini-cover" />
              <div class="mini-meta">
                <h4 class="mini-title">{{ album?.title || '当前短剧' }}</h4>
                <p class="mini-sub">{{ album?.category || '短剧' }} · 共 {{ episodes.length }} 集</p>
              </div>
            </div>

            <div class="folders-selection-list">
              <div class="section-label-row">
                <span>选择收藏夹（可多选）</span>
                <button class="btn-text-action" id="btn-show-create-folder" @click="showNewFolderInput = !showNewFolderInput">
                  {{ showNewFolderInput ? '收起' : '+ 新建收藏夹' }}
                </button>
              </div>

              <!-- New folder inline form -->
              <div v-if="showNewFolderInput" class="inline-new-folder-box">
                <input
                  v-model="newFolderName"
                  id="input-new-folder-name"
                  class="apple-form-input mini"
                  placeholder="输入收藏夹名称..."
                  maxlength="30"
                  @keyup.enter="handleCreateFolderInModal"
                />
                <label class="privacy-switch-label">
                  <input type="checkbox" v-model="newFolderIsPublic" id="checkbox-folder-public" />
                  <span>公开</span>
                </label>
                <button
                  class="apple-primary-btn mini-btn"
                  id="btn-confirm-create-folder"
                  @click="handleCreateFolderInModal"
                  :disabled="!newFolderName.trim()"
                >
                  创建
                </button>
              </div>

              <!-- Folder list -->
              <div class="folder-items-scroll">
                <div
                  v-for="folder in userFolders"
                  :key="folder.id"
                  class="folder-select-item"
                  :class="{ selected: selectedFolderIds.includes(folder.id) }"
                  @click="toggleFolderSelection(folder.id)"
                  :id="'folder-item-' + folder.id"
                >
                  <div class="folder-select-left">
                    <input
                      type="checkbox"
                      class="apple-checkbox"
                      :checked="selectedFolderIds.includes(folder.id)"
                      @click.stop="toggleFolderSelection(folder.id)"
                    />
                    <span class="folder-name-text">{{ folder.name }}</span>
                    <span v-if="folder.is_default" class="badge-default-tag">默认</span>
                    <span class="badge-privacy-tag">{{ folder.is_public ? '公开' : '私密' }}</span>
                  </div>
                  <span class="folder-count-badge">{{ folder.item_count }} 部</span>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer favorites-modal-footer">
            <button
              class="apple-btn-secondary"
              id="btn-quick-default-fav"
              @click="handleQuickDefaultSave"
            >
              一键存入默认收藏夹
            </button>
            <button
              class="apple-primary-btn"
              id="btn-save-favorites"
              @click="handleSaveToSelectedFolders"
              :disabled="isSavingFavorite"
            >
              {{ isSavingFavorite ? '保存中...' : `确认保存 (${selectedFolderIds.length})` }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Modal: Frosted Glass Coin Tipping (Feature 20) -->
    <transition name="apple-modal-fade">
      <div v-if="showCoinModal" class="apple-modal-backdrop modal-overlay" id="coin-tip-modal" @click.self="showCoinModal = false">
        <div class="apple-glass-dialog modal-card coin-tip-dialog">
          <div class="modal-header">
            <div class="modal-title-wrap">
              <span class="modal-emoji">🪙</span>
              <h3 class="modal-title">为《{{ album?.title }}》投币打赏</h3>
            </div>
            <button class="modal-close-btn" @click="showCoinModal = false">✕</button>
          </div>

          <div class="modal-body">
            <div class="wallet-balance-row">
              <span class="wallet-label">当前我的金币余额：</span>
              <span class="wallet-val">{{ userWalletBalance }} 🪙</span>
            </div>

            <div class="tipping-status-box">
              <div class="tip-status-text">
                本剧您已投：<strong>{{ userTippedCount }} / 2</strong> 枚金币
              </div>
              <div v-if="userTippedCount >= 2" class="max-tip-badge">
                ✓ 已投满 2 枚金币（感谢您的厚爱与支持！）
              </div>
            </div>

            <div v-if="tipSuccessTip" class="tip-success-banner">
              {{ tipSuccessTip }}
            </div>

            <div class="tipping-options-grid">
              <button
                class="tip-option-card"
                id="btn-tip-1-coin"
                :disabled="isTipping || userTippedCount >= 2 || (userTippedCount + 1 > 2) || userWalletBalance < 1"
                @click="executeTip(1)"
              >
                <div class="option-coin-icon">🪙</div>
                <div class="option-title">投 1 枚金币</div>
                <div class="option-sub">全站热度值 +10</div>
              </button>

              <button
                class="tip-option-card"
                id="btn-tip-2-coins"
                :disabled="isTipping || userTippedCount >= 1 || (userTippedCount + 2 > 2) || userWalletBalance < 2"
                @click="executeTip(2)"
              >
                <div class="option-coin-icon">🪙🪙</div>
                <div class="option-title">投 2 枚金币</div>
                <div class="option-sub">全站热度值 +20 · 倾囊力挺</div>
              </button>
            </div>
          </div>

          <div class="modal-footer">
            <button class="apple-btn-secondary" @click="showCoinModal = false">关闭</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Notification Skylight Drawer -->
    <NotificationSkylight
      v-model="showSkylightDrawer"
      :unread-counts="unreadCounts"
      @unread-count-changed="fetchUnreadCount"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { 
  videoApi, 
  type VideoAlbum, 
  type Episode, 
  type TwoTierCommentItem, 
  type CommentReplyItem, 
  type ActionCardData, 
  type HighlightItem 
} from '../api/video'
import { authApi, type UserInfo } from '../api/auth'
import { favoritesApi, type FavoriteFolder } from '../api/favorites'
import { userApi, notificationApi, type UnreadCountData } from '../api/user'
import { useUserStore } from '../stores/user'
import { Bell } from '@element-plus/icons-vue'
import NotificationSkylight from '../components/NotificationSkylight.vue'

const route = useRoute()
const props = defineProps<{ id?: string }>()
const userStore = useUserStore()

const defaultAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=apple'
const defaultCover = 'https://images.unsplash.com/photo-1518173946687-a4c8a383392e?w=800&q=80'

// State
const videoRef = ref<HTMLVideoElement | null>(null)
const chatScrollRef = ref<HTMLElement | null>(null)

const displayMode = ref<'landscape' | 'portrait'>('landscape')
const activeTab = ref<'episodes' | 'highlights' | 'agent' | 'review'>('episodes')
const isWebFullscreen = ref(false)
const isSidebarCollapsed = ref(false)

function toggleWebFullscreen() {
  isWebFullscreen.value = !isWebFullscreen.value
}

function toggleNativeFullscreen() {
  const container = document.getElementById('widescreen-player-box') || videoRef.value
  if (!container) return
  if (!document.fullscreenElement) {
    if (container.requestFullscreen) {
      container.requestFullscreen()
    } else if ((container as any).webkitRequestFullscreen) {
      (container as any).webkitRequestFullscreen()
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
    }
  }
}

// Continuous Autoplay State (persisted to localStorage)
const isAutoplayEnabled = ref(true)
const showCountdownHud = ref(false)
const countdownSeconds = ref(5)
let countdownTimer: any = null

function initAutoplaySetting() {
  const p1 = localStorage.getItem('cinema_player_autoplay')
  const p2 = localStorage.getItem('cinema_autoplay_enabled')
  if (p1 !== null) {
    isAutoplayEnabled.value = p1 !== 'false'
  } else if (p2 !== null) {
    isAutoplayEnabled.value = p2 !== 'false'
  } else {
    isAutoplayEnabled.value = true
  }
  localStorage.setItem('cinema_player_autoplay', String(isAutoplayEnabled.value))
  localStorage.setItem('cinema_autoplay_enabled', String(isAutoplayEnabled.value))
}

function toggleAutoplay() {
  isAutoplayEnabled.value = !isAutoplayEnabled.value
  localStorage.setItem('cinema_player_autoplay', String(isAutoplayEnabled.value))
  localStorage.setItem('cinema_autoplay_enabled', String(isAutoplayEnabled.value))
}

// Multi-level Favorites State
const isFavorited = ref(false)
const favoriteCount = ref(980)
const showFavoriteModal = ref(false)
const userFolders = ref<FavoriteFolder[]>([])
const selectedFolderIds = ref<string[]>([])
const showNewFolderInput = ref(false)
const newFolderName = ref('')
const newFolderIsPublic = ref(false)
const isSavingFavorite = ref(false)

// Coin Economy & Tipping State (Feature 20)
const showCoinModal = ref(false)
const videoCoinCount = ref(2140)
const userWalletBalance = ref(50)
const userTippedCount = ref(0)
const isTipping = ref(false)
const tipSuccessTip = ref('')

// Playback Rate & Resolution Controls
const currentRate = ref(1.0)
const showSpeedMenu = ref(false)
const currentResolution = ref('1080P 超清')
const showResMenu = ref(false)

let speedMenuTimer: any = null
let resMenuTimer: any = null

function openSpeedMenu() {
  if (speedMenuTimer) clearTimeout(speedMenuTimer)
  showSpeedMenu.value = true
}

function closeSpeedMenuDebounced() {
  if (speedMenuTimer) clearTimeout(speedMenuTimer)
  speedMenuTimer = setTimeout(() => {
    showSpeedMenu.value = false
  }, 250)
}

function openResMenu() {
  if (resMenuTimer) clearTimeout(resMenuTimer)
  showResMenu.value = true
}

function closeResMenuDebounced() {
  if (resMenuTimer) clearTimeout(resMenuTimer)
  resMenuTimer = setTimeout(() => {
    showResMenu.value = false
  }, 250)
}

function setPlaybackRate(rate: number) {
  currentRate.value = rate
  if (videoRef.value) {
    videoRef.value.playbackRate = rate
  }
  showSpeedMenu.value = false
}

function setResolution(res: string) {
  currentResolution.value = res
  showResMenu.value = false
}

const highlights = ref<Array<{ time: number; title: string; desc: string; tag: string }>>([])


const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const progressPercent = ref(0)

const album = ref<VideoAlbum | null>(null)
const episodes = ref<Episode[]>([])
const currentEpisode = ref<Episode | null>(null)
const currentStreamUrl = ref('')
const fallbackStreamUrl = ref('')

// Episode Chunking Logic (1-50, 51-100, 全部)
const selectedChunk = ref('1-50')

const episodeChunks = computed(() => {
  const total = episodes.value.length
  if (total <= 50) return []
  const chunks = []
  const step = 50
  for (let i = 1; i <= total; i += step) {
    const end = Math.min(i + step - 1, total)
    chunks.push({
      label: `${i}-${end}`,
      start: i,
      end: end
    })
  }
  chunks.push({ label: '全部', start: 1, end: total })
  return chunks
})

const visibleEpisodes = computed(() => {
  if (episodeChunks.value.length === 0 || selectedChunk.value === '全部') {
    return episodes.value
  }
  const chunk = episodeChunks.value.find(c => c.label === selectedChunk.value)
  if (!chunk) return episodes.value
  return episodes.value.filter(ep => ep.episode_num >= chunk.start && ep.episode_num <= chunk.end)
})

const isLiked = ref(false)
const likeCount = ref(0)
const resumeToast = ref('')

// Notification Skylight State
const showSkylightDrawer = ref(false)
const unreadCounts = ref<UnreadCountData>({ total: 0, announcements: 0, replies: 0, likes: 0 })

async function fetchUnreadCount() {
  const token = localStorage.getItem('cinema_access_token') || localStorage.getItem('token')
  if (!token) {
    unreadCounts.value = { total: 0, announcements: 0, replies: 0, likes: 0 }
    return
  }
  try {
    const res = await notificationApi.getUnreadCount()
    if (res?.data) {
      unreadCounts.value = res.data
    }
  } catch (err) {
    // ignore
  }
}

// Two-Tier Comments State
const comments = ref<TwoTierCommentItem[]>([])
const commentsTotal = ref(0)
const commentText = ref('')
const isSubmittingComment = ref(false)

const activeReplyRootId = ref('')
const activeReplyTargetUserId = ref('')
const replyTargetName = ref('')
const replyText = ref('')
const isSubmittingReply = ref(false)
const highlightedCommentId = ref('')

function formatNumber(val: number | undefined): string {
  if (!val) return '0'
  if (val >= 10000) {
    return (val / 10000).toFixed(1) + '万'
  }
  return val.toLocaleString()
}

// Danmaku
const danmakuInputText = ref('')
const activeDanmakus = ref<Array<{ id: string; content: string; color: string; track: number; speed: number }>>([])
let danmakuWs: WebSocket | null = null

// Companion Agent State
const agentInputText = ref('')
const isStreamingAgent = ref(false)
const quickPrompts = ref([
  '本集的核心矛盾反转是什么？',
  '为什么主角会在此时出手？',
  '跳到本集最精彩的高能名场面'
])
const agentMessages = ref<Array<{
  sender: 'user' | 'agent'
  text: string
  thought?: string
  targetTime?: number
  timeTag?: string
  scene?: string
  isTyping?: boolean
}>>([
  {
    sender: 'agent',
    text: '您好！我是您的智能短剧伴读 Agent。在观影过程中，您可以随时提问剧情矛盾、人物动机、台词细节或画面感知，我会为您智能解构并提供秒级精准跳转！',
    targetTime: 25,
    timeTag: '00:25',
    scene: '主角登场高能瞬间'
  }
])

// Review Queue
const reviewQueue = ref<Array<{ id: string; target_id: string; violation_reason: string }>>([])

// Auth state
const currentUser = userStore.currentUser
const showAuthModal = ref(false)
const authMode = ref<'login' | 'register'>('login')
const authForm = ref({ username: '', password: '' })

onMounted(async () => {
  initAutoplaySetting()
  await restoreUserSession()
  await fetchUnreadCount()
  const videoId = (route.params.id as string) || (route.query.videoId as string) || 'latest'
  await loadVideoData(videoId)
})

watch(
  () => [route.params.id, route.query.videoId, route.query.episodeId],
  async ([newId, newQId, newEpId]) => {
    const targetId = (newId as string) || (newQId as string)
    if (targetId && targetId !== album.value?.id) {
      await loadVideoData(targetId)
    } else if (newEpId && episodes.value.length > 0) {
      const matched = episodes.value.find(e => e.id === newEpId)
      if (matched && matched.id !== currentEpisode.value?.id) {
        selectEpisode(matched)
      }
    }
  }
)

onUnmounted(() => {
  reportHeartbeat(true)
  closeDanmakuWs()
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
})

async function restoreUserSession() {
  await userStore.refreshProfile()
  await fetchUnreadCount()
}

async function loadVideoData(videoId: string) {
  try {
    const res = await videoApi.getAlbum(videoId)
    if (res?.data) {
      album.value = res.data
      episodes.value = res.data.episodes || []
      if (episodes.value.length > 0) {
        const targetEpId = route.query.episodeId as string
        let chosenEp = episodes.value[0]
        if (targetEpId) {
          const matched = episodes.value.find(e => e.id === targetEpId)
          if (matched) chosenEp = matched
        }
        selectEpisode(chosenEp)
      }
      await checkFavoriteStatus(res.data.id)
    } else {
      setupMockAlbum(videoId)
    }
  } catch (err) {
    console.warn('Failed to load remote album, using local fallback:', err)
    setupMockAlbum(videoId)
  }
}

function setupMockAlbum(videoId: string) {
  album.value = {
    id: videoId,
    title: '【乘风2026】绝美舞台合唱瞬间',
    summary: '中国联通沃盘超清原画直连，视听大厅精选高能剧目。',
    category: '都市逆袭',
    cover_url: 'https://images.unsplash.com/photo-1518173946687-a4c8a383392e?w=800&q=80',
    episodes: [
      { id: 'ef96c393-0bab-43b5-9cf8-b0c8d065b0ba', episode_num: 1, title: '雨爱初相遇', stream_url: `/api/v1/videos/stream/ef96c393-0bab-43b5-9cf8-b0c8d065b0ba`, duration_seconds: 165, transcode_status: 'READY' },
      { id: '25320389-d52b-4696-be3f-6f064df91eb0', episode_num: 2, title: '风暴中的抉择', stream_url: `/api/v1/videos/stream/25320389-d52b-4696-be3f-6f064df91eb0`, duration_seconds: 180, transcode_status: 'READY' },
      { id: '7c819230-1123-4819-bf39-2a90184e9123', episode_num: 3, title: '荣耀与新生', stream_url: `/api/v1/videos/stream/7c819230-1123-4819-bf39-2a90184e9123`, duration_seconds: 195, transcode_status: 'READY' }
    ]
  }
  episodes.value = album.value.episodes || []
  if (episodes.value.length > 0) {
    const targetEpId = route.query.episodeId as string
    let chosenEp = episodes.value[0]
    if (targetEpId) {
      const matched = episodes.value.find(e => e.id === targetEpId)
      if (matched) chosenEp = matched
    }
    selectEpisode(chosenEp)
  }
}

function onVideoError(e: Event) {
  console.warn('Video stream error on current source:', currentStreamUrl.value, e)
  if (fallbackStreamUrl.value && currentStreamUrl.value !== fallbackStreamUrl.value) {
    console.info('Auto-fallback to proxy stream:', fallbackStreamUrl.value)
    currentStreamUrl.value = fallbackStreamUrl.value
    nextTick(() => {
      if (videoRef.value) {
        videoRef.value.load()
        videoRef.value.play().catch(playErr => console.warn('Fallback play warning:', playErr))
      }
    })
  }
}

async function selectEpisode(ep: Episode) {
  // Save heartbeat for previous episode before switching
  if (currentEpisode.value && currentEpisode.value.id !== ep.id) {
    reportHeartbeat(true)
  }
  currentEpisode.value = ep
  fallbackStreamUrl.value = ep.stream_url || `/api/v1/videos/stream/${ep.id}`
  currentStreamUrl.value = fallbackStreamUrl.value

  // Prioritize high-speed cloud direct stream with TTL lease
  videoApi.getDirectStreamUrl(ep.id).then(res => {
    if (res?.data?.direct_url && currentEpisode.value?.id === ep.id) {
      currentStreamUrl.value = res.data.direct_url
      if (res.data.fallback_proxy_url) {
        fallbackStreamUrl.value = res.data.fallback_proxy_url
      }
    }
  }).catch(() => {
    // Keep fallback proxy stream url silently
  })

  initDanmakuWs(ep.id)
  loadEpisodeHighlightsAndPrompts(ep.id)

  // Real watch history auto-resume from URL query or database
  let seekSec = 0
  if (route.query.time && Number(route.query.time) > 0) {
    seekSec = Number(route.query.time)
  } else {
    try {
      const hRes = await videoApi.getHistory(ep.id)
      if (hRes?.data?.progress_seconds && hRes.data.progress_seconds > 0) {
        seekSec = Math.floor(hRes.data.progress_seconds)
      }
    } catch (err) {}
  }

  if (seekSec > 0) {
    nextTick(() => {
      if (videoRef.value) {
        videoRef.value.currentTime = seekSec
      }
    })
    resumeToast.value = `已为您自动续播至上次观看进度 ${formatSeconds(seekSec)}`
    setTimeout(() => {
      resumeToast.value = ''
    }, 4000)
  }

  // Fetch real persistent like status & real two-tier comments from backend
  await loadEpisodeLikeStatus(ep.id)
  await loadEpisodeComments(ep.id)
  await loadEpisodeTipStatus(ep.id)

  // Immediate initial heartbeat report for watch history persistence
  setTimeout(() => {
    reportHeartbeat(true)
  }, 800)
}

async function loadEpisodeHighlightsAndPrompts(episodeId: string) {
  try {
    const res = await videoApi.getHighlights(episodeId)
    if (res?.data && res.data.length > 0) {
      highlights.value = res.data.map((h: any) => ({
        time: h.time,
        timeTag: h.timeTag,
        title: h.title,
        desc: h.desc,
        tag: h.tag || '高能时刻'
      }))
    }
  } catch (e) {
    console.warn('Load highlights failed:', e)
  }

  try {
    const pRes = await videoApi.getQuickPrompts(episodeId)
    if (pRes?.data && pRes.data.length > 0) {
      quickPrompts.value = pRes.data
    }
  } catch (e) {
    console.warn('Load quick prompts failed:', e)
  }
}

const nextEpisode = computed<Episode | null>(() => {
  if (!currentEpisode.value || episodes.value.length === 0) return null
  const currentIdx = episodes.value.findIndex(e => e.id === currentEpisode.value?.id)
  if (currentIdx >= 0 && currentIdx < episodes.value.length - 1) {
    return episodes.value[currentIdx + 1]
  }
  return null
})

function startCountdownAutoplay() {
  if (!nextEpisode.value) return
  showCountdownHud.value = true
  countdownSeconds.value = 5

  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    countdownSeconds.value -= 1
    if (countdownSeconds.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
      executeNextEpisodeImmediately()
    }
  }, 1000)
}

function executeNextEpisodeImmediately() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  showCountdownHud.value = false
  if (nextEpisode.value) {
    switchEpisodeSeamlessly(nextEpisode.value)
  }
}

function cancelCountdownAutoplay() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  showCountdownHud.value = false
  isPlaying.value = false
  if (videoRef.value) {
    videoRef.value.pause()
  }
}

function switchEpisodeSeamlessly(ep: Episode) {
  const savedRate = currentRate.value
  const savedVolume = videoRef.value ? videoRef.value.volume : 1.0
  const savedMuted = videoRef.value ? videoRef.value.muted : false

  selectEpisode(ep)

  nextTick(() => {
    if (videoRef.value) {
      videoRef.value.playbackRate = savedRate
      videoRef.value.volume = savedVolume
      videoRef.value.muted = savedMuted
      videoRef.value.currentTime = 0
      videoRef.value.play().then(() => {
        isPlaying.value = true
        if (videoRef.value) {
          videoRef.value.playbackRate = savedRate
        }
      }).catch(err => {
        console.warn('Playback resume error:', err)
      })
    }
  })
}

function switchEpisode(ep: Episode) {
  switchEpisodeSeamlessly(ep)
}

function togglePlay() {
  if (!videoRef.value) return
  if (videoRef.value.paused) {
    videoRef.value.play().then(() => {
      isPlaying.value = true
      reportHeartbeat(true)
    }).catch(err => {
      console.warn('Autoplay prevented:', err)
    })
  } else {
    videoRef.value.pause()
    isPlaying.value = false
    reportHeartbeat(true)
  }
}

let lastHeartbeatTime = 0
async function reportHeartbeat(force = false) {
  if (!currentEpisode.value?.id) return
  const cur = Math.floor(currentTime.value)
  if (!force && Math.abs(cur - lastHeartbeatTime) < 5) return
  lastHeartbeatTime = cur
  try {
    await videoApi.sendHeartbeat(currentEpisode.value.id, cur)
  } catch (err) {
    // Guest or offline
  }
}

function onTimeUpdate() {
  if (!videoRef.value) return
  currentTime.value = videoRef.value.currentTime
  if (duration.value > 0) {
    progressPercent.value = (currentTime.value / duration.value) * 100
  }
  reportHeartbeat(false)
}

function onLoadedMetadata() {
  if (!videoRef.value) return
  duration.value = videoRef.value.duration || 165
  // Crucial: preserve playbackRate across source switch
  if (currentRate.value) {
    videoRef.value.playbackRate = currentRate.value
  }
}

function onVideoEnded() {
  isPlaying.value = false
  reportHeartbeat(true)
  if (isAutoplayEnabled.value && nextEpisode.value) {
    startCountdownAutoplay()
  }
}

function handleSeekClick(e: MouseEvent) {
  const track = e.currentTarget as HTMLElement
  const rect = track.getBoundingClientRect()
  const clickX = e.clientX - rect.left
  const ratio = Math.max(0, Math.min(1, clickX / rect.width))
  if (videoRef.value && duration.value > 0) {
    videoRef.value.currentTime = ratio * duration.value
  }
}

function jumpToTimestamp(seconds: number | undefined | null, sceneName?: string) {
  if (seconds === undefined || seconds === null) return
  const sec = Number(seconds)
  if (videoRef.value) {
    videoRef.value.currentTime = sec
    videoRef.value.play().then(() => {
      isPlaying.value = true
    }).catch(() => {})
    const m = Math.floor(sec / 60)
    const s = Math.floor(sec % 60)
    const tag = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    resumeToast.value = `已精准跳帧至剧情名场面 [${tag}] ${sceneName ? '· ' + sceneName : ''}`
    setTimeout(() => {
      resumeToast.value = ''
    }, 3500)
  }
}

function formatSeconds(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// WebSocket Danmaku
function initDanmakuWs(episodeId: string) {
  closeDanmakuWs()
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/v1/danmaku/ws/${episodeId}`
  try {
    danmakuWs = new WebSocket(wsUrl)
    danmakuWs.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'danmaku') {
          pushFlyingDanmaku(msg.content, msg.color || '#FFFFFF')
        }
      } catch (e) {}
    }
  } catch (err) {
    console.warn('WebSocket connection not supported in current mode, simulated locally.')
  }
}

function closeDanmakuWs() {
  if (danmakuWs) {
    danmakuWs.close()
    danmakuWs = null
  }
}

function sendDanmaku() {
  const text = danmakuInputText.value.trim()
  if (!text) return

  // DFA check simulation for sensitive words
  if (text.includes('微信') || text.includes('代理') || text.includes('刷单')) {
    reviewQueue.value.push({
      id: String(Date.now()),
      target_id: text,
      violation_reason: '敏感广告营销词命中'
    })
    alert('【内容风控提醒】您发送的内容包含敏感广告词，已被机审系统拦截。')
    danmakuInputText.value = ''
    return
  }

  if (danmakuWs && danmakuWs.readyState === WebSocket.OPEN) {
    danmakuWs.send(JSON.stringify({ content: text, color: '#FFFFFF', time_offset: currentTime.value }))
  } else {
    pushFlyingDanmaku(text, '#FFFFFF')
  }
  danmakuInputText.value = ''
}

function pushFlyingDanmaku(content: string, color: string) {
  const bullet = {
    id: String(Math.random()),
    content,
    color,
    track: Math.floor(Math.random() * 4),
    speed: 6 + Math.random() * 3
  }
  activeDanmakus.value.push(bullet)
  setTimeout(() => {
    activeDanmakus.value = activeDanmakus.value.filter(b => b.id !== bullet.id)
  }, bullet.speed * 1000)
}

// Real Persistent Likes
async function loadEpisodeLikeStatus(episodeId: string) {
  try {
    const res = await videoApi.getLikeStatus(episodeId)
    if (res?.data) {
      isLiked.value = !!res.data.is_liked
      likeCount.value = res.data.like_count ?? 0
    }
  } catch (err) {
    console.warn('Failed to load like status:', err)
  }
}

async function handleToggleLike() {
  if (!currentUser.value) {
    openAuthModal('点赞需要先登录用户账号')
    return
  }
  if (!currentEpisode.value?.id) return
  try {
    const res = await videoApi.toggleLike(currentEpisode.value.id)
    if (res?.data) {
      isLiked.value = !!res.data.is_liked
      likeCount.value = res.data.like_count ?? (isLiked.value ? likeCount.value + 1 : Math.max(0, likeCount.value - 1))
    }
  } catch (err: any) {
    console.warn('Failed to toggle like:', err)
    alert(err?.response?.data?.detail || '点赞操作失败')
  }
}

async function loadEpisodeTipStatus(episodeId: string) {
  try {
    const res = await videoApi.getTipStatus(episodeId)
    if (res?.data) {
      userTippedCount.value = res.data.tipped_count ?? 0
      videoCoinCount.value = res.data.video_coin_count ?? 2140
    }
  } catch (err) {
    console.warn('Failed to load tip status:', err)
  }
}

async function handleCoin() {
  if (!currentUser.value) {
    openAuthModal('投币支持需要先登录用户账号')
    return
  }
  showCoinModal.value = true
  tipSuccessTip.value = ''
  try {
    const wRes = await userApi.getCoinWallet()
    if (wRes?.data) {
      userWalletBalance.value = wRes.data.balance ?? 50
    }
  } catch (err) {
    console.warn('Failed to load wallet balance:', err)
  }
  if (currentEpisode.value?.id) {
    await loadEpisodeTipStatus(currentEpisode.value.id)
  }
}

async function executeTip(amount: 1 | 2) {
  if (!currentEpisode.value?.id) return
  if (userTippedCount.value + amount > 2) {
    alert(`每部短剧每人最多打赏 2 枚金币，您已打赏 ${userTippedCount.value} 枚`)
    return
  }
  if (userWalletBalance.value < amount) {
    alert(`金币余额不足，需要 ${amount} 金币，当前余额为 ${userWalletBalance.value}`)
    return
  }
  isTipping.value = true
  try {
    const res = await videoApi.tipVideo(currentEpisode.value.id, { coin_amount: amount })
    if (res?.data) {
      userWalletBalance.value = res.data.wallet_balance
      videoCoinCount.value = res.data.video_coin_count
      userTippedCount.value = res.data.tipped_count
      tipSuccessTip.value = `🪙 感谢支持！成功打赏 ${amount} 枚金币！全站热度值 +${amount * 10}`
      setTimeout(() => {
        showCoinModal.value = false
      }, 1500)
    }
  } catch (err: any) {
    alert(err?.response?.data?.detail || err?.message || '投币失败')
  } finally {
    isTipping.value = false
  }
}

async function checkFavoriteStatus(videoId: string) {
  if (!currentUser.value) {
    isFavorited.value = false
    return
  }
  try {
    const res: any = await favoritesApi.getStatus(videoId)
    const data = res?.data || res
    isFavorited.value = !!data?.is_favorited
    selectedFolderIds.value = data?.folder_ids || []
  } catch (e) {
    console.warn('Check favorite status error:', e)
  }
}

async function handleFavoriteClick() {
  if (!currentUser.value) {
    openAuthModal('收藏短剧需要先登录用户账号')
    return
  }
  showFavoriteModal.value = true
  await loadUserFolders()
  if (album.value?.id) {
    await checkFavoriteStatus(album.value.id)
  }
}

function handleFavorite() {
  handleFavoriteClick()
}

async function loadUserFolders() {
  try {
    const res: any = await favoritesApi.getFolders()
    const data = res?.data || res
    userFolders.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.warn('Load user folders error:', e)
  }
}

function toggleFolderSelection(folderId: string) {
  const idx = selectedFolderIds.value.indexOf(folderId)
  if (idx >= 0) {
    selectedFolderIds.value.splice(idx, 1)
  } else {
    selectedFolderIds.value.push(folderId)
  }
}

async function handleCreateFolderInModal() {
  const name = newFolderName.value.trim()
  if (!name) return
  try {
    const res: any = await favoritesApi.createFolder({
      name,
      is_public: newFolderIsPublic.value
    })
    const created = res?.data || res
    if (created && created.id) {
      userFolders.value.push(created)
      selectedFolderIds.value.push(created.id)
      newFolderName.value = ''
      showNewFolderInput.value = false
    }
  } catch (err: any) {
    alert(err?.response?.data?.detail || '创建收藏夹失败，请重试')
  }
}

async function handleQuickDefaultSave() {
  if (!album.value?.id) return
  try {
    const res: any = await favoritesApi.quickDefaultToggle(album.value.id)
    const data = res?.data || res
    isFavorited.value = !!data?.is_favorited
    favoriteCount.value += isFavorited.value ? 1 : -1
    resumeToast.value = data?.message || (isFavorited.value ? '已存入默认收藏夹' : '已从默认收藏夹移出')
    setTimeout(() => { resumeToast.value = '' }, 3000)
    showFavoriteModal.value = false
  } catch (e: any) {
    alert(e?.response?.data?.detail || '快捷收藏失败')
  }
}

async function handleSaveToSelectedFolders() {
  if (!album.value?.id) return
  isSavingFavorite.value = true
  try {
    if (selectedFolderIds.value.length === 0) {
      await favoritesApi.removeItem(album.value.id)
      isFavorited.value = false
      favoriteCount.value = Math.max(0, favoriteCount.value - 1)
      resumeToast.value = '已从所有收藏夹移出'
    } else {
      await favoritesApi.addItem({
        video_id: album.value.id,
        folder_ids: selectedFolderIds.value
      })
      isFavorited.value = true
      favoriteCount.value += 1
      resumeToast.value = `已成功保存至 ${selectedFolderIds.value.length} 个收藏夹`
    }
    setTimeout(() => { resumeToast.value = '' }, 3000)
    showFavoriteModal.value = false
  } catch (e: any) {
    alert(e?.response?.data?.detail || '保存收藏失败')
  } finally {
    isSavingFavorite.value = false
  }
}

function handleShare() {
  navigator.clipboard?.writeText(window.location.href)
  alert('↗️ 播放链接已复制到剪贴板，快分享给好友一起追剧吧！')
}

// Real Two-Tier Comments Operations
async function loadEpisodeComments(episodeId: string) {
  try {
    const res = await videoApi.getComments(episodeId)
    if (res?.data) {
      comments.value = res.data.items || []
      commentsTotal.value = res.data.total ?? comments.value.length
    }
  } catch (err) {
    console.warn('Failed to load comments:', err)
  }

  // Handle route.query.commentId highlighting
  const targetCommentId = route.query.commentId as string
  if (targetCommentId) {
    highlightedCommentId.value = targetCommentId
    nextTick(() => {
      const el = document.getElementById('comment-' + targetCommentId)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    })
    setTimeout(() => {
      highlightedCommentId.value = ''
    }, 4000)
  }
}

async function submitComment() {
  if (!currentUser.value) {
    openAuthModal('发表评论需要先登录账号')
    return
  }
  const text = commentText.value.trim()
  if (!text) return
  if (!currentEpisode.value?.id) return

  isSubmittingComment.value = true
  try {
    const res = await videoApi.postComment(currentEpisode.value.id, { content: text })
    if (res?.data) {
      commentText.value = ''
      await loadEpisodeComments(currentEpisode.value.id)
    }
  } catch (err: any) {
    console.warn('Failed to submit comment:', err)
    alert(err?.response?.data?.detail || '发表评论失败，请重试')
  } finally {
    isSubmittingComment.value = false
  }
}

function toggleReplyInput(rootId: string, targetUserId?: string, targetName?: string) {
  if (!currentUser.value) {
    openAuthModal('回复评论需要先登录账号')
    return
  }
  if (activeReplyRootId.value === rootId && activeReplyTargetUserId.value === targetUserId) {
    cancelReply()
    return
  }
  activeReplyRootId.value = rootId
  activeReplyTargetUserId.value = targetUserId || ''
  replyTargetName.value = targetName || '用户'
  replyText.value = ''
}

function cancelReply() {
  activeReplyRootId.value = ''
  activeReplyTargetUserId.value = ''
  replyTargetName.value = ''
  replyText.value = ''
}

async function submitReply(rootId: string) {
  if (!currentUser.value) {
    openAuthModal('回复评论需要先登录账号')
    return
  }
  const text = replyText.value.trim()
  if (!text) return
  if (!currentEpisode.value?.id) return

  isSubmittingReply.value = true
  try {
    await videoApi.postComment(currentEpisode.value.id, {
      content: text,
      root_id: rootId,
      parent_id: rootId,
      reply_to_user_id: activeReplyTargetUserId.value || undefined
    })
    cancelReply()
    await loadEpisodeComments(currentEpisode.value.id)
  } catch (err: any) {
    console.warn('Failed to submit reply:', err)
    alert(err?.response?.data?.detail || '回复发表失败，请重试')
  } finally {
    isSubmittingReply.value = false
  }
}

async function handleToggleCommentLike(comment: TwoTierCommentItem | CommentReplyItem) {
  if (!currentUser.value) {
    openAuthModal('点赞评论需要先登录账号')
    return
  }
  try {
    const res = await videoApi.toggleCommentLike(comment.id)
    if (res?.data) {
      comment.is_liked = !!res.data.is_liked
      comment.like_count = res.data.like_count
    }
  } catch (err: any) {
    console.warn('Failed to toggle comment like:', err)
  }
}

// Companion interaction with SSE Streaming & Timeline RAG
async function sendAgentQuestion() {
  if (isStreamingAgent.value) return
  const q = agentInputText.value.trim()
  if (!q) return

  agentMessages.value.push({ sender: 'user', text: q })
  agentInputText.value = ''
  scrollToBottom()

  // Add agent placeholder message
  const agentMsgIndex = agentMessages.value.length
  agentMessages.value.push({
    sender: 'agent',
    text: '',
    thought: '',
    targetTime: undefined,
    timeTag: undefined,
    scene: undefined,
    isTyping: true
  })
  scrollToBottom()
  isStreamingAgent.value = true

  const currentSec = videoRef.value ? videoRef.value.currentTime : 0
  const episodeId = currentEpisode.value?.id || 'ef96c393-0bab-43b5-9cf8-b0c8d065b0ba'

  try {
    await videoApi.streamAgentChat({
      episodeId,
      question: q,
      currentVideoTime: currentSec,
      onThought: (th: string) => {
        agentMessages.value[agentMsgIndex].thought = (agentMessages.value[agentMsgIndex].thought || '') + th
        scrollToBottom()
      },
      onToken: (token: string) => {
        agentMessages.value[agentMsgIndex].text += token
        scrollToBottom()
      },
      onActionCard: (card: ActionCardData) => {
        agentMessages.value[agentMsgIndex].targetTime = card.timestamp
        agentMessages.value[agentMsgIndex].timeTag = card.time_tag
        agentMessages.value[agentMsgIndex].scene = card.title
      },
      onDone: (data) => {
        agentMessages.value[agentMsgIndex].isTyping = false
        if (agentMessages.value[agentMsgIndex].targetTime === undefined) {
          agentMessages.value[agentMsgIndex].targetTime = data.target_time
          agentMessages.value[agentMsgIndex].timeTag = data.time_tag
        }
        isStreamingAgent.value = false
        scrollToBottom()
      },
      onError: (err) => {
        console.warn('Stream chat error:', err)
        agentMessages.value[agentMsgIndex].isTyping = false
        isStreamingAgent.value = false
        if (!agentMessages.value[agentMsgIndex].text) {
          agentMessages.value[agentMsgIndex].text = `【系统异常】` + (err?.message || '伴读服务调用失败，请检查模型服务状态。')
        }
      }
    })
  } catch (err: any) {
    agentMessages.value[agentMsgIndex].isTyping = false
    isStreamingAgent.value = false
    if (!agentMessages.value[agentMsgIndex].text) {
      agentMessages.value[agentMsgIndex].text = `【网络中断】无法连接至伴读服务，请稍后重试。`
    }
  } finally {
    agentMessages.value[agentMsgIndex].isTyping = false
    isStreamingAgent.value = false
  }
}

function askQuickPrompt(p: string) {
  agentInputText.value = p
  sendAgentQuestion()
}

function scrollToBottom() {
  nextTick(() => {
    if (chatScrollRef.value) {
      chatScrollRef.value.scrollTop = chatScrollRef.value.scrollHeight
    }
  })
}


function parseTimeTagToSeconds(tag: string): number {
  const parts = tag.split(':')
  if (parts.length === 2) {
    return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10)
  }
  return 0
}

function jumpToTimeTag(timeTag: string) {
  const sec = parseTimeTagToSeconds(timeTag)
  jumpToTimestamp(sec, `时间胶囊 [${timeTag}]`)
}

function parseMessageSegments(text: string): Array<{ isTimeTag: boolean; content: string; timeTag?: string }> {
  if (!text) return []
  const regex = /\[(\d{1,2}:\d{2})\]/g
  const segments: Array<{ isTimeTag: boolean; content: string; timeTag?: string }> = []
  let lastIndex = 0
  let match: RegExpExecArray | null
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ isTimeTag: false, content: text.substring(lastIndex, match.index) })
    }
    segments.push({ isTimeTag: true, content: match[0], timeTag: match[1] })
    lastIndex = regex.lastIndex
  }
  if (lastIndex < text.length) {
    segments.push({ isTimeTag: false, content: text.substring(lastIndex) })
  }
  return segments
}

// Review moderation
function handleReviewDecision(id: string, decision: 'APPROVED' | 'REJECTED') {
  reviewQueue.value = reviewQueue.value.filter(r => r.id !== id)
  alert(`审核裁决完成：该记录已标记为【${decision === 'APPROVED' ? '放行通过' : '确认违规下架'}】`)
}

// Role switch
async function switchRole(roleName: string) {
  const accounts: Record<string, { u: string; p: string }> = {
    USER: { u: 'user', p: 'user123' },
    CREATOR: { u: 'creator', p: 'creator123' },
    REVIEWER: { u: 'reviewer', p: 'reviewer123' },
    ADMIN: { u: 'admin', p: 'admin123' }
  }
  const acc = accounts[roleName]
  if (!acc) return
  try {
    const res: any = await authApi.login({ username: acc.u, password: acc.p })
    const token = res?.access_token || res?.data?.access_token
    const userObj = res?.user || res?.data?.user
    if (token && userObj) {
      userStore.setUser(userObj, token)
    }
  } catch (e) {}
}

function getRoleLabel(role: string): string {
  const map: Record<string, string> = {
    USER: '普通用户',
    CREATOR: '创作者',
    REVIEWER: '审核员',
    ADMIN: '管理员'
  }
  return map[role] || role
}

function openAuthModal(hint = '') {
  showAuthModal.value = true
}

function handleLogout() {
  userStore.clearUser()
  window.location.href = '/'
}

async function handleAuthSubmit() {
  try {
    const res: any = await authApi.login({
      username: authForm.value.username.trim(),
      password: authForm.value.password.trim()
    })
    const token = res?.access_token || res?.data?.access_token
    const userObj = res?.user || res?.data?.user
    if (token && userObj) {
      userStore.setUser(userObj, token)
      showAuthModal.value = false
    } else {
      alert('登录失败，请检查账号密码')
    }
  } catch (e) {
    alert('登录失败，请检查账号密码')
  }
}
</script>

<style scoped>
/* ========================================================================== */
/* Apple HIG Unified Dual-Mode Player Styling                                 */
/* ========================================================================== */
.apple-player-page {
  min-height: 100vh;
  background-color: var(--apple-bg);
  color: var(--apple-text-primary);
  display: flex;
  flex-direction: column;
}

/* Header */
.player-global-header {
  position: sticky;
  top: 0;
  left: 0;
  width: 100%;
  height: 60px;
  background: rgba(18, 18, 20, 0.88);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  z-index: 100;
}

.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.apple-back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;
  color: var(--apple-text-primary);
  font-size: 13px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: var(--apple-radius-pill);
  background: rgba(0, 0, 0, 0.04);
  transition: all var(--apple-transition-fast);
}

.apple-back-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  transform: scale(1.02);
}

.back-svg {
  width: 16px;
  height: 16px;
}

.header-divider {
  color: var(--apple-text-tertiary);
}

.drama-headline-chip {
  display: flex;
  align-items: center;
  gap: 8px;
}

.drama-tag {
  background: rgba(0, 113, 227, 0.1);
  color: var(--apple-blue);
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--apple-radius-pill);
}

.drama-title-text {
  font-size: 14px;
  font-weight: 700;
}

.episode-pill {
  font-size: 12px;
  color: var(--apple-text-tertiary);
}

/* Center Dual-Mode Switcher */
.apple-mode-switcher-capsule {
  display: flex;
  background: var(--apple-input-bg);
  padding: 3px;
  border-radius: var(--apple-radius-pill);
  gap: 2px;
}

.mode-switch-btn {
  border: none;
  background: transparent;
  color: var(--apple-text-secondary);
  font-size: 13px;
  font-weight: 500;
  padding: 6px 14px;
  border-radius: var(--apple-radius-pill);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all var(--apple-transition-fast);
}

.mode-switch-btn:hover {
  color: var(--apple-text-primary);
}

.mode-switch-btn.active {
  background: #FFFFFF;
  color: var(--apple-text-primary);
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.mode-icon {
  width: 15px;
  height: 15px;
}

/* Header Right */
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.role-segment-pill {
  display: flex;
  background: var(--apple-input-bg);
  padding: 2px;
  border-radius: var(--apple-radius-pill);
  gap: 2px;
}

.role-mini-btn {
  border: none;
  background: transparent;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: var(--apple-radius-pill);
  color: var(--apple-text-secondary);
  cursor: pointer;
}

.role-mini-btn.active {
  background: #FFFFFF;
  color: var(--apple-text-primary);
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.user-chip-mini {
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  background: rgba(0, 0, 0, 0.04) !important;
  padding: 4px 10px 4px 5px !important;
  border-radius: var(--apple-radius-pill) !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  text-decoration: none !important;
  color: inherit !important;
  cursor: pointer;
  transition: all 0.2s ease;
  line-height: normal !important;
}

[data-theme="dark"] .user-chip-mini {
  background: rgba(255, 255, 255, 0.08) !important;
  border-color: rgba(255, 255, 255, 0.12) !important;
  color: var(--apple-text-primary) !important;
}

.avatar-mini {
  width: 24px !important;
  height: 24px !important;
  border-radius: 50% !important;
  object-fit: cover;
  flex-shrink: 0 !important;
}

.user-info-text {
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
  white-space: nowrap !important;
  line-height: 1 !important;
}

.user-name-mini {
  font-size: 12px !important;
  font-weight: 600 !important;
  max-width: 105px !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  color: #1d1d1f !important;
}

[data-theme="dark"] .user-name-mini {
  color: #f5f5f7 !important;
}

.user-role-badge-mini {
  font-size: 10px !important;
  font-weight: 600 !important;
  padding: 2px 7px !important;
  border-radius: 10px !important;
  background: rgba(0, 113, 227, 0.08) !important;
  color: #0071e3 !important;
  border: 1px solid rgba(0, 113, 227, 0.22) !important;
  white-space: nowrap !important;
  line-height: 1 !important;
}

[data-theme="dark"] .user-role-badge-mini {
  background: rgba(0, 113, 227, 0.18) !important;
  color: #5ac8fa !important;
  border-color: rgba(0, 113, 227, 0.35) !important;
}

.user-role-badge-mini.creator {
  background: rgba(52, 199, 89, 0.1) !important;
  color: #248a3d !important;
  border-color: rgba(52, 199, 89, 0.28) !important;
}

.user-role-badge-mini.admin {
  background: rgba(255, 45, 85, 0.1) !important;
  color: #d70035 !important;
  border-color: rgba(255, 45, 85, 0.28) !important;
}

.user-role-badge-mini.reviewer {
  background: rgba(255, 149, 0, 0.1) !important;
  color: #c97500 !important;
  border-color: rgba(255, 149, 0, 0.28) !important;
}

.logout-link-mini {
  border: none;
  background: transparent;
  color: var(--apple-text-tertiary);
  font-size: 12px;
  cursor: pointer;
  margin-left: 8px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

.logout-link-mini:hover {
  color: #ff3b30;
  background: rgba(255, 59, 48, 0.08);
}

.mini-btn {
  padding: 5px 12px;
  font-size: 12px;
}

/* Auto-resume toast */
.resume-toast-capsule {
  position: fixed;
  top: 76px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(29, 29, 31, 0.88);
  backdrop-filter: blur(16px);
  color: #FFFFFF;
  padding: 10px 20px;
  border-radius: var(--apple-radius-pill);
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  font-size: 13px;
  z-index: 200;
}

/* ========================================================================== */
/* Unified Stage Layout (Responsive Morphing between 16:9 and 9:16)          */
/* ========================================================================== */
.theater-stage-container {
  max-width: 1280px;
  margin: 24px auto 40px auto;
  padding: 0 24px;
  display: grid;
  gap: 28px;
  transition: all 0.4s var(--apple-ease);
}

/* MODE A: 16:9 Landscape Layout */
.stage-landscape {
  grid-template-columns: 1fr 360px;
}

.stage-landscape .video-viewport-box {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 24px;
  background: #000000;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.12);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* MODE B: 9:16 Portrait Capsule Layout */
.stage-portrait {
  grid-template-columns: 400px minmax(360px, 1fr);
  justify-content: center;
  align-items: start;
}

.stage-portrait .theater-player-column {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 400px;
}

.stage-portrait .video-viewport-box {
  width: 380px;
  max-width: 100%;
  height: 675px;
  margin: 0 auto;
  border-radius: 40px;
  background: #000000;
  box-shadow: 0 28px 70px rgba(0, 0, 0, 0.25), 0 0 0 8px #1d1d1f;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.stage-portrait .video-meta-card {
  width: 100%;
  max-width: 380px;
  margin-top: 16px;
  padding: 16px;
}

.stage-portrait .comments-bento-card {
  width: 100%;
  max-width: 380px;
  margin-top: 16px;
}

.stage-portrait .action-pills-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}

.stage-portrait .apple-action-pill {
  padding: 8px 4px;
  justify-content: center;
  font-size: 11px;
  gap: 4px;
}

.mobile-notch-bar {
  height: 32px;
  background: #1d1d1f;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  color: #86868b;
  font-size: 10px;
  font-weight: 600;
  z-index: 10;
}

.notch-speaker {
  width: 48px;
  height: 4px;
  border-radius: 4px;
  background: #333336;
}

/* Video Wrapper & Element */
.video-media-wrapper {
  flex: 1;
  position: relative;
  background: #000000;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.core-video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.stage-portrait .core-video-element {
  object-fit: cover;
}

/* Danmaku Screen Layer */
.danmaku-screen-layer {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.danmaku-flying-bullet {
  position: absolute;
  right: -100%;
  white-space: nowrap;
  font-size: 15px;
  font-weight: 600;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
  animation-name: flyBullet;
  animation-timing-function: linear;
  animation-iteration-count: 1;
  animation-fill-mode: forwards;
}

@keyframes flyBullet {
  from { right: -100px; transform: translateX(0); }
  to { right: 100%; transform: translateX(-100%); }
}

.play-splash-circle {
  position: absolute;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFFFFF;
}

.splash-svg {
  width: 32px;
  height: 32px;
}

/* In-Player Controls */
.player-controls-bar {
  background: linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.85) 100%);
  padding: 8px 16px 14px 16px;
  color: #FFFFFF;
  z-index: 10;
}

.progress-track-wrapper {
  height: 14px;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.progress-bar-bg {
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  position: relative;
  transition: height 0.2s;
}

.progress-track-wrapper:hover .progress-bar-bg {
  height: 6px;
}

.progress-bar-fill {
  height: 100%;
  background: var(--apple-blue);
  border-radius: 2px;
  position: relative;
}

.progress-handle {
  position: absolute;
  right: -5px;
  top: -3px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #FFFFFF;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}

.controls-action-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 6px;
  gap: 12px;
}

.ctrl-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.icon-ctrl-btn {
  background: transparent;
  border: none;
  color: #FFFFFF;
  cursor: pointer;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ctrl-svg {
  width: 22px;
  height: 22px;
}

.timestamp-display {
  font-size: 12px;
  color: #D1D1D6;
  font-variant-numeric: tabular-nums;
}

/* Danmaku Input */
.danmaku-send-box {
  flex: 1;
  max-width: 360px;
  display: flex;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
  border-radius: var(--apple-radius-pill);
  padding: 2px 4px 2px 12px;
}

.danmaku-pill-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #FFFFFF;
  font-size: 12px;
}

.danmaku-pill-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.btn-danmaku-send {
  background: var(--bili-pink);
  border: none;
  color: #FFFFFF;
  font-size: 11px;
  font-weight: 600;
  border-radius: var(--apple-radius-pill);
  padding: 4px 12px;
  cursor: pointer;
  transition: all var(--apple-transition-fast);
}

.btn-danmaku-send:hover {
  background: #f85b88;
  transform: scale(1.02);
}

.mode-quick-toggle {
  background: rgba(255, 255, 255, 0.25);
  border: none;
  color: #FFFFFF;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: var(--apple-radius-pill);
  cursor: pointer;
}

/* Playback Speed and Resolution Menus */
.speed-menu-wrap,
.resolution-menu-wrap {
  position: relative;
  display: inline-block;
}

.pill-ctrl-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #FFFFFF;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--apple-radius-pill);
  cursor: pointer;
  transition: all 0.2s ease;
}

.pill-ctrl-btn:hover {
  background: rgba(255, 255, 255, 0.35);
  transform: scale(1.04);
}

.dropdown-popover-glass {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  background: rgba(20, 20, 24, 0.94);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 14px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
  z-index: 99;
  min-width: 84px;
}

/* Safety hit bridge so cursor traversing between button and menu never triggers mouseleave */
.dropdown-popover-glass::after {
  content: '';
  position: absolute;
  top: 100%;
  left: -12px;
  right: -12px;
  height: 16px;
  background: transparent;
}

.popover-item {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  color: #d1d5db;
  border-radius: 8px;
  cursor: pointer;
  text-align: center;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.popover-item:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #FFFFFF;
}

.popover-item.active {
  background: var(--bili-pink);
  color: #FFFFFF;
  font-weight: 700;
}

/* ========================================================================== */
/* Video Metadata & Actions                                                   */
/* ========================================================================== */
.video-meta-card {
  background: var(--liquid-glass-bg);
  border: 1px solid var(--liquid-glass-border);
  backdrop-filter: var(--liquid-glass-blur);
  -webkit-backdrop-filter: var(--liquid-glass-blur);
  border-radius: 24px;
  padding: 24px;
  margin-top: 20px;
  box-shadow: var(--liquid-glass-shadow);
}

.meta-titles-row {
  margin-bottom: 16px;
}

.video-main-heading {
  margin: 0 0 6px 0;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.video-stats-labels {
  display: flex;
  gap: 14px;
  font-size: 13px;
  color: var(--apple-text-tertiary);
}

.action-pills-row {
  display: flex;
  gap: 10px;
}

.apple-action-pill {
  background: var(--apple-gray-btn);
  border: none;
  color: var(--apple-text-primary);
  font-size: 13px;
  font-weight: 600;
  padding: 8px 18px;
  border-radius: var(--apple-radius-pill);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all var(--apple-transition-fast);
}

.apple-action-pill:hover {
  background: var(--apple-gray-btn-hover);
  transform: scale(1.02);
}

.apple-action-pill.active {
  background: #ffebee;
  color: #e53935;
}

/* Comments Bento Card */
.comments-bento-card {
  background: var(--liquid-glass-bg);
  border: 1px solid var(--liquid-glass-border);
  backdrop-filter: var(--liquid-glass-blur);
  -webkit-backdrop-filter: var(--liquid-glass-blur);
  border-radius: 24px;
  padding: 24px;
  margin-top: 20px;
  box-shadow: var(--liquid-glass-shadow);
}

.comments-card-header h3 {
  margin: 0 0 16px 0;
  font-size: 17px;
  font-weight: 700;
}

.comment-compose-box {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.compose-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  flex-shrink: 0;
}

.compose-input-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
}

.comment-textarea {
  width: 100%;
  background: var(--apple-input-bg);
  border: none;
  outline: none;
  border-radius: 14px;
  padding: 12px 14px;
  font-size: 13px;
  color: var(--apple-text-primary);
  font-family: inherit;
  resize: vertical;
}

.comment-textarea:focus {
  background: #FFFFFF;
  box-shadow: 0 0 0 3px rgba(251, 114, 153, 0.25);
}

.comment-bubble-item {
  display: flex;
  gap: 12px;
  padding: 14px 0;
  border-top: 1px solid var(--apple-hairline);
}

.commenter-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
}

.comment-author-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.comment-name {
  font-size: 13px;
  font-weight: 600;
}

.comment-time {
  font-size: 11px;
  color: var(--apple-text-tertiary);
}

.comment-content-text {
  margin: 0;
  font-size: 13px;
  color: var(--apple-text-secondary);
  line-height: 1.5;
}

/* ========================================================================== */
/* Sidebar Column (Episodes, Highlights, Companion, Review)                   */
/* ========================================================================== */
.theater-sidebar-column {
  background: var(--liquid-glass-bg);
  border: 1px solid var(--liquid-glass-border);
  backdrop-filter: var(--liquid-glass-blur);
  -webkit-backdrop-filter: var(--liquid-glass-blur);
  border-radius: 24px;
  padding: 20px;
  box-shadow: var(--liquid-glass-shadow);
  display: flex;
  flex-direction: column;
  height: fit-content;
}

.sidebar-tab-segment {
  display: flex;
  background: var(--apple-input-bg);
  padding: 3px;
  border-radius: var(--apple-radius-pill);
  gap: 2px;
  margin-bottom: 16px;
}

.side-tab-btn {
  flex: 1;
  border: none;
  background: transparent;
  padding: 7px 0;
  font-size: 12px;
  font-weight: 500;
  color: var(--apple-text-secondary);
  border-radius: var(--apple-radius-pill);
  cursor: pointer;
  transition: all var(--apple-transition-fast);
}

.side-tab-btn.active {
  background: #FFFFFF;
  color: var(--bili-pink);
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(251, 114, 153, 0.16);
  border: 1px solid rgba(251, 114, 153, 0.2);
}

/* Episode Chunk Tabs & Scroll Viewport */
.episode-chunk-tabs-row {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 8px;
  margin-bottom: 12px;
}
.episode-chunk-tabs-row::-webkit-scrollbar {
  height: 4px;
}
.episode-chunk-tabs-row::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.25);
  border-radius: 4px;
}
[data-theme="dark"] .episode-chunk-tabs-row::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.25);
}
.chunk-pill-btn {
  background: var(--apple-input-bg, rgba(255, 255, 255, 0.08));
  border: 1px solid var(--apple-card-border, rgba(255, 255, 255, 0.12));
  color: var(--apple-text-secondary, #a1a1aa);
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}
.chunk-pill-btn:hover {
  color: #FFFFFF;
  background: rgba(255, 255, 255, 0.16);
}
.chunk-pill-btn.active {
  background: var(--bili-pink, #fb7299);
  color: #FFFFFF;
  border-color: var(--bili-pink, #fb7299);
  box-shadow: 0 2px 8px rgba(251, 114, 153, 0.3);
}

.episodes-scroll-window {
  max-height: 480px;
  overflow-y: auto;
  padding-right: 4px;
}
.episodes-scroll-window::-webkit-scrollbar {
  width: 5px;
}
.episodes-scroll-window::-webkit-scrollbar-track {
  background: transparent;
}
.episodes-scroll-window::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.25);
  border-radius: 10px;
}
[data-theme="dark"] .episodes-scroll-window::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.25);
}

/* Episodes Grid */
.episodes-bento-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.episode-tile-btn {
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid transparent;
  border-radius: 14px;
  padding: 12px;
  text-align: left;
  cursor: pointer;
  transition: all var(--apple-transition-fast);
}

.episode-tile-btn:hover {
  background: rgba(251, 114, 153, 0.05);
  border-color: rgba(251, 114, 153, 0.2);
  transform: scale(1.02);
}

.episode-tile-btn.active {
  background: rgba(251, 114, 153, 0.08);
  border-color: var(--bili-pink);
}

.ep-num-line {
  font-size: 12px;
  font-weight: 700;
  color: var(--bili-pink);
}

.ep-title-sub {
  font-size: 12px;
  color: var(--apple-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

/* High-Energy Highlights Flow */
.panel-highlights-wrap {
  display: flex;
  flex-direction: column;
}

.highlights-flow-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.highlight-card-item {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 12px 14px;
  cursor: pointer;
  transition: all var(--apple-transition-fast);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.highlight-card-item:hover {
  background: #FFFFFF;
  border-color: rgba(251, 114, 153, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(251, 114, 153, 0.12);
}

.highlight-time-badge {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.highlight-time-badge .time-text {
  font-size: 12px;
  font-weight: 700;
  color: var(--bili-pink);
  background: rgba(251, 114, 153, 0.1);
  padding: 2px 7px;
  border-radius: 6px;
}

.highlight-time-badge .jump-hint {
  font-size: 11px;
  color: var(--apple-text-tertiary);
  font-weight: 600;
}

.highlight-card-item:hover .jump-hint {
  color: var(--bili-pink);
}

.highlight-title-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.highlight-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--apple-text-primary);
}

.highlight-tag-pill {
  font-size: 10px;
  color: var(--bili-blue);
  background: rgba(0, 174, 236, 0.1);
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.highlight-desc {
  margin: 0;
  font-size: 12px;
  color: var(--apple-text-secondary);
  line-height: 1.45;
}

/* Agent Companion Dock */
.panel-agent-dock {
  display: flex;
  flex-direction: column;
  height: 520px;
}

.agent-quick-prompts-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.quick-prompt-pill {
  border: none;
  background: var(--apple-input-bg);
  color: var(--apple-text-secondary);
  font-size: 11px;
  padding: 4px 10px;
  border-radius: var(--apple-radius-pill);
  cursor: pointer;
  transition: all var(--apple-transition-fast);
}

.quick-prompt-pill:hover {
  background: var(--apple-gray-btn-hover);
  color: var(--apple-text-primary);
}

.agent-chat-messages-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 4px;
  margin-bottom: 14px;
}

.chat-bubble-row {
  display: flex;
  gap: 10px;
}

.bubble-avatar-squircle {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: rgba(0, 113, 227, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.bubble-content-card {
  flex: 1;
  background: var(--apple-input-bg);
  border-radius: 16px;
  padding: 10px 14px;
}

.bubble-sender-name {
  font-size: 11px;
  font-weight: 600;
  color: var(--apple-text-tertiary);
  margin-bottom: 4px;
}

.bubble-body-text {
  font-size: 13px;
  line-height: 1.5;
  color: var(--apple-text-primary);
}

/* Glowing Timestamp Seek Button */
.timestamp-jump-box {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.jump-timestamp-btn {
  background: linear-gradient(135deg, #0071e3 0%, #42a5f5 100%);
  border: none;
  color: #FFFFFF;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--apple-radius-pill);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  box-shadow: 0 2px 8px var(--apple-blue-glow);
  transition: all var(--apple-transition-fast);
}

.jump-timestamp-btn:hover {
  transform: scale(1.04);
}

.scene-label {
  font-size: 11px;
  color: var(--apple-text-tertiary);
}

.thought-collapsible-box {
  margin-bottom: 8px;
  background: rgba(0, 0, 0, 0.03);
  border-left: 2px solid var(--apple-text-tertiary);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 11px;
}

.thought-summary-badge {
  cursor: pointer;
  color: var(--apple-text-tertiary);
  font-weight: 500;
  user-select: none;
}

.thought-inner-text {
  margin-top: 6px;
  color: var(--apple-text-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
  max-height: 180px;
  overflow-y: auto;
}

.stream-cursor {
  display: inline-block;
  margin-left: 2px;
  animation: blinkCursor 0.8s infinite;
  color: var(--apple-blue);
  font-weight: bold;
}

@keyframes blinkCursor {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.agent-input-dock {
  display: flex;
  gap: 8px;
}

.agent-pill-input {
  flex: 1;
  background: var(--apple-input-bg);
  border: none;
  outline: none;
  padding: 10px 14px;
  border-radius: var(--apple-radius-pill);
  font-size: 13px;
  color: var(--apple-text-primary);
}

.agent-pill-input:focus {
  background: #FFFFFF;
  box-shadow: 0 0 0 2px var(--apple-blue-glow);
}

/* Review Tab */
.review-record-card {
  background: var(--apple-input-bg);
  border-radius: 14px;
  padding: 12px;
  margin-bottom: 10px;
}

.record-meta-line {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.review-badge-red {
  background: #ffebee;
  color: #d32f2f;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}

.violation-reason-tag {
  font-size: 11px;
  color: var(--apple-text-secondary);
}

.violating-text-quote {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 10px;
}

.review-actions-row {
  display: flex;
  gap: 8px;
}

.review-btn {
  flex: 1;
  border: none;
  padding: 5px 0;
  border-radius: var(--apple-radius-pill);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
}

.approve-btn {
  background: #e8f5e9;
  color: #2e7d32;
}

.reject-btn {
  background: #ffebee;
  color: #c62828;
}

/* Apple Buttons */
.apple-primary-btn {
  background: var(--apple-blue);
  color: #FFFFFF;
  border: none;
  border-radius: var(--apple-radius-pill);
  padding: 7px 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all var(--apple-transition-fast);
}

.apple-primary-btn:hover {
  background: var(--apple-blue-hover);
  transform: scale(1.02);
  box-shadow: 0 4px 14px var(--apple-blue-glow);
}

/* Modal */
.apple-modal-backdrop,
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.apple-modal-card {
  width: 90%;
  max-width: 400px;
  background: #FFFFFF;
  border-radius: var(--apple-radius-card);
  padding: 28px;
}

.modal-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.modal-close-icon-btn {
  border: none;
  background: var(--apple-input-bg);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
}

.form-field-group {
  margin-bottom: 16px;
}

.field-label {
  display: block;
  font-size: 12px;
  color: var(--apple-text-secondary);
  margin-bottom: 6px;
}

.apple-form-input {
  width: 100%;
  border: none;
  background: var(--apple-input-bg);
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 13px;
}

.modal-submit-btn {
  width: 100%;
  padding: 10px 0;
  justify-content: center;
}

/* Responsive */
@media (max-width: 960px) {
  .theater-stage-container {
    grid-template-columns: 1fr !important;
    gap: 20px;
    padding: 0 16px;
  }
  .stage-portrait .theater-player-column {
    max-width: 100%;
  }
  .stage-portrait .video-viewport-box {
    width: 100%;
    max-width: 380px;
    height: 640px;
    margin: 0 auto;
  }
  .stage-portrait .video-meta-card,
  .stage-portrait .comments-bento-card {
    max-width: 500px;
    width: 100%;
    margin-left: auto;
    margin-right: auto;
  }
}

/* Autoplay Continuous Toggle Button */
.autoplay-toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.85);
  padding: 6px 12px;
  border-radius: 980px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.autoplay-toggle-btn.active {
  background: #0071e3;
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 0 12px rgba(0, 113, 227, 0.4);
}

.autoplay-indicator-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  transition: all 0.2s ease;
}

.autoplay-toggle-btn.active .autoplay-indicator-dot {
  background: #34c759;
  box-shadow: 0 0 6px #34c759;
}

/* 5s Frosted Glass Countdown HUD Overlay */
.autoplay-countdown-hud-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 10, 14, 0.72);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  z-index: 50;
  padding: 20px;
}

.hud-glass-card {
  background: rgba(28, 28, 35, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 28px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.65);
  padding: 32px 36px;
  max-width: 440px;
  width: 100%;
  text-align: center;
  color: #ffffff;
}

.hud-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 20px;
}

.hud-sparkle-icon {
  font-size: 16px;
}

.hud-badge {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: rgba(255, 255, 255, 0.85);
}

.hud-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}

.hud-timer-circle {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 3px solid rgba(0, 113, 227, 0.35);
  border-top-color: #0071e3;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  animation: hud-spin-ring 5s linear infinite;
}

.hud-timer-num {
  font-size: 32px;
  font-weight: 800;
  color: #ffffff;
  line-height: 1;
}

.hud-timer-unit {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.6);
  margin-left: 2px;
}

.hud-next-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 6px;
}

.hud-next-title {
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hud-actions-row {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.hud-btn-primary {
  flex: 1;
  background: #0071e3;
  color: #ffffff;
  border: none;
  padding: 12px 18px;
  border-radius: 980px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(0, 113, 227, 0.4);
}

.hud-btn-primary:hover {
  background: #0077ed;
  transform: translateY(-1px);
}

.hud-btn-secondary {
  flex: 1;
  background: rgba(255, 255, 255, 0.14);
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.18);
  padding: 12px 18px;
  border-radius: 980px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.hud-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.22);
}

@keyframes hud-spin-ring {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Favorites Modal */
.favorites-modal-card {
  max-width: 480px;
  background: #1c1c24;
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 24px;
  padding: 24px 28px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
}

.favorites-modal-card .modal-title {
  color: #ffffff;
}

.modal-header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.drama-mini-preview {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 14px;
  margin-bottom: 20px;
}

.mini-cover {
  width: 46px;
  height: 64px;
  object-fit: cover;
  border-radius: 8px;
}

.mini-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #ffffff;
}

.mini-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.section-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 10px;
}

.btn-text-action {
  background: none;
  border: none;
  color: #2997ff;
  font-size: 13px;
  cursor: pointer;
  font-weight: 500;
}

.inline-new-folder-box {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
  background: rgba(255, 255, 255, 0.06);
  padding: 8px 12px;
  border-radius: 12px;
}

.privacy-switch-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  white-space: nowrap;
}

.folder-items-scroll {
  max-height: 200px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.folder-select-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.folder-select-item.selected {
  background: rgba(0, 113, 227, 0.18);
  border-color: rgba(0, 113, 227, 0.5);
}

.folder-select-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.apple-checkbox {
  accent-color: #0071e3;
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.folder-name-text {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
}

.badge-default-tag {
  font-size: 11px;
  background: rgba(0, 113, 227, 0.35);
  color: #64b5f6;
  padding: 2px 6px;
  border-radius: 6px;
}

.badge-privacy-tag {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
  padding: 2px 6px;
  border-radius: 6px;
}

.folder-count-badge {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.favorites-modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.apple-btn-secondary {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.16);
  padding: 10px 16px;
  border-radius: 980px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.apple-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Two-Tier Comments Apple HIG Styles */
.comments-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px 16px;
  color: var(--apple-text-tertiary);
  font-size: 13px;
}

.empty-emoji {
  font-size: 18px;
}

.comment-thread-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--apple-hairline);
  border-radius: 14px;
  margin-bottom: 12px;
  transition: all 0.3s ease;
}

[data-theme="light"] .comment-thread-card {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.comment-highlight {
  border-color: var(--apple-blue) !important;
  box-shadow: 0 0 16px var(--apple-blue-glow) !important;
  animation: pulseGlow 1.5s ease-in-out infinite alternate;
}

@keyframes pulseGlow {
  0% { box-shadow: 0 0 8px var(--apple-blue-glow); }
  100% { box-shadow: 0 0 20px rgba(0, 113, 227, 0.45); }
}

.comment-bubble-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.commenter-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  border: 1px solid var(--apple-hairline);
}

.sub-avatar {
  width: 28px;
  height: 28px;
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-author-line {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.comment-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--apple-text-primary);
}

.mention-target-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: var(--apple-radius-pill);
  background: rgba(0, 113, 227, 0.1);
  color: var(--apple-blue);
  font-weight: 500;
}

.comment-time {
  font-size: 11px;
  color: var(--apple-text-tertiary);
  margin-left: auto;
}

.comment-content-text {
  margin: 0 0 8px 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--apple-text-secondary);
  word-break: break-all;
}

.comment-actions-bar {
  display: flex;
  align-items: center;
  gap: 14px;
}

.comment-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: transparent;
  border: none;
  font-size: 12px;
  color: var(--apple-text-tertiary);
  cursor: pointer;
  padding: 2px 6px;
  border-radius: var(--apple-radius-pill);
  transition: all 0.2s ease;
}

.comment-action-btn:hover {
  color: var(--apple-text-primary);
  background: rgba(255, 255, 255, 0.06);
}

[data-theme="light"] .comment-action-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.comment-action-btn.liked {
  color: #ff3b30;
}

.sub-thread-container {
  margin-left: 36px;
  padding-left: 14px;
  border-left: 2px solid var(--apple-hairline);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Inline Reply Box */
.inline-reply-box {
  margin-top: 10px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 12px;
  border: 1px solid var(--apple-hairline);
}

[data-theme="light"] .inline-reply-box {
  background: rgba(0, 0, 0, 0.02);
}

.replying-to-badge {
  display: inline-block;
  font-size: 11px;
  color: var(--apple-blue);
  font-weight: 600;
  margin-bottom: 6px;
}

.reply-textarea {
  width: 100%;
  background: var(--apple-input-bg);
  border: 1px solid var(--apple-hairline);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 12px;
  color: var(--apple-text-primary);
  outline: none;
  resize: vertical;
  box-sizing: border-box;
}

.reply-textarea:focus {
  border-color: var(--apple-blue);
}

.reply-box-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.reply-cancel-btn {
  background: transparent;
  border: none;
  color: var(--apple-text-tertiary);
  font-size: 12px;
  cursor: pointer;
  padding: 4px 10px;
  border-radius: var(--apple-radius-pill);
}

.reply-cancel-btn:hover {
  color: var(--apple-text-primary);
}

.reply-submit-btn {
  padding: 4px 12px;
  font-size: 12px;
}

/* Header Skylight Trigger */
.skylight-trigger-wrap {
  position: relative;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.skylight-bell-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--apple-hairline);
  background: var(--apple-input-bg);
  color: var(--apple-text-secondary);
  cursor: pointer;
  transition: all var(--apple-transition-fast);
  flex-shrink: 0;
}

.skylight-bell-btn:hover {
  color: var(--apple-text-primary);
  background: var(--apple-gray-btn-hover);
  transform: scale(1.05);
}

.skylight-unread-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  background: #ff3b30;
  color: #ffffff;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  box-shadow: 0 0 4px rgba(255, 59, 48, 0.6);
  flex-shrink: 0;
}

/* Frosted Glass Coin Tip Modal (Feature 20) */
.coin-tip-dialog {
  max-width: 460px;
  width: 90%;
  background: rgba(22, 22, 26, 0.88) !important;
  backdrop-filter: blur(28px) saturate(190%) !important;
  -webkit-backdrop-filter: blur(28px) saturate(190%) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  border-radius: 18px !important;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6) !important;
  color: #f5f5f7;
  overflow: hidden;
}

.wallet-balance-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.04);
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.wallet-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.wallet-val {
  font-size: 16px;
  font-weight: 700;
  color: #ffd60a;
}

.tipping-status-box {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 16px;
  text-align: center;
}

.tip-status-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
}

.max-tip-badge {
  margin-top: 6px;
  font-size: 12px;
  color: #30d158;
  font-weight: 600;
}

.tip-success-banner {
  background: rgba(48, 209, 88, 0.12);
  border: 1px solid rgba(48, 209, 88, 0.3);
  color: #30d158;
  padding: 10px 14px;
  border-radius: 10px;
  margin-bottom: 16px;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  animation: appleFadeIn 0.3s ease;
}

.tipping-options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 12px;
}

.tip-option-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 12px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  color: #ffffff;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.tip-option-card:hover:not(:disabled) {
  background: rgba(255, 214, 10, 0.1);
  border-color: rgba(255, 214, 10, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(255, 214, 10, 0.15);
}

.tip-option-card:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.option-coin-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.option-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 4px;
}

.option-sub {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
}

/* Sidebar Folding & Floating Expand Trigger */
.sidebar-top-control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px 12px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 8px;
}

.sidebar-top-title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.sidebar-collapse-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.8);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.sidebar-collapse-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  color: #ffffff;
}

.floating-expand-sidebar-btn {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0, 113, 227, 0.85);
  backdrop-filter: blur(12px);
  color: #ffffff;
  border: none;
  padding: 12px 8px;
  border-radius: 12px 0 0 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  z-index: 999;
  box-shadow: -4px 0 16px rgba(0, 113, 227, 0.4);
  transition: all 0.2s;
  writing-mode: vertical-rl;
}

.floating-expand-sidebar-btn:hover {
  background: #0077ed;
  padding-left: 14px;
}

/* Sidebar Collapsed State: Main Video Stage Stretches 100% (Cinema Giant Screen) */
.theater-stage-container.sidebar-collapsed {
  display: flex !important;
  flex-direction: column !important;
  max-width: 1560px !important;
  grid-template-columns: 1fr !important;
  transition: max-width 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.theater-stage-container.sidebar-collapsed .theater-player-column {
  flex: 1 1 100% !important;
  width: 100% !important;
  max-width: 100% !important;
}

.theater-stage-container.sidebar-collapsed.stage-landscape .video-viewport-box,
.theater-stage-container.sidebar-collapsed .stage-landscape .video-viewport-box {
  width: 100% !important;
  aspect-ratio: 16 / 9;
}

.theater-stage-container.sidebar-collapsed .theater-sidebar-column {
  display: none !important;
}

/* Web Fullscreen (Theater Immersive Fullscreen Mode) */
.theater-stage-container.is-web-fullscreen {
  position: fixed !important;
  inset: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  max-width: 100vw !important;
  max-height: 100vh !important;
  z-index: 99999 !important;
  background: #000000 !important;
  padding: 0 !important;
  margin: 0 !important;
  display: flex !important;
}

.theater-stage-container.is-web-fullscreen .theater-player-column {
  width: 100vw !important;
  height: 100vh !important;
  flex: 1 1 100% !important;
  max-width: 100vw !important;
}

.theater-stage-container.is-web-fullscreen .video-viewport-box {
  width: 100vw !important;
  height: 100vh !important;
  border-radius: 0 !important;
  border: none !important;
}

.theater-stage-container.is-web-fullscreen .video-meta-card,
.theater-stage-container.is-web-fullscreen .comments-bento-card,
.theater-stage-container.is-web-fullscreen .theater-sidebar-column {
  display: none !important;
}

/* Comments Independent Viewport Scrolling (Prevents Endless Page Stretch) */
.comments-flow-list {
  max-height: 520px !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  padding-right: 8px !important;
  scroll-behavior: smooth !important;
}

.comments-flow-list::-webkit-scrollbar {
  width: 6px;
}

.comments-flow-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.25);
  border-radius: 6px;
}

.comments-flow-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.45);
}

[data-theme="dark"] .comments-flow-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.25);
}

[data-theme="dark"] .comments-flow-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.45);
}
</style>

<style>
/* ========================================================================== */
/* PlayerView - Comprehensive Apple HIG Light Theme Overrides                */
/* ========================================================================== */
[data-theme="light"] .apple-player-page {
  background: #f5f6f8 !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .player-global-header {
  background: rgba(255, 255, 255, 0.88) !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
}

[data-theme="light"] .drama-title-head {
  color: #1d1d1f !important;
}

[data-theme="light"] .ep-counter {
  color: #6e6e73 !important;
}

[data-theme="light"] .apple-back-btn {
  color: #1d1d1f !important;
}

[data-theme="light"] .apple-back-btn:hover {
  background: rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .mode-pill-tab {
  background: rgba(0, 0, 0, 0.05) !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .pill-option-btn {
  color: #6e6e73 !important;
}

[data-theme="light"] .pill-option-btn.active {
  background: #ffffff !important;
  color: #1d1d1f !important;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .video-meta-card {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
}

[data-theme="light"] .video-main-heading {
  color: #1d1d1f !important;
}

[data-theme="light"] .video-stats-labels {
  color: #6e6e73 !important;
}

[data-theme="light"] .apple-action-pill {
  background: rgba(0, 0, 0, 0.04) !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .apple-action-pill:hover {
  background: rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .apple-action-pill.active {
  background: rgba(251, 114, 153, 0.1) !important;
  border-color: rgba(251, 114, 153, 0.3) !important;
  color: #fb7299 !important;
}

[data-theme="light"] .comments-bento-card {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
}

[data-theme="light"] .comments-card-header h3 {
  color: #1d1d1f !important;
}

[data-theme="light"] .comment-textarea {
  background: rgba(0, 0, 0, 0.03) !important;
  border: 1px solid rgba(0, 0, 0, 0.12) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .comment-textarea:focus {
  background: #ffffff !important;
  border-color: #0071e3 !important;
}

[data-theme="light"] .comment-thread-card {
  background: rgba(0, 0, 0, 0.02) !important;
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .comment-name {
  color: #1d1d1f !important;
}

[data-theme="light"] .comment-time {
  color: #86868b !important;
}

[data-theme="light"] .comment-content-text {
  color: #1d1d1f !important;
}

[data-theme="light"] .comment-action-btn {
  color: #6e6e73 !important;
}

[data-theme="light"] .comment-action-btn:hover {
  background: rgba(0, 0, 0, 0.05) !important;
  color: #1d1d1f !important;
}

/* Right Sidebar (Full Div Box Collapsible) */
[data-theme="light"] .theater-sidebar-column {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05) !important;
}

[data-theme="light"] .sidebar-top-control-bar {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .sidebar-top-title {
  color: #1d1d1f !important;
}

[data-theme="light"] .sidebar-collapse-btn {
  background: rgba(0, 0, 0, 0.04) !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .sidebar-collapse-btn:hover {
  background: rgba(0, 0, 0, 0.08) !important;
  color: #0071e3 !important;
}

[data-theme="light"] .sidebar-tab-segment {
  background: rgba(0, 0, 0, 0.04) !important;
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .side-tab-btn {
  color: #6e6e73 !important;
}

[data-theme="light"] .side-tab-btn.active {
  background: #ffffff !important;
  color: #fb7299 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .chunk-pill-btn {
  background: rgba(0, 0, 0, 0.04) !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  color: #6e6e73 !important;
}

[data-theme="light"] .chunk-pill-btn:hover {
  color: #1d1d1f !important;
  background: rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .chunk-pill-btn.active {
  background: #fb7299 !important;
  color: #ffffff !important;
}

[data-theme="light"] .episode-tile-btn {
  background: rgba(0, 0, 0, 0.03) !important;
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .episode-tile-btn:hover {
  background: rgba(251, 114, 153, 0.06) !important;
  border-color: rgba(251, 114, 153, 0.3) !important;
}

[data-theme="light"] .episode-tile-btn.active {
  background: rgba(251, 114, 153, 0.1) !important;
  border-color: #fb7299 !important;
}

[data-theme="light"] .ep-num-line {
  color: #fb7299 !important;
}

[data-theme="light"] .ep-title-sub {
  color: #6e6e73 !important;
}

[data-theme="light"] .highlight-card-item {
  background: rgba(0, 0, 0, 0.02) !important;
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .highlight-card-item:hover {
  background: #ffffff !important;
  border-color: rgba(251, 114, 153, 0.3) !important;
  box-shadow: 0 4px 14px rgba(251, 114, 153, 0.12) !important;
}

[data-theme="light"] .highlight-title {
  color: #1d1d1f !important;
}

[data-theme="light"] .highlight-desc {
  color: #6e6e73 !important;
}

[data-theme="light"] .quick-prompt-pill {
  background: rgba(0, 0, 0, 0.04) !important;
  color: #6e6e73 !important;
}

[data-theme="light"] .quick-prompt-pill:hover {
  background: rgba(0, 0, 0, 0.08) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .bubble-text {
  color: #1d1d1f !important;
}

[data-theme="light"] .chat-bubble-row.agent .bubble-text {
  background: rgba(0, 0, 0, 0.04) !important;
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .chat-input-bar .agent-input {
  background: rgba(0, 0, 0, 0.03) !important;
  border: 1px solid rgba(0, 0, 0, 0.12) !important;
  color: #1d1d1f !important;
}

/* Light Theme Scrollbars across Player View */
[data-theme="light"] .comments-flow-list::-webkit-scrollbar-thumb,
[data-theme="light"] .episodes-scroll-window::-webkit-scrollbar-thumb,
[data-theme="light"] .agent-chat-messages-scroll::-webkit-scrollbar-thumb,
[data-theme="light"] .episode-chunk-tabs-row::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.25) !important;
  border-radius: 6px !important;
}

[data-theme="light"] .comments-flow-list::-webkit-scrollbar-thumb:hover,
[data-theme="light"] .episodes-scroll-window::-webkit-scrollbar-thumb:hover,
[data-theme="light"] .agent-chat-messages-scroll::-webkit-scrollbar-thumb:hover,
[data-theme="light"] .episode-chunk-tabs-row::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.45) !important;
}

/* Time Capsule Button Styling */
.inline-time-capsule-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  margin: 0 4px;
  padding: 1px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", monospace;
  background: rgba(0, 113, 227, 0.16);
  border: 1px solid rgba(0, 113, 227, 0.4);
  color: #0071e3;
  cursor: pointer;
  vertical-align: middle;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 0 0 8px rgba(0, 113, 227, 0.2);
}
.inline-time-capsule-btn:hover {
  background: #0071e3;
  color: #ffffff;
  transform: translateY(-1px) scale(1.04);
  box-shadow: 0 0 12px rgba(0, 113, 227, 0.5);
}
[data-theme="light"] .inline-time-capsule-btn {
  background: #e8f2ff !important;
  border-color: #0071e3 !important;
  color: #0071e3 !important;
}
[data-theme="light"] .inline-time-capsule-btn:hover {
  background: #0071e3 !important;
  color: #ffffff !important;
}
.time-svg {
  width: 12px;
  height: 12px;
  display: inline-block;
  vertical-align: middle;
}
</style>
