<template>
  <div class="codex-multi-agent-widget" :class="'mode-' + mode" :id="'codex-widget-' + mode">
    <!-- ==================== MODE 1: USER PROFILE CODEX PET CABIN (Agent 2) ==================== -->
    <div v-if="mode === 'profile'" class="pet-cabin-card" id="codex-pet-cabin">
      <div class="pet-cabin-header">
        <div>
          <span class="pet-eyebrow">AGENT 02 · CODEX COMPANION PET</span>
          <h3 class="pet-title">Codex 观影灵宠太空舱 · {{ pet.pet_name }}</h3>
          <p class="pet-sub">由 2 号领域专家智能体驱动，支持人设灵魂切换 (Role/Goal/Backstory) 与金币投喂养成升级</p>
        </div>
        <div class="pet-badges">
          <span class="pet-badge level-badge" id="pet-level-badge">Lv.{{ pet.level }}</span>
          <span class="pet-badge mood-badge">心情 {{ pet.mood_score }}/100</span>
          <span class="pet-badge exp-badge">EXP {{ pet.exp }}/100</span>
        </div>
      </div>

      <div class="pet-cabin-grid">
        <!-- Left: Persona & Coin Feeding -->
        <div class="pet-control-col">
          <div class="pet-persona-box">
            <div class="persona-row">
              <label>灵宠昵称：</label>
              <input v-model="pet.pet_name" type="text" class="pet-input" id="input-pet-name" />
              <button type="button" class="pet-btn secondary" id="btn-save-pet-name" @click="handleSwitchPersona(pet.persona_key)">
                改名
              </button>
            </div>

            <div class="persona-pills-wrap">
              <span class="small-lbl">切换性格人设：</span>
              <button
                v-for="p in pet.available_personas"
                :key="p.persona_key"
                type="button"
                class="persona-pill-btn"
                :class="{ active: pet.persona_key === p.persona_key }"
                :id="'btn-persona-' + p.persona_key"
                @click="handleSwitchPersona(p.persona_key)"
              >
                {{ p.persona_label }}
              </button>
            </div>

            <div class="persona-spec-list">
              <div><strong>Role (角色)：</strong>{{ pet.role_prompt }}</div>
              <div><strong>Goal (目标)：</strong>{{ pet.goal_prompt }}</div>
              <div><strong>Backstory (背景)：</strong>{{ pet.backstory_prompt }}</div>
            </div>
          </div>

          <div class="pet-feed-bar">
            <span class="feed-lbl">已累计投喂 {{ pet.total_coins_fed }} 金币</span>
            <div class="feed-btns">
              <button type="button" class="pet-btn primary" id="btn-feed-pet-5" @click="handleFeedPet(5)">
                投喂 5 金币 (+60 EXP)
              </button>
              <button type="button" class="pet-btn secondary" id="btn-feed-pet-10" @click="handleFeedPet(10)">
                投喂 10 金币 (+120 EXP 升级)
              </button>
            </div>
          </div>
        </div>

        <!-- Right: Companion Chat -->
        <div class="pet-chat-col">
          <div class="pet-chat-history" id="pet-chat-history">
            <div v-if="!petReply" class="pet-greeting">
              <strong>[{{ pet.pet_name }} · {{ pet.persona_label }}]：</strong>
              主人好！我现在是【{{ pet.role_prompt }}】状态，随时陪你锐评短剧名场面或推测幕后反转！
            </div>
            <div v-else class="pet-reply-bubble" id="pet-reply-text">
              <div class="pet-thought-tag">{{ petThought }}</div>
              <div>{{ petReply }}</div>
            </div>
          </div>

          <div class="pet-chat-input-row">
            <input
              v-model="petQuestion"
              type="text"
              class="pet-input flex-1"
              id="input-pet-chat"
              placeholder="和你的 Codex 观影灵宠聊聊刚刚看的短剧..."
              @keyup.enter="handleAskPet"
            />
            <button
              type="button"
              class="pet-btn primary"
              id="btn-send-pet-chat"
              :disabled="isAskingPet"
              @click="handleAskPet"
            >
              {{ isAskingPet ? '回应中...' : '发送互动' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== MODE 2: CREATOR STUDIO DIRECTOR & VIRAL ASSISTANT (Agent 5 & Agent 8) ==================== -->
    <div v-if="mode === 'creator'" class="creator-agent-studio" id="creator-agent-studio">
      <div class="pet-cabin-header">
        <div>
          <span class="pet-eyebrow">AGENT 05 & AGENT 08 · CREATOR & DIRECTOR AI WORKBENCH</span>
          <h3 class="pet-title">智能创作与短剧导演剧本分镜工坊 (已挂载短剧黄金 Skills)</h3>
          <p class="pet-sub">协同调用 5 号【创作者爆款运营助手】与 8 号【编剧-导演-毒舌制片人三角色分镜 Crew】</p>
        </div>
        <div class="persona-pills-wrap">
          <button
            type="button"
            class="persona-pill-btn"
            :class="{ active: creatorAgentMode === 'agent_8' }"
            id="btn-creator-mode-agent8"
            @click="creatorAgentMode = 'agent_8'"
          >
            8号 · 导演剧本与分镜表 Crew
          </button>
          <button
            type="button"
            class="persona-pill-btn"
            :class="{ active: creatorAgentMode === 'agent_5' }"
            id="btn-creator-mode-agent5"
            @click="creatorAgentMode = 'agent_5'"
          >
            5号 · 爆款剧名与黄金3秒钩子助手
          </button>
        </div>
      </div>

      <div class="pet-chat-input-row mt-8">
        <input
          v-model="creatorPrompt"
          type="text"
          class="pet-input flex-1"
          id="input-creator-agent-prompt"
          :placeholder="creatorAgentMode === 'agent_8' ? '输入场次主题（如：雨夜宴会厅女主亮出底牌反击分镜脚本）...' : '输入短剧题材（如：高智商悬疑复仇短剧起名与前3秒钩子）...'"
          @keyup.enter="handleRunCreatorAgent"
        />
        <button
          type="button"
          class="pet-btn primary"
          id="btn-run-creator-agent"
          :disabled="isRunningCreator"
          @click="handleRunCreatorAgent"
        >
          {{ isRunningCreator ? '导演组协同生成中...' : '一键启动 AI 创作' }}
        </button>
      </div>

      <div v-if="creatorResult" class="creator-result-box" id="creator-agent-result-box">
        <div class="result-meta-bar">
          <span class="pet-badge level-badge">{{ creatorResult.invoked_agent_name }}</span>
          <span v-for="sk in creatorResult.matched_skills" :key="sk.skill_id" class="pet-badge mood-badge">
            已注入技能：{{ sk.name }}
          </span>
          <span v-if="creatorResult.structured_payload?.critic_review" class="pet-badge exp-badge">
            制片人审校评分：{{ creatorResult.structured_payload.critic_review.producer_score }} 分
          </span>
        </div>

        <!-- Structured Storyboard Table if Agent 8 -->
        <div v-if="creatorResult.structured_payload?.storyboard_shots?.length" class="storyboard-table-wrap">
          <table class="storyboard-table" id="table-director-storyboard">
            <thead>
              <tr>
                <th>镜号</th>
                <th>9:16 景别与运镜</th>
                <th>画面视觉描述</th>
                <th>角色台词与潜台词</th>
                <th>BGM/音效卡点</th>
                <th>时长</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="shot in creatorResult.structured_payload.storyboard_shots" :key="shot.shot_no">
                <td class="mono-strong">{{ shot.shot_no }}</td>
                <td>{{ shot.framing_and_motion }}</td>
                <td>{{ shot.visual_description }}</td>
                <td>{{ shot.dialogue }}</td>
                <td>{{ shot.sound_bgm }}</td>
                <td>{{ shot.duration_sec }}s</td>
              </tr>
            </tbody>
          </table>
        </div>

        <pre class="creator-md-pre">{{ creatorResult.answer }}</pre>
      </div>
    </div>

    <!-- ==================== MODE 3: PLAYER OMNI-AGENT DOCK (Agents 9, 6, 7, 1) ==================== -->
    <div v-if="mode === 'player'" class="player-omni-dock" id="player-omni-agent-dock">
      <div class="omni-dock-top">
        <span class="omni-lbl">九大智能体协同坞：</span>
        <button
          v-for="item in playerAgentButtons"
          :key="item.id"
          type="button"
          class="omni-pill-btn"
          :class="{ active: selectedPlayerAgent === item.id }"
          :id="'btn-player-agent-' + item.id"
          @click="triggerPlayerSpecialist(item)"
        >
          {{ item.label }}
        </button>
      </div>

      <div v-if="playerAgentResponse" class="omni-response-card" id="player-omni-response-card">
        <div class="omni-resp-head">
          <strong>{{ playerAgentResponse.invoked_agent_name }}</strong>
          <span class="omni-model-tag">
            {{ playerAgentResponse.resolved_model_info?.bind_mode }} · {{ playerAgentResponse.resolved_model_info?.model_name }}
          </span>
        </div>
        <div v-if="playerAgentResponse.recommended_agents?.length" class="omni-rec-row">
          <span>推荐协同：</span>
          <button
            v-for="r in playerAgentResponse.recommended_agents"
            :key="r.agent_id"
            type="button"
            class="omni-rec-chip"
            @click="triggerPlayerSpecialist({ id: r.agent_id, defaultQuery: '请继续从你的专业领域补充分析' })"
          >
            {{ r.name.split('·')[1] || r.name }} ({{ r.confidence }}%)
          </button>
        </div>
        <pre class="omni-resp-pre">{{ playerAgentResponse.answer }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const props = defineProps({
  mode: {
    type: String,
    default: 'profile' // 'profile' | 'creator' | 'player'
  },
  dramaId: {
    type: String,
    default: ''
  },
  episodeId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['walletUpdated'])

// Mode 1: Pet state
const pet = reactive({
  pet_name: '影伴小灵狐',
  persona_key: 'sharp_critic',
  persona_label: '毒舌影评喵',
  role_prompt: '一针见血的毒舌短剧鉴赏喵',
  goal_prompt: '帮主人识破工业糖精与老套路，精准定位演技高光与逻辑反转',
  backstory_prompt: '阅片三千部的赛博观影灵猫，嘴硬心软，最懂主人看剧口味。',
  level: 1,
  exp: 20,
  mood_score: 92,
  total_coins_fed: 0,
  available_personas: [
    { persona_key: 'sharp_critic', persona_label: '毒舌影评喵' },
    { persona_key: 'suspense_hound', persona_label: '悬疑推理犬' },
    { persona_key: 'sweet_bunny', persona_label: '甜宠嗑糖兔' }
  ]
})
const petQuestion = ref('这集主角最后的眼神是什么意思？')
const petReply = ref('')
const petThought = ref('')
const isAskingPet = ref(false)

// Mode 2: Creator & Director Studio
const creatorAgentMode = ref('agent_8')
const creatorPrompt = ref('雨夜宴会厅女主亮出股权底牌反击全场的 9:16 竖屏导演分镜脚本')
const isRunningCreator = ref(false)
const creatorResult = ref(null)

// Mode 3: Player Omni Dock
const selectedPlayerAgent = ref('agent_9')
const playerAgentResponse = ref(null)
const playerAgentButtons = [
  { id: 'agent_9', label: '9号·主控智能路由', defaultQuery: '帮我全面分析当前剧集看点并推荐协同智能体' },
  { id: 'agent_6', label: '6号·耳眼脑剧情深析', defaultQuery: '用字幕轨(耳)+视觉场记(眼)+图谱(脑)深度拆解本集剧情' },
  { id: 'agent_7', label: '7号·实库追问荐剧', defaultQuery: '根据当前系统真实在架作品为我推荐好看短剧并追问偏好' },
  { id: 'agent_1', label: '1号·@AI课代表速通', defaultQuery: '@影伴AI课代表 30秒总结一下本集核心看点' }
]

async function loadPetData() {
  try {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const res = await axios.get('/api/v1/agent-hub/pet', { headers })
    if (res.data?.data) {
      Object.assign(pet, res.data.data)
    }
  } catch (e) {
    console.warn('Load pet error:', e)
  }
}

async function handleSwitchPersona(personaKey) {
  try {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const res = await axios.put(
      '/api/v1/agent-hub/pet/persona',
      { pet_name: pet.pet_name, persona_key: personaKey },
      { headers }
    )
    if (res.data?.data) {
      Object.assign(pet, res.data.data)
      ElMessage.success(res.data.message || '灵宠人设已更新')
    }
  } catch (e) {
    ElMessage.error('更新灵宠人设失败')
  }
}

async function handleFeedPet(coins) {
  try {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const res = await axios.post(
      '/api/v1/agent-hub/pet/feed',
      { coin_amount: coins },
      { headers }
    )
    if (res.data?.data) {
      Object.assign(pet, res.data.data)
      ElMessage.success(res.data.message || '投喂成功')
      emit('walletUpdated', res.data.data.wallet_balance)
      window.dispatchEvent(new CustomEvent('pet-level-updated', { detail: res.data.data }))
    }
  } catch (e) {
    ElMessage.warning(e.response?.data?.detail || '金币投喂失败')
  }
}

async function handleAskPet() {
  if (!petQuestion.value.trim()) return
  isAskingPet.value = true
  try {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const res = await axios.post(
      '/api/v1/agent-hub/dispatch',
      {
        query: petQuestion.value,
        agent_id: 'agent_2',
        session_id: 'user_pet_session'
      },
      { headers }
    )
    if (res.data?.data) {
      petReply.value = res.data.data.answer
      petThought.value = res.data.data.thought_chain
    }
  } catch (e) {
    ElMessage.error('灵宠互动失败')
  } finally {
    isAskingPet.value = false
  }
}

async function handleRunCreatorAgent() {
  if (!creatorPrompt.value.trim()) return
  isRunningCreator.value = true
  try {
    const res = await axios.post('/api/v1/agent-hub/dispatch', {
      query: creatorPrompt.value,
      agent_id: creatorAgentMode.value,
      session_id: 'creator_studio_session'
    })
    creatorResult.value = res.data?.data || null
    ElMessage.success('智能体创作方案已生成')
  } catch (e) {
    ElMessage.error('生成失败')
  } finally {
    isRunningCreator.value = false
  }
}

async function triggerPlayerSpecialist(item) {
  selectedPlayerAgent.value = item.id
  try {
    const res = await axios.post('/api/v1/agent-hub/dispatch', {
      query: item.defaultQuery,
      agent_id: item.id,
      drama_id: props.dramaId || undefined,
      episode_id: props.episodeId || undefined,
      session_id: 'player_shared_session'
    })
    playerAgentResponse.value = res.data?.data || null
  } catch (e) {
    ElMessage.error('调用智能体失败')
  }
}

function handleExternalPetUpdate(evt) {
  if (evt?.detail) {
    Object.assign(pet, evt.detail)
  }
}

onMounted(() => {
  if (props.mode === 'profile') {
    loadPetData()
  }
  window.addEventListener('pet-level-updated', handleExternalPetUpdate)
})

onUnmounted(() => {
  window.removeEventListener('pet-level-updated', handleExternalPetUpdate)
})
</script>

<style scoped>
.codex-multi-agent-widget {
  margin: 16px 0;
}

/* ==================== 灵宠太空舱底座 (Apple HIG 语义化深浅自适应) ==================== */
.pet-cabin-card,
.creator-agent-studio {
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  border-radius: 16px;
  padding: 20px 22px;
  color: var(--agent-text-title, #1d1d1f);
  box-shadow: var(--agent-shadow-md, 0 4px 20px rgba(0, 0, 0, 0.04));
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

:global([data-theme="light"]) .pet-cabin-card,
:global(.theme-light) .pet-cabin-card {
  background: #ffffff !important;
  border-color: rgba(0, 0, 0, 0.08) !important;
  color: #1d1d1f !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
}

:global([data-theme="dark"]) .pet-cabin-card,
:global(.theme-dark) .pet-cabin-card {
  background: #141721 !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: #f5f5f7 !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.45) !important;
}

/* 顶栏元信息 */
.pet-cabin-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.pet-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--agent-accent-blue, #0071e3);
}

.pet-title {
  margin: 2px 0 4px 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--agent-text-title, #1d1d1f);
}

:global([data-theme="dark"]) .pet-title,
:global(.theme-dark) .pet-title {
  color: #f5f5f7 !important;
}

.pet-sub {
  margin: 0;
  font-size: 12.5px;
  color: var(--agent-text-secondary, #6e6e73);
}

:global([data-theme="dark"]) .pet-sub,
:global(.theme-dark) .pet-sub {
  color: #9499a0 !important;
}

/* 状态徽章 */
.pet-badges,
.persona-pills-wrap,
.result-meta-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.pet-badge {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.level-badge {
  background: rgba(0, 113, 227, 0.12);
  color: #0071e3;
  border: 1px solid rgba(0, 113, 227, 0.25);
}

.mood-badge {
  background: rgba(52, 199, 89, 0.12);
  color: #248a3d;
  border: 1px solid rgba(52, 199, 89, 0.25);
}

:global([data-theme="dark"]) .mood-badge {
  color: #34c759;
}

.exp-badge {
  background: rgba(175, 82, 222, 0.12);
  color: #8944ab;
  border: 1px solid rgba(175, 82, 222, 0.25);
}

:global([data-theme="dark"]) .exp-badge {
  color: #bf5af2;
}

/* 核心两列栅格 */
.pet-cabin-grid {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: 16px;
}

@media (max-width: 860px) {
  .pet-cabin-grid {
    grid-template-columns: 1fr;
  }
}

.pet-persona-box,
.pet-chat-col {
  background: var(--agent-card-hover, #f8f9fa);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  border-radius: 14px;
  padding: 14px 16px;
}

:global([data-theme="light"]) .pet-persona-box,
:global([data-theme="light"]) .pet-chat-col,
:global(.theme-light) .pet-persona-box,
:global(.theme-light) .pet-chat-col {
  background: #f8f9fa !important;
  border-color: rgba(0, 0, 0, 0.08) !important;
}

:global([data-theme="dark"]) .pet-persona-box,
:global([data-theme="dark"]) .pet-chat-col,
:global(.theme-dark) .pet-persona-box,
:global(.theme-dark) .pet-chat-col {
  background: #1c2130 !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
}

.persona-row,
.pet-chat-input-row,
.pet-feed-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.pet-feed-bar {
  margin-top: 14px;
  justify-content: space-between;
  flex-wrap: wrap;
}

.feed-lbl,
.small-lbl,
.persona-row label {
  color: var(--agent-text-title, #1d1d1f);
  font-weight: 600;
  font-size: 13px;
}

:global([data-theme="dark"]) .feed-lbl,
:global([data-theme="dark"]) .small-lbl,
:global([data-theme="dark"]) .persona-row label {
  color: #f5f5f7 !important;
}

/* 输入框 */
.pet-input {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid var(--agent-input-border, rgba(0, 0, 0, 0.12));
  background: var(--agent-input-bg, #ffffff);
  color: var(--agent-text-title, #1d1d1f);
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.pet-input:focus {
  border-color: var(--agent-accent-blue, #0071e3);
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.15);
}

:global([data-theme="light"]) .pet-input,
:global(.theme-light) .pet-input {
  background: #ffffff !important;
  color: #1d1d1f !important;
  border-color: rgba(0, 0, 0, 0.14) !important;
}

:global([data-theme="dark"]) .pet-input,
:global(.theme-dark) .pet-input {
  background: #0f121a !important;
  color: #f5f5f7 !important;
  border-color: rgba(255, 255, 255, 0.14) !important;
}

.flex-1 {
  flex: 1;
}

/* 按钮组 */
.pet-btn {
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.15s ease;
}

.pet-btn.primary {
  background: var(--agent-accent-blue, #0071e3);
  color: #ffffff;
}

.pet-btn.primary:hover:not(:disabled) {
  background: #0077ed;
  box-shadow: 0 2px 8px rgba(0, 113, 227, 0.3);
}

.pet-btn.secondary {
  background: var(--agent-tag-bg, #f0f2f5);
  color: var(--agent-text-title, #1d1d1f);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

.pet-btn.secondary:hover {
  background: #e5e7eb;
}

:global([data-theme="light"]) .pet-btn.secondary,
:global(.theme-light) .pet-btn.secondary {
  background: #f0f2f5 !important;
  color: #1d1d1f !important;
  border-color: rgba(0, 0, 0, 0.1) !important;
}

:global([data-theme="dark"]) .pet-btn.secondary,
:global(.theme-dark) .pet-btn.secondary {
  background: #252b3d !important;
  color: #f5f5f7 !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
}

/* 人设药丸按钮 */
.persona-pill-btn,
.omni-pill-btn {
  padding: 5px 12px;
  border-radius: 999px;
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.1));
  background: var(--agent-input-bg, #f5f5f7);
  color: var(--agent-text-secondary, #3a3a3c);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

:global([data-theme="light"]) .persona-pill-btn,
:global(.theme-light) .persona-pill-btn {
  background: #f5f5f7 !important;
  color: #1d1d1f !important;
  border-color: rgba(0, 0, 0, 0.1) !important;
}

:global([data-theme="dark"]) .persona-pill-btn,
:global(.theme-dark) .persona-pill-btn {
  background: #252b3d !important;
  color: #c9d1d9 !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
}

.persona-pill-btn.active,
.omni-pill-btn.active {
  background: #0071e3 !important;
  color: #ffffff !important;
  border-color: #0071e3 !important;
}

/* 人设详细设定列表 */
.persona-spec-list {
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--agent-text-secondary, #515154);
  background: var(--agent-input-bg, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.06));
  border-radius: 10px;
  padding: 10px 12px;
  margin-top: 10px;
}

:global([data-theme="light"]) .persona-spec-list,
:global(.theme-light) .persona-spec-list {
  background: #ffffff !important;
  color: #515154 !important;
  border-color: rgba(0, 0, 0, 0.08) !important;
}

:global([data-theme="dark"]) .persona-spec-list,
:global(.theme-dark) .persona-spec-list {
  background: #141824 !important;
  color: #9499a0 !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
}

.persona-spec-list strong {
  color: var(--agent-text-title, #1d1d1f);
}

:global([data-theme="dark"]) .persona-spec-list strong {
  color: #f5f5f7 !important;
}

/* 对话消息区 */
.pet-chat-history {
  min-height: 130px;
  max-height: 220px;
  overflow-y: auto;
  margin-bottom: 12px;
  font-size: 13px;
  line-height: 1.6;
}

.pet-greeting {
  color: var(--agent-text-body, #2c2c2e);
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--agent-input-bg, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.06));
}

:global([data-theme="light"]) .pet-greeting,
:global(.theme-light) .pet-greeting {
  background: #ffffff !important;
  color: #1d1d1f !important;
  border-color: rgba(0, 0, 0, 0.08) !important;
}

:global([data-theme="dark"]) .pet-greeting,
:global(.theme-dark) .pet-greeting {
  background: #141824 !important;
  color: #f5f5f7 !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
}

.pet-reply-bubble {
  background: var(--agent-bubble-agent, #f0f4fc);
  border: 1px solid var(--agent-bubble-agent-border, rgba(0, 113, 227, 0.15));
  color: var(--agent-text-title, #1d1d1f);
  border-radius: 10px;
  padding: 12px 14px;
}

:global([data-theme="light"]) .pet-reply-bubble,
:global(.theme-light) .pet-reply-bubble {
  background: #f0f4fc !important;
  border-color: rgba(0, 113, 227, 0.18) !important;
  color: #1d1d1f !important;
}

:global([data-theme="dark"]) .pet-reply-bubble,
:global(.theme-dark) .pet-reply-bubble {
  background: #1c2738 !important;
  border-color: rgba(56, 189, 248, 0.25) !important;
  color: #f5f5f7 !important;
}

.pet-thought-tag {
  font-size: 11px;
  color: #0071e3;
  font-weight: 600;
  margin-bottom: 6px;
}

:global([data-theme="dark"]) .pet-thought-tag {
  color: #38bdf8;
}

/* 创作者工作台与画板支持 */
.creator-result-box {
  margin-top: 14px;
  padding: 14px;
  border-radius: 12px;
  background: var(--agent-card-hover, #f8f9fa);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

.storyboard-table-wrap {
  overflow-x: auto;
  margin: 12px 0;
}

.storyboard-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12.5px;
}

.storyboard-table th,
.storyboard-table td {
  padding: 8px 12px;
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  text-align: left;
}

.storyboard-table th {
  background: var(--agent-input-bg, #f5f5f7);
  font-weight: 700;
  color: var(--agent-text-title, #1d1d1f);
}

:global([data-theme="dark"]) .storyboard-table th {
  background: #1c2130;
  color: #f5f5f7;
}

.creator-md-pre,
.omni-resp-pre {
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 12.5px;
  line-height: 1.6;
  margin: 8px 0 0;
  color: var(--agent-text-title, #1d1d1f);
}

:global([data-theme="dark"]) .creator-md-pre,
:global([data-theme="dark"]) .omni-resp-pre {
  color: #e2e8f0;
}

.player-omni-dock {
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--agent-card-hover, #f8f9fa);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

:global([data-theme="dark"]) .player-omni-dock {
  background: #1a1e2b;
  border-color: rgba(255, 255, 255, 0.08);
}

.omni-dock-top {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.omni-lbl {
  font-size: 11.5px;
  font-weight: 700;
  color: #0071e3;
}

:global([data-theme="dark"]) .omni-lbl {
  color: #38bdf8;
}

.omni-response-card {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--agent-input-bg, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  font-size: 12px;
}

:global([data-theme="dark"]) .omni-response-card {
  background: #141722;
  border-color: rgba(255, 255, 255, 0.08);
}

.omni-rec-chip {
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid #0071e3;
  background: rgba(0, 113, 227, 0.1);
  color: #0071e3;
  font-size: 11px;
  cursor: pointer;
}

:global([data-theme="dark"]) .omni-rec-chip {
  border-color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
}

.mt-8 { margin-top: 8px; }
</style>