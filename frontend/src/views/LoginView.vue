<template>
  <div class="grand-auth-page" id="auth-center-root">
    <!-- Ambient Aurora Glow Canvas -->
    <div class="aurora-ambient-glow aurora-orb-1"></div>
    <div class="aurora-ambient-glow aurora-orb-2"></div>
    <div class="aurora-ambient-glow aurora-orb-3"></div>

    <!-- Floating Top Bar with Theme Toggle & Return Link -->
    <div class="auth-floating-bar">
      <router-link to="/" class="back-home-pill-btn" id="btn-login-back-home">
        ← 返回视听大厅
      </router-link>
      <div class="theme-switch-pill" id="login-theme-control" title="切换明暗色彩主题">
        <button 
          type="button" 
          class="theme-icon-btn" 
          :class="{ active: currentTheme === 'light' }" 
          id="btn-login-theme-light"
          @click="toggleTheme('light')"
          title="浅色白天模式"
        >
          ☀️
        </button>
        <button 
          type="button" 
          class="theme-icon-btn" 
          :class="{ active: currentTheme === 'dark' }" 
          id="btn-login-theme-dark"
          @click="toggleTheme('dark')"
          title="深色夜间模式"
        >
          🌙
        </button>
        <button 
          type="button" 
          class="theme-icon-btn" 
          :class="{ active: currentTheme === 'system' }" 
          id="btn-login-theme-system"
          @click="toggleTheme('system')"
          title="跟随系统自动"
        >
          💻
        </button>
      </div>
    </div>

    <!-- Dual-Column Glass Center Container -->
    <div class="grand-auth-container">
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
              <div class="feature-icon">⚡</div>
              <div class="feature-text">
                <h3>夸克网盘直读</h3>
                <p>毫秒级 206 范围断点切片，570+ 集短剧无需占用服务器存储</p>
              </div>
            </div>

            <div class="feature-bento-item">
              <div class="feature-icon">📱</div>
              <div class="feature-text">
                <h3>9:16 / 16:9 双模态</h3>
                <p>手机端胶囊短剧与宽屏电影级画质无缝切换，高能时刻一键穿梭</p>
              </div>
            </div>

            <div class="feature-bento-item">
              <div class="feature-icon">🤖</div>
              <div class="feature-text">
                <h3>AI 剧情伴读伴侣</h3>
                <p>本地 Ollama + 云端小米 MiMo 多模型自适应驱动，剧情解密与记忆自测</p>
              </div>
            </div>

            <div class="feature-bento-item">
              <div class="feature-icon">🎬</div>
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
            <span class="fb-icon">{{ feedbackType === 'error' ? '⚠️' : '✅' }}</span>
            <span class="fb-text">{{ feedbackMsg }}</span>
          </div>
        </transition>

        <!-- Form 1: LOGIN -->
        <form v-if="currentTab === 'login'" class="auth-form" @submit.prevent="handleLogin" id="form-login">
          <div class="form-group">
            <label class="form-label" for="input-login-username">用户名 / 账号</label>
            <div class="input-wrap">
              <span class="input-prefix">👤</span>
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
              <span class="input-prefix">🔒</span>
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
                {{ showPassword ? '🙈' : '👁️' }}
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
              <span class="input-prefix">👤</span>
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
              <span class="input-prefix">🏷️</span>
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
                <span class="input-prefix">🔒</span>
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
                <span class="input-prefix">🔁</span>
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
            <span class="demo-icon">👤</span>
            <span class="demo-name">普通用户</span>
            <span class="demo-sub">观众空间/追剧</span>
          </button>

          <button
            class="demo-role-btn role-creator"
            id="btn-demo-creator"
            @click="quickLogin('creator')"
            title="以认证创作者身份登录"
          >
            <span class="demo-icon">🎬</span>
            <span class="demo-name">创作者</span>
            <span class="demo-sub">网盘/剧集管理</span>
          </button>

          <button
            class="demo-role-btn role-reviewer"
            id="btn-demo-reviewer"
            @click="quickLogin('reviewer')"
            title="以内容合规审核员身份登录"
          >
            <span class="demo-icon">🛡️</span>
            <span class="demo-name">审核员</span>
            <span class="demo-sub">违规剧集仲裁</span>
          </button>

          <button
            class="demo-role-btn role-admin"
            id="btn-demo-admin"
            @click="quickLogin('admin')"
            title="以超级管理员身份登录"
          >
            <span class="demo-icon">⚡</span>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
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

onMounted(() => {
  const saved = (localStorage.getItem('cinema_theme') as any) || 'system'
  currentTheme.value = saved
  if (route.query.tab === 'register' || route.path === '/register') {
    currentTab.value = 'register'
  }
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
      showFeedback('🎉 注册成功！已自动登录，正在为您开启视听之旅...', 'success')
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
.auth-floating-bar {
  position: absolute;
  top: 24px;
  left: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 10;
  max-width: 1200px;
  margin: 0 auto;
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
</style>
