<template>
  <header class="apple-admin-header" id="admin-header">
    <div class="admin-header-inner">
      <!-- Left: Management Branding & Cluster Indicator -->
      <div class="header-left">
        <div class="admin-brand-badge" id="admin-brand-badge">
          <div class="brand-icon-squircle">
            <el-icon :size="18">
              <Platform v-if="mode === 'admin'" />
              <VideoCamera v-else />
            </el-icon>
          </div>
          <div class="brand-text-wrap">
            <span class="brand-title">
              {{ mode === 'admin' ? 'CinemaAgent 控制中台' : 'CinemaAgent 创作者工作台' }}
            </span>
            <span class="brand-caption">
              {{ mode === 'admin' ? 'ENTERPRISE ADMIN' : 'CREATOR CLOUD STUDIO' }}
            </span>
          </div>
        </div>

        <div class="cluster-env-tag" id="cluster-env-tag">
          <span class="cluster-dot"></span>
          <span>生产集群 · 夸克/沃盘双驱动</span>
        </div>

        <!-- Optional Context Breadcrumb -->
        <div v-if="activeTabTitle" class="header-breadcrumb" id="header-breadcrumb-tag">
          <span class="breadcrumb-sep">/</span>
          <span class="breadcrumb-current">{{ activeTabTitle }}</span>
        </div>
      </div>

      <!-- Center: System Health & Model Telemetry Capsule -->
      <div class="header-center">
        <div 
          class="telemetry-capsule" 
          id="system-health-indicator"
          :class="{ 
            'is-healthy': telemetry.status === 'healthy',
            'is-degraded': telemetry.status === 'degraded',
            'is-down': telemetry.status === 'down'
          }"
          @click="toggleTelemetryPopover"
          title="点击查看大模型底层遥测与断路器状态"
        >
          <!-- Status Breathing Indicator -->
          <span 
            class="health-dot" 
            :class="{
              'pulse-green': telemetry.status === 'healthy',
              'pulse-yellow': telemetry.status === 'degraded',
              'pulse-red': telemetry.status === 'down'
            }"
          ></span>

          <!-- Health Status Label -->
          <span class="health-status-text">
            {{ telemetry.status === 'healthy' ? '系统服务在线正常' : telemetry.status === 'degraded' ? '服务降级运行中' : '系统故障离线' }}
          </span>

          <span class="capsule-divider"></span>

          <!-- Active Model Badge -->
          <div class="model-badge-inline">
            <el-icon :size="13" class="model-icon"><Cpu /></el-icon>
            <span class="model-name-text">{{ telemetry.active_provider }}: {{ telemetry.active_model }}</span>
          </div>

          <!-- Latency Badge -->
          <span class="latency-badge" :class="latencyClass">
            ⚡ {{ telemetry.latency_ms > 0 ? telemetry.latency_ms.toFixed(1) : '1.0' }}ms
          </span>

          <!-- Circuit Breaker State -->
          <span class="circuit-pill" :class="circuitClass">
            {{ telemetry.circuit_state || 'CLOSED' }}
          </span>
        </div>

        <!-- Telemetry Popover Dropdown -->
        <transition name="popover-fade">
          <div v-if="showTelemetryPopover" class="telemetry-popover-card" id="telemetry-popover-card">
            <div class="popover-header">
              <div class="popover-title">
                <el-icon><DataAnalysis /></el-icon>
                <span>全局 LLM 遥测与高可用网关</span>
              </div>
              <button class="popover-close-btn" @click="showTelemetryPopover = false">✕</button>
            </div>

            <div class="telemetry-grid">
              <div class="telemetry-metric-item">
                <span class="metric-label">当前活跃底座</span>
                <span class="metric-value highlight">{{ telemetry.active_provider }} / {{ telemetry.active_model }}</span>
              </div>
              <div class="telemetry-metric-item">
                <span class="metric-label">断路器状态</span>
                <span class="metric-value" :class="circuitClass">
                  {{ telemetry.circuit_state === 'CLOSED' ? 'CLOSED (熔断器闭合 · 就绪)' : telemetry.circuit_state === 'OPEN' ? 'OPEN (触发熔断 · 降级保护)' : 'HALF-OPEN (半开试探中)' }}
                </span>
              </div>
              <div class="telemetry-metric-item">
                <span class="metric-label">服务探针延迟</span>
                <span class="metric-value">{{ telemetry.latency_ms }} ms</span>
              </div>
              <div class="telemetry-metric-item">
                <span class="metric-label">系统累计运行时长</span>
                <span class="metric-value">{{ formatUptime(telemetry.uptime_seconds) }}</span>
              </div>
              <div class="telemetry-metric-item">
                <span class="metric-label">待审合规任务</span>
                <span class="metric-value">{{ telemetry.pending_reviews_count }} 件</span>
              </div>
              <div class="telemetry-metric-item">
                <span class="metric-label">连续异常次数</span>
                <span class="metric-value">{{ telemetry.consecutive_failures || 0 }} 次</span>
              </div>
            </div>

            <div class="popover-footer">
              <button 
                type="button" 
                class="refresh-telemetry-btn" 
                :disabled="isFetchingTelemetry" 
                @click="fetchTelemetry"
              >
                <el-icon :class="{ 'is-loading': isFetchingTelemetry }"><Refresh /></el-icon>
                <span>{{ isFetchingTelemetry ? '刷新遥测中...' : '即刻刷新遥测状态' }}</span>
              </button>
              <button 
                type="button" 
                class="configure-engine-btn" 
                @click="openEngineModal"
              >
                <el-icon><Setting /></el-icon>
                <span>配置模型底座</span>
              </button>
            </div>
          </div>
        </transition>
      </div>

      <!-- Right: Skylight Notifications, Theme Switcher, Engine Settings, Identity Card -->
      <div class="header-right">
        <!-- 1. Notification Skylight Trigger Button -->
        <div class="skylight-wrap">
          <button 
            type="button"
            class="skylight-btn"
            id="admin-notification-skylight-btn"
            :class="{ active: showSkylightDrawer }"
            @click="toggleSkylightDrawer"
            title="查看全局通知与中台待办"
          >
            <el-icon :size="16"><Bell /></el-icon>
            <span v-if="notificationBadgeCount > 0" class="skylight-badge-count">
              {{ notificationBadgeCount > 99 ? '99+' : notificationBadgeCount }}
            </span>
          </button>
        </div>

        <!-- 2. Theme Switcher Capsule (Light / Dark / Auto System) -->
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

        <!-- 3. Engine Settings Trigger Button (Admin Only) -->
        <button 
          v-if="mode === 'admin'"
          type="button"
          class="admin-engine-btn" 
          id="btn-engine-settings" 
          @click="showSettingsModal = true" 
          title="配置全局本地与云端模型引擎"
        >
          <el-icon class="btn-icon"><Setting /></el-icon>
          <span>引擎设置</span>
        </button>

        <!-- 4. User Profile / Identity Card -->
        <div class="admin-profile-wrapper">
          <div 
            class="admin-profile-chip" 
            id="admin-profile-chip" 
            @click="toggleProfileMenu"
            title="管理人员身份与工作台切换"
          >
            <img :src="userAvatar" class="chip-avatar" id="admin-avatar-img" />
            <div class="chip-info">
              <span class="chip-name" id="admin-display-name">{{ userDisplayName }}</span>
              <span class="chip-role" :class="userRoleClass" id="admin-role-badge">
                {{ userRoleLabel }}
              </span>
            </div>
            <el-icon :size="12" class="arrow-icon"><ArrowDown /></el-icon>
          </div>

          <!-- Profile Dropdown Menu -->
          <transition name="popover-fade">
            <div v-if="showProfileMenu" class="profile-dropdown-card" id="admin-profile-dropdown">
              <div class="dropdown-header">
                <div class="user-meta">
                  <div class="user-name">{{ userDisplayName }}</div>
                  <div class="user-sub">{{ currentUser?.username || '未登录' }} · {{ userRoleLabel }}</div>
                </div>
              </div>

              <div class="dropdown-body">
                <button type="button" class="dropdown-item" @click="goToSpectatorHall">
                  <el-icon><Film /></el-icon>
                  <span>前往观影大厅 (观众视角)</span>
                </button>

                <button 
                  v-if="mode === 'admin'" 
                  type="button" 
                  class="dropdown-item" 
                  @click="goToCreatorStudio"
                >
                  <el-icon><VideoCamera /></el-icon>
                  <span>切换至创作者工作台</span>
                </button>

                <button 
                  v-else 
                  type="button" 
                  class="dropdown-item" 
                  id="btn-creator-goto-bi"
                  @click="goToCreatorBI"
                >
                  <el-icon><DataAnalysis /></el-icon>
                  <span>BI 创作数据看板</span>
                </button>

                <div class="dropdown-divider"></div>

                <button type="button" class="dropdown-item logout-item" id="btn-logout" @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  <span>安全退出中台</span>
                </button>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <!-- Notification Skylight Drawer (Apple HIG Glassmorphism) -->
    <transition name="skylight-slide">
      <div 
        v-if="showSkylightDrawer" 
        class="notification-skylight-drawer" 
        id="notification-skyway-drawer"
      >
        <div class="skylight-header">
          <div class="skylight-title-box">
            <div class="skylight-icon-squircle">
              <el-icon :size="16"><Bell /></el-icon>
            </div>
            <div>
              <h4 class="skylight-title">全局通知与中台待办</h4>
              <p class="skylight-subtitle">实时监控机审合规任务、底座热重载及集群告警</p>
            </div>
          </div>
          <div class="skylight-actions">
            <span class="skylight-count-pill">{{ notificationItems.length }} 项提醒</span>
            <button class="skylight-close-btn" @click="showSkylightDrawer = false">✕</button>
          </div>
        </div>

        <div class="skylight-body">
          <div 
            v-for="(item, idx) in notificationItems" 
            :key="idx" 
            class="skylight-item-card"
            :class="item.level"
          >
            <div class="item-left-accent"></div>
            <div class="item-content-wrap">
              <div class="item-header-row">
                <span class="item-category-tag" :class="item.categoryClass">{{ item.category }}</span>
                <span class="item-time-text">{{ item.time }}</span>
              </div>
              <h5 class="item-title">{{ item.title }}</h5>
              <p class="item-desc">{{ item.description }}</p>
            </div>
            <div class="item-action-wrap">
              <button 
                type="button" 
                class="skylight-direct-btn"
                @click="handleSkylightDirect(item)"
              >
                <span>直达处理</span>
                <el-icon :size="12"><ArrowRight /></el-icon>
              </button>
            </div>
          </div>

          <div v-if="notificationItems.length === 0" class="skylight-empty-box">
            <el-icon :size="32" class="empty-icon"><CircleCheckFilled /></el-icon>
            <span class="empty-title">当前无待处理中台任务</span>
            <span class="empty-desc">所有系统服务及合规流转均正常运行</span>
          </div>
        </div>
      </div>
    </transition>

    <!-- Background Backdrop for Drawer & Popovers -->
    <div 
      v-if="showSkylightDrawer || showTelemetryPopover || showProfileMenu" 
      class="admin-header-backdrop" 
      @click="closeAllOverlays"
    ></div>

    <!-- Engine Settings Modal -->
    <EngineSettingsModal 
      v-model="showSettingsModal" 
      @updated="onEngineConfigUpdated"
    />
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from '../api/client'
import { useUserStore } from '../stores/user'
import { 
  Sunny, 
  Moon, 
  Monitor, 
  Setting, 
  Platform, 
  VideoCamera, 
  Cpu, 
  DataAnalysis, 
  Refresh, 
  Bell, 
  ArrowDown, 
  ArrowRight, 
  Film, 
  SwitchButton, 
  CircleCheckFilled
} from '@element-plus/icons-vue'
import EngineSettingsModal from './EngineSettingsModal.vue'

// Props & Emits
const props = withDefaults(defineProps<{
  mode?: 'admin' | 'creator'
  activeTab?: string
}>(), {
  mode: 'admin',
  activeTab: ''
})

const emit = defineEmits<{
  (e: 'selectTab', tab: string): void
  (e: 'userChanged', user: any): void
}>()

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// State
const currentUser = userStore.currentUser
const defaultAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=apple-admin'
const userAvatar = computed(() => currentUser.value?.avatar_url || defaultAvatar)
const userDisplayName = computed(() => currentUser.value?.nickname || currentUser.value?.username || (props.mode === 'admin' ? '系统管理员' : '签约创作者'))
const userRoleLabel = computed(() => {
  const role = currentUser.value?.role
  if (role === 'ADMIN') return '超级管理员'
  if (role === 'CREATOR') return '签约创作者'
  if (role === 'REVIEWER') return '社区审核员'
  return props.mode === 'admin' ? '超级管理员' : '签约创作者'
})
const userRoleClass = computed(() => {
  const role = currentUser.value?.role?.toLowerCase() || ''
  return role || (props.mode === 'admin' ? 'admin' : 'creator')
})

// Theme Switching
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

// Overlays state
const showTelemetryPopover = ref(false)
const showSkylightDrawer = ref(false)
const showProfileMenu = ref(false)
const showSettingsModal = ref(false)

const closeAllOverlays = () => {
  showTelemetryPopover.value = false
  showSkylightDrawer.value = false
  showProfileMenu.value = false
}

const toggleTelemetryPopover = () => {
  showTelemetryPopover.value = !showTelemetryPopover.value
  if (showTelemetryPopover.value) {
    showSkylightDrawer.value = false
    showProfileMenu.value = false
  }
}

const toggleSkylightDrawer = () => {
  showSkylightDrawer.value = !showSkylightDrawer.value
  if (showSkylightDrawer.value) {
    showTelemetryPopover.value = false
    showProfileMenu.value = false
  }
}

const toggleProfileMenu = () => {
  showProfileMenu.value = !showProfileMenu.value
  if (showProfileMenu.value) {
    showTelemetryPopover.value = false
    showSkylightDrawer.value = false
  }
}

// Telemetry State
interface SystemTelemetry {
  status: 'healthy' | 'degraded' | 'down'
  circuit_state: 'CLOSED' | 'OPEN' | 'HALF-OPEN'
  active_provider: string
  active_model: string
  latency_ms: number
  uptime_seconds: number
  pending_reviews_count: number
  consecutive_failures?: number
  recovery_countdown_seconds?: number
}

const telemetry = ref<SystemTelemetry>({
  status: 'healthy',
  circuit_state: 'CLOSED',
  active_provider: 'ollama',
  active_model: 'deepseek-r1:1.5b',
  latency_ms: 1.0,
  uptime_seconds: 86400,
  pending_reviews_count: 0,
  consecutive_failures: 0,
  recovery_countdown_seconds: 0
})

const isFetchingTelemetry = ref(false)

async function fetchTelemetry() {
  isFetchingTelemetry.value = true
  try {
    const res: any = await api.get('/system/telemetry')
    if (res && res.status) {
      telemetry.value = {
        status: res.status,
        circuit_state: res.circuit_state || 'CLOSED',
        active_provider: res.active_provider || 'ollama',
        active_model: res.active_model || 'deepseek-r1:1.5b',
        latency_ms: typeof res.latency_ms === 'number' ? res.latency_ms : 1.0,
        uptime_seconds: res.uptime_seconds || 86400,
        pending_reviews_count: res.pending_reviews_count || 0,
        consecutive_failures: res.consecutive_failures || 0,
        recovery_countdown_seconds: res.recovery_countdown_seconds || 0
      }
    }
  } catch (err) {
    console.warn('System telemetry fetch fallback:', err)
  } finally {
    isFetchingTelemetry.value = false
  }
}

let telemetryTimer: any = null

onMounted(async () => {
  const saved = (localStorage.getItem('cinema_theme') as any) || 'system'
  currentTheme.value = saved
  await userStore.refreshProfile()
  emit('userChanged', currentUser.value)
  await fetchTelemetry()
  telemetryTimer = setInterval(fetchTelemetry, 10000)
})

onUnmounted(() => {
  if (telemetryTimer) {
    clearInterval(telemetryTimer)
    telemetryTimer = null
  }
})

watch(() => route.path, async () => {
  await userStore.refreshProfile()
  emit('userChanged', currentUser.value)
})

const latencyClass = computed(() => {
  const lat = telemetry.value.latency_ms
  if (lat < 100) return 'latency-fast'
  if (lat < 500) return 'latency-normal'
  return 'latency-slow'
})

const circuitClass = computed(() => {
  const state = telemetry.value.circuit_state
  if (state === 'CLOSED') return 'circuit-closed'
  if (state === 'OPEN') return 'circuit-open'
  return 'circuit-half-open'
})

function formatUptime(seconds: number): string {
  if (!seconds || seconds <= 0) return '1天 0小时'
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (d > 0) return `${d}天 ${h}小时`
  if (h > 0) return `${h}小时 ${m}分钟`
  return `${m}分钟`
}

function openEngineModal() {
  showTelemetryPopover.value = false
  showSettingsModal.value = true
}

function onEngineConfigUpdated() {
  fetchTelemetry()
}

// Active Tab Display
const tabNameMap: Record<string, string> = {
  bi: 'BI 智能驾驶舱',
  dramas: '短剧资产编目',
  sync: '网盘集群同步',
  carousels: '首页焦点展架',
  users: '用户权限流转',
  applications: '入驻资质审核',
  contents: '互动合规机审',
  engine: '模型引擎底座',
  creator: '创作者工作台',
  disk: '网盘空间管理',
  upload: '视频原画上传'
}

const activeTabTitle = computed(() => {
  if (props.activeTab && tabNameMap[props.activeTab]) {
    return tabNameMap[props.activeTab]
  }
  return ''
})

// Skylight Notification Items
interface SkylightItem {
  id: string
  category: string
  categoryClass: string
  title: string
  description: string
  time: string
  level: 'info' | 'warning' | 'urgent'
  targetTab?: string
  targetRoute?: string
}

const notificationItems = computed<SkylightItem[]>(() => {
  const list: SkylightItem[] = []
  
  if (telemetry.value.pending_reviews_count > 0) {
    list.push({
      id: 'pending-reviews',
      category: '合规待办',
      categoryClass: 'cat-review',
      title: `有 ${telemetry.value.pending_reviews_count} 条待审核工单等待处置`,
      description: '包括弹幕违规关键词机审记录与创作者入驻申请。',
      time: '刚刚',
      level: 'warning',
      targetTab: 'contents'
    })
  } else {
    list.push({
      id: 'pending-reviews-clean',
      category: '合规治理',
      categoryClass: 'cat-review',
      title: '社区互动内容机审队列就绪',
      description: 'DFA 字典树前台实时拦截生效，未决弹幕工单均已处理完毕。',
      time: '实时',
      level: 'info',
      targetTab: 'contents'
    })
  }

  list.push({
    id: 'model-telemetry-ready',
    category: '模型底座',
    categoryClass: 'cat-engine',
    title: `当前算力引擎就绪 (${telemetry.value.active_provider}: ${telemetry.value.active_model})`,
    description: `断路器处于 ${telemetry.value.circuit_state} 模式，单次探测时延 ${telemetry.value.latency_ms}ms。`,
    time: '刚刚更新',
    level: 'info',
    targetTab: 'engine'
  })

  list.push({
    id: 'pan-cluster-active',
    category: '网盘集群',
    categoryClass: 'cat-storage',
    title: '夸克 · 沃盘双驱动分布式直连',
    description: 'HTTP 206 流式视频点播通道与大文件分片转存正常就绪。',
    time: '常驻在线',
    level: 'info',
    targetTab: 'sync'
  })

  return list
})

const notificationBadgeCount = computed(() => {
  return telemetry.value.pending_reviews_count > 0 ? telemetry.value.pending_reviews_count : 1
})

function handleSkylightDirect(item: SkylightItem) {
  showSkylightDrawer.value = false
  if (item.targetTab) {
    emit('selectTab', item.targetTab)
    if (props.mode === 'admin') {
      router.push({ path: '/admin', query: { tab: item.targetTab } })
    }
  } else if (item.targetRoute) {
    router.push(item.targetRoute)
  }
}

// User Actions
function goToSpectatorHall() {
  showProfileMenu.value = false
  router.push('/')
}

function goToCreatorStudio() {
  showProfileMenu.value = false
  router.push('/creator')
}

function goToCreatorBI() {
  showProfileMenu.value = false
  emit('selectTab', 'bi')
  router.push({ path: '/creator', query: { tab: 'bi' } })
}

function goToAdminConsole() {
  showProfileMenu.value = false
  router.push('/admin')
}

function handleLogout() {
  showProfileMenu.value = false
  userStore.clearUser()
  emit('userChanged', null)
  router.push('/login')
}
</script>

<style scoped>
/* ========================================================================== */
/* Apple HIG Management Header (Liquid Glass, Hairlines, Squircle)            */
/* ========================================================================== */
.apple-admin-header {
  position: sticky;
  top: 0;
  left: 0;
  width: 100%;
  height: 60px;
  z-index: 1000;
  background: var(--liquid-glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--apple-hairline);
  box-shadow: var(--glass-shadow);
  user-select: none;
  transition: background 0.3s ease, border-color 0.3s ease;
}

.admin-header-inner {
  max-width: 1920px;
  height: 100%;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

/* -------------------------------------------------------------------------- */
/* Left: Branding & Cluster Status                                            */
/* -------------------------------------------------------------------------- */
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.admin-brand-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.brand-icon-squircle {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0071E3 0%, #0051A8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFFFFF;
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.3);
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.admin-brand-badge:hover .brand-icon-squircle {
  transform: scale(1.04);
}

.brand-text-wrap {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--apple-text-primary);
  letter-spacing: -0.2px;
  line-height: 1.2;
}

.brand-caption {
  font-size: 10px;
  font-weight: 600;
  color: var(--apple-text-tertiary);
  letter-spacing: 0.8px;
  margin-top: 2px;
}

.cluster-env-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 12px;
  background: rgba(0, 113, 227, 0.08);
  border: 1px solid rgba(0, 113, 227, 0.2);
  font-size: 11px;
  font-weight: 500;
  color: var(--apple-blue);
}

.cluster-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #34C759;
  box-shadow: 0 0 6px rgba(52, 199, 89, 0.7);
}

.header-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--apple-text-secondary);
}

.breadcrumb-sep {
  color: var(--apple-text-tertiary);
  opacity: 0.6;
}

.breadcrumb-current {
  font-weight: 600;
  color: var(--apple-text-primary);
}

/* -------------------------------------------------------------------------- */
/* Center: System Health & Telemetry Capsule                                  */
/* -------------------------------------------------------------------------- */
.header-center {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.telemetry-capsule {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 14px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid var(--apple-hairline);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

[data-theme="dark"] .telemetry-capsule {
  background: rgba(30, 30, 32, 0.65);
}

.telemetry-capsule:hover {
  background: rgba(255, 255, 255, 0.85);
  border-color: rgba(0, 113, 227, 0.4);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
}

[data-theme="dark"] .telemetry-capsule:hover {
  background: rgba(45, 45, 48, 0.9);
}

.health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.pulse-green {
  background: #34C759;
  box-shadow: 0 0 8px rgba(52, 199, 89, 0.8);
  animation: pulseGreen 2.2s infinite ease-in-out;
}

.pulse-yellow {
  background: #FF9500;
  box-shadow: 0 0 8px rgba(255, 149, 0, 0.8);
  animation: pulseYellow 1.8s infinite ease-in-out;
}

.pulse-red {
  background: #FF3B30;
  box-shadow: 0 0 8px rgba(255, 59, 48, 0.8);
  animation: pulseRed 1.2s infinite ease-in-out;
}

@keyframes pulseGreen {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 199, 89, 0.7); }
  70% { transform: scale(1.1); box-shadow: 0 0 0 6px rgba(52, 199, 89, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 199, 89, 0); }
}

@keyframes pulseYellow {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 149, 0, 0.7); }
  70% { transform: scale(1.1); box-shadow: 0 0 0 6px rgba(255, 149, 0, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 149, 0, 0); }
}

@keyframes pulseRed {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.7); }
  70% { transform: scale(1.15); box-shadow: 0 0 0 8px rgba(255, 59, 48, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 59, 48, 0); }
}

.health-status-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--apple-text-primary);
  white-space: nowrap;
}

.capsule-divider {
  width: 1px;
  height: 12px;
  background: var(--apple-hairline);
}

.model-badge-inline {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 500;
  color: var(--apple-text-secondary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.latency-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.latency-fast {
  background: rgba(52, 199, 89, 0.12);
  color: #248A3D;
}
[data-theme="dark"] .latency-fast {
  color: #34C759;
}

.latency-normal {
  background: rgba(255, 149, 0, 0.12);
  color: #C97700;
}
[data-theme="dark"] .latency-normal {
  color: #FF9500;
}

.latency-slow {
  background: rgba(255, 59, 48, 0.12);
  color: #D70015;
}

.circuit-pill {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 6px;
  letter-spacing: 0.5px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.circuit-closed {
  background: rgba(52, 199, 89, 0.15);
  color: #248A3D;
  border: 1px solid rgba(52, 199, 89, 0.3);
}
[data-theme="dark"] .circuit-closed {
  color: #34C759;
}

.circuit-open {
  background: rgba(255, 59, 48, 0.15);
  color: #D70015;
  border: 1px solid rgba(255, 59, 48, 0.3);
}

.circuit-half-open {
  background: rgba(255, 149, 0, 0.15);
  color: #C97700;
  border: 1px solid rgba(255, 149, 0, 0.3);
}

/* -------------------------------------------------------------------------- */
/* Telemetry Popover Card                                                     */
/* -------------------------------------------------------------------------- */
.telemetry-popover-card {
  position: absolute;
  top: 50px;
  left: 50%;
  transform: translateX(-50%);
  width: 440px;
  background: var(--bg-card);
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid var(--apple-hairline);
  border-radius: 16px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.14);
  padding: 16px;
  z-index: 1010;
}

.popover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--apple-hairline);
}

.popover-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--apple-text-primary);
}

.popover-close-btn {
  background: none;
  border: none;
  font-size: 14px;
  color: var(--apple-text-tertiary);
  cursor: pointer;
}

.telemetry-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 14px 0;
}

.telemetry-metric-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: rgba(0, 0, 0, 0.02);
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid var(--apple-hairline);
}

[data-theme="dark"] .telemetry-metric-item {
  background: rgba(255, 255, 255, 0.03);
}

.metric-label {
  font-size: 11px;
  color: var(--apple-text-secondary);
}

.metric-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--apple-text-primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.metric-value.highlight {
  color: var(--apple-blue);
}

.popover-footer {
  display: flex;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--apple-hairline);
}

.refresh-telemetry-btn,
.configure-engine-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.refresh-telemetry-btn {
  background: var(--input-bg);
  border: 1px solid var(--apple-hairline);
  color: var(--apple-text-primary);
}

.refresh-telemetry-btn:hover:not(:disabled) {
  background: var(--border-line);
}

.configure-engine-btn {
  background: var(--apple-blue);
  border: none;
  color: #FFFFFF;
}

.configure-engine-btn:hover {
  filter: brightness(1.08);
}

/* -------------------------------------------------------------------------- */
/* Right: Controls & Profile                                                  */
/* -------------------------------------------------------------------------- */
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

/* Skylight Button */
.skylight-wrap {
  position: relative;
}

.skylight-btn {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid var(--apple-hairline);
  color: var(--apple-text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

[data-theme="dark"] .skylight-btn {
  background: rgba(255, 255, 255, 0.05);
}

.skylight-btn:hover,
.skylight-btn.active {
  background: rgba(0, 113, 227, 0.12);
  color: var(--apple-blue);
  border-color: rgba(0, 113, 227, 0.3);
}

.skylight-badge-count {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #FF3B30;
  color: #FFFFFF;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(255, 59, 48, 0.4);
}

/* Theme Switch Pill */
.theme-switch-pill {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 3px;
  border-radius: 18px;
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid var(--apple-hairline);
}

[data-theme="dark"] .theme-switch-pill {
  background: rgba(255, 255, 255, 0.06);
}

.theme-icon-btn {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--apple-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.theme-icon-btn.active {
  background: #FFFFFF;
  color: var(--apple-text-primary);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

[data-theme="dark"] .theme-icon-btn.active {
  background: #2C2C2E;
  color: #FFFFFF;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
}

/* Engine Settings Button */
.admin-engine-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 10px;
  background: rgba(0, 113, 227, 0.08);
  border: 1px solid rgba(0, 113, 227, 0.2);
  color: var(--apple-blue);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.admin-engine-btn:hover {
  background: rgba(0, 113, 227, 0.16);
  border-color: rgba(0, 113, 227, 0.4);
}

/* Admin Profile Chip */
.admin-profile-wrapper {
  position: relative;
}

.admin-profile-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 10px 4px 5px;
  border-radius: 20px;
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid var(--apple-hairline);
  cursor: pointer;
  transition: all 0.2s ease;
}

[data-theme="dark"] .admin-profile-chip {
  background: rgba(255, 255, 255, 0.05);
}

.admin-profile-chip:hover {
  background: rgba(0, 0, 0, 0.08);
  border-color: var(--apple-hairline);
}

[data-theme="dark"] .admin-profile-chip:hover {
  background: rgba(255, 255, 255, 0.1);
}

.chip-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--apple-hairline);
}

.chip-info {
  display: flex;
  flex-direction: column;
}

.chip-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--apple-text-primary);
  line-height: 1.2;
}

.chip-role {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.3px;
  line-height: 1;
  margin-top: 2px;
}

.chip-role.admin {
  color: #0071E3;
}

.chip-role.creator {
  color: #FF2D55;
}

.arrow-icon {
  color: var(--apple-text-tertiary);
  transition: transform 0.2s ease;
}

/* Profile Dropdown */
.profile-dropdown-card {
  position: absolute;
  top: 48px;
  right: 0;
  width: 230px;
  background: var(--bg-card);
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid var(--apple-hairline);
  border-radius: 14px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.14);
  padding: 8px;
  z-index: 1010;
}

.dropdown-header {
  padding: 8px 10px 10px 10px;
  border-bottom: 1px solid var(--apple-hairline);
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--apple-text-primary);
}

.user-sub {
  font-size: 11px;
  color: var(--apple-text-secondary);
  margin-top: 2px;
}

.dropdown-body {
  padding-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--apple-text-primary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s ease;
}

.dropdown-item:hover {
  background: var(--input-bg);
}

.dropdown-divider {
  height: 1px;
  background: var(--apple-hairline);
  margin: 4px 0;
}

.dropdown-item.logout-item {
  color: #FF3B30;
}

.dropdown-item.logout-item:hover {
  background: rgba(255, 59, 48, 0.08);
}

/* -------------------------------------------------------------------------- */
/* Notification Skylight Drawer (Top-Down Slide)                              */
/* -------------------------------------------------------------------------- */
.notification-skylight-drawer {
  position: fixed;
  top: 60px;
  right: 24px;
  width: 420px;
  max-height: calc(100vh - 80px);
  background: var(--bg-card);
  backdrop-filter: blur(32px);
  -webkit-backdrop-filter: blur(32px);
  border: 1px solid var(--apple-hairline);
  border-radius: 18px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  z-index: 1010;
  overflow: hidden;
}

.skylight-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--apple-hairline);
  background: var(--liquid-glass-bg);
}

.skylight-title-box {
  display: flex;
  align-items: center;
  gap: 12px;
}

.skylight-icon-squircle {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #FF9500 0%, #FF5E3A 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFFFFF;
}

.skylight-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--apple-text-primary);
  margin: 0;
}

.skylight-subtitle {
  font-size: 11px;
  color: var(--apple-text-tertiary);
  margin: 2px 0 0 0;
}

.skylight-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.skylight-count-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255, 149, 0, 0.12);
  color: #FF9500;
}

.skylight-close-btn {
  background: none;
  border: none;
  font-size: 15px;
  color: var(--apple-text-tertiary);
  cursor: pointer;
  padding: 4px;
}

.skylight-body {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  max-height: 520px;
}

.skylight-item-card {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px 12px 16px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid var(--apple-hairline);
  transition: all 0.2s ease;
}

[data-theme="dark"] .skylight-item-card {
  background: rgba(255, 255, 255, 0.03);
}

.skylight-item-card:hover {
  background: var(--input-bg);
  border-color: rgba(0, 113, 227, 0.3);
  transform: translateY(-1px);
}

.item-left-accent {
  position: absolute;
  left: 0;
  top: 10px;
  bottom: 10px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: #0071E3;
}

.skylight-item-card.warning .item-left-accent {
  background: #FF9500;
}

.skylight-item-card.urgent .item-left-accent {
  background: #FF3B30;
}

.item-content-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.item-category-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
}

.cat-review {
  background: rgba(255, 149, 0, 0.12);
  color: #FF9500;
}

.cat-engine {
  background: rgba(0, 113, 227, 0.12);
  color: #0071E3;
}

.cat-storage {
  background: rgba(52, 199, 89, 0.12);
  color: #34C759;
}

.item-time-text {
  font-size: 10px;
  color: var(--apple-text-tertiary);
}

.item-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--apple-text-primary);
  margin: 0;
  line-height: 1.3;
}

.item-desc {
  font-size: 11px;
  color: var(--apple-text-secondary);
  margin: 0;
  line-height: 1.4;
}

.item-action-wrap {
  flex-shrink: 0;
}

.skylight-direct-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 8px;
  background: var(--apple-blue);
  border: none;
  color: #FFFFFF;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.skylight-direct-btn:hover {
  filter: brightness(1.1);
  transform: translateX(1px);
}

.skylight-empty-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 8px;
  color: var(--apple-text-tertiary);
}

.empty-icon {
  color: #34C759;
}

.empty-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--apple-text-primary);
}

.empty-desc {
  font-size: 11px;
}

/* Background overlay */
.admin-header-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1005;
  background: transparent;
}

/* Transitions */
.popover-fade-enter-active,
.popover-fade-leave-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.popover-fade-enter-from,
.popover-fade-leave-to {
  opacity: 0;
  transform: translate(-50%, -6px);
}

.profile-dropdown-card.popover-fade-enter-from,
.profile-dropdown-card.popover-fade-leave-to {
  transform: translateY(-6px);
}

.skylight-slide-enter-active,
.skylight-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.skylight-slide-enter-from,
.skylight-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
</style>
