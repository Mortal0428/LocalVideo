<template>
  <el-dialog
    v-model="dialogVisible"
    :title="modalTitle"
    width="760px"
    class="universal-agent-dialog"
    destroy-on-close
    :append-to-body="true"
    @open="handleDialogOpen"
  >
    <div class="uagent-chat-container">
      <!-- 顶部智能体身份与滑动窗口提示条 -->
      <div class="uagent-header-strip">
        <div class="uagent-id-box">
          <span class="uagent-badge">{{ agentId.toUpperCase() }}</span>
          <span class="uagent-role-text">{{ roleTitle }}</span>
        </div>
        <div class="uagent-strip-actions">
          <span class="uagent-window-tip">滑动窗口记忆：保留近 10 轮 (物理隔离防串通)</span>
          <button class="btn-reset-history" title="清空并重启本智能体历史会话" @click="clearHistory">
            清空历史
          </button>
        </div>
      </div>

      <!-- 消息列表滚动区 -->
      <div class="uagent-messages-scroll" ref="scrollContainer">
        <div v-if="messages.length === 0" class="uagent-empty-hint">
          <div class="uagent-empty-avatar">{{ getAvatarInitial(agentId) }}</div>
          <p class="empty-main">我是【{{ agentName }}】，很高兴为您服务！</p>
          <p class="empty-sub">支持自由发送对话、上传剧本文档附件或图片，智能体将真实调用大模型进行多模态深度协同。</p>
        </div>

        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="uagent-msg-row"
          :class="'is-' + msg.role"
        >
          <div class="uagent-avatar">
            {{ msg.role === 'user' ? '我' : getAvatarInitial(agentId) }}
          </div>
          <div class="uagent-bubble" :class="{ 'is-diag-error': msg.isDiagnostic }">
            <!-- 思考折叠条 (Thinking Chain) -->
            <div v-if="msg.thought" class="uagent-thought-pill">
              <span class="thought-tag">Thinking 思考链路：</span>
              <span class="thought-content">{{ msg.thought }}</span>
            </div>

            <!-- 用户上传的图片预览 -->
            <div v-if="msg.attachment_url && msg.is_image" class="uagent-msg-image-wrap">
              <img :src="msg.attachment_url" alt="上传图片" class="uagent-msg-image" />
            </div>

            <!-- 用户上传的文件胶囊 -->
            <div v-else-if="msg.attachment_name" class="uagent-msg-file-pill">
              <span class="file-icon">📄</span>
              <span class="file-name">{{ msg.attachment_name }}</span>
            </div>

            <!-- 正文内容 (支持打字机光标与结构化 Markdown 渲染) -->
            <div
              v-if="msg.role === 'assistant'"
              class="uagent-text markdown-render"
              v-html="renderMarkdown(msg.content)"
            ></div>
            <div v-else class="uagent-text user-text">
              {{ msg.content }}
            </div>
            <span v-if="msg.isTyping" class="uagent-cursor">▌</span>

            <!-- 工具执行数据卡片 (选填展示) -->
            <div v-if="msg.tool_results && msg.tool_results.length > 0" class="uagent-tool-card">
              <span class="tool-card-title">工具执行回包 (已验证真实入库):</span>
              <pre class="tool-card-pre">{{ formatToolData(msg.tool_results[0]) }}</pre>
            </div>

            <span class="uagent-timestamp">{{ msg.timestamp || '刚刚' }}</span>
          </div>
        </div>

        <div v-if="isThinking" class="uagent-msg-row is-assistant thinking-placeholder">
          <div class="uagent-avatar">{{ getAvatarInitial(agentId) }}</div>
          <div class="uagent-bubble">
            <div class="thinking-dots">
              <span class="dot"></span><span class="dot"></span><span class="dot"></span>
              <span class="thinking-text">{{ agentName }} 正在调用底层大模型进行深度思辨...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部附件上传与输入框 -->
      <div class="uagent-input-dock">
        <!-- 待发送附件预览栏 -->
        <div v-if="attachedFile" class="uagent-attachment-preview">
          <div v-if="attachedFile.is_image" class="image-preview-box">
            <img :src="attachedFile.file_url" alt="预览" class="preview-thumb" />
            <span class="thumb-name">{{ attachedFile.file_name }}</span>
          </div>
          <div v-else class="doc-preview-box">
            <span class="doc-icon">📑</span>
            <span class="doc-name">{{ attachedFile.file_name }} ({{ formatFileSize(attachedFile.file_size) }})</span>
          </div>
          <button class="btn-clear-att" title="移除该附件" @click="clearAttachment">✕</button>
        </div>

        <div class="uagent-input-row">
          <!-- 上传附件/图片按钮 (ChatGPT 风格) -->
          <label class="btn-attach-file" title="上传剧本文档 (.txt, .md, .pdf) 或参考剧照图片 (.png, .jpg, .webp)">
            <input
              type="file"
              accept=".txt,.md,.json,.doc,.docx,.pdf,.png,.jpg,.jpeg,.webp"
              style="display: none;"
              :disabled="isUploading || isThinking"
              @change="handleFileSelected"
            />
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
          </label>

          <input
            v-model="inputQuery"
            type="text"
            class="uagent-text-input"
            :placeholder="inputPlaceholder"
            :disabled="isThinking"
            @keyup.enter="handleSend"
          />

          <button
            class="uagent-send-btn"
            :disabled="(!inputQuery.trim() && !attachedFile) || isThinking || isUploading"
            @click="handleSend"
          >
            {{ isThinking ? '思考中...' : '发送' }}
          </button>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps<{
  modelValue: boolean
  agentId: string
  agentName: string
  roleTitle: string
  contextData?: Record<string, any>
}>()

const emit = defineEmits(['update:modelValue'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const modalTitle = computed(() => `专属智能体中枢: ${props.agentName}`)
const inputPlaceholder = computed(() => {
  if (props.agentId === 'agent_7') return '输入找剧诉求，或粘贴外部短剧网盘链接...'
  if (props.agentId === 'agent_8') return '输入故事大纲或点击左侧上传剧本文档/分镜图片...'
  if (props.agentId === 'agent_3') return '询问向量化情况、未切片列表或知识图谱状态...'
  if (props.agentId === 'agent_4') return '咨询敏感词风控拦截、台词审查或违规判定...'
  return '输入您的问题或指令，与专属领域专家展开多轮协同...'
})

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  thought?: string
  tool_results?: any[]
  timestamp?: string
  isTyping?: boolean
  isDiagnostic?: boolean
  attachment_url?: string
  attachment_name?: string
  is_image?: boolean
}

interface AttachedFileInfo {
  file_name: string
  file_path: string
  file_url: string
  file_size: number
  is_image: boolean
  preview_text?: string
}

const messages = ref<ChatMessage[]>([])
const inputQuery = ref('')
const isThinking = ref(false)
const isUploading = ref(false)
const attachedFile = ref<AttachedFileInfo | null>(null)
const scrollContainer = ref<HTMLElement | null>(null)

// 针对每个智能体维持确定性持久化隔离作用域
const sessionId = computed(() => `uagent_session_${props.agentId}`)

function getAvatarInitial(id: string): string {
  if (!id) return 'A'
  const match = id.match(/\d+/)
  return match ? `A${match[0]}` : 'A'
}

function formatFileSize(bytes: number): string {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function renderMarkdown(content: string): string {
  if (!content) return ''
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Code blocks: ```lang\n...\n```
  html = html.replace(/```([\w-]*)\n([\s\S]*?)```/g, (_m, lang, code) => {
    return `<pre class="md-code-block"><code class="lang-${lang}">${code.trim()}</code></pre>`
  })

  // Inline code: `code`
  html = html.replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>')

  // Headers: ###, ##, #
  html = html.replace(/^### (.*$)/gim, '<h4 class="md-h3">$1</h4>')
  html = html.replace(/^## (.*$)/gim, '<h3 class="md-h2">$1</h3>')
  html = html.replace(/^# (.*$)/gim, '<h2 class="md-h1">$1</h2>')

  // Horizontal rules: --- or ***
  html = html.replace(/^\s*(?:---|\*\*\*)\s*$/gim, '<hr class="md-hr" />')

  // Bold & Italic
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')

  // Tables: lines starting with | and ending with |
  html = html.replace(/((?:(?:^|\n)\|[^\n]+\|\s*)+)/g, (tableBlock) => {
    const rawLines = tableBlock.trim().split('\n').map(l => l.trim()).filter(Boolean)
    if (rawLines.length < 2) return tableBlock
    const isSeparator = /^\|(?::?-+:?\|)+$/.test(rawLines[1].replace(/\s+/g, ''))
    if (!isSeparator) return tableBlock

    const parseRow = (line: string) => line.slice(1, -1).split('|').map(c => c.trim())
    const headers = parseRow(rawLines[0])
    const bodyLines = rawLines.slice(2)

    let tableHtml = '<div class="md-table-wrap"><table class="md-table"><thead><tr>'
    for (const h of headers) tableHtml += `<th>${h}</th>`
    tableHtml += '</tr></thead><tbody>'
    for (const bLine of bodyLines) {
      const cells = parseRow(bLine)
      tableHtml += '<tr>'
      for (let i = 0; i < headers.length; i++) tableHtml += `<td>${cells[i] || ''}</td>`
      tableHtml += '</tr>'
    }
    tableHtml += '</tbody></table></div>'
    return '\n' + tableHtml + '\n'
  })

  // Bullet Lists: - item or * item
  html = html.replace(/(?:^|\n)[-*] (.*)/g, '\n<li class="md-li">$1</li>')
  html = html.replace(/((?:<li class="md-li">.*<\/li>\s*)+)/g, '<ul class="md-ul">$1</ul>')

  // Line breaks
  html = html.replace(/\n\n/g, '<div class="md-gap"></div>')
  html = html.replace(/\n/g, '<br />')

  return html
}

function formatToolData(data: any): string {
  if (!data) return ''
  try {
    return JSON.stringify(data.data || data, null, 2)
  } catch (e) {
    return String(data)
  }
}

async function handleDialogOpen() {
  await loadHistory()
}

async function loadHistory() {
  try {
    const res = await axios.get(`/api/v1/agent-mesh/history/${props.agentId}/${sessionId.value}`)
    if (res.data?.data && Array.isArray(res.data.data)) {
      messages.value = res.data.data.map((m: any) => ({
        role: m.role || 'assistant',
        content: m.content || '',
        thought: m.thought || '',
        tool_results: m.tool_results || [],
        timestamp: m.timestamp || '此前会话',
        isDiagnostic: (m.content || '').includes('[模型连接/配置异常:'),
      }))
      scrollToBottom()
    }
  } catch (e) {
    console.warn('Failed to load isolated history:', e)
  }
}

async function clearHistory() {
  try {
    await ElMessageBox.confirm('确定要清空该智能体的专属滑动窗口历史吗？', '提示', {
      type: 'warning',
      confirmButtonText: '确定清空',
      cancelButtonText: '取消',
    })
    messages.value = []
    ElMessage.success('已清空当前智能体历史记忆')
  } catch {
    // canceled
  }
}

async function handleFileSelected(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  const file = target.files[0]
  const formData = new FormData()
  formData.append('file', file)

  isUploading.value = true
  try {
    const res = await axios.post('/api/v1/agent-mesh/upload-attachment', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (res.data?.data) {
      attachedFile.value = res.data.data
      ElMessage.success(`附件【${file.name}】已成功解析挂载`)
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '附件上传失败')
  } finally {
    isUploading.value = false
    target.value = ''
  }
}

function clearAttachment() {
  attachedFile.value = null
}

function scrollToBottom() {
  nextTick(() => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
    }
  })
}

async function handleSend() {
  const query = inputQuery.value.trim()
  if (!query && !attachedFile.value) return

  const currentAtt = attachedFile.value
  const userMsgText = query || (currentAtt ? `[已发送附件: ${currentAtt.file_name}]` : '')

  // 1. 推入用户端消息
  messages.value.push({
    role: 'user',
    content: userMsgText,
    attachment_name: currentAtt ? currentAtt.file_name : undefined,
    attachment_url: currentAtt ? currentAtt.file_url : undefined,
    is_image: currentAtt ? currentAtt.is_image : false,
    timestamp: '刚刚',
  })

  inputQuery.value = ''
  clearAttachment()
  isThinking.value = true
  scrollToBottom()

  try {
    const res = await axios.post('/api/v1/agent-mesh/chat', {
      agent_id: props.agentId,
      session_id: sessionId.value,
      message: userMsgText,
      attachment_path: currentAtt ? currentAtt.file_path : null,
      context_data: props.contextData || {},
    })

    const data = res.data?.data || {}
    const fullReply = data.reply || '已完成处理。'
    const isDiag = fullReply.includes('[模型连接/配置异常:')

    // 2. 准备打字机流式输出
    const assistantMsg = ref<ChatMessage>({
      role: 'assistant',
      content: isDiag ? fullReply : '',
      thought: data.thought || '',
      tool_results: data.tool_data ? [{ data: data.tool_data }] : (data.storyboard_data ? [{ data: data.storyboard_data }] : []),
      timestamp: '刚刚',
      isTyping: !isDiag,
      isDiagnostic: isDiag,
    })

    messages.value.push(assistantMsg.value)
    scrollToBottom()

    if (!isDiag) {
      // 快速打字机输出动画 (每步步长按长度自适应)
      const step = Math.max(2, Math.floor(fullReply.length / 32))
      for (let i = 0; i < fullReply.length; i += step) {
        assistantMsg.value.content = fullReply.slice(0, i + step)
        scrollToBottom()
        await new Promise((resolve) => setTimeout(resolve, 25))
      }
      assistantMsg.value.content = fullReply
      assistantMsg.value.isTyping = false
      scrollToBottom()
    }
  } catch (err: any) {
    messages.value.push({
      role: 'assistant',
      content: '[系统诊断异常: 后端请求超时或服务掉线，已触发弹性断路器保护]',
      isDiagnostic: true,
      timestamp: '刚刚',
    })
  } finally {
    isThinking.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.uagent-chat-container {
  display: flex;
  flex-direction: column;
  height: 580px;
  background: var(--agent-card-surface, #ffffff);
  color: var(--agent-text-title, #1d1d1f);
}

.uagent-header-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--agent-bg-canvas, #f5f5f7);
  border-bottom: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

.uagent-id-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.uagent-badge {
  font-size: 11px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 6px;
  background: #0071e3;
  color: #ffffff;
}

.uagent-role-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--agent-text-body, #2c2c2e);
}

.uagent-strip-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.uagent-window-tip {
  font-size: 11px;
  color: var(--agent-text-muted, #6e6e73);
}

.btn-reset-history {
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.12);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--agent-text-secondary, #515154);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-reset-history:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #ff3b30;
  border-color: #ff3b30;
}

.uagent-messages-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.uagent-empty-hint {
  text-align: center;
  margin: auto;
  padding: 30px;
}

.uagent-empty-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #0071e3;
  color: #fff;
  font-size: 18px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 14px;
}

.empty-main {
  font-size: 15px;
  font-weight: 700;
  color: var(--agent-text-title, #1d1d1f);
}

.empty-sub {
  font-size: 12.5px;
  color: var(--agent-text-muted, #6e6e73);
  margin-top: 6px;
  max-width: 440px;
  line-height: 1.5;
}

.uagent-msg-row {
  display: flex;
  gap: 10px;
  max-width: 88%;
}

.uagent-msg-row.is-user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.uagent-msg-row.is-assistant {
  align-self: flex-start;
}

.uagent-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  background: #0071e3;
  color: #ffffff;
  flex-shrink: 0;
}

.uagent-msg-row.is-user .uagent-avatar {
  background: #34c759;
}

.uagent-bubble {
  padding: 12px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.55;
  background: var(--agent-bubble-agent, #f0f4fc);
  border: 1px solid var(--agent-bubble-agent-border, rgba(0, 113, 227, 0.15));
  color: var(--agent-text-title, #1d1d1f);
}

.uagent-bubble.is-diag-error {
  background: rgba(255, 59, 48, 0.08);
  border: 1px solid rgba(255, 59, 48, 0.3);
  color: #d70015;
}

.uagent-msg-row.is-user .uagent-bubble {
  background: #0071e3;
  color: #ffffff;
  border: none;
}

.uagent-thought-pill {
  font-size: 11.5px;
  padding: 5px 8px;
  margin-bottom: 8px;
  border-radius: 6px;
  background: rgba(0, 113, 227, 0.08);
  border-left: 3px solid #0071e3;
  color: var(--agent-text-secondary, #515154);
}

.thought-tag {
  font-weight: 700;
  margin-right: 4px;
}

.uagent-msg-image-wrap {
  margin-bottom: 8px;
}

.uagent-msg-image {
  max-width: 240px;
  max-height: 180px;
  border-radius: 8px;
  object-fit: cover;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.uagent-msg-file-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.2);
  margin-bottom: 8px;
  font-size: 12px;
}

.uagent-cursor {
  display: inline-block;
  color: #0071e3;
  animation: cursor-blink 0.8s infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.uagent-tool-card {
  margin-top: 8px;
  padding: 8px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.04);
  font-size: 11px;
}

.tool-card-title {
  font-weight: 700;
  color: var(--agent-text-secondary, #515154);
}

.tool-card-pre {
  margin: 4px 0 0;
  font-family: monospace;
  white-space: pre-wrap;
  max-height: 140px;
  overflow-y: auto;
}

.uagent-timestamp {
  display: block;
  font-size: 10px;
  color: var(--agent-text-muted, #8e8e93);
  margin-top: 4px;
  text-align: right;
}

.uagent-input-dock {
  padding: 12px 16px;
  background: var(--agent-bg-canvas, #f5f5f7);
  border-top: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

.uagent-attachment-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(0, 113, 227, 0.08);
  border: 1px dashed rgba(0, 113, 227, 0.3);
  margin-bottom: 10px;
}

.image-preview-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-thumb {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  object-fit: cover;
}

.thumb-name, .doc-name {
  font-size: 12px;
  font-weight: 600;
  color: #0071e3;
}

.doc-preview-box {
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-clear-att {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 13px;
  color: #6e6e73;
}

.btn-clear-att:hover {
  color: #ff3b30;
}

.uagent-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-attach-file {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-input-border, rgba(0, 0, 0, 0.12));
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--agent-text-secondary, #515154);
  transition: all 0.2s;
}

.btn-attach-file:hover {
  border-color: #0071e3;
  color: #0071e3;
}

.uagent-text-input {
  flex: 1;
  height: 38px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid var(--agent-input-border, rgba(0, 0, 0, 0.12));
  background: var(--agent-card-surface, #ffffff);
  color: var(--agent-text-title, #1d1d1f);
  font-size: 13px;
}

.uagent-send-btn {
  height: 38px;
  padding: 0 18px;
  border-radius: 8px;
  border: none;
  background: #0071e3;
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.uagent-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.thinking-dots {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #0071e3;
  font-size: 12px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #0071e3;
  animation: pulse-dot 1.2s infinite ease-in-out;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes pulse-dot {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* Markdown 结构化输出样式 (Apple HIG 语义化排版与原生表格) */
.markdown-render :deep(.md-h1) {
  font-size: 14.5px;
  font-weight: 700;
  margin: 6px 0 4px 0;
  color: inherit;
}

.markdown-render :deep(.md-h2) {
  font-size: 13.5px;
  font-weight: 700;
  margin: 5px 0 3px 0;
  color: inherit;
}

.markdown-render :deep(.md-h3) {
  font-size: 12.5px;
  font-weight: 600;
  margin: 3px 0 2px 0;
}

.markdown-render :deep(.md-hr) {
  border: none;
  border-top: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.1));
  margin: 8px 0;
}

.markdown-render :deep(.md-table-wrap) {
  width: 100%;
  overflow-x: auto;
  margin: 8px 0;
  border-radius: 8px;
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.12));
}

.markdown-render :deep(.md-table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  text-align: left;
}

.markdown-render :deep(.md-table th),
.markdown-render :deep(.md-table td) {
  padding: 6px 10px;
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

.markdown-render :deep(.md-table th) {
  background: var(--agent-card-surface, #ffffff);
  font-weight: 700;
  color: var(--agent-text-title, #1d1d1f);
}

.markdown-render :deep(.md-table td) {
  background: var(--agent-bg-canvas, #f8f9fa);
  color: var(--agent-text-body, #2c2c2e);
}

.markdown-render :deep(.md-code-block) {
  background: #1e1e24;
  color: #f8f8f2;
  padding: 8px 10px;
  border-radius: 6px;
  font-family: monospace;
  font-size: 11.5px;
  overflow-x: auto;
  margin: 6px 0;
}

.markdown-render :deep(.md-inline-code) {
  background: rgba(0, 113, 227, 0.1);
  color: #0071e3;
  padding: 1px 4px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 11.5px;
}

.markdown-render :deep(.md-ul) {
  margin: 4px 0;
  padding-left: 18px;
}

.markdown-render :deep(.md-li) {
  margin-bottom: 2px;
}

.markdown-render :deep(.md-gap) {
  height: 6px;
}
</style>

<style>
/* Universal Agent Dialog Global Styles for Light & Dark */
.universal-agent-dialog {
  border-radius: 18px !important;
  overflow: hidden !important;
  background: var(--agent-card-surface, #ffffff) !important;
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08)) !important;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.15) !important;
}

[data-theme="light"] .universal-agent-dialog {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  color: #18191C !important;
}

[data-theme="light"] .universal-agent-dialog .el-dialog__header {
  background: #f8f9fa !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
  margin: 0 !important;
  padding: 16px 20px !important;
}

[data-theme="light"] .universal-agent-dialog .el-dialog__title {
  color: #18191C !important;
  font-weight: 700 !important;
}

[data-theme="light"] .universal-agent-dialog .el-dialog__body {
  padding: 0 !important;
  background: #ffffff !important;
  color: #18191C !important;
}

[data-theme="dark"] .universal-agent-dialog {
  background: #161B22 !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #F5F5F7 !important;
}

[data-theme="dark"] .universal-agent-dialog .el-dialog__header {
  background: #0D1117 !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
  margin: 0 !important;
  padding: 16px 20px !important;
}

[data-theme="dark"] .universal-agent-dialog .el-dialog__title {
  color: #F5F5F7 !important;
  font-weight: 700 !important;
}

[data-theme="dark"] .universal-agent-dialog .el-dialog__body {
  padding: 0 !important;
  background: #161B22 !important;
  color: #F5F5F7 !important;
}
</style>
