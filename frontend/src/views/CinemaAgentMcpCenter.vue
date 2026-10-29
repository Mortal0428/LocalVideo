<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Connection,
  Cpu,
  Monitor,
  VideoCamera,
  FolderOpened,
  Document,
  CaretRight,
  Refresh,
  Check,
  Warning,
  CircleCheck,
  Plus,
  Compass
} from '@element-plus/icons-vue'
import { mcpApi, type McpOverviewData, type McpServerNode } from '../api/mcp'

const props = withDefaults(defineProps<{
  isDark?: boolean
}>(), {
  isDark: true
})

// 1. Data State
const loading = ref(false)
const sandboxLoading = ref(false)
const overview = ref<McpOverviewData | null>(null)
const activeCapTab = ref<'tools' | 'resources' | 'prompts'>('tools')

// 2. Sandbox Form State
const sandboxForm = reactive({
  method: 'tools/call' as 'tools/call' | 'resources/read' | 'prompts/get',
  target: 'moderation_inspect_content',
  paramsJson: JSON.stringify({
    content: '这部短剧的编剧真的很厉害，剧情反转让人意想不到！',
    target_type: 'danmaku',
    risk_threshold: 60
  }, null, 2)
})

const requestPayloadPreview = computed(() => {
  let args = {}
  try {
    args = JSON.parse(sandboxForm.paramsJson || '{}')
  } catch {
    args = { parse_error: 'Invalid JSON' }
  }

  if (sandboxForm.method === 'tools/call') {
    return {
      jsonrpc: '2.0',
      id: Math.floor(Math.random() * 90000) + 10000,
      method: 'tools/call',
      params: {
        name: sandboxForm.target,
        arguments: args
      }
    }
  } else if (sandboxForm.method === 'resources/read') {
    return {
      jsonrpc: '2.0',
      id: Math.floor(Math.random() * 90000) + 10000,
      method: 'resources/read',
      params: {
        uri: sandboxForm.target
      }
    }
  } else {
    return {
      jsonrpc: '2.0',
      id: Math.floor(Math.random() * 90000) + 10000,
      method: 'prompts/get',
      params: {
        name: sandboxForm.target,
        arguments: args
      }
    }
  }
})

const responseOutput = ref<any>(null)
const executionLatencyMs = ref<number | null>(null)

// 3. Preset Templates
function applyPreset(name: string) {
  if (name === 'moderation') {
    sandboxForm.method = 'tools/call'
    sandboxForm.target = 'moderation_inspect_content'
    sandboxForm.paramsJson = JSON.stringify({
      content: '演员演得太差了，强烈退钱，垃圾剧情！',
      target_type: 'danmaku',
      risk_threshold: 60
    }, null, 2)
  } else if (name === 'search') {
    sandboxForm.method = 'tools/call'
    sandboxForm.target = 'cinema_search_dramas'
    sandboxForm.paramsJson = JSON.stringify({
      keyword: '逆袭',
      category: null,
      min_heat: 100,
      limit: 3
    }, null, 2)
  } else if (name === 'transcript') {
    sandboxForm.method = 'tools/call'
    sandboxForm.target = 'cinema_get_episode_transcript'
    sandboxForm.paramsJson = JSON.stringify({
      video_id: 'drama_01',
      episode_num: 1,
      start_sec: 0,
      end_sec: 180
    }, null, 2)
  } else if (name === 'graph') {
    sandboxForm.method = 'tools/call'
    sandboxForm.target = 'graph_query_character_relations'
    sandboxForm.paramsJson = JSON.stringify({
      character_name: '顾千帆',
      drama_title: '梦华录',
      depth: 2
    }, null, 2)
  } else if (name === 'res_trending') {
    sandboxForm.method = 'resources/read'
    sandboxForm.target = 'cinema://dramas/trending-top5'
    sandboxForm.paramsJson = '{}'
  } else if (name === 'res_ontology') {
    sandboxForm.method = 'resources/read'
    sandboxForm.target = 'graph://schema/ontology'
    sandboxForm.paramsJson = '{}'
  } else if (name === 'prompt_twist') {
    sandboxForm.method = 'prompts/get'
    sandboxForm.target = 'critique_plot_twist'
    sandboxForm.paramsJson = JSON.stringify({
      drama_title: '隐秘的角落',
      character: '朱朝阳'
    }, null, 2)
  }
}

// 4. Node Management
const showAddNodeDialog = ref(false)
const newNodeForm = reactive({
  name: '',
  url: 'http://',
  type: 'REMOTE_STREAMABLE'
})

async function fetchOverview() {
  loading.value = true
  try {
    const data = await mcpApi.getOverview()
    overview.value = data
  } catch (err: any) {
    ElMessage.error('获取 MCP 概览状态失败：' + (err.message || '网络异常'))
  } finally {
    loading.value = false
  }
}

async function handleAddNode() {
  if (!newNodeForm.name || !newNodeForm.url) {
    ElMessage.warning('请填写完整的节点名称与服务地址')
    return
  }
  try {
    await mcpApi.registerNode(newNodeForm)
    ElMessage.success('MCP 拓扑节点注册成功')
    showAddNodeDialog.value = false
    newNodeForm.name = ''
    newNodeForm.url = 'http://'
    await fetchOverview()
  } catch (err: any) {
    ElMessage.error('注册节点失败：' + (err.message || '网络异常'))
  }
}

// 5. Execute Sandbox
async function executeSandboxCall() {
  sandboxLoading.value = true
  responseOutput.value = null
  executionLatencyMs.value = null
  const startTime = performance.now()

  try {
    let args = {}
    if (sandboxForm.paramsJson) {
      args = JSON.parse(sandboxForm.paramsJson)
    }

    const payload = {
      jsonrpc: '2.0',
      id: Date.now(),
      method: sandboxForm.method,
      params: sandboxForm.method === 'tools/call'
        ? { name: sandboxForm.target, arguments: args }
        : sandboxForm.method === 'resources/read'
          ? { uri: sandboxForm.target }
          : { name: sandboxForm.target, arguments: args }
    }

    const res = await mcpApi.callJsonRpc(payload)
    executionLatencyMs.value = Math.round(performance.now() - startTime)
    responseOutput.value = res
    ElMessage.success('MCP 调用响应成功 (' + executionLatencyMs.value + 'ms)')
  } catch (err: any) {
    executionLatencyMs.value = Math.round(performance.now() - startTime)
    responseOutput.value = {
      jsonrpc: '2.0',
      error: {
        code: -32603,
        message: err.message || 'Internal RPC Failure',
        detail: err.response?.data || null
      }
    }
    ElMessage.error('MCP 执行失败：' + (err.message || '请求未响应'))
  } finally {
    sandboxLoading.value = false
  }
}

function copyOutput() {
  if (!responseOutput.value) return
  navigator.clipboard.writeText(JSON.stringify(responseOutput.value, null, 2))
  ElMessage.success('已复制响应 JSON 报文')
}

onMounted(() => {
  fetchOverview()
})
</script>

<template>
  <div class="mcp-center-container" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }" id="mcp-center-root">
    <!-- Header Section -->
    <header class="mcp-header-card">
      <div class="mcp-header-left">
        <div class="header-icon-squircle">
          <el-icon :size="22"><Connection /></el-icon>
        </div>
        <div class="header-titles">
          <div class="title-row">
            <h1 class="main-title">Model Context Protocol (MCP) 云端中台</h1>
            <span class="mcp-status-pill online">
              <span class="pulsing-dot"></span>
              ONLINE
            </span>
            <span class="mcp-protocol-pill">JSON-RPC 2.0</span>
          </div>
          <p class="sub-title">
            统一多智能体异构工具协议，高内聚打通平台在架短剧检索、Neo4j 人物知识图谱遍历与全域内容风控审查能力。
          </p>
        </div>
      </div>
      <div class="mcp-header-right">
        <button
          type="button"
          class="action-btn secondary"
          :disabled="loading"
          @click="fetchOverview"
          id="btn-refresh-mcp-status"
        >
          <el-icon :class="{ 'is-spinning': loading }"><Refresh /></el-icon>
          <span>刷新状态</span>
        </button>
      </div>
    </header>

    <!-- Stat Strip -->
    <section class="mcp-stat-strip" id="mcp-stat-strip">
      <div class="stat-card">
        <div class="stat-icon-wrap tool-icon">
          <el-icon :size="18"><Cpu /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-label">已注册工具 (Tools)</span>
          <span class="stat-value" id="val-mcp-tools">{{ overview?.counts?.tools ?? 4 }}</span>
        </div>
        <span class="stat-tag">可执行函数</span>
      </div>

      <div class="stat-card">
        <div class="stat-icon-wrap resource-icon">
          <el-icon :size="18"><FolderOpened /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-label">只读资源 (Resources)</span>
          <span class="stat-value" id="val-mcp-resources">{{ overview?.counts?.resources ?? 2 }}</span>
        </div>
        <span class="stat-tag">URI 定位</span>
      </div>

      <div class="stat-card">
        <div class="stat-icon-wrap prompt-icon">
          <el-icon :size="18"><Document /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-label">提示词模板 (Prompts)</span>
          <span class="stat-value" id="val-mcp-prompts">{{ overview?.counts?.prompts ?? 2 }}</span>
        </div>
        <span class="stat-tag">标准工法</span>
      </div>

      <div class="stat-card">
        <div class="stat-icon-wrap node-icon">
          <el-icon :size="18"><Monitor /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-label">活跃拓扑节点</span>
          <span class="stat-value" id="val-mcp-nodes">{{ overview?.server_nodes?.length ?? 1 }}</span>
        </div>
        <span class="stat-tag">分布式网关</span>
      </div>
    </section>

    <!-- Main Content Workspace (Split Layout) -->
    <div class="mcp-workspace-grid">
      <!-- Left Column: Topology & Capabilities -->
      <div class="mcp-left-column">
        <!-- 1. Distributed Topology Nodes -->
        <div class="mcp-bento-card">
          <div class="bento-header">
            <div class="bento-title-group">
              <el-icon class="bento-icon"><Monitor /></el-icon>
              <h2 class="bento-title">MCP 服务拓扑节点 (Topology)</h2>
            </div>
            <button
              type="button"
              class="mini-btn"
              @click="showAddNodeDialog = true"
              id="btn-add-mcp-node"
            >
              <el-icon><Plus /></el-icon>
              <span>登记外部节点</span>
            </button>
          </div>

          <div class="node-list">
            <div
              v-for="node in overview?.server_nodes"
              :key="node.name"
              class="node-card"
              :class="{ 'is-active': node.status === 'ONLINE' }"
            >
              <div class="node-main">
                <div class="node-status-indicator">
                  <span class="pulse-indicator"></span>
                </div>
                <div class="node-meta">
                  <div class="node-name-row">
                    <span class="node-name">{{ node.name }}</span>
                    <span class="node-badge">{{ node.type }}</span>
                  </div>
                  <span class="node-url">{{ node.url }}</span>
                </div>
              </div>
              <div class="node-stats">
                <span class="ping-badge">{{ node.ping_ms }}ms</span>
                <span class="state-badge online">已连接</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. Capabilities Hub -->
        <div class="mcp-bento-card capabilities-card">
          <div class="bento-header">
            <div class="bento-title-group">
              <el-icon class="bento-icon"><Compass /></el-icon>
              <h2 class="bento-title">MCP 能力大厅 (Capabilities Hub)</h2>
            </div>
            <!-- Sub-tabs -->
            <div class="caps-subnav">
              <button
                type="button"
                class="caps-tab-btn"
                :class="{ active: activeCapTab === 'tools' }"
                @click="activeCapTab = 'tools'"
                id="tab-cap-tools"
              >
                工具集 ({{ overview?.tools?.length || 4 }})
              </button>
              <button
                type="button"
                class="caps-tab-btn"
                :class="{ active: activeCapTab === 'resources' }"
                @click="activeCapTab = 'resources'"
                id="tab-cap-resources"
              >
                资源 ({{ overview?.resources?.length || 2 }})
              </button>
              <button
                type="button"
                class="caps-tab-btn"
                :class="{ active: activeCapTab === 'prompts' }"
                @click="activeCapTab = 'prompts'"
                id="tab-cap-prompts"
              >
                提示词 ({{ overview?.prompts?.length || 2 }})
              </button>
            </div>
          </div>

          <!-- Cap List: Tools -->
          <div v-show="activeCapTab === 'tools'" class="caps-scroll-area">
            <div
              v-for="tool in overview?.tools"
              :key="tool.name"
              class="cap-item-card"
              @click="applyPreset(
                tool.name === 'moderation_inspect_content' ? 'moderation' :
                tool.name === 'cinema_search_dramas' ? 'search' :
                tool.name === 'cinema_get_episode_transcript' ? 'transcript' : 'graph'
              )"
            >
              <div class="cap-card-header">
                <span class="cap-name">
                  <el-icon class="cap-prefix-icon"><Cpu /></el-icon>
                  {{ tool.name }}
                </span>
                <button type="button" class="insert-param-btn">载入调试</button>
              </div>
              <p class="cap-desc">{{ tool.description }}</p>
              <div class="cap-params-preview">
                <span class="param-label">入参属性:</span>
                <span
                  v-for="(prop, pName) in tool.parameters?.properties"
                  :key="pName"
                  class="prop-pill"
                >
                  {{ pName }} ({{ prop.type }})
                </span>
              </div>
            </div>
          </div>

          <!-- Cap List: Resources -->
          <div v-show="activeCapTab === 'resources'" class="caps-scroll-area">
            <div
              v-for="res in overview?.resources"
              :key="res.uri"
              class="cap-item-card"
              @click="applyPreset(res.uri.includes('trending') ? 'res_trending' : 'res_ontology')"
            >
              <div class="cap-card-header">
                <span class="cap-name">
                  <el-icon class="cap-prefix-icon"><FolderOpened /></el-icon>
                  {{ res.name }}
                </span>
                <button type="button" class="insert-param-btn">载入读取</button>
              </div>
              <p class="cap-desc">{{ res.description }}</p>
              <div class="cap-uri-badge">
                <code>{{ res.uri }}</code>
              </div>
            </div>
          </div>

          <!-- Cap List: Prompts -->
          <div v-show="activeCapTab === 'prompts'" class="caps-scroll-area">
            <div
              v-for="prompt in overview?.prompts"
              :key="prompt.name"
              class="cap-item-card"
              @click="applyPreset(prompt.name.includes('twist') ? 'prompt_twist' : 'moderation')"
            >
              <div class="cap-card-header">
                <span class="cap-name">
                  <el-icon class="cap-prefix-icon"><Document /></el-icon>
                  {{ prompt.name }}
                </span>
                <button type="button" class="insert-param-btn">载入模板</button>
              </div>
              <p class="cap-desc">{{ prompt.description }}</p>
              <div class="cap-params-preview">
                <span class="param-label">占位参数:</span>
                <span
                  v-for="arg in prompt.arguments"
                  :key="arg.name"
                  class="prop-pill"
                >
                  {{ arg.name }} {{ arg.required ? '(必需)' : '' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Interactive Studio & Sandbox -->
      <div class="mcp-right-column">
        <div class="mcp-bento-card studio-card">
          <div class="bento-header">
            <div class="bento-title-group">
              <el-icon class="bento-icon"><CaretRight /></el-icon>
              <h2 class="bento-title">MCP 在线沙盒调试器 (JSON-RPC 2.0 Studio)</h2>
            </div>
            <div class="studio-presets">
              <span class="preset-label">快速范例:</span>
              <button type="button" class="preset-tag-btn" @click="applyPreset('moderation')">风控安全</button>
              <button type="button" class="preset-tag-btn" @click="applyPreset('search')">短剧检索</button>
              <button type="button" class="preset-tag-btn" @click="applyPreset('transcript')">台词切片</button>
              <button type="button" class="preset-tag-btn" @click="applyPreset('graph')">图谱关系</button>
            </div>
          </div>

          <!-- Form Controls -->
          <div class="studio-form-row">
            <div class="form-group method-group">
              <label class="form-label">RPC Method</label>
              <select v-model="sandboxForm.method" class="native-select" id="select-mcp-method">
                <option value="tools/call">tools/call (调用工具)</option>
                <option value="resources/read">resources/read (读取只读资源)</option>
                <option value="prompts/get">prompts/get (获取提示词模板)</option>
              </select>
            </div>

            <div class="form-group target-group">
              <label class="form-label">Target Name / URI</label>
              <input
                v-model="sandboxForm.target"
                type="text"
                class="native-input"
                placeholder="例如: moderation_inspect_content"
                id="input-mcp-target"
              />
            </div>
          </div>

          <!-- Params JSON Editor -->
          <div class="studio-editor-section">
            <div class="editor-header">
              <label class="form-label">Arguments JSON (参数对象)</label>
              <span class="editor-hint">标准 JSON 格式键值对</span>
            </div>
            <textarea
              v-model="sandboxForm.paramsJson"
              class="native-code-editor"
              rows="5"
              placeholder="{}"
              id="textarea-mcp-params"
            ></textarea>
          </div>

          <!-- Action Button Strip -->
          <div class="studio-actions-row">
            <button
              type="button"
              class="action-btn primary execute-btn"
              :disabled="sandboxLoading"
              @click="executeSandboxCall"
              id="btn-execute-mcp-sandbox"
            >
              <el-icon v-if="!sandboxLoading"><CaretRight /></el-icon>
              <el-icon v-else class="is-spinning"><Refresh /></el-icon>
              <span>{{ sandboxLoading ? '正在执行 RPC...' : '执行 MCP 调用' }}</span>
            </button>
          </div>

          <!-- Payloads Inspector -->
          <div class="payload-inspectors-grid">
            <!-- Request Frame -->
            <div class="frame-col">
              <div class="frame-header">
                <span class="frame-title">RPC Request Body</span>
                <span class="frame-badge">客户端发往端点</span>
              </div>
              <pre class="code-viewport"><code>{{ JSON.stringify(requestPayloadPreview, null, 2) }}</code></pre>
            </div>

            <!-- Response Frame -->
            <div class="frame-col">
              <div class="frame-header">
                <div class="header-left-meta">
                  <span class="frame-title">RPC Response Output</span>
                  <span v-if="executionLatencyMs !== null" class="latency-badge">{{ executionLatencyMs }}ms</span>
                </div>
                <button
                  v-if="responseOutput"
                  type="button"
                  class="mini-copy-btn"
                  @click="copyOutput"
                  id="btn-copy-mcp-output"
                >
                  复制报文
                </button>
              </div>
              <pre class="code-viewport response-viewport" id="viewport-mcp-response"><code>{{ responseOutput ? JSON.stringify(responseOutput, null, 2) : '等待执行沙盒测试...' }}</code></pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dialog for Adding Remote Node -->
    <div v-if="showAddNodeDialog" class="modal-backdrop" @click.self="showAddNodeDialog = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3 class="modal-title">登记外部 MCP 拓扑节点</h3>
          <button type="button" class="close-btn" @click="showAddNodeDialog = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">节点标识名称</label>
            <input v-model="newNodeForm.name" type="text" class="native-input" placeholder="例如: external_director_worker" />
          </div>
          <div class="form-group">
            <label class="form-label">端点服务地址 (URL)</label>
            <input v-model="newNodeForm.url" type="text" class="native-input" placeholder="http://127.0.0.1:8001/api/v1/mcp" />
          </div>
          <div class="form-group">
            <label class="form-label">传输协议类型</label>
            <select v-model="newNodeForm.type" class="native-select">
              <option value="REMOTE_STREAMABLE">REMOTE_STREAMABLE (标准流式 HTTP)</option>
              <option value="STANDALONE_SSE">STANDALONE_SSE (Server-Sent Events)</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="action-btn secondary" @click="showAddNodeDialog = false">取消</button>
          <button type="button" class="action-btn primary" @click="handleAddNode">确认注册</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Main Container */
.mcp-center-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  padding: 8px 4px;
  box-sizing: border-box;
  color: var(--text-primary, #ffffff);
}

/* Header Card */
.mcp-header-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-surface, rgba(28, 28, 30, 0.65));
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.1));
  border-radius: 16px;
  padding: 24px 28px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}

.mcp-header-left {
  display: flex;
  align-items: center;
  gap: 18px;
}

.header-icon-squircle {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(0, 113, 227, 0.2), rgba(0, 199, 190, 0.2));
  border: 1px solid rgba(0, 113, 227, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2997ff;
}

.header-titles {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--text-primary, #ffffff);
}

.mcp-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: rgba(52, 199, 89, 0.15);
  border: 1px solid rgba(52, 199, 89, 0.35);
  color: #30d158;
}

.pulsing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #30d158;
  box-shadow: 0 0 8px #30d158;
}

.mcp-protocol-pill {
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
  background: rgba(0, 113, 227, 0.12);
  border: 1px solid rgba(0, 113, 227, 0.25);
  color: #2997ff;
}

.sub-title {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.65));
}

/* Stat Strip */
.mcp-stat-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: var(--bg-surface, rgba(28, 28, 30, 0.65));
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.08));
  border-radius: 14px;
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  overflow: hidden;
}

.stat-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tool-icon {
  background: rgba(41, 151, 255, 0.15);
  border: 1px solid rgba(41, 151, 255, 0.3);
  color: #2997ff;
}

.resource-icon {
  background: rgba(255, 159, 10, 0.15);
  border: 1px solid rgba(255, 159, 10, 0.3);
  color: #ff9f0a;
}

.prompt-icon {
  background: rgba(175, 82, 222, 0.15);
  border: 1px solid rgba(175, 82, 222, 0.3);
  color: #bf5af2;
}

.node-icon {
  background: rgba(50, 215, 75, 0.15);
  border: 1px solid rgba(50, 215, 75, 0.3);
  color: #32d74b;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.6));
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary, #ffffff);
}

.stat-tag {
  position: absolute;
  top: 12px;
  right: 14px;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-muted, rgba(255, 255, 255, 0.45));
}

/* Main Workspace Grid */
.mcp-workspace-grid {
  display: grid;
  grid-template-columns: 460px 1fr;
  gap: 20px;
  align-items: start;
}

.mcp-left-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.mcp-right-column {
  display: flex;
  flex-direction: column;
}

/* Bento Card Common */
.mcp-bento-card {
  background: var(--bg-surface, rgba(28, 28, 30, 0.65));
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.08));
  border-radius: 16px;
  padding: 20px 22px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.bento-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--border-line, rgba(255, 255, 255, 0.06));
  padding-bottom: 12px;
}

.bento-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bento-icon {
  font-size: 16px;
  color: #2997ff;
}

.bento-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #ffffff);
}

/* Topology Node Cards */
.node-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.node-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.06));
  border-radius: 10px;
  padding: 12px 14px;
}

.node-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pulse-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #30d158;
  box-shadow: 0 0 6px #30d158;
}

.node-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.node-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #ffffff);
}

.node-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(0, 113, 227, 0.15);
  color: #2997ff;
}

.node-url {
  font-size: 11px;
  font-family: monospace;
  color: var(--text-muted, rgba(255, 255, 255, 0.5));
}

.node-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ping-badge {
  font-size: 11px;
  font-family: monospace;
  color: var(--text-secondary, rgba(255, 255, 255, 0.7));
}

.state-badge.online {
  font-size: 11px;
  color: #30d158;
  font-weight: 500;
}

/* Capabilities Hub */
.caps-subnav {
  display: flex;
  gap: 6px;
  background: rgba(255, 255, 255, 0.04);
  padding: 3px;
  border-radius: 8px;
}

.caps-tab-btn {
  background: transparent;
  border: none;
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 6px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.6));
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
}

.caps-tab-btn.active {
  background: var(--bg-hover, rgba(255, 255, 255, 0.12));
  color: var(--text-primary, #ffffff);
  font-weight: 600;
}

.caps-scroll-area {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 480px;
  overflow-y: auto;
  padding-right: 4px;
}

.cap-item-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.06));
  border-radius: 10px;
  padding: 12px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cap-item-card:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(41, 151, 255, 0.4);
  transform: translateY(-1px);
}

.cap-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.cap-name {
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: monospace;
  color: #2997ff;
}

.cap-prefix-icon {
  font-size: 14px;
}

.insert-param-btn {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.1));
  border-radius: 6px;
  padding: 2px 8px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.7));
  cursor: pointer;
  user-select: none;
}

.insert-param-btn:hover {
  background: #0071e3;
  color: #ffffff;
  border-color: #0071e3;
}

.cap-desc {
  margin: 0 0 8px 0;
  font-size: 12px;
  line-height: 1.4;
  color: var(--text-secondary, rgba(255, 255, 255, 0.65));
}

.cap-params-preview {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.param-label {
  font-size: 11px;
  color: var(--text-muted, rgba(255, 255, 255, 0.45));
}

.prop-pill {
  font-size: 10px;
  font-family: monospace;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  padding: 1px 6px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.75));
}

.cap-uri-badge code {
  font-size: 11px;
  color: #ff9f0a;
  background: rgba(255, 159, 10, 0.08);
  padding: 2px 8px;
  border-radius: 4px;
}

/* Studio & Interactive Sandbox */
.studio-presets {
  display: flex;
  align-items: center;
  gap: 6px;
}

.preset-label {
  font-size: 11px;
  color: var(--text-muted, rgba(255, 255, 255, 0.5));
}

.preset-tag-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.08));
  border-radius: 6px;
  padding: 3px 8px;
  font-size: 11px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.75));
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
}

.preset-tag-btn:hover {
  background: rgba(41, 151, 255, 0.15);
  border-color: rgba(41, 151, 255, 0.35);
  color: #2997ff;
}

.studio-form-row {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 14px;
  margin-bottom: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary, rgba(255, 255, 255, 0.7));
}

.native-select,
.native-input {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.1));
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-primary, #ffffff);
  outline: none;
  transition: border-color 0.2s ease;
}

.native-select:focus,
.native-input:focus,
.native-code-editor:focus {
  border-color: #0071e3;
}

.native-select option {
  background: #1c1c1e;
  color: #ffffff;
}

.studio-editor-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.editor-hint {
  font-size: 11px;
  color: var(--text-muted, rgba(255, 255, 255, 0.45));
}

.native-code-editor {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.08));
  border-radius: 10px;
  padding: 12px;
  font-size: 12px;
  font-family: 'SF Mono', Menlo, Consolas, Monaco, monospace;
  line-height: 1.5;
  color: #30d158;
  outline: none;
  resize: vertical;
}

.studio-actions-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.execute-btn {
  padding: 10px 24px;
  font-size: 13px;
  font-weight: 600;
}

/* Payloads Frame Grid */
.payload-inspectors-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.frame-col {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.06));
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.frame-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid var(--border-line, rgba(255, 255, 255, 0.06));
}

.header-left-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.frame-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary, rgba(255, 255, 255, 0.75));
}

.frame-badge {
  font-size: 10px;
  color: var(--text-muted, rgba(255, 255, 255, 0.45));
}

.latency-badge {
  font-size: 11px;
  font-family: monospace;
  color: #30d158;
  background: rgba(48, 209, 88, 0.12);
  border-radius: 4px;
  padding: 1px 6px;
}

.mini-copy-btn {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.1));
  border-radius: 4px;
  padding: 2px 8px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.75));
  cursor: pointer;
  user-select: none;
}

.mini-copy-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.code-viewport {
  margin: 0;
  padding: 14px;
  font-size: 12px;
  font-family: 'SF Mono', Menlo, Consolas, Monaco, monospace;
  line-height: 1.5;
  color: var(--text-secondary, rgba(255, 255, 255, 0.8));
  max-height: 280px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.response-viewport {
  color: #64d2ff;
}

/* Button & Common Styles */
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
  border: none;
}

.action-btn.primary {
  background: #0071e3;
  color: #ffffff;
}

.action-btn.primary:hover:not(:disabled) {
  background: #0077ed;
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.1));
  color: var(--text-primary, #ffffff);
}

.action-btn.secondary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mini-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.08));
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 11px;
  color: var(--text-primary, #ffffff);
  cursor: pointer;
  user-select: none;
}

.mini-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.is-spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Modal Backdrop */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-card {
  width: 440px;
  background: var(--bg-surface, #1c1c1e);
  border: 1px solid var(--border-line, rgba(255, 255, 255, 0.12));
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-line, rgba(255, 255, 255, 0.08));
}

.modal-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 20px;
  color: var(--text-muted, rgba(255, 255, 255, 0.5));
  cursor: pointer;
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--border-line, rgba(255, 255, 255, 0.08));
  background: rgba(0, 0, 0, 0.15);
}

/* Light Theme Adaptations */
.theme-light {
  color: #1d1d1f;
}

.theme-light .mcp-header-card,
.theme-light .stat-card,
.theme-light .mcp-bento-card,
.theme-light .modal-card {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.08);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

.theme-light .main-title,
.theme-light .bento-title,
.theme-light .stat-value,
.theme-light .node-name {
  color: #1d1d1f;
}

.theme-light .sub-title,
.theme-light .stat-label,
.theme-light .cap-desc,
.theme-light .form-label {
  color: #6e6e73;
}

.theme-light .node-card,
.theme-light .cap-item-card {
  background: #f5f5f7;
  border-color: rgba(0, 0, 0, 0.05);
}

.theme-light .native-select,
.theme-light .native-input {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.12);
  color: #1d1d1f;
}

.theme-light .native-select option {
  background: #ffffff;
  color: #1d1d1f;
}

.theme-light .native-code-editor {
  background: #fbfbfd;
  border-color: rgba(0, 0, 0, 0.1);
  color: #007700;
}

.theme-light .frame-col {
  background: #f5f5f7;
  border-color: rgba(0, 0, 0, 0.06);
}

.theme-light .frame-header {
  background: #ebebee;
  border-bottom-color: rgba(0, 0, 0, 0.06);
}

.theme-light .code-viewport {
  color: #1d1d1f;
}

.theme-light .response-viewport {
  color: #0055aa;
}

.theme-light .action-btn.secondary,
.theme-light .mini-btn,
.theme-light .insert-param-btn,
.theme-light .preset-tag-btn {
  background: #e5e5ea;
  border-color: rgba(0, 0, 0, 0.08);
  color: #1d1d1f;
}

.theme-light .caps-subnav {
  background: #e5e5ea;
}

.theme-light .caps-tab-btn {
  color: #6e6e73;
}

.theme-light .caps-tab-btn.active {
  background: #ffffff;
  color: #1d1d1f;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
</style>
