<template>
  <div class="agent-command-center" id="agent-command-center-root">
    <!-- Top Sub-Navigation Bar -->
    <div class="acc-header-bar">
      <div class="acc-title-group">
        <div class="acc-eyebrow">NINE-AGENT FLEET & TACTICAL COMMAND</div>
        <h2 class="acc-main-title">九大领域专家智能体总控台、Skills 挂载器与战术大屏</h2>
      </div>

      <div class="acc-subtab-pills" id="acc-subtab-bar">
        <button
          v-for="tab in subTabs"
          :key="tab.key"
          type="button"
          class="acc-subtab-btn"
          :class="{ active: activeSubTab === tab.key }"
          :id="'acc-tab-' + tab.key"
          @click="switchSubTab(tab.key)"
        >
          <span>{{ tab.label }}</span>
          <span v-if="tab.badge" class="acc-tab-badge">{{ tab.badge }}</span>
        </button>
      </div>
    </div>

    <!-- ================= 1. TACTICAL BIG SCREEN (agent-display-5.0) ================= -->
    <section v-if="activeSubTab === 'tactical'" class="acc-section" id="acc-panel-tactical">
      <div class="tactical-toolbar">
        <div class="tactical-toolbar-left">
          <span class="toolbar-label">战术大屏主题切换 (原封不动集成 agent-display-5.0)：</span>
          <div class="theme-pill-group">
            <button
              v-for="th in tacticalThemes"
              :key="th.id"
              type="button"
              class="theme-select-btn"
              :class="{ active: currentTacticalTheme === th.id }"
              :id="'btn-tactical-theme-' + th.id"
              @click="selectTacticalTheme(th.id)"
            >
              {{ th.label }}
            </button>
          </div>
        </div>
        <div class="tactical-toolbar-right">
          <button type="button" class="acc-action-btn secondary" id="btn-refresh-tactical-telemetry" @click="refreshAllData">
            同步实时遥测
          </button>
          <a
            :href="'/agent-display-5.0/index.html#' + currentTacticalTheme"
            target="_blank"
            class="acc-action-btn primary"
            id="btn-open-tactical-fullscreen"
          >
            独立全屏打开战术大屏
          </a>
        </div>
      </div>

      <div class="tactical-iframe-container">
        <iframe
          ref="tacticalIframeRef"
          :src="'/agent-display-5.0/index.html#' + currentTacticalTheme"
          class="tactical-iframe"
          id="tactical-display-iframe"
          title="CinemaAgent Tactical Big Screen"
        ></iframe>
      </div>
    </section>

    <!-- ================= 2. AGENT BI DATA VISUALIZATION DASHBOARD ================= -->
    <section v-show="activeSubTab === 'bi'" class="acc-section" id="acc-panel-bi">
      <!-- KPI Summary Row -->
      <div class="acc-kpi-grid">
        <div class="acc-kpi-card">
          <div class="kpi-label">在线热插拔智能体</div>
          <div class="kpi-value">{{ telemetry.summary?.enabled_agents || 9 }} / {{ telemetry.summary?.total_agents || 9 }}</div>
          <div class="kpi-foot">支持毫秒级独立开关与温和兜底</div>
        </div>
        <div class="acc-kpi-card">
          <div class="kpi-label">累计智能体调度 / Token</div>
          <div class="kpi-value">{{ telemetry.summary?.total_calls || 0 }} 次</div>
          <div class="kpi-foot">累计消耗 {{ telemetry.summary?.total_tokens || 0 }} Tokens</div>
        </div>
        <div class="acc-kpi-card">
          <div class="kpi-label">平均响应延迟 / 降级保护率</div>
          <div class="kpi-value">{{ telemetry.summary?.avg_latency_ms || 0 }} ms</div>
          <div class="kpi-foot">断路器与静态兜底率 {{ telemetry.summary?.fallback_rate_pct || 0 }}%</div>
        </div>
        <div class="acc-kpi-card">
          <div class="kpi-label">已挂载 Skills / 黑板会话</div>
          <div class="kpi-value">{{ telemetry.summary?.total_skills || 6 }} 项技能</div>
          <div class="kpi-foot">活跃黑板会话 {{ telemetry.summary?.active_blackboard_sessions || 1 }} 个</div>
        </div>
      </div>

      <!-- ECharts 2x2 Grid -->
      <div class="acc-charts-grid">
        <div class="acc-chart-box">
          <div class="chart-box-header">
            <h3>1~9 号智能体调用频次与平均耗时 (Callback 实时探头)</h3>
          </div>
          <div ref="chartAgentCallsRef" class="acc-echart-canvas" id="echart-agent-calls"></div>
        </div>

        <div class="acc-chart-box">
          <div class="chart-box-header">
            <h3>三大职能分类 Token 消耗占比 & Skills 命中排行</h3>
          </div>
          <div ref="chartCategorySkillsRef" class="acc-echart-canvas" id="echart-category-skills"></div>
        </div>
      </div>

      <!-- Recent Callback Traces Table -->
      <div class="acc-card-block">
        <div class="card-block-header flex items-center justify-between flex-wrap gap-12">
          <div>
            <h3>AgentTelemetryCallbackHandler 实时调用链路追踪日志</h3>
            <p class="section-desc">捕获全平台真实智能体调用、Token 消耗、延迟、思考命中 Skills 及问答摘要。</p>
          </div>
          <div class="filter-controls-row flex items-center gap-8">
            <select v-model="selectedTraceAgent" class="acc-input filter-select" id="select-trace-agent-filter" @change="fetchTelemetry(1)">
              <option value="ALL">全部响应智能体 (1~9号)</option>
              <option value="agent_1">1号 · 剧情答疑</option>
              <option value="agent_2">2号 · 观影灵宠</option>
              <option value="agent_3">3号 · 知识检索</option>
              <option value="agent_4">4号 · 内容合规</option>
              <option value="agent_5">5号 · 编剧创意</option>
              <option value="agent_6">6号 · 视听场记</option>
              <option value="agent_7">7号 · 个性推荐</option>
              <option value="agent_8">8号 · 导演分镜</option>
              <option value="agent_9">9号 · 主控议长</option>
            </select>
            <select v-model="selectedTraceStatus" class="acc-input filter-select" id="select-trace-status-filter" @change="fetchTelemetry(1)">
              <option value="ALL">全部执行状态</option>
              <option value="SUCCESS">成功 (SUCCESS)</option>
              <option value="INTERCEPTED">拦截 (INTERCEPTED)</option>
              <option value="FALLBACK">降级 (FALLBACK)</option>
              <option value="FAILED">失败 (FAILED)</option>
            </select>
            <button type="button" class="acc-action-btn secondary" id="btn-refresh-traces" @click="fetchTelemetry(1)">刷新流水</button>
          </div>
        </div>
        <div class="acc-table-wrap scrollable-traces-box" style="max-height: 480px; overflow-y: auto; overflow-x: auto; border: 1px solid var(--agent-card-border, rgba(0,0,0,0.08)); border-radius: 8px;">
          <table class="acc-data-table" id="table-agent-telemetry-traces">
            <thead>
              <tr style="position: sticky; top: 0; background: var(--agent-card-bg, #ffffff); z-index: 2;">
                <th>Trace ID</th>
                <th>响应智能体</th>
                <th>模型治理策略 & 实际引擎</th>
                <th>思考期命中 Skills</th>
                <th>耗时</th>
                <th>Tokens</th>
                <th>状态</th>
                <th>提问与响应摘要</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tr in telemetry.recent_traces" :key="tr.trace_id">
                <td class="mono-cell">{{ tr.trace_id }}</td>
                <td class="strong-cell">{{ tr.agent_name }}</td>
                <td>
                  <span class="mode-pill" :class="tr.bind_mode.toLowerCase()">{{ formatBindMode(tr.bind_mode) }}</span>
                  <span class="mono-cell ml-4">{{ tr.resolved_model }}</span>
                </td>
                <td>
                  <span v-for="sk in tr.matched_skills" :key="sk" class="skill-chip">{{ sk }}</span>
                  <span v-if="!tr.matched_skills || !tr.matched_skills.length" class="muted-txt">默认底座</span>
                </td>
                <td class="mono-cell">{{ tr.latency_ms }} ms</td>
                <td class="mono-cell">{{ tr.total_tokens }}</td>
                <td>
                  <span class="status-pill" :class="tr.status === 'SUCCESS' ? 'ok' : 'warn'">{{ tr.status }}</span>
                </td>
                <td class="preview-cell" :title="tr.response_preview">
                  <div class="line-clamp-1"><strong>问：</strong>{{ tr.query_preview }}</div>
                  <div class="muted-txt line-clamp-1"><strong>答：</strong>{{ tr.response_preview }}</div>
                </td>
              </tr>
              <tr v-if="!telemetry.recent_traces || !telemetry.recent_traces.length">
                <td colspan="8" style="text-align: center; padding: 28px; color: var(--agent-text-muted);">
                  当前筛选条件下暂无调用链路追踪日志
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- 分页器 -->
        <div class="table-pagination-footer flex items-center justify-between mt-12" style="padding: 10px 12px; border-top: 1px solid var(--agent-card-border, rgba(0,0,0,0.06));" v-if="telemetry.traces_total > 0">
          <span style="font-size: 13px; color: var(--agent-text-muted);">共 {{ telemetry.traces_total }} 条调用链路流水</span>
          <el-pagination
            background
            layout="prev, pager, next"
            :current-page="telemetry.traces_page"
            :page-size="telemetry.traces_page_size"
            :total="telemetry.traces_total"
            @current-change="fetchTelemetry"
          />
        </div>
      </div>
    </section>

    <!-- ================= 3. THREE-TIER LLM GOVERNANCE & 9 AGENTS DECOUPLED MATRIX ================= -->
    <section v-if="activeSubTab === 'models'" class="acc-section" id="acc-panel-models">
      <!-- 顶部治理全局模式切换卡片 -->
      <div class="acc-card-block mb-16">
        <div class="card-block-header">
          <div>
            <h3>智能体大模型解耦治理中枢（9大智能体独立定制 / 勾选批量配置 / 全员一键切换）</h3>
            <p class="section-desc">
              彻底解耦！每个智能体均可独立配置模型底座与超参数；亦可勾选多个智能体，在下方批量控制台统一应用参数并写入生效。
            </p>
          </div>
          <div class="btn-row">
            <button
              type="button"
              class="acc-action-btn primary"
              id="btn-switch-all-unified"
              @click="handleBatchSwitchMode('GLOBAL_UNIFIED')"
            >
              一键全员切换：全局统一模型 (GLOBAL_UNIFIED)
            </button>
            <button
              type="button"
              class="acc-action-btn secondary"
              id="btn-switch-all-category"
              @click="handleBatchSwitchMode('CATEGORY_GROUP')"
            >
              一键全员切换：三大分类治理 (CATEGORY_GROUP)
            </button>
          </div>
        </div>

        <!-- 批量勾选配置工具栏 -->
        <div class="batch-agent-toolbar" id="batch-agent-toolbar">
          <div class="batch-toolbar-header">
            <div class="batch-select-status">
              <button
                type="button"
                class="acc-action-btn secondary small"
                id="btn-toggle-select-all-agents"
                @click="toggleSelectAllAgents"
              >
                {{ isAllAgentsSelected ? '取消全选' : '全选 9 个智能体' }}
              </button>
              <span class="selected-badge ml-8">
                已勾选 {{ selectedAgentIds.length }} / {{ overview.agents?.length || 9 }} 个智能体
              </span>
            </div>
            <span class="batch-tip">勾选下方智能体卡片右上角复选框，可在此一键批量覆盖模型与温度参数</span>
          </div>

          <div class="batch-inputs-grid mt-10">
            <div class="form-item">
              <label>批量 Provider</label>
              <select v-model="batchConfigForm.provider" class="acc-input" id="select-batch-provider">
                <option value="mimo">mimo (小米 MiMo)</option>
                <option value="ollama">ollama (本地推理)</option>
                <option value="deepseek">deepseek (DeepSeek 官方)</option>
                <option value="openai">openai (OpenAI 兼容)</option>
              </select>
            </div>
            <div class="form-item">
              <label>批量 Model Name</label>
              <input v-model="batchConfigForm.model_name" type="text" class="acc-input" id="input-batch-model-name" placeholder="如 mimo-v2.6-flash" />
            </div>
            <div class="form-item">
              <label>批量 Base URL</label>
              <input v-model="batchConfigForm.base_url" type="text" class="acc-input" id="input-batch-base-url" placeholder="如 https://api.xiaomimimo.com/v1" />
            </div>
            <div class="form-item">
              <label>批量温度 ({{ batchConfigForm.temperature }})</label>
              <input v-model.number="batchConfigForm.temperature" type="number" step="0.05" min="0" max="1.5" class="acc-input" id="input-batch-temperature" />
            </div>
            <div class="form-item flex-end">
              <button
                type="button"
                class="acc-action-btn primary full-width"
                id="btn-apply-batch-agent-config"
                :disabled="selectedAgentIds.length === 0"
                @click="applyBatchAgentConfig"
              >
                批量应用并保存所选 ({{ selectedAgentIds.length }})
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 9 大智能体独立解耦卡片矩阵 -->
      <div class="acc-card-block mb-16">
        <div class="card-block-header">
          <div>
            <h3>9 大领域专家智能体独立配置矩阵 (单体解耦)</h3>
            <p class="section-desc">每个智能体均可单独指定供应商、模型、温度与专属端点，互不干扰。</p>
          </div>
        </div>

        <div class="agent-custom-cards-grid">
          <div
            v-for="ag in overview.agents"
            :key="ag.agent_id"
            class="agent-single-config-card"
            :class="{ 'is-selected': selectedAgentIds.includes(ag.agent_id) }"
            :id="'agent-card-' + ag.agent_id"
          >
            <!-- 卡片顶栏: 勾选框与身份徽章 -->
            <div class="agent-card-top-strip">
              <div class="agent-badge-box">
                <span class="agent-id-pill">AGENT 0{{ ag.agent_number }}</span>
                <span class="agent-mode-tag" :class="ag.model_bind_mode?.toLowerCase()">
                  {{ ag.model_bind_mode || 'GLOBAL_UNIFIED' }}
                </span>
              </div>
              <label class="agent-checkbox-label">
                <input
                  type="checkbox"
                  :value="ag.agent_id"
                  v-model="selectedAgentIds"
                  :id="'chk-agent-' + ag.agent_id"
                />
                <span class="chk-text">批量勾选</span>
              </label>
            </div>

            <div class="agent-meta-header">
              <h4 class="agent-name-title">{{ ag.name }}</h4>
              <p class="agent-role-desc">{{ ag.role_title }}</p>
            </div>

            <!-- 独立模型表单 -->
            <div class="agent-form-rows">
              <div class="form-item">
                <label>绑定模式</label>
                <select v-model="ag.model_bind_mode" class="acc-input">
                  <option value="AGENT_CUSTOM">AGENT_CUSTOM (单体专属定制)</option>
                  <option value="GLOBAL_UNIFIED">GLOBAL_UNIFIED (全局继承)</option>
                  <option value="CATEGORY_GROUP">CATEGORY_GROUP (职能分类继承)</option>
                </select>
              </div>

              <div class="form-grid-2">
                <div class="form-item">
                  <label>供应商 (Provider)</label>
                  <select v-model="ag.provider" class="acc-input">
                    <option value="mimo">mimo (小米 MiMo)</option>
                    <option value="ollama">ollama (本地推理)</option>
                    <option value="deepseek">deepseek (DeepSeek 官方)</option>
                    <option value="openai">openai (OpenAI 兼容)</option>
                  </select>
                </div>
                <div class="form-item">
                  <label>模型名称 (Model)</label>
                  <input v-model="ag.model_name" type="text" class="acc-input" placeholder="如 mimo-v2.6-flash" />
                </div>
              </div>

              <div class="form-item">
                <label>接口地址 (Base URL)</label>
                <input v-model="ag.base_url" type="text" class="acc-input" placeholder="如 https://api.xiaomimimo.com/v1" />
              </div>

              <div class="form-grid-2">
                <div class="form-item">
                  <label>采样温度 ({{ ag.temperature }})</label>
                  <input v-model.number="ag.temperature" type="number" step="0.05" min="0" max="1.5" class="acc-input" />
                </div>
                <div class="form-item">
                  <label>超时时间 (秒)</label>
                  <input v-model.number="ag.timeout_sec" type="number" step="5" min="5" max="120" class="acc-input" />
                </div>
              </div>
            </div>

            <!-- 单卡底部操作栏 -->
            <div class="agent-card-actions mt-12">
              <button
                type="button"
                class="acc-action-btn primary flex-1"
                :id="'btn-save-agent-' + ag.agent_id"
                @click="saveSingleAgent(ag)"
              >
                保存此智能体配置
              </button>
              <button
                type="button"
                class="acc-action-btn secondary ml-8"
                :id="'btn-test-agent-' + ag.agent_id"
                @click="openAgentChat(ag)"
              >
                对话测试
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 下方三大职能分类参考折叠卡片 -->
      <div class="acc-card-block">
        <div class="card-block-header">
          <div>
            <h3>三大职能分类通用配置模板 (可选参考)</h3>
            <p class="section-desc">当智能体选择 CATEGORY_GROUP 模式时，将自动从以下分类规则中继承配置。</p>
          </div>
        </div>
        <div class="category-cards-grid">
          <div
            v-for="cat in overview.categories"
            :key="cat.category_key"
            class="category-config-card"
            :id="'category-card-' + cat.category_key"
          >
            <div class="cat-card-head">
              <span class="cat-key-badge">{{ cat.category_key }}</span>
              <h4>{{ cat.category_name }}</h4>
            </div>
            <p class="cat-desc">{{ cat.description }}</p>

            <div class="form-grid-2">
              <div class="form-item">
                <label>供应商 (Provider)</label>
                <select v-model="cat.provider" class="acc-input">
                  <option value="mimo">mimo (小米 MiMo)</option>
                  <option value="ollama">ollama (本地推理)</option>
                  <option value="deepseek">deepseek (DeepSeek 官方)</option>
                  <option value="openai">openai (OpenAI 兼容)</option>
                </select>
              </div>
              <div class="form-item">
                <label>模型名称 (Model Name)</label>
                <input v-model="cat.model_name" type="text" class="acc-input" placeholder="如 mimo-v2.6-flash" />
              </div>
              <div class="form-item">
                <label>接口地址 (Base URL)</label>
                <input v-model="cat.base_url" type="text" class="acc-input" placeholder="如 https://api.xiaomimimo.com/v1" />
              </div>
              <div class="form-item">
                <label>采样温度 ({{ cat.temperature }})</label>
                <input v-model.number="cat.temperature" type="number" step="0.05" min="0" max="1.5" class="acc-input" />
              </div>
            </div>

            <div class="cat-card-foot">
              <button
                type="button"
                class="acc-action-btn primary full-width"
                :id="'btn-save-category-' + cat.category_key"
                @click="saveCategoryConfig(cat)"
              >
                保存分类模板
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= 4. NINE AGENTS HOT-PLUG & BLACKBOARD INTEGRATOR ================= -->
    <section v-if="activeSubTab === 'integrator'" class="acc-section" id="acc-panel-integrator">
      <!-- Live Sandbox Dispatcher -->
      <div class="acc-card-block sandbox-card">
        <div class="card-block-header">
          <div>
            <h3>9 号主智能体总控台 & 跨智能体协同沙盒测试舱</h3>
            <p class="section-desc">可指定调用 1~9 号任意智能体，验证 0~100 置信度路由、推荐智能体胶囊、Skills 自动注入以及后台关停时的温和兜底提示。</p>
          </div>
        </div>
        <div class="sandbox-controls">
          <select v-model="sandboxAgentId" class="acc-input sandbox-select" id="sandbox-agent-select">
            <option value="agent_9">9号 · 主智能体总控自动路由 (Supervisor)</option>
            <option v-for="ag in overview.agents" :key="ag.agent_id" :value="ag.agent_id">
              {{ ag.name }} ({{ ag.is_enabled ? '在线' : '已关停' }})
            </option>
          </select>
          <input
            v-model="sandboxQuery"
            type="text"
            class="acc-input sandbox-input"
            id="sandbox-query-input"
            placeholder="输入测试指令，例如：帮我用耳眼脑三路深度分析第一集剧情 / 生成一场雨夜重逢的导演分镜表 / 剧荒推荐好看短剧..."
            @keyup.enter="runSandboxDispatch"
          />
          <button
            type="button"
            class="acc-action-btn primary"
            id="btn-run-sandbox-dispatch"
            :disabled="isDispatching"
            @click="runSandboxDispatch"
          >
            {{ isDispatching ? '智能体思考中...' : '发送测试指令' }}
          </button>
        </div>

        <div v-if="sandboxResult" class="sandbox-result-panel" id="sandbox-result-panel">
          <div class="sandbox-meta-row">
            <span class="status-pill" :class="sandboxResult.is_fallback ? 'warn' : 'ok'">
              响应节点：{{ sandboxResult.invoked_agent_name }}
            </span>
            <span class="mode-pill">
              实际模型：{{ sandboxResult.resolved_model_info?.bind_mode }} -> {{ sandboxResult.resolved_model_info?.provider }}:{{ sandboxResult.resolved_model_info?.model_name }}
            </span>
            <span class="mode-pill">路由置信度：{{ sandboxResult.route_confidence }}%</span>
            <span class="mode-pill">耗时：{{ sandboxResult.latency_ms }} ms</span>
          </div>

          <div v-if="sandboxResult.recommended_agents?.length" class="rec-capsules-row">
            <span class="rec-label">9号主控推荐协同智能体胶囊：</span>
            <button
              v-for="rec in sandboxResult.recommended_agents"
              :key="rec.agent_id"
              type="button"
              class="rec-agent-capsule"
              @click="sandboxAgentId = rec.agent_id"
            >
              {{ rec.name }} ({{ rec.confidence }}%)
            </button>
          </div>

          <div v-if="sandboxResult.matched_skills?.length" class="rec-capsules-row">
            <span class="rec-label">Thought 思考期动态注入 Skills：</span>
            <span v-for="sk in sandboxResult.matched_skills" :key="sk.skill_id" class="skill-chip">
              {{ sk.name }}
            </span>
          </div>

          <div class="sandbox-thought-box">
            <strong>Thought 推理轨迹：</strong>{{ sandboxResult.thought_chain }}
          </div>
          <pre class="sandbox-answer-pre" id="sandbox-answer-text">{{ sandboxResult.answer }}</pre>
        </div>
      </div>

      <!-- 9 Agents Hot-Plug Matrix -->
      <div class="agents-matrix-grid">
        <div
          v-for="ag in overview.agents"
          :key="ag.agent_id"
          class="agent-config-card"
          :class="{ 'is-disabled': !ag.is_enabled }"
          :id="'agent-card-' + ag.agent_id"
        >
          <div class="agent-card-top">
            <div>
              <span class="agent-num-tag">#{{ ag.agent_number }} · {{ ag.category }}</span>
              <h4>{{ ag.name }}</h4>
              <p class="agent-role-sub">{{ ag.role_title }}</p>
            </div>
            <div class="hotplug-switch-wrap">
              <label class="switch-label">{{ ag.is_enabled ? '运行中' : '已关停' }}</label>
              <input
                type="checkbox"
                v-model="ag.is_enabled"
                :id="'switch-enable-' + ag.agent_id"
                @change="saveSingleAgent(ag)"
              />
            </div>
          </div>

          <div class="agent-form-body">
            <div class="form-grid-2">
              <div class="form-item">
                <label>模型绑定模式</label>
                <select v-model="ag.model_bind_mode" class="acc-input" :id="'select-bind-' + ag.agent_id">
                  <option value="GLOBAL_UNIFIED">全局统一 (跟随系统底座)</option>
                  <option value="CATEGORY_GROUP">分类治理 (跟随 {{ ag.category }})</option>
                  <option value="AGENT_CUSTOM">单智能体定制 (独立引擎)</option>
                </select>
              </div>
              <div class="form-item">
                <label>当前生效模型</label>
                <input
                  :value="ag.resolved_model ? (ag.resolved_model.provider + ':' + ag.resolved_model.model_name) : ag.model_name"
                  disabled
                  class="acc-input disabled-input"
                />
              </div>
            </div>

            <div v-if="ag.model_bind_mode === 'AGENT_CUSTOM'" class="form-grid-2 mt-8">
              <div class="form-item">
                <label>独立 Provider</label>
                <select v-model="ag.provider" class="acc-input">
                  <option value="ollama">ollama</option>
                  <option value="deepseek">deepseek</option>
                  <option value="mimo">mimo</option>
                  <option value="openai">openai</option>
                </select>
              </div>
              <div class="form-item">
                <label>独立模型名</label>
                <input v-model="ag.model_name" type="text" class="acc-input" />
              </div>
            </div>

            <div class="form-item mt-8">
              <label style="font-size: 12px; font-weight: 600; color: var(--agent-text-secondary, #61666D); margin-bottom: 4px; display: block;">后台关停提示 (disabled_fallback_msg)</label>
              <input
                v-model="ag.disabled_fallback_msg"
                type="text"
                class="acc-input"
                :id="'input-fallback-' + ag.agent_id"
              />
            </div>
          </div>

          <div class="agent-card-foot">
            <button
              type="button"
              class="acc-action-btn secondary"
              :id="'btn-test-' + ag.agent_id"
              @click="toggleInlineTest(ag)"
            >
              {{ getInlineTest(ag.agent_id).isOpen ? '收起业务测试' : '业务极速测试' }}
            </button>
            <button
              type="button"
              class="acc-action-btn primary"
              :id="'btn-open-chat-' + ag.agent_id"
              @click="openAgentChat(ag)"
            >
              专属中台对话
            </button>
            <button
              type="button"
              class="acc-action-btn primary"
              :id="'btn-save-' + ag.agent_id"
              @click="saveSingleAgent(ag)"
            >
              保存热配置
            </button>
          </div>

          <!-- Inline Test Drawer for instant visibility -->
          <div v-if="getInlineTest(ag.agent_id).isOpen" class="inline-agent-test-drawer" :id="'test-drawer-' + ag.agent_id">
            <div class="drawer-header">
              <span class="drawer-title">业务验证沙盒 · {{ ag.name }}</span>
              <button class="drawer-close" @click="getInlineTest(ag.agent_id).isOpen = false">✕</button>
            </div>

            <!-- Query Input Row -->
            <div class="drawer-input-row">
              <input
                v-model="getInlineTest(ag.agent_id).query"
                type="text"
                class="acc-input flex-1"
                :placeholder="'输入向 ' + ag.name + ' 发送的测试指令...'"
                :disabled="getInlineTest(ag.agent_id).isLoading"
                @keyup.enter="runInlineTest(ag.agent_id)"
              />
              <button
                type="button"
                class="acc-action-btn primary"
                :id="'btn-run-test-' + ag.agent_id"
                :disabled="getInlineTest(ag.agent_id).isLoading"
                @click="runInlineTest(ag.agent_id)"
              >
                {{ getInlineTest(ag.agent_id).isLoading ? '执行中...' : '立即调度' }}
              </button>
            </div>

            <!-- Result Box -->
            <div v-if="getInlineTest(ag.agent_id).result" class="drawer-result-box" :id="'test-result-' + ag.agent_id">
              <div class="result-tags-row">
                <span class="tag-status">执行耗时 {{ getInlineTest(ag.agent_id).result.cost_ms || 120 }}ms</span>
                <span class="tag-model">{{ getInlineTest(ag.agent_id).result.resolved_model_info?.model_name || '大模型引擎' }}</span>
                <span v-for="sk in getInlineTest(ag.agent_id).result.matched_skills" :key="sk.skill_id" class="skill-chip">
                  技能: {{ sk.name }}
                </span>
              </div>

              <!-- Thought Chain -->
              <div v-if="getInlineTest(ag.agent_id).result.thought_chain" class="drawer-thought">
                <strong>Thought 思考链路：</strong>{{ getInlineTest(ag.agent_id).result.thought_chain }}
              </div>

              <!-- Structured Storyboard Table if Agent 8 -->
              <div v-if="getInlineTest(ag.agent_id).result.structured_payload?.storyboard_shots?.length" class="storyboard-table-wrap">
                <table class="storyboard-table">
                  <thead>
                    <tr>
                      <th>镜号</th>
                      <th>景别与运镜</th>
                      <th>画面视觉</th>
                      <th>台词与潜台词</th>
                      <th>音效/BGM</th>
                      <th>时长</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="shot in getInlineTest(ag.agent_id).result.structured_payload.storyboard_shots" :key="shot.shot_no">
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

              <!-- Answer Markdown / Plaintext -->
              <pre class="drawer-answer-pre">{{ getInlineTest(ag.agent_id).result.answer }}</pre>
            </div>
          </div>
        </div>
      </div>

      <!-- Blackboard Memory Integrator -->
      <div class="acc-card-block mt-16">
        <div class="card-block-header">
          <div>
            <h3>管理员会话记忆整合器 (Blackboard Shared Memory & Sliding-Window Summarization)</h3>
            <p class="section-desc">管理 1~9 号智能体共用的全局黑板上下文，支持滑动窗口超限自动摘要与管理员一键强制压缩。</p>
          </div>
          <button
            type="button"
            class="acc-action-btn primary"
            id="btn-compress-default-blackboard"
            @click="handleCompressBlackboard('global_shared_session')"
          >
            一键压缩全局共享会话记忆
          </button>
        </div>

        <div class="acc-table-wrap" style="overflow-x: auto; width: 100%;">
          <table class="acc-data-table" id="table-blackboard-sessions" style="table-layout: fixed; width: 100%; min-width: 860px;">
            <thead>
              <tr>
                <th style="width: 140px;">会话 Session ID</th>
                <th style="width: 70px; text-align: center;">轮数</th>
                <th style="width: 80px; text-align: center;">压缩次数</th>
                <th>滚动摘要 (Rolling Summary)</th>
                <th style="width: 220px;">跨智能体共享事实锚点</th>
                <th style="width: 120px; text-align: center;">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="bs in pagedBlackboardSessions" :key="bs.session_id">
                <td class="mono-cell" style="word-break: break-all;">{{ bs.session_id }}</td>
                <td class="mono-cell" style="text-align: center;">{{ bs.turn_count }} 轮</td>
                <td class="mono-cell" style="text-align: center;">{{ bs.compression_count }} 次</td>
                <td class="preview-cell">
                  <div class="summary-clamp-box">
                    <span>{{ bs.rolling_summary || "暂无滚动摘要" }}</span>
                    <button v-if="bs.rolling_summary && bs.rolling_summary.length > 50" class="btn-expand-summary" @click="openSummaryModal(bs.rolling_summary)">
                      查看完整
                    </button>
                  </div>
                </td>
                <td>
                  <div class="shared-facts-box">
                    <span v-for="(v, k) in bs.shared_facts" :key="k" class="fact-pill">
                      {{ k }}: {{ typeof v === "object" ? JSON.stringify(v) : v }}
                    </span>
                    <span v-if="!bs.shared_facts || Object.keys(bs.shared_facts).length === 0" class="muted-txt">无事实锚点</span>
                  </div>
                </td>
                <td style="text-align: center;">
                  <button
                    type="button"
                    class="acc-action-btn secondary"
                    @click="handleCompressBlackboard(bs.session_id)"
                  >
                    立即摘要压缩
                  </button>
                </td>
              </tr>
              <tr v-if="!overview.blackboard_sessions?.length">
                <td colspan="6" class="empty-cell" style="text-align: center; padding: 24px;">暂无黑板共享会话记录</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="pagination-row mt-12" style="display: flex; justify-content: flex-end; padding-top: 10px;">
          <el-pagination
            v-model:current-page="bbCurrentPage"
            v-model:page-size="bbPageSize"
            :page-sizes="[5, 10, 20]"
            layout="total, sizes, prev, pager, next"
            :total="overview.blackboard_sessions?.length || 0"
          />
        </div>
      </div>
    </section>

    <!-- ================= 5. SKILLS MANAGER & HITL MODERATION QUEUE ================= -->
    <section v-if="activeSubTab === 'skills'" class="acc-section" id="acc-panel-skills">
      <!-- Skills Free-Mounting Manager -->
      <div class="acc-card-block">
        <div class="card-block-header">
          <div>
            <h3>Skills 自由挂载管理器（支持定向挂载单个智能体 / 一键全量挂载 / 外部 GitHub SKILL.md 导入）</h3>
            <p class="section-desc">智能体在 Thought 思考阶段自动扫描已挂载技能并在命中后注入完整 SKILL.md 执行 SOP。</p>
          </div>
          <div class="btn-row">
            <button
              type="button"
              class="acc-action-btn primary"
              id="btn-mount-all-skills-global"
              @click="handleToggleAllGlobalMount(true)"
            >
              一键全员挂载全部 Skills
            </button>
            <button
              type="button"
              class="acc-action-btn secondary"
              id="btn-unmount-all-skills-targeted"
              @click="handleToggleAllGlobalMount(false)"
            >
              恢复按智能体定向挂载
            </button>
            <button
              type="button"
              class="acc-action-btn primary"
              id="btn-open-new-skill-modal"
              @click="showNewSkillForm = !showNewSkillForm"
            >
              + 导入 / 新建 SKILL.md 技能包
            </button>
          </div>
        </div>

        <!-- New Skill Import Drawer/Box -->
        <div v-if="showNewSkillForm" class="new-skill-form-box" id="new-skill-form-box">
          <h4>新建或粘贴外部 GitHub SKILL.md 技能插件</h4>
          <div class="form-grid-3">
            <div class="form-item">
              <label>技能名称</label>
              <input v-model="newSkill.name" type="text" class="acc-input" id="input-new-skill-name" placeholder="如：短剧黄金反转台词精修器" />
            </div>
            <div class="form-item">
              <label>技能分类</label>
              <input v-model="newSkill.category" type="text" class="acc-input" placeholder="如：短剧编导" />
            </div>
            <div class="form-item">
              <label>触发关键词 (逗号分隔)</label>
              <input v-model="newSkill.trigger_keywords" type="text" class="acc-input" id="input-new-skill-keywords" placeholder="反转,台词,精修,冲突" />
            </div>
          </div>
          <div class="form-item mt-8">
            <label>技能描述</label>
            <input v-model="newSkill.description" type="text" class="acc-input" placeholder="简述该技能何时被智能体在思考阶段调用" />
          </div>
          <div class="form-item mt-8">
            <label>SKILL.md 完整指令正文 (Markdown SOP)</label>
            <textarea v-model="newSkill.skill_markdown" rows="4" class="acc-input" id="input-new-skill-md" placeholder="# 技能 SOP 正文..."></textarea>
          </div>
          <div class="btn-row mt-8">
            <label class="checkbox-inline">
              <input type="checkbox" v-model="newSkill.is_global_mount" />
              <span>直接全局挂载给全部 1~9 号智能体</span>
            </label>
            <button type="button" class="acc-action-btn primary" id="btn-submit-new-skill" @click="createNewSkill">
              确认保存并挂载技能
            </button>
          </div>
        </div>

        <!-- Skills Cards Grid -->
        <div class="skills-grid">
          <div
            v-for="sk in overview.skills"
            :key="sk.skill_id"
            class="skill-manage-card"
            :id="'skill-card-' + sk.skill_id"
          >
            <div class="skill-card-head">
              <div>
                <span class="cat-key-badge">{{ sk.category }}</span>
                <h4>{{ sk.name }}</h4>
              </div>
              <span class="hit-count-pill">累计触发 {{ sk.hit_count }} 次</span>
            </div>
            <p class="cat-desc">{{ sk.description }}</p>
            <div class="skill-kw-line">
              <strong>触发词：</strong><span>{{ sk.trigger_keywords }}</span>
            </div>

            <div class="skill-mount-controls">
              <label class="checkbox-inline strong-toggle">
                <input
                  type="checkbox"
                  v-model="sk.is_global_mount"
                  :id="'check-global-skill-' + sk.skill_id"
                  @change="saveSkillConfig(sk)"
                />
                <span>全员挂载 (1~9号全部共享)</span>
              </label>

              <div class="agent-checkbox-group">
                <span class="small-lbl">定向挂载智能体：</span>
                <label v-for="n in 9" :key="n" class="agent-mini-check">
                  <input
                    type="checkbox"
                    :value="'agent_' + n"
                    v-model="sk.mounted_agents"
                    :disabled="sk.is_global_mount"
                    @change="saveSkillConfig(sk)"
                  />
                  <span>{{ n }}号</span>
                </label>
              </div>
            </div>
            <div class="skill-card-actions mt-12" style="display: flex; gap: 8px; justify-content: flex-end; border-top: 1px solid var(--agent-card-border, rgba(0,0,0,0.06)); padding-top: 10px;">
              <button
                type="button"
                class="acc-action-btn secondary"
                :id="'btn-export-rag-' + sk.skill_id"
                @click="openExportRagModal(sk)"
              >
                加入知识库 (向量化)
              </button>
              <button
                type="button"
                class="acc-action-btn danger"
                :id="'btn-del-skill-' + sk.skill_id"
                @click="deleteSingleSkill(sk)"
              >
                删除技能
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Skills 流转与向量化审计流水日志 -->
      <div class="acc-card-block mt-16" id="skills-logs-block">
        <div class="card-block-header flex items-center justify-between pb-3" style="border-bottom: 1px solid var(--border-line, rgba(255,255,255,0.08));">
          <div>
            <div class="flex items-center gap-2">
              <span class="pulse-dot" style="background: #0071E3;"></span>
              <h4 style="font-size: 15px; font-weight: 700; color: var(--agent-text-title, #18191C); margin: 0;">Skills 技能流转与向量化审计流水日志</h4>
            </div>
            <p class="section-desc mt-1" style="font-size: 12px; color: var(--agent-text-muted, #86868b); margin: 0;">
              实时捕获技能全员挂载、定向装配、新建入库、删除以及向量化切片注入 RAG 知识库的全链路审计日志。
            </p>
          </div>
          <button type="button" class="acc-action-btn secondary" id="btn-refresh-skill-logs" @click="loadSkillLogs">
            刷新流水
          </button>
        </div>

        <div class="acc-table-wrap mt-10" style="overflow-x: auto; width: 100%;">
          <table class="acc-data-table" id="table-skills-logs" style="table-layout: fixed; width: 100%; min-width: 800px;">
            <thead>
              <tr>
                <th style="width: 150px;">操作时间</th>
                <th style="width: 110px; text-align: center;">操作类型</th>
                <th style="width: 180px;">技能名称</th>
                <th style="width: 90px; text-align: center;">操作人</th>
                <th>生效范畴 / 归属短剧</th>
                <th style="width: 90px; text-align: center;">切片数</th>
                <th style="width: 90px; text-align: center;">状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in skillLogs" :key="log.id">
                <td class="mono-cell" style="font-size: 11px;">{{ log.created_at || '刚刚' }}</td>
                <td style="text-align: center;">
                  <span class="px-2 py-0.5 rounded text-[11px] font-bold"
                    :style="log.action === 'EXPORT_RAG' ? 'background: rgba(52,199,89,0.15); color: #34C759;' : (log.action === 'DELETE' ? 'background: rgba(255,59,48,0.15); color: #FF3B30;' : 'background: rgba(0,113,227,0.15); color: #0071E3;')">
                    {{ log.action === 'EXPORT_RAG' ? 'RAG向量化' : (log.action === 'DELETE' ? '删除技能' : (log.action === 'CREATE' ? '新建技能' : '挂载变更')) }}
                  </span>
                </td>
                <td style="font-weight: 600; color: var(--agent-text-title, #18191C);">{{ log.skill_name }}</td>
                <td style="text-align: center; font-size: 12px; color: var(--agent-text-muted, #86868b);">{{ log.operator }}</td>
                <td style="font-size: 12px;">{{ log.target_scope }}</td>
                <td class="mono-cell" style="text-align: center;">{{ log.chunks_count || '-' }}</td>
                <td style="text-align: center;">
                  <span class="px-2 py-0.5 rounded text-[11px] font-bold" style="background: rgba(52,199,89,0.15); color: #34C759;">
                    {{ log.status }}
                  </span>
                </td>
              </tr>
              <tr v-if="skillLogs.length === 0">
                <td colspan="7" class="empty-cell" style="text-align: center; padding: 20px; color: var(--agent-text-muted, #86868b);">
                  暂无技能操作流转审计日志（执行向量化入库或挂载操作后自动记录）
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </section>

    <!-- ================= 6. ROUNDTABLE WORKSPACE (沉浸式协同圆桌方案三) ================= -->
    <section v-if="activeSubTab === 'roundtable'" class="acc-section" id="acc-panel-roundtable">
      <AgentRoundTableCanvas />
    </section>

    <!-- ================= 7. SKILL EVOLUTION HITL (自进化提案审核工作台) ================= -->
    <section v-if="activeSubTab === 'evolution'" class="acc-section" id="acc-panel-evolution">
      <div class="acc-card-block">
        <div class="card-block-header flex flex-wrap items-center justify-between gap-3 pb-3" style="border-bottom: 1px solid var(--border-line, rgba(255,255,255,0.08));">
          <div>
            <div class="flex items-center gap-2">
              <span class="pulse-dot" style="background: #34C759;"></span>
              <h3 style="font-size: 16px; font-weight: 700; color: var(--agent-text-title, #18191C); margin: 0;">Skills 自进化技能提案审核工作台 (HITL 人机回环)</h3>
            </div>
            <p class="section-desc mt-1" style="font-size: 13px; color: var(--agent-text-muted, #86868b); margin: 0;">
              运行机制说明：当智能体在圆桌协同或剧本创作中完成高难度演练时，Critic 质检智能体自动对轨迹执行反思蒸馏，生成可热加载的专业 SOP 提案。管理员在此进行 Diff 审核，批准后无需重启即可动态热加载生效。
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" class="acc-action-btn secondary" id="btn-refresh-evolution" @click="loadEvolutionProposals">
              刷新提案
            </button>
            <button type="button" class="acc-action-btn primary" id="btn-trigger-distill-sample" @click="triggerEvolutionDistill">
              + 演练蒸馏: 生成高分分镜SOP提案
            </button>
          </div>
        </div>

        <!-- 提案卡片展示列表 -->
        <div class="evolution-proposals-container mt-4">
          <div v-if="evolutionLoading" class="p-8 text-center" style="color: var(--agent-text-muted, #86868b);">
            正在同步智能体自进化提案池...
          </div>
          <div v-else-if="evolutionProposals.length === 0" class="p-8 text-center rounded-2xl" style="background: var(--agent-card-bg-subtle, rgba(255,255,255,0.03)); border: 1px dashed var(--border-line, rgba(255,255,255,0.15));">
            <h4 style="font-size: 15px; font-weight: 600; color: var(--agent-text-title, #18191C);">当前暂无待审核的自进化提案</h4>
            <p style="font-size: 13px; color: var(--agent-text-muted, #86868b); max-width: 520px; margin: 8px auto 16px;">
              智能体在日常协同与创作中持续演练。点击下方按钮，可模拟 Critic 质检智能体对 8号导演分镜 在雨夜反杀高分场景中的真实思考轨迹，自动蒸馏并生成一条高含金量 SOP 技能提案。
            </p>
            <button type="button" class="acc-action-btn primary" @click="triggerEvolutionDistill">
              立即生成一条高分自进化提案演示
            </button>
          </div>
          <div v-else class="grid grid-cols-1 gap-4">
            <div
              v-for="p in evolutionProposals"
              :key="p.id"
              class="evo-card p-4 rounded-xl"
              style="background: var(--agent-card-bg, rgba(255,255,255,0.04)); border: 1px solid var(--border-line, rgba(255,255,255,0.12));"
              :id="'evo-card-' + p.id"
            >
              <div class="flex items-center justify-between gap-3 mb-2">
                <div class="flex items-center gap-2">
                  <span class="px-2 py-0.5 rounded text-[11px] font-bold" style="background: #0071E3; color: #fff;">
                    {{ p.target_agent_id }}
                  </span>
                  <h4 style="font-size: 14px; font-weight: 700; color: var(--agent-text-title, #18191C); margin: 0;">{{ p.title }}</h4>
                </div>
                <div class="flex items-center gap-2">
                  <span class="px-2.5 py-1 rounded-full text-xs font-bold" style="background: rgba(52, 199, 89, 0.15); color: #34C759;">
                    Critic 评分: {{ p.critic_score }}分
                  </span>
                  <span class="px-2 py-0.5 rounded text-xs" :style="p.status === 'APPROVED' ? 'background: #34C759; color: #fff;' : 'background: #FF9500; color: #fff;'">
                    {{ p.status === 'APPROVED' ? '已热加载上线' : '待人工审核' }}
                  </span>
                </div>
              </div>

              <p style="font-size: 12px; color: var(--agent-text-muted, #86868b); margin: 4px 0 10px;">
                质检专家评审结论: {{ p.critic_verdict }}
              </p>

              <!-- Markdown/SOP Diff 预览 (优化排版与舒适间距) -->
              <div class="p-3 rounded-xl overflow-x-auto" style="background: var(--agent-code-bg, rgba(0,0,0,0.3)); border: 1px solid var(--border-line, rgba(255,255,255,0.1)); font-family: 'JetBrains Mono', Consolas, monospace; font-size: 12px; line-height: 1.6; max-height: 240px; margin: 8px 0;">
                <pre style="margin: 0; white-space: pre-wrap; word-break: break-word; color: var(--agent-text-body, #d1d5db);">{{ p.skill_content }}</pre>
              </div>

              <div class="flex items-center justify-between mt-3 pt-2" style="border-top: 1px solid var(--border-line, rgba(255,255,255,0.08));">
                <span style="font-size: 11px; color: var(--agent-text-muted, #86868b);">提炼生成时间: {{ p.created_at || '刚刚' }}</span>
                <div class="flex items-center gap-2">
                  <button
                    v-if="p.status === 'PENDING'"
                    type="button"
                    class="acc-action-btn primary"
                    :id="'btn-approve-evo-' + p.id"
                    @click="approveEvolutionProposal(p.id)"
                  >
                    一键批准并动态热加载上线
                  </button>
                  <span v-else style="font-size: 12px; color: #34C759; font-weight: 600;">已处于生产挂载状态</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= 8. RUNTIME GOVERNANCE SLIDERS (动态超时治理滑块) ================= -->
    <section v-if="activeSubTab === 'governance'" class="acc-section" id="acc-panel-governance">
      <div class="acc-card-block">
        <div class="card-block-header">
          <div>
            <h3>运行时工程韧性与动态超时滑块治理 (免重启热生效)</h3>
            <p class="section-desc">动态调节单工具调用超时与单轮长思考推理超时阈值，彻底规避复杂模型与多模态分析卡死。</p>
          </div>
          <button type="button" class="acc-action-btn primary" id="btn-save-governance-sliders" @click="saveGovernanceSliders">
            保存治理配置
          </button>
        </div>

        <div class="form-grid-3 mt-16">
          <div class="form-item">
            <label>单工具调用超时: <strong>{{ governanceConfig.tool_timeout_seconds }} 秒</strong> (建议 15~60s)</label>
            <input
              type="range"
              min="5"
              max="120"
              step="5"
              v-model.number="governanceConfig.tool_timeout_seconds"
              class="acc-slider"
              id="slider-tool-timeout"
            />
          </div>
          <div class="form-item">
            <label>单轮思考推理超时: <strong>{{ governanceConfig.thought_timeout_seconds }} 秒</strong> (建议 30~180s)</label>
            <input
              type="range"
              min="15"
              max="300"
              step="15"
              v-model.number="governanceConfig.thought_timeout_seconds"
              class="acc-slider"
              id="slider-thought-timeout"
            />
          </div>
          <div class="form-item">
            <label>滑动窗口截断轮次: <strong>{{ governanceConfig.sliding_window_rounds }} 轮</strong> (近5~10轮)</label>
            <input
              type="range"
              min="3"
              max="30"
              step="1"
              v-model.number="governanceConfig.sliding_window_rounds"
              class="acc-slider"
              id="slider-sliding-window"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- 挂载通用网页版智能体对话弹窗 (类似 ChatGPT) -->
    <UniversalAgentChatModal
      v-model="showUniversalChat"
      :agent-id="currentChatAgent.agent_id"
      :agent-name="currentChatAgent.name"
      :role-title="currentChatAgent.role_title"
    />

    <!-- 挂载自进化技能审核模态框 -->
    <SkillEvolutionModal v-model="showEvolutionModal" />
    <!-- Export Skill to RAG Knowledge Base Dialog -->
    <el-dialog
      v-model="showExportRagDialog"
      title="将技能文档切片并向量化存入 RAG 知识库"
      width="560px"
      append-to-body
    >
      <div v-if="exportingSkill" class="export-rag-dialog-body">
        <p class="export-hint" style="font-size: 13px; line-height: 1.6; color: var(--agent-text-body, #2c2c2e);">
          将技能【<strong>{{ exportingSkill.name }}</strong>】转存入 RAG 知识库，系统将对其 SOP 进行真实分块（Chunking），并调用向量 Embedder 嵌入向量，持久化存入向量库。
        </p>
        <div class="form-item mt-12">
          <label style="display: block; font-size: 12px; font-weight: 600; margin-bottom: 4px;">目标知识库分类 (文件夹)</label>
          <select v-model="ragExportTargetCategory" class="acc-input" style="width: 100%;">
            <option value="">默认根分类 (通用业务规范)</option>
            <option v-for="c in ragCategoriesList" :key="c.id" :value="c.id">
              {{ c.name }}
            </option>
          </select>
        </div>
        <div class="form-item mt-12">
          <label style="display: block; font-size: 12px; font-weight: 600; margin-bottom: 4px;">归属短剧上下文 (选填)</label>
          <select v-model="ragExportTargetDrama" class="acc-input" style="width: 100%;">
            <option value="">全剧通用规则 (无特定短剧)</option>
            <option v-for="d in ragDramasList" :key="d.id" :value="d.id">
              {{ d.title }}
            </option>
          </select>
        </div>
        <div class="form-item mt-12">
          <label style="display: block; font-size: 12px; font-weight: 600; margin-bottom: 4px;">切片策略</label>
          <select v-model="ragExportStrategy" class="acc-input" style="width: 100%;">
            <option value="fixed">定长重叠切片 (Fixed 250字, 重叠40字)</option>
            <option value="parent_child">父子级块级切片 (Parent-Child)</option>
            <option value="sliding">滑动窗口切片 (Sliding Window)</option>
          </select>
        </div>
        <div v-if="ragExportResult" class="export-result-box mt-12" style="background: rgba(52, 199, 89, 0.12); border: 1px solid rgba(52, 199, 89, 0.35); border-radius: 10px; padding: 12px; font-size: 13px; color: #34c759;">
          <div class="flex items-center justify-between">
            <strong>切片与向量化完成！已归入知识库</strong>
            <button type="button" class="btn-text-action font-bold" style="color: #0071e3; cursor: pointer; text-decoration: underline; background: none; border: none; font-size: 13px;" @click="goToRagKnowledgeCenter" id="btn-jump-to-rag">
              前往 RAG 知识库查看 →
            </button>
          </div>
          <p style="margin: 6px 0 0; color: var(--agent-text-body, #334155); font-size: 12px;">
            资产标题：<strong>{{ ragExportResult.title || exportingSkill?.name }}</strong> | 
            已切片: {{ ragExportResult.chunks_count }} 块 | 向量维度: {{ ragExportResult.vector_dim }} 维
          </p>
        </div>
      </div>
      <template #footer>
        <button class="acc-action-btn secondary" @click="showExportRagDialog = false">取消</button>
        <button
          class="acc-action-btn primary ml-8"
          :disabled="isExportingRag"
          @click="submitExportSkillToRag"
        >
          {{ isExportingRag ? "正在切片向量化..." : "立即切片入库" }}
        </button>
      </template>
    </el-dialog>

    <!-- Full Summary Viewer Dialog -->
    <el-dialog v-model="showSummaryDialog" title="黑板全局滚动摘要详情" width="600px" append-to-body>
      <div class="summary-dialog-content" style="max-height: 400px; overflow-y: auto; padding: 8px;">
        <pre style="white-space: pre-wrap; font-family: monospace; font-size: 13px; line-height: 1.6; margin: 0;">{{ currentFullSummary }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
if (typeof window !== 'undefined') {
  window.echarts = echarts
}
import axios from 'axios'
import UniversalAgentChatModal from './UniversalAgentChatModal.vue'
import AgentRoundTableCanvas from './AgentRoundTableCanvas.vue'
import SkillEvolutionModal from './SkillEvolutionModal.vue'

const props = defineProps({
  initialSubTab: {
    type: String,
    default: 'tactical'
  }
})

const route = useRoute()
const activeSubTab = ref(props.initialSubTab || 'tactical')

const subTabs = [
  { key: 'tactical', label: '1. Agent 战术大屏 (5主题)', badge: 'LIVE' },
  { key: 'bi', label: '2. Agent BI 可视化看板', badge: '' },
  { key: 'models', label: '3. 大模型统一/三分类治理', badge: '3级' },
  { key: 'integrator', label: '4. 九大智能体热插拔 & 记忆整合器', badge: '9 Agents' },
  { key: 'skills', label: '5. Skills 动态挂载与知识库转存', badge: 'Skills' },
  { key: 'roundtable', label: '6. 沉浸协同圆桌 (方案三)', badge: 'Grok/Muse' },
  { key: 'evolution', label: '7. Skills 自进化审核', badge: 'HITL' },
  { key: 'governance', label: '8. 动态超时滑块治理', badge: '30s/60s' }
]

const bbCurrentPage = ref(1)
const bbPageSize = ref(5)
const pagedBlackboardSessions = computed(() => {
  const list = overview.blackboard_sessions || []
  const start = (bbCurrentPage.value - 1) * bbPageSize.value
  return list.slice(start, start + bbPageSize.value)
})

const showSummaryDialog = ref(false)
const currentFullSummary = ref("")
function openSummaryModal(summary) {
  currentFullSummary.value = summary || ""
  showSummaryDialog.value = true
}

const showExportRagDialog = ref(false)
const exportingSkill = ref(null)
const ragExportTargetCategory = ref("")
const ragExportTargetDrama = ref("")
const ragExportStrategy = ref("fixed")
const isExportingRag = ref(false)
const ragExportResult = ref(null)
const ragCategoriesList = ref([])
const ragDramasList = ref([])

async function openExportRagModal(skill) {
  exportingSkill.value = skill
  ragExportTargetCategory.value = ""
  ragExportTargetDrama.value = ""
  ragExportStrategy.value = "fixed"
  ragExportResult.value = null
  showExportRagDialog.value = true
  try {
    const res = await axios.get("/api/v1/agent-hub/skills/rag-categories")
    ragCategoriesList.value = res.data?.data?.categories || []
    ragDramasList.value = res.data?.data?.dramas || []
  } catch (e) {
    console.warn("Failed to load rag categories:", e)
  }
}


function goToRagKnowledgeCenter() {
  showExportRagDialog.value = false
  window.location.hash = '#/admin?tab=rag'
}

async function submitExportSkillToRag() {
  if (!exportingSkill.value) return
  isExportingRag.value = true
  try {
    const res = await axios.post(`/api/v1/agent-hub/skills/${exportingSkill.value.skill_id}/export-to-rag`, {
      category_id: ragExportTargetCategory.value || null,
      drama_id: ragExportTargetDrama.value || null,
      strategy: ragExportStrategy.value || "fixed",
    })
    ragExportResult.value = res.data?.data
    loadSkillLogs()
    ElMessage.success(res.data?.message || "技能已切片并成功向量化入库！")
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || "向量化入库失败")
  } finally {
    isExportingRag.value = false
  }
}

async function deleteSingleSkill(skill) {
  try {
    await ElMessageBox.confirm(`确定要彻底删除技能【${skill.name}】吗？`, "确认删除", {
      type: "warning",
      confirmButtonText: "确认删除",
      cancelButtonText: "取消",
    })
    const res = await axios.delete(`/api/v1/agent-hub/skills/${skill.skill_id}`)
    ElMessage.success(res.data?.message || "技能已成功删除")
    await refreshAllData()
  } catch (err) {
    if (err !== "cancel") {
      ElMessage.error(err.response?.data?.detail || "删除技能失败")
    }
  }
}

// 批量配置智能体专属状态
const selectedAgentIds = ref([])
const batchConfigForm = reactive({
  provider: 'mimo',
  model_name: 'mimo-v2.6-flash',
  base_url: 'https://api.xiaomimimo.com/v1',
  temperature: 0.4,
  timeout_sec: 30,
})

const isAllAgentsSelected = computed(() => {
  const agents = overview.agents || []
  return agents.length > 0 && selectedAgentIds.value.length === agents.length
})

function toggleSelectAllAgents() {
  const agents = overview.agents || []
  if (isAllAgentsSelected.value) {
    selectedAgentIds.value = []
  } else {
    selectedAgentIds.value = agents.map(a => a.agent_id)
  }
}

async function applyBatchAgentConfig() {
  if (selectedAgentIds.value.length === 0) {
    ElMessage.warning('请先勾选需要批量配置的智能体！')
    return
  }
  try {
    const res = await axios.post('/api/v1/agent-hub/agents/batch-configure', {
      agent_ids: selectedAgentIds.value,
      provider: batchConfigForm.provider,
      model_name: batchConfigForm.model_name,
      base_url: batchConfigForm.base_url,
      temperature: batchConfigForm.temperature,
      timeout_sec: batchConfigForm.timeout_sec,
      model_bind_mode: 'AGENT_CUSTOM',
    })
    ElMessage.success(res.data?.message || '批量配置已应用并生效')
    await refreshAllData()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '批量配置失败')
  }
}



const showUniversalChat = ref(false)
const currentChatAgent = ref({ agent_id: 'agent_9', name: '主控议长', role_title: '全局调度' })
const showEvolutionModal = ref(false)

const governanceConfig = reactive({
  tool_timeout_seconds: 30.0,
  thought_timeout_seconds: 60.0,
  sliding_window_rounds: 10
})

function openAgentChat(ag) {
  currentChatAgent.value = {
    agent_id: ag.agent_id,
    name: ag.name,
    role_title: ag.role_title
  }
  showUniversalChat.value = true
}

async function loadGovernanceConfig() {
  try {
    const res = await axios.get('/api/v1/agent-mesh/governance/config')
    if (res.data?.data) {
      Object.assign(governanceConfig, res.data.data)
    }
  } catch (e) {
    console.warn('Failed to load governance config:', e)
  }
}

async function saveGovernanceSliders() {
  try {
    const res = await axios.put('/api/v1/agent-mesh/governance/config', governanceConfig)
    ElMessage.success(res.data?.message || '运行时治理配置已保存并生效')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const tacticalThemes = [
  { id: 'spider', label: '01 SPIDER 星核蛛网' },
  { id: 'ops', label: '02 OPS 战术指挥' },
  { id: 'neural', label: '03 NEURAL 神经星环 (3D)' },
  { id: 'factory', label: '04 FACTORY 机器人工厂 (3D)' },
  { id: 'nebula', label: '05 NEBULA 星云矩阵 (3D)' }
]
const currentTacticalTheme = ref('spider')
const tacticalIframeRef = ref(null)

const overview = reactive({
  global_llm_config: {},
  agents: [],
  categories: [],
  skills: [],
  blackboard_sessions: [],
  moderation_interrupts: []
})

const telemetry = reactive({
  summary: {},
  agent_nodes: [],
  category_distribution: [],
  skill_rankings: [],
  recent_traces: [],
  traces_total: 0,
  traces_page: 1,
  traces_page_size: 10
})

const selectedTraceAgent = ref('ALL')
const selectedTraceStatus = ref('ALL')

const sandboxAgentId = ref('agent_9')
const sandboxQuery = ref('帮我用耳眼脑三路深度分析第一集剧情，并推荐类似高能短剧')
const isDispatching = ref(false)
const sandboxResult = ref(null)

const showNewSkillForm = ref(false)
const newSkill = reactive({
  name: '',
  category: '短剧编导',
  trigger_keywords: '反转,高潮,钩子',
  description: '',
  skill_markdown: '# 自定义短剧技能 SOP\n1. 强化人物动机冲突\n2. 保持台词精炼有力',
  is_global_mount: true,
  mounted_agents: ['agent_5', 'agent_8', 'agent_9']
})

const chartAgentCallsRef = ref(null)
const chartCategorySkillsRef = ref(null)
let chartCallsInst = null
let chartCatInst = null

function formatBindMode(mode) {
  if (mode === 'CATEGORY_GROUP') return '三分类治理'
  if (mode === 'AGENT_CUSTOM') return '单Agent定制'
  return '全局统一底座'
}

function switchSubTab(key) {
  activeSubTab.value = key
  if (key === 'bi') {
    nextTick(() => {
      renderBiCharts()
      setTimeout(() => {
        if (chartCallsInst) chartCallsInst.resize()
        if (chartCatInst) chartCatInst.resize()
      }, 150)
    })
  } else if (key === 'skills') {
    loadSkillLogs()
  } else if (key === 'evolution') {
    loadEvolutionProposals()
  }
}

function selectTacticalTheme(themeId) {
  currentTacticalTheme.value = themeId
  if (tacticalIframeRef.value && tacticalIframeRef.value.contentWindow) {
    tacticalIframeRef.value.contentWindow.postMessage(
      { type: 'CINEMA_SWITCH_THEME', theme: themeId },
      '*'
    )
  }
}

async function fetchOverview() {
  try {
    const res = await axios.get('/api/v1/agent-hub/overview')
    if (res.data?.data) {
      const d = res.data.data
      overview.global_llm_config = d.global_llm_config || {}
      overview.agents = d.agents || []
      overview.categories = d.categories || []
      overview.skills = d.skills || []
      overview.blackboard_sessions = d.blackboard_sessions || []
      overview.moderation_interrupts = d.moderation_interrupts || []
    }
  } catch (e) {
    console.warn('Fetch agent overview error:', e)
  }
}

async function fetchTelemetry(page = 1) {
  try {
    telemetry.traces_page = page
    const params = {
      page: telemetry.traces_page,
      page_size: telemetry.traces_page_size || 10
    }
    if (selectedTraceAgent.value && selectedTraceAgent.value !== 'ALL') {
      params.agent_id = selectedTraceAgent.value
    }
    if (selectedTraceStatus.value && selectedTraceStatus.value !== 'ALL') {
      params.status = selectedTraceStatus.value
    }
    const res = await axios.get('/api/v1/agent-hub/telemetry/live', { params })
    if (res.data?.data) {
      const d = res.data.data
      telemetry.summary = d.summary || {}
      telemetry.agent_nodes = d.agent_nodes || []
      telemetry.category_distribution = d.category_distribution || []
      telemetry.skill_rankings = d.skill_rankings || []
      telemetry.recent_traces = d.recent_traces || []
      telemetry.traces_total = d.traces_total || 0
      telemetry.traces_page = d.traces_page || page
      telemetry.traces_page_size = d.traces_page_size || 10
      if (activeSubTab.value === 'bi') {
        nextTick(() => renderBiCharts())
      }
    }
  } catch (e) {
    console.warn('Fetch live telemetry error:', e)
  }
}

async function refreshAllData() {
  await Promise.all([fetchOverview(), fetchTelemetry(), loadSkillLogs()])
  if (tacticalIframeRef.value && tacticalIframeRef.value.contentWindow) {
    tacticalIframeRef.value.contentWindow.postMessage({ type: 'CINEMA_REFRESH_TELEMETRY' }, '*')
  }
}

async function handleBatchSwitchMode(mode) {
  try {
    const res = await axios.post('/api/v1/agent-hub/model-governance/switch-all', {
      model_bind_mode: mode
    })
    ElMessage.success(res.data?.message || '模型治理模式已切换')
    await refreshAllData()
  } catch (e) {
    ElMessage.error('切换失败')
  }
}

async function saveCategoryConfig(cat) {
  try {
    const res = await axios.put(`/api/v1/agent-hub/categories/${cat.category_key}`, {
      provider: cat.provider,
      model_name: cat.model_name,
      base_url: cat.base_url,
      temperature: cat.temperature
    })
    ElMessage.success(res.data?.message || '分类配置已保存')
    await refreshAllData()
  } catch (e) {
    ElMessage.error('保存分类配置失败')
  }
}

async function saveSingleAgent(ag) {
  try {
    const res = await axios.put(`/api/v1/agent-hub/agents/${ag.agent_id}`, {
      is_enabled: ag.is_enabled,
      model_bind_mode: ag.model_bind_mode,
      provider: ag.provider,
      model_name: ag.model_name,
      base_url: ag.base_url,
      temperature: ag.temperature,
      disabled_fallback_msg: ag.disabled_fallback_msg
    })
    ElMessage.success(res.data?.message || '智能体配置已更新')
    await refreshAllData()
  } catch (e) {
    ElMessage.error('保存智能体配置失败')
  }
}

const inlineTestState = reactive({})

function getInlineTest(agentId) {
  if (!inlineTestState[agentId]) {
    const presets = {
      agent_1: '@影伴AI课代表 针对第三集主角反击做个深度点评',
      agent_2: '作为观影灵宠，聊聊我最近看剧的品味并夸夸我',
      agent_3: '用Agentic RAG检索第三集关键道具信物与时间轴分片',
      agent_4: '测试弹幕审核拦截：【大结局幕后黑手就是管家，女主被骗了】',
      agent_5: '为都市悬疑复仇短剧起3个爆款剧名，并输出黄金前3秒视觉钩子',
      agent_6: '结合字幕轨、视觉场记与人物图谱，多模态深度拆解男女主对峙名场面',
      agent_7: '基于系统真实在架短剧为我推荐两部高能逆袭剧，并主动追问我的偏好',
      agent_8: '编写一段【雨夜豪门宴会厅女主亮出股权底牌反杀】的9:16竖屏导演分镜表',
      agent_9: '全面分析当前短剧的看点，并自动派发协同智能体组合',
    }
    inlineTestState[agentId] = {
      isOpen: false,
      isLoading: false,
      query: presets[agentId] || '请执行你的专属领域专家任务',
      result: null,
    }
  }
  return inlineTestState[agentId]
}

async function toggleInlineTest(ag) {
  const state = getInlineTest(ag.agent_id)
  state.isOpen = !state.isOpen
  if (state.isOpen && !state.result) {
    await runInlineTest(ag.agent_id)
  }
}

async function runInlineTest(agentId) {
  const state = getInlineTest(agentId)
  if (!state.query.trim()) return
  state.isLoading = true
  try {
    const res = await axios.post('/api/v1/agent-hub/dispatch', {
      query: state.query,
      agent_id: agentId,
      session_id: 'admin_inline_test_' + agentId,
    })
    state.result = res.data?.data || null
    ElMessage.success('智能体业务调度成功')
  } catch (err) {
    ElMessage.error('调度失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    state.isLoading = false
  }
}

async function quickTestAgent(ag) {
  await toggleInlineTest(ag)
}

async function runSandboxDispatch() {
  if (!sandboxQuery.value.trim()) return
  isDispatching.value = true
  try {
    const res = await axios.post('/api/v1/agent-hub/dispatch', {
      query: sandboxQuery.value,
      agent_id: sandboxAgentId.value,
      session_id: 'global_shared_session'
    })
    sandboxResult.value = res.data?.data || null
    await refreshAllData()
  } catch (e) {
    ElMessage.error('调度失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    isDispatching.value = false
  }
}

async function handleCompressBlackboard(sessionId) {
  try {
    const res = await axios.post('/api/v1/agent-hub/blackboard/compress', {
      session_id: sessionId
    })
    ElMessage.success(res.data?.message || '会话记忆压缩完成')
    await fetchOverview()
  } catch (e) {
    ElMessage.error('压缩会话记忆失败')
  }
}

async function handleToggleAllGlobalMount(flag) {
  try {
    const res = await axios.post('/api/v1/agent-hub/skills/mount-all', {
      is_global_mount: flag
    })
    ElMessage.success(res.data?.message || '已更新全局挂载状态')
    await refreshAllData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function saveSkillConfig(sk) {
  try {
    const res = await axios.put(`/api/v1/agent-hub/skills/${sk.skill_id}`, sk)
    ElMessage.success(res.data?.message || '技能挂载已更新')
    await refreshAllData()
  } catch (e) {
    ElMessage.error('更新技能失败')
  }
}

async function createNewSkill() {
  if (!newSkill.name.trim()) {
    ElMessage.warning('请填写技能名称')
    return
  }
  try {
    const res = await axios.post('/api/v1/agent-hub/skills', newSkill)
    ElMessage.success(res.data?.message || '新技能已导入并挂载')
    showNewSkillForm.value = false
    newSkill.name = ''
    await refreshAllData()
  } catch (e) {
    ElMessage.error('创建技能失败')
  }
}

async function handleResumeInterrupt(interruptId, action) {
  try {
    const res = await axios.post(`/api/v1/agent-hub/moderation/interrupts/${interruptId}/resume`, {
      action,
      reviewer_note: action === 'APPROVE' ? '审核员人工复核通过' : '审核员裁定违规拦截'
    })
    ElMessage.success(res.data?.message || '已执行回环裁决')
    await refreshAllData()
  } catch (e) {
    ElMessage.error('裁决执行失败')
  }
}

function renderBiCharts() {
  if (!chartAgentCallsRef.value || !chartCategorySkillsRef.value) return
  const isLight = document.documentElement.getAttribute('data-theme') === 'light'
  const textColor = isLight ? '#18191C' : '#F1F2F3'
  const subColor = isLight ? '#48484a' : '#94a3b8'
  const splitLineColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)'
  const tooltipBg = isLight ? 'rgba(255, 255, 255, 0.98)' : 'rgba(28, 28, 30, 0.95)'
  const tooltipBorder = isLight ? 'rgba(0, 0, 0, 0.12)' : 'rgba(255, 255, 255, 0.15)'

  if (!chartCallsInst) {
    chartCallsInst = echarts.init(chartAgentCallsRef.value)
  }
  if (!chartCatInst) {
    chartCatInst = echarts.init(chartCategorySkillsRef.value)
  }

  const nodes = telemetry.agent_nodes || []
  const names = nodes.map(n => `#${n.agent_number}`)
  const calls = nodes.map(n => n.calls || 0)
  const latencies = nodes.map(n => n.avg_latency_ms || 0)

  chartCallsInst.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      textStyle: { color: textColor }
    },
    legend: { 
      data: ['调用次数', '平均耗时(ms)'], 
      top: 8,
      right: 20,
      textStyle: { color: textColor, fontSize: 12 } 
    },
    grid: { left: 55, right: 55, top: 48, bottom: 44 },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: { color: subColor, fontWeight: 500, fontSize: 11, interval: 0 },
      axisLine: { lineStyle: { color: splitLineColor } }
    },
    yAxis: [
      {
        type: 'value',
        name: '次数',
        nameTextStyle: { color: subColor },
        axisLabel: { color: subColor },
        splitLine: { lineStyle: { color: splitLineColor } }
      },
      {
        type: 'value',
        name: 'ms',
        nameTextStyle: { color: subColor },
        axisLabel: { color: subColor },
        splitLine: { show: false }
      }
    ],
    series: [
      { name: '调用次数', type: 'bar', data: calls, itemStyle: { color: '#0071E3', borderRadius: [6, 6, 0, 0] } },
      { name: '平均耗时(ms)', type: 'line', yAxisIndex: 1, data: latencies, itemStyle: { color: '#34C759' } }
    ]
  })

  const skills = (telemetry.skill_rankings || []).slice(0, 6)
  chartCatInst.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      textStyle: { color: textColor }
    },
    grid: { left: 150, right: 30, top: 25, bottom: 25 },
    xAxis: {
      type: 'value',
      axisLabel: { color: subColor },
      splitLine: { lineStyle: { color: splitLineColor } }
    },
    yAxis: {
      type: 'category',
      data: skills.map(s => s.name.slice(0, 12)),
      axisLabel: { color: textColor, fontWeight: 500 }
    },
    series: [
      {
        name: 'Skill命中次数',
        type: 'bar',
        data: skills.map(s => s.hit_count || 0),
        itemStyle: { color: '#AF52DE', borderRadius: [0, 6, 6, 0] }
      }
    ]
  })
}

let themeObserver = null

watch(
  () => props.initialSubTab,
  (val) => {
    if (val) switchSubTab(val)
  }
)


// =================== 7. Skills 自进化提案审核逻辑 ===================
const skillLogs = ref([])
async function loadSkillLogs() {
  try {
    const res = await axios.get('/api/v1/agent-hub/skills/logs')
    skillLogs.value = res.data?.data?.items || []
  } catch (e) {
    console.warn('Failed to load skill logs:', e)
  }
}

const evolutionLoading = ref(false)
const evolutionProposals = ref([])

async function loadEvolutionProposals() {
  evolutionLoading.value = true
  try {
    const res = await axios.get('/api/v1/agent-mesh/evolution/proposals')
    evolutionProposals.value = res.data?.data || []
  } catch (e) {
    console.warn('Failed to load evolution proposals:', e)
  } finally {
    evolutionLoading.value = false
  }
}

async function triggerEvolutionDistill() {
  try {
    const res = await axios.post('/api/v1/agent-mesh/evolution/distill-sample')
    ElMessage.success('已自动蒸馏生成一条高难分镜创作新技能提案！')
    await loadEvolutionProposals()
  } catch (e) {
    ElMessage.error('生成演示提案失败')
  }
}

async function approveEvolutionProposal(id) {
  try {
    const res = await axios.post(`/api/v1/agent-mesh/evolution/proposals/${id}/approve`)
    ElMessage.success(res.data?.message || '技能已成功动态热加载！')
    await loadEvolutionProposals()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '批准失败')
  }
}

// =================== ECharts ResizeObserver 监听治理 ===================
let biResizeObserver = null

function setupBiResizeObserver() {
  if (typeof ResizeObserver === 'undefined') return
  if (biResizeObserver) biResizeObserver.disconnect()

  biResizeObserver = new ResizeObserver((entries) => {
    for (const entry of entries) {
      if (entry.contentRect.width > 0) {
        if (chartCallsInst) chartCallsInst.resize()
        if (chartCatInst) chartCatInst.resize()
      }
    }
  })

  if (chartAgentCallsRef.value) biResizeObserver.observe(chartAgentCallsRef.value)
  if (chartCategorySkillsRef.value) biResizeObserver.observe(chartCategorySkillsRef.value)
}

onMounted(async () => {
  setupBiResizeObserver()

  if (route.query.sub === 'hitl') {
    activeSubTab.value = 'skills'
  }
  await Promise.all([refreshAllData(), loadGovernanceConfig()])

  if (typeof MutationObserver !== 'undefined') {
    themeObserver = new MutationObserver(() => {
      if (activeSubTab.value === 'bi') {
        renderBiCharts()
      }
    })
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
  }
})

onBeforeUnmount(() => {
  if (chartCallsInst) chartCallsInst.dispose()
  if (chartCatInst) chartCatInst.dispose()
  if (themeObserver) themeObserver.disconnect()
  if (biResizeObserver) biResizeObserver.disconnect()
})
</script>

<style scoped>
.agent-command-center {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 6px 4px 32px;
  color: var(--agent-text-title, #18191C);
}

/* 统一 Apple HIG 卡片基底 */
.acc-header-bar,
.tactical-toolbar,
.acc-kpi-card,
.acc-chart-box,
.acc-card-block,
.category-config-card,
.agent-config-card,
.skill-manage-card {
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  border-radius: 18px;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.04);
  color: var(--agent-text-title, #18191C);
  transition: all 0.25s ease;
}

.acc-header-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 18px 24px;
}

.acc-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.2px;
  color: var(--agent-accent-blue, #0071e3);
  margin-bottom: 4px;
}

.acc-main-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--agent-text-title, #18191C);
}

.acc-subtab-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 对齐 AdminView .subtab-btn 原生药丸 */
.acc-subtab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 9999px;
  border: 1px solid var(--agent-card-border, #e5e5ea);
  background: var(--agent-bg-canvas, #f5f5f7);
  color: var(--agent-text-secondary, #48484a);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.acc-subtab-btn:hover {
  background: var(--agent-card-hover, #e8e8ed);
  color: var(--agent-text-title, #18191C);
}

.acc-subtab-btn.active {
  background: var(--agent-accent-blue, #0071e3) !important;
  color: #ffffff !important;
  border-color: var(--agent-accent-blue, #0071e3) !important;
  box-shadow: 0 4px 14px rgba(0, 113, 227, 0.35) !important;
}

.acc-tab-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.25);
}

.tactical-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  padding: 14px 20px;
}

.theme-pill-group {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 6px;
}

.theme-select-btn {
  padding: 6px 14px;
  border-radius: 9999px;
  border: 1px solid var(--agent-card-border, #e5e5ea);
  background: var(--agent-bg-canvas, #f5f5f7);
  color: var(--agent-text-secondary, #48484a);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.theme-select-btn:hover {
  background: var(--agent-card-hover, #e8e8ed);
  color: var(--agent-text-title, #18191C);
}

.theme-select-btn.active {
  background: var(--agent-accent-blue, #0071e3) !important;
  color: #ffffff !important;
  border-color: var(--agent-accent-blue, #0071e3) !important;
}

.tactical-iframe-container {
  width: 100%;
  height: 700px;
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.1));
  background: #050811;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}

.tactical-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.acc-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 18px;
}

.acc-kpi-card {
  padding: 20px;
}

.kpi-label {
  font-size: 12.5px;
  font-weight: 500;
  color: var(--agent-text-secondary, #61666D);
}

.kpi-value {
  font-size: 26px;
  font-weight: 800;
  margin: 8px 0;
  color: var(--agent-text-title, #18191C);
  letter-spacing: -0.5px;
}

.kpi-foot {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--agent-accent-blue, #0071e3);
}

.acc-charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 18px;
}

.acc-chart-box {
  padding: 20px;
}

.acc-echart-canvas {
  width: 100%;
  height: 290px;
}

.card-block-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.06));
}

.card-block-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--agent-text-title, #18191C);
}

.section-desc {
  margin: 4px 0 0;
  font-size: 12.5px;
  color: var(--agent-text-secondary, #61666D);
}

.btn-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.acc-action-btn {
  padding: 7px 16px;
  border-radius: 9999px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.acc-action-btn.primary {
  background: var(--agent-accent-blue, #0071e3);
  color: #ffffff;
}

.acc-action-btn.primary:hover {
  opacity: 0.92;
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.3);
}

.acc-action-btn.secondary {
  background: var(--agent-bg-canvas, #f5f5f7);
  color: var(--agent-text-title, #18191C);
  border: 1px solid var(--agent-card-border, #d2d2d7);
}

.acc-action-btn.secondary:hover {
  background: var(--agent-card-hover, #e8e8ed);
}

.acc-action-btn.danger {
  background: var(--agent-accent-red, #ff3b30);
  color: #ffffff;
}

.category-cards-grid,
.agents-matrix-grid,
.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(390px, 1fr));
  gap: 20px;
}

.acc-card-block {
  padding: 22px;
}

.category-config-card,
.agent-config-card,
.skill-manage-card {
  padding: 18px;
}

.form-grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.form-grid-3 {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 10px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-item label {
  font-size: 11.5px;
  font-weight: 500;
  color: var(--agent-text-secondary, #48484a);
}

/* 统一输入框与下拉选择框 */
.acc-input,
.sandbox-select,
.sandbox-input {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid var(--agent-input-border, rgba(0, 0, 0, 0.14));
  background: var(--agent-input-bg, #f5f5f7);
  color: var(--agent-text-title, #18191C);
  font-size: 13px;
  outline: none;
  box-sizing: border-box;
  transition: all 0.2s ease;
}

.acc-input:focus,
.sandbox-select:focus,
.sandbox-input:focus {
  border-color: var(--agent-accent-blue, #0071e3);
  background: var(--agent-card-surface, #ffffff);
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.18);
}

.disabled-input {
  background: var(--agent-bg-canvas, #f0f2f5) !important;
  color: var(--agent-text-muted, #6e6e73) !important;
  border-color: var(--agent-card-border, #e5e5ea) !important;
  cursor: not-allowed;
}

.sandbox-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.sandbox-select {
  width: 280px;
}

.sandbox-input {
  flex: 1;
}

.sandbox-result-panel {
  margin-top: 14px;
  padding: 16px;
  border-radius: 14px;
  background: var(--agent-bg-canvas, #f8fafc);
  border: 1px solid var(--agent-card-border, #e2e8f0);
}

.sandbox-meta-row,
.rec-capsules-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.rec-agent-capsule {
  padding: 4px 12px;
  border-radius: 999px;
  background: var(--agent-accent-blue-soft, rgba(0, 113, 227, 0.08));
  border: 1px solid var(--agent-accent-blue, #0071e3);
  color: var(--agent-accent-blue, #0071e3);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.sandbox-thought-box {
  font-size: 12px;
  color: var(--agent-accent-blue, #0071e3);
  margin-bottom: 8px;
}

.sandbox-answer-pre {
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
  padding: 12px;
  border-radius: 10px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, #e2e8f0);
  color: var(--agent-text-body, #18191C);
}

.agent-card-top,
.agent-card-foot,
.skill-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.agent-card-foot {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.agent-config-card.is-disabled {
  opacity: 0.72;
  border-color: rgba(239, 68, 68, 0.45);
}

.agent-num-tag,
.cat-key-badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--agent-accent-blue, #0071e3);
  background: var(--agent-accent-blue-soft, rgba(0, 113, 227, 0.08));
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid rgba(0, 113, 227, 0.2);
}

.agent-card-top h4,
.cat-card-head h4,
.skill-card-head h4 {
  margin: 6px 0 2px;
  font-size: 15px;
  font-weight: 700;
  color: var(--agent-text-title, #18191C);
}

.agent-role-sub,
.cat-desc {
  font-size: 12px;
  color: var(--agent-text-secondary, #61666D);
  margin: 4px 0 10px;
}

.acc-table-wrap {
  overflow-x: auto;
}

.acc-data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12.5px;
}

.acc-data-table th,
.acc-data-table td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  text-align: left;
}

.acc-data-table th {
  background: var(--agent-bg-canvas, #f5f5f7);
  color: var(--agent-text-title, #18191C);
  font-weight: 700;
}

.status-pill,
.mode-pill,
.skill-chip,
.hit-count-pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
}

.status-pill.ok {
  background: rgba(52, 199, 89, 0.12);
  color: #34c759;
}

.status-pill.warn {
  background: rgba(255, 149, 0, 0.12);
  color: #ff9500;
}

.status-pill.err {
  background: rgba(255, 59, 48, 0.12);
  color: #ff3b30;
}

.mode-pill {
  background: rgba(0, 113, 227, 0.08);
  color: #0071e3;
  border: 1px solid rgba(0, 113, 227, 0.2);
}

.skill-chip {
  background: rgba(175, 82, 222, 0.1);
  color: #af52de;
  margin-right: 4px;
}

.agent-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.agent-mini-check {
  font-size: 11.5px;
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.acc-slider {
  width: 100%;
  accent-color: var(--agent-accent-blue, #0071e3);
  cursor: pointer;
}

.mt-8 { margin-top: 8px; }
.mt-16 { margin-top: 16px; }
.ml-4 { margin-left: 4px; }
.full-width { width: 100%; margin-top: 10px; }

/* ========================================================================== */
/* Apple HIG 白昼与暗黑模式深度穿透保障规则                                   */
/* ========================================================================== */
:global([data-theme="light"]) .agent-command-center,
:global(.theme-light) .agent-command-center {
  color: #18191C !important;
}

:global([data-theme="light"]) .acc-header-bar,
:global(.theme-light) .acc-header-bar,
:global([data-theme="light"]) .tactical-toolbar,
:global(.theme-light) .tactical-toolbar,
:global([data-theme="light"]) .acc-kpi-card,
:global(.theme-light) .acc-kpi-card,
:global([data-theme="light"]) .acc-chart-box,
:global(.theme-light) .acc-chart-box,
:global([data-theme="light"]) .acc-card-block,
:global(.theme-light) .acc-card-block,
:global([data-theme="light"]) .category-config-card,
:global(.theme-light) .category-config-card,
:global([data-theme="light"]) .agent-config-card,
:global(.theme-light) .agent-config-card,
:global([data-theme="light"]) .skill-manage-card,
:global(.theme-light) .skill-manage-card {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.04) !important;
  color: #18191C !important;
}

:global([data-theme="light"]) .acc-eyebrow {
  color: #0071e3 !important;
}

:global([data-theme="light"]) .acc-main-title,
:global(.theme-light) .acc-main-title,
:global([data-theme="light"]) .card-block-header h3,
:global(.theme-light) .card-block-header h3,
:global([data-theme="light"]) .kpi-value,
:global(.theme-light) .kpi-value,
:global([data-theme="light"]) .agent-card-top h4,
:global([data-theme="light"]) .cat-card-head h4,
:global([data-theme="light"]) .skill-card-head h4 {
  color: #18191C !important;
}

:global([data-theme="light"]) .kpi-label,
:global(.theme-light) .kpi-label,
:global([data-theme="light"]) .section-desc,
:global(.theme-light) .section-desc,
:global([data-theme="light"]) .agent-role-sub,
:global(.theme-light) .agent-role-sub,
:global([data-theme="light"]) .cat-desc,
:global(.theme-light) .cat-desc,
:global([data-theme="light"]) .form-item label,
:global(.theme-light) .form-item label {
  color: #515154 !important;
}

:global([data-theme="light"]) .acc-subtab-btn {
  background: #f5f5f7 !important;
  border: 1px solid #e5e5ea !important;
  color: #48484a !important;
}

:global([data-theme="light"]) .acc-subtab-btn:hover {
  background: #e8e8ed !important;
  color: #18191C !important;
}

:global([data-theme="light"]) .acc-subtab-btn.active {
  background: #0071e3 !important;
  border-color: #0071e3 !important;
  color: #ffffff !important;
  box-shadow: 0 4px 14px rgba(0, 113, 227, 0.35) !important;
}

:global([data-theme="light"]) .theme-select-btn {
  background: #f5f5f7 !important;
  border: 1px solid #e5e5ea !important;
  color: #48484a !important;
}

:global([data-theme="light"]) .theme-select-btn.active {
  background: #0071e3 !important;
  border-color: #0071e3 !important;
  color: #ffffff !important;
}

:global([data-theme="light"]) .acc-input,
:global(.theme-light) .acc-input,
:global([data-theme="light"]) .sandbox-select,
:global([data-theme="light"]) .sandbox-input {
  background: #f5f5f7 !important;
  border: 1px solid #d2d2d7 !important;
  color: #18191C !important;
}

:global([data-theme="light"]) .acc-input:focus,
:global([data-theme="light"]) .sandbox-select:focus,
:global([data-theme="light"]) .sandbox-input:focus {
  background: #ffffff !important;
  border-color: #0071e3 !important;
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.18) !important;
}

:global([data-theme="light"]) .acc-input option,
:global([data-theme="light"]) .sandbox-select option {
  background: #ffffff !important;
  color: #18191C !important;
}

:global([data-theme="light"]) .acc-action-btn.secondary {
  background: #f2f2f7 !important;
  border: 1px solid #d2d2d7 !important;
  color: #18191C !important;
}

:global([data-theme="light"]) .acc-action-btn.secondary:hover {
  background: #e5e5ea !important;
  color: #000000 !important;
}

:global([data-theme="light"]) .disabled-input {
  background: #f0f2f5 !important;
  color: #6e6e73 !important;
  border-color: #e5e5ea !important;
}

:global([data-theme="light"]) .sandbox-result-panel {
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  color: #18191C !important;
}

:global([data-theme="light"]) .sandbox-answer-pre {
  background: #ffffff !important;
  border: 1px solid #e2e8f0 !important;
  color: #18191C !important;
}

:global([data-theme="light"]) .acc-data-table th {
  background: #f5f5f7 !important;
  color: #18191C !important;
  border-bottom: 1px solid #e5e5ea !important;
}

:global([data-theme="light"]) .acc-data-table td {
  color: #18191C !important;
  border-bottom: 1px solid #f2f2f7 !important;
}

/* Inline Agent Test Drawer */
.inline-agent-test-drawer {
  margin-top: 12px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.03);
  border: 1px dashed rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:global([data-theme="light"]) .inline-agent-test-drawer {
  background: #f8fafc;
  border-color: #cbd5e1;
}

:global([data-theme="dark"]) .inline-agent-test-drawer {
  background: rgba(15, 23, 42, 0.5);
  border-color: rgba(255, 255, 255, 0.1);
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.drawer-title {
  font-size: 11.5px;
  font-weight: 700;
  color: #0071e3;
}

.drawer-close {
  background: transparent;
  border: none;
  cursor: pointer;
  color: #8e8e93;
  font-size: 12px;
}

.drawer-input-row {
  display: flex;
  gap: 6px;
}

.drawer-result-box {
  padding: 10px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

:global([data-theme="dark"]) .drawer-result-box {
  background: #1c1c1e;
  border-color: rgba(255, 255, 255, 0.1);
}

.result-tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 6px;
}

.tag-status,
.tag-model {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 113, 227, 0.08);
  color: #0071e3;
  font-weight: 600;
}

.drawer-thought {
  font-size: 11px;
  color: #64748b;
  margin-bottom: 6px;
  line-height: 1.45;
}

.drawer-answer-pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  font-family: inherit;
  color: inherit;
}


.summary-clamp-box {
  display: flex;
  align-items: center;
  gap: 6px;
  max-height: 60px;
  overflow: hidden;
  line-height: 1.4;
  font-size: 12px;
}

.btn-expand-summary {
  background: transparent;
  border: 1px solid #0071e3;
  color: #0071e3;
  border-radius: 4px;
  font-size: 10px;
  padding: 1px 6px;
  cursor: pointer;
  flex-shrink: 0;
}

.shared-facts-box {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  max-height: 70px;
  overflow-y: auto;
}

.fact-pill {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 113, 227, 0.08);
  color: #0071e3;
  border: 1px solid rgba(0, 113, 227, 0.2);
  word-break: break-all;
}


/* 9大智能体独立解耦卡片与批量工具栏样式 (Apple HIG 语义化) */
.batch-agent-toolbar {
  padding: 14px 18px;
  border-radius: 12px;
  background: var(--agent-bg-canvas, #f8f9fa);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

.batch-toolbar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.batch-select-status {
  display: flex;
  align-items: center;
}

.selected-badge {
  font-size: 12px;
  font-weight: 700;
  color: var(--agent-accent-blue, #0071e3);
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 113, 227, 0.1);
}

.batch-tip {
  font-size: 12px;
  color: var(--agent-text-muted, #6e6e73);
}

.batch-inputs-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr 1.5fr 0.8fr 1.4fr;
  gap: 12px;
  align-items: flex-end;
}

@media (max-width: 1024px) {
  .batch-inputs-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.agent-custom-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
  gap: 16px;
  margin-top: 14px;
}

.agent-single-config-card {
  padding: 16px;
  border-radius: 14px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
  display: flex;
  flex-direction: column;
  transition: all 0.2s ease;
}

.agent-single-config-card.is-selected {
  border-color: #0071e3;
  box-shadow: 0 0 0 2px rgba(0, 113, 227, 0.2);
}

.agent-card-top-strip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.agent-badge-box {
  display: flex;
  align-items: center;
  gap: 6px;
}

.agent-id-pill {
  font-size: 11px;
  font-weight: 800;
  color: #0071e3;
  background: rgba(0, 113, 227, 0.1);
  padding: 2px 7px;
  border-radius: 999px;
}

.agent-mode-tag {
  font-size: 10.5px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--agent-tag-bg, #f0f2f5);
  color: var(--agent-text-secondary, #515154);
}

.agent-mode-tag.agent_custom {
  background: rgba(52, 199, 89, 0.12);
  color: #248a3d;
  font-weight: 700;
}

.agent-checkbox-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--agent-text-secondary, #515154);
  cursor: pointer;
}

.agent-name-title {
  font-size: 14.5px;
  font-weight: 700;
  color: var(--agent-text-title, #1d1d1f);
  margin: 0 0 4px 0;
}

.agent-role-desc {
  font-size: 12px;
  color: var(--agent-text-muted, #6e6e73);
  margin: 0 0 10px 0;
}

.agent-form-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.agent-card-actions {
  display: flex;
  align-items: center;
  margin-top: auto;
}
</style>
