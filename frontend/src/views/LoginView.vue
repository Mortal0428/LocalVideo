<template>
  <div class="grand-auth-page" id="auth-center-root">
    <!-- Dynamic Wallpaper Engine Layer -->
    <div v-if="wallpaperMode !== 'default_aurora'" class="login-wallpaper-layer" :style="wallpaperLayerStyle"></div>
    <div v-if="wallpaperMode !== 'default_aurora'" class="login-wallpaper-mask" :style="wallpaperMaskStyle"></div>

    <!-- Dynamic Sakura Canvas Particle Layer (60fps Wallpaper Engine Leaves Simulation) -->
    <canvas 
      v-if="wallpaperMode !== 'default_aurora'" 
      ref="sakuraCanvasRef" 
      class="sakura-canvas-layer"
      id="login-sakura-canvas"
    ></canvas>

    <!-- Ambient Aurora Glow Canvas -->
    <div class="aurora-ambient-glow aurora-orb-1"></div>
    <div class="aurora-ambient-glow aurora-orb-2"></div>
    <div class="aurora-ambient-glow aurora-orb-3"></div>

    <!-- Floating Top Sensory Island with Hover Down Auto-Show -->
    <div class="auth-top-sensor-zone" id="auth-top-sensor">
      <div class="sensor-indicator-handle" title="悬停滑出导航与设置"></div>
      <div class="auth-floating-bar" id="auth-floating-island">
      <router-link to="/" class="back-home-pill-btn" id="btn-login-back-home">
        ← 返回视听大厅
      </router-link>
      <!-- Pure Wallpaper Mode Switch -->
      <button 
        type="button" 
        class="pure-wallpaper-btn" 
        :class="{ active: isWallpaperOnlyMode }"
        id="btn-toggle-wallpaper-pure"
        @click="toggleWallpaperOnlyMode"
        title="纯享壁纸模式 (一键收起登录表单)"
      >
        <svg viewBox="0 0 24 24" class="pure-svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
          <circle cx="12" cy="12" r="3"></circle>
        </svg>
        <span>纯享壁纸</span>
      </button>
      <div class="theme-switch-pill" id="login-theme-control" title="切换明暗色彩主题">
        <button 
          type="button" 
          class="theme-icon-btn" 
          :class="{ active: currentTheme === 'light' }" 
          id="btn-login-theme-light"
          @click="toggleTheme('light')"
          title="浅色白天模式"
        >
          <svg viewBox="0 0 24 24" class="theme-svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
          </svg>
        </button>
        <button 
          type="button" 
          class="theme-icon-btn" 
          :class="{ active: currentTheme === 'dark' }" 
          id="btn-login-theme-dark"
          @click="toggleTheme('dark')"
          title="深色夜间模式"
        >
          <svg viewBox="0 0 24 24" class="theme-svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
          </svg>
        </button>
        <button 
          type="button" 
          class="theme-icon-btn" 
          :class="{ active: currentTheme === 'system' }" 
          id="btn-login-theme-system"
          @click="toggleTheme('system')"
          title="跟随系统自动"
        >
          <svg viewBox="0 0 24 24" class="theme-svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
          </svg>
        </button>
      </div>
      </div>
    </div>

    <!-- Dual-Column Glass Center Container -->
    <div class="grand-auth-container" :class="{ 'card-collapsed-down': isWallpaperOnlyMode }" id="grand-auth-box">
      <!-- Left Column: Platform Branding & Value Showcase -->
      <section class="auth-brand-panel">
        <div class="brand-top-bar">
          <router-link to="/" class="brand-logo-wrap" title="返回首页大厅">
            <span class="logo-text">Cinema<span class="accent">Agent</span></span>
            <span class="tag-version">2.0 Ultra</span>
          </router-link>
          <span class="brand-badge-pill">夸克网盘直通 · 双模态影院</span>
        </div>

        <div class="brand-hero-content">
          <h1 class="hero-title">
            全场景沉浸式<br />
            <span class="gradient-text">微短剧流媒体与创作平台</span>
          </h1>
          <p class="hero-desc">
            融合网盘高速流媒体直读、9:16 胶囊与 16:9 极简宽屏双模态切换、AI 剧情伴读 Agent 及创作者一键生态。
          </p>

          <div class="feature-bento-grid">
            <div class="feature-bento-item">
              <div class="feature-icon">
                <svg viewBox="0 0 24 24" class="bento-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path>
                </svg>
              </div>
              <div class="feature-text">
                <h3>夸克网盘直读</h3>
                <p>毫秒级 206 范围断点切片，570+ 集短剧无需占用服务器存储</p>
              </div>
            </div>

            <div class="feature-bento-item">
              <div class="feature-icon">
                <svg viewBox="0 0 24 24" class="bento-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect>
                  <line x1="12" y1="18" x2="12.01" y2="18"></line>
                </svg>
              </div>
              <div class="feature-text">
                <h3>9:16 / 16:9 双模态</h3>
                <p>手机端胶囊短剧与宽屏电影级画质无缝切换，高能时刻一键穿梭</p>
              </div>
            </div>

            <div class="feature-bento-item">
              <div class="feature-icon">
                <svg viewBox="0 0 24 24" class="bento-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                  <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
              </div>
              <div class="feature-text">
                <h3>AI 剧情伴读伴侣</h3>
                <p>本地 Ollama + 云端小米 MiMo 多模型自适应驱动，剧情解密与记忆自测</p>
              </div>
            </div>

            <div class="feature-bento-item">
              <div class="feature-icon">
                <svg viewBox="0 0 24 24" class="bento-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
                  <line x1="7" y1="2" x2="7" y2="22"></line>
                  <line x1="17" y1="2" x2="17" y2="22"></line>
                  <line x1="2" y1="12" x2="22" y2="12"></line>
                  <line x1="2" y1="7" x2="7" y2="7"></line>
                  <line x1="2" y1="17" x2="7" y2="17"></line>
                  <line x1="17" y1="17" x2="22" y2="17"></line>
                  <line x1="17" y1="7" x2="22" y2="7"></line>
                </svg>
              </div>
              <div class="feature-text">
                <h3>创作者工作室</h3>
                <p>创作者身份一键申请，网盘资源自动化映射与全生命周期审核</p>
              </div>
            </div>
          </div>
        </div>

        <div class="brand-footer-stats">
          <div class="stat-pill">
            <span class="stat-num">570+</span>
            <span class="stat-label">网盘同步剧集</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-pill">
            <span class="stat-num">100%</span>
            <span class="stat-label">无损高清直读</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-pill">
            <span class="stat-num">&lt; 30ms</span>
            <span class="stat-label">切片流媒体时延</span>
          </div>
        </div>
      </section>

      <!-- Right Column: Interactive Login / Register Form Card -->
      <section class="auth-form-card" id="auth-form-container">
        <!-- Segmented Tab Header -->
        <div class="auth-tab-segment" id="auth-tab-bar">
          <button
            class="tab-btn"
            :class="{ active: currentTab === 'login' }"
            id="tab-btn-login"
            @click="switchTab('login')"
          >
            账号登录
          </button>
          <button
            class="tab-btn"
            :class="{ active: currentTab === 'register' }"
            id="tab-btn-register"
            @click="switchTab('register')"
          >
            注册新账号
          </button>
        </div>

        <!-- Alert / Feedback Banner -->
        <transition name="fade">
          <div v-if="feedbackMsg" class="auth-feedback-banner" :class="feedbackType" id="auth-feedback">
            <span class="fb-icon">
              <svg v-if="feedbackType === 'error'" viewBox="0 0 24 24" class="fb-svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <svg v-else viewBox="0 0 24 24" class="fb-svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
            </span>
            <span class="fb-text">{{ feedbackMsg }}</span>
          </div>
        </transition>

        <!-- Form 1: LOGIN -->
        <form v-if="currentTab === 'login'" class="auth-form" @submit.prevent="handleLogin" id="form-login">
          <div class="form-group">
            <label class="form-label" for="input-login-username">用户名 / 账号</label>
            <div class="input-wrap">
              <span class="input-prefix"><svg viewBox="0 0 24 24" class="form-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg></span>
              <input
                id="input-login-username"
                v-model="loginForm.username"
                type="text"
                class="form-input"
                placeholder="请输入用户名 (如 viewer, creator, admin)"
                required
              />
            </div>
          </div>

          <div class="form-group">
            <div class="label-row">
              <label class="form-label" for="input-login-password">登录密码</label>
            </div>
            <div class="input-wrap">
              <span class="input-prefix"><svg viewBox="0 0 24 24" class="form-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></span>
              <input
                id="input-login-password"
                v-model="loginForm.password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input"
                placeholder="请输入密码"
                required
              />
              <button
                type="button"
                class="pwd-toggle-btn"
                id="btn-toggle-login-pwd"
                @click="showPassword = !showPassword"
                title="显示/隐藏密码"
              >
                <svg v-if="!showPassword" viewBox="0 0 24 24" class="form-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg><svg v-else viewBox="0 0 24 24" class="form-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
              </button>
            </div>
          </div>

          <button
            type="submit"
            class="auth-primary-btn"
            id="btn-submit-login"
            :disabled="isLoading"
          >
            <span v-if="isLoading" class="spinner"></span>
            <span v-else>立即登录 CinemaAgent</span>
          </button>
        </form>

        <!-- Form 2: REGISTER -->
        <form v-else class="auth-form" @submit.prevent="handleRegister" id="form-register">
          <div class="form-group">
            <label class="form-label" for="input-reg-username">账号名称 (登录唯一标识)</label>
            <div class="input-wrap">
              <span class="input-prefix"><svg viewBox="0 0 24 24" class="form-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg></span>
              <input
                id="input-reg-username"
                v-model="regForm.username"
                type="text"
                class="form-input"
                placeholder="3-20位字母、数字或下划线"
                required
              />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="input-reg-nickname">用户昵称 (大厅公开显示)</label>
            <div class="input-wrap">
              <span class="input-prefix"><svg viewBox="0 0 24 24" class="form-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg></span>
              <input
                id="input-reg-nickname"
                v-model="regForm.nickname"
                type="text"
                class="form-input"
                placeholder="起一个响亮的昵称 (如 追剧大魔王)"
              />
            </div>
          </div>

          <div class="form-row-dual">
            <div class="form-group">
              <label class="form-label" for="input-reg-password">设置密码</label>
              <div class="input-wrap">
                <span class="input-prefix"><svg viewBox="0 0 24 24" class="form-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></span>
                <input
                  id="input-reg-password"
                  v-model="regForm.password"
                  :type="showPassword ? 'text' : 'password'"
                  class="form-input"
                  placeholder="至少 6 位密码"
                  required
                />
              </div>
            </div>

            <div class="form-group">
              <label class="form-label" for="input-reg-confirm-pwd">确认密码</label>
              <div class="input-wrap">
                <span class="input-prefix"><svg viewBox="0 0 24 24" class="form-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg></span>
                <input
                  id="input-reg-confirm-pwd"
                  v-model="regForm.confirmPassword"
                  :type="showPassword ? 'text' : 'password'"
                  class="form-input"
                  placeholder="再次输入以确认"
                  required
                />
              </div>
            </div>
          </div>

          <!-- Genre Preference Tags -->
          <div class="form-group">
            <label class="form-label">观剧兴趣偏好 (多选，为您定制首页推荐)</label>
            <div class="genre-tags-wrap">
              <button
                v-for="tag in genreOptions"
                :key="tag"
                type="button"
                class="genre-chip"
                :class="{ active: regForm.preferences.includes(tag) }"
                @click="togglePreference(tag)"
              >
                {{ tag }}
              </button>
            </div>
          </div>

          <button
            type="submit"
            class="auth-primary-btn"
            id="btn-submit-register"
            :disabled="isLoading"
          >
            <span v-if="isLoading" class="spinner"></span>
            <span v-else>注册并开始探索</span>
          </button>
        </form>

        <div class="auth-divider">
          <span>快捷体验通道 · 角色一键切换</span>
        </div>

        <!-- Quick Demo Switch Bar -->
        <div class="quick-demo-roles" id="quick-demo-accounts-bar">
          <button
            class="demo-role-btn role-viewer"
            id="btn-demo-viewer"
            @click="quickLogin('viewer')"
            title="以普通观众身份登录"
          >
            <span class="demo-icon">
              <svg viewBox="0 0 24 24" class="demo-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
            </span>
            <span class="demo-name">普通用户</span>
            <span class="demo-sub">观众空间/追剧</span>
          </button>

          <button
            class="demo-role-btn role-creator"
            id="btn-demo-creator"
            @click="quickLogin('creator')"
            title="以认证创作者身份登录"
          >
            <span class="demo-icon">
              <svg viewBox="0 0 24 24" class="demo-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
            </span>
            <span class="demo-name">创作者</span>
            <span class="demo-sub">网盘/剧集管理</span>
          </button>

          <button
            class="demo-role-btn role-reviewer"
            id="btn-demo-reviewer"
            @click="quickLogin('reviewer')"
            title="以内容合规审核员身份登录"
          >
            <span class="demo-icon">
              <svg viewBox="0 0 24 24" class="demo-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
            </span>
            <span class="demo-name">审核员</span>
            <span class="demo-sub">违规剧集仲裁</span>
          </button>

          <button
            class="demo-role-btn role-admin"
            id="btn-demo-admin"
            @click="quickLogin('admin')"
            title="以超级管理员身份登录"
          >
            <span class="demo-icon">
              <svg viewBox="0 0 24 24" class="demo-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
            </span>
            <span class="demo-name">超管</span>
            <span class="demo-sub">全量用户管控</span>
          </button>
        </div>

        <!-- Guest Access Action -->
        <div class="guest-access-wrap">
          <router-link to="/" class="guest-link-btn" id="btn-guest-entry">
            <span>暂不登录，以游客身份漫游大厅</span>
            <span class="arrow">→</span>
          </router-link>
        </div>
      </section>
    </div>
    <!-- Floating Restore Pill when in Pure Wallpaper Mode -->
    <transition name="apple-fade">
      <div 
        v-if="isWallpaperOnlyMode" 
        class="restore-login-floating-pill" 
        id="btn-restore-login" 
        @click="toggleWallpaperOnlyMode"
        title="点击恢复登录表单"
      >
        <svg viewBox="0 0 24 24" class="restore-svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
          <polyline points="10 17 15 12 10 7"></polyline>
          <line x1="15" y1="12" x2="3" y2="12"></line>
        </svg>
        <span>恢复登录表单</span>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authApi } from '../api/auth'

const router = useRouter()
const route = useRoute()

const currentTab = ref<'login' | 'register'>('login')
const showPassword = ref(false)
const isLoading = ref(false)
const feedbackMsg = ref('')
const feedbackType = ref<'success' | 'error'>('error')

const genreOptions = ['逆袭爽剧', '年代逆袭', '现代甜宠', '科技AI', '动漫番剧', '悬疑刑侦', '影视原声']

const loginForm = reactive({
  username: '',
  password: ''
})

const regForm = reactive({
  username: '',
  nickname: '',
  password: '',
  confirmPassword: '',
  preferences: ['逆袭爽剧', '年代逆袭'] as string[]
})

const currentTheme = ref<'light' | 'dark' | 'system'>('system')

const toggleTheme = (mode: 'light' | 'dark' | 'system') => {
  currentTheme.value = mode
  localStorage.setItem('cinema_theme', mode)
  if (mode === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark')
  } else if (mode === 'light') {
    document.documentElement.setAttribute('data-theme', 'light')
  } else {
    const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light')
  }
}

// Wallpaper Engine State
const wallpaperMode = ref<string>('gaoleng_qianjin')
const wallpaperCustomUrl = ref<string>('')
const wallpaperDarkOpacity = ref<number>(0.45)
const wallpaperLightOpacity = ref<number>(0.18)
const wallpaperBlurPx = ref<number>(0)

const wallpaperLayerStyle = computed(() => {
  let bgUrl = '/wallpapers/gaoleng_qianjin.png'
  if (wallpaperMode.value === 'custom_url' && wallpaperCustomUrl.value) {
    bgUrl = wallpaperCustomUrl.value
  }
  return {
    backgroundImage: `url(${bgUrl})`,
    filter: wallpaperBlurPx.value > 0 ? `blur(${wallpaperBlurPx.value}px)` : 'none'
  }
})

const isWallpaperOnlyMode = ref(false)
function toggleWallpaperOnlyMode() {
  isWallpaperOnlyMode.value = !isWallpaperOnlyMode.value
}

const wallpaperMaskStyle = computed(() => {
  const isL = currentTheme.value === 'light'
  let op = isL ? wallpaperLightOpacity.value : wallpaperDarkOpacity.value
  if (isWallpaperOnlyMode.value) {
    op = 0.08
  }
  return {
    backgroundColor: isL ? `rgba(255, 255, 255, ${op})` : `rgba(0, 0, 0, ${op})`
  }
})

// Sakura Falling Petals Engine (Wallpaper Engine Leaves Simulation)
const sakuraCanvasRef = ref<HTMLCanvasElement | null>(null)
let sakuraAnimId: number | null = null
let sakuraPetals: any[] = []

class SakuraPetal {
  x: number
  y: number
  size: number
  speedX: number
  speedY: number
  rotation: number
  rotationSpeed: number
  opacity: number
  swing: number
  swingSpeed: number

  constructor(w: number, h: number, isInitial = false) {
    this.x = Math.random() * w
    this.y = isInitial ? Math.random() * h : -20
    this.size = 10 + Math.random() * 12
    this.speedX = 0.6 + Math.random() * 1.4
    this.speedY = 1.2 + Math.random() * 1.8
    this.rotation = Math.random() * Math.PI * 2
    this.rotationSpeed = (Math.random() - 0.5) * 0.04
    this.opacity = 0.4 + Math.random() * 0.45
    this.swing = Math.random() * Math.PI * 2
    this.swingSpeed = 0.02 + Math.random() * 0.03
  }

  update(w: number, h: number) {
    this.swing += this.swingSpeed
    this.x += this.speedX + Math.sin(this.swing) * 0.8
    this.y += this.speedY
    this.rotation += this.rotationSpeed
    if (this.y > h + 30 || this.x > w + 30) {
      this.y = -20
      this.x = Math.random() * w
    }
  }

  draw(ctx: CanvasRenderingContext2D) {
    ctx.save()
    ctx.translate(this.x, this.y)
    ctx.rotate(this.rotation)
    ctx.fillStyle = `rgba(255, 183, 197, ${this.opacity})`
    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.bezierCurveTo(-this.size / 2, -this.size / 2, -this.size / 2, this.size / 2, 0, this.size)
    ctx.bezierCurveTo(this.size / 2, this.size / 2, this.size / 2, -this.size / 2, 0, 0)
    ctx.fill()
    ctx.restore()
  }
}

function initSakuraEngine() {
  const canvas = sakuraCanvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const resize = () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  }
  resize()
  window.addEventListener('resize', resize)

  sakuraPetals = []
  const count = Math.min(42, Math.floor(window.innerWidth / 35))
  for (let i = 0; i < count; i++) {
    sakuraPetals.push(new SakuraPetal(canvas.width, canvas.height, true))
  }

  const loop = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    for (const p of sakuraPetals) {
      p.update(canvas.width, canvas.height)
      p.draw(ctx)
    }
    sakuraAnimId = requestAnimationFrame(loop)
  }
  loop()
}

function stopSakuraEngine() {
  if (sakuraAnimId) {
    cancelAnimationFrame(sakuraAnimId)
    sakuraAnimId = null
  }
  sakuraPetals = []
}

watch(wallpaperMode, (m) => {
  if (m !== 'default_aurora') {
    nextTick(() => initSakuraEngine())
  } else {
    stopSakuraEngine()
  }
})

async function fetchWallpaperConfig() {
  try {
    const res: any = await authApi.getWallpaperConfig()
    const d = res?.data?.data || res?.data
    if (d) {
      wallpaperMode.value = d.mode || 'gaoleng_qianjin'
      wallpaperCustomUrl.value = d.custom_url || ''
      wallpaperDarkOpacity.value = d.dark_opacity ?? 0.45
      wallpaperLightOpacity.value = d.light_opacity ?? 0.18
      wallpaperBlurPx.value = d.blur_px ?? 0
    }
  } catch (err) {
    console.warn('Failed to fetch wallpaper config:', err)
  }
}

onMounted(() => {
  fetchWallpaperConfig().then(() => {
    if (wallpaperMode.value !== 'default_aurora') {
      nextTick(() => initSakuraEngine())
    }
  })
  const saved = (localStorage.getItem('cinema_theme') as any) || 'system'
  currentTheme.value = saved
  if (route.query.tab === 'register' || route.path === '/register') {
    currentTab.value = 'register'
  }
})

onUnmounted(() => {
  stopSakuraEngine()
})

function switchTab(tab: 'login' | 'register') {
  currentTab.value = tab
  feedbackMsg.value = ''
}

function togglePreference(tag: string) {
  const idx = regForm.preferences.indexOf(tag)
  if (idx >= 0) {
    regForm.preferences.splice(idx, 1)
  } else {
    regForm.preferences.push(tag)
  }
}

function showFeedback(msg: string, type: 'success' | 'error' = 'error') {
  feedbackMsg.value = msg
  feedbackType.value = type
}

async function handleLogin() {
  if (!loginForm.username.trim() || !loginForm.password.trim()) {
    showFeedback('请输入用户名和密码')
    return
  }
  isLoading.value = true
  feedbackMsg.value = ''

  try {
    const res: any = await authApi.login({
      username: loginForm.username.trim(),
      password: loginForm.password.trim()
    })

    const token = res?.access_token || res?.data?.access_token
    const user = res?.user || res?.data?.user

    if (token) {
      localStorage.setItem('token', token)
      localStorage.setItem('cinema_access_token', token)
      localStorage.setItem('user', JSON.stringify(user))
      showFeedback('登录成功，正在进入平台...', 'success')
      setTimeout(() => {
        const redirect = (route.query.redirect as string) || '/'
        router.push(redirect)
      }, 500)
    } else {
      showFeedback(res?.message || '登录失败，请检查账号密码')
    }
  } catch (err: any) {
    const detail = err?.response?.data?.detail || err?.message || '登录失败'
    showFeedback(`登录错误: ${detail}`)
  } finally {
    isLoading.value = false
  }
}

async function handleRegister() {
  if (!regForm.username.trim()) {
    showFeedback('请输入用户名')
    return
  }
  if (regForm.password.length < 6) {
    showFeedback('密码长度不得少于 6 位')
    return
  }
  if (regForm.password !== regForm.confirmPassword) {
    showFeedback('两次输入的密码不一致')
    return
  }

  isLoading.value = true
  feedbackMsg.value = ''

  try {
    const res: any = await authApi.register({
      username: regForm.username.trim(),
      password: regForm.password.trim(),
      nickname: regForm.nickname.trim() || regForm.username.trim(),
      role: 'USER'
    })

    const token = res?.access_token || res?.data?.access_token
    const user = res?.user || res?.data?.user

    if (token) {
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
      showFeedback(' 注册成功！已自动登录，正在为您开启视听之旅...', 'success')
      setTimeout(() => {
        router.push('/')
      }, 700)
    } else {
      showFeedback(res?.message || '注册成功，请使用新账号登录', 'success')
      currentTab.value = 'login'
    }
  } catch (err: any) {
    const detail = err?.response?.data?.detail || err?.message || '注册失败'
    showFeedback(`注册错误: ${detail}`)
  } finally {
    isLoading.value = false
  }
}

async function quickLogin(roleName: string) {
  isLoading.value = true
  feedbackMsg.value = ''
  try {
    const res: any = await authApi.quickSwitch(roleName)
    const token = res?.access_token || res?.data?.access_token
    const user = res?.user || res?.data?.user

    if (token) {
      localStorage.setItem('token', token)
      localStorage.setItem('cinema_access_token', token)
      localStorage.setItem('user', JSON.stringify(user))
      showFeedback(`已成功以【${user?.nickname || roleName}】身份快捷登录！`, 'success')
      setTimeout(() => {
        if (roleName === 'admin') router.push('/admin')
        else if (roleName === 'creator') router.push('/creator')
        else router.push('/')
      }, 400)
    }
  } catch (err: any) {
    showFeedback('快捷登录切换失败: ' + (err?.message || '网络异常'))
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.grand-auth-page {
  position: relative;
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-base);
  color: var(--text-primary);
  overflow: hidden;
  padding: 60px 24px 40px;
  box-sizing: border-box;
  transition: background-color var(--apple-transition-normal), color var(--apple-transition-normal);
}

/* Floating Top Controls */
.auth-top-sensor-zone {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 48px;
  z-index: 100;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  pointer-events: auto;
}

.sensor-indicator-handle {
  width: 48px;
  height: 4px;
  margin-top: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.28);
  backdrop-filter: blur(8px);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.auth-floating-bar {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%) translateY(-130%);
  width: calc(100% - 48px);
  max-width: 1200px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 100;
  opacity: 0;
  pointer-events: none;
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease;
}

.auth-top-sensor-zone:hover .auth-floating-bar,
.auth-floating-bar:hover,
.auth-floating-bar:focus-within {
  transform: translateX(-50%) translateY(0);
  opacity: 1;
  pointer-events: auto;
}

.auth-top-sensor-zone:hover .sensor-indicator-handle {
  opacity: 0;
  transform: scaleX(0.5);
}

.back-home-pill-btn {
  background: var(--bg-surface);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-glass);
  border-radius: var(--apple-radius-pill);
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  text-decoration: none;
  box-shadow: var(--glass-shadow);
  transition: all var(--apple-transition-fast);
}

.back-home-pill-btn:hover {
  border-color: var(--bili-blue);
  color: var(--bili-blue);
  transform: translateX(-3px);
}

/* Theme Switcher Capsule */
.theme-switch-pill {
  display: flex;
  align-items: center;
  background: var(--apple-input-bg);
  padding: 3px;
  border-radius: var(--apple-radius-pill);
  gap: 2px;
  border: 1px solid var(--border-line);
  box-shadow: var(--glass-shadow);
}

.theme-icon-btn {
  border: none;
  background: transparent;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all var(--apple-transition-fast);
}

.theme-icon-btn:hover {
  color: var(--text-primary);
  transform: scale(1.1);
}

.theme-icon-btn.active {
  background: var(--bg-card);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
  transform: scale(1.05);
}

/* Ambient Aurora Glow Orbs */
.aurora-ambient-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.35;
  pointer-events: none;
  z-index: 0;
}
.aurora-orb-1 {
  width: 520px;
  height: 520px;
  background: radial-gradient(circle, #00aeec, #3b82f6);
  top: -100px;
  left: -80px;
}
.aurora-orb-2 {
  width: 480px;
  height: 480px;
  background: radial-gradient(circle, #fb7299, #ec4899);
  bottom: -100px;
  right: -60px;
}
.aurora-orb-3 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #8b5cf6, #6366f1);
  top: 40%;
  left: 45%;
}

/* Container */
.grand-auth-container {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  width: 100%;
  max-width: 1200px;
  min-height: 680px;
  background: var(--bg-surface);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  border: 1px solid var(--border-glass);
  border-radius: 28px;
  box-shadow: var(--glass-shadow-hover);
  overflow: hidden;
  transition: all var(--apple-transition-normal);
}

/* Left Brand Panel */
.auth-brand-panel {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 48px;
  background: linear-gradient(145deg, rgba(125, 125, 125, 0.03) 0%, rgba(0, 174, 236, 0.05) 100%);
  border-right: 1px solid var(--border-line);
}

.brand-top-bar {
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand-logo-wrap {
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-text {
  font-size: 26px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}
.logo-text .accent {
  color: #00aeec;
}

.tag-version {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  background: rgba(0, 174, 236, 0.18);
  border: 1px solid rgba(0, 174, 236, 0.35);
  color: #00aeec;
  border-radius: 12px;
}

.brand-badge-pill {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 4px 12px;
  background: var(--apple-input-bg);
  border: 1px solid var(--border-line);
  border-radius: 16px;
}

.brand-hero-content {
  margin: 36px 0;
}

.hero-title {
  font-size: 34px;
  line-height: 1.25;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.gradient-text {
  background: linear-gradient(90deg, #00aeec, #60a5fa, #fb7299);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-desc {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin-bottom: 32px;
  max-width: 500px;
}

.feature-bento-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.feature-bento-item {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: var(--apple-input-bg);
  border: 1px solid var(--border-line);
  border-radius: 16px;
  transition: all 0.25s ease;
}
.feature-bento-item:hover {
  background: var(--bg-card);
  border-color: rgba(0, 174, 236, 0.4);
  transform: translateY(-2px);
  box-shadow: var(--glass-shadow);
}

.feature-icon {
  font-size: 20px;
  line-height: 1;
}

.feature-text h3 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}
.feature-text p {
  font-size: 11px;
  line-height: 1.4;
  color: var(--text-secondary);
  margin: 0;
}

.brand-footer-stats {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--apple-input-bg);
  border-radius: 18px;
  border: 1px solid var(--border-line);
}

.stat-pill {
  display: flex;
  flex-direction: column;
}
.stat-num {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-primary);
}
.stat-label {
  font-size: 11px;
  color: var(--text-muted);
}
.stat-divider {
  width: 1px;
  height: 24px;
  background: var(--border-line);
}

/* Right Form Card */
.auth-form-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 48px;
  background: transparent;
}

/* Tab Segment */
.auth-tab-segment {
  display: flex;
  background: var(--apple-input-bg);
  padding: 4px;
  border-radius: 14px;
  margin-bottom: 24px;
  border: 1px solid var(--border-line);
}

.tab-btn {
  flex: 1;
  padding: 10px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.tab-btn.active {
  background: var(--bg-card);
  color: var(--bili-blue);
  box-shadow: 0 4px 12px rgba(0, 174, 236, 0.2);
}

/* Feedback Banner */
.auth-feedback-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 13px;
  margin-bottom: 18px;
}
.auth-feedback-banner.error {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}
.auth-feedback-banner.success {
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #22c55e;
}

/* Form Styles */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--apple-input-bg);
  border: 1px solid var(--border-line);
  border-radius: 12px;
  padding: 0 12px;
  transition: all 0.2s ease;
}
.input-wrap:focus-within {
  border-color: #00aeec;
  background: var(--bg-card);
  box-shadow: 0 0 0 3px rgba(0, 174, 236, 0.15);
}

.input-prefix {
  font-size: 14px;
  margin-right: 8px;
  user-select: none;
}

.form-input {
  width: 100%;
  height: 42px;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 14px;
}
.form-input::placeholder {
  color: var(--text-muted);
  font-size: 13px;
}

.pwd-toggle-btn {
  background: transparent;
  border: none;
  font-size: 14px;
  cursor: pointer;
  padding: 4px;
  color: var(--text-secondary);
}

.form-row-dual {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

/* Genre Preference Chips */
.genre-tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.genre-chip {
  padding: 6px 12px;
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--apple-input-bg);
  border: 1px solid var(--border-line);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.genre-chip.active {
  background: rgba(0, 174, 236, 0.15);
  border-color: #00aeec;
  color: #00aeec;
  font-weight: 600;
}

/* Primary Submit Button */
.auth-primary-btn {
  margin-top: 6px;
  height: 44px;
  background: linear-gradient(135deg, #00aeec 0%, #0088cc 100%);
  border: none;
  border-radius: 12px;
  color: #ffffff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(0, 174, 236, 0.3);
}
.auth-primary-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 174, 236, 0.45);
}
.auth-primary-btn:active {
  transform: scale(0.97);
}
.auth-primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Divider */
.auth-divider {
  display: flex;
  align-items: center;
  text-align: center;
  margin: 24px 0 16px 0;
  color: var(--text-muted);
  font-size: 11px;
}
.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--border-line);
}
.auth-divider span {
  padding: 0 10px;
}

/* Quick Demo Role Dock */
.quick-demo-roles {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.demo-role-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 6px;
  background: var(--apple-input-bg);
  border: 1px solid var(--border-line);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.demo-role-btn:hover {
  background: var(--bg-card);
  transform: translateY(-2px);
  box-shadow: var(--glass-shadow);
}
.demo-role-btn:active {
  transform: scale(0.96);
}
.demo-role-btn.role-viewer:hover { border-color: #38bdf8; }
.demo-role-btn.role-creator:hover { border-color: #ec4899; }
.demo-role-btn.role-reviewer:hover { border-color: #fbbf24; }
.demo-role-btn.role-admin:hover { border-color: #a855f7; }

.demo-icon {
  font-size: 18px;
  margin-bottom: 2px;
}
.demo-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}
.demo-sub {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* Guest link */
.guest-access-wrap {
  text-align: center;
  margin-top: 20px;
}
.guest-link-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.2s ease;
}
.guest-link-btn:hover {
  color: #00aeec;
}
.guest-link-btn .arrow {
  transition: transform 0.2s ease;
}
.guest-link-btn:hover .arrow {
  transform: translateX(3px);
}

/* Responsive */
@media (max-width: 960px) {
  .grand-auth-container {
    grid-template-columns: 1fr;
    max-width: 520px;
  }
  .auth-brand-panel {
    display: none;
  }
  .auth-form-card {
    padding: 32px 24px;
  }
}

/* Wallpaper Layer Styling */
.login-wallpaper-layer {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  z-index: 1;
  transition: filter 0.3s ease;
}

.login-wallpaper-mask {
  position: absolute;
  inset: 0;
  z-index: 2;
  transition: background-color 0.3s ease;
}

.grand-auth-container {
  position: relative;
  z-index: 5;
}

.theme-svg,
.bento-svg,
.form-svg,
.demo-svg,
.fb-svg {
  width: 16px;
  height: 16px;
}

.bento-svg {
  width: 20px;
  height: 20px;
  color: var(--apple-blue, #0071E3);
}

.demo-svg {
  width: 22px;
  height: 22px;
}

.fb-svg {
  width: 18px;
  height: 18px;
}

/* Sakura Particle Layer */
.sakura-canvas-layer {
  position: absolute;
  inset: 0;
  z-index: 3;
  pointer-events: none;
  width: 100%;
  height: 100%;
}

/* Pure Wallpaper Mode Button */
.pure-wallpaper-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  background: var(--bg-secondary, rgba(255, 255, 255, 0.08));
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.14));
  color: var(--text-primary, #f5f5f7);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
  backdrop-filter: blur(16px);
}

.pure-wallpaper-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.28);
}

.pure-wallpaper-btn.active {
  background: rgba(0, 113, 227, 0.25);
  border-color: var(--apple-blue, #2997ff);
  color: var(--apple-blue, #2997ff);
}

.pure-svg {
  width: 14px;
  height: 14px;
}

/* Login Card Slide Down Collapse */
.grand-auth-container {
  transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.45s ease;
}

.grand-auth-container.card-collapsed-down {
  transform: translateY(115vh) scale(0.94);
  opacity: 0;
  pointer-events: none;
}

/* Floating Restore Pill */
.restore-login-floating-pill {
  position: fixed;
  bottom: 32px;
  right: 32px;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 22px;
  border-radius: 999px;
  background: rgba(28, 28, 30, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  backdrop-filter: blur(20px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
  transition: all 0.25s ease;
}

.restore-login-floating-pill:hover {
  background: #0071E3;
  transform: translateY(-2px);
  box-shadow: 0 16px 40px rgba(0, 113, 227, 0.5);
}

.restore-svg {
  width: 16px;
  height: 16px;
}

</style>
