<template>
  <el-dialog
    v-model="dialogVisible"
    title="Skills 自进化技能提案审核中台 (HITL 人机回环)"
    width="800px"
    class="evolution-hitl-dialog"
    destroy-on-close
    :append-to-body="true"
    @open="loadProposals"
  >
    <div class="evolution-modal-container">
      <div class="evo-header-hint">
        <span>由 Critic 质检智能体对高难度圆桌演练轨迹进行蒸馏生成的备选技能 SOP。管理员在此审核、对比 Diff 并一键热加载入库。</span>
      </div>

      <div v-if="loading" class="evo-loading">正在拉取自进化提案列表...</div>
      <div v-else-if="proposals.length === 0" class="evo-empty">
        <p>当前暂无待审核的自进化提案。</p>
        <button class="btn-sample-distill" @click="triggerSampleDistill">演示: 生成一条高分自进化提案</button>
      </div>

      <div v-else class="evo-proposals-list">
        <div
          v-for="p in proposals"
          :key="p.id"
          class="evo-proposal-card"
          :class="'status-' + p.status.toLowerCase()"
          :id="'proposal-card-' + p.id"
        >
          <div class="prop-card-head">
            <div>
              <span class="prop-badge">{{ p.target_agent_id }}</span>
              <h4 class="prop-title">{{ p.title }}</h4>
            </div>
            <div class="prop-score-box">
              <span class="score-num">{{ p.critic_score }}分</span>
              <span class="score-tag">Critic 质检评分</span>
            </div>
          </div>

          <p class="prop-verdict">{{ p.critic_verdict }}</p>

          <!-- Markdown 预览区 -->
          <div class="prop-code-preview">
            <pre>{{ p.skill_content }}</pre>
          </div>

          <div class="prop-card-foot">
            <span class="prop-status-tag">{{ p.status === 'APPROVED' ? '已热加载上线' : '待人工复核' }}</span>
            <div class="prop-actions">
              <button
                v-if="p.status === 'PENDING'"
                class="btn-approve-hotload"
                :id="'btn-approve-skill-' + p.id"
                @click="approveProposal(p.id)"
              >
                一键批准并动态热加载上线
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits(['update:modelValue'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const loading = ref(false)
const proposals = ref<any[]>([])

async function loadProposals() {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/agent-mesh/evolution/proposals')
    proposals.value = res.data?.data || []
  } catch (e) {
    console.warn('Failed to load proposals:', e)
  } finally {
    loading.value = false
  }
}

async function triggerSampleDistill() {
  try {
    const res = await axios.post('/api/v1/agent-mesh/evolution/distill-sample')
    ElMessage.success('已自动蒸馏生成一条高难分镜创作新技能提案！')
    await loadProposals()
  } catch (e) {
    ElMessage.error('生成演示提案失败')
  }
}

async function approveProposal(id: string) {
  try {
    const res = await axios.post(`/api/v1/agent-mesh/evolution/proposals/${id}/approve`)
    ElMessage.success(res.data?.message || '技能已成功动态热加载！')
    await loadProposals()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '批准失败')
  }
}
</script>

<style scoped>
.evolution-modal-container {
  max-height: 600px;
  overflow-y: auto;
  color: var(--agent-text-title, #1d1d1f);
}

.evo-header-hint {
  padding: 10px 14px;
  border-radius: 8px;
  background: var(--agent-bg-canvas, #f5f5f7);
  font-size: 12px;
  color: var(--agent-text-secondary, #515154);
  margin-bottom: 14px;
}

.evo-empty {
  text-align: center;
  padding: 40px 0;
  font-size: 13px;
  color: var(--agent-text-muted, #6e6e73);
}

.btn-sample-distill {
  margin-top: 10px;
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  background: var(--agent-accent-blue, #0071e3);
  color: #ffffff;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
}

.evo-proposals-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.evo-proposal-card {
  padding: 16px;
  border-radius: 12px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.prop-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 8px;
}

.prop-badge {
  font-size: 10.5px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--agent-accent-blue-soft, rgba(0, 113, 227, 0.1));
  color: var(--agent-accent-blue, #0071e3);
}

.prop-title {
  margin: 4px 0 0;
  font-size: 15px;
  font-weight: 700;
}

.prop-score-box {
  text-align: right;
}

.score-num {
  display: block;
  font-size: 18px;
  font-weight: 800;
  color: #34c759;
}

.score-tag {
  font-size: 10px;
  color: var(--agent-text-muted, #8e8e93);
}

.prop-verdict {
  font-size: 12px;
  color: var(--agent-text-secondary, #515154);
  margin: 0 0 10px;
}

.prop-code-preview {
  max-height: 140px;
  overflow-y: auto;
  padding: 10px;
  border-radius: 8px;
  background: var(--agent-bg-canvas, #f5f5f7);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.06));
  font-family: monospace;
  font-size: 11px;
  line-height: 1.45;
}

.prop-card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.06));
}

.prop-status-tag {
  font-size: 11px;
  font-weight: 600;
  color: var(--agent-text-secondary, #515154);
}

.btn-approve-hotload {
  padding: 6px 14px;
  border-radius: 6px;
  border: none;
  background: #34c759;
  color: #ffffff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
</style>

<style>
/* Evolution HITL Dialog Global Styles for Light & Dark */
.evolution-hitl-dialog {
  border-radius: 18px !important;
  overflow: hidden !important;
  background: var(--agent-card-surface, #ffffff) !important;
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08)) !important;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.15) !important;
}

[data-theme="light"] .evolution-hitl-dialog {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  color: #18191C !important;
}

[data-theme="light"] .evolution-hitl-dialog .el-dialog__header {
  background: #f8f9fa !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
  margin: 0 !important;
  padding: 16px 20px !important;
}

[data-theme="light"] .evolution-hitl-dialog .el-dialog__title {
  color: #18191C !important;
  font-weight: 700 !important;
}

[data-theme="light"] .evolution-hitl-dialog .el-dialog__body {
  padding: 16px 20px !important;
  background: #ffffff !important;
  color: #18191C !important;
}

[data-theme="dark"] .evolution-hitl-dialog {
  background: #161B22 !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #F5F5F7 !important;
}

[data-theme="dark"] .evolution-hitl-dialog .el-dialog__header {
  background: #0D1117 !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
  margin: 0 !important;
  padding: 16px 20px !important;
}

[data-theme="dark"] .evolution-hitl-dialog .el-dialog__title {
  color: #F5F5F7 !important;
  font-weight: 700 !important;
}

[data-theme="dark"] .evolution-hitl-dialog .el-dialog__body {
  padding: 16px 20px !important;
  background: #161B22 !important;
  color: #F5F5F7 !important;
}
</style>
