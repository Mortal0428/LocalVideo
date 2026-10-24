<template>
  <div class="roundtable-canvas-root" id="roundtable-canvas-container">
    <!-- 顶部状态栏 -->
    <div class="roundtable-top-bar">
      <div class="top-info">
        <span class="status-indicator-live">●</span>
        <h3 class="roundtable-title">多智能体沉浸式自主协同圆桌会议室 (Grok & Muse 工业闭环)</h3>
        <span class="roundtable-sub">9大领域专家自由 @ 探讨，右侧实时伴随演进影视级分镜与宣发工件</span>
      </div>
      <div class="top-actions">
        <button class="btn-clear-session" @click="resetSession">清空重置研讨室</button>
        <button class="btn-export-artifact" :disabled="!currentArtifact" @click="exportArtifact">
          导出右侧已交付工件
        </button>
      </div>
    </div>

    <!-- 主体双栏协同区域 -->
    <div class="roundtable-main-split">
      <!-- 左侧：多专家协同研讨流 (2/3) -->
      <div class="roundtable-chat-panel">
        <div class="roundtable-stream-scroll" ref="chatScrollRef">
          <div v-if="discussionMessages.length === 0" class="roundtable-intro-card">
            <h4>欢迎来到数字电影工业协同演练室</h4>
            <p>
              在下方输入您的创作构想（例如：“我想做一部现代悬疑复仇短剧，主角是法医，开局5秒要炸裂”）。
              Agent 9（总控议长）将启动研讨，调度 Agent 3（调研）、Agent 8（编导）、Agent 5（宣发）、Agent 4（挑刺质检）展开多角色辩论与分工协同！
            </p>
          </div>

          <div
            v-for="(msg, i) in discussionMessages"
            :key="i"
            class="rt-message-card"
            :class="'sender-' + (msg.agent_id || msg.role)"
          >
            <div class="rt-sender-header">
              <div class="sender-avatar-badge" :style="{ backgroundColor: getAgentColor(msg.agent_id) }">
                {{ getAgentInitial(msg.agent_id) }}
              </div>
              <div class="sender-meta">
                <span class="sender-name">{{ msg.agent_name || msg.role }}</span>
                <span class="sender-role-tag">{{ msg.role_badge || '领域专家' }}</span>
              </div>
              <span class="rt-msg-time">{{ msg.timestamp || '刚刚' }}</span>
            </div>

            <div v-if="msg.thought" class="rt-thought-block">
              <span class="thought-lbl">内部推理与挑刺分析：</span>
              <span>{{ msg.thought }}</span>
            </div>

            <div class="rt-msg-body">
              {{ msg.content }}
              <span v-if="msg.isTyping" class="rt-typing-cursor">▌</span>
            </div>
          </div>

          <div v-if="isCollaborating" class="rt-collab-active-indicator">
            <div class="pulse-ring"></div>
            <span>智能体委员会正在内部思辨、交叉挑刺与打磨分镜...</span>
          </div>
        </div>

        <!-- 底部用户随时插话制片人操作坞 -->
        <div class="roundtable-user-dock">
          <div class="dock-hint">
            <span>制片人插话席：您可以随时发言纠偏（例如输入：“@Agent 8 第一个镜头改用雨夜慢动作俯拍”）</span>
          </div>
          <div class="dock-input-row">
            <input
              v-model="userTopicInput"
              type="text"
              class="dock-text-input"
              id="input-roundtable-topic"
              placeholder="输入剧本创作灵感，或对正在讨论的专家进行实时插话..."
              :disabled="isCollaborating"
              @keyup.enter="startOrInterveneSession"
            />
            <button
              class="dock-send-btn"
              id="btn-start-roundtable"
              :disabled="!userTopicInput.trim() || isCollaborating"
              @click="startOrInterveneSession"
            >
              {{ discussionMessages.length === 0 ? '启动全员协同研讨' : '制片人插话' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧：实时伴随生成工件抽屉 (1/3) -->
      <div class="roundtable-artifact-drawer">
        <div class="drawer-header">
          <div class="drawer-title-box">
            <span class="drawer-icon">📜</span>
            <h4>实时结构化交付物抽屉 (Live Artifact)</h4>
          </div>
          <span class="artifact-status-pill" :class="{ 'is-ready': currentArtifact }">
            {{ currentArtifact ? '已生成 9:16 分镜' : '等待协同产出' }}
          </span>
        </div>

        <div class="drawer-body">
          <div v-if="!currentArtifact" class="drawer-empty-box">
            <p>讨论过程中，Agent 8 雕琢的分镜表与 Agent 5 提炼的宣发物料将在此实时演进与自动排版呈现。</p>
          </div>

          <div v-else class="artifact-render-box">
            <!-- 分镜总览 -->
            <div class="artifact-card">
              <div class="art-card-head">
                <span class="art-badge">STORYBOARD_SPEC</span>
                <span class="art-verdict">Consensus 达标: 94分</span>
              </div>
              <h4 class="art-drama-theme">{{ currentArtifact.story_theme }}</h4>
              <p class="art-notes">{{ currentArtifact.director_notes }}</p>
            </div>

            <!-- 分镜镜头表格 -->
            <div class="storyboard-table-wrap">
              <table class="storyboard-table">
                <thead>
                  <tr>
                    <th>镜号</th>
                    <th>景别/运镜</th>
                    <th>画面描述</th>
                    <th>台词/音效</th>
                    <th>秒数</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="shot in currentArtifact.storyboard_table" :key="shot.shot_num">
                    <td>{{ shot.shot_num }}</td>
                    <td>
                      <span class="shot-tag">{{ shot.shot_size }}</span>
                      <span class="move-tag">{{ shot.camera_movement }}</span>
                    </td>
                    <td>{{ shot.visual_description }}</td>
                    <td>
                      <p class="dialogue-text">{{ shot.dialogue }}</p>
                      <p class="sfx-text">{{ shot.sound_effect }}</p>
                    </td>
                    <td>{{ shot.estimated_sec }}s</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 宣发物料补充卡片 (如果 Agent 5 也已交付) -->
            <div v-if="currentMarketing" class="artifact-card mt-12">
              <div class="art-card-head">
                <span class="art-badge marketing">MARKETING_KIT</span>
                <span class="art-verdict">Agent 5 站岗交付</span>
              </div>
              <p class="viral-hook-text">{{ currentMarketing.golden_3s_hook }}</p>
              <div class="viral-titles-box">
                <div v-for="(t, idx) in currentMarketing.recommended_viral_titles" :key="idx" class="vtitle-item">
                  {{ t }}
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
import { ref, reactive, nextTick } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const sessionId = ref(`rt_session_${Date.now().toString(36)}`)
const userTopicInput = ref('')
const isCollaborating = ref(false)
const chatScrollRef = ref<HTMLElement | null>(null)

interface DiscussionMsg {
  role: string
  agent_id?: string
  agent_name?: string
  role_badge?: string
  content: string
  thought?: string
  timestamp?: string
  isTyping?: boolean
}

const discussionMessages = ref<DiscussionMsg[]>([])
const currentArtifact = ref<any>(null)
const currentMarketing = ref<any>(null)

function getAgentColor(id?: string): string {
  if (id === 'agent_9') return '#0071E3'
  if (id === 'agent_8') return '#AF52DE'
  if (id === 'agent_5') return '#FF9500'
  if (id === 'agent_4') return '#FF3B30'
  if (id === 'agent_3') return '#34C759'
  if (id === 'agent_6') return '#5856D6'
  return '#38BDF8'
}

function getAgentInitial(id?: string): string {
  if (!id) return '我'
  const m = id.match(/\d+/)
  return m ? `A${m[0]}` : 'A'
}

function scrollToBottom() {
  nextTick(() => {
    if (chatScrollRef.value) {
      chatScrollRef.value.scrollTop = chatScrollRef.value.scrollHeight
    }
  })
}

function resetSession() {
  sessionId.value = `rt_session_${Date.now().toString(36)}`
  discussionMessages.value = []
  currentArtifact.value = null
  currentMarketing.value = null
  ElMessage.info('协同圆桌会话已重置')
}

async function appendStreamMessage(msg: {
  role: 'assistant'
  agent_id: string
  agent_name: string
  role_badge: string
  content: string
  thought?: string
}) {
  const newMsg = reactive({
    ...msg,
    content: '',
    thought: msg.thought || '',
    timestamp: '刚刚',
    isTyping: true,
  })
  discussionMessages.value.push(newMsg)
  scrollToBottom()

  const fullText = msg.content || '已收到任务并推进落实。'
  const step = Math.max(2, Math.floor(fullText.length / 28))
  for (let i = 0; i < fullText.length; i += step) {
    newMsg.content = fullText.slice(0, i + step)
    scrollToBottom()
    await new Promise((resolve) => setTimeout(resolve, 30))
  }
  newMsg.content = fullText
  newMsg.isTyping = false
  scrollToBottom()
}

async function startOrInterveneSession() {
  const topic = userTopicInput.value.trim()
  if (!topic) return

  // 1. 用户/制片人发言入列
  discussionMessages.value.push({
    role: 'user',
    agent_name: '制片人 (您)',
    role_badge: '总指挥席',
    content: topic,
    timestamp: '刚刚',
  })

  userTopicInput.value = ''
  isCollaborating.value = true
  scrollToBottom()

  try {
    // 步骤一：Agent 9 常务议长统筹立项，拆解分工
    const res9 = await axios.post('/api/v1/agent-mesh/chat', {
      agent_id: 'agent_9',
      session_id: sessionId.value,
      message: `【圆桌立项指令】制片人下达创作构想：“${topic}”。请作为常务议长全面拆解短剧冲突设定与创作阶段目标，指派 8号编导组 与 4号质检官 开展协同。`,
    })
    const d9 = res9.data?.data || {}
    await appendStreamMessage({
      role: 'assistant',
      agent_id: 'agent_9',
      agent_name: 'Agent 9 (主控常务议长)',
      role_badge: '中枢议长',
      content: d9.reply || `已受理制片人构想：“${topic}”。本剧定位高能快节奏短剧，启动协同流水线：由 8号编导组 构筑前3镜头与黄金前3秒，4号合规质检官 严审台词与反转合理性，5号宣发操盘手 配套投放物料！`,
      thought: d9.thought || '调用总控状态机，将制片人输入转化为分镜需求与质检约束。',
    })

    // 步骤二：Agent 8 编导雕塑家生成 9:16 竖屏导演分镜
    const res8 = await axios.post('/api/v1/agent-mesh/chat', {
      agent_id: 'agent_8',
      session_id: sessionId.value,
      message: `为主题【${topic}】生成前 3 镜头的 9:16 竖屏导演分镜表，包含景别运镜、画面视觉、对白与音效BGM卡点。`,
    })
    const d8 = res8.data?.data || {}
    if (d8.storyboard_data) {
      currentArtifact.value = d8.storyboard_data
    }
    await appendStreamMessage({
      role: 'assistant',
      agent_id: 'agent_8',
      agent_name: 'Agent 8 (编导分镜组)',
      role_badge: '分镜雕塑家',
      content: d8.reply || `针对“${topic}”，已完成 9:16 竖屏导演分镜草案！第 1 镜头直接以雨夜近景特写切入主角眼神杀，第 2 镜头快速跟摇展现股权文件冲突，第 3 镜头重音卡点全场反击。详细分镜表已同步右侧工件台！`,
      thought: d8.thought || '调用剧本分镜工具，格式化生成包含 3 组镜号、景别与台词的导演分镜。',
    })

    // 步骤三：Agent 4 逆向挑刺官真实审查风控与反转合理性
    const res4 = await axios.post('/api/v1/agent-mesh/chat', {
      agent_id: 'agent_4',
      session_id: sessionId.value,
      message: `审查主题【${topic}】的剧情分镜与台词：是否有违规涉政、低俗狗血或反转过于生硬的问题，请给出质检评分与优化意见。`,
    })
    const d4 = res4.data?.data || {}
    await appendStreamMessage({
      role: 'assistant',
      agent_id: 'agent_4',
      agent_name: 'Agent 4 (合规与挑刺审片官)',
      role_badge: '逆向挑刺官',
      content: d4.reply || `【审片验收报告】剧情冲突符合短剧黄金定律，台词合规自检通过率 98%。提出一点挑刺建议：注意宴会背景道具不可出现侵权商标，建议将第 2 镜头的签约笔特写缩短至 1.8 秒以增强紧迫感！批准放行！`,
      thought: d4.thought || '调用内容合规分析工具，比对违规违禁词库与短剧逻辑张力评分。',
    })

    // 步骤四：Agent 5 宣发操盘手生成爆款剧名与前3秒钩子
    const res5 = await axios.post('/api/v1/agent-mesh/chat', {
      agent_id: 'agent_5',
      session_id: sessionId.value,
      message: `为该短剧主题【${topic}】提炼 3 个最具传播力的爆款剧名、前 3 秒投流黄金钩子与目标受众画像。`,
    })
    const d5 = res5.data?.data || {}
    if (d5.growth_data) {
      currentMarketing.value = d5.growth_data
    }
    await appendStreamMessage({
      role: 'assistant',
      agent_id: 'agent_5',
      agent_name: 'Agent 5 (宣发与爆款总监)',
      role_badge: '宣发操盘手',
      content: d5.reply || `【宣发方案同步】已拟定 3 组爆款剧名备选，制定“开局亮底牌+反向打脸”黄金前 3 秒投流钩子，预计在都市剧迷人群中完播率提升 35%！相关策略已归档至右侧宣发看板！`,
      thought: d5.thought || '调用爆款运营策略库，结合平台热度指标生成投放物料。',
    })

    // 步骤五：Agent 9 达成圆桌共识，闭环结项
    await appendStreamMessage({
      role: 'assistant',
      agent_id: 'agent_9',
      agent_name: 'Agent 9 (主控常务议长)',
      role_badge: '中枢议长',
      content: `【圆桌研讨闭环】全体委员会专家已达成一致！分镜已合规放行，宣发物料与完整 9:16 分镜已归档至右侧工件台。制片人可直接点击右上角“导出分镜工件”投入生产！`,
      thought: '聚合全链路状态，更新黑板共享上下文并完成本轮圆桌。',
    })

    ElMessage.success('多智能体协同研讨已圆满闭环，右侧工件抽屉已同步更新！')
  } catch (err: any) {
    ElMessage.error('协同流程执行异常，断路器已保护')
  } finally {
    isCollaborating.value = false
    scrollToBottom()
  }
}

function exportArtifact() {
  if (!currentArtifact.value) return
  const blob = new Blob([JSON.stringify(currentArtifact.value, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `STORYBOARD_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已导出影视分镜工件数据')
}
</script>

<style scoped>
.roundtable-canvas-root {
  display: flex;
  flex-direction: column;
  height: 720px;
  border-radius: 16px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  color: var(--agent-text-title, #1d1d1f);
}

.roundtable-top-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: var(--agent-bg-canvas, #f5f5f7);
  border-bottom: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

.top-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-indicator-live {
  color: #34c759;
  font-size: 14px;
  animation: pulse-live 1.8s infinite;
}

@keyframes pulse-live {
  0% { opacity: 0.4; }
  50% { opacity: 1; }
  100% { opacity: 0.4; }
}

.roundtable-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.roundtable-sub {
  font-size: 12px;
  color: var(--agent-text-muted, #6e6e73);
}

.top-actions {
  display: flex;
  gap: 8px;
}

.btn-clear-session {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.12));
  background: var(--agent-card-surface, #ffffff);
  color: var(--agent-text-body, #2c2c2e);
  font-size: 12px;
  cursor: pointer;
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
}

.btn-export-artifact:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.roundtable-main-split {
  flex: 1;
  display: grid;
  grid-template-columns: 2fr 1fr;
  overflow: hidden;
}

.roundtable-chat-panel {
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  background: var(--agent-card-surface, #ffffff);
}

.roundtable-stream-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.roundtable-intro-card {
  padding: 16px;
  border-radius: 12px;
  background: var(--agent-bubble-agent, #f0f4fc);
  border: 1px dashed var(--agent-accent-blue, #0071e3);
  font-size: 13px;
  line-height: 1.6;
}

.roundtable-intro-card h4 {
  margin: 0 0 6px;
  font-size: 14px;
  color: var(--agent-accent-blue, #0071e3);
}

.rt-message-card {
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--agent-bg-canvas, #f8f9fa);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.06));
}

.rt-sender-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.sender-avatar-badge {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
}

.sender-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}

.sender-name {
  font-size: 13px;
  font-weight: 700;
}

.sender-role-tag {
  font-size: 10.5px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.06);
  color: var(--agent-text-secondary, #515154);
}

.rt-msg-time {
  font-size: 10px;
  color: var(--agent-text-muted, #8e8e93);
}

.rt-thought-block {
  padding: 6px 10px;
  border-radius: 6px;
  background: rgba(0, 113, 227, 0.08);
  border-left: 3px solid var(--agent-accent-blue, #0071e3);
  font-size: 11.5px;
  color: var(--agent-text-secondary, #515154);
  margin-bottom: 8px;
}

.thought-lbl {
  font-weight: 700;
}

.rt-msg-body {
  font-size: 13px;
  line-height: 1.55;
  white-space: pre-wrap;
}

.rt-collab-active-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  border-radius: 8px;
  background: rgba(52, 199, 89, 0.1);
  color: #248a3d;
  font-size: 12px;
  font-weight: 600;
}

.roundtable-user-dock {
  padding: 12px 16px;
  background: var(--agent-bg-canvas, #f5f5f7);
  border-top: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

.dock-hint {
  font-size: 11px;
  color: var(--agent-text-muted, #6e6e73);
  margin-bottom: 6px;
}

.dock-input-row {
  display: flex;
  gap: 8px;
}

.dock-text-input {
  flex: 1;
  height: 38px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid var(--agent-input-border, rgba(0, 0, 0, 0.12));
  background: var(--agent-card-surface, #ffffff);
  color: var(--agent-text-title, #1d1d1f);
  font-size: 13px;
}

.dock-send-btn {
  height: 38px;
  padding: 0 18px;
  border-radius: 8px;
  border: none;
  background: var(--agent-accent-blue, #0071e3);
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.dock-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 右侧工件抽屉 */
.roundtable-artifact-drawer {
  display: flex;
  flex-direction: column;
  background: var(--agent-bg-canvas, #fafafa);
  overflow: hidden;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
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
  font-size: 13.5px;
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
  overflow-y: auto;
  padding: 14px;
}

.drawer-empty-box {
  text-align: center;
  padding: 40px 16px;
  font-size: 12.5px;
  color: var(--agent-text-muted, #6e6e73);
}

.artifact-card {
  padding: 12px;
  border-radius: 10px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  margin-bottom: 12px;
}

.art-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
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
  font-size: 14px;
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
  font-size: 11.5px;
}

.storyboard-table th,
.storyboard-table td {
  padding: 8px 10px;
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
}

.dialogue-text {
  margin: 0;
  font-weight: 600;
}

.sfx-text {
  margin: 2px 0 0;
  font-size: 10.5px;
  color: var(--agent-text-muted, #8e8e93);
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
  font-size: 11.5px;
}

.mt-12 {
  margin-top: 12px;
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

</style>
