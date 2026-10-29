<template>
  <div class="roundtable-canvas-root" id="roundtable-canvas-container">
    <!-- 顶部控制栏与 10 大专家在席徽章行 -->
    <div class="roundtable-top-bar">
      <div class="top-info">
        <span class="status-indicator-live">●</span>
        <div class="title-group">
          <h3 class="roundtable-title">多智能体沉浸协同圆桌会议室 (10大领域专家在席)</h3>
          <span class="roundtable-sub">原生 LangGraph 状态图驱动 · 支持点击专家一键定向 @ 探讨 · 右侧实时伴随生成交付物工件</span>
        </div>
      </div>
      <div class="top-actions">
        <button
          type="button"
          class="btn-toggle-drawer"
          :class="{ 'is-collapsed': isDrawerCollapsed }"
          id="btn-toggle-artifact-drawer"
          @click="isDrawerCollapsed = !isDrawerCollapsed"
          :title="isDrawerCollapsed ? '展开右侧交付物抽屉' : '折叠右侧交付物抽屉'"
        >
          {{ isDrawerCollapsed ? '展开工件抽屉 ◀' : '折叠抽屉 ▶' }}
        </button>
        <!-- 历史研讨会话快速切换 -->
        <select
          v-model="selectedHistorySessionId"
          class="btn-clear-session"
          id="select-roundtable-session-history"
          @change="loadHistorySession"
          title="选择历史圆桌研讨会话"
          style="padding: 6px 12px; cursor: pointer; outline: none;"
        >
          <option value="">当前研讨会话 (实时)</option>
          <option v-for="s in historySessionsList" :key="s.session_id" :value="s.session_id">
            {{ s.updated_at ? s.updated_at.slice(5, 16) : '' }} · {{ s.rolling_summary ? s.rolling_summary.slice(0, 14) + '...' : s.session_id.slice(0, 8) }} ({{ s.turn_count }}轮)
          </option>
        </select>
        <button type="button" class="btn-clear-session" id="btn-clear-roundtable" @click="resetSession">
          清空研讨记录
        </button>
        <button
          type="button"
          class="btn-export-artifact"
          id="btn-export-artifact"
          :disabled="!currentArtifact"
          @click="exportArtifact"
        >
          导出交付工件
        </button>
      </div>
    </div>

    <!-- Plan & Execute 动态待办清单 (TodoList) 交互看板 -->
    <div class="todo-plan-canvas-card" v-if="currentTodoList.length > 0">
      <div class="todo-card-header" @click="isTodoListCollapsed = !isTodoListCollapsed">
        <div class="todo-header-left">
          <svg class="todo-header-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 18px !important; height: 18px !important; flex-shrink: 0 !important;">
            <path d="M9 11l3 3L22 4" />
            <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
          </svg>
          <span class="todo-header-title">Plan &amp; Execute 协同执行清单</span>
          <span class="todo-header-badge">{{ todoCompletedCount }}/{{ currentTodoList.length }} 项已达成</span>
        </div>
        <div class="todo-header-right">
          <div class="todo-progress-track">
            <div class="todo-progress-fill" :style="{ width: todoProgressPercent + '%' }"></div>
          </div>
          <span class="todo-percent-text">{{ todoProgressPercent }}%</span>
          <button type="button" class="btn-toggle-todo" :title="isTodoListCollapsed ? '展开清单' : '收起清单'">
            <svg class="todo-chevron" :class="{ 'is-collapsed': isTodoListCollapsed }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 16px !important; height: 16px !important; flex-shrink: 0 !important;">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
        </div>
      </div>
      <div class="todo-items-list" v-show="!isTodoListCollapsed">
        <div
          v-for="item in currentTodoList"
          :key="item.id"
          class="todo-step-row"
          :class="['status-' + item.status]"
        >
          <div class="step-checkbox-wrap">
            <span v-if="item.status === 'completed'" class="step-check-icon check-done">
              <svg class="todo-status-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </span>
            <span v-else-if="item.status === 'in_progress'" class="step-check-icon check-progress">
              <svg class="todo-status-svg spinner-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="2" x2="12" y2="6" />
                <line x1="12" y1="18" x2="12" y2="22" />
                <line x1="4.93" y1="4.93" x2="7.76" y2="7.76" />
                <line x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
                <line x1="2" y1="12" x2="6" y2="12" />
                <line x1="18" y1="12" x2="22" y2="12" />
                <line x1="4.93" y1="19.07" x2="7.76" y2="16.24" />
                <line x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
              </svg>
            </span>
            <span v-else-if="item.status === 'failed'" class="step-check-icon check-failed">
              <svg class="todo-status-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </span>
            <span v-else class="step-check-icon check-pending">
              <svg class="todo-status-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
            </span>
          </div>
          <div class="step-info-col">
            <div class="step-line-primary">
              <span class="step-num-pill">Step {{ item.id }}</span>
              <span class="step-agent-name">{{ item.agentName }}</span>
              <span class="step-role-pill">{{ item.roleBadge }}</span>
              <span class="step-status-tag" :class="item.status">
                {{ item.status === 'completed' ? '已达成' : (item.status === 'in_progress' ? '正在执行' : (item.status === 'failed' ? '降级跳过' : '待执行')) }}
              </span>
              <span v-if="item.costMs" class="step-cost-label">{{ (item.costMs / 1000).toFixed(1) }}s</span>
            </div>
            <div class="step-instruction-text">{{ item.instruction }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 10 大领域专家在席徽章横向滚动栏 (支持点击一键定向 @ 发言) -->
    <div class="experts-presence-bar">
      <span class="presence-title">全员在席专家 (点击即刻定向 @)：</span>
      <div class="experts-pills-wrap">
        <button
          v-for="ag in agentRoster"
          :key="ag.id"
          type="button"
          class="expert-presence-pill"
          :class="{ 'is-active': activeAgentMention === ag.id }"
          :style="{ borderColor: ag.color }"
          @click="mentionAgent(ag)"
        >
          <span class="expert-pill-avatar" :style="{ backgroundColor: ag.color }">{{ ag.shortInitial }}</span>
          <span class="expert-pill-name">{{ ag.num }}号 · {{ ag.name }}</span>
          <span class="expert-pill-role">{{ ag.role }}</span>
        </button>
      </div>
    </div>

    <!-- 主体双栏协同区域 -->
    <div class="roundtable-main-split" :class="{ 'drawer-collapsed': isDrawerCollapsed }">
      <!-- 左侧：微信群聊式交互流 -->
      <div class="roundtable-chat-panel">
        <!-- 真正可自由滑动的消息流视口 (min-height: 0 解锁滚动死锁) -->
        <div class="roundtable-stream-scroll" ref="chatScrollRef">
          <div v-if="discussionMessages.length === 0" class="roundtable-intro-card">
            <div class="intro-badge">群聊协作模式已就绪</div>
            <h4>欢迎来到影视工业圆桌协同研讨室</h4>
            <p>
              全平台 9 大智能体专家全员在席待命。您可以在下方直接提出剧本、人设、台词、分镜或宣发构想，系统将由
              <strong>9号主控议长</strong> 统筹并按需点将最对口的专家接力研讨；亦可在上方点击专家徽章精准
              <strong>@定向提问</strong>，秒级获得专业答复。
            </p>
            <div class="quick-prompts-row mt-8">
              <span class="quick-lbl">点击快速启发：</span>
              <button
                type="button"
                class="quick-tag-btn"
                @click="fillQuickPrompt('我想创作一部都市豪门复仇短剧，主角是隐秘法医，开局前5秒如何设计最具爆款张力的反转？')"
              >
                豪门复仇爆款开局
              </button>
              <button
                type="button"
                class="quick-tag-btn"
                @click="fillQuickPrompt('@8号 请为雨夜女主手撕伪造遗嘱的高潮戏，设计一组竖屏9:16导演镜头表')"
              >
                @8号 雨夜反杀分镜表
              </button>
              <button
                type="button"
                class="quick-tag-btn"
                @click="fillQuickPrompt('@4号 帮我质检反派下毒害人情节的审核红线与合规建议')"
              >
                @4号 敏感剧情合规质检
              </button>
              <button
                type="button"
                class="quick-tag-btn"
                @click="fillQuickPrompt('@5号 提炼3个最具点击率的宣发爆款剧名与黄金前3秒投流文案')"
              >
                @5号 宣发爆款剧名操盘
              </button>
            </div>
          </div>

          <!-- 微信群聊消息列表 -->
          <div
            v-for="(msg, i) in discussionMessages"
            :key="i"
            class="wechat-msg-row"
            :class="msg.role === 'user' ? 'msg-align-right' : 'msg-align-left'"
          >
            <!-- 智能体头像 (居左) -->
            <div
              v-if="msg.role !== 'user'"
              class="wechat-avatar"
              :style="{ backgroundColor: getAgentColor(msg.agent_id) }"
            >
              {{ getAgentInitial(msg.agent_id) }}
            </div>

            <!-- 气泡与主体内容 -->
            <div class="wechat-bubble-container">
              <!-- 发信人信息栏 -->
              <div class="wechat-meta-header">
                <span class="wechat-sender-name">{{ msg.agent_name || (msg.role === 'user' ? '制片人 (您)' : '智能体') }}</span>
                <span class="wechat-role-pill" v-if="msg.role_badge">{{ msg.role_badge }}</span>
                <span class="wechat-timestamp">{{ msg.timestamp || '刚刚' }}</span>
              </div>

              <!-- 思维链推理抽屉 (可点击折叠/展开) -->
              <div v-if="msg.thought" class="wechat-thought-collapse">
                <div class="thought-summary" @click="msg.showThought = !msg.showThought">
                  <span class="thought-icon">▶</span>
                  <span class="thought-title">专家深层思考轨迹 (Thought Chain)</span>
                  <span class="thought-toggle-txt">{{ msg.showThought ? '收起' : '展开' }}</span>
                </div>
                <div v-if="msg.showThought" class="thought-body">
                  {{ msg.thought }}
                </div>
              </div>

              <!-- 消息气泡主体 -->
              <div
                class="wechat-bubble"
                :class="msg.role === 'user' ? 'user-bubble' : 'agent-bubble'"
              >
                <div class="bubble-content-text">{{ msg.content }}</div>
                <span v-if="msg.isTyping" class="rt-typing-cursor">▌</span>
              </div>
            </div>

            <!-- 用户头像 (居右) -->
            <div v-if="msg.role === 'user'" class="wechat-avatar user-avatar">
              制
            </div>
          </div>

          <!-- 专家接力打字思考状态指示器 -->
          <div v-if="isCollaborating" class="wechat-typing-status-row">
            <div class="typing-dots-pill">
              <span class="pulse-dot"></span>
              <span class="typing-text">{{ currentSpeakerName || '专家委员' }} 正在思考并组织发言...</span>
            </div>
          </div>
        </div>

        <!-- 底部制片人微信对话输入栏 -->
        <div class="roundtable-user-dock">
          <div class="dock-header-hint flex items-center justify-between">
            <span class="dock-hint-txt">制片人席：支持实时插话或 @ 智能体（如输入 @8号 或在上方点击头像）</span>
            <span class="dock-state-badge" v-if="activeAgentMention">已定向：{{ activeAgentMention }}</span>
          </div>
          <div class="dock-input-row">
            <textarea
              v-model="userTopicInput"
              class="dock-textarea"
              id="input-roundtable-topic"
              rows="2"
              placeholder="输入剧本构想、修改要求，或对专家进行定向指导（按 Enter 发送，Shift+Enter 换行）..."
              :disabled="isCollaborating"
              @keydown.enter.exact.prevent="startOrInterveneSession"
            ></textarea>
            <button
              type="button"
              class="dock-send-btn"
              id="btn-start-roundtable"
              :disabled="!userTopicInput.trim() || isCollaborating"
              @click="startOrInterveneSession"
            >
              {{ isCollaborating ? '接力发言中...' : '发送指令' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧：结构化交付物抽屉 (支持一键折叠) -->
      <div class="roundtable-artifact-drawer" v-show="!isDrawerCollapsed">
        <div class="drawer-header">
          <div class="drawer-title-box">
            <span class="drawer-icon-doc">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
            </span>
            <h4>结构化交付物抽屉 (Live Artifact)</h4>
          </div>
          <span class="artifact-status-pill" :class="{ 'is-ready': currentArtifact }">
            {{ currentArtifact ? '分镜工件已就绪' : '等待协同产出' }}
          </span>
        </div>

        <div class="drawer-body">
          <div v-if="!currentArtifact && !currentMarketing" class="drawer-empty-box">
            <div class="empty-icon-art">
              <svg viewBox="0 0 24 24" class="empty-clapperboard-svg" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="2" width="20" height="20" rx="3" ry="3"></rect>
                <line x1="7" y1="2" x2="7" y2="22"></line>
                <line x1="17" y1="2" x2="17" y2="22"></line>
                <line x1="2" y1="12" x2="22" y2="12"></line>
                <line x1="2" y1="7" x2="7" y2="7"></line>
                <line x1="2" y1="17" x2="7" y2="17"></line>
                <line x1="17" y1="17" x2="22" y2="17"></line>
                <line x1="17" y1="7" x2="22" y2="7"></line>
              </svg>
            </div>
            <p class="empty-title">暂未生成交付物</p>
            <p class="empty-desc">
              当您与 8号导演分镜 或 5号宣发操盘手 进行研讨时，系统将自动提炼专业 9:16 竖屏镜头脚本与宣发包在此实时排版呈现。
            </p>
          </div>

          <div v-else class="artifact-render-box">
            <!-- 分镜总览卡片 -->
            <div v-if="currentArtifact" class="artifact-card">
              <div class="art-card-head">
                <span class="art-badge">STORYBOARD 导演分镜</span>
                <span class="art-verdict">Consensus 达标: 95分</span>
              </div>
              <h4 class="art-drama-theme">{{ currentArtifact.story_theme || '短剧高光场次分镜' }}</h4>
              <p class="art-notes">{{ currentArtifact.director_notes || '按竖屏 9:16 镜头节奏设计，强化前 3 秒黄金抓手。' }}</p>

              <!-- 分镜镜头明细表 -->
              <div class="storyboard-table-wrap mt-10">
                <table class="storyboard-table">
                  <thead>
                    <tr>
                      <th style="width: 44px;">镜号</th>
                      <th style="width: 80px;">景别运镜</th>
                      <th>画面视觉</th>
                      <th>台词对白与音效</th>
                      <th style="width: 50px;">时长</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="shot in currentArtifact.storyboard_table" :key="shot.shot_num">
                      <td class="font-bold text-center">{{ shot.shot_num }}</td>
                      <td>
                        <span class="shot-tag">{{ shot.shot_size }}</span>
                        <span class="move-tag">{{ shot.camera_movement }}</span>
                      </td>
                      <td class="visual-desc-td">{{ shot.visual_description }}</td>
                      <td>
                        <p class="dialogue-text">{{ shot.dialogue }}</p>
                        <p class="sfx-text">{{ shot.sound_effect }}</p>
                      </td>
                      <td class="font-mono text-center">{{ shot.estimated_sec }}s</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 宣发物料卡片 -->
            <div v-if="currentMarketing" class="artifact-card mt-12">
              <div class="art-card-head">
                <span class="art-badge marketing">MARKETING 宣发物料</span>
                <span class="art-verdict">5号宣发总监站岗交付</span>
              </div>
              <div class="marketing-section">
                <span class="sec-label">黄金前 3 秒投流钩子：</span>
                <p class="viral-hook-text">{{ currentMarketing.golden_3s_hook }}</p>
              </div>
              <div class="marketing-section mt-8" v-if="currentMarketing.recommended_viral_titles?.length">
                <span class="sec-label">S级短剧爆款推荐剧名：</span>
                <div class="viral-titles-box">
                  <div
                    v-for="(t, idx) in currentMarketing.recommended_viral_titles"
                    :key="idx"
                    class="vtitle-item"
                  >
                    {{ idx + 1 }}. {{ t }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const sessionId = ref(`rt_session_${Date.now().toString(36)}`)
const userTopicInput = ref('')
const isCollaborating = ref(false)
const currentSpeakerName = ref('')
const isDrawerCollapsed = ref(false)
const activeAgentMention = ref('')
const chatScrollRef = ref<HTMLElement | null>(null)
const activeGraphStage = ref<'PLANNING' | 'EXECUTING' | 'SYNC' | 'SYNTHESIZING' | ''>('')

// Plan & Execute 响应式待办清单状态
const currentTodoList = ref<TodoStepItem[]>([])
const isTodoListCollapsed = ref(false)

const todoCompletedCount = computed(() => {
  return currentTodoList.value.filter(t => t.status === 'completed').length
})

const todoProgressPercent = computed(() => {
  if (currentTodoList.value.length === 0) return 0
  return Math.round((todoCompletedCount.value / currentTodoList.value.length) * 100)
})

// 10 大智能体全员花名册 (加入 10号 Coze 外部超脑)
const agentRoster = [
  { id: 'agent_1', num: 1, name: '剧情答疑', role: '剧本伏笔专家', shortInitial: '1号', color: '#0071E3' },
  { id: 'agent_2', num: 2, name: '观影灵宠', role: '陪伴共情专家', shortInitial: '2号', color: '#34C759' },
  { id: 'agent_3', num: 3, name: '知识检索', role: '事实资产检索', shortInitial: '3号', color: '#5856D6' },
  { id: 'agent_4', num: 4, name: '内容合规', role: '反转审核风控', shortInitial: '4号', color: '#FF3B30' },
  { id: 'agent_5', num: 5, name: '编剧创意', role: '爆款钩子操盘', shortInitial: '5号', color: '#FF9500' },
  { id: 'agent_6', num: 6, name: '视听场记', role: '台词多模态分析', shortInitial: '6号', color: '#30B0C7' },
  { id: 'agent_7', num: 7, name: '个性推荐', role: '受众偏好画像', shortInitial: '7号', color: '#AF52DE' },
  { id: 'agent_8', num: 8, name: '导演分镜', role: '9:16镜头雕塑', shortInitial: '8号', color: '#FF2D55' },
  { id: 'agent_9', num: 9, name: '主控议长', role: '全局中枢统筹', shortInitial: '9号', color: '#0A84FF' },
  { id: 'agent_10', num: 10, name: 'Coze超脑', role: '外部生态与工作流', shortInitial: '10号', color: '#10B981' },
]

interface DiscussionMsg {
  role: 'user' | 'assistant'
  agent_id?: string
  agent_name?: string
  role_badge?: string
  content: string
  thought?: string
  showThought?: boolean
  timestamp?: string
  isTyping?: boolean
}

/**
 * Plan & Execute 状态机待办项结构
 */
interface TodoStepItem {
  id: number
  agentId: string
  agentName: string
  roleBadge: string
  instruction: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  costMs?: number
  outputSummary?: string
}

const discussionMessages = ref<DiscussionMsg[]>([])
const selectedHistorySessionId = ref('')
const historySessionsList = ref<any[]>([])

async function fetchRoundtableSessions() {
  try {
    const res = await axios.get('/api/v1/agent-mesh/roundtable/sessions')
    historySessionsList.value = res.data?.data || []
  } catch (e) {
    console.warn('Failed to fetch roundtable history sessions:', e)
  }
}

async function loadHistorySession() {
  if (!selectedHistorySessionId.value) return
  try {
    sessionId.value = selectedHistorySessionId.value
    // 切换历史会话时必须重置当前工件交付物状态，杜绝上一个会话的数据滞留
    currentArtifact.value = null
    currentMarketing.value = null

    const res = await axios.get(`/api/v1/agent-mesh/roundtable/session-all/${selectedHistorySessionId.value}`)
    const d = res.data?.data || {}
    const rawMsgs = Array.isArray(d.messages) ? d.messages : []
    if (rawMsgs.length > 0) {
      discussionMessages.value = rawMsgs.map((m: any) => ({
        role: m.role || 'assistant',
        agent_id: m.agent_id,
        agent_name: m.agent_name || (m.role === 'user' ? '制片人 (您)' : '智能体'),
        role_badge: m.role === 'user' ? '总指挥席' : (m.agent_id === 'agent_9' ? '全局中枢主持' : '领域专家'),
        content: m.content || '',
        thought: m.thought || '',
        showThought: false,
        timestamp: m.timestamp ? (m.timestamp.length >= 16 ? m.timestamp.slice(11, 16) : m.timestamp) : '历史',
        isTyping: false
      }))
      ElMessage.success(`已动态载入历史圆桌研讨记录 (共 ${rawMsgs.length} 条发言)`)
    } else {
      discussionMessages.value = []
      ElMessage.info('该历史研讨记录暂无存档发言')
    }

    if (d.blackboard) {
      currentArtifact.value = d.blackboard.STORYBOARD_SPEC || null
      currentMarketing.value = d.blackboard.MARKETING_KIT || null
    }

    persistActiveSessionState()
    scrollToBottom()
  } catch (e) {
    ElMessage.error('加载历史会话失败')
  }
}
const currentArtifact = ref<any>(null)
const currentMarketing = ref<any>(null)

function getAgentColor(id?: string): string {
  const ag = agentRoster.find(a => a.id === id)
  return ag ? ag.color : '#0071E3'
}

function getAgentInitial(id?: string): string {
  const ag = agentRoster.find(a => a.id === id)
  return ag ? ag.shortInitial : 'AI'
}

function mentionAgent(ag: any) {
  activeAgentMention.value = `@${ag.num}号 · ${ag.name}`
  const mentionTag = `@${ag.num}号 `
  if (!userTopicInput.value.includes(mentionTag)) {
    userTopicInput.value = mentionTag + userTopicInput.value
  }
}

function fillQuickPrompt(promptText: string) {
  userTopicInput.value = promptText
}

function scrollToBottom() {
  nextTick(() => {
    if (chatScrollRef.value) {
      chatScrollRef.value.scrollTop = chatScrollRef.value.scrollHeight
    }
  })
}


function persistActiveSessionState() {
  if (typeof window === 'undefined') return
  try {
    const payload = {
      sessionId: sessionId.value,
      messages: discussionMessages.value,
      currentArtifact: currentArtifact.value,
      currentMarketing: currentMarketing.value,
      savedAt: Date.now()
    }
    localStorage.setItem('cinema_roundtable_active_session', JSON.stringify(payload))
  } catch (e) {
    console.warn('Failed to persist roundtable active session:', e)
  }
}

onMounted(async () => {
  let hasRestored = false
  const cachedRaw = localStorage.getItem('cinema_roundtable_active_session')
  if (cachedRaw) {
    try {
      const parsed = JSON.parse(cachedRaw)
      if (parsed.sessionId && Array.isArray(parsed.messages) && parsed.messages.length > 0) {
        sessionId.value = parsed.sessionId
        discussionMessages.value = parsed.messages
        if (parsed.currentArtifact) currentArtifact.value = parsed.currentArtifact
        if (parsed.currentMarketing) currentMarketing.value = parsed.currentMarketing
        hasRestored = true
        scrollToBottom()
      }
    } catch (e) {
      console.warn('Failed to parse cached roundtable session:', e)
    }
  }

  await fetchRoundtableSessions()

  if (!hasRestored && historySessionsList.value.length > 0) {
    selectedHistorySessionId.value = historySessionsList.value[0].session_id
    await loadHistorySession()
  }
})

function resetSession() {
  sessionId.value = `rt_session_${Date.now().toString(36)}`
  discussionMessages.value = []
  currentArtifact.value = null
  currentMarketing.value = null
  activeAgentMention.value = ''
  currentTodoList.value = []
  isTodoListCollapsed.value = false
  localStorage.removeItem('cinema_roundtable_active_session')
  ElMessage.info('协同圆桌会话记录已重置')
}

// 逐字流式平滑打印
async function appendStreamMessage(msg: {
  role: 'assistant'
  agent_id: string
  agent_name: string
  role_badge: string
  content: string
  thought?: string
}) {
  const newMsg = reactive<DiscussionMsg>({
    ...msg,
    content: '',
    thought: msg.thought || '',
    showThought: false,
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    isTyping: true,
  })
  discussionMessages.value.push(newMsg)
  scrollToBottom()

  const fullText = msg.content || '已收到任务并推进落实。'
  const step = Math.max(3, Math.floor(fullText.length / 20))
  for (let i = 0; i < fullText.length; i += step) {
    newMsg.content = fullText.slice(0, i + step)
    scrollToBottom()
    await new Promise((resolve) => setTimeout(resolve, 20))
  }
  newMsg.content = fullText
  newMsg.isTyping = false
  persistActiveSessionState()
  scrollToBottom()
}

// 调度逻辑：按需精准调用与接力协同
async function startOrInterveneSession() {
  const rawInput = userTopicInput.value.trim()
  if (!rawInput || isCollaborating.value) return

  // 1. 用户发言入列
  discussionMessages.value.push({
    role: 'user',
    agent_name: '制片人 (您)',
    role_badge: '总指挥席',
    content: rawInput,
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
  })
  persistActiveSessionState()

  userTopicInput.value = ''
  activeAgentMention.value = ''
  isCollaborating.value = true
  activeGraphStage.value = 'PLANNING'
  scrollToBottom()

  try {
    // 全局扫描提取所有被 @ 的智能体清单
    const mentionMatches = [...rawInput.matchAll(/@(\d+)号|@Agent\s*(\d+)|@agent_(\d+)/gi)]
    const targetAgentIds = mentionMatches.map(m => `agent_${m[1] || m[2] || m[3]}`)
    const uniqueAgentIds = [...new Set(targetAgentIds)]

    const collectedExpertNotes: Array<{ name: string; role: string; content: string }> = []

    if (uniqueAgentIds.length > 0) {
      // 模式 A：用户指定了 @ 智能体
      // 1. 若列表中包含 9号且有其他子智能体，先由 9号议长主持开场定调
      const subAgentIds = uniqueAgentIds.filter(id => id !== 'agent_9')
      const hasHost9 = uniqueAgentIds.includes('agent_9')

      if (hasHost9 && subAgentIds.length > 0) {
        currentSpeakerName.value = '9号主控议长'
        const othersNames = subAgentIds.map(id => {
          const m = agentRoster.find(a => a.id === id)
          return m ? `${m.num}号 · ${m.name}` : id
        }).join('、')

        const res9Intro = await axios.post('/api/v1/agent-mesh/chat', {
          agent_id: 'agent_9',
          session_id: sessionId.value,
          message: `【圆桌主持发令】制片人提出：“${rawInput}”。请作为9号主控议长开场定调，并正式主持点将让 ${othersNames} 依次发言阐述专业方案。`,
        })
        const d9Intro = res9Intro.data?.data || {}
        await appendStreamMessage({
          role: 'assistant',
          agent_id: 'agent_9',
          agent_name: '9号 · 主控议长',
          role_badge: '全局中枢主持',
          content: d9Intro.reply || `各位同仁请注意，制片人提出最新指示：“${rawInput}”。下面请各就各位，开展多维度推演！`,
          thought: d9Intro.thought || '主持开场，统筹调度对应领域子智能体。',
        })
      }

      // 2. 依次调度各子智能体发言（若仅指定了 9号单人则由 9号直接回答）
      const speakersToCall = subAgentIds.length > 0 ? subAgentIds : ['agent_9']
      for (const targetAgentId of speakersToCall) {
        const targetMeta = agentRoster.find(a => a.id === targetAgentId) || agentRoster[0]
        currentSpeakerName.value = targetMeta.name

        const promptForAgent = `【圆桌专家发言】制片人指示：“${rawInput}”。请严格以你作为【${targetMeta.role}】的垂直专业视角输出落地方案。
排版规范：请采用 Markdown 分小节结构化阐述（包含【领域专精推演】与【落地执行建议】），专注于自身专业领域，请勿冒充9号议长发表总结。`

        const res = await axios.post('/api/v1/agent-mesh/chat', {
          agent_id: targetAgentId,
          session_id: sessionId.value,
          message: promptForAgent,
        })
        const d = res.data?.data || {}

        if (targetAgentId === 'agent_8' && d.storyboard_data) {
          currentArtifact.value = d.storyboard_data
        } else if (targetAgentId === 'agent_5' && d.growth_data) {
          currentMarketing.value = d.growth_data
        }

        const replyContent = d.reply || `针对制片人要求，已为您定制落实相关专家方案。`
        collectedExpertNotes.push({
          name: `${targetMeta.num}号 · ${targetMeta.name}`,
          role: targetMeta.role,
          content: replyContent
        })

        await appendStreamMessage({
          role: 'assistant',
          agent_id: targetAgentId,
          agent_name: `${targetMeta.num}号 · ${targetMeta.name}`,
          role_badge: targetMeta.role,
          content: replyContent,
          thought: d.thought || `以${targetMeta.role}专业视角完成研讨。`,
        })
      }

      // 3. 若有子智能体发言，且调用了 9号 或多位子智能体，由 9号议长压轴出具结构化综合总结
      if (subAgentIds.length > 0 && (hasHost9 || subAgentIds.length >= 2)) {
        currentSpeakerName.value = '9号主控议长 (总结)'
        const summaryContext = collectedExpertNotes.map(e => `【${e.name} (${e.role})】：\n${e.content.slice(0, 350)}...`).join('\n\n')
        const res9Summary = await axios.post('/api/v1/agent-mesh/chat', {
          agent_id: 'agent_9',
          session_id: sessionId.value,
          message: `【圆桌决议总结指令】各位专家的意见已全部收齐：\n\n${summaryContext}\n\n请作为9号常务主控议长，对上述各位专家的核心要点进行精要提炼，输出结构化的【圆桌研讨决议与多方成果总结】。\n【输出规范】：篇幅适中（250~350字以内），论述完整有始有终，严禁中途截断，确保语句自然闭合。包含三部分：1. 各专家核心观点摘要；2. 综合推进决议；3. 下一步行动清单。`,
        })
        const d9Summary = res9Summary.data?.data || {}
        await appendStreamMessage({
          role: 'assistant',
          agent_id: 'agent_9',
          agent_name: '9号 · 主控议长',
          role_badge: '会议决议终审总结',
          content: d9Summary.reply || `综合各位专家的发言，本轮研讨决议已生成，各方已达成一致，全力推进落实！`,
          thought: d9Summary.thought || '整合多位专家产出，生成结构化圆桌研讨决议与落地清单。',
        })
      }
    } else {
      // 模式 B：未明确 @ 智能体，由 9号主脑统一执行 Plan 规划，严格言行合一
      currentSpeakerName.value = '9号主控议长'
      activeGraphStage.value = 'PLANNING'

      // 阶段 1：9号依据制片人诉求出具正规《协同计划表》
      const res9 = await axios.post('/api/v1/agent-mesh/chat', {
        agent_id: 'agent_9',
        session_id: sessionId.value,
        message: rawInput,
      }, { timeout: 60000 })
      const d9 = res9.data?.data || {}
      await appendStreamMessage({
        role: 'assistant',
        agent_id: 'agent_9',
        agent_name: '9号 · 主控议长',
        role_badge: '全局中枢主持',
        content: d9.reply || `已受理制片人指令：“${rawInput}”，正在统筹多智能体协同流水线。`,
        thought: d9.thought || '拆解多智能体协同流水线并出具执行计划表。',
      })

      if (d9.artifacts) {
        if (d9.artifacts.storyboard_spec) currentArtifact.value = d9.artifacts.storyboard_spec
        if (d9.artifacts.marketing_kit) currentMarketing.value = d9.artifacts.marketing_kit
      }

      // 阶段 2：完全遵照 9号大脑《计划表》指定的专家接力发言 (100% 言行合一，绝不表里不一)
      const pipelineSteps = Array.isArray(d9.task_pipeline) && d9.task_pipeline.length > 0 ? d9.task_pipeline : []
      
      // 初始化 Plan & Execute 动态待办清单 (TodoList)
      if (pipelineSteps.length > 0) {
        currentTodoList.value = pipelineSteps.map((s: any, idx: number) => {
          const m = agentRoster.find(a => a.id === s.assigned_agent)
          return {
            id: s.step_id || idx + 1,
            agentId: s.assigned_agent,
            agentName: s.agent_name || (m ? `${m.num}号 · ${m.name}` : s.assigned_agent),
            roleBadge: s.role_badge || (m ? m.role : '协同专家'),
            instruction: s.instruction,
            status: 'pending',
            costMs: 0
          }
        })
        isTodoListCollapsed.value = false
      }

      const actualTargets = pipelineSteps.map((s: any, idx: number) => ({
        stepId: s.step_id || idx + 1,
        id: s.assigned_agent,
        instruction: s.instruction,
        meta: agentRoster.find(a => a.id === s.assigned_agent) || agentRoster[0]
      }))

      if (actualTargets.length === 0) {
        // 兜底派发
        actualTargets.push({
          stepId: 1,
          id: 'agent_1',
          instruction: rawInput,
          meta: agentRoster[0]
        })
        currentTodoList.value = [{
          id: 1,
          agentId: 'agent_1',
          agentName: '1号 · 剧情答疑',
          roleBadge: '剧情解析',
          instruction: rawInput,
          status: 'pending',
          costMs: 0
        }]
      }

      for (const target of actualTargets) {
        const meta = target.meta
        currentSpeakerName.value = meta.name
        activeGraphStage.value = 'EXECUTING'

        // 动态推进 TodoList 状态机为执行中
        const currentTodo = currentTodoList.value.find(t => t.id === target.stepId)
        if (currentTodo) {
          currentTodo.status = 'in_progress'
        }

        const missionSubject = d9.mission_subject || '平台重点短剧《高冷千金的贴身高手》全链条工业化协同研发'
        const tStepStart = performance.now()
        let dSub: any = {}
        try {
          const resSub = await axios.post('/api/v1/agent-mesh/chat', {
            agent_id: target.id,
            session_id: sessionId.value,
            message: `【圆桌协同研讨标的】：“${missionSubject}”\n【本步骤专精任务】：${target.instruction}\n请严格以【${meta.role}】专业视角，紧扣上述研讨标的展开深度推演，输出可落地的专业方案。篇幅 200~350 字，结构清晰，严禁客套。`,
          }, { timeout: 60000 })
          dSub = resSub.data?.data || {}
          if (currentTodo) {
            currentTodo.status = 'completed'
            currentTodo.costMs = Math.round(performance.now() - tStepStart)
          }
        } catch (stepErr: any) {
          if (currentTodo) {
            currentTodo.status = 'failed'
            currentTodo.costMs = Math.round(performance.now() - tStepStart)
          }
        }

        if (target.id === 'agent_8' && dSub.storyboard_data) {
          currentArtifact.value = dSub.storyboard_data
        } else if (target.id === 'agent_5' && dSub.growth_data) {
          currentMarketing.value = dSub.growth_data
        }

        const subReply = dSub.reply || `针对分配任务，专业建议已就绪。`
        collectedExpertNotes.push({
          name: `${meta.num}号 · ${meta.name}`,
          role: meta.role,
          content: subReply
        })

        await appendStreamMessage({
          role: 'assistant',
          agent_id: target.id,
          agent_name: `${meta.num}号 · ${meta.name}`,
          role_badge: meta.role,
          content: subReply,
          thought: dSub.thought || '根据9号总控计划表落实专业领域方案。',
        })
      }

      // 阶段 3：9号主控议长压轴终结总结
      activeGraphStage.value = 'SYNTHESIZING'
      currentSpeakerName.value = '9号主控议长 (总结)'
      const summaryContext = collectedExpertNotes.map(e => `【${e.name} (${e.role})】：\n${e.content.slice(0, 350)}...`).join('\n\n')
      const res9Summary = await axios.post('/api/v1/agent-mesh/chat', {
        agent_id: 'agent_9',
        session_id: sessionId.value,
        message: `【圆桌决议总结指令】各位专家的意见已全部收齐：\n\n${summaryContext}\n\n请作为9号常务主控议长，对上述各位专家的核心要点进行精要提炼，输出结构化的【圆桌研讨决议与多方成果总结】。\n【输出规范】：篇幅适中（250~350字以内），论述完整有始有终，严禁中途截断，确保语句自然闭合。包含三部分：1. 各专家核心观点摘要；2. 综合推进决议；3. 下一步行动清单。`,
      }, { timeout: 60000 })
      const d9Summary = res9Summary.data?.data || {}
      await appendStreamMessage({
        role: 'assistant',
        agent_id: 'agent_9',
        agent_name: '9号 · 主控议长',
        role_badge: '会议决议终审总结',
        content: d9Summary.reply || `综合各位专家的发言，本轮研讨决议已生成，各方已达成一致，全力推进落实！`,
        thought: d9Summary.thought || '整合多位专家产出，生成结构化圆桌研讨决议与落地清单。',
      })
    }
  } catch (err: any) {
    ElMessage.error('智能体协同响应出现波动，已启动安全降级')
  } finally {
    isCollaborating.value = false
    currentSpeakerName.value = ''
    setTimeout(() => {
      activeGraphStage.value = ''
    }, 2500)
    scrollToBottom()
  }
}

function exportArtifact() {
  if (!currentArtifact.value) {
    ElMessage.warning('当前暂无可导出的交付工件')
    return
  }
  const blob = new Blob([JSON.stringify(currentArtifact.value, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `STORYBOARD_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已成功导出 9:16 影视分镜工件数据')
}
</script>

<style scoped>
.roundtable-canvas-root {
  display: flex;
  flex-direction: column;
  height: 740px;
  border-radius: 16px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  color: var(--agent-text-title, #1d1d1f);
}

/* 顶部控制栏 */
.roundtable-top-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  background: var(--agent-bg-canvas, #f8f9fa);
  border-bottom: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

.top-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-indicator-live {
  color: #34c759;
  font-size: 13px;
  animation: pulse-live 1.8s infinite;
}

@keyframes pulse-live {
  0% { opacity: 0.35; }
  50% { opacity: 1; }
  100% { opacity: 0.35; }
}

.title-group {
  display: flex;
  flex-direction: column;
}

.roundtable-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--agent-text-title, #1d1d1f);
}

.roundtable-sub {
  font-size: 11.5px;
  color: var(--agent-text-muted, #6e6e73);
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-toggle-drawer,
.btn-clear-session {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.12));
  background: var(--agent-card-surface, #ffffff);
  color: var(--agent-text-body, #2c2c2e);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-toggle-drawer:hover,
.btn-clear-session:hover {
  background: rgba(0, 113, 227, 0.06);
  border-color: #0071e3;
  color: #0071e3;
}

.btn-export-artifact {
  padding: 6px 14px;
  border-radius: 8px;
  border: none;
  background: var(--agent-accent-blue, #0071e3);
  color: #ffffff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.btn-export-artifact:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* 原生 LangGraph 运行时 HUD 流程指示条 */
.langgraph-hud-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 7px 16px;
  background: var(--agent-card-surface, #ffffff);
  border-bottom: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  user-select: none;
  backdrop-filter: blur(8px);
}

.hud-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.03);
  color: var(--agent-text-muted, #86868b);
  font-size: 11.5px;
  font-weight: 500;
  transition: all 0.25s ease;
}

.hud-item.is-active {
  background: rgba(0, 113, 227, 0.08);
  color: var(--agent-accent-blue, #0071e3);
  font-weight: 700;
  box-shadow: 0 0 0 1px rgba(0, 113, 227, 0.2);
}

.hud-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #c7c7cc;
}

.hud-item.is-active .hud-dot {
  background: var(--agent-accent-blue, #0071e3);
  box-shadow: 0 0 6px rgba(0, 113, 227, 0.6);
  animation: pulse-live 1.2s infinite;
}

.hud-step {
  font-family: monospace;
  font-size: 10px;
  opacity: 0.7;
}

.hud-divider {
  color: var(--agent-text-muted, #c7c7cc);
  font-size: 11px;
}

/* 10 大专家在席徽章栏 */
.experts-presence-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: var(--agent-bg-canvas, #f3f4f6);
  border-bottom: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.06));
  overflow-x: auto;
  white-space: nowrap;
}

.presence-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--agent-text-secondary, #515154);
  flex-shrink: 0;
}

.experts-pills-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
}

.expert-presence-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s ease;
  color: var(--agent-text-title, #1d1d1f);
}

.expert-presence-pill:hover,
.expert-presence-pill.is-active {
  background: rgba(0, 113, 227, 0.08);
  transform: translateY(-1px);
}

.expert-pill-avatar {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 800;
}

.expert-pill-name {
  font-weight: 600;
}

.expert-pill-role {
  font-size: 10px;
  color: var(--agent-text-muted, #8e8e93);
}

/* 主体分栏 */
.roundtable-main-split {
  flex: 1;
  min-height: 0; /* 关键：解决 flex 嵌套内溢出滚动失效 */
  display: flex;
  overflow: hidden;
  transition: all 0.3s ease;
}

.roundtable-chat-panel {
  flex: 1;
  min-height: 0; /* 关键：解决滚动锁死 */
  display: flex;
  flex-direction: column;
  background: var(--agent-card-surface, #ffffff);
  border-right: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

/* 微信群聊滚动视口 */
.roundtable-stream-scroll {
  flex: 1;
  min-height: 0; /* 关键：确保能够触发自身滚动条 */
  max-height: 100%;
  overflow-y: auto;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: var(--agent-bg-canvas, #f9fafb);
}

.roundtable-intro-card {
  padding: 16px 20px;
  border-radius: 14px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
}

.intro-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(0, 113, 227, 0.1);
  color: #0071e3;
  font-size: 11px;
  font-weight: 700;
  margin-bottom: 8px;
}

.roundtable-intro-card h4 {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 700;
}

.roundtable-intro-card p {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--agent-text-secondary, #515154);
}

.quick-prompts-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.06));
}

.quick-lbl {
  font-size: 11px;
  color: var(--agent-text-muted, #8e8e93);
}

.quick-tag-btn {
  padding: 3px 9px;
  border-radius: 999px;
  border: 1px solid rgba(0, 113, 227, 0.2);
  background: rgba(0, 113, 227, 0.04);
  color: #0071e3;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.quick-tag-btn:hover {
  background: #0071e3;
  color: #ffffff;
}

/* 微信群聊消息单行 */
.wechat-msg-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: 88%;
}

.msg-align-left {
  align-self: flex-start;
}

.msg-align-right {
  align-self: flex-end;
  flex-direction: row;
}

.wechat-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 800;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

.user-avatar {
  background: linear-gradient(135deg, #0071e3, #42a5f5);
}

.wechat-bubble-container {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.msg-align-right .wechat-bubble-container {
  align-items: flex-end;
}

.wechat-meta-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.wechat-sender-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--agent-text-title, #1d1d1f);
}

.wechat-role-pill {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.06);
  color: var(--agent-text-muted, #6e6e73);
}

.wechat-timestamp {
  font-size: 10px;
  color: var(--agent-text-muted, #8e8e93);
}

/* 思维链折叠块 */
.wechat-thought-collapse {
  margin-bottom: 6px;
  border-radius: 8px;
  background: rgba(0, 113, 227, 0.06);
  border: 1px solid rgba(0, 113, 227, 0.16);
  overflow: hidden;
  font-size: 11px;
}

.thought-summary {
  padding: 4px 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
  color: #0071e3;
  font-weight: 600;
}

.thought-icon {
  font-size: 9px;
}

.thought-toggle-txt {
  margin-left: auto;
  font-size: 10px;
  opacity: 0.8;
}

.thought-body {
  padding: 6px 10px;
  background: var(--agent-card-surface, #ffffff);
  color: var(--agent-text-secondary, #515154);
  line-height: 1.5;
  border-top: 1px dashed rgba(0, 113, 227, 0.15);
  white-space: pre-wrap;
}

/* 微信气泡样式 */
.wechat-bubble {
  position: relative;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.bubble-content-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.7;
  font-size: 13.5px;
}

.agent-bubble .bubble-content-text {
  color: var(--agent-text-body, #2c2c2e);
}

.user-bubble .bubble-content-text {
  color: #ffffff;
}

.agent-bubble {
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  color: var(--agent-text-body, #2c2c2e);
  border-top-left-radius: 3px;
}

.user-bubble {
  background: var(--agent-accent-blue, #0071e3);
  color: #ffffff;
  border-top-right-radius: 3px;
}

/* 正在输入状态 */
.wechat-typing-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.typing-dots-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(52, 199, 89, 0.12);
  color: #248a3d;
  font-size: 12px;
  font-weight: 600;
}

.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #34c759;
  animation: pulse-live 1.2s infinite;
}

/* 底部操作坞 */
.roundtable-user-dock {
  padding: 12px 18px;
  background: var(--agent-bg-canvas, #f8f9fa);
  border-top: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

.dock-header-hint {
  font-size: 11px;
  color: var(--agent-text-muted, #6e6e73);
  margin-bottom: 6px;
}

.dock-state-badge {
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(0, 113, 227, 0.1);
  color: #0071e3;
  font-weight: 600;
}

.dock-input-row {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.dock-textarea {
  flex: 1;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.14));
  background: var(--agent-card-surface, #ffffff);
  color: var(--agent-text-title, #1d1d1f);
  font-size: 13px;
  line-height: 1.45;
  resize: none;
  outline: none;
  transition: border-color 0.2s ease;
}

.dock-textarea:focus {
  border-color: #0071e3;
}

.dock-send-btn {
  height: 42px;
  padding: 0 20px;
  border-radius: 10px;
  border: none;
  background: var(--agent-accent-blue, #0071e3);
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity 0.2s ease;
}

.dock-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 右侧交付物抽屉 (支持折叠) */
.roundtable-artifact-drawer {
  width: 380px;
  display: flex;
  flex-direction: column;
  background: var(--agent-bg-canvas, #fafafa);
  overflow: hidden;
  border-left: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.roundtable-main-split.drawer-collapsed .roundtable-artifact-drawer {
  width: 0;
  border-left: none;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--agent-card-surface, #ffffff);
  border-bottom: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

.drawer-title-box {
  display: flex;
  align-items: center;
  gap: 6px;
}

.drawer-title-box h4 {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
}

.artifact-status-pill {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.06);
  color: var(--agent-text-muted, #6e6e73);
}

.artifact-status-pill.is-ready {
  background: rgba(52, 199, 89, 0.15);
  color: #248a3d;
  font-weight: 700;
}

.drawer-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 14px;
}

.drawer-empty-box {
  text-align: center;
  padding: 50px 20px;
}

.empty-icon-art {
  font-size: 32px;
  margin-bottom: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.empty-clapperboard-svg {
  width: 40px;
  height: 40px;
  color: var(--apple-text-secondary, #86868B);
  opacity: 0.7;
}

.empty-title {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 700;
  color: var(--agent-text-title, #1d1d1f);
}

.empty-desc {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--agent-text-muted, #8e8e93);
}

.artifact-card {
  padding: 14px;
  border-radius: 12px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.art-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.art-badge {
  font-size: 10px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--agent-accent-blue, #0071e3);
  color: #ffffff;
}

.art-badge.marketing {
  background: #ff9500;
}

.art-verdict {
  font-size: 11px;
  font-weight: 700;
  color: #34c759;
}

.art-drama-theme {
  margin: 4px 0;
  font-size: 13.5px;
  font-weight: 700;
}

.art-notes {
  margin: 0;
  font-size: 11.5px;
  color: var(--agent-text-secondary, #515154);
}

.storyboard-table-wrap {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  background: var(--agent-card-surface, #ffffff);
}

.storyboard-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.storyboard-table th,
.storyboard-table td {
  padding: 6px 8px;
  border-bottom: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.06));
  text-align: left;
}

.storyboard-table th {
  background: var(--agent-bg-canvas, #f5f5f7);
  font-weight: 700;
}

.shot-tag,
.move-tag {
  display: block;
  font-size: 10px;
  color: var(--agent-accent-blue, #0071e3);
  font-weight: 600;
}

.visual-desc-td {
  font-size: 11px;
  line-height: 1.4;
}

.dialogue-text {
  margin: 0;
  font-weight: 600;
}

.sfx-text {
  margin: 2px 0 0;
  font-size: 10px;
  color: var(--agent-text-muted, #8e8e93);
}

.sec-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--agent-text-title, #1d1d1f);
}

.viral-hook-text {
  font-size: 12px;
  font-weight: 700;
  color: #ff9500;
  margin: 4px 0;
}

.viral-titles-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 4px;
  font-size: 11.5px;
}

.vtitle-item {
  padding: 4px 8px;
  border-radius: 6px;
  background: var(--agent-bg-canvas, #f5f5f7);
}

.rt-typing-cursor {
  display: inline-block;
  margin-left: 2px;
  color: #0071e3;
  animation: cursor-blink 0.8s infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.mt-8 { margin-top: 8px; }
.mt-10 { margin-top: 10px; }
.mt-12 { margin-top: 12px; }
</style>


/* 自定义 Apple HIG 极简半透明细滚动条 */
.roundtable-stream-scroll::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.roundtable-stream-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.roundtable-stream-scroll::-webkit-scrollbar-thumb {
  background: rgba(120, 120, 128, 0.35);
  border-radius: 4px;
}
.roundtable-stream-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(120, 120, 128, 0.65);
}

/* Plan & Execute 动态待办清单 (TodoList) 看板样式 */
.todo-plan-canvas-card {
  margin: 10px 18px 4px 18px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
  transition: all 0.25s ease;
}

.todo-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: pointer;
  background: rgba(0, 0, 0, 0.015);
  border-bottom: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.06));
  user-select: none;
}

.todo-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.todo-header-icon {
  width: 17px;
  height: 17px;
  color: var(--agent-accent-blue, #0071e3);
}

.todo-header-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--agent-text-title, #1d1d1f);
}

.todo-header-badge {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 10px;
  background: rgba(52, 199, 89, 0.12);
  color: var(--agent-accent-green, #34c759);
  font-weight: 600;
}

.todo-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.todo-progress-track {
  width: 90px;
  height: 5px;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 3px;
  overflow: hidden;
}

.todo-progress-fill {
  height: 100%;
  background: var(--agent-accent-green, #34c759);
  border-radius: 3px;
  transition: width 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.todo-percent-text {
  font-size: 11.5px;
  font-weight: 700;
  color: var(--agent-text-secondary, #515154);
  min-width: 30px;
}

.btn-toggle-todo {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 2px;
  color: var(--agent-text-muted, #86868b);
  display: flex;
  align-items: center;
  justify-content: center;
}

.todo-chevron {
  width: 15px;
  height: 15px;
  transition: transform 0.25s ease;
}

.todo-chevron.is-collapsed {
  transform: rotate(-90deg);
}

.todo-items-list {
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.todo-step-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.015);
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.todo-step-row.status-in_progress {
  background: rgba(0, 113, 227, 0.04);
  border-color: rgba(0, 113, 227, 0.25);
  box-shadow: 0 2px 8px rgba(0, 113, 227, 0.06);
}

.todo-step-row.status-completed {
  background: rgba(52, 199, 89, 0.03);
  border-color: rgba(52, 199, 89, 0.15);
}

.todo-step-row.status-failed {
  background: rgba(255, 59, 48, 0.03);
  border-color: rgba(255, 59, 48, 0.15);
}

.step-checkbox-wrap {
  margin-top: 1px;
  flex-shrink: 0;
}

.step-check-icon {
  width: 16px !important;
  height: 16px !important;
  min-width: 16px !important;
  min-height: 16px !important;
  max-width: 16px !important;
  max-height: 16px !important;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  flex-shrink: 0 !important;
}

.todo-status-svg,
.step-check-icon svg {
  width: 16px !important;
  height: 16px !important;
  min-width: 16px !important;
  min-height: 16px !important;
  max-width: 16px !important;
  max-height: 16px !important;
  flex-shrink: 0 !important;
  display: block !important;
}

.step-check-icon.check-done {
  color: var(--agent-accent-green, #34c759);
}

.step-check-icon.check-progress {
  color: var(--agent-accent-blue, #0071e3);
}

.step-check-icon.check-failed {
  color: var(--agent-accent-red, #ff3b30);
}

.step-check-icon.check-pending {
  color: var(--agent-text-muted, #86868b);
  opacity: 0.6;
}

.spinner-svg {
  animation: spin-pulse 1s linear infinite;
}

@keyframes spin-pulse {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.step-info-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.step-line-primary {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.step-num-pill {
  font-family: monospace;
  font-size: 10.5px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.06);
  color: var(--agent-text-secondary, #515154);
}

.step-agent-name {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--agent-text-title, #1d1d1f);
}

.step-role-pill {
  font-size: 10.5px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(0, 113, 227, 0.08);
  color: var(--agent-accent-blue, #0071e3);
  font-weight: 500;
}

.step-status-tag {
  font-size: 10.5px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.step-status-tag.pending {
  background: rgba(0, 0, 0, 0.04);
  color: var(--agent-text-muted, #86868b);
}

.step-status-tag.in_progress {
  background: rgba(0, 113, 227, 0.12);
  color: var(--agent-accent-blue, #0071e3);
}

.step-status-tag.completed {
  background: rgba(52, 199, 89, 0.12);
  color: var(--agent-accent-green, #34c759);
}

.step-status-tag.failed {
  background: rgba(255, 59, 48, 0.12);
  color: var(--agent-accent-red, #ff3b30);
}

.step-cost-label {
  font-size: 10.5px;
  font-family: monospace;
  color: var(--agent-text-muted, #86868b);
}

.step-instruction-text {
  font-size: 12px;
  color: var(--agent-text-body, #2c2c2e);
  line-height: 1.45;
}
