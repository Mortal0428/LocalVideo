<template>
  <Teleport to="body">
    <div v-if="modelValue" class="settings-modal-overlay" id="modal-engine-settings-backdrop" @click.self="close">
      <div class="settings-modal-card fade-in-up dual-engine-modal">
        <!-- Modal Header -->
        <div class="modal-header">
          <div class="header-title-box">
            <span class="header-icon">⚙️</span>
            <div>
              <h3 class="modal-title">模型引擎与 RAG 向量双轨解耦配置</h3>
              <p class="modal-subtitle">大语言对话推理底座与知识库向量嵌入引擎完全独立配置、独立测速与持久化记忆</p>
            </div>
          </div>
          <button class="close-btn" id="btn-close-engine-modal" @click="close" title="关闭">✕</button>
        </div>

        <!-- Admin Permission Notice Banner -->
        <div v-if="!isAdmin" class="admin-notice-banner read-only" id="engine-readonly-notice">
          <div class="notice-info">
            <span class="notice-icon">🛡️</span>
            <div>
              <div class="notice-title">只读配置模式（非系统管理员）</div>
              <div class="notice-desc">
                系统底层推理模型属于全站核心基建，仅<strong>系统管理员 (ADMIN)</strong> 拥有变更权限。当前身份为「{{ getRoleLabel(userRole) }}」。
              </div>
            </div>
          </div>
          <button type="button" class="switch-admin-btn" id="btn-switch-admin-in-modal" @click="quickSwitchToAdmin">
            ⚡ 一键切换为管理员 (ADMIN)
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <span class="loading-spinner"></span>
          <span>正在探测模型环境与持久化双轨基建配置...</span>
        </div>

        <div v-else class="modal-dual-grid">
          <!-- CARD 1: Chat Reasoning Engine -->
          <div class="engine-card glass-panel" id="card-chat-engine">
            <div class="card-head-line">
              <div class="head-left">
                <span class="engine-badge chat-badge">推理主脑</span>
                <h4 class="engine-name">大语言对话推理模型 (Chat Engine)</h4>
              </div>
              <span class="engine-status-tag" :class="chatTestResult?.status || 'idle'">
                {{ chatTestResult?.status === 'success' ? '连通正常' : (chatTestResult?.status === 'failed' ? '连接异常' : '未检测') }}
              </span>
            </div>
            <p class="engine-intro">驱动剧情伴读 AI Bot、分集解构剖析与实时高光问答</p>

            <!-- Provider Switcher -->
            <div class="provider-switch-group">
              <button 
                type="button"
                class="provider-pill-btn" 
                :class="{ active: chatProvider === 'ollama' }"
                @click="switchChatProvider('ollama')"
              >
                <span class="pill-badge">本地</span>
                Ollama
              </button>
              <button 
                type="button"
                class="provider-pill-btn" 
                :class="{ active: chatProvider === 'deepseek' }"
                @click="switchChatProvider('deepseek')"
              >
                <span class="pill-badge cloud-deepseek">云端</span>
                DeepSeek
              </button>
              <button 
                type="button"
                class="provider-pill-btn" 
                :class="{ active: chatProvider === 'mimo' }"
                @click="switchChatProvider('mimo')"
              >
                <span class="pill-badge cloud-mimo">云端</span>
                小米 MiMo
              </button>
              <button 
                type="button"
                class="provider-pill-btn" 
                :class="{ active: chatProvider === 'openai' }"
                @click="switchChatProvider('openai')"
              >
                <span class="pill-badge cloud-openai">云端</span>
                OpenAI
              </button>
            </div>

            <!-- Chat Config Form -->
            <div class="engine-form-stack">
              <div class="form-item">
                <label class="form-label">服务 Base URL</label>
                <input 
                  v-model="chatBaseUrl" 
                  type="text" 
                  class="custom-input"
                  placeholder="如 http://localhost:11434 或 https://api.xiaomimimo.com/v1"
                  :disabled="!isAdmin"
                  id="input-chat-base-url"
                />
              </div>

              <div class="form-item">
                <label class="form-label">驱动模型 (Chat Model)</label>
                <input 
                  v-model="chatModel" 
                  type="text" 
                  class="custom-input"
                  placeholder="如 deepseek-r1:1.5b, mimo-v2.6-flash, gpt-4o-mini"
                  :disabled="!isAdmin"
                  id="input-chat-model"
                />
                <div v-if="chatSuggestions.length" class="suggest-tags-row">
                  <span class="suggest-title">常用：</span>
                  <button 
                    v-for="m in chatSuggestions" 
                    :key="m" 
                    type="button"
                    class="suggest-chip"
                    :class="{ active: chatModel === m }"
                    :disabled="!isAdmin"
                    @click="chatModel = m"
                  >
                    {{ m }}
                  </button>
                </div>
              </div>

              <div v-if="chatProvider !== 'ollama'" class="form-item">
                <label class="form-label">API 鉴权密钥 (API Key)</label>
                <input 
                  v-model="chatApiKey" 
                  type="password" 
                  class="custom-input"
                  placeholder="sk-..."
                  :disabled="!isAdmin"
                  id="input-chat-api-key"
                />
              </div>

              <div class="test-action-line">
                <button 
                  type="button" 
                  class="test-inline-btn"
                  id="btn-test-chat-engine"
                  :disabled="testingChat"
                  @click="testChatEngine"
                >
                  {{ testingChat ? '正在测试对话连通性...' : '⚡ 测试对话模型连通性' }}
                </button>
              </div>

              <div v-if="chatTestResult" class="test-feedback-box" :class="chatTestResult.status">
                <span>{{ chatTestResult.status === 'success' ? '✅' : '❌' }}</span>
                <span>{{ chatTestResult.message }}</span>
              </div>
            </div>
          </div>

          <!-- CARD 2: RAG Embedding Engine -->
          <div class="engine-card glass-panel" id="card-embedding-engine">
            <div class="card-head-line">
              <div class="head-left">
                <span class="engine-badge emb-badge">向量底座</span>
                <h4 class="engine-name">知识库向量嵌入模型 (Embedding Engine)</h4>
              </div>
              <span class="engine-status-tag" :class="embTestResult?.status || 'idle'">
                {{ embTestResult?.status === 'success' ? '计算正常' : (embTestResult?.status === 'failed' ? '计算异常' : '未检测') }}
              </span>
            </div>
            <p class="engine-intro">驱动台词切片向量化、剧本语义 RAG 检索与高能反转秒级检索</p>

            <!-- Provider Switcher -->
            <div class="provider-switch-group">
              <button 
                type="button"
                class="provider-pill-btn" 
                :class="{ active: embProvider === 'ollama' }"
                @click="switchEmbProvider('ollama')"
              >
                <span class="pill-badge">本地</span>
                Ollama 向量模型
              </button>
              <button 
                type="button"
                class="provider-pill-btn" 
                :class="{ active: embProvider === 'openai' }"
                @click="switchEmbProvider('openai')"
              >
                <span class="pill-badge cloud-openai">云端</span>
                OpenAI 兼容 Embedding
              </button>
            </div>

            <!-- Embedding Config Form -->
            <div class="engine-form-stack">
              <div class="form-item">
                <label class="form-label">向量服务 Base URL</label>
                <input 
                  v-model="embBaseUrl" 
                  type="text" 
                  class="custom-input"
                  placeholder="http://localhost:11434"
                  :disabled="!isAdmin"
                  id="input-emb-base-url"
                />
              </div>

              <div class="form-item">
                <label class="form-label">嵌入模型 (Embedding Model)</label>
                <input 
                  v-model="embModel" 
                  type="text" 
                  class="custom-input"
                  placeholder="如 qwen3-embedding:0.6b, bge-m3:latest"
                  :disabled="!isAdmin"
                  id="input-emb-model"
                />
                <div v-if="embSuggestions.length" class="suggest-tags-row">
                  <span class="suggest-title">推荐：</span>
                  <button 
                    v-for="m in embSuggestions" 
                    :key="m" 
                    type="button"
                    class="suggest-chip"
                    :class="{ active: embModel === m }"
                    :disabled="!isAdmin"
                    @click="embModel = m"
                  >
                    {{ m }}
                  </button>
                </div>
              </div>

              <div v-if="embProvider !== 'ollama'" class="form-item">
                <label class="form-label">向量 API 密钥 (API Key)</label>
                <input 
                  v-model="embApiKey" 
                  type="password" 
                  class="custom-input"
                  placeholder="sk-..."
                  :disabled="!isAdmin"
                  id="input-emb-api-key"
                />
              </div>

              <div class="test-action-line">
                <button 
                  type="button" 
                  class="test-inline-btn"
                  id="btn-test-emb-engine"
                  :disabled="testingEmb"
                  @click="testEmbEngine"
                >
                  {{ testingEmb ? '正在测试向量计算...' : '⚡ 测试向量嵌入连通性' }}
                </button>
              </div>

              <div v-if="embTestResult" class="test-feedback-box" :class="embTestResult.status">
                <span>{{ embTestResult.status === 'success' ? '✅' : '❌' }}</span>
                <span>{{ embTestResult.message }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Global Save Notification Banner -->
        <div v-if="saveNotice" class="global-save-banner" :class="saveNotice.status">
          <span>{{ saveNotice.status === 'success' ? '✅' : '❌' }}</span>
          <span>{{ saveNotice.message }}</span>
        </div>

        <!-- Modal Footer Actions -->
        <div class="modal-footer">
          <div class="footer-left">
            <span class="version-label">双轨解耦架构 v2.0 · 实时热加载</span>
          </div>
          <div class="footer-right">
            <button type="button" class="action-btn cancel-btn" @click="close">取消</button>
            <button 
              type="button" 
              class="action-btn save-btn" 
              id="btn-save-engine-config"
              :disabled="saving || !isAdmin"
              @click="saveDualConfig"
              :title="!isAdmin ? '仅管理员可保存' : '保存模型配置并毫秒级热重载'"
            >
              {{ saving ? '保存中...' : (isAdmin ? '保存并热生效' : '只读锁定') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { adminApi } from '../api/admin'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'updated', config: any): void
}>()

const loading = ref(false)
const saving = ref(false)
const testingChat = ref(false)
const testingEmb = ref(false)

const userRole = ref<string>('USER')
const isAdmin = ref<boolean>(false)

// 1. Chat Engine States
type ChatProviderType = 'ollama' | 'deepseek' | 'mimo' | 'openai'
const chatProvider = ref<ChatProviderType>('mimo')
const chatModel = ref('mimo-v2.6-flash')
const chatBaseUrl = ref('https://api.xiaomimimo.com/v1')
const chatApiKey = ref('')
const chatTestResult = ref<{ status: 'success' | 'failed'; message: string } | null>(null)

// 2. Embedding Engine States
type EmbProviderType = 'ollama' | 'openai'
const embProvider = ref<EmbProviderType>('ollama')
const embModel = ref('qwen3-embedding:0.6b')
const embBaseUrl = ref('http://localhost:11434')
const embApiKey = ref('')
const embTestResult = ref<{ status: 'success' | 'failed'; message: string } | null>(null)

const saveNotice = ref<{ status: 'success' | 'failed'; message: string } | null>(null)

const probeData = ref<any>({
  ollama: { running: false, chat_models: [], embedding_models: [], all_models: [] },
  deepseek: { configured: false, masked_key: '', supported_models: ['deepseek-chat', 'deepseek-reasoner'] },
  mimo: { configured: false, masked_key: '', supported_models: ['mimo-v1', 'mimo-v1-chat', 'mimo-v1-pro'] },
  openai: { configured: false, masked_key: '', supported_models: ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'] }
})

const chatSuggestions = computed(() => {
  if (chatProvider.value === 'ollama') {
    return probeData.value.ollama?.chat_models?.length ? probeData.value.ollama.chat_models : ['deepseek-r1:1.5b', 'qwen3.5:2b']
  }
  if (chatProvider.value === 'deepseek') return ['deepseek-chat', 'deepseek-reasoner']
  if (chatProvider.value === 'mimo') return ['mimo-v2.6-flash', 'mimo-v1-chat', 'mimo-v1-pro']
  if (chatProvider.value === 'openai') return ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo']
  return []
})

const embSuggestions = computed(() => {
  if (embProvider.value === 'ollama') {
    return probeData.value.ollama?.embedding_models?.length ? probeData.value.ollama.embedding_models : ['qwen3-embedding:0.6b', 'bge-m3:latest']
  }
  return ['text-embedding-3-small', 'text-embedding-3-large']
})

const getRoleLabel = (role: string): string => {
  const map: Record<string, string> = {
    USER: '普通用户',
    CREATOR: '创作者',
    REVIEWER: '审核员',
    ADMIN: '系统管理员',
    GUEST: '游客'
  }
  return map[role] || role
}

const checkUserPermission = () => {
  try {
    const raw = localStorage.getItem('user')
    if (raw) {
      const user = JSON.parse(raw)
      userRole.value = user.role || 'USER'
      isAdmin.value = user.role === 'ADMIN'
    } else {
      userRole.value = 'GUEST'
      isAdmin.value = false
    }
  } catch {
    isAdmin.value = false
  }
}

const switchChatProvider = (p: ChatProviderType) => {
  chatProvider.value = p
  chatTestResult.value = null
  if (p === 'ollama') {
    chatBaseUrl.value = 'http://localhost:11434'
    chatModel.value = probeData.value.ollama?.chat_models?.[0] || 'deepseek-r1:1.5b'
  } else if (p === 'deepseek') {
    chatBaseUrl.value = 'https://api.deepseek.com'
    chatModel.value = 'deepseek-chat'
  } else if (p === 'mimo') {
    chatBaseUrl.value = 'https://api.xiaomimimo.com/v1'
    chatModel.value = 'mimo-v2.6-flash'
  } else if (p === 'openai') {
    chatBaseUrl.value = 'https://api.openai.com/v1'
    chatModel.value = 'gpt-4o-mini'
  }
}

const switchEmbProvider = (p: EmbProviderType) => {
  embProvider.value = p
  embTestResult.value = null
  if (p === 'ollama') {
    embBaseUrl.value = 'http://localhost:11434'
    embModel.value = probeData.value.ollama?.embedding_models?.[0] || 'qwen3-embedding:0.6b'
  } else {
    embBaseUrl.value = 'https://api.openai.com/v1'
    embModel.value = 'text-embedding-3-small'
  }
}

const quickSwitchToAdmin = async () => {
  try {
    const res = await fetch('/api/v1/auth/quick-switch/ADMIN', { method: 'POST' })
    if (res.ok) {
      const json = await res.json()
      const token = json.access_token || json.data?.access_token
      const user = json.user || json.data?.user
      if (token) {
        localStorage.setItem('cinema_access_token', token)
        localStorage.setItem('token', token)
        localStorage.setItem('user', JSON.stringify(user))
        userRole.value = 'ADMIN'
        isAdmin.value = true
        saveNotice.value = {
          status: 'success',
          message: '已成功切换至系统管理员 (ADMIN) 身份，已解锁模型配置权限！'
        }
      }
    }
  } catch (err: any) {
    console.error('Failed to switch to admin:', err)
  }
}

const loadData = async () => {
  loading.value = true
  chatTestResult.value = null
  embTestResult.value = null
  saveNotice.value = null
  checkUserPermission()
  try {
    // 1. Load Dual Settings
    const dualRes: any = await adminApi.getDualModelSettings()
    const dualData = dualRes?.data || dualRes
    if (dualData?.chat_engine) {
      chatProvider.value = dualData.chat_engine.provider || 'mimo'
      chatModel.value = dualData.chat_engine.model_name || 'mimo-v2.6-flash'
      chatBaseUrl.value = dualData.chat_engine.base_url || 'https://api.xiaomimimo.com/v1'
      chatApiKey.value = dualData.chat_engine.api_key || ''
    }
    if (dualData?.embedding_engine) {
      embProvider.value = dualData.embedding_engine.provider || 'ollama'
      embModel.value = dualData.embedding_engine.model_name || 'qwen3-embedding:0.6b'
      embBaseUrl.value = dualData.embedding_engine.base_url || 'http://localhost:11434'
      embApiKey.value = dualData.embedding_engine.api_key || ''
    }

    // 2. Load Probe Telemetry
    const probeRes = await fetch('/api/v1/models/probe')
    if (probeRes.ok) {
      const json = await probeRes.json()
      if (json.code === 200 && json.data) {
        probeData.value = json.data
      }
    }
  } catch (err) {
    console.error('Failed to load dual engine settings:', err)
  } finally {
    loading.value = false
  }
}

const testChatEngine = async () => {
  testingChat.value = true
  chatTestResult.value = null
  try {
    const res: any = await adminApi.testChatConnection({
      provider: chatProvider.value,
      model: chatModel.value.trim(),
      base_url: chatBaseUrl.value.trim(),
      api_key: chatApiKey.value.trim() || undefined
    })
    const data = res?.data || res
    if (res?.code === 200 || data?.code === 200) {
      chatTestResult.value = {
        status: 'success',
        message: data.reply || '对话推理模型连通成功！'
      }
    } else {
      chatTestResult.value = {
        status: 'failed',
        message: data.detail || '对话模型连接失败'
      }
    }
  } catch (err: any) {
    chatTestResult.value = {
      status: 'failed',
      message: err.message || '网络连接异常'
    }
  } finally {
    testingChat.value = false
  }
}

const testEmbEngine = async () => {
  testingEmb.value = true
  embTestResult.value = null
  try {
    const res: any = await adminApi.testEmbeddingConnection({
      provider: embProvider.value,
      model: embModel.value.trim(),
      base_url: embBaseUrl.value.trim(),
      api_key: embApiKey.value.trim() || undefined
    })
    const data = res?.data || res
    if (res?.code === 200 || data?.code === 200) {
      embTestResult.value = {
        status: 'success',
        message: data.reply || '向量嵌入模型计算正常！'
      }
    } else {
      embTestResult.value = {
        status: 'failed',
        message: data.detail || '向量模型测试失败'
      }
    }
  } catch (err: any) {
    embTestResult.value = {
      status: 'failed',
      message: err.message || '向量服务连接失败'
    }
  } finally {
    testingEmb.value = false
  }
}

const saveDualConfig = async () => {
  if (!isAdmin.value) {
    saveNotice.value = {
      status: 'failed',
      message: '权限不足：仅系统管理员 (ADMIN) 可修改全局模型配置！'
    }
    return
  }
  saving.value = true
  saveNotice.value = null
  try {
    const payload = {
      chat_engine: {
        provider: chatProvider.value,
        model_name: chatModel.value.trim(),
        base_url: chatBaseUrl.value.trim(),
        api_key: chatApiKey.value.trim() || undefined
      },
      embedding_engine: {
        provider: embProvider.value,
        model_name: embModel.value.trim(),
        base_url: embBaseUrl.value.trim(),
        api_key: embApiKey.value.trim() || undefined
      }
    }
    const res: any = await adminApi.updateDualModelSettings(payload)
    saveNotice.value = {
      status: 'success',
      message: '双轨大模型配置已成功保存并实时热重载生效！'
    }
    emit('updated', res?.data || payload)
    setTimeout(() => {
      close()
    }, 1200)
  } catch (err: any) {
    saveNotice.value = {
      status: 'failed',
      message: err.message || '保存配置失败'
    }
  } finally {
    saving.value = false
  }
}

const close = () => {
  emit('update:modelValue', false)
}

watch(() => props.modelValue, (val) => {
  if (val) {
    loadData()
  }
})
</script>

<style scoped>
.settings-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
  box-sizing: border-box;
}

.settings-modal-card {
  width: 100%;
  max-width: 960px;
  max-height: 90vh;
  background: rgba(22, 24, 29, 0.94);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 20px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: #f5f5f7;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
}

.header-title-box {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  font-size: 24px;
}

.modal-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #ffffff;
}

.modal-subtitle {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 18px;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  color: #ffffff;
}

.modal-dual-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  padding: 24px;
  overflow-y: auto;
  max-height: calc(90vh - 170px);
}

.engine-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.card-head-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.head-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.engine-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  color: #ffffff;
}

.chat-badge {
  background: #0071e3;
}

.emb-badge {
  background: #34c759;
}

.engine-name {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}

.engine-status-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

.engine-status-tag.success {
  background: rgba(52, 199, 89, 0.2);
  color: #34c759;
  border: 1px solid rgba(52, 199, 89, 0.4);
}

.engine-status-tag.failed {
  background: rgba(255, 59, 48, 0.2);
  color: #ff3b30;
  border: 1px solid rgba(255, 59, 48, 0.4);
}

.engine-status-tag.idle {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
}

.engine-intro {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.4;
}

.provider-switch-group {
  display: flex;
  gap: 6px;
  background: rgba(0, 0, 0, 0.3);
  padding: 4px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.provider-pill-btn {
  flex: 1;
  border: none;
  background: transparent;
  padding: 6px 4px;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.2s;
  white-space: nowrap;
}

.provider-pill-btn.active {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.pill-badge {
  font-size: 9px;
  padding: 1px 4px;
  border-radius: 4px;
  background: #0071e3;
  color: #ffffff;
}

.pill-badge.cloud-deepseek { background: #0066ff; }
.pill-badge.cloud-mimo { background: #fb7299; }
.pill-badge.cloud-openai { background: #10a37f; }

.engine-form-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}

.custom-input {
  width: 100%;
  height: 36px;
  padding: 0 12px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  font-size: 13px;
  color: #ffffff;
  outline: none;
  box-sizing: border-box;
  transition: all 0.2s;
}

.custom-input:focus {
  border-color: #0071e3;
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.3);
  background: rgba(255, 255, 255, 0.1);
}

.custom-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.suggest-tags-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.suggest-title {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.suggest-chip {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  cursor: pointer;
}

.suggest-chip:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
}

.suggest-chip.active {
  background: rgba(0, 113, 227, 0.3);
  border-color: #0071e3;
  color: #ffffff;
}

.test-inline-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #ffffff;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
}

.test-inline-btn:hover {
  background: rgba(255, 255, 255, 0.15);
}

.test-feedback-box {
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.test-feedback-box.success {
  background: rgba(52, 199, 89, 0.15);
  border: 1px solid rgba(52, 199, 89, 0.35);
  color: #34c759;
}

.test-feedback-box.failed {
  background: rgba(255, 59, 48, 0.15);
  border: 1px solid rgba(255, 59, 48, 0.35);
  color: #ff3b30;
}

.global-save-banner {
  margin: 0 24px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.global-save-banner.success {
  background: rgba(52, 199, 89, 0.2);
  color: #34c759;
  border: 1px solid rgba(52, 199, 89, 0.4);
}

.global-save-banner.failed {
  background: rgba(255, 59, 48, 0.2);
  color: #ff3b30;
  border: 1px solid rgba(255, 59, 48, 0.4);
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
}

.version-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-btn {
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.cancel-btn {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.cancel-btn:hover {
  background: rgba(255, 255, 255, 0.15);
}

.save-btn {
  background: #0071e3;
  color: #ffffff;
}

.save-btn:hover {
  background: #0077ed;
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.4);
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.admin-notice-banner {
  margin: 12px 24px 0 24px;
  background: rgba(255, 149, 0, 0.15);
  border: 1px solid rgba(255, 149, 0, 0.35);
  border-radius: 10px;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.notice-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.notice-title {
  font-size: 13px;
  font-weight: 600;
  color: #ff9500;
}

.notice-desc {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
}

.switch-admin-btn {
  background: #ff9500;
  color: #000;
  font-weight: 700;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}
</style>
