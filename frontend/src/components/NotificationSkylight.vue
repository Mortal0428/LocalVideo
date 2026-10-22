<template>
  <div v-if="modelValue" class="skylight-wrapper">
    <!-- Semi-transparent backdrop -->
    <div class="skylight-backdrop" @click="closeDrawer"></div>

    <!-- Apple HIG Frosted Glass Drawer -->
    <aside 
      class="notification-skylight-drawer" 
      id="notification-skylight-drawer"
      role="dialog"
      aria-label="通知天窗"
    >
      <!-- Header -->
      <header class="skylight-header">
        <div class="skylight-header-left">
          <div class="skylight-icon-squircle">
            <el-icon :size="16"><Bell /></el-icon>
          </div>
          <div>
            <h3 class="skylight-title">通知天窗</h3>
            <p class="skylight-subtitle">系统公告、评论回复与收到的赞</p>
          </div>
        </div>
        <div class="skylight-header-right">
          <button 
            type="button" 
            class="skylight-action-pill" 
            id="btn-skylight-mark-all-read" 
            :disabled="isMarkingAll || currentTabUnread === 0"
            @click="handleMarkAllRead"
          >
            <el-icon :size="12"><Check /></el-icon>
            <span>全部已读</span>
          </button>
          <button 
            type="button" 
            class="skylight-close-btn" 
            id="btn-close-skylight" 
            @click="closeDrawer"
            title="关闭天窗"
          >
            ✕
          </button>
        </div>
      </header>

      <!-- Category Tabs (3 tabs with unread badges) -->
      <div class="skylight-tab-bar" role="tablist">
        <button
          type="button"
          class="skylight-tab-btn"
          :class="{ active: activeCategory === 'ANNOUNCEMENT' }"
          id="skylight-tab-announcements"
          role="tab"
          :aria-selected="activeCategory === 'ANNOUNCEMENT'"
          @click="selectTab('ANNOUNCEMENT')"
        >
          <span>系统公告</span>
          <span 
            v-if="unreadCounts.announcements > 0" 
            class="skylight-tab-badge"
          >
            {{ unreadCounts.announcements > 99 ? '99+' : unreadCounts.announcements }}
          </span>
        </button>

        <button
          type="button"
          class="skylight-tab-btn"
          :class="{ active: activeCategory === 'REPLY' }"
          id="skylight-tab-replies"
          role="tab"
          :aria-selected="activeCategory === 'REPLY'"
          @click="selectTab('REPLY')"
        >
          <span>回复我的</span>
          <span 
            v-if="unreadCounts.replies > 0" 
            class="skylight-tab-badge"
          >
            {{ unreadCounts.replies > 99 ? '99+' : unreadCounts.replies }}
          </span>
        </button>

        <button
          type="button"
          class="skylight-tab-btn"
          :class="{ active: activeCategory === 'LIKE' }"
          id="skylight-tab-likes"
          role="tab"
          :aria-selected="activeCategory === 'LIKE'"
          @click="selectTab('LIKE')"
        >
          <span>收到的赞</span>
          <span 
            v-if="unreadCounts.likes > 0" 
            class="skylight-tab-badge"
          >
            {{ unreadCounts.likes > 99 ? '99+' : unreadCounts.likes }}
          </span>
        </button>
      </div>

      <!-- Feed Body -->
      <div class="skylight-body">
        <div v-if="isLoading" class="skylight-loading-state">
          <div class="skylight-spinner"></div>
          <span>加载最新通知...</span>
        </div>

        <div v-else-if="notifications.length === 0" class="skylight-empty-state">
          <div class="empty-icon-circle">
            <el-icon :size="24"><Check /></el-icon>
          </div>
          <span class="empty-title">暂无通知提醒</span>
          <p class="empty-desc">与剧迷深入互动、探讨剧情即可接收最新动态</p>
        </div>

        <div v-else class="skylight-list">
          <article
            v-for="item in notifications"
            :key="item.id"
            class="skylight-card"
            :class="{ unread: !item.is_read }"
            @click="handleNotificationClick(item)"
          >
            <!-- Unread Status Dot -->
            <span v-if="!item.is_read" class="unread-dot" aria-label="未读"></span>

            <div class="card-avatar-wrap">
              <img 
                v-if="item.sender_avatar" 
                :src="item.sender_avatar" 
                class="card-avatar-img" 
                alt="头像" 
              />
              <div v-else class="card-avatar-fallback">
                <el-icon :size="16">
                  <Notification v-if="item.category === 'ANNOUNCEMENT'" />
                  <ChatDotRound v-else-if="item.category === 'REPLY'" />
                  <StarFilled v-else />
                </el-icon>
              </div>
            </div>

            <div class="card-info-wrap">
              <div class="card-top-row">
                <span class="card-sender-name">{{ item.sender_name || '系统通知' }}</span>
                <time class="card-time-text">{{ item.created_at }}</time>
              </div>
              <h4 class="card-title">{{ item.title }}</h4>
              <p class="card-content-text">{{ item.content }}</p>
            </div>
          </article>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  notificationApi, 
  type UserNotificationItem, 
  type UnreadCountData 
} from '../api/user'
import { 
  Bell, 
  Check, 
  Notification, 
  ChatDotRound, 
  StarFilled 
} from '@element-plus/icons-vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    unreadCounts?: UnreadCountData
  }>(),
  {
    modelValue: false,
    unreadCounts: () => ({ total: 0, announcements: 0, replies: 0, likes: 0 })
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'unreadCountChanged'): void
}>()

const router = useRouter()

type CategoryType = 'ANNOUNCEMENT' | 'REPLY' | 'LIKE'
const activeCategory = ref<CategoryType>('ANNOUNCEMENT')
const notifications = ref<UserNotificationItem[]>([])
const isLoading = ref(false)
const isMarkingAll = ref(false)

const currentTabUnread = computed(() => {
  if (activeCategory.value === 'ANNOUNCEMENT') return props.unreadCounts.announcements
  if (activeCategory.value === 'REPLY') return props.unreadCounts.replies
  if (activeCategory.value === 'LIKE') return props.unreadCounts.likes
  return 0
})

function closeDrawer() {
  emit('update:modelValue', false)
}

function selectTab(cat: CategoryType) {
  activeCategory.value = cat
  fetchFeed(cat)
}

async function fetchFeed(cat: CategoryType) {
  isLoading.value = true
  try {
    const res = await notificationApi.getNotifications(cat, 1, 30)
    if (res?.data?.items) {
      notifications.value = res.data.items
    } else {
      notifications.value = []
    }
  } catch (err) {
    console.warn('Failed to load notifications:', err)
    notifications.value = []
  } finally {
    isLoading.value = false
  }
}

async function handleMarkAllRead() {
  if (isMarkingAll.value) return
  isMarkingAll.value = true
  try {
    await notificationApi.markAllRead(activeCategory.value)
    // Mark local items as read
    notifications.value.forEach(item => { item.is_read = true })
    emit('unreadCountChanged')
  } catch (err) {
    console.error('Failed to mark all read:', err)
  } finally {
    isMarkingAll.value = false
  }
}

async function handleNotificationClick(item: UserNotificationItem) {
  // 1. Mark single notification as read if unread
  if (!item.is_read) {
    try {
      await notificationApi.markRead(item.id)
      item.is_read = true
      emit('unreadCountChanged')
    } catch (e) {
      console.warn('Failed to mark notification read:', e)
    }
  }

  // 2. Direct jump according to notification type
  closeDrawer()

  if (item.category === 'REPLY') {
    if (item.video_id) {
      let url = `/play?videoId=${item.video_id}`
      if (item.episode_id) url += `&episodeId=${item.episode_id}`
      if (item.comment_id) url += `&commentId=${item.comment_id}`
      router.push(url)
    }
  } else if (item.category === 'LIKE') {
    if (item.video_id) {
      let url = `/play?videoId=${item.video_id}`
      if (item.episode_id) url += `&episodeId=${item.episode_id}`
      router.push(url)
    }
  } else if (item.category === 'ANNOUNCEMENT') {
    if (item.video_id) {
      router.push(`/play?videoId=${item.video_id}`)
    }
  }
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      fetchFeed(activeCategory.value)
    }
  }
)

onMounted(() => {
  if (props.modelValue) {
    fetchFeed(activeCategory.value)
  }
})
</script>

<style scoped>
.skylight-wrapper {
  position: fixed;
  inset: 0;
  z-index: 1005;
  pointer-events: auto;
}

.skylight-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  animation: fadeIn 0.2s ease forwards;
}

.notification-skylight-drawer {
  position: absolute;
  top: 72px;
  right: 24px;
  width: 420px;
  max-width: calc(100vw - 32px);
  max-height: calc(100vh - 96px);
  background: rgba(22, 22, 26, 0.88);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 18px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideDown 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

[data-theme="light"] .notification-skylight-drawer {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15), inset 0 1px 1px rgba(255, 255, 255, 0.9);
}

/* Header */
.skylight-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

[data-theme="light"] .skylight-header {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.skylight-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.skylight-icon-squircle {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #0071e3 0%, #42a5f5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0, 113, 227, 0.35);
}

.skylight-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--apple-text-primary);
  line-height: 1.2;
}

.skylight-subtitle {
  margin: 2px 0 0 0;
  font-size: 11px;
  color: var(--apple-text-tertiary);
}

.skylight-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.skylight-action-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--apple-text-primary);
  border-radius: var(--apple-radius-pill);
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

[data-theme="light"] .skylight-action-pill {
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.skylight-action-pill:hover:not(:disabled) {
  background: rgba(0, 113, 227, 0.15);
  border-color: rgba(0, 113, 227, 0.3);
  color: var(--apple-blue);
}

.skylight-action-pill:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.skylight-close-btn {
  background: transparent;
  border: none;
  font-size: 14px;
  color: var(--apple-text-tertiary);
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  transition: color 0.2s ease;
}

.skylight-close-btn:hover {
  color: var(--apple-text-primary);
}

/* Category Tabs */
.skylight-tab-bar {
  display: flex;
  padding: 10px 18px;
  gap: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

[data-theme="light"] .skylight-tab-bar {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.skylight-tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 10px;
  background: transparent;
  border: none;
  border-radius: var(--apple-radius-pill);
  color: var(--apple-text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.skylight-tab-btn:hover {
  color: var(--apple-text-primary);
  background: rgba(255, 255, 255, 0.05);
}

[data-theme="light"] .skylight-tab-btn:hover {
  background: rgba(0, 0, 0, 0.04);
}

.skylight-tab-btn.active {
  background: rgba(0, 113, 227, 0.15);
  color: var(--apple-blue);
  font-weight: 600;
}

.skylight-tab-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #ff3b30;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  line-height: 1;
}

/* Body */
.skylight-body {
  flex: 1;
  overflow-y: auto;
  max-height: 520px;
  padding: 12px 16px 16px;
}

.skylight-loading-state,
.skylight-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  color: var(--apple-text-tertiary);
  font-size: 13px;
  gap: 10px;
}

.empty-icon-circle {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--apple-text-tertiary);
}

[data-theme="light"] .empty-icon-circle {
  background: rgba(0, 0, 0, 0.04);
}

.empty-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--apple-text-primary);
}

.empty-desc {
  margin: 0;
  font-size: 12px;
  text-align: center;
  line-height: 1.4;
}

.skylight-spinner {
  width: 22px;
  height: 22px;
  border: 2px solid rgba(255, 255, 255, 0.15);
  border-top-color: var(--apple-blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* List & Cards */
.skylight-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skylight-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

[data-theme="light"] .skylight-card {
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.skylight-card:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateY(-1px);
}

[data-theme="light"] .skylight-card:hover {
  background: rgba(0, 0, 0, 0.05);
}

.skylight-card.unread {
  background: rgba(0, 113, 227, 0.08);
  border-color: rgba(0, 113, 227, 0.25);
}

.unread-dot {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff3b30;
  box-shadow: 0 0 6px rgba(255, 59, 48, 0.6);
}

.card-avatar-wrap {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
}

.card-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-avatar-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 113, 227, 0.15);
  color: var(--apple-blue);
}

.card-info-wrap {
  flex: 1;
  min-width: 0;
}

.card-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.card-sender-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--apple-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-time-text {
  font-size: 11px;
  color: var(--apple-text-tertiary);
  white-space: nowrap;
}

.card-title {
  margin: 4px 0 2px 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--apple-blue);
}

.card-content-text {
  margin: 0;
  font-size: 12px;
  color: var(--apple-text-secondary);
  line-height: 1.4;
  word-break: break-all;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-16px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
