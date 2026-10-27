<template>
  <div class="floating-companion-pet-root" id="floating-pet-container" :style="containerStyle" :class="{ 'near-top': isNearTop, 'near-left': isNearLeft }">
    <!-- 1. 灵宠伴看全功能交互对话抽屉/小窗 (可展开/挂起收纳) -->
    <transition name="chat-slide-fade">
      <div v-if="isChatOpen" class="pet-companion-chat-window" id="pet-companion-chat-window">
        <!-- 窗口顶栏 -->
        <div class="chat-win-header">
          <div class="header-left">
            <span class="pet-status-dot"></span>
            <div class="pet-title-meta">
              <span class="pet-title-name">{{ petProfile.pet_name || '星瞳' }}</span>
              <span class="pet-lvl-pill" id="floating-pet-lvl-pill">Lv.{{ petProfile.growth_level || petProfile.level || 1 }}</span>
              <span class="pet-mood-pill">好感度 {{ petProfile.mood_score || 88 }}</span>
            </div>
          </div>
          <div class="header-right">
            <button
              type="button"
              class="win-ctrl-btn"
              @click="toggleChat"
              title="最小化挂回后台"
              id="btn-dock-pet-chat"
            >
              _
            </button>
            <button
              type="button"
              class="win-ctrl-btn close"
              @click="isChatOpen = false"
              title="收起对话"
              id="btn-close-pet-chat"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- 顶部快捷操作栏 (投喂、戳一戳、清空) -->
        <div class="chat-win-toolbar">
          <button
            type="button"
            class="toolbar-pill-btn feed"
            id="btn-pet-win-feed"
            :disabled="isFeeding"
            @click="quickFeedCoin(10)"
          >
            {{ isFeeding ? '投喂中...' : '投喂 10 金币 (+成长)' }}
          </button>
          <button
            type="button"
            class="toolbar-pill-btn poke"
            id="btn-pet-win-poke"
            @click="pokePet"
          >
            戳一戳
          </button>
          <button
            type="button"
            class="toolbar-pill-btn clear"
            @click="clearHistory"
            title="清空当前滑动窗口"
          >
            重置记忆
          </button>
        </div>

        <!-- 对话消息滚动流 (保持 5~10 轮滑动窗口) -->
        <div class="chat-messages-container" ref="messageScrollRef">
          <div
            v-for="(msg, idx) in chatMessages"
            :key="idx"
            class="chat-bubble-row"
            :class="msg.role"
          >
            <div class="chat-avatar-chip">
              {{ msg.role === 'assistant' ? '✦' : '我' }}
            </div>
            <div class="chat-bubble-content">
              <div v-if="msg.thought" class="pet-thought-crumb">
                思考：{{ msg.thought }}
              </div>
              <div class="chat-bubble-text">{{ msg.content }}</div>
              <span class="chat-time-tag">{{ msg.time || '刚刚' }}</span>
            </div>
          </div>
          <div v-if="isResponding" class="chat-bubble-row assistant">
            <div class="chat-avatar-chip">✦</div>
            <div class="chat-bubble-content typing">
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
            </div>
          </div>
        </div>

        <!-- 快捷追问药丸 -->
        <div class="quick-prompts-row">
          <button
            v-for="(qp, qIdx) in quickQuestions"
            :key="qIdx"
            type="button"
            class="quick-pill-btn"
            @click="sendPresetQuestion(qp)"
          >
            {{ qp }}
          </button>
        </div>

        <!-- 输入底栏 -->
        <div class="chat-win-input-bar">
          <input
            v-model="inputQuery"
            type="text"
            class="pet-chat-input"
            id="input-floating-pet-chat"
            placeholder="和灵宠星瞳聊聊你最近看的短剧..."
            :disabled="isResponding"
            @keyup.enter="handleSend"
          />
          <button
            type="button"
            class="pet-chat-send-btn"
            id="btn-send-floating-pet"
            :disabled="isResponding || !inputQuery.trim()"
            @click="handleSend"
          >
            发送
          </button>
        </div>
      </div>
    </transition>

    <!-- 2. 迷你气泡提示 (未展开大窗时出现) -->
    <transition name="pop-fade">
      <div v-if="showBubble && !isChatOpen" class="pet-speech-bubble" id="pet-speech-bubble-box">
        <div class="bubble-header">
          <span class="pet-name-tag">{{ petProfile.pet_name || '星瞳' }}</span>
          <span class="pet-lvl-tag">Lv.{{ petProfile.growth_level || petProfile.level || 1 }}</span>
          <button class="bubble-close-btn" @click="showBubble = false">✕</button>
        </div>
        <p class="bubble-text">{{ currentSpeech }}</p>

        <div class="bubble-actions">
          <button class="btn-bubble-action chat" id="btn-open-pet-dialog" @click="toggleChat">
            开启伴聊
          </button>
          <button class="btn-bubble-action feed" id="btn-pet-quick-feed" @click="quickFeedCoin(10)">
            投喂10金币
          </button>
          <button class="btn-bubble-action poke" @click="pokePet">
            戳一戳
          </button>
        </div>
      </div>
    </transition>

    <!-- 3. 动态灵宠主体 (可点击交互、呼吸浮动) -->
    <div
      class="pet-avatar-character"
      id="pet-avatar-main"
      :class="{ 'is-poked': isPoking, 'is-happy': isHappy, 'is-chat-active': isChatOpen, 'is-dragging': isDragging }"
      @pointerdown="onPointerDown"
      title="按住拖拽自由移动灵宠位置，点击开启/收起伴聊"
    >
      <div class="pet-glow-aura"></div>
      <div class="pet-ears">
        <span class="ear left"></span>
        <span class="ear right"></span>
      </div>
      <div class="pet-face">
        <div class="pet-eyes">
          <span class="eye left"></span>
          <span class="eye right"></span>
        </div>
        <div class="pet-blush"></div>
        <div class="pet-mouth"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const route = useRoute()

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  thought?: string
  time?: string
}

const isChatOpen = ref(false)
const showBubble = ref(false)
const isPoking = ref(false)
const isHappy = ref(false)
const isFeeding = ref(false)
const isResponding = ref(false)
const inputQuery = ref('')
const messageScrollRef = ref<HTMLElement | null>(null)

const petProfile = ref<any>({
  pet_name: '星瞳 (小灵宠)',
  growth_level: 1,
  level: 1,
  exp: 0,
  mood_score: 88,
  favorite_genres: ['都市逆袭', '高能反转'],
})

const currentSpeech = ref('主人主人！今天想看什么高能反转短剧呀？星瞳一直陪着你！')

const quickQuestions = [
  '推荐最近高分反转短剧',
  '刚才主角的表现有伏笔吗？',
  '夸夸我的看剧品味',
]

const defaultSpeeches = [
  '主人！听说新上的反转悬疑剧很刺激，我们要不要去看看？',
  '看剧记得保护眼睛哦，星瞳一直都在主人身边！',
  '刚才那个反转镜头真是太爽了！真不愧是主人喜欢的好剧！',
  '(星瞳开心地晃了晃尾巴) 主人的品味永远是最好的！',
]

// 保持 5~10 轮滑动窗口记忆（最大 10 条消息）
const MAX_SLIDING_WINDOW_TURNS = 10
const chatMessages = ref<ChatMessage[]>([
  {
    role: 'assistant',
    content: '主人好！我是您的专属 2 号伴看灵宠星瞳。今天有什么关于短剧名场面、反转推测或剧情疑问想和我聊聊吗？',
    time: '刚才',
  },
])

function getAuthHeaders() {
  const token = localStorage.getItem('token') || localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function scrollToBottom() {
  nextTick(() => {
    if (messageScrollRef.value) {
      messageScrollRef.value.scrollTop = messageScrollRef.value.scrollHeight
    }
  })
}

// 统一数据源：从 MySQL 权威接口加载真实等级与人设
async function loadPetData() {
  try {
    const res = await axios.get('/api/v1/agent-hub/pet', {
      headers: getAuthHeaders(),
    })
    if (res.data?.data) {
      const d = res.data.data
      petProfile.value = {
        ...d,
        growth_level: d.level || 1,
        level: d.level || 1,
      }
    }
  } catch (e) {
    console.warn('Failed to load pet data from agent-hub:', e)
  }
}

function handlePetAvatarClick() {
  toggleChat()
}

function toggleChat() {
  isChatOpen.value = !isChatOpen.value
  if (isChatOpen.value) {
    loadPetData()
    showBubble.value = false
    scrollToBottom()
  }
}

watch(() => route?.path, () => {
  loadPetData()
})

function pokePet() {
  isPoking.value = true
  isHappy.value = true
  currentSpeech.value = '(被戳了一下，高兴地翻了个跟头) 嘻嘻，好痒呀主人！'
  if (isChatOpen.value) {
    chatMessages.value.push({
      role: 'assistant',
      content: '(星瞳被你戳了一下，两只耳朵摇了摇，开心地转了个圈) 主人是在想我吗？',
      time: '刚刚',
    })
    trimSlidingWindow()
    scrollToBottom()
  }
  setTimeout(() => {
    isPoking.value = false
    isHappy.value = false
  }, 1200)
}

async function quickFeedCoin(amount: number = 10) {
  if (isFeeding.value) return
  isFeeding.value = true
  try {
    const res = await axios.post(
      '/api/v1/agent-hub/pet/feed',
      { coin_amount: amount, coins_to_feed: amount },
      { headers: getAuthHeaders() }
    )
    const petData = res.data?.data || {}
    const newLevel = petData.level || petData.pet_level || (petProfile.value.growth_level + 1)
    petProfile.value.growth_level = newLevel
    petProfile.value.level = newLevel
    petProfile.value.exp = petData.exp || 0
    petProfile.value.mood_score = petData.mood_score || 95

    ElMessage.success(res.data?.message || `投喂成功！星瞳升级至 Lv.${newLevel}`)
    isHappy.value = true
    currentSpeech.value = `太好吃啦！谢谢主人的投喂，星瞳感觉又进化到了 Lv.${newLevel}！`

    if (isChatOpen.value) {
      chatMessages.value.push({
        role: 'assistant',
        content: `(美美饱餐了一顿金币大餐) 谢谢主人的投喂！星瞳经验大涨，当前等级已升至 Lv.${newLevel}！一定会更加努力陪伴主人看剧！`,
        time: '刚刚',
      })
      trimSlidingWindow()
      scrollToBottom()
    }

    // 跨组件事件通知，确保个人中心太空舱同步更新
    window.dispatchEvent(new CustomEvent('pet-level-updated', { detail: petData }))

    setTimeout(() => {
      isHappy.value = false
    }, 1500)
  } catch (e: any) {
    const detail = e.response?.data?.detail || e.message || '金币不足'
    ElMessage.warning(`投喂失败：${detail}。前往个人中心每日签到领金币吧！`)
  } finally {
    isFeeding.value = false
  }
}

function trimSlidingWindow() {
  if (chatMessages.value.length > MAX_SLIDING_WINDOW_TURNS) {
    chatMessages.value = chatMessages.value.slice(-MAX_SLIDING_WINDOW_TURNS)
  }
}

function clearHistory() {
  chatMessages.value = [
    {
      role: 'assistant',
      content: '记忆已刷新。主人，现在想聊聊哪部短剧？',
      time: '刚才',
    },
  ]
  ElMessage.success('灵宠对话记忆已清空重置')
}

function sendPresetQuestion(q: string) {
  inputQuery.value = q
  handleSend()
}

async function handleSend() {
  const query = inputQuery.value.trim()
  if (!query || isResponding.value) return

  chatMessages.value.push({
    role: 'user',
    content: query,
    time: '刚刚',
  })
  inputQuery.value = ''
  trimSlidingWindow()
  scrollToBottom()

  isResponding.value = true
  try {
    const res = await axios.post(
      '/api/v1/agent-hub/dispatch',
      {
        agent_id: 'agent_2',
        query: query,
        session_id: `pet_session_${getCurrentUserId()}`,
      },
      { headers: getAuthHeaders() }
    )
    const data = res.data?.data || {}
    chatMessages.value.push({
      role: 'assistant',
      content: data.answer || '星瞳收到啦！感觉这个剧情确实很精彩！',
      thought: data.thought_chain || '',
      time: '刚刚',
    })
    trimSlidingWindow()
    scrollToBottom()
  } catch (err: any) {
    chatMessages.value.push({
      role: 'assistant',
      content: '(星瞳抖了抖小耳朵) 哎呀，刚才信号开小差了，主人能再说一遍吗？',
      time: '刚刚',
    })
    scrollToBottom()
  } finally {
    isResponding.value = false
  }
}

function handleGlobalPetSync(evt: any) {
  if (evt?.detail?.level) {
    petProfile.value.level = evt.detail.level
    petProfile.value.growth_level = evt.detail.level
  }
}

// ==================== 用户隔离与自由拖拽算法 ====================
function getCurrentUserId(): string {
  try {
    const rawUser = localStorage.getItem('cinema_user') || localStorage.getItem('user')
    if (rawUser) {
      const parsed = JSON.parse(rawUser)
      if (parsed.id) return String(parsed.id)
    }
  } catch (e) {}
  return 'default_user'
}

function loadLocalChatHistory() {
  const uid = getCurrentUserId()
  const saved = localStorage.getItem(`cinema_pet_history_${uid}`)
  if (saved) {
    try {
      const list = JSON.parse(saved)
      if (Array.isArray(list) && list.length > 0) {
        chatMessages.value = list
        return
      }
    } catch (e) {}
  }
  chatMessages.value = [
    {
      role: 'assistant',
      content: '主人好！我是您的专属 2 号伴看灵宠星瞳。今天有什么关于短剧名场面、反转推测或剧情疑问想和我聊聊吗？',
      time: '刚才',
    },
  ]
}

function saveLocalChatHistory() {
  const uid = getCurrentUserId()
  localStorage.setItem(`cinema_pet_history_${uid}`, JSON.stringify(chatMessages.value))
}

const pos = ref({ x: typeof window !== 'undefined' ? window.innerWidth - 100 : 800, y: typeof window !== 'undefined' ? window.innerHeight - 120 : 600 })
const isDragging = ref(false)
let isPointerDown = false
let startPointerX = 0
let startPointerY = 0
let startPosX = 0
let startPosY = 0

function clampPosition(x: number, y: number) {
  if (typeof window === 'undefined') return { x, y }
  const minX = 10
  const maxX = Math.max(minX, window.innerWidth - 88)
  const minY = 10
  const maxY = Math.max(minY, window.innerHeight - 88)
  return {
    x: Math.min(Math.max(x, minX), maxX),
    y: Math.min(Math.max(y, minY), maxY),
  }
}

function initPosition() {
  if (typeof window === 'undefined') return
  const uid = getCurrentUserId()
  const saved = localStorage.getItem(`cinema_pet_pos_${uid}`)
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      if (typeof parsed.x === 'number' && typeof parsed.y === 'number') {
        pos.value = clampPosition(parsed.x, parsed.y)
        return
      }
    } catch (e) {}
  }
  pos.value = clampPosition(window.innerWidth - 96, window.innerHeight - 110)
}

function handleResize() {
  pos.value = clampPosition(pos.value.x, pos.value.y)
}

function onPointerDown(e: PointerEvent) {
  if (e.button !== 0) return
  isPointerDown = true
  isDragging.value = false
  startPointerX = e.clientX
  startPointerY = e.clientY
  startPosX = pos.value.x
  startPosY = pos.value.y

  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
}

let rafDragId: number | null = null

function onPointerMove(e: PointerEvent) {
  if (!isPointerDown) return
  const dx = e.clientX - startPointerX
  const dy = e.clientY - startPointerY
  if (!isDragging.value && Math.hypot(dx, dy) > 4) {
    isDragging.value = true
  }
  if (isDragging.value) {
    if (rafDragId) cancelAnimationFrame(rafDragId)
    rafDragId = requestAnimationFrame(() => {
      pos.value = clampPosition(startPosX + dx, startPosY + dy)
    })
  }
}

function onPointerUp(e: PointerEvent) {
  if (!isPointerDown) return
  isPointerDown = false
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', onPointerUp)
  if (rafDragId) {
    cancelAnimationFrame(rafDragId)
    rafDragId = null
  }

  if (isDragging.value) {
    const uid = getCurrentUserId()
    localStorage.setItem(`cinema_pet_pos_${uid}`, JSON.stringify(pos.value))
    setTimeout(() => {
      isDragging.value = false
    }, 60)
  } else {
    toggleChat()
  }
}

const containerStyle = computed(() => ({
  transform: `translate3d(${pos.value.x}px, ${pos.value.y}px, 0)`,
  left: '0px',
  top: '0px',
  willChange: isDragging.value ? 'transform' : 'auto',
}))

const isNearTop = computed(() => pos.value.y < 490)
const isNearLeft = computed(() => pos.value.x < 360)

onMounted(() => {
  initPosition()
  loadLocalChatHistory()
  loadPetData()
  window.addEventListener('resize', handleResize)
  window.addEventListener('pet-level-updated', handleGlobalPetSync)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('pet-level-updated', handleGlobalPetSync)
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', onPointerUp)
})
</script>

<style scoped>
.floating-companion-pet-root {
  position: fixed;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  pointer-events: none;
  user-select: none;
}

.floating-companion-pet-root > * {
  pointer-events: auto;
}

.floating-companion-pet-root.near-left {
  align-items: flex-start;
}

.floating-companion-pet-root.near-top {
  flex-direction: column-reverse;
}

.floating-companion-pet-root.near-top .pet-companion-chat-window {
  margin-bottom: 0;
  margin-top: 14px;
}

.floating-companion-pet-root.near-top .pet-speech-bubble {
  margin-bottom: 0;
  margin-top: 10px;
}

.pet-avatar-character {
  cursor: grab;
  touch-action: none;
}

.pet-avatar-character.is-dragging {
  cursor: grabbing;
}

/* ==================== 伴看全功能对话抽屉窗口 ==================== */
.pet-companion-chat-window {
  width: 330px;
  height: 480px;
  margin-bottom: 14px;
  display: flex;
  flex-direction: column;
  border-radius: 18px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.1));
  box-shadow: 0 16px 38px rgba(0, 0, 0, 0.16);
  backdrop-filter: blur(20px);
  overflow: hidden;
  color: var(--agent-text-title, #18191c);
}

:global([data-theme="light"]) .pet-companion-chat-window {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.08);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.1);
  color: #18191c;
}

:global([data-theme="dark"]) .pet-companion-chat-window {
  background: rgba(22, 22, 26, 0.92);
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45);
  color: #f5f5f7;
}

/* 顶栏 */
.chat-win-header {
  padding: 12px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.06));
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pet-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #34c759;
  box-shadow: 0 0 6px rgba(52, 199, 89, 0.6);
}

.pet-title-meta {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pet-title-name {
  font-size: 13.5px;
  font-weight: 700;
  color: inherit;
}

.pet-lvl-pill {
  font-size: 10px;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(0, 113, 227, 0.12);
  color: #0071e3;
  border: 1px solid rgba(0, 113, 227, 0.25);
}

.pet-mood-pill {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(255, 149, 0, 0.12);
  color: #ff9500;
}

.header-right {
  display: flex;
  gap: 6px;
}

.win-ctrl-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: #8e8e93;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.win-ctrl-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  color: #1d1d1f;
}

/* 工具栏 */
.chat-win-toolbar {
  padding: 6px 12px;
  display: flex;
  gap: 6px;
  background: rgba(0, 0, 0, 0.02);
  border-bottom: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.04));
}

.toolbar-pill-btn {
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 10.5px;
  font-weight: 600;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
}

.toolbar-pill-btn.feed {
  background: #ff9500;
  color: #ffffff;
}

.toolbar-pill-btn.feed:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.toolbar-pill-btn.poke {
  background: rgba(0, 113, 227, 0.08);
  color: #0071e3;
}

.toolbar-pill-btn.clear {
  background: transparent;
  color: #8e8e93;
}

/* 消息滚动流 */
.chat-messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-bubble-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.chat-bubble-row.user {
  flex-direction: row-reverse;
}

.chat-avatar-chip {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0071e3 0%, #42a5f5 100%);
  color: #ffffff;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-bubble-row.user .chat-avatar-chip {
  background: #8e8e93;
}

.chat-bubble-content {
  max-width: 80%;
  padding: 8px 11px;
  border-radius: 12px;
  font-size: 12px;
  line-height: 1.5;
  background: #f5f5f7;
  color: #1d1d1f;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

:global([data-theme="dark"]) .chat-bubble-content {
  background: #2c2c2e;
  color: #f5f5f7;
}

.chat-bubble-row.user .chat-bubble-content {
  background: #0071e3;
  color: #ffffff;
}

.pet-thought-crumb {
  font-size: 10px;
  color: #0071e3;
  background: rgba(0, 113, 227, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  margin-bottom: 4px;
}

.chat-time-tag {
  display: block;
  font-size: 9.5px;
  color: #8e8e93;
  margin-top: 3px;
  text-align: right;
}

.chat-bubble-row.user .chat-time-tag {
  color: rgba(255, 255, 255, 0.7);
}

/* 打字动效 */
.chat-bubble-content.typing {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px 14px;
}

.typing-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #8e8e93;
  animation: typing-bounce 1.2s infinite ease-in-out;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing-bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-4px); }
}

/* 快捷追问药丸 */
.quick-prompts-row {
  padding: 6px 12px;
  display: flex;
  gap: 5px;
  overflow-x: auto;
  border-top: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.04));
}

.quick-pill-btn {
  white-space: nowrap;
  font-size: 10.5px;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(0, 113, 227, 0.06);
  border: 1px solid rgba(0, 113, 227, 0.15);
  color: #0071e3;
  cursor: pointer;
  transition: all 0.15s ease;
}

.quick-pill-btn:hover {
  background: rgba(0, 113, 227, 0.12);
}

/* 输入底栏 */
.chat-win-input-bar {
  padding: 8px 12px;
  display: flex;
  gap: 6px;
  background: var(--agent-card-surface, #ffffff);
  border-top: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.06));
}

.pet-chat-input {
  flex: 1;
  padding: 7px 10px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: #f5f5f7;
  color: inherit;
  font-size: 12px;
  outline: none;
}

:global([data-theme="dark"]) .pet-chat-input {
  background: #1c1c1e;
  border-color: rgba(255, 255, 255, 0.1);
}

.pet-chat-input:focus {
  border-color: #0071e3;
}

.pet-chat-send-btn {
  padding: 0 12px;
  border-radius: 8px;
  border: none;
  background: #0071e3;
  color: #ffffff;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pet-chat-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ==================== 迷你气泡 ==================== */
.pet-speech-bubble {
  width: 270px;
  margin-bottom: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.1));
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  color: var(--agent-text-title, #1d1d1f);
  backdrop-filter: blur(12px);
}

:global([data-theme="light"]) .pet-speech-bubble {
  background: #ffffff;
  color: #18191c;
}

:global([data-theme="dark"]) .pet-speech-bubble {
  background: rgba(22, 22, 26, 0.95);
  color: #f5f5f7;
}

.bubble-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.pet-name-tag {
  font-size: 12px;
  font-weight: 700;
  color: var(--agent-accent-blue, #0071e3);
}

.pet-lvl-tag {
  font-size: 10.5px;
  font-weight: 800;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(52, 199, 89, 0.15);
  color: #248a3d;
}

.bubble-close-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--agent-text-muted, #8e8e93);
  font-size: 11px;
}

.bubble-text {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--agent-text-body, #2c2c2e);
}

:global([data-theme="dark"]) .bubble-text {
  color: #e5e5ea;
}

.bubble-actions {
  display: flex;
  gap: 5px;
  margin-top: 10px;
}

.btn-bubble-action {
  flex: 1;
  padding: 5px 6px;
  border-radius: 6px;
  border: none;
  font-size: 10.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-bubble-action.chat {
  background: #0071e3;
  color: #ffffff;
}

.btn-bubble-action.feed {
  background: #ff9500;
  color: #ffffff;
}

.btn-bubble-action.poke {
  background: rgba(0, 0, 0, 0.06);
  color: var(--agent-text-body, #2c2c2e);
}

:global([data-theme="dark"]) .btn-bubble-action.poke {
  background: rgba(255, 255, 255, 0.1);
  color: #f5f5f7;
}

/* ==================== 灵宠动态形象 ==================== */
.pet-avatar-character {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
  position: relative;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(0, 113, 227, 0.3);
  animation: pet-float 3s ease-in-out infinite;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.pet-avatar-character:hover {
  transform: scale(1.08);
}

.pet-avatar-character.is-chat-active {
  box-shadow: 0 0 0 3px #0071e3, 0 8px 24px rgba(0, 113, 227, 0.4);
}

.pet-avatar-character.is-poked {
  animation: pet-bounce 0.6s ease;
}

.pet-avatar-character.is-happy {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
}

@keyframes pet-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

@keyframes pet-bounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2) rotate(15deg); }
}

.pet-glow-aura {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.4) 0%, transparent 70%);
  pointer-events: none;
}

/* 耳朵 */
.pet-ears .ear {
  position: absolute;
  top: -6px;
  width: 14px;
  height: 16px;
  border-radius: 8px 8px 0 0;
  background: #7bb5fc;
}

.pet-ears .ear.left { left: 10px; transform: rotate(-20deg); }
.pet-ears .ear.right { right: 10px; transform: rotate(20deg); }

/* 脸与表情 */
.pet-face {
  position: relative;
  width: 100%;
  height: 100%;
}

.pet-eyes {
  display: flex;
  justify-content: space-between;
  width: 32px;
  position: absolute;
  top: 26px;
  left: 16px;
}

.pet-eyes .eye {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #1e293b;
  position: relative;
}

.pet-eyes .eye::after {
  content: '';
  position: absolute;
  top: 1px;
  left: 1px;
  width: 2.5px;
  height: 2.5px;
  border-radius: 50%;
  background: #ffffff;
}

.pet-blush {
  position: absolute;
  top: 34px;
  left: 14px;
  width: 36px;
  height: 4px;
  border-radius: 4px;
  background: rgba(244, 63, 94, 0.35);
}

.pet-mouth {
  position: absolute;
  top: 36px;
  left: 28px;
  width: 8px;
  height: 4px;
  border-bottom: 2px solid #1e293b;
  border-radius: 0 0 6px 6px;
}

/* 过渡动效：Apple Spring 物理弹性果冻弹出 */
.chat-slide-fade-enter-active {
  transition: transform 0.38s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.25s ease-out;
  transform-origin: bottom right;
}

.chat-slide-fade-leave-active {
  transition: transform 0.22s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s ease-in;
  transform-origin: bottom right;
}

.near-left .chat-slide-fade-enter-active,
.near-left .chat-slide-fade-leave-active {
  transform-origin: bottom left;
}

.near-top .chat-slide-fade-enter-active,
.near-top .chat-slide-fade-leave-active {
  transform-origin: top right;
}

.near-top.near-left .chat-slide-fade-enter-active,
.near-top.near-left .chat-slide-fade-leave-active {
  transform-origin: top left;
}

.chat-slide-fade-enter-from {
  opacity: 0;
  transform: translateY(18px) scale(0.82);
}

.chat-slide-fade-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.88);
}

.pop-fade-enter-active,
.pop-fade-leave-active {
  transition: all 0.2s ease;
}

.pop-fade-enter-from,
.pop-fade-leave-to {
  opacity: 0;
  transform: scale(0.92);
}
</style>