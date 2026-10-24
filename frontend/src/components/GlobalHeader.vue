<template>
  <header class="apple-global-header" id="bili-global-header">
    <div class="header-inner">
      <!-- Left: Logo & Nav items -->
      <div class="header-left">
        <router-link to="/" class="apple-logo-badge" id="nav-logo-link">
          <div class="logo-icon-squircle">
            <el-icon :size="18"><Film /></el-icon>
          </div>
          <div class="logo-text-wrap">
            <span class="logo-title">CinemaAgent</span>
            <span class="logo-caption">夸克 · 沃盘直连</span>
          </div>
        </router-link>

        <nav class="header-nav">
          <router-link to="/landing" class="nav-item" active-class="active">展示大厅</router-link>
          <router-link to="/" class="nav-item" active-class="active">视听大厅</router-link>
          <router-link
            v-if="currentUser?.is_creator || currentUser?.role === 'CREATOR' || currentUser?.role === 'ADMIN'"
            to="/creator"
            class="nav-item creator-privilege-link"
            id="nav-creator-privilege-btn"
            active-class="active"
          >创作者中心</router-link>
          <router-link
            v-if="currentUser?.is_reviewer || currentUser?.role === 'REVIEWER' || currentUser?.role === 'ADMIN'"
            to="/admin?tab=agent-hub&sub=hitl"
            class="nav-item reviewer-privilege-link"
            id="nav-reviewer-privilege-btn"
            active-class="active"
          >审核员工作台</router-link>
          <router-link to="/user/space" class="nav-item user-space-link" active-class="active">个人中心</router-link>
          <router-link v-if="currentUser?.role === 'ADMIN'" to="/admin" class="nav-item admin-nav-link" active-class="active">后台管理</router-link>
        </nav>
      </div>

      <!-- Center: Apple Pill Search Input Bar -->
      <div class="header-center">
        <div class="search-capsule-box" id="header-search-bar">
          <svg viewBox="0 0 24 24" class="search-prefix-icon">
            <path fill="currentColor" d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
          </svg>
          <input
            v-model="searchKeyword"
            type="text"
            id="home-search-input"
            class="apple-search-input"
            placeholder="搜索短剧、镜头秒数、台词或题材..."
            @keyup.enter="handleSearch"
          />
          <button class="search-submit-btn" id="btn-search" @click="handleSearch">搜索</button>
        </div>
      </div>

      <!-- Right: Theme Switcher, Role Switcher & User Account State -->
      <div class="header-right">
        <!-- Theme Switcher Capsule (Light / Dark / Auto System) -->
        <div class="theme-switch-pill" id="theme-switch-control" title="切换明暗色彩主题 (浅色/深色/跟随系统)">
          <button 
            type="button"
            class="theme-icon-btn" 
            :class="{ active: currentTheme === 'light' }"
            id="btn-theme-light"
            @click="toggleTheme('light')"
            title="明亮白天模式"
          >
            <el-icon :size="14"><Sunny /></el-icon>
          </button>
          <button 
            type="button"
            class="theme-icon-btn" 
            :class="{ active: currentTheme === 'dark' }"
            id="btn-theme-dark"
            @click="toggleTheme('dark')"
            title="深色暗黑模式"
          >
            <el-icon :size="14"><Moon /></el-icon>
          </button>
          <button 
            type="button"
            class="theme-icon-btn" 
            :class="{ active: currentTheme === 'system' }"
            id="btn-theme-system"
            @click="toggleTheme('system')"
            title="跟随操作系统自动切换"
          >
            <el-icon :size="14"><Monitor /></el-icon>
          </button>
        </div>

        <!-- Notification Skylight Bell Trigger -->
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

        <!-- User profile or Guest -->
        <div class="user-state-area">
          <template v-if="currentUser">
            <router-link to="/user/space" class="user-profile-chip" id="user-profile-badge" title="前往个人空间">
              <img :src="currentUser.avatar_url || defaultAvatar" class="chip-avatar" id="user-avatar-img" />
              <div class="chip-info">
                <span class="chip-name" id="user-display-name">{{ currentUser.nickname || currentUser.username }}</span>
                <span class="chip-role" :class="currentUser.role.toLowerCase()" id="user-role-badge">
                  {{ getRoleLabel(currentUser.role) }}
                </span>
              </div>
            </router-link>
            <button class="apple-secondary-btn chip-logout-btn" id="btn-logout" @click="handleLogout">退出</button>
          </template>

          <template v-else>
            <span class="guest-label-pill" id="guest-badge">未登录游客</span>
            <router-link to="/login" class="apple-primary-btn" id="btn-open-login">
              登录 / 注册
            </router-link>
          </template>

          <!-- Engine Settings Trigger Button -->
          <button 
            type="button"
            class="engine-settings-trigger-btn" 
            id="btn-engine-settings" 
            @click="showSettingsModal = true" 
            title="配置本地/云端模型引擎"
          >
            <el-icon class="btn-icon"><Setting /></el-icon>
            <span>引擎设置</span>
          </button>

          <!-- Upload / Creator Button -->
          <button class="apple-primary-btn creator-publish-btn" id="btn-creator-upload" @click="handleCreatorUpload">
            <el-icon class="btn-icon"><Upload /></el-icon>
            <span>创作投稿</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Apple HIG Glassmorphism Auth Modal -->
    <transition name="apple-modal-fade">
      <div v-if="showAuthModal" class="apple-modal-backdrop" @click.self="showAuthModal = false" id="modal-auth-backdrop">
        <div class="apple-modal-card" id="modal-auth-card">
          <div class="modal-card-header">
            <div class="modal-title-wrap">
              <div class="modal-icon-squircle">
                <el-icon :size="20"><Lock /></el-icon>
              </div>
              <div>
                <h3 class="modal-title">{{ authMode === 'login' ? '账号登录' : '注册新账号' }}</h3>
                <p class="modal-subtitle">{{ modalHintText || '登录后畅享全部互动点赞与 AI 伴读特权' }}</p>
              </div>
            </div>
            <button class="modal-close-icon-btn" id="btn-close-auth-modal" @click="showAuthModal = false">✕</button>
          </div>

          <!-- Tab switch: Login vs Register -->
          <div class="modal-tab-segment">
            <button
              class="tab-btn"
              :class="{ active: authMode === 'login' }"
              id="tab-switch-login"
              @click="authMode = 'login'"
            >
              密码登录
            </button>
            <button
              class="tab-btn"
              :class="{ active: authMode === 'register' }"
              id="tab-switch-register"
              @click="authMode = 'register'"
            >
              新用户注册
            </button>
          </div>

          <!-- Error Alert Banner -->
          <div v-if="authError" class="modal-error-banner" id="auth-error-msg">
            <el-icon class="err-icon"><Warning /></el-icon>
            <span>{{ authError }}</span>
          </div>

          <!-- Auth Form Fields -->
          <form class="modal-form" @submit.prevent="handleAuthSubmit">
            <div class="form-field-group">
              <label class="field-label">用户名</label>
              <input
                v-model="authForm.username"
                type="text"
                id="input-auth-username"
                class="apple-form-input"
                placeholder="请输入用户名（如 cinema_fan）"
                required
              />
            </div>

            <div class="form-field-group">
              <label class="field-label">密码</label>
              <input
                v-model="authForm.password"
                type="password"
                id="input-auth-password"
                class="apple-form-input"
                placeholder="请输入密码（不少于 6 位）"
                required
              />
            </div>

            <!-- Extra field for register -->
            <div v-if="authMode === 'register'" class="form-field-group">
              <label class="field-label">用户昵称（选填）</label>
              <input
                v-model="authForm.nickname"
                type="text"
                id="input-auth-nickname"
                class="apple-form-input"
                placeholder="您的专属剧迷昵称"
              />
            </div>

            <div v-if="authMode === 'register'" class="form-field-group">
              <label class="field-label">注册角色</label>
              <div class="role-select-grid">
                <label class="role-option-label" :class="{ selected: authForm.role === 'USER' }">
                  <input type="radio" v-model="authForm.role" value="USER" />
                  <span>普通追剧用户</span>
                </label>
                <label class="role-option-label" :class="{ selected: authForm.role === 'CREATOR' }">
                  <input type="radio" v-model="authForm.role" value="CREATOR" />
                  <span>短剧创作者</span>
                </label>
              </div>
            </div>

            <div class="modal-actions-row">
              <button
                type="submit"
                class="apple-primary-btn modal-submit-btn"
                id="btn-submit-auth"
                :disabled="isSubmitting"
              >
                {{ isSubmitting ? '正在验证中...' : (authMode === 'login' ? '立即登录' : '完成注册并登录') }}
              </button>
            </div>
          </form>

          <!-- Quick Test Accounts Helper -->
          <div class="test-accounts-helper">
            <span class="helper-caption">演示环境快速登入账号：</span>
            <div class="helper-pills-row">
              <button class="helper-pill" @click="fillQuickAccount('user', 'user123')">普通用户 (user)</button>
              <button class="helper-pill" @click="fillQuickAccount('creator', 'creator123')">创作者 (creator)</button>
              <button class="helper-pill" @click="fillQuickAccount('reviewer', 'reviewer123')">审核员 (reviewer)</button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Engine Settings Modal -->
    <EngineSettingsModal 
      v-model="showSettingsModal" 
      @updated="onModelEngineUpdated" 
    />

    <!-- Notification Skylight Drawer -->
    <NotificationSkylight
      v-model="showSkylightDrawer"
      :unread-counts="unreadCounts"
      @unread-count-changed="fetchUnreadCount"
    />
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authApi, type UserProfile } from '../api/auth'
import { notificationApi, type UnreadCountData } from '../api/user'
import { useUserStore } from '../stores/user'
import { 
  Sunny, 
  Moon, 
  Monitor, 
  Setting, 
  Upload, 
  Film, 
  Lock, 
  Warning,
  Bell
} from '@element-plus/icons-vue'
import EngineSettingsModal from './EngineSettingsModal.vue'
import NotificationSkylight from './NotificationSkylight.vue'

const emit = defineEmits<{
  (e: 'search', keyword: string): void
  (e: 'userChanged', user: UserProfile | null): void
}>()

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const defaultAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=apple'

const searchKeyword = ref('')
const currentUser = userStore.currentUser
const showAuthModal = ref(false)
const showSettingsModal = ref(false)
const showSkylightDrawer = ref(false)
const unreadCounts = ref<UnreadCountData>({ total: 0, announcements: 0, replies: 0, likes: 0 })
const authMode = ref<'login' | 'register'>('login')
const modalHintText = ref('')
const authError = ref('')
const isSubmitting = ref(false)
const currentTheme = ref<'light' | 'dark' | 'system'>('system')

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

const onModelEngineUpdated = (cfg: any) => {
  console.log('Active model engine updated:', cfg)
}

const authForm = ref({
  username: '',
  password: '',
  nickname: '',
  role: 'USER'
})

onMounted(async () => {
  const saved = (localStorage.getItem('cinema_theme') as any) || 'system'
  currentTheme.value = saved
  await userStore.refreshProfile()
  emit('userChanged', currentUser.value as any)
  await fetchUnreadCount()
})

watch(() => route.path, async () => {
  await userStore.refreshProfile()
  emit('userChanged', currentUser.value as any)
  await fetchUnreadCount()
})

async function restoreUserSession() {
  const profile = await userStore.refreshProfile()
  emit('userChanged', profile as any)
  await fetchUnreadCount()
  return profile
}

function handleSearch() {
  emit('search', searchKeyword.value.trim())
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

async function switchRole(roleName: string) {
  try {
    const res: any = await authApi.quickSwitch(roleName)
    const token = res?.access_token || res?.data?.access_token
    const userObj = res?.user || res?.data?.user
    if (token && userObj) {
      userStore.setUser(userObj, token)
      emit('userChanged', userObj)
      window.location.reload()
    }
  } catch (err) {
    console.error('Failed to switch demo role via quickSwitch:', err)
  }
}

function openAuthModal(hint = '') {
  modalHintText.value = hint
  authError.value = ''
  authForm.value = {
    username: '',
    password: '',
    nickname: '',
    role: 'USER'
  }
  showAuthModal.value = true
}

function fillQuickAccount(u: string, p: string) {
  authForm.value.username = u
  authForm.value.password = p
  authMode.value = 'login'
}

async function handleAuthSubmit() {
  authError.value = ''
  isSubmitting.value = true

  try {
    if (authMode.value === 'login') {
      const res: any = await authApi.login({
        username: authForm.value.username.trim(),
        password: authForm.value.password.trim()
      })
      const token = res?.access_token || res?.data?.access_token
      const userObj = res?.user || res?.data?.user
      if (token) {
        if (userObj) {
          userStore.setUser(userObj, token)
        }
        emit('userChanged', currentUser.value as any)
        showAuthModal.value = false
      } else {
        authError.value = res?.message || '登录失败，请检查账号密码'
      }
    } else {
      const res: any = await authApi.register({
        username: authForm.value.username.trim(),
        password: authForm.value.password.trim(),
        nickname: authForm.value.nickname.trim() || undefined,
        role: authForm.value.role
      })
      const token = res?.access_token || res?.data?.access_token
      const userObj = res?.user || res?.data?.user
      if (token) {
        if (userObj) {
          userStore.setUser(userObj, token)
        }
        emit('userChanged', currentUser.value as any)
        showAuthModal.value = false
      } else {
        authError.value = res?.message || '注册失败'
      }
    }
  } catch (err: any) {
    authError.value = err.response?.data?.detail || err.message || '网络请求错误'
  } finally {
    isSubmitting.value = false
  }
}

function handleLogout() {
  userStore.clearUser()
  emit('userChanged', null)
  window.location.href = '/'
}

function handleCreatorUpload() {
  router.push('/creator')
}

defineExpose({
  openAuthModal,
  restoreUserSession
})
</script>

<style scoped>
/* ========================================================================== */
/* Apple HIG Translucent Frosted Glass Header                                 */
/* ========================================================================== */
.apple-global-header {
  position: sticky;
  top: 0;
  left: 0;
  width: 100%;
  height: 64px;
  background: var(--header-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--header-border);
  z-index: 100;
  transition: background var(--apple-transition-normal), border-color var(--apple-transition-normal);
}

.header-inner {
  max-width: 1720px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  gap: 14px;
}

/* Left: Logo & Nav */
.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-shrink: 0;
}

.apple-logo-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--apple-text-primary);
  transition: transform var(--apple-transition-fast);
  flex-shrink: 0;
}

.apple-logo-badge:hover {
  transform: scale(1.02);
}

.logo-icon-squircle {
  width: 38px;
  height: 38px;
  border-radius: var(--apple-radius-icon);
  background: linear-gradient(135deg, #0071e3 0%, #42a5f5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.25);
}

.logo-text-wrap {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--apple-text-primary);
  white-space: nowrap;
}

.logo-caption {
  font-size: 11px;
  color: var(--apple-text-tertiary);
  font-weight: 500;
  white-space: nowrap;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.nav-item {
  text-decoration: none;
  color: var(--apple-text-secondary);
  font-size: 14px;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: var(--apple-radius-pill);
  transition: all var(--apple-transition-fast);
  white-space: nowrap;
}

.nav-item:hover {
  color: var(--apple-text-primary);
  background: rgba(0, 0, 0, 0.04);
}

.nav-item.active {
  color: var(--apple-blue);
  background: rgba(0, 113, 227, 0.08);
  font-weight: 600;
}

/* Center: Pill Search */
.header-center {
  flex: 1;
  max-width: 440px;
  min-width: 200px;
}

.search-capsule-box {
  display: flex;
  align-items: center;
  background: var(--apple-input-bg);
  border-radius: var(--apple-radius-pill);
  padding: 4px 6px 4px 14px;
  transition: all var(--apple-transition-fast);
  border: 1px solid transparent;
}

.search-capsule-box:focus-within {
  background: #FFFFFF;
  border-color: var(--apple-blue);
  box-shadow: 0 0 0 3px var(--apple-blue-glow);
}

.search-prefix-icon {
  width: 17px;
  height: 17px;
  color: var(--apple-text-tertiary);
  margin-right: 8px;
  flex-shrink: 0;
}

.apple-search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: var(--apple-text-primary);
}

.apple-search-input::placeholder {
  color: var(--apple-text-tertiary);
}

.search-submit-btn {
  background: var(--apple-gray-btn);
  color: var(--apple-text-primary);
  border: none;
  border-radius: var(--apple-radius-pill);
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--apple-transition-fast);
}

.search-submit-btn:hover {
  background: var(--apple-gray-btn-hover);
}

/* Right: Role Control & User State */
.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

/* Theme Switcher Pill */
.theme-switch-pill {
  display: flex;
  align-items: center;
  background: var(--apple-input-bg);
  padding: 2px;
  border-radius: var(--apple-radius-pill);
  gap: 2px;
  border: 1px solid var(--apple-hairline);
  flex-shrink: 0;
}

.theme-icon-btn {
  border: none;
  background: transparent;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--apple-text-secondary);
  transition: all var(--apple-transition-fast);
}

.theme-icon-btn:hover {
  color: var(--apple-text-primary);
  transform: scale(1.08);
}

.theme-icon-btn.active {
  background: var(--bg-card);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
  transform: scale(1.04);
}

/* Apple Segmented Control */
.role-segment-control {
  display: flex;
  background: var(--apple-input-bg);
  padding: 3px;
  border-radius: var(--apple-radius-pill);
  gap: 2px;
  border: 1px solid var(--apple-hairline);
  flex-shrink: 0;
}

.segment-btn {
  border: none;
  background: transparent;
  color: var(--apple-text-secondary);
  font-size: 11px;
  font-weight: 500;
  padding: 4px 7px;
  border-radius: var(--apple-radius-pill);
  cursor: pointer;
  transition: all var(--apple-transition-fast);
  white-space: nowrap;
}

.segment-btn:hover {
  color: var(--apple-text-primary);
}

.segment-btn.active {
  background: var(--bg-card);
  color: var(--apple-text-primary);
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

button:active, .nav-item:active, .segment-btn:active, .engine-settings-trigger-btn:active {
  transform: scale(0.96) !important;
}

.user-state-area {
  display: flex;
  align-items: center;
  gap: 10px;
}

.guest-label-pill {
  font-size: 12px;
  color: var(--apple-text-tertiary);
  background: rgba(0, 0, 0, 0.04);
  padding: 4px 10px;
  border-radius: var(--apple-radius-pill);
}

/* Apple Pill Buttons */
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

.apple-secondary-btn {
  background: var(--apple-gray-btn);
  color: var(--apple-text-primary);
  border: none;
  border-radius: var(--apple-radius-pill);
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--apple-transition-fast);
}

.apple-secondary-btn:hover {
  background: var(--apple-gray-btn-hover);
  transform: scale(1.02);
}

.engine-settings-trigger-btn {
  background: var(--liquid-glass-bg);
  backdrop-filter: var(--liquid-glass-blur);
  border: 1px solid rgba(0, 0, 0, 0.08);
  color: var(--bili-text-dark);
  border-radius: var(--apple-radius-pill);
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  flex-shrink: 0;
  transition: all var(--apple-transition-fast);
}

.engine-settings-trigger-btn:hover {
  background: #ffffff;
  border-color: var(--bili-blue);
  color: var(--bili-blue);
  transform: scale(1.02);
  box-shadow: 0 4px 14px var(--bili-blue-glow);
}

.creator-publish-btn {
  background: var(--bili-pink);
  box-shadow: 0 4px 14px var(--bili-pink-glow);
  white-space: nowrap;
  flex-shrink: 0;
}

.creator-publish-btn:hover {
  background: var(--bili-pink-hover);
  transform: scale(1.02);
}

/* Notification Skylight Bell Trigger */
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
  width: 36px;
  height: 36px;
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

/* User Profile Chip - Complete Style Hardening & Anti-Pollution */
.user-profile-chip,
.user-profile-chip:link,
.user-profile-chip:visited,
.user-profile-chip:hover,
.user-profile-chip:active {
  display: inline-flex !important;
  align-items: center !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  gap: 10px !important;
  background: rgba(0, 0, 0, 0.04) !important;
  padding: 4px 12px 4px 5px !important;
  border-radius: var(--apple-radius-pill) !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  text-decoration: none !important;
  color: inherit !important;
  cursor: pointer;
  flex-shrink: 0 !important;
  white-space: nowrap !important;
  transition: all 0.2s ease;
  line-height: normal !important;
  position: relative !important;
}

[data-theme="dark"] .user-profile-chip,
[data-theme="dark"] .user-profile-chip:visited {
  background: rgba(255, 255, 255, 0.08) !important;
  border-color: rgba(255, 255, 255, 0.12) !important;
  color: var(--apple-text-primary) !important;
}

.user-profile-chip:hover {
  background: rgba(0, 113, 227, 0.08) !important;
  border-color: rgba(0, 113, 227, 0.25) !important;
}

.chip-avatar {
  width: 26px !important;
  height: 26px !important;
  border-radius: 50% !important;
  background: #FFFFFF;
  flex-shrink: 0 !important;
  object-fit: cover;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.chip-info {
  display: inline-flex !important;
  align-items: center !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  gap: 8px !important;
  white-space: nowrap !important;
  flex-shrink: 0 !important;
  line-height: 1 !important;
}

.chip-name,
#user-display-name {
  display: inline-block !important;
  max-width: 110px !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  color: #1d1d1f !important;
  text-decoration: none !important;
  white-space: nowrap !important;
  line-height: 1.2 !important;
  flex-shrink: 1 !important;
  vertical-align: middle !important;
}

[data-theme="dark"] .chip-name,
[data-theme="dark"] #user-display-name {
  color: #f5f5f7 !important;
}

.chip-role,
#user-role-badge {
  display: inline-flex !important;
  align-items: center !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  padding: 2px 8px !important;
  border-radius: 12px !important;
  background: rgba(0, 113, 227, 0.08) !important;
  color: #0071e3 !important;
  border: 1px solid rgba(0, 113, 227, 0.22) !important;
  white-space: nowrap !important;
  line-height: 1.2 !important;
  flex-shrink: 0 !important;
  text-decoration: none !important;
  vertical-align: middle !important;
  letter-spacing: 0.2px !important;
}

.chip-role.user {
  background: rgba(0, 113, 227, 0.08) !important;
  color: #0071e3 !important;
  border-color: rgba(0, 113, 227, 0.22) !important;
}

[data-theme="dark"] .chip-role.user {
  background: rgba(0, 113, 227, 0.18) !important;
  color: #5ac8fa !important;
  border-color: rgba(0, 113, 227, 0.35) !important;
}

.chip-role.creator {
  background: rgba(52, 199, 89, 0.1) !important;
  color: #248a3d !important;
  border-color: rgba(52, 199, 89, 0.28) !important;
}

[data-theme="dark"] .chip-role.creator {
  background: rgba(52, 199, 89, 0.18) !important;
  color: #30d158 !important;
  border-color: rgba(52, 199, 89, 0.35) !important;
}

.chip-role.reviewer {
  background: rgba(255, 149, 0, 0.1) !important;
  color: #c97500 !important;
  border-color: rgba(255, 149, 0, 0.28) !important;
}

[data-theme="dark"] .chip-role.reviewer {
  background: rgba(255, 149, 0, 0.18) !important;
  color: #ff9f0a !important;
  border-color: rgba(255, 149, 0, 0.35) !important;
}

.chip-role.admin {
  background: rgba(255, 45, 85, 0.1) !important;
  color: #d70035 !important;
  border-color: rgba(255, 45, 85, 0.28) !important;
}

[data-theme="dark"] .chip-role.admin {
  background: rgba(255, 45, 85, 0.18) !important;
  color: #ff375f !important;
  border-color: rgba(255, 45, 85, 0.35) !important;
}

.chip-logout-btn {
  margin-left: 6px !important;
  font-size: 12px !important;
  padding: 4px 10px !important;
  border-radius: 12px !important;
  color: #6e6e73 !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  background: transparent !important;
  transition: all 0.2s !important;
}

.chip-logout-btn:hover {
  background: rgba(255, 59, 48, 0.08) !important;
  color: #ff3b30 !important;
  border-color: rgba(255, 59, 48, 0.25) !important;
}

[data-theme="dark"] .chip-logout-btn {
  color: rgba(255, 255, 255, 0.6) !important;
  border-color: rgba(255, 255, 255, 0.12) !important;
}

/* ========================================================================== */
/* Apple HIG Glassmorphism Auth Modal                                         */
/* ========================================================================== */
.apple-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.apple-modal-card {
  width: 90%;
  max-width: 440px;
  background: var(--bg-surface);
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
  border-radius: var(--apple-radius-card);
  border: 1px solid var(--border-glass);
  box-shadow: var(--glass-shadow-hover);
  padding: 32px;
  animation: modalScaleUp 0.3s var(--apple-ease);
}

@keyframes modalScaleUp {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.modal-title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-icon-squircle {
  width: 44px;
  height: 44px;
  border-radius: var(--apple-radius-icon);
  background: rgba(0, 113, 227, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.modal-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--apple-text-primary);
  letter-spacing: -0.02em;
}

.modal-subtitle {
  margin: 4px 0 0 0;
  font-size: 13px;
  color: var(--apple-text-tertiary);
}

.modal-close-icon-btn {
  border: none;
  background: var(--apple-input-bg);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 13px;
  color: var(--apple-text-secondary);
  cursor: pointer;
  transition: all var(--apple-transition-fast);
}

.modal-close-icon-btn:hover {
  background: var(--apple-gray-btn-hover);
  color: var(--apple-text-primary);
}

.modal-tab-segment {
  display: flex;
  background: var(--apple-input-bg);
  padding: 4px;
  border-radius: var(--apple-radius-pill);
  margin-bottom: 20px;
}

.tab-btn {
  flex: 1;
  border: none;
  background: transparent;
  padding: 8px 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--apple-text-secondary);
  border-radius: var(--apple-radius-pill);
  cursor: pointer;
  transition: all var(--apple-transition-fast);
}

.tab-btn.active {
  background: var(--bg-card);
  color: var(--apple-text-primary);
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.modal-error-banner {
  background: #ffebee;
  color: #c62828;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.form-field-group {
  margin-bottom: 16px;
}

.field-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--apple-text-secondary);
  margin-bottom: 6px;
}

.apple-form-input {
  width: 100%;
  border: none;
  outline: none;
  background: var(--apple-input-bg);
  padding: 12px 14px;
  border-radius: 12px;
  font-size: 14px;
  color: var(--apple-text-primary);
  transition: all var(--apple-transition-fast);
}

.apple-form-input:focus {
  background: #FFFFFF;
  box-shadow: 0 0 0 3px var(--apple-blue-glow);
}

.role-select-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.role-option-label {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--apple-input-bg);
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 13px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all var(--apple-transition-fast);
}

.role-option-label.selected {
  background: rgba(0, 113, 227, 0.08);
  border-color: var(--apple-blue);
  color: var(--apple-blue);
  font-weight: 600;
}

.modal-actions-row {
  margin-top: 24px;
}

.modal-submit-btn {
  width: 100%;
  padding: 12px 0;
  font-size: 15px;
  justify-content: center;
}

.test-accounts-helper {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--apple-hairline);
}

.helper-caption {
  font-size: 11px;
  color: var(--apple-text-tertiary);
  display: block;
  margin-bottom: 8px;
}

.helper-pills-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.helper-pill {
  border: none;
  background: var(--apple-input-bg);
  color: var(--apple-text-secondary);
  font-size: 11px;
  padding: 4px 10px;
  border-radius: var(--apple-radius-pill);
  cursor: pointer;
  transition: all var(--apple-transition-fast);
}

.helper-pill:hover {
  background: var(--apple-gray-btn-hover);
  color: var(--apple-text-primary);
}
</style>
