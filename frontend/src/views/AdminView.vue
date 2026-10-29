<template>
  <div class="admin-page-root" id="admin-console-page">
    <AdminHeader mode="admin" :active-tab="currentTab" @selectTab="selectTab" />

    <!-- Global Hidden Image Upload Input adhering to DOM Selector Matrix #input-upload-image -->
    <input 
      type="file" 
      id="input-upload-image" 
      ref="imageUploadInputRef" 
      accept="image/jpeg,image/png,image/webp" 
      style="display: none;" 
      @change="handleImageFileSelected" 
    />

    <div class="admin-layout-wrapper">
      <!-- Ambient Lights -->
      <div class="admin-ambient-bg">
        <div class="admin-orb orb-1"></div>
        <div class="admin-orb orb-2"></div>
      </div>

      <!-- Collapsible Apple HIG Dynamic Sidebar -->
      <aside 
        class="admin-sidebar" 
        :class="{ 'is-collapsed': !isSidebarExpanded, 'is-pinned': isSidebarPinned }"
        @mouseenter="onSidebarMouseEnter"
        @mouseleave="onSidebarMouseLeave"
        id="admin-collapsible-sidebar"
      >
        <div class="sidebar-header">
          <div class="sidebar-brand" v-if="isSidebarExpanded">
            <el-icon class="brand-icon"><TrendCharts /></el-icon>
            <div class="brand-text">
              <span class="brand-name">管控中台</span>
              <span class="brand-sub">ENTERPRISE ADMIN</span>
            </div>
          </div>
          <div class="sidebar-brand-collapsed" v-else>
            <el-icon class="brand-icon"><TrendCharts /></el-icon>
          </div>

          <button 
            type="button" 
            class="sidebar-pin-btn" 
            @click="toggleSidebarPin"
            :title="isSidebarPinned ? '解除固定 (鼠标悬停展开)' : '锁定固定侧边栏'"
            id="btn-toggle-sidebar-pin"
          >
            <el-icon :size="16">
              <Fold v-if="isSidebarPinned" />
              <Expand v-else />
            </el-icon>
          </button>
        </div>

        <nav class="sidebar-nav-scroll">
          <!-- GROUP 1: 数据智能 -->
          <div class="nav-group-title" v-if="isSidebarExpanded">数据智能与看板</div>
          <div class="nav-divider" v-else></div>

          <button 
            class="nav-tab-item" 
            :class="{ active: currentTab === 'bi' }" 
            @click="selectTab('bi')"
            id="admin-tab-bi"
            title="BI 全景驾驶舱与时序预测"
          >
            <el-icon class="nav-icon"><DataLine /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">BI 智能驾驶舱</span>
          </button>

          <!-- GROUP 2: 短剧内容 -->
          <div class="nav-group-title" v-if="isSidebarExpanded">短剧资产与编目</div>
          <div class="nav-divider" v-else></div>

          <button 
            class="nav-tab-item" 
            :class="{ active: currentTab === 'dramas' }" 
            @click="selectTab('dramas')"
            id="admin-tab-dramas"
            title="短剧内容与封面管理"
          >
            <el-icon class="nav-icon"><Film /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">短剧资产编目</span>
          </button>

          <button 
            class="nav-tab-item" 
            :class="{ active: currentTab === 'sync' }" 
            @click="selectTab('sync')"
            id="admin-tab-sync"
            title="夸克网盘增量/全量同步"
          >
            <el-icon class="nav-icon"><Refresh /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">网盘双模同步</span>
          </button>

          <!-- GROUP 3: 运营调度 -->
          <div class="nav-group-title" v-if="isSidebarExpanded">运营调度营销</div>
          <div class="nav-divider" v-else></div>

          <button 
            class="nav-tab-item" 
            :class="{ active: currentTab === 'carousels' }" 
            @click="selectTab('carousels')"
            id="admin-tab-carousels"
            title="首页 5 秒焦点轮播管理"
          >
            <el-icon class="nav-icon"><Picture /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">首页焦点轮播</span>
          </button>

          <button 
            class="nav-tab-item" 
            :class="{ active: currentTab === 'announcements' }" 
            @click="selectTab('announcements')"
            id="admin-tab-announcements"
            title="全员系统公告发布与治理"
          >
            <el-icon class="nav-icon"><Bell /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">系统公告治理</span>
          </button>

          <button 
            class="nav-tab-item" 
            :class="{ active: currentTab === 'redemption' }" 
            @click="selectTab('redemption')"
            id="admin-tab-redemption"
            title="金币与会员兑换码批量生成与核销审计"
          >
            <el-icon class="nav-icon"><Promotion /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">兑换码资产中心</span>
          </button>

          <!-- GROUP 4: 权限治理 -->
          <div class="nav-group-title" v-if="isSidebarExpanded">用户与权限治理</div>
          <div class="nav-divider" v-else></div>

          <button 
            class="nav-tab-item" 
            :class="{ active: currentTab === 'users' }" 
            @click="selectTab('users')"
            id="admin-tab-users"
            title="用户账号与 RBAC 权限"
          >
            <el-icon class="nav-icon"><User /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">用户与 RBAC</span>
          </button>

          <button 
            class="nav-tab-item" 
            :class="{ active: currentTab === 'applications' }" 
            @click="selectTab('applications')"
            id="admin-tab-applications"
            title="创作者/审核员入驻审批"
          >
            <el-icon class="nav-icon"><DocumentChecked /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">资质双轨审批</span>
            <span v-if="pendingCount > 0 && isSidebarExpanded" class="nav-badge">{{ pendingCount }}</span>
          </button>

          <!-- GROUP 5: 安全合规 -->
          <div class="nav-group-title" v-if="isSidebarExpanded">社区合规安全</div>
          <div class="nav-divider" v-else></div>

          <button 
            class="nav-tab-item" 
            :class="{ active: currentTab === 'contents' }" 
            @click="selectTab('contents')"
            id="admin-tab-contents"
            title="弹幕与评论合规审查"
          >
            <el-icon class="nav-icon"><ChatLineSquare /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">互动合规风控</span>
          </button>

          <!-- GROUP 6: 引擎配置 -->


          <!-- GROUP 7: 知识中台与评测 -->
          <div class="nav-group-title" v-if="isSidebarExpanded">知识中台与算法评测</div>
          <div class="nav-divider" v-else></div>

          <button 
            class="nav-tab-item" 
            :class="{ active: currentTab === 'rag' }" 
            @click="selectTab('rag')"
            id="admin-tab-rag"
            title="RAG 知识工程与四维评测雷达大屏"
          >
            <el-icon class="nav-icon"><Cpu /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">RAG 知识与评测</span>
          </button>

          <!-- GROUP 8: 九大智能体与战术大屏 -->
          <div class="nav-group-title" v-if="isSidebarExpanded">九大智能体与战术大屏</div>
          <div class="nav-divider" v-else></div>

          <button 
            class="nav-tab-item" 
            :class="{ active: currentTab === 'agent-hub' }" 
            @click="selectTab('agent-hub')"
            id="admin-tab-agent-hub"
            title="九大智能体总控台、三级大模型治理、Skills挂载器与战术大屏"
          >
            <el-icon class="nav-icon"><DataLine /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">九大智能体 & 战术大屏</span>
          </button>

          <!-- GROUP 8.5: MCP 云端中台 -->
          <button
            class="nav-tab-item"
            :class="{ active: currentTab === 'mcp' }"
            @click="selectTab('mcp')"
            id="admin-tab-mcp"
            title="Model Context Protocol (MCP) 云端拓扑与沙盒调试"
          >
            <el-icon class="nav-icon"><Connection /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">MCP 云端中台</span>
          </button>

          <!-- GROUP 9: 系统与外观管理 -->
          <div class="nav-group-title" v-if="isSidebarExpanded">系统与外观</div>
          <div class="nav-divider" v-else></div>

          <button 
            class="nav-tab-item" 
            :class="{ active: currentTab === 'wallpaper' }" 
            @click="selectTab('wallpaper')"
            id="admin-tab-wallpaper"
            title="登录主页背景壁纸引擎与全局视觉配置"
          >
            <el-icon class="nav-icon"><Picture /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">登录壁纸配置</span>
          </button>
        </nav>
      </aside>

      <!-- Main Stage Workspace -->
      <main class="admin-main-stage" :class="{ 'is-rag-view': currentTab === 'rag' }">
        <!-- Top Action Bar -->
        <header class="stage-top-bar" v-if="currentTab !== 'rag'">
          <div class="bar-left">
            <span class="bar-breadcrumb">后台控制中台 / {{ currentTabTitle }}</span>
            <h2 class="bar-headline">{{ currentTabTitle }}</h2>
          </div>

          <div class="bar-right">
            <button 
              type="button" 
              class="apple-btn-secondary" 
              id="btn-admin-refresh" 
              @click="refreshCurrentTab"
              :disabled="loading"
            >
              <el-icon :class="{ 'is-loading': loading }"><Refresh /></el-icon>
              <span>刷新数据</span>
            </button>

            <button 
              type="button" 
              class="apple-btn-primary" 
              id="btn-quick-sync-pan" 
              @click="openSyncDialog"
            >
              <el-icon><Refresh /></el-icon>
              <span>网盘同步</span>
            </button>
          </div>
        </header>

        <!-- ================================================================= -->
        <!-- TAB 1: BI 全景驾驶舱与预测走势                                    -->
        <!-- ================================================================= -->
        <section v-show="currentTab === 'bi'" class="content-section" id="section-bi">
          <!-- 8 KPI Metrics Bento Grid -->
          <div class="kpi-grid">
            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">全站播放总量</span>
                <span class="kpi-badge blue">累计</span>
              </div>
              <div class="kpi-number">{{ formatNumber(biMetrics.total_views) }}</div>
              <div class="kpi-sub">包含 16:9 与 9:16 双模极速播放</div>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">实时弹幕互动</span>
                <span class="kpi-badge cyan">4轨并发</span>
              </div>
              <div class="kpi-number">{{ formatNumber(biMetrics.total_danmakus) }}</div>
              <div class="kpi-sub">WebSocket 弹幕引擎活跃吞吐</div>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">剧迷精选评论</span>
                <span class="kpi-badge purple">伴读社区</span>
              </div>
              <div class="kpi-number">{{ formatNumber(biMetrics.total_comments) }}</div>
              <div class="kpi-sub">高质量剧情剖析与高能反转讨论</div>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">用户点赞互动</span>
                <span class="kpi-badge pink">好评</span>
              </div>
              <div class="kpi-number">{{ formatNumber(biMetrics.total_likes) }}</div>
              <div class="kpi-sub">短剧精品完播与收藏认可</div>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">注册用户底座</span>
                <span class="kpi-badge indigo">RBAC</span>
              </div>
              <div class="kpi-number">{{ biMetrics.total_users }}</div>
              <div class="kpi-sub">包含普通追剧用户与持权账号</div>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">签约认证创作者</span>
                <span class="kpi-badge green">内容供给</span>
              </div>
              <div class="kpi-number">{{ biMetrics.active_creators }}</div>
              <div class="kpi-sub">夸克短剧上传与分发特权</div>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">持证合规审核员</span>
                <span class="kpi-badge amber">机审中台</span>
              </div>
              <div class="kpi-number">{{ biMetrics.active_reviewers }}</div>
              <div class="kpi-sub">DFA 敏感词拦截复审保障</div>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">待审入驻资质</span>
                <span class="kpi-badge red">双轨待办</span>
              </div>
              <div class="kpi-number">{{ biMetrics.pending_applications }}</div>
              <div class="kpi-sub">创作者与审核员入驻审批流程</div>
            </div>
          </div>

          <!-- ECharts Area Time Series & Holt-Winters Predictive Curves -->
          <div class="chart-block glass-card">
            <div class="chart-header">
              <div class="chart-title-wrap">
                <el-icon class="chart-icon"><TrendCharts /></el-icon>
                <div>
                  <h3 class="chart-heading">全站时序流量趋势与 AI 预测模型</h3>
                  <p class="chart-subtext">基于短视频平台核心算法：Holt-Winters 三次指数平滑（带 95% 置信预测区间）</p>
                </div>
              </div>

              <div class="chart-legend-pills">
                <span class="legend-pill history"><span class="dot history"></span>历史实测播放</span>
                <span class="legend-pill forecast"><span class="dot forecast"></span>AI 算法预测走势</span>
                <span class="legend-pill bound"><span class="dot bound"></span>95% 置信区间带</span>
              </div>
            </div>

            <!-- ECharts DOM container -->
            <div ref="biChartRef" class="echarts-container" id="bi-trend-echart"></div>
          </div>

          <!-- Bass Diffusion Model Viral Potential Drama Ranking -->
          <div class="viral-ranking-block glass-card">
            <div class="block-header">
              <div class="title-wrap">
                <el-icon class="block-icon"><Rank /></el-icon>
                <div>
                  <h3 class="chart-heading">短剧破圈爆款扩散潜力榜 (Bass Diffusion Model)</h3>
                  <p class="chart-subtext">通过创新系数 (p) 与模仿扩散系数 (q) 计算破圈动能与未来 7 天预测增量</p>
                </div>
              </div>
            </div>

            <div class="viral-table-wrap">
              <table class="apple-table">
                <thead>
                  <tr>
                    <th style="width: 70px;">排名</th>
                    <th>短剧作品</th>
                    <th>题材分类</th>
                    <th>总集数</th>
                    <th>历史播放</th>
                    <th>破圈扩散指数</th>
                    <th>破圈梯队</th>
                    <th>未来7天预测增量</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, idx) in viralRankings" :key="item.video_id">
                    <td>
                      <span class="rank-index" :class="'rank-' + (idx + 1)">#{{ idx + 1 }}</span>
                    </td>
                    <td class="font-bold">{{ item.title }}</td>
                    <td><span class="tag-pill">{{ item.category }}</span></td>
                    <td>共 {{ item.total_episodes }} 集</td>
                    <td>{{ formatNumber(item.view_count) }}</td>
                    <td>
                      <div class="score-progress-wrap">
                        <span class="score-val">{{ item.viral_score }}</span>
                        <div class="score-bar"><div class="score-fill" :style="{ width: item.viral_score + '%' }"></div></div>
                      </div>
                    </td>
                    <td>
                      <span class="status-badge" :class="item.badge_type">{{ item.viral_tag }}</span>
                    </td>
                    <td class="growth-text">+{{ formatNumber(item.predicted_next_week_views) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 3-Pillar Panoramic Middle-Platform Intelligence Matrix -->
          <div class="bi-matrix-grid mt-20">
            <!-- 1. RAG 知识中台态势 -->
            <div class="matrix-card glass-card">
              <div class="matrix-header">
                <div class="matrix-title-wrap">
                  <span class="matrix-dot purple"></span>
                  <span class="matrix-heading">RAG 知识检索与评测态势</span>
                </div>
                <span class="matrix-badge purple">工业级模块化</span>
              </div>
              <div class="matrix-stats-row">
                <div class="m-stat-item">
                  <div class="m-stat-label">知识库语料</div>
                  <div class="m-stat-val">{{ ragCenterMetrics.total_corpus }} 部</div>
                </div>
                <div class="m-stat-item">
                  <div class="m-stat-label">结构切片总量</div>
                  <div class="m-stat-val">{{ ragCenterMetrics.total_chunks }} 块</div>
                </div>
                <div class="m-stat-item">
                  <div class="m-stat-label">忠实度均分</div>
                  <div class="m-stat-val green-text">{{ ragCenterMetrics.faithfulness_pct }}%</div>
                </div>
                <div class="m-stat-item">
                  <div class="m-stat-label">答案相关度</div>
                  <div class="m-stat-val green-text">{{ ragCenterMetrics.relevance_pct }}%</div>
                </div>
              </div>
              <div class="matrix-footer-meta">
                <span>Neo4j 图谱实体预估：{{ ragCenterMetrics.graph_entities_estimate }} 节点</span>
                <span class="status-indicator-tag success">健康运行</span>
              </div>
            </div>

            <!-- 2. 九大智能体集群态势 -->
            <div class="matrix-card glass-card">
              <div class="matrix-header">
                <div class="matrix-title-wrap">
                  <span class="matrix-dot blue"></span>
                  <span class="matrix-heading">九大智能体集群调度态势</span>
                </div>
                <span class="matrix-badge blue">Mesh 协同</span>
              </div>
              <div class="matrix-stats-row">
                <div class="m-stat-item">
                  <div class="m-stat-label">在线专家智能体</div>
                  <div class="m-stat-val">{{ agentFleetMetrics.active_agents }} 席</div>
                </div>
                <div class="m-stat-item">
                  <div class="m-stat-label">圆桌研讨会话</div>
                  <div class="m-stat-val">{{ agentFleetMetrics.total_roundtable_sessions }} 场</div>
                </div>
                <div class="m-stat-item">
                  <div class="m-stat-label">活跃桌宠小茜</div>
                  <div class="m-stat-val">{{ agentFleetMetrics.active_pets }} 尊</div>
                </div>
                <div class="m-stat-item">
                  <div class="m-stat-label">中枢响应时延</div>
                  <div class="m-stat-val blue-text">{{ agentFleetMetrics.dispatch_latency_ms }} ms</div>
                </div>
              </div>
              <div class="matrix-footer-meta">
                <span>L1-L4 分级记忆中枢与滑动窗口实时摘要已启用</span>
                <span class="status-indicator-tag success">全量在网</span>
              </div>
            </div>

            <!-- 3. 全域用户与资产运营 -->
            <div class="matrix-card glass-card">
              <div class="matrix-header">
                <div class="matrix-title-wrap">
                  <span class="matrix-dot green"></span>
                  <span class="matrix-heading">全域用户与资产互动态势</span>
                </div>
                <span class="matrix-badge green">真实入库</span>
              </div>
              <div class="matrix-stats-row">
                <div class="m-stat-item">
                  <div class="m-stat-label">VIP 特权会员</div>
                  <div class="m-stat-val">{{ userOpsMetrics.vip_members }} 位</div>
                </div>
                <div class="m-stat-item">
                  <div class="m-stat-label">金币全网流通</div>
                  <div class="m-stat-val amber-text">{{ userOpsMetrics.coin_circulation }} 币</div>
                </div>
                <div class="m-stat-item">
                  <div class="m-stat-label">用户投币打赏</div>
                  <div class="m-stat-val">{{ userOpsMetrics.total_tips_count }} 次</div>
                </div>
                <div class="m-stat-item">
                  <div class="m-stat-label">用户多级收藏</div>
                  <div class="m-stat-val">{{ userOpsMetrics.total_favorites_count }} 部</div>
                </div>
              </div>
              <div class="matrix-footer-meta">
                <span>系统审计事件总览：{{ userOpsMetrics.audit_logs_count }} 条流水</span>
                <span class="status-indicator-tag success">成功率 {{ userOpsMetrics.audit_success_rate }}%</span>
              </div>
            </div>
          </div>

          <!-- ================================================================= -->
          <!-- System Full-Link Audit Trail Cockpit (全链路全用户全操作审计流水追溯) -->
          <!-- ================================================================= -->
          <div class="audit-cockpit-block glass-card mt-20" id="audit-trail-cockpit">
            <div class="block-header audit-header">
              <div class="title-wrap">
                <el-icon class="block-icon"><DocumentChecked /></el-icon>
                <div>
                  <h3 class="chart-heading">全链路全用户全操作审计追溯看板</h3>
                  <p class="chart-subtext">记录系统内认证鉴权、播放流控、RAG问答、Agent协作、管理治理的全生命周期审计事件</p>
                </div>
              </div>

              <div class="audit-stats-summary-pills">
                <span class="audit-pill">24小时动态: <b>{{ auditStats.recent_24h_count }}</b> 条</span>
                <span class="audit-pill success">成功率: <b>{{ auditStats.success_rate }}%</b></span>
                <span class="audit-pill">平均执行延时: <b>{{ auditStats.avg_latency_ms }} ms</b></span>
              </div>
            </div>

            <!-- Multi-Dimensional Filter Toolbar -->
            <div class="audit-filter-bar">
              <div class="filter-item">
                <span class="filter-label">功能模块</span>
                <select v-model="auditQuery.module" class="audit-select" id="select-audit-module" @change="handleAuditSearch">
                  <option value="">全部模块 (All)</option>
                  <option value="auth">认证鉴权 (auth)</option>
                  <option value="player">播放器流控 (player)</option>
                  <option value="rag">RAG知识检索 (rag)</option>
                  <option value="agent_roundtable">智能体协同 (agent_roundtable)</option>
                  <option value="admin_bi">管理驾驶舱 (admin_bi)</option>
                  <option value="pet">灵宠伴看 (pet)</option>
                  <option value="creator_studio">创作者中台 (creator_studio)</option>
                  <option value="coin">金币与经济 (coin)</option>
                </select>
              </div>

              <div class="filter-item">
                <span class="filter-label">执行状态</span>
                <select v-model="auditQuery.status" class="audit-select" id="select-audit-status" @change="handleAuditSearch">
                  <option value="">全部状态 (All)</option>
                  <option value="SUCCESS">成功 (SUCCESS)</option>
                  <option value="FAILED">失败 (FAILED)</option>
                  <option value="WARNING">预警 (WARNING)</option>
                  <option value="BLOCKED">安全拦截 (BLOCKED)</option>
                </select>
              </div>

              <div class="filter-item">
                <span class="filter-label">操作人角色</span>
                <select v-model="auditQuery.user_role" class="audit-select" id="select-audit-role" @change="handleAuditSearch">
                  <option value="">全部角色 (All)</option>
                  <option value="admin">系统管理员 (admin)</option>
                  <option value="creator">创作者 (creator)</option>
                  <option value="user">普通用户 (user)</option>
                  <option value="system">系统自调度 (system)</option>
                  <option value="visitor">未登录访客 (visitor)</option>
                </select>
              </div>

              <div class="filter-search-wrap">
                <input
                  v-model="auditQuery.keyword"
                  class="audit-search-input"
                  id="input-audit-keyword"
                  placeholder="检索摘要、用户名、IP地址、目标ID..."
                  @keyup.enter="handleAuditSearch"
                />
                <button type="button" class="audit-btn-search" id="btn-search-audit" @click="handleAuditSearch">
                  查询
                </button>
              </div>
            </div>

            <!-- Audit Logs Table -->
            <div class="audit-table-wrap mt-10">
              <table class="apple-table" id="table-audit-logs">
                <thead>
                  <tr>
                    <th style="width: 65px;">流水ID</th>
                    <th style="width: 140px;">时间戳</th>
                    <th style="width: 100px;">操作人/角色</th>
                    <th style="width: 110px;">客户端IP</th>
                    <th style="width: 120px;">模块 / 动作</th>
                    <th style="width: 85px;">执行状态</th>
                    <th style="width: 80px;">耗时</th>
                    <th>操作流水审计摘要</th>
                    <th style="width: 90px; text-align: center;">溯源明细</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="auditLogsLoading">
                    <td colspan="9" class="text-center py-20 text-muted">正在检索全链路审计记录...</td>
                  </tr>
                  <tr v-else-if="auditLogsList.length === 0">
                    <td colspan="9" class="text-center py-20 text-muted">暂无匹配的审计追踪记录</td>
                  </tr>
                  <tr v-for="item in auditLogsList" :key="item.id" class="audit-row">
                    <td class="font-mono text-muted">#{{ item.id }}</td>
                    <td class="font-mono text-xs">{{ item.created_at ? item.created_at.slice(0, 19).replace('T', ' ') : '-' }}</td>
                    <td>
                      <div class="user-cell">
                        <span class="user-name">{{ item.username || '匿名/系统' }}</span>
                        <span class="role-sub-badge" :class="item.user_role">{{ item.user_role }}</span>
                      </div>
                    </td>
                    <td class="font-mono text-xs">{{ item.ip_address || '127.0.0.1' }}</td>
                    <td>
                      <div class="module-action-cell">
                        <span class="module-tag">{{ item.module }}</span>
                        <span class="action-tag">{{ item.action }}</span>
                      </div>
                    </td>
                    <td>
                      <span class="status-badge" :class="item.status === 'SUCCESS' ? 'success' : item.status === 'FAILED' ? 'danger' : 'warning'">
                        {{ item.status }}
                      </span>
                    </td>
                    <td class="font-mono text-xs text-muted">{{ item.exec_time_ms }} ms</td>
                    <td class="audit-summary-cell" :title="item.summary">{{ item.summary }}</td>
                    <td style="text-align: center;">
                      <button
                        type="button"
                        class="btn-detail-pill"
                        :id="'btn-audit-detail-' + item.id"
                        @click="viewAuditDetail(item)"
                      >
                        查看JSON
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Pagination Bar -->
            <div class="audit-pagination-bar" v-if="auditLogsTotal > 0">
              <span class="pagination-info">共 {{ auditLogsTotal }} 条全链路流水，当前第 {{ auditQuery.page }} 页</span>
              <div class="pagination-btns">
                <button
                  type="button"
                  class="page-nav-btn"
                  id="btn-audit-prev-page"
                  :disabled="auditQuery.page <= 1"
                  @click="handleAuditPageChange(auditQuery.page - 1)"
                >
                  上一页
                </button>
                <span class="page-indicator">第 {{ auditQuery.page }} 页</span>
                <button
                  type="button"
                  class="page-nav-btn"
                  id="btn-audit-next-page"
                  :disabled="auditQuery.page * auditQuery.page_size >= auditLogsTotal"
                  @click="handleAuditPageChange(auditQuery.page + 1)"
                >
                  下一页
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- Audit Detail JSON Dialog -->
        <el-dialog
          v-model="isAuditDetailDialogOpen"
          title="审计流水结构化溯源明细 (Audit Detail JSON)"
          width="680px"
          class="apple-modal-dialog"
          :destroy-on-close="true"
        >
          <div v-if="selectedAuditDetail" class="audit-modal-body">
            <div class="audit-modal-summary-box">
              <div class="modal-sum-row">
                <span><b>流水编号:</b> #{{ selectedAuditDetail.id }}</span>
                <span><b>记录时间:</b> {{ selectedAuditDetail.created_at }}</span>
                <span><b>执行状态:</b> <span class="status-badge" :class="selectedAuditDetail.status === 'SUCCESS' ? 'success' : 'danger'">{{ selectedAuditDetail.status }}</span></span>
              </div>
              <div class="modal-sum-row mt-6">
                <span><b>操作人:</b> {{ selectedAuditDetail.username }} ({{ selectedAuditDetail.user_role }})</span>
                <span><b>客户端 IP:</b> {{ selectedAuditDetail.ip_address }}</span>
                <span><b>作用域:</b> {{ selectedAuditDetail.module }} / {{ selectedAuditDetail.action }}</span>
              </div>
              <div class="modal-sum-desc mt-6">
                <b>操作描述:</b> {{ selectedAuditDetail.summary }}
              </div>
            </div>

            <div class="audit-json-box mt-12">
              <div class="json-header">
                <span>结构化 Payload / 上下文参数 (detail_json)</span>
                <span class="json-bytes">{{ JSON.stringify(selectedAuditDetail.detail_json || {}).length }} bytes</span>
              </div>
              <pre class="json-content"><code>{{ JSON.stringify(selectedAuditDetail.detail_json || {}, null, 2) }}</code></pre>
            </div>
          </div>
          <template #footer>
            <div class="dialog-footer">
              <button type="button" class="apple-btn-secondary" @click="isAuditDetailDialogOpen = false">
                关闭溯源窗口
              </button>
            </div>
          </template>
        </el-dialog>

        <!-- ================================================================= -->
        <!-- TAB 2: 短剧资产编目 (屏蔽、解蔽、自定义封面、剧照轮播查看、删除)  -->
        <!-- ================================================================= -->
        <section v-if="currentTab === 'dramas'" class="content-section" id="section-dramas">
          <div class="table-card glass-card">
            <div class="table-card-header">
              <div class="search-box">
                <el-icon><Search /></el-icon>
                <input 
                  v-model="dramaSearchKeyword" 
                  placeholder="搜索短剧标题、题材分类..." 
                  class="table-search-input"
                  @input="filterDramas"
                />
              </div>

              <div class="table-header-actions">
                <span class="stat-counter">共编目 {{ filteredDramas.length }} 部短剧</span>
                <button 
                  v-if="selectedDramaIds.length > 0"
                  class="apple-btn-secondary" 
                  style="color: #ff453a; border-color: rgba(255, 69, 58, 0.4);"
                  @click="handleBatchDeleteDramas"
                  id="btn-admin-batch-delete-dramas"
                >
                  <el-icon><Delete /></el-icon>
                  <span>批量删除已选 ({{ selectedDramaIds.length }})</span>
                </button>
                <button class="apple-btn-primary" @click="openSyncDialog">
                  <el-icon><Refresh /></el-icon>
                  <span>同步新剧</span>
                </button>
              </div>
            </div>

            <div class="apple-table-viewport-wrap">
              <table class="apple-table">
                <thead>
                  <tr>
                    <th style="width: 44px; text-align: center;">
                      <input 
                        type="checkbox" 
                        :checked="isAllDramasSelected" 
                        @change="toggleSelectAllDramas" 
                        id="checkbox-select-all-dramas"
                      />
                    </th>
                    <th style="width: 140px;">封面/海报</th>
                    <th>短剧名称</th>
                    <th>题材分类</th>
                    <th>集数</th>
                    <th>播放 / 互动</th>
                    <th>上架状态</th>
                    <th style="width: 260px;">资产管理操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="d in paginatedDramas" :key="d.id" :id="'drama-row-' + d.id" class="table-row drama-card">
                    <td style="text-align: center;">
                      <input 
                        type="checkbox" 
                        :value="d.id" 
                        v-model="selectedDramaIds" 
                        :id="'chk-drama-' + d.id"
                      />
                    </td>
                    <td>
                      <div class="drama-thumb-wrapper" @click="openPosterCarousel(d)">
                        <img 
                          :src="d.effective_cover || d.cover_url || defaultDramaPoster" 
                          @error="(e) => (e.target as HTMLImageElement).src = defaultDramaPoster"
                          class="drama-thumb-img" 
                        />
                        <div v-if="d.extra_images && d.extra_images.length > 1" class="multi-poster-tag" title="包含多张剧照海报">
                          <el-icon :size="10"><Picture /></el-icon>
                          <span>{{ d.extra_images.length }}图</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div class="drama-title-main">{{ d.title }}</div>
                      <div class="drama-synopsis-sub">{{ d.summary || '暂无梗概' }}</div>
                    </td>
                    <td><span class="tag-pill">{{ d.category }}</span></td>
                    <td>共 {{ d.total_episodes }} 集</td>
                    <td>
                      <div class="stats-mini-line">
                        <span>▶ {{ formatNumber(d.view_count) }}</span>
                        <span>赞 {{ formatNumber(d.like_count) }}</span>
                      </div>
                    </td>
                    <td>
                      <span 
                        class="status-badge" 
                        :class="d.status === 'PUBLISHED' ? 'success' : 'warning'"
                        :id="'drama-status-' + d.id"
                      >
                        {{ d.status === 'PUBLISHED' ? '已上架' : '已屏蔽下线' }}
                      </span>
                    </td>
                    <td>
                      <div class="actions-group">
                        <!-- Status Toggle -->
                        <button 
                          class="btn-text-action" 
                          :class="d.status === 'PUBLISHED' ? 'btn-warn' : 'btn-success'"
                          @click="toggleDramaStatus(d)"
                          :id="'btn-toggle-status-' + d.id"
                        >
                          <el-icon><View v-if="d.status !== 'PUBLISHED'" /><Hide v-else /></el-icon>
                          <span>{{ d.status === 'PUBLISHED' ? '屏蔽' : '上架' }}</span>
                        </button>

                        <!-- Edit Metadata & Cover -->
                        <button 
                          class="btn-text-action" 
                          @click="openEditCoverModal(d)"
                          :id="'btn-edit-cover-' + d.id"
                          title="全量编辑短剧元数据与海报"
                        >
                          <el-icon><Edit /></el-icon>
                          <span>全量编辑</span>
                        </button>

                        <!-- Extra Posters preview -->
                        <button 
                          v-if="d.extra_images && d.extra_images.length > 1"
                          class="btn-text-action" 
                          @click="openPosterCarousel(d)"
                        >
                          <el-icon><Picture /></el-icon>
                          <span>剧照</span>
                        </button>

                        <!-- Delete -->
                        <button 
                          class="btn-text-action btn-danger" 
                          @click="handleDeleteDrama(d)"
                          :id="'btn-delete-drama-' + d.id"
                        >
                          <el-icon><Delete /></el-icon>
                          <span>删除</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Dramas Pagination -->
            <div class="table-pagination-row">
              <el-pagination
                v-model:current-page="dramaPage"
                v-model:page-size="dramaPageSize"
                :page-sizes="[10, 20, 50]"
                :total="filteredDramas.length"
                layout="total, sizes, prev, pager, next, jumper"
                id="pagination-dramas"
              />
            </div>
          </div>
        </section>

        <!-- ================================================================= -->
        <!-- TAB 3: 网盘双模同步 (增量跳过已存在 vs 全量重新探测)             -->
        <!-- ================================================================= -->
        <section v-if="currentTab === 'sync'" class="content-section" id="section-sync">
          <div class="sync-dashboard-grid">
            <div class="sync-config-card glass-card">
              <div class="card-header-styled">
                <el-icon class="head-icon"><Refresh /></el-icon>
                <div>
                  <h3 class="chart-heading">夸克网盘短剧直连同步引擎</h3>
                  <p class="chart-subtext">通过 OpenList 驱动直连网盘，支持单剧剧集探测、txt 剧情梗概提取与多剧照轮播</p>
                </div>
              </div>

              <!-- Mode Selection -->
              <div class="sync-mode-selector">
                <label class="mode-radio-box" :class="{ selected: syncMode === 'incremental' }">
                  <input type="radio" v-model="syncMode" value="incremental" />
                  <div class="radio-content">
                    <div class="radio-title-row">
                      <span class="radio-name">1. 增量同步模式 (推荐)</span>
                      <span class="recommend-pill">省服务器负担</span>
                    </div>
                    <p class="radio-desc">系统中已有的短剧不做重复拉取，只探测并映射网盘中新上传的短剧文件，避免资源浪费与服务器过载。</p>
                  </div>
                </label>

                <label class="mode-radio-box" :class="{ selected: syncMode === 'full' }">
                  <input type="radio" v-model="syncMode" value="full" />
                  <div class="radio-content">
                    <div class="radio-title-row">
                      <span class="radio-name">2. 全量重新同步模式</span>
                    </div>
                    <p class="radio-desc">深度扫描网盘所有短剧目录，强制重新解析所有分集、txt 梗概文本与剧照海报并全量入库。</p>
                  </div>
                </label>
              </div>

              <!-- Action button -->
              <div class="sync-action-row">
                <button 
                  type="button" 
                  class="apple-btn-primary big-btn" 
                  id="btn-start-sync-execute"
                  :disabled="isSyncing"
                  @click="executeSync"
                >
                  <el-icon :class="{ 'is-loading': isSyncing }"><Refresh /></el-icon>
                  <span>{{ isSyncing ? '正在与夸克网盘极速同步中...' : '立即启动网盘短剧映射同步' }}</span>
                </button>
              </div>

              <!-- Last sync result banner -->
              <div v-if="syncResult" class="sync-report-card">
                <div class="report-header">
                  <span class="report-status-badge">同步执行完成</span>
                  <span class="report-mode-tag">模式：{{ syncResult.mode === 'incremental' ? '增量跳过已有' : '全量重新探测' }}</span>
                </div>
                <div class="report-stats-grid">
                  <div class="report-stat-item">
                    <span class="num">{{ syncResult.total_synced_dramas }}</span>
                    <span class="label">网盘短剧数</span>
                  </div>
                  <div class="report-stat-item">
                    <span class="num">{{ syncResult.total_episodes }}</span>
                    <span class="label">累计总集数</span>
                  </div>
                  <div class="report-stat-item">
                    <span class="num">{{ syncResult.new_episodes_added }}</span>
                    <span class="label">新写入剧集</span>
                  </div>
                  <div class="report-stat-item">
                    <span class="num">{{ syncResult.skipped_dramas }}</span>
                    <span class="label">跳过已存在剧</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Gateway Status Card -->
            <div class="sync-telemetry-card glass-card">
              <h3 class="chart-heading">网盘直连网关探针</h3>
              <div class="telemetry-list">
                <div class="telem-row">
                  <span class="telem-label">服务协议</span>
                  <span class="telem-val">OpenList Native REST API</span>
                </div>
                <div class="telem-row">
                  <span class="telem-label">网关本地端口</span>
                  <span class="telem-val font-mono">http://127.0.0.1:5244</span>
                </div>
                <div class="telem-row">
                  <span class="telem-label">挂载驱动类型</span>
                  <span class="telem-val">Quark Pan (夸克网盘)</span>
                </div>
                <div class="telem-row">
                  <span class="telem-label">挂载短剧路径</span>
                  <span class="telem-val font-mono">/短剧</span>
                </div>
                <div class="telem-row">
                  <span class="telem-label">元数据解析</span>
                  <span class="telem-val font-bold text-success">已启用 (*.txt 简介 + *.jpg 多海报)</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- ================================================================= -->
        <!-- TAB 4: 首页 5 秒焦点轮播运营调度                                  -->
        <!-- ================================================================= -->
        <section v-if="currentTab === 'carousels'" class="content-section" id="section-carousels">
          <!-- 16:9 WYSIWYG Live Preview Workbench Card -->
          <div class="carousel-workbench-card glass-card">
            <div class="workbench-header">
              <div class="workbench-title-box">
                <el-icon class="head-icon text-primary"><Picture /></el-icon>
                <div>
                  <h3 class="chart-heading">16:9 所见即所得轮播画报工作台</h3>
                  <p class="chart-subtext">选择短剧资产一键提取海报与元数据，实时预览大厅首屏 16:9 渲染效果</p>
                </div>
              </div>
              <div class="workbench-quick-actions">
                <label class="dropdown-label">快捷关联合约短剧：</label>
                <select 
                  id="select-carousel-drama" 
                  class="apple-select workbench-select"
                  v-model="selectedCarouselDramaId" 
                  @change="handleQuickSelectDrama"
                >
                  <option value="">-- 选择短剧生成 16:9 焦点画报 --</option>
                  <option v-for="d in dramaOptionsList" :key="d.id" :value="d.id">
                    《{{ d.title }}》({{ d.category || '短剧' }})
                  </option>
                </select>
                <button class="apple-btn-primary" @click="openCreateCarouselModal" id="btn-create-carousel">
                  <el-icon><Plus /></el-icon>
                  <span>新增轮播焦点</span>
                </button>
              </div>
            </div>

            <!-- WYSIWYG 16:9 Live Preview Card -->
            <div class="carousel-live-preview-grid">
              <div class="carousel-preview-wrapper">
                <div class="carousel-preview-container" id="carousel-preview-16-9">
                  <div class="aspect-16-9-box">
                    <img 
                      v-if="workbenchPreviewCover && !workbenchImgError" 
                      :src="workbenchPreviewCover" 
                      class="preview-bg-img" 
                      @error="workbenchImgError = true" 
                    />
                    <div v-else class="preview-empty-placeholder">
                      <el-icon :size="40"><Picture /></el-icon>
                      <span>请从上方选择短剧或录入 16:9 海报链接</span>
                    </div>
                    <div class="preview-overlay">
                      <span class="preview-tag-badge">{{ workbenchPreviewTag }}</span>
                      <h4 class="preview-title">{{ workbenchPreviewTitle }}</h4>
                      <p class="preview-subtitle">{{ workbenchPreviewSubtitle }}</p>
                    </div>
                  </div>
                </div>
                <div class="preview-ratio-label">
                  <span>16 : 9 标准大屏高清比例 (1920 × 1080 / 1280 × 720)</span>
                  <span class="preview-badge-status">动态即时渲染</span>
                </div>
              </div>

              <div class="workbench-quick-info">
                <h4 class="info-title">轮播焦点运营准则</h4>
                <ul class="info-list">
                  <li>海报建议采用横版 16:9 构图，重要视觉元素居中靠右，左侧保留文案安全区。</li>
                  <li>主标题控制在 16 字以内，副标题精炼概括短剧最强爽点与反转冲突。</li>
                  <li>角标标签推荐使用“本周爆款榜首”、“今日必看”、“独播首发”等强吸引力关键词。</li>
                  <li>支持将所选短剧一键带入下方轮播发布表单，实现秒级排期上线。</li>
                </ul>
                <button 
                  v-if="selectedCarouselDramaId" 
                  class="apple-btn-secondary" 
                  @click="applyWorkbenchToModal"
                >
                  <el-icon><Promotion /></el-icon>
                  <span>将此短剧作为焦点排期入库</span>
                </button>
              </div>
            </div>
          </div>

          <div class="table-card glass-card">
            <div class="table-card-header">
              <div>
                <h3 class="chart-heading">首页焦点轮播图运营调度 (默认 5 秒自播)</h3>
                <p class="chart-subtext">管理大厅首屏推荐位的海报背景、营销文案、关联剧集跳转与展示排序</p>
              </div>
            </div>

            <table class="apple-table">
              <thead>
                <tr>
                  <th style="width: 160px;">轮播海报</th>
                  <th>标题文案</th>
                  <th>副标题</th>
                  <th>角标标签</th>
                  <th>关联短剧 ID</th>
                  <th>排序权重</th>
                  <th>启停状态</th>
                  <th style="width: 160px;">调度操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in carouselsList" :key="c.id" :id="'carousel-row-' + c.id" class="table-row">
                  <td>
                    <img :src="c.cover_url" class="carousel-preview-img" />
                  </td>
                  <td class="font-bold">{{ c.title }}</td>
                  <td class="sub-text-col">{{ c.subtitle }}</td>
                  <td><span class="tag-pill">{{ c.tag }}</span></td>
                  <td class="font-mono text-xs">{{ c.video_id || '未关联' }}</td>
                  <td>{{ c.sort_order }}</td>
                  <td>
                    <el-switch 
                      v-model="c.is_active" 
                      @change="handleToggleCarouselActive(c)" 
                    />
                  </td>
                  <td>
                    <div class="actions-group">
                      <button class="btn-text-action" @click="openEditCarouselModal(c)">
                        <el-icon><Edit /></el-icon>
                        <span>编辑</span>
                      </button>
                      <button class="btn-text-action btn-danger" @click="handleDeleteCarousel(c)">
                        <el-icon><Delete /></el-icon>
                        <span>删除</span>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- ================================================================= -->
        <!-- TAB 4.5: 全员系统公告全流程治理中台 (对标 X & Instagram 官方公告中枢) -->
        <!-- ================================================================= -->
        <section v-if="currentTab === 'announcements'" class="content-section" id="section-announcements">
          <!-- 4 Bento KPI Cards for Announcements -->
          <div class="kpi-grid">
            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">平台公告总数</span>
                <span class="kpi-badge blue">治理</span>
              </div>
              <div class="kpi-number">{{ announcementsList.length }}</div>
              <div class="kpi-sub">包含全员广播与定向治理公告</div>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">已发布广播</span>
                <span class="kpi-badge green">实时在线</span>
              </div>
              <div class="kpi-number">{{ announcementsList.filter(a => a.is_published).length }}</div>
              <div class="kpi-sub">前台用户与顶栏天窗已同步触达</div>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">草稿与已撤回</span>
                <span class="kpi-badge amber">待排期</span>
              </div>
              <div class="kpi-number">{{ announcementsList.filter(a => !a.is_published).length }}</div>
              <div class="kpi-sub">未向普通用户展示的留存文档</div>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">全员平等通知</span>
                <span class="kpi-badge purple">直达触达</span>
              </div>
              <div class="kpi-number">{{ biMetrics.total_users || '全员' }}</div>
              <div class="kpi-sub">发布即刻毫秒级广播至所有用户天窗</div>
            </div>
          </div>

          <!-- Announcements Governance Toolbar & Workbench -->
          <div class="table-card glass-card">
            <div class="table-card-header user-toolbar-header">
              <div>
                <h3 class="chart-heading">全员系统公告治理中心</h3>
                <p class="chart-subtext">支持在线发布、全员广播、内容编辑、撤回草稿与彻底删除，保障社区与管理通知双向畅通</p>
              </div>

              <div class="user-filters-group">
                <div class="search-box">
                  <el-icon><Search /></el-icon>
                  <input 
                    v-model="announcementSearchKeyword" 
                    placeholder="搜索公告标题或内容..." 
                    class="table-search-input"
                    id="input-search-announcements"
                  />
                </div>

                <select 
                  v-model="announcementStatusFilter" 
                  class="apple-select" 
                  id="select-announcement-status"
                >
                  <option value="all">全部发布状态</option>
                  <option value="published">已发布在线</option>
                  <option value="draft">已撤回 / 草稿</option>
                </select>

                <button 
                  v-if="selectedAnnouncementIds.length > 0"
                  class="apple-btn-danger" 
                  id="btn-batch-delete-announcements"
                  @click="handleBatchDeleteAnnouncements"
                >
                  <el-icon><Delete /></el-icon>
                  <span>批量删除 ({{ selectedAnnouncementIds.length }})</span>
                </button>

                <button 
                  class="apple-btn-primary" 
                  id="btn-create-announcement"
                  @click="openCreateAnnouncementModal"
                >
                  <el-icon><Plus /></el-icon>
                  <span>发布系统公告</span>
                </button>
              </div>
            </div>

            <!-- Announcements Table -->
            <table class="apple-table" id="table-announcements">
              <thead>
                <tr>
                  <th style="width: 44px; text-align: center;">
                    <input 
                      type="checkbox" 
                      id="checkbox-select-all-announcements"
                      :checked="isAllAnnouncementsSelected" 
                      @change="toggleSelectAllAnnouncements"
                    />
                  </th>
                  <th style="width: 120px;">标签分类</th>
                  <th style="min-width: 200px;">公告标题</th>
                  <th>公告正文摘要</th>
                  <th style="width: 100px;">发布状态</th>
                  <th style="width: 170px;">发布/更新时间</th>
                  <th style="width: 180px;">治理操作</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="a in filteredAnnouncements" 
                  :key="a.id" 
                  :id="'announcement-row-' + a.id"
                  class="table-row"
                  :class="{ 'row-selected': selectedAnnouncementIds.includes(a.id) }"
                >
                  <td style="text-align: center;">
                    <input 
                      type="checkbox" 
                      :value="a.id" 
                      v-model="selectedAnnouncementIds"
                      :id="'checkbox-announcement-' + a.id"
                    />
                  </td>
                  <td>
                    <span class="tag-pill announcement-tag-badge">{{ a.tag || '系统公告' }}</span>
                  </td>
                  <td class="font-bold text-headline">
                    {{ a.title }}
                  </td>
                  <td class="sub-text-col announcement-content-col" :title="a.content">
                    {{ a.content }}
                  </td>
                  <td>
                    <el-switch 
                      v-model="a.is_published" 
                      @change="handleToggleAnnouncementStatus(a)"
                      :id="'switch-announcement-' + a.id"
                      active-text=""
                      inactive-text=""
                    />
                  </td>
                  <td class="font-mono text-xs">
                    {{ a.updated_at || a.created_at || '刚刚' }}
                  </td>
                  <td>
                    <div class="actions-group">
                      <button 
                        class="btn-text-action" 
                        :id="'btn-edit-announcement-' + a.id"
                        @click="openEditAnnouncementModal(a)"
                      >
                        <el-icon><Edit /></el-icon>
                        <span>编辑</span>
                      </button>
                      <button 
                        class="btn-text-action btn-danger" 
                        :id="'btn-delete-announcement-' + a.id"
                        @click="handleDeleteAnnouncement(a)"
                      >
                        <el-icon><Delete /></el-icon>
                        <span>删除</span>
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="filteredAnnouncements.length === 0">
                  <td colspan="6" class="empty-table-cell">
                    {{ loadingAnnouncements ? '正在拉取系统公告数据...' : '暂无符合条件的系统公告' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- ================================================================= -->
        <!-- TAB 4.5: 金币与会员兑换码资产中心                                   -->
        <!-- ================================================================= -->
        <section v-if="currentTab === 'redemption'" class="content-section" id="section-redemption">
          <!-- 4 Bento KPI Cards for Redemption Codes -->
          <div class="kpi-grid">
            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">待使用激活卡密</span>
                <span class="kpi-badge green">可核销</span>
              </div>
              <div class="kpi-number">{{ redemptionSummary.total_active }}</div>
              <div class="kpi-sub">当前处于有效期内尚未被兑换的卡密</div>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">已成功核销卡密</span>
                <span class="kpi-badge blue">已消费</span>
              </div>
              <div class="kpi-number">{{ redemptionSummary.total_used }}</div>
              <div class="kpi-sub">已被用户兑换并永久锁定防重</div>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">累计兑换发放金币</span>
                <span class="kpi-badge amber">金币池</span>
              </div>
              <div class="kpi-number">+{{ redemptionSummary.total_coins_redeemed }}</div>
              <div class="kpi-sub">通过金币兑换码累计入账总额</div>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-header">
                <span class="kpi-title">累计兑换会员天数</span>
                <span class="kpi-badge purple">VIP 权益</span>
              </div>
              <div class="kpi-number">{{ redemptionSummary.total_vip_days_redeemed }} 天</div>
              <div class="kpi-sub">通过会员兑换码累计激活顺延天数</div>
            </div>
          </div>

          <div class="table-card glass-card">
            <div class="table-card-header user-toolbar-header">
              <div class="user-filters-group">
                <div class="search-box">
                  <el-icon><Search /></el-icon>
                  <input
                    v-model="redemptionSearchKeyword"
                    placeholder="搜索兑换码、批次备注或核销用户..."
                    class="table-search-input"
                    id="input-search-redemption"
                    @input="loadRedemptionCodes"
                  />
                </div>
                <select
                  v-model="redemptionTypeFilter"
                  class="apple-select filter-select"
                  id="select-redemption-type"
                  @change="loadRedemptionCodes"
                >
                  <option value="">全部权益类型</option>
                  <option value="COIN">金币兑换码 (COIN)</option>
                  <option value="VIP">会员兑换码 (VIP)</option>
                </select>
                <select
                  v-model="redemptionStatusFilter"
                  class="apple-select filter-select"
                  id="select-redemption-status"
                  @change="loadRedemptionCodes"
                >
                  <option value="">全部核销状态</option>
                  <option value="ACTIVE">待兑换 (ACTIVE)</option>
                  <option value="USED">已核销 (USED)</option>
                  <option value="REVOKED">已作废 (REVOKED)</option>
                  <option value="EXPIRED">已过期 (EXPIRED)</option>
                </select>
              </div>

              <div class="table-header-actions">
                <button
                  v-if="selectedRedemptionIds.length > 0"
                  type="button"
                  class="apple-btn-secondary"
                  id="btn-batch-revoke-codes"
                  @click="handleBatchRedemptionAction('revoke')"
                >
                  <span>批量作废 ({{ selectedRedemptionIds.length }})</span>
                </button>
                <button
                  v-if="selectedRedemptionIds.length > 0"
                  type="button"
                  class="apple-btn-danger"
                  id="btn-batch-delete-codes"
                  @click="handleBatchRedemptionAction('delete')"
                >
                  <el-icon><Delete /></el-icon>
                  <span>批量删除 ({{ selectedRedemptionIds.length }})</span>
                </button>
                <button
                  type="button"
                  class="apple-btn-secondary"
                  id="btn-copy-all-active-codes"
                  @click="copyAllActiveRedemptionCodes"
                >
                  <span>一键复制可用码</span>
                </button>
                <button
                  type="button"
                  class="apple-btn-primary"
                  id="btn-open-generate-redemption"
                  @click="openGenerateRedemptionDialog"
                >
                  <el-icon><Plus /></el-icon>
                  <span>生成兑换码</span>
                </button>
              </div>
            </div>

            <div class="apple-table-viewport-wrap">
              <table class="apple-table" id="table-redemption-codes">
                <thead>
                  <tr>
                    <th style="width: 44px; text-align: center;">
                      <input
                        type="checkbox"
                        :checked="redemptionCodesList.length > 0 && selectedRedemptionIds.length === redemptionCodesList.length"
                        @change="toggleSelectAllRedemptionCodes"
                      />
                    </th>
                    <th>兑换码 (点击复制)</th>
                    <th>权益类型</th>
                    <th>面额 / 天数</th>
                    <th>当前状态</th>
                    <th>核销用户与时间</th>
                    <th>有效期限</th>
                    <th>批次备注</th>
                    <th class="text-right">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="rc in redemptionCodesList"
                    :key="rc.id"
                    :id="'redemption-row-' + rc.id"
                    class="table-row"
                  >
                    <td style="text-align: center;">
                      <input
                        type="checkbox"
                        :checked="selectedRedemptionIds.includes(rc.id)"
                        @change="toggleRedemptionSelection(rc.id)"
                      />
                    </td>
                    <td>
                      <button
                        type="button"
                        class="voucher-code-pill"
                        :id="'btn-copy-code-' + rc.code"
                        @click="copySingleRedemptionCode(rc.code)"
                        title="点击复制此兑换码"
                      >
                        <span class="font-mono font-bold">{{ rc.code }}</span>
                        <span class="copy-hint">复制</span>
                      </button>
                    </td>
                    <td>
                      <span
                        class="status-pill"
                        :class="rc.code_type === 'COIN' ? 'status-amber' : 'status-purple'"
                      >
                        {{ rc.code_type === 'COIN' ? '金币兑换码' : 'VIP 会员码' }}
                      </span>
                    </td>
                    <td>
                      <strong class="font-mono" :style="rc.code_type === 'COIN' ? 'color: #f59e0b;' : 'color: #a855f7;'">
                        {{ rc.code_type === 'COIN' ? `+${rc.reward_amount} 金币` : `+${rc.reward_amount} 天 VIP` }}
                      </strong>
                    </td>
                    <td>
                      <span
                        class="status-pill"
                        :class="{
                          'status-active': rc.status === 'ACTIVE',
                          'status-info': rc.status === 'USED',
                          'status-banned': rc.status === 'REVOKED' || rc.status === 'EXPIRED'
                        }"
                      >
                        {{ rc.status === 'ACTIVE' ? '待兑换' : rc.status === 'USED' ? '已核销' : rc.status === 'REVOKED' ? '已作废' : '已过期' }}
                      </span>
                    </td>
                    <td>
                      <div v-if="rc.status === 'USED'" class="text-xs">
                        <div class="font-semibold">{{ rc.used_by_username || '已核销用户' }}</div>
                        <div class="text-muted font-mono">{{ rc.used_at }}</div>
                      </div>
                      <span v-else class="text-muted text-xs">尚未核销</span>
                    </td>
                    <td class="font-mono text-xs">{{ rc.expires_at }}</td>
                    <td class="text-xs">{{ rc.remark || '—' }}</td>
                    <td class="text-right">
                      <div class="row-actions justify-end">
                        <button
                          v-if="rc.status === 'ACTIVE'"
                          type="button"
                          class="action-btn warn"
                          :id="'btn-revoke-code-' + rc.id"
                          @click="handleRevokeSingleCode(rc)"
                        >
                          <span>作废</span>
                        </button>
                        <button
                          type="button"
                          class="action-btn danger"
                          :id="'btn-delete-code-' + rc.id"
                          @click="handleDeleteSingleCode(rc)"
                        >
                          <el-icon><Delete /></el-icon>
                          <span>删除</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="redemptionCodesList.length === 0">
                    <td colspan="9" class="empty-table-cell">
                      {{ loadingRedemptionCodes ? '正在加载兑换码数据...' : '暂无符合条件的兑换码记录，请点击右上角「生成兑换码」创建' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>


        <!-- ================================================================= -->
        <!-- TAB 5: 用户与角色 RBAC                                           -->
        <!-- ================================================================= -->
        <section v-if="currentTab === 'users'" class="content-section" id="section-users">
          <div class="table-card glass-card">
            <div class="table-card-header user-toolbar-header">
              <div class="user-filters-group">
                <div class="search-box">
                  <el-icon><Search /></el-icon>
                  <input 
                    v-model="userSearchKeyword" 
                    placeholder="搜索用户名、昵称..." 
                    class="table-search-input"
                    id="input-search-users"
                    @input="loadUsers"
                  />
                </div>

                <select 
                  v-model="userFilterRole" 
                  @change="loadUsers" 
                  class="apple-select" 
                  id="select-filter-role"
                >
                  <option value="ALL">全部系统角色</option>
                  <option value="USER">普通用户 (USER)</option>
                  <option value="CREATOR">短剧创作者 (CREATOR)</option>
                  <option value="REVIEWER">合规审核员 (REVIEWER)</option>
                  <option value="ADMIN">超级管理员 (ADMIN)</option>
                </select>

                <select 
                  v-model="userFilterStatus" 
                  @change="loadUsers" 
                  class="apple-select" 
                  id="select-filter-status"
                >
                  <option value="ALL">全部账号状态</option>
                  <option value="ACTIVE">正常活跃 (ACTIVE)</option>
                  <option value="BANNED">已封禁 (BANNED)</option>
                </select>
              </div>

              <div class="table-header-actions">
                <span class="stat-counter">平台共 {{ userTotalCount }} 名注册用户</span>
                <button 
                  v-if="selectedUserIds.length > 0"
                  class="apple-btn-secondary" 
                  style="color: #ff453a; border-color: rgba(255, 69, 58, 0.4);"
                  @click="handleBatchDeleteUsers"
                  id="btn-admin-batch-delete-users"
                >
                  <el-icon><Delete /></el-icon>
                  <span>批量删除已选 ({{ selectedUserIds.length }})</span>
                </button>
                <button 
                  class="apple-btn-primary" 
                  @click="openAddUserModal" 
                  id="btn-admin-add-user"
                >
                  <el-icon><Plus /></el-icon>
                  <span>新增用户</span>
                </button>
              </div>
            </div>

            <div class="apple-table-viewport-wrap">
              <table class="apple-table">
                <thead>
                  <tr>
                    <th style="width: 44px; text-align: center;">
                      <input 
                        type="checkbox" 
                        :checked="isAllUsersSelected" 
                        @change="toggleSelectAllUsers" 
                        id="checkbox-select-all-users"
                      />
                    </th>
                    <th>用户标识</th>
                    <th>用户昵称</th>
                    <th>系统角色</th>
                    <th>特权资质</th>
                    <th>金币与VIP</th>
                    <th>账号状态</th>
                    <th>注册时间</th>
                    <th style="width: 290px;">用户治理操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="u in usersList" :key="u.id" :id="'user-row-' + u.id" class="table-row">
                    <td style="text-align: center;">
                      <input 
                        type="checkbox" 
                        :value="u.id" 
                        v-model="selectedUserIds" 
                        :id="'chk-user-' + u.id"
                      />
                    </td>
                    <td class="font-bold">{{ u.username }}</td>
                    <td>{{ u.nickname || '-' }}</td>
                    <td><span class="role-badge" :class="u.role.toLowerCase()">{{ getRoleLabel(u.role) }}</span></td>
                    <td>
                      <div class="privilege-tags">
                        <span v-if="u.is_creator" class="priv-tag creator">创作者</span>
                        <span v-if="u.is_reviewer" class="priv-tag reviewer">审核员</span>
                        <span v-if="!u.is_creator && !u.is_reviewer" class="priv-tag guest">普通观众</span>
                      </div>
                    </td>
                    <td>
                      <div class="economy-summary-cell">
                        <span class="coin-tag">{{ u.coins ?? 50 }} 金币</span>
                        <span v-if="u.is_vip" class="vip-tag-active">VIP</span>
                        <span v-else class="vip-tag-none">非VIP</span>
                      </div>
                    </td>
                    <td>
                      <span class="status-badge" :class="u.status === 'ACTIVE' ? 'success' : 'danger'">
                        {{ u.status === 'ACTIVE' ? '正常活跃' : '已封禁' }}
                      </span>
                    </td>
                    <td class="sub-text-col">{{ u.created_at?.slice(0, 10) }}</td>
                    <td>
                      <div class="actions-group">
                        <!-- Edit User Details & Assets -->
                        <button 
                          class="btn-text-action" 
                          @click="openEditUserModal(u)" 
                          :id="'btn-edit-user-' + u.id"
                          title="编辑资料与资产"
                        >
                          <el-icon><Edit /></el-icon>
                          <span>编辑</span>
                        </button>

                        <!-- Change Role -->
                        <button 
                          class="btn-text-action" 
                          @click="openRoleModal(u)" 
                          :id="'btn-change-role-' + u.id"
                          title="调整系统角色"
                        >
                          <el-icon><Switch /></el-icon>
                          <span>调权</span>
                        </button>

                        <!-- Ban / Unban -->
                        <button 
                          class="btn-text-action" 
                          :class="u.status === 'ACTIVE' ? 'btn-warn' : 'btn-success'"
                          @click="toggleUserStatus(u)"
                          :id="'btn-toggle-ban-' + u.id"
                        >
                          <el-icon><Lock v-if="u.status === 'ACTIVE'" /><Unlock v-else /></el-icon>
                          <span>{{ u.status === 'ACTIVE' ? '封禁' : '解封' }}</span>
                        </button>

                        <!-- Hard Delete -->
                        <button 
                          class="btn-text-action btn-danger" 
                          @click="handleDeleteUser(u)" 
                          :id="'btn-delete-user-' + u.id"
                          title="物理级联删除"
                        >
                          <el-icon><Delete /></el-icon>
                          <span>删除</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Standard Pagination -->
            <div class="table-pagination-row">
              <el-pagination
                v-model:current-page="userPage"
                v-model:page-size="userPageSize"
                :page-sizes="[10, 20, 50, 100]"
                :total="userTotalCount"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="loadUsers"
                @current-change="loadUsers"
                id="pagination-users"
              />
            </div>
          </div>
        </section>

        <!-- ================================================================= -->
        <!-- TAB 6: 资质双轨审批 (创作者 / 审核员入驻)                         -->
        <!-- ================================================================= -->
        <section v-if="currentTab === 'applications'" class="content-section" id="section-applications">
          <div class="dual-subtabs-row">
            <button 
              class="subtab-btn" 
              :class="{ active: applicationSubTab === 'creators' }"
              @click="applicationSubTab = 'creators'"
              id="subtab-creators"
            >
              <span>短剧创作者入驻申请 ({{ pendingCreators.length }})</span>
            </button>
            <button 
              class="subtab-btn" 
              :class="{ active: applicationSubTab === 'reviewers' }"
              @click="applicationSubTab = 'reviewers'"
              id="subtab-reviewers"
            >
              <span>合规审核员资质申请 ({{ pendingReviewers.length }})</span>
            </button>
          </div>

          <div class="table-card glass-card">
            <table class="apple-table">
              <thead>
                <tr>
                  <th>申请用户</th>
                  <th>申请类型</th>
                  <th>资质陈述 / 作品履历</th>
                  <th>申请时间</th>
                  <th>审批状态</th>
                  <th style="width: 200px;">审批决策</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="app in (applicationSubTab === 'creators' ? pendingCreators : pendingReviewers)" 
                  :key="app.user_id"
                  :id="'app-row-' + app.user_id"
                >
                  <td class="font-bold">{{ app.username }}</td>
                  <td>{{ applicationSubTab === 'creators' ? '短剧创作者' : '持证审核员' }}</td>
                  <td class="sub-text-col">{{ app.bio || '无附加陈述' }}</td>
                  <td>{{ app.applied_at?.slice(0, 16) }}</td>
                  <td><span class="status-badge warning">待审批</span></td>
                  <td>
                    <div class="actions-group">
                      <button 
                        class="apple-btn-primary btn-sm" 
                        @click="handleApproveApplication(app)"
                        :id="'btn-approve-' + app.user_id"
                      >
                        <el-icon><Check /></el-icon>
                        <span>批准入驻</span>
                      </button>
                      <button 
                        class="apple-btn-secondary btn-sm" 
                        @click="handleRejectApplication(app)"
                        :id="'btn-reject-' + app.user_id"
                      >
                        <el-icon><Close /></el-icon>
                        <span>驳回</span>
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="(applicationSubTab === 'creators' ? pendingCreators : pendingReviewers).length === 0">
                  <td colspan="6" class="empty-table-cell">暂无待处理的入驻资质申请</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- ================================================================= -->
        <!-- TAB 7: 互动合规风控 (工单流、敏感词库、弹幕与评论审查)            -->
        <!-- ================================================================= -->
        <section v-if="currentTab === 'contents'" class="content-section moderation-main-section" id="section-contents">
          <!-- 顶部子标签导航 -->
          <div class="dual-subtabs-row">
            <button 
              class="subtab-btn" 
              :class="{ active: contentSubTab === 'queue' }"
              @click="switchContentSubTab('queue')"
              id="subtab-review-queue"
            >
              <span>机审待办工单 ({{ reviewQueueTotal }})</span>
            </button>
            <button 
              class="subtab-btn" 
              :class="{ active: contentSubTab === 'lexicon' }"
              @click="switchContentSubTab('lexicon')"
              id="subtab-sensitive-lexicon"
            >
              <span>DFA 敏感词库 ({{ sensitiveWordsTotal }})</span>
            </button>
            <button 
              class="subtab-btn" 
              :class="{ active: contentSubTab === 'danmakus' }"
              @click="switchContentSubTab('danmakus')"
              id="subtab-danmakus"
            >
              <span>弹幕机审列表 ({{ danmakuTotal }})</span>
            </button>
            <button 
              class="subtab-btn" 
              :class="{ active: contentSubTab === 'comments' }"
              @click="switchContentSubTab('comments')"
              id="subtab-comments"
            >
              <span>剧迷评论列表 ({{ commentTotal }})</span>
            </button>
            <button 
              class="subtab-btn" 
              :class="{ active: contentSubTab === 'agent4_hitl' }"
              @click="switchContentSubTab('agent4_hitl')"
              id="subtab-agent4-hitl"
            >
              <span>4号风控人机回环 ({{ agent4Interrupts.length }})</span>
            </button>
            <button 
              class="subtab-btn" 
              :class="{ active: contentSubTab === 'inspection_history' }"
              @click="switchContentSubTab('inspection_history')"
              id="subtab-inspection-history"
            >
              <span>4号巡检检测记录 ({{ inspectionHistoryTotal }})</span>
            </button>
          </div>

          <!-- 动态进度条 HUD 浮层 (Apple 极简微光卡片) -->
          <transition name="apple-modal-fade">
            <div v-if="isInspectingInteractions" class="inspect-progress-hud glass-card" id="agent4-progress-hud">
              <div class="progress-hud-header">
                <div class="hud-indicator-dot pulse"></div>
                <span class="hud-title font-bold">4号合规审片官全域深度巡检中</span>
                <span class="hud-percent font-mono">{{ inspectProgress }}%</span>
              </div>
              <el-progress 
                :percentage="inspectProgress" 
                :stroke-width="6" 
                :show-text="false" 
                status="primary"
                class="mt-8"
              />
              <p class="hud-stage-desc mt-6">{{ inspectProgressStage }}</p>
            </div>
          </transition>


          <!-- SUBTAB 1: 机审待办工单流 -->
          <div v-if="contentSubTab === 'queue'" class="content-moderation-card glass-card" id="card-review-queue">
            <div class="table-card-header">
              <div>
                <h3 class="chart-heading">社区内容风控工单待办流</h3>
                <p class="chart-subtext">由 DFA 自动状态机与 4号合规官实时拦截挂起的违规发言，支持审核员 1 键放行或驳回清理</p>
              </div>
              <div class="header-action-wrap">
                <span class="stat-counter">待审工单 {{ reviewQueueTotal }} 笔</span>
                <button class="apple-btn-secondary btn-sm" @click="loadReviewQueue(1)">
                  <el-icon><Refresh /></el-icon>
                  <span>刷新</span>
                </button>
              </div>
            </div>

            <!-- 滑动窗口滚动容器 -->
            <div class="apple-table-scroll-window">
              <table class="apple-table">
                <thead>
                  <tr>
                    <th>违规类型</th>
                    <th>所属短剧</th>
                    <th>违规内容与判定依据</th>
                    <th>命中敏感词</th>
                    <th>风险等级</th>
                    <th>提交时间</th>
                    <th style="width: 200px;">合规裁决</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in pagedReviewQueueList" :key="item.id" :id="'review-row-' + item.id">
                    <td>
                      <span class="priv-tag" :class="item.target_type === 'DANMAKU' ? 'creator' : 'reviewer'">
                        {{ item.target_type === 'DANMAKU' ? '弹幕' : '评论' }}
                      </span>
                    </td>
                    <td class="font-bold">{{ item.video_title }}</td>
                    <td>
                      <div class="violation-reason-cell">
                        <span class="raw-snippet">{{ item.raw_content || item.violation_reason }}</span>
                      </div>
                    </td>
                    <td>
                      <div class="matched-words-wrap">
                        <span v-for="w in item.matched_words" :key="w" class="risk-pill-mini high">{{ w }}</span>
                        <span v-if="!item.matched_words?.length" class="sub-text-col">-</span>
                      </div>
                    </td>
                    <td>
                      <span class="status-badge" :class="item.risk_level === 'HIGH' ? 'danger' : 'warning'">
                        {{ item.risk_level === 'HIGH' ? '高风险' : '中风险' }}
                      </span>
                    </td>
                    <td class="sub-text-col">{{ item.created_at }}</td>
                    <td>
                      <div class="actions-group">
                        <button 
                          class="apple-btn-secondary btn-sm" 
                          @click="handleReviewDecision(item.id, 'APPROVED')"
                          :id="'btn-approve-review-' + item.id"
                        >
                          <el-icon><Check /></el-icon>
                          <span>放行</span>
                        </button>
                        <button 
                          class="apple-btn-primary btn-sm btn-danger" 
                          @click="handleReviewDecision(item.id, 'REJECTED')"
                          :id="'btn-reject-review-' + item.id"
                        >
                          <el-icon><Delete /></el-icon>
                          <span>驳回删除</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="reviewQueueList.length === 0">
                    <td colspan="7" class="empty-table-cell">当前暂无待处理的风控违规工单，社区环境良好</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 分页栏 -->
            <div class="moderation-pagination-footer" v-if="reviewQueueTotal > 0">
              <span class="pagination-summary">共 {{ reviewQueueTotal }} 笔工单 (第 {{ reviewQueuePage }} 页)</span>
              <el-pagination
                v-model:current-page="reviewQueuePage"
                v-model:page-size="reviewQueuePageSize"
                :page-sizes="[10, 20, 50]"
                layout="sizes, prev, pager, next"
                :total="reviewQueueTotal"
                small
              />
            </div>
          </div>

          <!-- SUBTAB 2: DFA 敏感词库治理 & 实时沙盒 -->
          <div v-if="contentSubTab === 'lexicon'" class="lexicon-composite-grid" id="card-sensitive-lexicon">
            <!-- Left: Lexicon Table -->
            <div class="content-moderation-card glass-card">
              <div class="table-card-header">
                <div>
                  <h3 class="chart-heading">DFA 前缀树敏感词库</h3>
                  <p class="chart-subtext">实时同步 MySQL 与内存 Trie 树，支持添加自定义敏感词及分类治理</p>
                </div>
                <div class="header-action-wrap">
                  <button 
                    class="apple-btn-secondary proposal-trigger-btn" 
                    @click="openWordProposalsDrawer" 
                    id="btn-open-proposals-drawer"
                  >
                    <el-icon><Opportunity /></el-icon>
                    <span>AI 待审自迭代词单</span>
                    <span v-if="proposalsPendingCount > 0" class="proposal-count-pill">{{ proposalsPendingCount }}</span>
                  </button>
                  <button class="apple-btn-primary" @click="openAddWordModal" id="btn-add-sensitive-word">
                    <el-icon><Plus /></el-icon>
                    <span>录入敏感词</span>
                  </button>
                </div>
              </div>

              <!-- 分类统计胶囊栏 -->
              <div class="category-pills-row">
                <button 
                  v-for="cat in ['ALL', '违禁', '涉政', '暴恐', '涉黄', '辱骂', '广告']" 
                  :key="cat"
                  class="category-pill-btn"
                  :class="{ active: sensitiveWordCategory === cat }"
                  @click="handleCategoryPillClick(cat)"
                >
                  <span class="pill-title">{{ cat === 'ALL' ? '全部违规词' : cat }}</span>
                  <span class="pill-count-badge">{{ sensitiveWordCategoriesStat[cat] || 0 }}</span>
                </button>
              </div>

              <!-- 搜索与等级筛选栏 -->
              <div class="lexicon-filters-row">
                <input 
                  v-model="sensitiveWordSearch" 
                  type="text" 
                  class="apple-input search-input" 
                  placeholder="搜索敏感词内容..." 
                  @input="loadSensitiveWords(1)"
                  id="input-search-word"
                />
                <select v-model="sensitiveWordLevel" class="apple-select" @change="loadSensitiveWords(1)">
                  <option value="ALL">全部风险等级</option>
                  <option value="HIGH">高风险 (HIGH)</option>
                  <option value="MEDIUM">中风险 (MEDIUM)</option>
                  <option value="LOW">低风险 (LOW)</option>
                </select>
              </div>

              <!-- 滑动窗口表格滚动区 -->
              <div class="apple-table-scroll-window">
                <table class="apple-table">
                  <thead>
                    <tr>
                      <th>敏感词条</th>
                      <th>分类类别</th>
                      <th>风险等级</th>
                      <th>录入时间</th>
                      <th style="width: 100px;">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="word in sensitiveWordsList" :key="word.id" :id="'word-row-' + word.id">
                      <td class="font-bold font-mono">{{ word.word }}</td>
                      <td><span class="priv-tag creator">{{ word.category }}</span></td>
                      <td>
                        <span class="status-badge" :class="word.level === 'HIGH' ? 'danger' : 'warning'">
                          {{ word.level }}
                        </span>
                      </td>
                      <td class="sub-text-col">{{ word.created_at }}</td>
                      <td>
                        <button 
                          class="btn-text-action btn-danger" 
                          @click="handleDeleteSensitiveWord(word)"
                          :id="'btn-del-word-' + word.id"
                        >
                          <el-icon><Delete /></el-icon>
                          <span>删除</span>
                        </button>
                      </td>
                    </tr>
                    <tr v-if="sensitiveWordsList.length === 0">
                      <td colspan="5" class="empty-table-cell">暂无该分类下的敏感词记录</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 分页栏 -->
              <div class="moderation-pagination-footer" v-if="sensitiveWordsTotal > 0">
                <span class="pagination-summary">共 {{ sensitiveWordsTotal }} 条敏感词 (第 {{ sensitiveWordPage }} 页)</span>
                <el-pagination
                  v-model:current-page="sensitiveWordPage"
                  v-model:page-size="sensitiveWordPageSize"
                  :page-sizes="[10, 20, 50]"
                  layout="sizes, prev, pager, next"
                  :total="sensitiveWordsTotal"
                  @current-change="loadSensitiveWords"
                  @size-change="loadSensitiveWords(1)"
                  small
                />
              </div>
            </div>

            <!-- Right: DFA Live Testing Sandbox -->
            <div class="content-moderation-card glass-card dfa-sandbox-card" id="card-dfa-sandbox">
              <div class="card-header-styled">
                <el-icon class="head-icon"><Check /></el-icon>
                <div>
                  <h3 class="chart-heading">DFA 引擎实时匹配沙盒</h3>
                  <p class="chart-subtext">输入测试语句，即时检验 DFA 自动机匹配速度与星号脱敏输出</p>
                </div>
              </div>

              <div class="sandbox-body">
                <label class="form-label">待测文案</label>
                <textarea 
                  v-model="dfaTestText" 
                  class="apple-textarea" 
                  rows="4" 
                  placeholder="例如：这部短剧太好看了，但是有些违禁词需要测试，看看能否精准拦截..."
                  id="textarea-dfa-test"
                ></textarea>

                <button 
                  class="apple-btn-primary full-width" 
                  :disabled="!dfaTestText.trim() || dfaTesting" 
                  @click="runDfaTest"
                  id="btn-run-dfa-test"
                >
                  <el-icon :class="{ 'is-loading': dfaTesting }"><Refresh /></el-icon>
                  <span>{{ dfaTesting ? '检测中...' : '立即运行 DFA 匹配检测' }}</span>
                </button>

                <!-- Sandbox Output Card -->
                <div v-if="dfaTestResult" class="sandbox-result-box" :class="{ 'is-violation': dfaTestResult.has_violation }" id="dfa-test-result-box">
                  <div class="result-status-row">
                    <span class="status-badge" :class="dfaTestResult.has_violation ? 'danger' : 'success'">
                      {{ dfaTestResult.has_violation ? '命中违禁词！' : '检测通过（安全无违规）' }}
                    </span>
                    <span v-if="dfaTestResult.has_violation" class="risk-tag-text">
                      最高等级: {{ dfaTestResult.max_risk_level }}
                    </span>
                  </div>

                  <div class="result-detail-line" v-if="dfaTestResult.has_violation">
                    <span class="detail-label">命中违规词条：</span>
                    <span v-for="w in dfaTestResult.matched_words" :key="w" class="risk-pill-mini high">{{ w }}</span>
                  </div>

                  <div class="result-detail-line">
                    <span class="detail-label">自动脱敏输出：</span>
                    <span class="sanitized-code">{{ dfaTestResult.sanitized_text }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- SUBTAB 3: 弹幕机审列表 -->
          <div v-if="contentSubTab === 'danmakus'" class="content-moderation-card glass-card">
            <div class="table-card-header">
              <div style="display: flex; gap: 12px; align-items: center;">
                <input
                  v-model="danmakuSearchQuery"
                  type="text"
                  placeholder="搜索弹幕内容/关键词..."
                  class="apple-input"
                  style="width: 260px;"
                  @keyup.enter="fetchDanmakus(1)"
                />
                <button class="btn-action" @click="fetchDanmakus(1)">
                  <el-icon><Search /></el-icon>
                  <span>筛选</span>
                </button>
              </div>
              <div class="header-action-wrap">
                <button
                  id="btn-agent4-inspect-danmakus"
                  class="apple-btn-primary btn-radar"
                  :disabled="isInspectingInteractions"
                  @click="triggerAgent4BatchInspect('danmaku')"
                >
                  <el-icon :class="{ 'is-loading': isInspectingInteractions }"><Aim /></el-icon>
                  <span>{{ isInspectingInteractions ? '4号合规官全域巡检中...' : '4号智能体一键批量巡检' }}</span>
                </button>
                <button
                  id="btn-batch-delete-danmakus"
                  class="btn-action btn-danger"
                  :disabled="selectedDanmakuIds.length === 0"
                  @click="handleBatchDeleteDanmakus"
                >
                  <el-icon><Delete /></el-icon>
                  <span>批量下架 ({{ selectedDanmakuIds.length }})</span>
                </button>
              </div>
            </div>

            <!-- 滑动窗口表格滚动区 -->
            <div class="apple-table-scroll-window">
              <table class="apple-table">
                <thead>
                  <tr>
                    <th style="width: 40px;">
                      <input
                        type="checkbox"
                        :checked="selectedDanmakuIds.length > 0 && selectedDanmakuIds.length === pagedDanmakusList.length"
                        @change="toggleSelectAllDanmakus"
                      />
                    </th>
                    <th>弹幕内容</th>
                    <th>发送剧迷</th>
                    <th>所属短剧</th>
                    <th>集数</th>
                    <th>时间轴</th>
                    <th>发送时间</th>
                    <th style="width: 120px;">合规处置</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="dm in pagedDanmakusList" :key="dm.id">
                    <td>
                      <input
                        type="checkbox"
                        :value="dm.id"
                        v-model="selectedDanmakuIds"
                      />
                    </td>
                    <td class="font-bold">{{ dm.content }}</td>
                    <td>{{ dm.user_name }}</td>
                    <td>{{ dm.video_title }}</td>
                    <td>{{ dm.episode_title }}</td>
                    <td>{{ (dm.timestamp || 0).toFixed(1) }}s</td>
                    <td class="sub-text-col">{{ dm.created_at?.slice(0, 16) }}</td>
                    <td>
                      <button class="btn-text-action btn-danger" @click="handleDeleteDanmaku(dm.id)">
                        <el-icon><Delete /></el-icon>
                        <span>删除违规</span>
                      </button>
                    </td>
                  </tr>
                  <tr v-if="danmakusList.length === 0">
                    <td colspan="8" class="empty-table-cell">暂无弹幕记录</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 分页栏 -->
            <div class="moderation-pagination-footer" v-if="danmakuTotal > 0">
              <span class="pagination-summary">共 {{ danmakuTotal }} 条弹幕 (第 {{ danmakuPage }} 页)</span>
              <el-pagination
                v-model:current-page="danmakuPage"
                v-model:page-size="danmakuPageSize"
                :page-sizes="[10, 20, 50]"
                layout="sizes, prev, pager, next"
                :total="danmakuTotal"
                small
              />
            </div>
          </div>

          <!-- SUBTAB 4: 剧迷评论列表 -->
          <div v-if="contentSubTab === 'comments'" class="content-moderation-card glass-card">
            <div class="table-card-header">
              <div style="display: flex; gap: 12px; align-items: center;">
                <input
                  v-model="commentSearchQuery"
                  type="text"
                  placeholder="搜索评论内容/发表用户..."
                  class="apple-input"
                  style="width: 260px;"
                  @keyup.enter="fetchComments(1)"
                />
                <button class="btn-action" @click="fetchComments(1)">
                  <el-icon><Search /></el-icon>
                  <span>筛选</span>
                </button>
              </div>
              <div class="header-action-wrap">
                <button
                  id="btn-agent4-inspect-comments"
                  class="apple-btn-primary btn-radar"
                  :disabled="isInspectingInteractions"
                  @click="triggerAgent4BatchInspect('comment')"
                >
                  <el-icon :class="{ 'is-loading': isInspectingInteractions }"><Aim /></el-icon>
                  <span>{{ isInspectingInteractions ? '4号合规官全域巡检中...' : '4号智能体一键批量巡检' }}</span>
                </button>
              </div>
            </div>

            <!-- 滑动窗口表格滚动区 -->
            <div class="apple-table-scroll-window">
              <table class="apple-table">
                <thead>
                  <tr>
                    <th>评论内容</th>
                    <th>剧迷</th>
                    <th>短剧作品</th>
                    <th>发表时间</th>
                    <th style="width: 120px;">合规处置</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="cm in pagedCommentsList" :key="cm.id">
                    <td class="font-bold">{{ cm.content }}</td>
                    <td>{{ cm.user_name }}</td>
                    <td>{{ cm.video_title }}</td>
                    <td class="sub-text-col">{{ cm.created_at?.slice(0, 16) }}</td>
                    <td>
                      <button class="btn-text-action btn-danger" @click="handleDeleteComment(cm.id)">
                        <el-icon><Delete /></el-icon>
                        <span>删除违规</span>
                      </button>
                    </td>
                  </tr>
                  <tr v-if="commentsList.length === 0">
                    <td colspan="5" class="empty-table-cell">暂无评论记录</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 分页栏 -->
            <div class="moderation-pagination-footer" v-if="commentTotal > 0">
              <span class="pagination-summary">共 {{ commentTotal }} 条评论 (第 {{ commentPage }} 页)</span>
              <el-pagination
                v-model:current-page="commentPage"
                v-model:page-size="commentPageSize"
                :page-sizes="[10, 20, 50]"
                layout="sizes, prev, pager, next"
                :total="commentTotal"
                small
              />
            </div>
          </div>
        
          <!-- SUBTAB 5: 4号违规词风控智能体 · 人机回环审批台 (LangGraph interrupt & resume) -->
          <div v-if="contentSubTab === 'agent4_hitl'" class="agent4-subtab-container" id="subtab-container-agent4">
            <!-- 4号智能体专属工作台卡片 -->
            <div class="glass-card agent4-workspace-card mb-16" id="card-agent4-workspace">
              <div class="agent4-card-header">
                <div class="agent4-identity-box">
                  <span class="agent-pod-tag">AGENT 04 · MODERATION POD</span>
                  <h3 class="agent4-title">合规审片官 · 违规词与内容安全风控智能体</h3>
                  <p class="agent4-desc">
                    集成全域敏感词拦截网络、DFA 有限状态机与 LLM 深度毒性研判引擎，提供人机回环 (HITL) 决策与全模态剧本安全质检。
                  </p>
                </div>
                <div class="agent4-actions-box">
                  <button
                    type="button"
                    class="btn-primary flex items-center gap-6"
                    id="btn-open-agent4-chat"
                    @click="openAgent4Chat()"
                  >
                    <el-icon><ChatLineSquare /></el-icon>
                    <span>与 4号合规审片官对话 (支持传附件/剧本图片)</span>
                  </button>
                </div>
              </div>

              <!-- 快速风控送审交互区 -->
              <div class="agent4-quick-audit-box mt-12">
                <div class="audit-input-bar">
                  <input
                    v-model="agent4QuickAuditText"
                    type="text"
                    class="apple-input flex-1"
                    id="input-agent4-quick-audit"
                    placeholder="输入待审弹幕、敏感台词或剧本片段，让 4 号智能体进行实时 AI 毒性研判..."
                    @keyup.enter="runAgent4QuickAudit"
                  />
                  <button
                    type="button"
                    class="btn-secondary ml-8"
                    id="btn-agent4-quick-audit"
                    :disabled="isAgent4QuickAuditing || !agent4QuickAuditText.trim()"
                    @click="runAgent4QuickAudit"
                  >
                    {{ isAgent4QuickAuditing ? '智能研判中...' : '快速 AI 质检' }}
                  </button>
                  <button
                    type="button"
                    class="btn-primary ml-8"
                    id="btn-agent4-open-with-text"
                    :disabled="!agent4QuickAuditText.trim()"
                    @click="openAgent4Chat(agent4QuickAuditText)"
                  >
                    打开 4号合规审片官全屏工作台
                  </button>
                </div>

                <!-- 快速研判结果展示区 -->
                <div v-if="agent4QuickAuditResult" class="audit-result-display mt-10">
                  <div class="result-badge-row">
                    <span class="status-pill" :class="agent4QuickAuditResult.risk_level === 'HIGH' ? 'err' : (agent4QuickAuditResult.risk_level === 'MEDIUM' ? 'warn' : 'ok')">
                      风险等级: {{ agent4QuickAuditResult.risk_level || '安全' }}
                    </span>
                    <span class="meta-time ml-8">研判耗时: {{ agent4QuickAuditResult.cost_ms || 45 }}ms</span>
                  </div>
                  <div class="result-reason-text mt-6">
                    {{ agent4QuickAuditResult.reason }}
                  </div>
                </div>
              </div>
            </div>

            <!-- 下方人机回环工单流表格 -->
            <div class="content-moderation-card glass-card" id="card-agent4-hitl">
              <div class="table-card-header">
                <div>
                  <h3 class="chart-heading">4 号违规词风控智能体 · 人机回环审批台 (LangGraph interrupt & Command(resume))</h3>
                  <p class="chart-subtext">当弹幕或评论风险分处于 30~85 灰色区间时自动挂起至此，由审核员执行放行或拦截。</p>
                </div>
                <button class="btn-primary" @click="fetchAgent4Interrupts">刷新待审队列</button>
              </div>

              <div class="apple-table-scroll-window">
                <table class="apple-table" id="table-hitl-interrupts">
                  <thead>
                    <tr>
                      <th>挂起单号</th>
                      <th>来源</th>
                      <th>发布用户</th>
                      <th>待审弹幕/评论内容</th>
                      <th>AI 风险评分 & 原因</th>
                      <th>当前状态</th>
                      <th>人工裁决操作 (Command(resume))</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in pagedAgent4Interrupts" :key="item.interrupt_id">
                      <td class="mono-cell">{{ item.interrupt_id.slice(0, 8) }}</td>
                      <td>{{ item.source_type }}</td>
                      <td>{{ item.username }}</td>
                      <td class="strong-cell">{{ item.content_text }}</td>
                      <td>
                        <span class="status-pill warn">{{ item.risk_score }} 分</span>
                        <span class="muted-txt ml-4">{{ item.risk_reason }}</span>
                      </td>
                      <td>
                        <span class="status-pill" :class="item.status === 'APPROVED' ? 'ok' : (item.status === 'REJECTED' ? 'err' : 'warn')">
                          {{ item.status }}
                        </span>
                      </td>
                      <td>
                        <div v-if="item.status === 'PENDING'" class="btn-row">
                          <button
                            type="button"
                            class="btn-primary"
                            :id="'btn-approve-' + item.interrupt_id"
                            @click="handleResumeAgent4Interrupt(item.interrupt_id, 'APPROVE')"
                          >
                            批准放行 (APPROVE)
                          </button>
                          <button
                            type="button"
                            class="btn-danger ml-8"
                            :id="'btn-reject-' + item.interrupt_id"
                            @click="handleResumeAgent4Interrupt(item.interrupt_id, 'REJECT')"
                          >
                            违规拦截 (REJECT)
                          </button>
                        </div>
                        <span v-else class="muted-txt">由 {{ item.reviewer_username }} 裁决完毕</span>
                      </td>
                    </tr>
                    <tr v-if="!agent4Interrupts?.length">
                      <td colspan="7" class="empty-cell" style="text-align: center; padding: 32px; color: var(--apple-text-sub);">
                        当前暂无挂起待审的灰色地带单据 (系统运行平稳，风险评分处于安全阈值内)
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 人机回环分页栏 -->
              <div class="hitl-pagination-bar">
                <span class="pagination-info muted-txt">共 {{ agent4Interrupts.length }} 条人机回环待审工单 (当前第 {{ hitlCurrentPage }} 页)</span>
                <el-pagination
                  v-model:current-page="hitlCurrentPage"
                  v-model:page-size="hitlPageSize"
                  :page-sizes="[5, 10, 20]"
                  layout="sizes, prev, pager, next"
                  :total="agent4Interrupts.length"
                  small
                />
              </div>
            </div>
          </div>

          <!-- SUBTAB 6: 4号巡检检测记录 -->
          <div v-if="contentSubTab === 'inspection_history'" class="content-moderation-card glass-card" id="card-inspection-history">
            <div class="table-card-header">
              <div>
                <h3 class="chart-heading">4号合规审片官 · 全域巡检检测历史</h3>
                <p class="chart-subtext">自动存档每次弹幕与评论巡检结果快照、命中违规数、新型词建议及大模型状态，支持历史报告回放</p>
              </div>
              <div class="header-action-wrap">
                <button class="apple-btn-secondary btn-sm" @click="fetchInspectionHistory(1)" id="btn-refresh-inspection-history">
                  <el-icon><Refresh /></el-icon>
                  <span>刷新记录</span>
                </button>
              </div>
            </div>

            <!-- 滑动窗口表格滚动容器 -->
            <div class="apple-table-scroll-window">
              <table class="apple-table" id="table-inspection-history">
                <thead>
                  <tr>
                    <th>批次号</th>
                    <th>巡检对象</th>
                    <th>送检总数</th>
                    <th>命中违规</th>
                    <th>新型词建议</th>
                    <th>研判耗时</th>
                    <th>模型状态</th>
                    <th>巡检时间</th>
                    <th style="width: 140px;">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in inspectionHistoryList" :key="item.id" class="inspection-history-row">
                    <td class="font-mono font-bold">{{ item.batch_id }}</td>
                    <td>
                      <span class="status-badge" :class="item.target_type === 'danmaku' ? 'info' : 'primary'">
                        {{ item.target_type === 'danmaku' ? '弹幕' : '剧迷评论' }}
                      </span>
                    </td>
                    <td>{{ item.total_inspected }} 条</td>
                    <td>
                      <span class="status-badge" :class="item.violation_count > 0 ? 'danger' : 'success'">
                        {{ item.violation_count }} 条违规
                      </span>
                    </td>
                    <td>{{ item.suggested_words_count }} 个</td>
                    <td class="font-mono">{{ item.cost_ms }}ms</td>
                    <td>
                      <span class="status-badge" :class="item.llm_status.includes('TIMEOUT') ? 'warning' : 'success'">
                        {{ item.llm_status }}
                      </span>
                    </td>
                    <td class="sub-text-col">{{ item.created_at }}</td>
                    <td>
                      <button class="btn-text-action btn-primary btn-view-report" @click="handleViewHistoricalReport(item.id)">
                        <el-icon><Document /></el-icon>
                        <span>查看报告</span>
                      </button>
                    </td>
                  </tr>
                  <tr v-if="inspectionHistoryList.length === 0">
                    <td colspan="9" class="empty-table-cell">暂无巡检检测记录，可点击弹幕或评论列表上方“4号智能体一键批量巡检”触发！</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 分页器 -->
            <div class="moderation-pagination-footer" v-if="inspectionHistoryTotal > 0">
              <span class="pagination-info">共 {{ inspectionHistoryTotal }} 次巡检记录</span>
              <el-pagination
                background
                layout="prev, pager, next"
                :current-page="inspectionHistoryPage"
                :page-size="inspectionHistoryPageSize"
                :total="inspectionHistoryTotal"
                @current-change="fetchInspectionHistory"
              />
            </div>
          </div>



          <!-- 抽屉: 4号智能体 AI 待审自迭代词单 -->
          <el-drawer
            v-model="showProposalsDrawer"
            title="4号合规审片官 · 新型违规词自迭代待审单"
            direction="rtl"
            size="580px"
            custom-class="proposals-drawer-glass"
          >
            <div class="proposals-drawer-body">
              <div class="drawer-top-bar">
                <p class="drawer-tip">智能体巡检弹幕/评论时提炼出规避检测的新型黑话与变体词，经审核员审批后实时同步入库并热重载 DFA 树。</p>
              </div>

              <div class="proposals-list-scroll">
                <div v-for="prop in proposalsList" :key="prop.id" class="proposal-card-item">
                  <div class="prop-header">
                    <span class="prop-word font-bold font-mono">{{ prop.word }}</span>
                    <div class="prop-badges">
                      <span class="priv-tag creator">{{ prop.category }}</span>
                      <span class="status-badge" :class="prop.level === 'HIGH' ? 'danger' : 'warning'">{{ prop.level }}</span>
                    </div>
                  </div>
                  <div class="prop-reason mt-6">
                    <span class="muted-label">提炼理由:</span>
                    <span class="reason-val">{{ prop.reason }}</span>
                  </div>
                  <div class="prop-source mt-4" v-if="prop.source_content">
                    <span class="muted-label">来源发言:</span>
                    <span class="source-val font-mono">“{{ prop.source_content }}”</span>
                  </div>
                  <div class="prop-actions mt-10">
                    <button class="apple-btn-primary btn-sm" @click="handleDecideProposal(prop.id, 'ACCEPT')">
                      <el-icon><Check /></el-icon>
                      <span>采纳并录入 DFA</span>
                    </button>
                    <button class="apple-btn-secondary btn-sm ml-8" @click="handleDecideProposal(prop.id, 'REJECT')">
                      <el-icon><Close /></el-icon>
                      <span>驳回忽略</span>
                    </button>
                  </div>
                </div>

                <div v-if="proposalsList.length === 0" class="empty-drawer-state">
                  <p>当前暂无挂起的新型自迭代敏感词建议，词库处于平稳防御状态。</p>
                </div>
              </div>
            </div>
          </el-drawer>

          <!-- 模态框: 4号合规官批量巡检研判报告 -->
          <transition name="apple-modal-fade">
            <div v-if="showInspectReportModal" class="inspect-report-modal-backdrop" @click.self="showInspectReportModal = false">
              <div class="inspect-report-modal glass-card">
                <div class="report-modal-header">
                  <div class="report-title-box">
                    <span class="report-badge">AGENT 04 · INSPECTION REPORT</span>
                    <h3 class="report-title">4号合规审片官 · 互动全域巡检研判报告</h3>
                    <p class="report-meta">
                      巡检类型: {{ inspectReportData?.interaction_type === 'danmaku' ? '弹幕' : '评论' }} · 
                      总样本数: {{ inspectReportData?.total_inspected }} · 
                      检出违规: {{ inspectReportData?.violation_count }} 笔 · 
                      研判耗时: {{ inspectReportData?.cost_ms }}ms
                    </p>
                  </div>
                  <button class="btn-close-modal" @click="showInspectReportModal = false">
                    <el-icon><Close /></el-icon>
                  </button>
                </div>

                <div class="report-modal-body">
                  <!-- 区域 1: 检出违规项 -->
                  <div class="report-section">
                    <div class="section-title-row">
                      <h4 class="section-title">检出违规记录 ({{ inspectReportData?.violations?.length || 0 }})</h4>
                      <div class="section-actions" v-if="inspectReportData?.violations?.length">
                        <button class="apple-btn-primary btn-sm btn-danger" @click="handleBatchResolveViolationsInModal('DELETE')">
                          批量下架已选违规 ({{ selectedViolationIds.length }})
                        </button>
                        <button class="apple-btn-secondary btn-sm ml-8" @click="handleBatchResolveViolationsInModal('PENDING_HITL')">
                          送入人机回环工单
                        </button>
                      </div>
                    </div>

                    <div class="violations-table-wrap">
                      <table class="apple-table" v-if="inspectReportData?.violations?.length">
                        <thead>
                          <tr>
                            <th style="width: 40px;">
                              <input 
                                type="checkbox" 
                                :checked="selectedViolationIds.length > 0 && selectedViolationIds.length === inspectReportData.violations.length"
                                @change="toggleSelectAllViolationsInModal"
                              />
                            </th>
                            <th>发言内容</th>
                            <th>发表人</th>
                            <th>所属短剧</th>
                            <th>风险判定与依据</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="v in inspectReportData.violations" :key="v.id">
                            <td>
                              <input type="checkbox" :value="v.id" v-model="selectedViolationIds" />
                            </td>
                            <td class="font-bold">{{ v.content }}</td>
                            <td>{{ v.user_name }}</td>
                            <td>{{ v.video_title }}</td>
                            <td>
                              <span class="status-badge danger">风险 {{ v.risk_score }}分</span>
                              <span class="muted-txt ml-4">{{ v.reason }}</span>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                      <div v-else class="empty-ok-state">
                        本次巡检样本均未检出恶意或违禁违规内容，互动生态健康。
                      </div>
                    </div>
                  </div>

                  <!-- 区域 2: 提炼出的新型违规词建议 -->
                  <div class="report-section mt-16" v-if="inspectReportData?.suggested_words?.length">
                    <div class="section-title-row">
                      <h4 class="section-title">智能体提炼出新型建议词 ({{ inspectReportData.suggested_words.length }})</h4>
                      <button class="apple-btn-primary btn-sm" @click="handleBatchAcceptProposalsInModal">
                        一键采纳所有建议新词并热重载
                      </button>
                    </div>

                    <div class="suggested-words-grid">
                      <div v-for="w in inspectReportData.suggested_words" :key="w.id" class="suggested-word-chip">
                        <div class="chip-main font-bold font-mono">{{ w.word }}</div>
                        <div class="chip-meta">
                          <span class="priv-tag creator">{{ w.category }}</span>
                          <span class="status-badge danger">{{ w.level }}</span>
                        </div>
                        <p class="chip-reason">{{ w.reason }}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="report-modal-footer">
                  <button class="apple-btn-secondary" @click="showInspectReportModal = false">关闭报告</button>
                </div>
              </div>
            </div>
          </transition>
        </section>



        <!-- ================================================================= -->
        <!-- TAB 9: RAG 知识中台 & 算法四维评测大屏                             -->
        <!-- ================================================================= -->
        <section v-if="currentTab === 'rag'" class="content-section-rag" id="section-rag">
          <CinemaAgentRagCenter :is-dark="isDark" />
        </section>

        <!-- ================================================================= -->
        <!-- TAB 10: 九大领域专家智能体总控、三级模型治理、Skills & 战术大屏     -->
        <!-- ================================================================= -->
        <section v-if="currentTab === 'agent-hub'" class="content-section" id="section-agent-hub">
          <AgentCommandCenter @switch-tab="selectTab" />
        </section>

        <!-- ================================================================= -->
        <!-- TAB 10.5: MCP 云端中台 (拓扑大屏与在线沙盒)                    -->
        <!-- ================================================================= -->
        <section v-if="currentTab === 'mcp'" class="content-section" id="section-mcp">
          <CinemaAgentMcpCenter :is-dark="isDark" />
        </section>

        <!-- ================================================================= -->
        <!-- TAB 11: 登录主页壁纸引擎与系统视觉管理                             -->
        <!-- ================================================================= -->
        <section v-if="currentTab === 'wallpaper'" class="content-section" id="section-wallpaper">
          <div class="wallpaper-admin-wrap">
            <div class="wallpaper-admin-header">
              <div class="header-left">
                <h2 class="section-title">登录主页背景壁纸配置</h2>
                <p class="section-desc">管理普通用户与系统登录入口的主题背景呈现模式、暗度遮罩及高斯模糊质感</p>
              </div>
              <div class="header-right">
                <button class="apple-btn-secondary" id="btn-reset-wallpaper" @click="handleResetWallpaperConfig" :disabled="isSavingWallpaper">
                  恢复默认预设
                </button>
                <button class="apple-btn-primary" id="btn-save-wallpaper" @click="handleSaveWallpaperConfig" :disabled="isSavingWallpaper">
                  <span v-if="isSavingWallpaper">保存中...</span>
                  <span v-else>保存并即时生效</span>
                </button>
              </div>
            </div>

            <div class="wallpaper-config-grid">
              <!-- Left: Form Controls -->
              <div class="config-form-card glass-card">
                <h3 class="card-subtitle">壁纸模式与参数调优</h3>

                <div class="form-group-item">
                  <label class="form-label">壁纸渲染模式</label>
                  <div class="mode-selector-capsules">
                    <button 
                      type="button" 
                      class="mode-capsule-btn" 
                      :class="{ active: wallpaperConfig.mode === 'gaoleng_qianjin' }"
                      id="btn-mode-gaoleng"
                      @click="wallpaperConfig.mode = 'gaoleng_qianjin'"
                    >
                      <span class="capsule-title">高冷千金原画</span>
                      <span class="capsule-sub">Steam 1080P 超清壁纸</span>
                    </button>
                    <button 
                      type="button" 
                      class="mode-capsule-btn" 
                      :class="{ active: wallpaperConfig.mode === 'default_aurora' }"
                      id="btn-mode-aurora"
                      @click="wallpaperConfig.mode = 'default_aurora'"
                    >
                      <span class="capsule-title">极光流光动态</span>
                      <span class="capsule-sub">原生粒子流动画</span>
                    </button>
                    <button 
                      type="button" 
                      class="mode-capsule-btn" 
                      :class="{ active: wallpaperConfig.mode === 'custom_url' }"
                      id="btn-mode-custom"
                      @click="wallpaperConfig.mode = 'custom_url'"
                    >
                      <span class="capsule-title">自定义直链</span>
                      <span class="capsule-sub">外链或本地静态直链</span>
                    </button>
                  </div>
                </div>

                <div class="form-group-item" v-if="wallpaperConfig.mode === 'custom_url'">
                  <label class="form-label">自定义图片 URL</label>
                  <input 
                    type="text" 
                    v-model="wallpaperConfig.custom_url" 
                    placeholder="https://example.com/wallpaper.png 或 /wallpapers/xxx.png"
                    class="apple-input-text"
                    id="input-wallpaper-custom-url"
                  />
                </div>

                <div class="form-group-item">
                  <div class="label-with-value">
                    <label class="form-label">深色模式微遮罩暗度</label>
                    <span class="value-badge">{{ Math.round((wallpaperConfig.dark_opacity || 0) * 100) }}%</span>
                  </div>
                  <input 
                    type="range" 
                    min="0" 
                    max="0.9" 
                    step="0.01" 
                    v-model.number="wallpaperConfig.dark_opacity" 
                    class="apple-range-slider"
                    id="slider-dark-opacity"
                  />
                  <span class="form-hint">在深色夜间模式下，半透明黑色遮罩的叠加浓度，保证登录表单文字清晰可读</span>
                </div>

                <div class="form-group-item">
                  <div class="label-with-value">
                    <label class="form-label">浅色模式微遮罩亮度</label>
                    <span class="value-badge">{{ Math.round((wallpaperConfig.light_opacity || 0) * 100) }}%</span>
                  </div>
                  <input 
                    type="range" 
                    min="0" 
                    max="0.9" 
                    step="0.01" 
                    v-model.number="wallpaperConfig.light_opacity" 
                    class="apple-range-slider"
                    id="slider-light-opacity"
                  />
                  <span class="form-hint">在浅色白天模式下，半透明白色遮罩的叠加浓度</span>
                </div>

                <div class="form-group-item">
                  <div class="label-with-value">
                    <label class="form-label">背景高斯模糊度</label>
                    <span class="value-badge">{{ wallpaperConfig.blur_px || 0 }} px</span>
                  </div>
                  <input 
                    type="range" 
                    min="0" 
                    max="20" 
                    step="1" 
                    v-model.number="wallpaperConfig.blur_px" 
                    class="apple-range-slider"
                    id="slider-blur-px"
                  />
                  <span class="form-hint">为壁纸附加高斯模糊毛玻璃特效，0px 为原画无损锐利输出</span>
                </div>
              </div>

              <!-- Right: Live WYSIWYG Preview Card -->
              <div class="preview-stage-card glass-card">
                <div class="preview-header">
                  <h3 class="card-subtitle">所见即所得实时效果预览</h3>
                  <div class="preview-theme-switch">
                    <button 
                      type="button" 
                      class="preview-toggle-btn" 
                      :class="{ active: previewTheme === 'dark' }" 
                      id="btn-preview-dark"
                      @click="previewTheme = 'dark'"
                    >深色效果</button>
                    <button 
                      type="button" 
                      class="preview-toggle-btn" 
                      :class="{ active: previewTheme === 'light' }" 
                      id="btn-preview-light"
                      @click="previewTheme = 'light'"
                    >浅色效果</button>
                  </div>
                </div>

                <div class="preview-viewport-mock" :class="previewTheme">
                  <!-- Wallpaper background layer -->
                  <div class="preview-bg-layer" :style="previewWallpaperStyle"></div>
                  <!-- Mask layer -->
                  <div class="preview-mask-layer" :style="previewMaskStyle"></div>

                  <!-- Mock Login Box -->
                  <div class="mock-login-box">
                    <div class="mock-brand">
                      <span class="mock-title">CinemaAgent</span>
                      <span class="mock-sub">极简视听登录中心</span>
                    </div>
                    <div class="mock-input-row"></div>
                    <div class="mock-input-row"></div>
                    <div class="mock-button-row"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>

    <!-- Modal: Create / Edit System Announcement (Fixed Center Backdrop) -->
    <transition name="apple-modal-fade">
      <div 
        v-if="showAnnouncementModal" 
        class="announcement-modal-backdrop" 
        id="modal-announcement"
        @click.self="showAnnouncementModal = false"
      >
        <div class="apple-glass-dialog modal-card announcement-dialog">
          <div class="modal-header">
            <div class="modal-title-wrap">
              <el-icon :size="20" class="modal-icon-brand"><Bell /></el-icon>
              <h3 class="modal-title">
                {{ announcementModalMode === 'create' ? '发布新系统公告 (全员广播)' : '编辑系统公告详情' }}
              </h3>
            </div>
            <button class="modal-close-btn" @click="showAnnouncementModal = false">&times;</button>
          </div>

          <div class="modal-body">
            <div class="form-group">
              <label class="form-label">公告标题 <span class="required">*</span></label>
              <input 
                v-model="announcementForm.title" 
                class="apple-input" 
                id="input-announcement-title" 
                placeholder="例如：系统算力底层升级完成及社区公约更新" 
              />
            </div>

            <div class="form-group">
              <label class="form-label">分类标签</label>
              <div class="tag-quick-select">
                <button 
                  v-for="t in ['系统公告', '版本升级', '社区公约', '活动福利', '安全通告']" 
                  :key="t"
                  type="button"
                  class="tag-option-pill"
                  :class="{ active: announcementForm.tag === t }"
                  @click="announcementForm.tag = t"
                >
                  {{ t }}
                </button>
              </div>
              <input 
                v-model="announcementForm.tag" 
                class="apple-input mt-2" 
                id="input-announcement-tag" 
                placeholder="自定义公告标签" 
              />
            </div>

            <div class="form-group">
              <label class="form-label">公告详情正文 <span class="required">*</span></label>
              <textarea 
                v-model="announcementForm.content" 
                class="apple-textarea" 
                id="textarea-announcement-content" 
                rows="5"
                placeholder="在此输入需要向全站用户广播展示的公告正文内容..."
              ></textarea>
            </div>

            <div class="form-group switch-group" v-if="announcementModalMode === 'create'">
              <span class="switch-label">创建后即刻向全站活跃用户广播</span>
              <el-switch v-model="announcementForm.is_published" />
            </div>
          </div>

          <div class="modal-footer">
            <button 
              type="button" 
              class="apple-btn-secondary" 
              @click="showAnnouncementModal = false"
            >
              取消
            </button>
            <button 
              type="button" 
              class="apple-btn-primary" 
              id="btn-submit-announcement"
              :disabled="isSubmittingAnnouncement || !announcementForm.title.trim() || !announcementForm.content.trim()"
              @click="submitAnnouncementModal"
            >
              <el-icon v-if="isSubmittingAnnouncement" class="is-loading"><Refresh /></el-icon>
              <span>{{ isSubmittingAnnouncement ? '正在广播提交...' : (announcementModalMode === 'create' ? '立即发布广播' : '保存修改') }}</span>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Modal: Edit Drama Cover & Metadata Governance -->
    <el-dialog 
      v-model="showEditCoverDialog" 
      title="短剧封面资产与多画报海报治理" 
      width="720px"
      id="modal-edit-cover"
    >
      <div class="dialog-form cover-governance-form">
        <!-- Section A: Metadata -->
        <div class="form-row-grid">
          <div class="form-group">
            <label class="form-label">短剧名称</label>
            <input 
              v-model="editingDramaMeta.title" 
              class="apple-input" 
              placeholder="短剧主标题" 
              id="input-drama-title"
            />
          </div>
          <div class="form-group">
            <label class="form-label">题材分类</label>
            <input 
              v-model="editingDramaMeta.category" 
              class="apple-input" 
              placeholder="如：现代言情、逆袭爽剧" 
              id="input-drama-category"
            />
          </div>
        </div>

        <div class="form-row-grid">
          <div class="form-group full-width">
            <label class="form-label">剧情梗概简介</label>
            <textarea 
              v-model="editingDramaMeta.summary" 
              class="apple-textarea" 
              rows="2" 
              placeholder="输入剧情核心冲突亮点..."
              id="textarea-drama-summary"
            ></textarea>
          </div>
        </div>

        <!-- Section B: Cover Drag & Drop Upload (Eliminating #000 Black Box) -->
        <div class="form-group full-width">
          <label class="form-label">主封面海报 (支持本地拖拽安全上传 JPG/PNG/WEBP <=10MB)</label>
          <div 
            class="cover-preview-box" 
            :class="{ 'is-dragover': isCoverDragOver }"
            @dragover.prevent="isCoverDragOver = true"
            @dragleave.prevent="isCoverDragOver = false"
            @drop.prevent="handleCoverDrop"
            @click="triggerUploadImage"
            id="dropzone-cover-upload"
          >
            <img 
              v-if="editingCoverUrl && !coverImgError" 
              :src="editingCoverUrl" 
              class="preview-img" 
              @error="coverImgError = true" 
            />
            <div v-else class="dashed-micro-glow-placeholder">
              <el-icon :size="36" class="placeholder-icon"><Upload /></el-icon>
              <div class="placeholder-text">
                <span class="main-tip">点击或拖拽图片至此处上传新主封面</span>
                <span class="sub-tip">支持 JPG / PNG / WEBP 格式，大小不超过 10MB</span>
              </div>
            </div>
            <div v-if="editingCoverUrl && !coverImgError" class="cover-hover-prompt">
              <el-icon><Upload /></el-icon>
              <span>点击或拖拽新图片可直接替换</span>
            </div>
          </div>

          <div class="cover-url-manual-row">
            <input 
              v-model="editingCoverUrl" 
              class="apple-input text-xs" 
              placeholder="或输入外部静态图片 URL 直链" 
              id="input-cover-url"
              @input="coverImgError = false"
            />
            <button 
              type="button" 
              class="apple-btn-secondary btn-sm" 
              @click.stop="triggerUploadImage"
            >
              <el-icon><Upload /></el-icon>
              <span>选择本地文件</span>
            </button>
          </div>
        </div>

        <!-- Section C: Multi-Poster Shelf (extra_images) -->
        <div class="form-group full-width">
          <div class="shelf-header-row">
            <label class="form-label">画报海报展架 ({{ editingDramaPosters.length }} 张海报，支持设为主封面)</label>
            <button 
              type="button" 
              class="apple-btn-secondary btn-sm" 
              @click.stop="triggerUploadImage"
            >
              <el-icon><Plus /></el-icon>
              <span>添加画报海报</span>
            </button>
          </div>

          <div class="posters-shelf-grid">
            <div 
              v-for="(poster, idx) in editingDramaPosters" 
              :key="idx" 
              class="poster-shelf-card"
              :class="{ 'is-main': poster === editingCoverUrl }"
            >
              <img :src="poster" class="shelf-thumb" />
              <div class="shelf-card-overlay">
                <span v-if="poster === editingCoverUrl" class="shelf-main-badge">主封面</span>
                <button 
                  v-else 
                  type="button" 
                  class="shelf-btn-set-main" 
                  @click="setAsMainCover(poster)"
                >
                  设为主封面
                </button>
                <button 
                  type="button" 
                  class="shelf-btn-del" 
                  @click="removePoster(idx)"
                  title="移除画报"
                >
                  <el-icon><Delete /></el-icon>
                </button>
              </div>
            </div>
            <div 
              v-if="editingDramaPosters.length === 0" 
              class="shelf-empty-hint"
            >
              暂未录入附加画报海报，上传后前台大厅将自动激活多画报焦点轮播
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="apple-btn-secondary" @click="showEditCoverDialog = false">取消</button>
        <button class="apple-btn-primary" @click="confirmUpdateCover" id="btn-save-drama-cover">保存全部元数据与海报</button>
      </template>
    </el-dialog>

    <!-- Modal: View Drama Posters Carousel -->
    <el-dialog v-model="showPostersCarouselDialog" :title="activeDramaForPosters?.title + ' · 多剧照展架'" width="640px">
      <div v-if="activeDramaForPosters?.extra_images?.length" class="posters-carousel-wrap">
        <el-carousel trigger="click" height="360px">
          <el-carousel-item v-for="(imgUrl, idx) in activeDramaForPosters.extra_images" :key="idx">
            <div class="carousel-item-img" :style="{ backgroundImage: `url(${imgUrl})` }">
              <span class="img-idx-pill">第 {{ idx + 1 }} / {{ activeDramaForPosters.extra_images.length }} 张</span>
            </div>
          </el-carousel-item>
        </el-carousel>
      </div>
    </el-dialog>

    <!-- Modal: Create / Edit Carousel (16:9 WYSIWYG Live Preview) -->
    <el-dialog 
      v-model="showCarouselDialog" 
      :title="isEditingCarousel ? '编辑焦点轮播' : '新增焦点轮播 (16:9 所见即所得)'" 
      width="860px"
      id="modal-carousel"
    >
      <div class="carousel-dialog-grid">
        <!-- Left: Config Form -->
        <div class="dialog-form">
          <div class="form-group">
            <label class="form-label">快速关联合约短剧 (自动提取标题、海报与 ID)</label>
            <select 
              v-model="selectedCarouselDramaModalId" 
              class="apple-select" 
              id="select-carousel-drama-modal"
              @change="handleModalSelectDrama"
            >
              <option value="">-- 选择已有短剧作品 --</option>
              <option v-for="d in dramaOptionsList" :key="d.id" :value="d.id">
                《{{ d.title }}》({{ d.category || '短剧' }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">标题推荐文案</label>
            <input 
              v-model="carouselForm.title" 
              class="apple-input" 
              placeholder="输入吸引人的轮播焦点标题" 
              id="input-carousel-title"
            />
          </div>
          <div class="form-group">
            <label class="form-label">副标题简介</label>
            <input 
              v-model="carouselForm.subtitle" 
              class="apple-input" 
              placeholder="简短亮点说明" 
              id="input-carousel-subtitle"
            />
          </div>
          <div class="form-group">
            <label class="form-label">标签 Badge (如：本周爆款榜首、今日焦点)</label>
            <input 
              v-model="carouselForm.tag" 
              class="apple-input" 
              placeholder="本周爆款榜首" 
              id="input-carousel-tag"
            />
          </div>
          <div class="form-group">
            <label class="form-label">海报大图 URL (16:9 比例推荐)</label>
            <input 
              v-model="carouselForm.cover_url" 
              class="apple-input" 
              placeholder="https://..." 
              id="input-carousel-cover"
            />
          </div>
          <div class="form-group">
            <label class="form-label">关联短剧 ID (选填)</label>
            <input 
              v-model="carouselForm.video_id" 
              class="apple-input font-mono" 
              placeholder="短剧 ID" 
              id="input-carousel-videoid"
            />
          </div>
          <div class="form-row-grid">
            <div class="form-group">
              <label class="form-label">排序权重</label>
              <input v-model.number="carouselForm.sort_order" type="number" class="apple-input" />
            </div>
            <div class="form-group">
              <label class="form-label">轮播停留时长 (秒)</label>
              <input v-model.number="carouselForm.duration_seconds" type="number" min="3" max="20" class="apple-input" placeholder="默认 5 秒" id="input-carousel-duration" />
            </div>
            <div class="form-group">
              <label class="form-label">立即启用上线</label>
              <el-switch v-model="carouselForm.is_active" />
            </div>
          </div>
        </div>

        <!-- Right: 16:9 Live Preview Card -->
        <div class="dialog-preview-col">
          <label class="form-label">大厅首屏 16:9 所见即所得实时效果</label>
          <div class="carousel-preview-wrapper">
            <div class="carousel-preview-container" id="carousel-preview-16-9-modal">
              <div class="aspect-16-9-box">
                <img 
                  v-if="carouselForm.cover_url" 
                  :src="carouselForm.cover_url" 
                  class="preview-bg-img" 
                />
                <div v-else class="preview-empty-placeholder">
                  <el-icon :size="40"><Picture /></el-icon>
                  <span>请从左侧选择短剧或录入海报链接</span>
                </div>
                <div class="preview-overlay">
                  <span class="preview-tag-badge">{{ carouselForm.tag || '推荐焦点' }}</span>
                  <h4 class="preview-title">{{ carouselForm.title || '主标题预览' }}</h4>
                  <p class="preview-subtitle">{{ carouselForm.subtitle || '副标题亮点预览...' }}</p>
                </div>
              </div>
            </div>
            <div class="preview-ratio-label">
              <span>16 : 9 标准大屏高清比例</span>
              <span class="preview-badge-status">动态即时渲染</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="apple-btn-secondary" @click="showCarouselDialog = false">取消</button>
        <button class="apple-btn-primary" @click="saveCarousel" id="btn-submit-carousel">保存配置</button>
      </template>
    </el-dialog>

    <!-- Modal: Add User Full CRUD -->
    <el-dialog 
      v-model="showAddUserDialog" 
      title="创建新用户账号与特权配置" 
      width="500px" 
      id="modal-add-user"
    >
      <div class="dialog-form">
        <div class="form-group">
          <label class="form-label">用户账号名称 (Username) <span class="text-danger">*</span></label>
          <input 
            v-model="addUserForm.username" 
            class="apple-input" 
            placeholder="输入唯一登录账号名" 
            id="input-add-username"
          />
        </div>
        <div class="form-group">
          <label class="form-label">登录密码 (Password) <span class="text-danger">*</span></label>
          <input 
            v-model="addUserForm.password" 
            type="password" 
            class="apple-input" 
            placeholder="输入初始登录密码" 
            id="input-add-password"
          />
        </div>
        <div class="form-group">
          <label class="form-label">用户展示昵称 (Nickname)</label>
          <input 
            v-model="addUserForm.nickname" 
            class="apple-input" 
            placeholder="输入个性化展示昵称 (选填)" 
            id="input-add-nickname"
          />
        </div>
        <div class="form-group">
          <label class="form-label">初始系统角色 (Role)</label>
          <select 
            v-model="addUserForm.role" 
            class="apple-select full-width" 
            id="select-add-role"
          >
            <option value="USER">普通观众用户 (USER)</option>
            <option value="CREATOR">短剧创作者 (CREATOR)</option>
            <option value="REVIEWER">合规审核员 (REVIEWER)</option>
            <option value="ADMIN">超级管理员 (ADMIN)</option>
          </select>
        </div>
        <div class="form-row-grid">
          <div class="form-group">
            <label class="form-label">初始金币余额</label>
            <input 
              v-model.number="addUserForm.coins" 
              type="number" 
              class="apple-input" 
              placeholder="默认 50" 
              id="input-add-coins"
            />
          </div>
          <div class="form-group">
            <label class="form-label">赠送 VIP 天数</label>
            <input 
              v-model.number="addUserForm.vip_days" 
              type="number" 
              class="apple-input" 
              placeholder="默认 0 天" 
              id="input-add-vip-days"
            />
          </div>
        </div>
      </div>
      <template #footer>
        <button class="apple-btn-secondary" @click="showAddUserDialog = false">取消</button>
        <button class="apple-btn-primary" @click="confirmAddUser" id="btn-submit-add-user">确认创建用户</button>
      </template>
    </el-dialog>

    <!-- Modal: Edit User Full Profile & Assets -->
    <el-dialog 
      v-model="showEditUserDialog" 
      title="编辑用户全量资料与特权资产" 
      width="520px" 
      id="modal-edit-user"
    >
      <div class="dialog-form" v-if="selectedUserForEdit">
        <div class="form-group">
          <label class="form-label">用户标识</label>
          <input 
            :value="selectedUserForEdit.username" 
            class="apple-input" 
            disabled 
          />
        </div>
        <div class="form-group">
          <label class="form-label">用户昵称</label>
          <input 
            v-model="editUserForm.nickname" 
            class="apple-input" 
            placeholder="修改用户昵称" 
            id="input-edit-nickname"
          />
        </div>
        <div class="form-group">
          <label class="form-label">重置登录密码 (留空则保持原密码不变)</label>
          <input 
            v-model="editUserForm.password" 
            type="password" 
            class="apple-input" 
            placeholder="输入新密码重置" 
            id="input-edit-password"
          />
        </div>
        <div class="form-row-grid">
          <div class="form-group">
            <label class="form-label">系统角色</label>
            <select 
              v-model="editUserForm.role" 
              class="apple-select full-width" 
              id="select-edit-role"
            >
              <option value="USER">普通用户 (USER)</option>
              <option value="CREATOR">创作者 (CREATOR)</option>
              <option value="REVIEWER">审核员 (REVIEWER)</option>
              <option value="ADMIN">管理员 (ADMIN)</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">账号状态</label>
            <select 
              v-model="editUserForm.status" 
              class="apple-select full-width" 
              id="select-edit-status"
            >
              <option value="ACTIVE">正常活跃 (ACTIVE)</option>
              <option value="BANNED">已封禁 (BANNED)</option>
            </select>
          </div>
        </div>
        <div class="form-row-grid">
          <div class="form-group">
            <label class="form-label">金币增减调整 (如 +50 或 -20)</label>
            <input 
              v-model.number="editUserForm.coins_adjustment" 
              type="number" 
              class="apple-input" 
              placeholder="0" 
              id="input-edit-coins-adj"
            />
          </div>
          <div class="form-group">
            <label class="form-label">增加 VIP 期限 (天)</label>
            <input 
              v-model.number="editUserForm.vip_days" 
              type="number" 
              class="apple-input" 
              placeholder="0" 
              id="input-edit-vip-days"
            />
          </div>
        </div>
      </div>
      <template #footer>
        <button class="apple-btn-secondary" @click="showEditUserDialog = false">取消</button>
        <button class="apple-btn-primary" @click="confirmEditUser" id="btn-submit-edit-user">保存修改</button>
      </template>
    </el-dialog>

    <!-- Modal: Change Role -->
    <el-dialog v-model="showRoleDialog" title="调整用户系统角色与权限" width="400px">
      <div class="role-select-form">
        <label v-for="r in ['USER', 'CREATOR', 'REVIEWER', 'ADMIN']" :key="r" class="role-radio-item">
          <input type="radio" v-model="selectedRole" :value="r" />
          <span>{{ getRoleLabel(r) }}</span>
        </label>
      </div>
      <template #footer>
        <button class="apple-btn-secondary" @click="showRoleDialog = false">取消</button>
        <button class="apple-btn-primary" @click="confirmChangeRole">确认赋权</button>
      </template>
    </el-dialog>

    <!-- Modal: Add Sensitive Word -->
    <el-dialog v-model="showAddWordDialog" title="录入社区风控敏感词" width="460px">
      <div class="dialog-form">
        <div class="form-group">
          <label class="form-label">敏感词条内容</label>
          <input v-model="newWordForm.word" class="apple-input" placeholder="输入敏感词或违禁短语" id="input-modal-new-word" />
        </div>
        <div class="form-group">
          <label class="form-label">分类标签</label>
          <select v-model="newWordForm.category" class="apple-select" id="select-modal-new-word-category">
            <option value="违禁">违禁</option>
            <option value="涉政">涉政</option>
            <option value="暴恐">暴恐</option>
            <option value="涉黄">涉黄</option>
            <option value="辱骂">辱骂</option>
            <option value="广告">广告</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">风险判定等级</label>
          <select v-model="newWordForm.level" class="apple-select" id="select-modal-new-word-level">
            <option value="HIGH">高风险 (HIGH - 阻断上屏)</option>
            <option value="MEDIUM">中风险 (MEDIUM - 脱敏放行)</option>
            <option value="LOW">低风险 (LOW - 仅日志审计)</option>
          </select>
        </div>
      </div>
      <template #footer>
        <button class="apple-btn-secondary" @click="showAddWordDialog = false">取消</button>
        <button class="apple-btn-primary" :disabled="!newWordForm.word.trim()" @click="confirmAddSensitiveWord" id="btn-confirm-add-word">录入并热重载 DFA</button>
      </template>
    </el-dialog>

    <!-- Modal: LLM Judge Configuration -->
    <el-dialog v-model="showJudgeConfigDialog" title="RAG 四维评测裁判模型配置 (LLM Judge)" width="600px" id="modal-judge-config">
      <div class="dialog-form">
        <div class="form-group">
          <label class="form-label">裁判运行模式</label>
          <div class="role-select-form">
            <label class="role-radio-item">
              <input type="radio" v-model="judgeConfigForm.mode" value="local" />
              <span>模式 A: 本地复用 (本地已有 Ollama / 系统模型)</span>
            </label>
            <label class="role-radio-item">
              <input type="radio" v-model="judgeConfigForm.mode" value="cloud" />
              <span>模式 B: 自定义独立云端裁判 (DeepSeek-R1 / Qwen-Max / OpenAI)</span>
            </label>
          </div>
        </div>

        <div v-if="judgeConfigForm.mode === 'local'" class="judge-local-fields">
          <div class="form-group">
            <label class="form-label">本地 Provider</label>
            <input v-model="judgeConfigForm.local.provider" class="apple-input" placeholder="ollama" />
          </div>
          <div class="form-group">
            <label class="form-label">本地模型名称</label>
            <input v-model="judgeConfigForm.local.model_name" class="apple-input" placeholder="deepseek-r1:1.5b" />
          </div>
          <div class="form-group">
            <label class="form-label">本地服务 Base URL</label>
            <input v-model="judgeConfigForm.local.base_url" class="apple-input" placeholder="http://localhost:11434" />
          </div>
        </div>

        <div v-if="judgeConfigForm.mode === 'cloud'" class="judge-cloud-fields">
          <div class="form-group">
            <label class="form-label">云端 Provider</label>
            <select v-model="judgeConfigForm.cloud.provider" class="apple-select full-width">
              <option value="deepseek">DeepSeek 官方 API</option>
              <option value="openai">OpenAI</option>
              <option value="qwen">阿里千问 Qwen</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">云端裁判模型标识</label>
            <input v-model="judgeConfigForm.cloud.model_name" class="apple-input" placeholder="deepseek-r1" />
          </div>
          <div class="form-group">
            <label class="form-label">Base URL</label>
            <input v-model="judgeConfigForm.cloud.base_url" class="apple-input" placeholder="https://api.deepseek.com" />
          </div>
          <div class="form-group">
            <label class="form-label">API Key 密钥</label>
            <input v-model="judgeConfigForm.cloud.api_key" type="password" class="apple-input" :placeholder="judgeConfigForm.cloud.masked_api_key || 'sk-...'" />
          </div>
        </div>

        <div class="form-group switch-group mt-3" style="display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; background: rgba(255, 255, 255, 0.04); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08);">
          <div>
            <div class="font-semibold text-xs" style="color: var(--text-primary, #ffffff);">裁判模型流式输出 (Stream Mode)</div>
            <div class="text-[11px]" style="color: var(--text-muted, #9499a0);">大模型若支持流式则开启实时逐 Token 流式读取；不支持则平滑降级同步完成</div>
          </div>
          <el-switch v-model="judgeConfigForm.enable_stream" id="switch-judge-stream-admin" />
        </div>
      </div>
      <template #footer>
        <button class="apple-btn-secondary" @click="showJudgeConfigDialog = false">取消</button>
        <button class="apple-btn-primary" @click="handleSaveJudgeConfig" id="btn-save-judge-config">持久化保存裁判配置</button>
      </template>
    </el-dialog>

    <!-- Modal: Create Corpus -->
    <el-dialog v-model="showCreateCorpusDialog" title="录入短剧知识文档" width="600px" id="modal-create-corpus">
      <div class="dialog-form">
        <div class="form-group">
          <label class="form-label">知识文档标题 <span class="text-danger">*</span></label>
          <input v-model="newCorpusForm.title" class="apple-input" placeholder="如：《千金归来》主线人物档案" />
        </div>
        <div class="form-group">
          <label class="form-label">文档类别</label>
          <select v-model="newCorpusForm.doc_type" class="apple-select full-width">
            <option value="script">分镜剧本 (Script)</option>
            <option value="srt_subtitle">SRT 时间轴字幕 (Subtitles)</option>
            <option value="biography">人物设定与世界观 (Biography)</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">切片策略</label>
          <select v-model="newCorpusForm.strategy" class="apple-select full-width">
            <option value="fixed">固定大小切片</option>
            <option value="sliding_window">滑动窗口切片</option>
            <option value="sentence_window">基于时间轴的句子窗口切片</option>
            <option value="parent_child">父子分块策略</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">原始文本内容 <span class="text-danger">*</span></label>
          <textarea v-model="newCorpusForm.content" class="apple-textarea" rows="8" placeholder="粘贴剧本大纲或标准 SRT 文本..."></textarea>
        </div>
      </div>
      <template #footer>
        <button class="apple-btn-secondary" @click="showCreateCorpusDialog = false">取消</button>
        <button class="apple-btn-primary" :disabled="!newCorpusForm.title.trim() || !newCorpusForm.content.trim()" @click="handleCreateCorpus" id="btn-submit-create-corpus">录入并自动切片索引</button>
      </template>
    </el-dialog>

    <!-- Modal: Generate Gold Coin / VIP Redemption Codes -->
    <el-dialog
      v-model="showGenerateRedemptionDialog"
      title="批量生成金币兑换码 / VIP 会员兑换码"
      width="540px"
      id="modal-generate-redemption"
      align-center
    >
      <div class="dialog-form">
        <div class="form-group">
          <label class="form-label">选择兑换码权益类型 <span class="text-danger">*</span></label>
          <div class="tag-quick-select">
            <button
              type="button"
              class="tag-option-pill"
              :class="{ active: generateRedemptionForm.code_type === 'COIN' }"
              id="btn-type-coin"
              @click="selectRedemptionType('COIN')"
            >
              金币充值兑换码 (COIN)
            </button>
            <button
              type="button"
              class="tag-option-pill"
              :class="{ active: generateRedemptionForm.code_type === 'VIP' }"
              id="btn-type-vip"
              @click="selectRedemptionType('VIP')"
            >
              VIP 尊享会员兑换码 (VIP)
            </button>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">
            {{ generateRedemptionForm.code_type === 'COIN' ? '单张兑换金币面额 (枚)' : '单张兑换 VIP 会员时长 (天)' }}
            <span class="text-danger">*</span>
          </label>
          <div class="tag-quick-select" v-if="generateRedemptionForm.code_type === 'COIN'">
            <button
              v-for="preset in [50, 100, 200, 500, 1000]"
              :key="preset"
              type="button"
              class="tag-option-pill"
              :class="{ active: generateRedemptionForm.reward_amount === preset }"
              @click="generateRedemptionForm.reward_amount = preset"
            >
              {{ preset }} 金币
            </button>
          </div>
          <div class="tag-quick-select" v-else>
            <button
              v-for="preset in [{d: 7, l: '7天周卡'}, {d: 30, l: '30天月卡'}, {d: 90, l: '90天季卡'}, {d: 365, l: '365天年卡'}]"
              :key="preset.d"
              type="button"
              class="tag-option-pill"
              :class="{ active: generateRedemptionForm.reward_amount === preset.d }"
              @click="generateRedemptionForm.reward_amount = preset.d"
            >
              {{ preset.l }}
            </button>
          </div>
          <input
            v-model.number="generateRedemptionForm.reward_amount"
            type="number"
            min="1"
            max="100000"
            class="apple-input"
            id="input-redemption-reward-amount"
            :placeholder="generateRedemptionForm.code_type === 'COIN' ? '输入自定义金币数量' : '输入自定义 VIP 天数'"
          />
        </div>

        <div class="form-row-grid">
          <div class="form-group">
            <label class="form-label">生成卡密张数 (1 ~ 100)</label>
            <input
              v-model.number="generateRedemptionForm.count"
              type="number"
              min="1"
              max="100"
              class="apple-input"
              id="input-redemption-count"
              placeholder="默认 5 张"
            />
          </div>
          <div class="form-group">
            <label class="form-label">有效期天数 (留空为永久有效)</label>
            <input
              v-model.number="generateRedemptionForm.expires_days"
              type="number"
              min="1"
              max="3650"
              class="apple-input"
              id="input-redemption-expires"
              placeholder="留空默认永久有效"
            />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">批次发放备注说明 (选填)</label>
          <input
            v-model="generateRedemptionForm.remark"
            class="apple-input"
            id="input-redemption-remark"
            placeholder="例如：首期核心用户福利发放 / VIP 体验卡活动"
          />
        </div>

        <div v-if="lastGeneratedCodes.length > 0" class="generated-codes-preview-box" id="box-generated-codes-result">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-xs font-bold">本次新生成兑换码 ({{ lastGeneratedCodes.length }} 张)：</span>
            <button type="button" class="text-xs font-bold underline" style="color: #0071e3;" @click="copyLastGeneratedCodes">
              一键复制全部新码
            </button>
          </div>
          <div class="generated-codes-list font-mono text-xs">
            <div v-for="c in lastGeneratedCodes" :key="c.id" class="generated-code-line">
              <span>{{ c.code }}</span>
              <span>{{ c.code_type === 'COIN' ? `+${c.reward_amount}币` : `+${c.reward_amount}天VIP` }}</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="apple-btn-secondary" @click="showGenerateRedemptionDialog = false">关闭</button>
        <button
          class="apple-btn-primary"
          id="btn-submit-generate-redemption"
          :disabled="isGeneratingRedemption || generateRedemptionForm.reward_amount < 1"
          @click="handleConfirmGenerateRedemption"
        >
          {{ isGeneratingRedemption ? '正在加密生成...' : '立即生成兑换码' }}
        </button>
      </template>
    </el-dialog>

    <!-- 4号违规词风控智能体专属对话模态框 (ChatGPT 式体验，支持附件/图片与多轮滑动窗口) -->
    <UniversalAgentChatModal
      v-model="showAgent4ChatModal"
      agent-id="agent_4"
      agent-name="合规审片官"
      role-title="4号 违规词与合规风控智能体"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminHeader from '../components/AdminHeader.vue'
import CinemaAgentRagCenter from './CinemaAgentRagCenter.vue'
import AgentCommandCenter from '../components/AgentCommandCenter.vue'
import CinemaAgentMcpCenter from './CinemaAgentMcpCenter.vue'
import UniversalAgentChatModal from '../components/UniversalAgentChatModal.vue'
import { 
  DataLine, 
  TrendCharts, 
  Film, 
  Refresh, 
  Picture, 
  User, 
  Check, 
  Close, 
  Warning, 
  Setting, 
  Search, 
  Delete, 
  Edit, 
  Plus, 
  Switch, 
  Lock, 
  Unlock, 
  View, 
  Hide, 
  Fold, 
  Expand, 
  DocumentChecked, 
  ChatLineSquare,
  Rank,
  Upload,
  Promotion,
  Cpu,
  Connection
} from '@element-plus/icons-vue'
import { 
  adminApi, 
  getSystemAuditLogs,
  getSystemAuditStats,
  type AdminBiCards, 
  type AdminDramaItem, 
  type SystemCarouselItem, 
  type AdminUserItem, 
  type ApplicationItem,
  type AdminDanmakuItem,
  type AdminCommentItem,
  type BiTrendsData,
  type ReviewQueueItem,
  type SensitiveWordItem,
  type SensitiveWordTestResult,
  type AdminRedemptionCodeItem,
  type SystemAuditLogItem,
  type SystemAuditLogsQuery,
  type SystemAuditStatsData,
  type WallpaperConfigData,
  getAdminWallpaperConfig,
  updateAdminWallpaperConfig
} from '../api/admin'
import {
  ragApi,
  type RAGOverviewStats,
  type RAGCorpusItem,
  type RAGChunkItem,
  type RAGEvalRunItem
} from '../api/rag'

// Global Theme State Linked to AdminHeader & HTML attribute
const isDark = ref(typeof document !== 'undefined' ? (document.documentElement.getAttribute('data-theme') !== 'light') : true)

// Sidebar State
const isSidebarPinned = ref(true)
const isSidebarHovered = ref(false)
const isSidebarExpanded = computed(() => isSidebarPinned.value || isSidebarHovered.value)

function onSidebarMouseEnter() {
  if (!isSidebarPinned.value) {
    isSidebarHovered.value = true
  }
}

function onSidebarMouseLeave() {
  if (!isSidebarPinned.value) {
    isSidebarHovered.value = false
  }
}

function toggleSidebarPin() {
  isSidebarPinned.value = !isSidebarPinned.value
  isSidebarHovered.value = false
}

// Navigation Tab State
const route = useRoute()
const router = useRouter()
const currentTab = ref<'bi' | 'dramas' | 'sync' | 'carousels' | 'announcements' | 'redemption' | 'users' | 'applications' | 'contents' | 'engine' | 'rag' | 'agent-hub' | 'wallpaper' | 'mcp'>((route.query.tab as any) || localStorage.getItem('cinema_admin_tab') || 'bi')

const tabTitleMap: Record<string, string> = {
  bi: 'BI 全景驾驶舱与预测走势',
  dramas: '短剧资产编目与封面治理',
  sync: '网盘增量/全量同步中心',
  carousels: '首页 5 秒焦点轮播运营调度',
  announcements: '全员系统公告治理中枢',
  redemption: '金币与 VIP 会员兑换码资产中心',
  users: '用户管理与 RBAC 权限流转',
  applications: '资质双轨入驻审批 (创作者/审核员)',
  contents: '互动合规风控 (弹幕/评论机审)',
  engine: '模型引擎与 RAG 参数配置',
  rag: 'RAG 知识中台 & 算法四维评测',
  'agent-hub': '九大智能体总控台、Skills 挂载器与战术大屏',
  wallpaper: '登录主页壁纸引擎与全局视觉配置'
}

const currentTabTitle = computed(() => tabTitleMap[currentTab.value] || '管理控制台')

function selectTab(tab: any) {
  currentTab.value = tab
  localStorage.setItem('cinema_admin_tab', tab)
  router.replace({ query: { ...route.query, tab } }).catch(() => {})
  if (tab === 'bi') {
    loadAuditLogs()
    loadAuditStats()
    nextTick(() => initBiChart())
  } else if (tab === 'rag') {
    loadRagData()
  } else if (tab === 'announcements') {
    loadAnnouncements()
  loadRedemptionCodes()
  } else if (tab === 'redemption') {
    loadRedemptionCodes()
  } else if (tab === 'wallpaper') {
    loadAdminWallpaperConfig()
  }
}

// Data States
const loading = ref(false)
watch(
  () => route.query.tab,
  (newTab) => {
    if (newTab && typeof newTab === 'string' && newTab !== currentTab.value) {
      selectTab(newTab as any)
    }
  }
)

const biMetrics = ref<AdminBiCards>({
  total_views: 0,
  total_danmakus: 0,
  total_comments: 0,
  total_likes: 0,
  total_users: 0,
  active_creators: 0,
  active_reviewers: 0,
  banned_users: 0,
  pending_applications: 0,
  total_dramas: 0,
  total_episodes: 0
})

// ECharts Instance & Trends Data
const biChartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null
const biTrendsData = ref<BiTrendsData | null>(null)
const viralRankings = computed(() => biTrendsData.value?.viral_rankings || [])

// Dramas State
const dramasList = ref<AdminDramaItem[]>([])
const dramaSearchKeyword = ref('')
const dramaPage = ref(1)
const dramaPageSize = ref(10)
const selectedDramaIds = ref<string[]>([])
const defaultDramaPoster = "data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%22320%22%20height%3D%22480%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cdefs%3E%3ClinearGradient%20id%3D%22g%22%20x1%3D%220%25%22%20y1%3D%220%25%22%20x2%3D%22100%25%22%20y2%3D%22100%25%22%3E%3Cstop%20offset%3D%220%25%22%20stop-color%3D%22%231c1d22%22%2F%3E%3Cstop%20offset%3D%22100%25%22%20stop-color%3D%22%232c2d35%22%2F%3E%3C%2FlinearGradient%3E%3C%2Fdefs%3E%3Crect%20width%3D%22100%25%22%20height%3D%22100%25%22%20fill%3D%22url(%23g)%22%2F%3E%3Ctext%20x%3D%2250%25%22%20y%3D%2250%25%22%20fill%3D%22%238e8e93%22%20font-size%3D%2218%22%20font-family%3D%22sans-serif%22%20text-anchor%3D%22middle%22%20dy%3D%22.3em%22%3E%E5%AE%98%E6%96%B9%E6%B5%B7%E6%8A%A5%3C%2Ftext%3E%3C%2Fsvg%3E"

const filteredDramas = computed(() => {
  if (!dramaSearchKeyword.value.trim()) return dramasList.value
  const kw = dramaSearchKeyword.value.toLowerCase()
  return dramasList.value.filter(d => d.title.toLowerCase().includes(kw) || (d.category || '').toLowerCase().includes(kw))
})

const paginatedDramas = computed(() => {
  const start = (dramaPage.value - 1) * dramaPageSize.value
  return filteredDramas.value.slice(start, start + dramaPageSize.value)
})

const isAllDramasSelected = computed(() => {
  return paginatedDramas.value.length > 0 && paginatedDramas.value.every(d => selectedDramaIds.value.includes(d.id))
})

function toggleSelectAllDramas() {
  if (isAllDramasSelected.value) {
    selectedDramaIds.value = selectedDramaIds.value.filter(id => !paginatedDramas.value.some(d => d.id === id))
  } else {
    const curIds = paginatedDramas.value.map(d => d.id)
    selectedDramaIds.value = Array.from(new Set([...selectedDramaIds.value, ...curIds]))
  }
}

async function handleBatchDeleteDramas() {
  if (selectedDramaIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确定要批量彻底删除选中的 ${selectedDramaIds.value.length} 部短剧作品吗？其剧集资源也将一并移除！`, '批量删除短剧', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })
    const res: any = await adminApi.batchDeleteDramas(selectedDramaIds.value)
    ElMessage.success(res?.message || '批量删除短剧成功！')
    selectedDramaIds.value = []
    await loadDramas()
  } catch (err) {}
}

// Edit Cover & Metadata State
const showEditCoverDialog = ref(false)
const editingDrama = ref<AdminDramaItem | null>(null)
const editingCoverUrl = ref('')
const editingDramaPosters = ref<string[]>([])
const editingDramaMeta = ref({
  id: '',
  title: '',
  category: '',
  summary: '',
  status: 'PUBLISHED'
})
const imageUploadInputRef = ref<HTMLInputElement | null>(null)
const uploadingImage = ref(false)
const isCoverDragOver = ref(false)
const coverImgError = ref(false)

// Posters Carousel Dialog
const showPostersCarouselDialog = ref(false)
const activeDramaForPosters = ref<AdminDramaItem | null>(null)

// Sync State
const syncMode = ref<'incremental' | 'full'>('incremental')
const isSyncing = ref(false)
const syncResult = ref<any>(null)

// Carousels State
const carouselsList = ref<SystemCarouselItem[]>([])
const showCarouselDialog = ref(false)
const isEditingCarousel = ref(false)
const dramaOptionsList = ref<Array<{ id: string; title: string; category: string; cover_url: string; extra_images: string }>>([])
const selectedCarouselDramaId = ref('')
const selectedCarouselDramaModalId = ref('')
const workbenchImgError = ref(false)
const carouselForm = ref<Partial<SystemCarouselItem>>({
  title: '',
  subtitle: '',
  tag: '本周爆款榜首',
  cover_url: '',
  video_id: '',
  sort_order: 1,
  is_active: true
})

const selectedWorkbenchDrama = computed(() => {
  return dramaOptionsList.value.find(d => d.id === selectedCarouselDramaId.value)
})

const workbenchPreviewCover = computed(() => {
  if (selectedWorkbenchDrama.value?.cover_url) {
    return selectedWorkbenchDrama.value.cover_url
  }
  return carouselsList.value[0]?.cover_url || ''
})

const workbenchPreviewTitle = computed(() => {
  if (selectedWorkbenchDrama.value?.title) {
    return selectedWorkbenchDrama.value.title
  }
  return carouselsList.value[0]?.title || '首屏焦点画报推荐'
})

const workbenchPreviewSubtitle = computed(() => {
  if (selectedWorkbenchDrama.value?.category) {
    return selectedWorkbenchDrama.value.category + ' · 全网独家热播'
  }
  return carouselsList.value[0]?.subtitle || '沉浸式观剧，连播爽不停'
})

const workbenchPreviewTag = computed(() => {
  return carouselsList.value[0]?.tag || '本周爆款榜首'
})

// Users State
const usersList = ref<AdminUserItem[]>([])
const userSearchKeyword = ref('')
const userFilterRole = ref('ALL')
const userFilterStatus = ref('ALL')
const userTotalCount = ref(0)
const userPage = ref(1)
const userPageSize = ref(10)
const selectedUserIds = ref<string[]>([])

const isAllUsersSelected = computed(() => {
  return usersList.value.length > 0 && selectedUserIds.value.length === usersList.value.length
})

function toggleSelectAllUsers() {
  if (isAllUsersSelected.value) {
    selectedUserIds.value = []
  } else {
    selectedUserIds.value = usersList.value.map(u => u.id)
  }
}

async function handleBatchDeleteUsers() {
  if (selectedUserIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确定要批量永久删除选中的 ${selectedUserIds.value.length} 个用户账号吗？此操作将级联删除其全部关联数据！`, '批量删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })
    const res: any = await adminApi.batchDeleteUsers(selectedUserIds.value)
    ElMessage.success(res?.message || '批量删除成功！')
    selectedUserIds.value = []
    await loadUsers()
  } catch (err) {}
}

const showRoleDialog = ref(false)
const selectedUserForRole = ref<AdminUserItem | null>(null)
const selectedRole = ref('USER')

// User CRUD Modals
const showAddUserDialog = ref(false)
const addUserForm = ref({
  username: '',
  password: '',
  nickname: '',
  role: 'USER',
  coins: 50,
  vip_days: 0
})

const showEditUserDialog = ref(false)
const selectedUserForEdit = ref<AdminUserItem | null>(null)
const editUserForm = ref({
  id: '',
  username: '',
  nickname: '',
  password: '',
  role: 'USER',
  status: 'ACTIVE',
  coins_adjustment: 0,
  vip_days: 0
})

// Applications State
const applicationSubTab = ref<'creators' | 'reviewers'>('creators')
const pendingCreators = ref<ApplicationItem[]>([])
const pendingReviewers = ref<ApplicationItem[]>([])
const pendingCount = computed(() => pendingCreators.value.length + pendingReviewers.value.length)

// Content Moderation State
const contentSubTab = ref<'queue' | 'lexicon' | 'danmakus' | 'comments' | 'agent4_hitl' | 'inspection_history'>((route.query.subtab as any) || localStorage.getItem('cinema_admin_contents_subtab') || 'lexicon')
const reviewQueueList = ref<ReviewQueueItem[]>([])
const reviewQueueTotal = ref(0)
const reviewQueuePage = ref(1)
const reviewQueuePageSize = ref(10)
const pagedReviewQueueList = computed(() => {
  const start = (reviewQueuePage.value - 1) * reviewQueuePageSize.value
  return reviewQueueList.value.slice(start, start + reviewQueuePageSize.value)
})

const sensitiveWordsList = ref<SensitiveWordItem[]>([])
const sensitiveWordsTotal = ref(0)
const sensitiveWordPage = ref(1)
const sensitiveWordPageSize = ref(10)
const sensitiveWordSearch = ref('')
const sensitiveWordCategory = ref('ALL')
const sensitiveWordLevel = ref('ALL')
const sensitiveWordCategoriesStat = ref<Record<string, number>>({
  ALL: 0,
  违禁: 0,
  涉政: 0,
  暴恐: 0,
  涉黄: 0,
  辱骂: 0,
  广告: 0
})

const showAddWordDialog = ref(false)
const newWordForm = ref({
  word: '',
  category: '违禁',
  level: 'HIGH'
})

const dfaTestText = ref('')
const dfaTestResult = ref<SensitiveWordTestResult | null>(null)
const dfaTesting = ref(false)

const danmakusList = ref<AdminDanmakuItem[]>([])
const danmakuTotal = ref(0)
const danmakuPage = ref(1)
const danmakuPageSize = ref(10)
const pagedDanmakusList = computed(() => {
  const start = (danmakuPage.value - 1) * danmakuPageSize.value
  return danmakusList.value.slice(start, start + danmakuPageSize.value)
})
const selectedDanmakuIds = ref<string[]>([])
const danmakuSearchQuery = ref('')

const commentsList = ref<AdminCommentItem[]>([])
const commentTotal = ref(0)
const commentPage = ref(1)
const commentPageSize = ref(10)
const pagedCommentsList = computed(() => {
  const start = (commentPage.value - 1) * commentPageSize.value
  return commentsList.value.slice(start, start + commentPageSize.value)
})
const selectedCommentIds = ref<string[]>([])
const commentSearchQuery = ref('')

// 4号智能体巡检与自迭代状态
const isInspectingInteractions = ref(false)
const showInspectReportModal = ref(false)
const inspectReportData = ref<any>(null)
const selectedViolationIds = ref<string[]>([])
const showProposalsDrawer = ref(false)
const proposalsList = ref<any[]>([])
const proposalsPendingCount = ref(0)

// Engine Form
const engineForm = ref({
  modelName: localStorage.getItem('cinema_active_model') || 'deepseek-r1:7b',
  temperature: 0.7,
  prompt: '你是一位精通短剧镜头语言与剧情反转的电影解说伴读助手。'
})

let themeObserver: MutationObserver | null = null


// Announcements Governance State (Feature R3)
import { type AdminAnnouncementItem } from '../api/admin'

const announcementsList = ref<AdminAnnouncementItem[]>([])
const selectedAnnouncementIds = ref<string[]>([])

const isAllAnnouncementsSelected = computed(() => {
  return filteredAnnouncements.value.length > 0 && selectedAnnouncementIds.value.length === filteredAnnouncements.value.length
})

function toggleSelectAllAnnouncements() {
  if (isAllAnnouncementsSelected.value) {
    selectedAnnouncementIds.value = []
  } else {
    selectedAnnouncementIds.value = filteredAnnouncements.value.map(a => a.id)
  }
}

async function handleBatchDeleteAnnouncements() {
  if (selectedAnnouncementIds.value.length === 0) return
  const count = selectedAnnouncementIds.value.length
  if (!confirm(`确定要批量删除选中的 ${count} 条系统公告吗？`)) return
  try {
    const res = await adminApi.batchDeleteAnnouncements(selectedAnnouncementIds.value)
    if (res?.data) {
      selectedAnnouncementIds.value = []
      await loadAnnouncements()
      alert(`已成功批量清理 ${count} 条系统公告`)
    }
  } catch (err: any) {
    alert(err?.response?.data?.detail || err?.message || '批量删除失败')
  }
}
const announcementSearchKeyword = ref('')
const announcementStatusFilter = ref<'all' | 'published' | 'draft'>('all')
const loadingAnnouncements = ref(false)
const showAnnouncementModal = ref(false)
const announcementModalMode = ref<'create' | 'edit'>('create')
const editingAnnouncementId = ref('')
const isSubmittingAnnouncement = ref(false)

const announcementForm = ref({
  title: '',
  content: '',
  tag: '系统公告',
  is_published: true
})

const filteredAnnouncements = computed(() => {
  return announcementsList.value.filter(a => {
    if (announcementStatusFilter.value === 'published' && !a.is_published) return false
    if (announcementStatusFilter.value === 'draft' && a.is_published) return false
    if (announcementSearchKeyword.value.trim()) {
      const kw = announcementSearchKeyword.value.trim().toLowerCase()
      const matchTitle = (a.title || '').toLowerCase().includes(kw)
      const matchContent = (a.content || '').toLowerCase().includes(kw)
      const matchTag = (a.tag || '').toLowerCase().includes(kw)
      if (!matchTitle && !matchContent && !matchTag) return false
    }
    return true
  })
})

async function loadAnnouncements() {
  loadingAnnouncements.value = true
  try {
    const res = await adminApi.getAnnouncements(1, 100)
    if (res?.data?.items) {
      announcementsList.value = res.data.items
    }
  } catch (err) {
    console.warn('Failed to load announcements:', err)
  } finally {
    loadingAnnouncements.value = false
  }
}

function openCreateAnnouncementModal() {
  announcementModalMode.value = 'create'
  editingAnnouncementId.value = ''
  announcementForm.value = {
    title: '',
    content: '',
    tag: '系统公告',
    is_published: true
  }
  showAnnouncementModal.value = true
}

function openEditAnnouncementModal(item: AdminAnnouncementItem) {
  announcementModalMode.value = 'edit'
  editingAnnouncementId.value = item.id
  announcementForm.value = {
    title: item.title,
    content: item.content,
    tag: item.tag || '系统公告',
    is_published: item.is_published
  }
  showAnnouncementModal.value = true
}

async function submitAnnouncementModal() {
  if (!announcementForm.value.title.trim() || !announcementForm.value.content.trim()) {
    alert('请填写完整的公告标题与公告详情内容')
    return
  }
  isSubmittingAnnouncement.value = true
  try {
    if (announcementModalMode.value === 'create') {
      const res = await adminApi.createAnnouncement({
        title: announcementForm.value.title.trim(),
        content: announcementForm.value.content.trim(),
        tag: announcementForm.value.tag.trim() || '系统公告'
      })
      if (res?.data) {
        showAnnouncementModal.value = false
        await loadAnnouncements()
        alert('系统公告发布成功，已即刻向全员广播！')
      }
    } else {
      const res = await adminApi.updateAnnouncement(editingAnnouncementId.value, {
        title: announcementForm.value.title.trim(),
        content: announcementForm.value.content.trim(),
        tag: announcementForm.value.tag.trim() || '系统公告'
      })
      if (res?.data) {
        showAnnouncementModal.value = false
        await loadAnnouncements()
        alert('公告信息更新成功')
      }
    }
  } catch (err: any) {
    alert(err?.response?.data?.detail || err?.message || '操作失败')
  } finally {
    isSubmittingAnnouncement.value = false
  }
}

async function handleToggleAnnouncementStatus(item: AdminAnnouncementItem) {
  try {
    const res = await adminApi.updateAnnouncement(item.id, {
      is_published: item.is_published
    })
    if (res?.data) {
      // success
    }
  } catch (err: any) {
    item.is_published = !item.is_published
    alert(err?.response?.data?.detail || err?.message || '状态切换失败')
  }
}

async function handleDeleteAnnouncement(item: AdminAnnouncementItem) {
  if (!confirm(`确定要彻底删除公告《${item.title}》吗？关联的全员通知也将一并清理。`)) {
    return
  }
  try {
    const res = await adminApi.deleteAnnouncement(item.id)
    if (res) {
      await loadAnnouncements()
    }
  } catch (err: any) {
    alert(err?.response?.data?.detail || err?.message || '删除公告失败')
  }
}

// =========================================================================
// Redemption Codes Management (金币兑换码 & 会员兑换码)
// =========================================================================
const redemptionCodesList = ref<AdminRedemptionCodeItem[]>([])
const loadingRedemptionCodes = ref(false)
const redemptionSearchKeyword = ref('')
const redemptionTypeFilter = ref('')
const redemptionStatusFilter = ref('')
const selectedRedemptionIds = ref<string[]>([])
const redemptionSummary = ref({
  total_active: 0,
  total_used: 0,
  total_coins_redeemed: 0,
  total_vip_days_redeemed: 0
})

const showGenerateRedemptionDialog = ref(false)
const isGeneratingRedemption = ref(false)
const lastGeneratedCodes = ref<AdminRedemptionCodeItem[]>([])
const generateRedemptionForm = ref<{
  code_type: 'COIN' | 'VIP'
  reward_amount: number
  count: number
  expires_days: number | null
  remark: string
}>({
  code_type: 'COIN',
  reward_amount: 100,
  count: 5,
  expires_days: null,
  remark: ''
})

async function loadRedemptionCodes() {
  loadingRedemptionCodes.value = true
  try {
    const res = await adminApi.getRedemptionCodes({
      page: 1,
      per_page: 100,
      code_type: redemptionTypeFilter.value || undefined,
      status: redemptionStatusFilter.value || undefined,
      keyword: redemptionSearchKeyword.value.trim() || undefined
    })
    if (res?.data) {
      redemptionCodesList.value = res.data.items || []
      if (res.data.summary) {
        redemptionSummary.value = res.data.summary
      }
      selectedRedemptionIds.value = []
    }
  } catch (err: any) {
    console.error('Failed to load redemption codes:', err)
  } finally {
    loadingRedemptionCodes.value = false
  }
}

function selectRedemptionType(t: 'COIN' | 'VIP') {
  generateRedemptionForm.value.code_type = t
  generateRedemptionForm.value.reward_amount = t === 'COIN' ? 100 : 30
}

function openGenerateRedemptionDialog() {
  lastGeneratedCodes.value = []
  generateRedemptionForm.value = {
    code_type: 'COIN',
    reward_amount: 100,
    count: 5,
    expires_days: null,
    remark: ''
  }
  showGenerateRedemptionDialog.value = true
}

async function handleConfirmGenerateRedemption() {
  if (generateRedemptionForm.value.reward_amount < 1) {
    ElMessage.warning('面额或天数必须大于 0')
    return
  }
  isGeneratingRedemption.value = true
  try {
    const countVal = Math.min(100, Math.max(1, Number(generateRedemptionForm.value.count) || 1))
    const res = await adminApi.generateRedemptionCodes({
      code_type: generateRedemptionForm.value.code_type,
      reward_amount: Number(generateRedemptionForm.value.reward_amount),
      count: countVal,
      expires_days: generateRedemptionForm.value.expires_days ? Number(generateRedemptionForm.value.expires_days) : null,
      remark: generateRedemptionForm.value.remark.trim() || undefined
    })
    if (res?.data?.codes) {
      lastGeneratedCodes.value = res.data.codes
      ElMessage.success(res.message || `成功生成 ${res.data.count} 张兑换码`)
      await loadRedemptionCodes()
    }
  } catch (err: any) {
    ElMessage.error(err.message || '生成兑换码失败')
  } finally {
    isGeneratingRedemption.value = false
  }
}

function toggleRedemptionSelection(id: string) {
  const idx = selectedRedemptionIds.value.indexOf(id)
  if (idx >= 0) {
    selectedRedemptionIds.value.splice(idx, 1)
  } else {
    selectedRedemptionIds.value.push(id)
  }
}

function toggleSelectAllRedemptionCodes() {
  if (selectedRedemptionIds.value.length === redemptionCodesList.value.length) {
    selectedRedemptionIds.value = []
  } else {
    selectedRedemptionIds.value = redemptionCodesList.value.map(i => i.id)
  }
}

async function copySingleRedemptionCode(code: string) {
  try {
    await navigator.clipboard.writeText(code)
  } catch (e) {}
  ElMessage.success(`已复制兑换码：${code}`)
}

async function copyLastGeneratedCodes() {
  const text = lastGeneratedCodes.value.map(c => c.code).join('\n')
  try {
    await navigator.clipboard.writeText(text)
  } catch (e) {}
  ElMessage.success(`已复制全部 ${lastGeneratedCodes.value.length} 张新生成的兑换码`)
}

async function copyAllActiveRedemptionCodes() {
  const activeCodes = redemptionCodesList.value.filter(c => c.status === 'ACTIVE').map(c => c.code)
  if (activeCodes.length === 0) {
    ElMessage.warning('当前列表中没有待兑换的可用卡密')
    return
  }
  try {
    await navigator.clipboard.writeText(activeCodes.join('\n'))
  } catch (e) {}
  ElMessage.success(`已一键复制 ${activeCodes.length} 张可用兑换码`)
}

async function handleRevokeSingleCode(rc: AdminRedemptionCodeItem) {
  try {
    const res = await adminApi.batchRedemptionCodesAction({ code_ids: [rc.id], action: 'revoke' })
    if (res) {
      ElMessage.success(`已作废兑换码 ${rc.code}`)
      await loadRedemptionCodes()
    }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '作废失败')
  }
}

async function handleDeleteSingleCode(rc: AdminRedemptionCodeItem) {
  try {
    await adminApi.deleteRedemptionCode(rc.id)
    ElMessage.success(`已删除兑换码 ${rc.code}`)
    await loadRedemptionCodes()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '删除失败')
  }
}

async function handleBatchRedemptionAction(action: 'revoke' | 'delete') {
  if (selectedRedemptionIds.value.length === 0) return
  try {
    const res = await adminApi.batchRedemptionCodesAction({
      code_ids: selectedRedemptionIds.value,
      action
    })
    if (res) {
      ElMessage.success(res.message || '批量操作成功')
      await loadRedemptionCodes()
    }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '批量操作失败')
  }
}

const handleTabSwitchEvent = (e: any) => {
  if (e?.detail) {
    selectTab(e.detail)
  }
}

onMounted(async () => {
  window.addEventListener('switch-admin-tab', handleTabSwitchEvent)
  loadAnnouncements()
  if (route.query.tab && typeof route.query.tab === 'string') {
    currentTab.value = route.query.tab as any
  }
  await loadAllData()
  window.addEventListener('resize', handleWindowResize)

  themeObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.type === 'attributes' && m.attributeName === 'data-theme') {
        isDark.value = document.documentElement.getAttribute('data-theme') !== 'light'
        if (currentTab.value === 'bi') {
          initBiChart()
        } else if (currentTab.value === 'rag' && ragSubTab.value === 'benchmark') {
          initRagRadarChart()
        }
      }
    }
  })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
})

onUnmounted(() => {
  window.removeEventListener('switch-admin-tab', handleTabSwitchEvent)
  window.removeEventListener('resize', handleWindowResize)
  if (themeObserver) {
    themeObserver.disconnect()
    themeObserver = null
  }
  if (biChartResizeObserver) {
    biChartResizeObserver.disconnect()
    biChartResizeObserver = null
  }
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  if (ragRadarInstance) {
    ragRadarInstance.dispose()
    ragRadarInstance = null
  }
})

function handleWindowResize() {
  if (chartInstance) {
    chartInstance.resize()
  }
  if (ragRadarInstance) {
    ragRadarInstance.resize()
  }
}

async function loadAllData() {
  loading.value = true
  try {
    fetchAgent4Interrupts()
    await Promise.all([
      loadBiOverview(),
      loadBiTrends(),
      loadDramas(),
      loadDramaOptions(),
      loadCarousels(),
      loadUsers(),
      loadApplications(),
      loadContents(),
      loadRagData()
    ])
  } catch (e) {
    console.error('Failed to load admin overview data:', e)
  } finally {
    loading.value = false
  }
}

async function refreshCurrentTab() {
  loading.value = true
  try {
    if (currentTab.value === 'bi') {
      await Promise.all([loadBiOverview(), loadBiTrends()])
    } else if (currentTab.value === 'dramas') {
      await loadDramas()
    } else if (currentTab.value === 'carousels') {
      await loadCarousels()
    } else if (currentTab.value === 'users') {
      await loadUsers()
    } else if (currentTab.value === 'applications') {
      await loadApplications()
    } else if (currentTab.value === 'contents') {
      await loadContents()
    } else if (currentTab.value === 'redemption') {
      await loadRedemptionCodes()
    } else if (currentTab.value === 'rag') {
      await loadRagData()
    }
    ElMessage.success('数据已更新至最新状态')
  } catch (err: any) {
    ElMessage.error(err.message || '刷新失败')
  } finally {
    loading.value = false
  }
}

// =========================================================================
// BI & ECharts
// =========================================================================
const ragCenterMetrics = ref<any>({
  total_corpus: 4,
  total_chunks: 128,
  eval_run_count: 12,
  faithfulness_pct: 94.2,
  relevance_pct: 92.8,
  graph_entities_estimate: 908,
  status: 'NOMINAL'
})

const agentFleetMetrics = ref<any>({
  active_agents: 9,
  total_roundtable_sessions: 16,
  active_pets: 6,
  dispatch_latency_ms: 42,
  status: 'ONLINE'
})

const userOpsMetrics = ref<any>({
  vip_members: 8,
  coin_circulation: 4850,
  total_tips_count: 34,
  total_favorites_count: 58,
  audit_logs_count: 45,
  audit_success_rate: 98.5
})

// System Audit Log State
const auditLogsList = ref<SystemAuditLogItem[]>([])
const auditLogsTotal = ref(0)
const auditLogsLoading = ref(false)
const auditQuery = reactive<SystemAuditLogsQuery>({
  page: 1,
  page_size: 10,
  module: '',
  action: '',
  status: '',
  user_role: '',
  keyword: ''
})

const auditStats = ref<SystemAuditStatsData>({
  total_logs: 0,
  success_count: 0,
  failed_count: 0,
  warning_count: 0,
  success_rate: 100,
  recent_24h_count: 0,
  avg_latency_ms: 38,
  module_distribution: [],
  role_distribution: []
})

const selectedAuditDetail = ref<SystemAuditLogItem | null>(null)
const isAuditDetailDialogOpen = ref(false)
let biChartResizeObserver: ResizeObserver | null = null

async function loadAuditLogs() {
  auditLogsLoading.value = true
  try {
    const res: any = await getSystemAuditLogs(auditQuery)
    const data = res?.data?.data || res?.data || res
    if (data?.items) {
      auditLogsList.value = data.items
      auditLogsTotal.value = data.total || data.items.length
    }
  } catch (err: any) {
    console.warn('Failed to load audit logs:', err)
  } finally {
    auditLogsLoading.value = false
  }
}

async function loadAuditStats() {
  try {
    const res: any = await getSystemAuditStats()
    const data = res?.data?.data || res?.data || res
    if (data) {
      auditStats.value = data
    }
  } catch (err) {
    console.warn('Failed to load audit stats:', err)
  }
}

function handleAuditSearch() {
  auditQuery.page = 1
  loadAuditLogs()
}

function handleAuditPageChange(newPage: number) {
  auditQuery.page = newPage
  loadAuditLogs()
}

function viewAuditDetail(item: SystemAuditLogItem) {
  selectedAuditDetail.value = item
  isAuditDetailDialogOpen.value = true
}

async function loadBiOverview() {
  const res: any = await adminApi.getBiMetrics()
  const data = res?.data || res
  if (data?.bi_cards) {
    biMetrics.value = data.bi_cards
  }
  if (data?.rag_center) {
    ragCenterMetrics.value = data.rag_center
  }
  if (data?.agent_fleet) {
    agentFleetMetrics.value = data.agent_fleet
  }
  if (data?.user_operations) {
    userOpsMetrics.value = data.user_operations
  }
}

async function loadBiTrends() {
  const res: any = await adminApi.getBiTrends()
  const data = res?.data || res
  if (data) {
    biTrendsData.value = data
    nextTick(() => {
      initBiChart()
    })
  }
}

function initBiChart() {
  if (!biChartRef.value || !biTrendsData.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(biChartRef.value)
  }

  const { history, prediction } = biTrendsData.value
  const allDates = [...history.dates, ...prediction.dates]

  // Construct series data
  // History series: real values for history dates, null for prediction dates
  const historySeriesData = [
    ...history.views,
    ...prediction.dates.map(() => null)
  ]

  // Prediction series: bridges from last history date
  const lastHistoryVal = history.views[history.views.length - 1]
  const forecastSeriesData = [
    ...history.views.slice(0, -1).map(() => null),
    lastHistoryVal,
    ...prediction.forecast_views
  ]

  // Confidence Bounds for prediction (Robust differential stack to prevent truncation)
  const lowerData = [
    ...history.views.slice(0, -1).map(() => null),
    lastHistoryVal,
    ...prediction.lower_bound
  ]
  const diffData = [
    ...history.views.slice(0, -1).map(() => null),
    0,
    ...prediction.upper_bound.map((up, i) => Math.max(up - (prediction.lower_bound[i] || 0), 0))
  ]

  const isLight = document.documentElement.getAttribute('data-theme') === 'light'
  const axisTextColor = isLight ? '#48484a' : 'rgba(255, 255, 255, 0.65)'
  const axisLineColor = isLight ? 'rgba(0, 0, 0, 0.15)' : 'rgba(255, 255, 255, 0.2)'
  const splitLineColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)'
  const tooltipBg = isLight ? 'rgba(255, 255, 255, 0.96)' : 'rgba(28, 28, 30, 0.92)'
  const tooltipBorder = isLight ? 'rgba(0, 0, 0, 0.12)' : 'rgba(255, 255, 255, 0.15)'
  const tooltipTextColor = isLight ? '#1d1d1f' : '#FFFFFF'

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      textStyle: { color: tooltipTextColor, fontSize: 12 },
      formatter: (params: any) => {
        let str = `<div style="font-weight: bold; margin-bottom: 4px;">${params[0].axisValue}</div>`
        params.forEach((item: any) => {
          if (item.value !== null && item.value !== undefined && item.seriesName !== '置信区间下限') {
            const valFormatted = Number(item.value).toLocaleString()
            str += `<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${item.color};margin-right:6px;"></span>${item.seriesName}: <b>${valFormatted} 次</b></div>`
          }
        })
        return str
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '8%',
      top: '12%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: allDates,
      axisLine: { lineStyle: { color: axisLineColor } },
      axisLabel: { color: axisTextColor, fontSize: 11, fontWeight: isLight ? 600 : 400 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: splitLineColor } },
      axisLine: { show: true, lineStyle: { color: axisLineColor } },
      axisLabel: {
        color: axisTextColor,
        fontSize: 11,
        fontWeight: isLight ? 600 : 400,
        formatter: (val: number) => {
          return val >= 10000 ? (val / 10000).toFixed(1) + 'w' : val.toString()
        }
      }
    },
    series: [
      {
        name: '历史实测播放',
        type: 'line',
        smooth: true,
        data: historySeriesData,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#0071E3' },
        lineStyle: { width: 3, color: '#0071E3' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 113, 227, 0.4)' },
            { offset: 1, color: 'rgba(0, 113, 227, 0.0)' }
          ])
        }
      },
      {
        name: 'AI 预测走势 (Holt-Winters)',
        type: 'line',
        smooth: true,
        data: forecastSeriesData,
        symbol: 'diamond',
        symbolSize: 7,
        itemStyle: { color: '#30D158' },
        lineStyle: { width: 3, type: 'dashed', color: '#30D158' }
      },
      {
        name: '置信区间基底',
        type: 'line',
        data: lowerData,
        lineStyle: { opacity: 0 },
        stack: 'confidence-band',
        symbol: 'none'
      },
      {
        name: '置信区间带 (95%)',
        type: 'line',
        data: diffData,
        lineStyle: { opacity: 0 },
        areaStyle: {
          color: 'rgba(48, 209, 88, 0.16)'
        },
        stack: 'confidence-band',
        symbol: 'none'
      }
    ]
  }

  chartInstance.setOption(option)

  // Attach ResizeObserver for instant container self-healing
  if (biChartRef.value && typeof ResizeObserver !== 'undefined' && !biChartResizeObserver) {
    biChartResizeObserver = new ResizeObserver(() => {
      if (chartInstance) {
        chartInstance.resize()
      }
    })
    biChartResizeObserver.observe(biChartRef.value)
  }
}

// =========================================================================
// Dramas Management
// =========================================================================
async function loadDramas() {
  const res: any = await adminApi.getDramas({ per_page: 100 })
  const data = res?.data || res
  if (data?.items) {
    dramasList.value = data.items
  }
}

function filterDramas() {}

async function toggleDramaStatus(drama: AdminDramaItem) {
  const target = drama.status === 'PUBLISHED' ? 'HIDDEN' : 'PUBLISHED'
  try {
    await adminApi.toggleDramaStatus(drama.id, target)
    drama.status = target
    ElMessage.success(`短剧《${drama.title}》已成功${target === 'PUBLISHED' ? '上架发布' : '屏蔽下线'}`)
  } catch (err: any) {
    ElMessage.error(err.message || '修改状态失败')
  }
}

// =========================================================================
// Drama Cover & Metadata Governance (Feature 23)
// =========================================================================
function openEditCoverModal(drama: AdminDramaItem) {
  editingDrama.value = drama
  editingCoverUrl.value = drama.effective_cover || drama.custom_cover_url || drama.cover_url || ''
  coverImgError.value = false
  editingDramaPosters.value = [...(drama.extra_images || [])]
  if (editingCoverUrl.value && !editingDramaPosters.value.includes(editingCoverUrl.value)) {
    editingDramaPosters.value.unshift(editingCoverUrl.value)
  }
  editingDramaMeta.value = {
    id: drama.id,
    title: drama.title,
    category: drama.category || '微短剧',
    summary: drama.summary || '',
    status: drama.status || 'PUBLISHED'
  }
  showEditCoverDialog.value = true
}

function triggerUploadImage() {
  imageUploadInputRef.value?.click()
}

async function handleImageFileSelected(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    await doUploadImageFile(file)
  }
  target.value = ''
}

async function handleCoverDrop(e: DragEvent) {
  isCoverDragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) {
    await doUploadImageFile(file)
  }
}

async function doUploadImageFile(file: File) {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    ElMessage.error('仅支持 JPG, PNG, WEBP 格式图片')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('图片体积不能超过 10MB')
    return
  }
  uploadingImage.value = true
  try {
    const res: any = await adminApi.uploadImage(file)
    const url = res?.data?.url || res?.url
    if (url) {
      editingCoverUrl.value = url
      coverImgError.value = false
      if (!editingDramaPosters.value.includes(url)) {
        editingDramaPosters.value.push(url)
      }
      ElMessage.success('图片安全上传成功！')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '图片上传失败')
  } finally {
    uploadingImage.value = false
  }
}

function setAsMainCover(imgUrl: string) {
  editingCoverUrl.value = imgUrl
  coverImgError.value = false
  ElMessage.success('已设为主封面')
}

function removePoster(idx: number) {
  editingDramaPosters.value.splice(idx, 1)
}

async function confirmUpdateCover() {
  if (!editingDrama.value) return
  try {
    await adminApi.updateDrama(editingDrama.value.id, {
      title: editingDramaMeta.value.title,
      category: editingDramaMeta.value.category,
      summary: editingDramaMeta.value.summary,
      status: editingDramaMeta.value.status
    })
    if (editingCoverUrl.value.trim()) {
      await adminApi.updateDramaCover(editingDrama.value.id, editingCoverUrl.value.trim())
      editingDrama.value.custom_cover_url = editingCoverUrl.value.trim()
      editingDrama.value.effective_cover = editingCoverUrl.value.trim()
    }
    await adminApi.updateDramaPosters(editingDrama.value.id, editingDramaPosters.value)
    editingDrama.value.extra_images = [...editingDramaPosters.value]
    showEditCoverDialog.value = false
    ElMessage.success('短剧信息与封面画报已成功保存！')
    await loadDramas()
    await loadDramaOptions()
  } catch (err: any) {
    ElMessage.error(err.message || '保存短剧封面与元数据失败')
  }
}

function openPosterCarousel(drama: AdminDramaItem) {
  activeDramaForPosters.value = drama
  showPostersCarouselDialog.value = true
}

async function handleDeleteDrama(drama: AdminDramaItem) {
  try {
    await ElMessageBox.confirm(
      `确定要从平台物理删除短剧《${drama.title}》及其全部分集记录吗？此操作无法撤销。`,
      '危险删除提示',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' }
    )
    await adminApi.deleteDrama(drama.id)
    dramasList.value = dramasList.value.filter(d => d.id !== drama.id)
    ElMessage.success(`短剧《${drama.title}》已彻底移除`)
  } catch (e) {
    // cancelled
  }
}

// =========================================================================
// Sync Pan
// =========================================================================
function openSyncDialog() {
  currentTab.value = 'sync'
}

async function executeSync() {
  isSyncing.value = true
  syncResult.value = null
  try {
    const res: any = await adminApi.syncPanAll(syncMode.value)
    const data = res?.data || res
    syncResult.value = data
    ElMessage.success(`网盘同步成功完成！共映射 ${data.total_synced_dramas} 部短剧，新增 ${data.new_episodes_added} 集`)
    await loadDramas()
  } catch (err: any) {
    ElMessage.error(err.message || '网盘同步失败，请检查 OpenList 网关是否在线')
  } finally {
    isSyncing.value = false
  }
}

// =========================================================================
// Carousels (Feature 24: 16:9 WYSIWYG Live Preview)
// =========================================================================
async function loadDramaOptions() {
  try {
    const res: any = await adminApi.getDramaOptions()
    const data = res?.data || res
    if (Array.isArray(data)) {
      dramaOptionsList.value = data
      if (data.length > 0 && !selectedCarouselDramaId.value) {
        selectedCarouselDramaId.value = data[0].id
      }
    }
  } catch (e) {
    console.error('Failed to load drama options:', e)
  }
}

function handleQuickSelectDrama() {
  workbenchImgError.value = false
}

function applyWorkbenchToModal() {
  const d = selectedWorkbenchDrama.value
  if (!d) return
  isEditingCarousel.value = false
  selectedCarouselDramaModalId.value = d.id
  carouselForm.value = {
    title: d.title,
    subtitle: (d.category || '短剧') + ' · 独播首发',
    tag: '今日焦点推荐',
    cover_url: d.cover_url,
    video_id: d.id,
    sort_order: carouselsList.value.length + 1,
    is_active: true
  }
  showCarouselDialog.value = true
}

function handleModalSelectDrama() {
  const d = dramaOptionsList.value.find(item => item.id === selectedCarouselDramaModalId.value)
  if (d) {
    carouselForm.value.video_id = d.id
    carouselForm.value.title = d.title
    carouselForm.value.cover_url = d.cover_url
    carouselForm.value.subtitle = (d.category || '短剧') + ' · 独播首发'
  }
}

async function loadCarousels() {
  const res: any = await adminApi.getCarousels()
  const data = res?.data || res
  if (Array.isArray(data)) {
    carouselsList.value = data
  }
}

function openCreateCarouselModal() {
  isEditingCarousel.value = false
  selectedCarouselDramaModalId.value = ''
  carouselForm.value = {
    title: '',
    subtitle: '',
    tag: '今日焦点推荐',
    cover_url: '',
    video_id: '',
    sort_order: carouselsList.value.length + 1,
    is_active: true
  }
  showCarouselDialog.value = true
}

function openEditCarouselModal(item: SystemCarouselItem) {
  isEditingCarousel.value = true
  selectedCarouselDramaModalId.value = item.video_id || ''
  carouselForm.value = { ...item }
  showCarouselDialog.value = true
}

async function saveCarousel() {
  if (!carouselForm.value.title || !carouselForm.value.cover_url) {
    ElMessage.warning('请填写标题文案与海报图片地址')
    return
  }
  try {
    if (isEditingCarousel.value && carouselForm.value.id) {
      await adminApi.updateCarousel(carouselForm.value.id, carouselForm.value)
      ElMessage.success('轮播焦点更新成功')
    } else {
      await adminApi.createCarousel(carouselForm.value)
      ElMessage.success('新增轮播焦点成功')
    }
    showCarouselDialog.value = false
    await loadCarousels()
  } catch (err: any) {
    ElMessage.error(err.message || '保存轮播图失败')
  }
}

async function handleToggleCarouselActive(item: SystemCarouselItem) {
  try {
    await adminApi.updateCarousel(item.id, { is_active: item.is_active })
    ElMessage.success(`轮播焦点已${item.is_active ? '启用上线' : '暂停下线'}`)
  } catch (err: any) {
    item.is_active = !item.is_active
    ElMessage.error(err.message || '修改状态失败')
  }
}

async function handleDeleteCarousel(item: SystemCarouselItem) {
  try {
    await ElMessageBox.confirm(`确定删除轮播条目《${item.title}》吗？`, '删除提示')
    await adminApi.deleteCarousel(item.id)
    carouselsList.value = carouselsList.value.filter(c => c.id !== item.id)
    ElMessage.success('轮播条目已删除')
  } catch (e) {}
}

// =========================================================================
// Users Management & Full CRUD (Feature 22)
// =========================================================================
async function loadUsers() {
  try {
    const params: any = {
      page: userPage.value,
      per_page: userPageSize.value
    }
    if (userSearchKeyword.value.trim()) params.search = userSearchKeyword.value.trim()
    if (userFilterRole.value && userFilterRole.value !== 'ALL') params.role = userFilterRole.value
    const res: any = await adminApi.getUsers(params)
    const data = res?.data || res
    if (data?.items) {
      let items = data.items
      if (userFilterStatus.value && userFilterStatus.value !== 'ALL') {
        items = items.filter((u: any) => u.status === userFilterStatus.value)
      }
      usersList.value = items
      userTotalCount.value = data.total || items.length
    }
  } catch (e) {
    console.error('Failed to load users:', e)
  }
}

function openAddUserModal() {
  addUserForm.value = {
    username: '',
    password: '',
    nickname: '',
    role: 'USER',
    coins: 50,
    vip_days: 0
  }
  showAddUserDialog.value = true
}

async function confirmAddUser() {
  if (!addUserForm.value.username.trim() || !addUserForm.value.password.trim()) {
    ElMessage.warning('用户名与密码为必填项')
    return
  }
  try {
    await adminApi.createUser({
      username: addUserForm.value.username.trim(),
      password: addUserForm.value.password.trim(),
      nickname: addUserForm.value.nickname.trim() || undefined,
      role: addUserForm.value.role,
      coins: addUserForm.value.coins ?? 50,
      vip_days: addUserForm.value.vip_days ?? 0
    })
    ElMessage.success(`用户 @${addUserForm.value.username} 创建成功！`)
    showAddUserDialog.value = false
    await loadUsers()
  } catch (err: any) {
    ElMessage.error(err.message || '创建用户失败')
  }
}

function openEditUserModal(user: AdminUserItem) {
  selectedUserForEdit.value = user
  editUserForm.value = {
    id: user.id,
    username: user.username,
    nickname: user.nickname || '',
    password: '',
    role: user.role,
    status: user.status,
    coins_adjustment: 0,
    vip_days: 0
  }
  showEditUserDialog.value = true
}

async function confirmEditUser() {
  if (!selectedUserForEdit.value) return
  try {
    const payload: any = {
      nickname: editUserForm.value.nickname.trim(),
      role: editUserForm.value.role,
      status: editUserForm.value.status
    }
    if (editUserForm.value.password.trim()) {
      payload.password = editUserForm.value.password.trim()
    }
    if (editUserForm.value.coins_adjustment !== 0) {
      payload.coins_adjustment = editUserForm.value.coins_adjustment
    }
    if (editUserForm.value.vip_days !== 0) {
      payload.vip_days = editUserForm.value.vip_days
    }
    await adminApi.updateUser(selectedUserForEdit.value.id, payload)
    ElMessage.success(`用户 @${selectedUserForEdit.value.username} 资料更新成功`)
    showEditUserDialog.value = false
    await loadUsers()
  } catch (err: any) {
    ElMessage.error(err.message || '更新用户失败')
  }
}

async function handleDeleteUser(user: AdminUserItem) {
  try {
    await ElMessageBox.confirm(
      `确定要从平台物理删除用户 @${user.username} 吗？此操作将级联清理其所有互动资产，无法撤销。`,
      '危险删除提示',
      { confirmButtonText: '确认物理删除', cancelButtonText: '取消', type: 'warning' }
    )
    await adminApi.deleteUser(user.id)
    ElMessage.success(`用户 @${user.username} 已被物理清除`)
    await loadUsers()
  } catch (e) {
    // cancelled
  }
}

function openRoleModal(user: AdminUserItem) {
  selectedUserForRole.value = user
  selectedRole.value = user.role
  showRoleDialog.value = true
}

async function confirmChangeRole() {
  if (!selectedUserForRole.value) return
  try {
    await adminApi.updateUserRole(selectedUserForRole.value.id, selectedRole.value)
    selectedUserForRole.value.role = selectedRole.value
    showRoleDialog.value = false
    ElMessage.success(`用户 ${selectedUserForRole.value.username} 角色已调整为 ${getRoleLabel(selectedRole.value)}`)
  } catch (err: any) {
    ElMessage.error(err.message || '调权失败')
  }
}

async function toggleUserStatus(user: AdminUserItem) {
  const target = user.status === 'ACTIVE' ? 'BANNED' : 'ACTIVE'
  try {
    await adminApi.updateUserStatus(user.id, target)
    user.status = target
    ElMessage.success(`用户 ${user.username} 账号已${target === 'ACTIVE' ? '解除封禁' : '封禁阻断'}`)
  } catch (err: any) {
    ElMessage.error(err.message || '修改用户状态失败')
  }
}

// =========================================================================
// Applications (Dual Track)
// =========================================================================
async function loadApplications() {
  const res: any = await adminApi.getApplications()
  const data = res?.data || res
  if (data) {
    pendingCreators.value = (data.creators || []).filter((c: any) => c.status === 'PENDING')
    pendingReviewers.value = (data.reviewers || []).filter((r: any) => r.status === 'PENDING')
  }
}

async function handleApproveApplication(app: ApplicationItem) {
  try {
    if (applicationSubTab.value === 'creators') {
      await adminApi.reviewCreator(app.user_id, 'APPROVE')
      pendingCreators.value = pendingCreators.value.filter(c => c.user_id !== app.user_id)
      ElMessage.success(`创作者 ${app.username} 入驻申请已批准，创作者空间与发布特权已下发！`)
    } else {
      await adminApi.reviewReviewer(app.user_id, 'APPROVE')
      pendingReviewers.value = pendingReviewers.value.filter(r => r.user_id !== app.user_id)
      ElMessage.success(`审核员 ${app.username} 资质已批准，机审中台巡检特权已下发！`)
    }
  } catch (err: any) {
    ElMessage.error(err.message || '审批操作失败')
  }
}

async function handleRejectApplication(app: ApplicationItem) {
  try {
    if (applicationSubTab.value === 'creators') {
      await adminApi.reviewCreator(app.user_id, 'REJECT')
      pendingCreators.value = pendingCreators.value.filter(c => c.user_id !== app.user_id)
    } else {
      await adminApi.reviewReviewer(app.user_id, 'REJECT')
      pendingReviewers.value = pendingReviewers.value.filter(r => r.user_id !== app.user_id)
    }
    ElMessage.info('申请已驳回')
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  }
}

// =========================================================================
// Content Moderation (工单流、敏感词库、弹幕与评论)
// =========================================================================
// 4号违规词风控智能体专属状态
const showAgent4ChatModal = ref(false)
const agent4QuickAuditText = ref('')
const isAgent4QuickAuditing = ref(false)
const agent4QuickAuditResult = ref<any>(null)

function openAgent4Chat(initialText?: string) {
  if (initialText && typeof initialText === 'string') {
    agent4QuickAuditText.value = initialText
  }
  showAgent4ChatModal.value = true
}

async function runAgent4QuickAudit() {
  const query = agent4QuickAuditText.value.trim()
  if (!query || isAgent4QuickAuditing.value) return
  isAgent4QuickAuditing.value = true
  agent4QuickAuditResult.value = null
  const startTime = performance.now()
  try {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const res = await axios.post('/api/v1/agent-hub/dispatch', {
      agent_id: 'agent_4',
      query: `请作为4号合规审片官，对以下输入文本进行深度风控毒性与违规研判，指出是否违规并说明原因：\n\n${query}`,
    }, { headers })
    const data = res.data?.data || {}
    const ans = data.answer || ''
    const actualCostMs = Math.max(1, Math.round(performance.now() - startTime))

    const tLower = query.toLowerCase()
    const ansLower = ans.toLowerCase()

    // 1. 本地高危辱骂词库优先判定 (防错判)
    const isLocalVulgar = /操你妈|草你妈|傻逼|煞笔|操死|妈逼|nmsl|cnm|去死|狗杂种/.test(tLower)
    
    // 2. 云端安全拒绝策略检测 (High Risk Refusal)
    const isCloudRejected = ansLower.includes('rejected') || ansLower.includes('high risk') || ansLower.includes('safety')

    // 3. 大模型风控研判
    const isModelViolated = ans.includes('违规') || ans.includes('拦截') || ans.includes('高危') || ans.includes('不合规')
    const isModelWarn = ans.includes('敏感') || ans.includes('低俗') || ans.includes('注意') || ans.includes('争议')

    let riskLevel = 'LOW'
    let finalReason = ans

    if (isLocalVulgar || isCloudRejected || isModelViolated) {
      riskLevel = 'HIGH'
      if (isCloudRejected) {
        finalReason = `【触发高危安全策略拦截】云端大模型安全守卫已拒绝该内容：${ans}。本地风控判定为 HIGH 级违规。`
      } else if (isLocalVulgar && !isModelViolated) {
        finalReason = `【命中本地高危敏感特征】检测到明显辱骂违规用语，本地状态机已触发阻断。`
      }
    } else if (isModelWarn) {
      riskLevel = 'MEDIUM'
    }

    agent4QuickAuditResult.value = {
      risk_level: riskLevel,
      reason: finalReason || '4号智能体机审完成，该文本符合平台合规要求。',
      cost_ms: actualCostMs
    }
    ElMessage.success('4号合规审片官完成机审研判')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '4号智能体机审调用失败')
  } finally {
    isAgent4QuickAuditing.value = false
  }
}

const agent4Interrupts = ref<any[]>([])
const hitlCurrentPage = ref(1)
const hitlPageSize = ref(5)
const pagedAgent4Interrupts = computed(() => {
  const list = agent4Interrupts.value || []
  const start = (hitlCurrentPage.value - 1) * hitlPageSize.value
  return list.slice(start, start + hitlPageSize.value)
})

async function fetchAgent4Interrupts() {
  try {
    const res = await axios.get('/api/v1/agent-hub/overview')
    agent4Interrupts.value = res.data?.data?.moderation_interrupts || []
  } catch (e) {
    console.warn('Failed to load agent 4 interrupts:', e)
  }
}

async function handleResumeAgent4Interrupt(interruptId: string, action: string) {
  try {
    const res = await axios.post(`/api/v1/agent-hub/moderation/interrupts/${interruptId}/resume`, {
      action,
      reviewer_note: action === 'APPROVE' ? '审核员在互动合规风控台复核放行' : '审核员在互动合规风控台判定违规拦截'
    })
    ElMessage.success(res.data?.message || '已执行回环裁决')
    await fetchAgent4Interrupts()
  } catch (e) {
    ElMessage.error('裁决执行失败')
  }
}

function switchContentSubTab(tab: 'queue' | 'lexicon' | 'danmakus' | 'comments' | 'agent4_hitl' | 'inspection_history') {
  contentSubTab.value = tab
  localStorage.setItem('cinema_admin_contents_subtab', tab)
  router.replace({ query: { ...route.query, subtab: tab } }).catch(() => {})
  if (tab === 'inspection_history') {
    fetchInspectionHistory(1)
  }
  if (tab === 'queue') {
    loadReviewQueue()
  } else if (tab === 'lexicon') {
    loadSensitiveWords()
  } else if (tab === 'agent4_hitl') {
    fetchAgent4Interrupts()
  } else if (tab === 'danmakus') {
    fetchDanmakus(1)
  } else if (tab === 'comments') {
    fetchComments(1)
  }
}

async function fetchSensitiveCategoriesStat() {
  try {
    const res: any = await adminApi.getSensitiveWordCategoriesStat()
    if (res?.data) {
      sensitiveWordCategoriesStat.value = { ...sensitiveWordCategoriesStat.value, ...res.data }
    }
  } catch (e) {
    console.error('Failed to fetch categories stat:', e)
  }
}

async function loadContents() {
  try {
    await Promise.all([
      fetchDanmakus(1),
      fetchComments(1),
      loadReviewQueue(1),
      loadSensitiveWords(1),
      fetchSensitiveCategoriesStat(),
      fetchWordProposals()
    ])
  } catch (e) {
    console.error('Error loading content moderation records:', e)
  }
}

async function loadReviewQueue(page = 1) {
  try {
    reviewQueuePage.value = page
    const res: any = await adminApi.getReviewQueue('PENDING')
    const list = res?.data || res || []
    reviewQueueList.value = list
    reviewQueueTotal.value = list.length
  } catch (e) {
    console.error('Failed to load review queue:', e)
  }
}

async function handleReviewDecision(reviewId: string, decision: 'APPROVED' | 'REJECTED') {
  try {
    await adminApi.makeReviewDecision(reviewId, decision)
    reviewQueueList.value = reviewQueueList.value.filter(r => r.id !== reviewId)
    reviewQueueTotal.value = Math.max(0, reviewQueueTotal.value - 1)
    ElMessage.success(`风控裁决已生效：${decision === 'APPROVED' ? '放行通过' : '违规驳回并清理'}`)
  } catch (err: any) {
    ElMessage.error(err.message || '裁决操作失败')
  }
}

async function handleCategoryPillClick(cat: string) {
  sensitiveWordCategory.value = cat
  await loadSensitiveWords(1)
}

async function loadSensitiveWords(page = 1) {
  try {
    sensitiveWordPage.value = page
    const res: any = await adminApi.getSensitiveWords({
      query: sensitiveWordSearch.value.trim() || undefined,
      category: sensitiveWordCategory.value !== 'ALL' ? sensitiveWordCategory.value : undefined,
      level: sensitiveWordLevel.value !== 'ALL' ? sensitiveWordLevel.value : undefined,
      page: sensitiveWordPage.value,
      per_page: sensitiveWordPageSize.value
    })
    const data = res?.data || res
    sensitiveWordsList.value = data?.items || []
    sensitiveWordsTotal.value = data?.total || 0
    await fetchSensitiveCategoriesStat()
  } catch (e) {
    console.error('Failed to load sensitive words:', e)
  }
}

function openAddWordModal() {
  newWordForm.value = { word: '', category: '违禁', level: 'HIGH' }
  showAddWordDialog.value = true
}

async function confirmAddSensitiveWord() {
  if (!newWordForm.value.word.trim()) return
  try {
    await adminApi.addSensitiveWord({
      word: newWordForm.value.word.trim(),
      category: newWordForm.value.category,
      level: newWordForm.value.level
    })
    showAddWordDialog.value = false
    ElMessage.success(`敏感词 [${newWordForm.value.word.trim()}] 录入成功，DFA 已热重载！`)
    sensitiveWordSearch.value = ''
    sensitiveWordCategory.value = 'ALL'
    sensitiveWordLevel.value = 'ALL'
    await loadSensitiveWords(1)
  } catch (err: any) {
    ElMessage.error(err.message || '录入敏感词失败')
  }
}

async function handleDeleteSensitiveWord(item: SensitiveWordItem) {
  try {
    await adminApi.deleteSensitiveWord(item.id)
    sensitiveWordsList.value = sensitiveWordsList.value.filter(w => w.id !== item.id)
    sensitiveWordsTotal.value = Math.max(0, sensitiveWordsTotal.value - 1)
    ElMessage.success(`已删除敏感词 [${item.word}]，DFA 树已更新`)
    await fetchSensitiveCategoriesStat()
  } catch (err: any) {
    ElMessage.error(err.message || '删除敏感词失败')
  }
}

async function runDfaTest() {
  if (!dfaTestText.value.trim()) return
  dfaTesting.value = true
  try {
    const res: any = await adminApi.testSensitiveWords(dfaTestText.value.trim())
    dfaTestResult.value = res?.data || res
  } catch (err: any) {
    ElMessage.error(err.message || '检测失败')
  } finally {
    dfaTesting.value = false
  }
}

async function fetchDanmakus(page = 1) {
  try {
    danmakuPage.value = page
    const dmRes: any = await adminApi.getDanmakus({
      per_page: 50,
      keyword: danmakuSearchQuery.value.trim() || undefined
    })
    const items = dmRes?.data?.items || dmRes?.items || []
    danmakusList.value = items
    danmakuTotal.value = items.length
  } catch (e: any) {
    ElMessage.error(e.message || '查询弹幕列表失败')
  }
}

async function fetchComments(page = 1) {
  try {
    commentPage.value = page
    const cmRes: any = await adminApi.getComments({
      per_page: 50,
      search: commentSearchQuery.value.trim() || undefined
    })
    const items = cmRes?.data?.items || cmRes?.items || []
    commentsList.value = items
    commentTotal.value = items.length
  } catch (e: any) {
    ElMessage.error(e.message || '查询评论列表失败')
  }
}

function toggleSelectAllDanmakus(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.checked) {
    selectedDanmakuIds.value = pagedDanmakusList.value.map(d => d.id)
  } else {
    selectedDanmakuIds.value = []
  }
}

async function handleBatchDeleteDanmakus() {
  if (selectedDanmakuIds.value.length === 0) {
    ElMessage.warning('请先勾选需要下架的弹幕')
    return
  }
  try {
    const res: any = await adminApi.batchDeleteDanmakus(selectedDanmakuIds.value)
    ElMessage.success(res?.message || `已成功批量下架 ${selectedDanmakuIds.value.length} 条违规弹幕`)
    danmakusList.value = danmakusList.value.filter(d => !selectedDanmakuIds.value.includes(d.id))
    danmakuTotal.value = danmakusList.value.length
    selectedDanmakuIds.value = []
  } catch (err: any) {
    ElMessage.error(err.message || '批量删除失败')
  }
}

async function handleDeleteDanmaku(id: string) {
  try {
    await adminApi.deleteDanmaku(id)
    danmakusList.value = danmakusList.value.filter(d => d.id !== id)
    danmakuTotal.value = danmakusList.value.length
    selectedDanmakuIds.value = selectedDanmakuIds.value.filter(item => item !== id)
    ElMessage.success('违规弹幕已移除并清退')
  } catch (err: any) {
    ElMessage.error(err.message || '删除失败')
  }
}

async function handleDeleteComment(id: string) {
  try {
    await adminApi.deleteComment(id)
    commentsList.value = commentsList.value.filter(c => c.id !== id)
    commentTotal.value = commentsList.value.length
    ElMessage.success('违规评论已清理')
  } catch (err: any) {
    ElMessage.error(err.message || '删除失败')
  }
}

// 4号合规审片官: 按需一键批量巡检

// 4号合规官巡检历史与动态进度条状态
const inspectProgress = ref(0)
const inspectProgressStage = ref('')
let inspectTimer: any = null

const inspectionHistoryList = ref<any[]>([])
const inspectionHistoryTotal = ref(0)
const inspectionHistoryPage = ref(1)
const inspectionHistoryPageSize = ref(10)
const isHistoryLoading = ref(false)

async function fetchInspectionHistory(page = 1) {
  isHistoryLoading.value = true
  try {
    inspectionHistoryPage.value = page
    const res: any = await adminApi.getInspectionHistory({
      page: inspectionHistoryPage.value,
      per_page: inspectionHistoryPageSize.value
    })
    const data = res?.data || {}
    inspectionHistoryList.value = data.items || []
    inspectionHistoryTotal.value = data.total || 0
  } catch (err: any) {
    console.error('Failed to load inspection history:', err)
  } finally {
    isHistoryLoading.value = false
  }
}

async function handleViewHistoricalReport(logId: string) {
  try {
    const res: any = await adminApi.getInspectionHistoryDetail(logId)
    const detail = res?.data || {}
    inspectReportData.value = detail.report || {}
    selectedViolationIds.value = (detail.report?.violations || []).map((v: any) => v.id)
    showInspectReportModal.value = true
  } catch (err: any) {
    ElMessage.error(err.message || '获取历史巡检报告快照失败')
  }
}

async function triggerAgent4BatchInspect(targetType: 'danmaku' | 'comment') {
  isInspectingInteractions.value = true
  inspectProgress.value = 10
  inspectProgressStage.value = '准备语料，清洗待审文本...'
  if (inspectTimer) clearInterval(inspectTimer)
  inspectTimer = setInterval(() => {
    if (inspectProgress.value < 35) {
      inspectProgress.value += 5
      inspectProgressStage.value = 'DFA 前缀状态机特征快速初筛匹配...'
    } else if (inspectProgress.value < 75) {
      inspectProgress.value += 4
      inspectProgressStage.value = '4号合规官深度大模型语义与毒性研判...'
    } else if (inspectProgress.value < 95) {
      inspectProgress.value += 2
      inspectProgressStage.value = '提炼变体暗语黑话，汇编巡检研判快照报告...'
    }
  }, 600)

  try {
    const res: any = await adminApi.batchInspectInteractions({ target_type: targetType, limit: 30 })
    const report = res?.data || {}
    inspectProgress.value = 100
    inspectProgressStage.value = '巡检完成，正在呈现报告...'
    inspectReportData.value = report
    selectedViolationIds.value = (report.violations || []).map((v: any) => v.id)
    showInspectReportModal.value = true
    ElMessage.success(res?.message || '4号合规官巡检研判完成！')
    await fetchWordProposals()
    await fetchInspectionHistory(1)
  } catch (err: any) {
    const detail = err?.response?.data?.detail || err?.response?.data?.message || err?.message || '响应超时或服务繁忙'
    ElMessage.error('4号合规官批量巡检提示: ' + (detail || '服务繁忙'))
  } finally {
    if (inspectTimer) clearInterval(inspectTimer)
    setTimeout(() => {
      isInspectingInteractions.value = false
      inspectProgress.value = 0
    }, 400)
  }
}

function toggleSelectAllViolationsInModal(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.checked && inspectReportData.value?.violations) {
    selectedViolationIds.value = inspectReportData.value.violations.map((v: any) => v.id)
  } else {
    selectedViolationIds.value = []
  }
}

async function handleBatchResolveViolationsInModal(action: 'DELETE' | 'PENDING_HITL') {
  if (!selectedViolationIds.value.length) {
    ElMessage.warning('请先勾选需要处置的违规条目')
    return
  }
  try {
    const res: any = await adminApi.batchResolveViolations({
      target_type: inspectReportData.value?.interaction_type || 'danmaku',
      action,
      ids: selectedViolationIds.value
    })
    ElMessage.success(res?.message || '批量处置已生效')
    if (inspectReportData.value?.violations) {
      inspectReportData.value.violations = inspectReportData.value.violations.filter(
        (v: any) => !selectedViolationIds.value.includes(v.id)
      )
    }
    selectedViolationIds.value = []
    if (inspectReportData.value?.interaction_type === 'danmaku') {
      await fetchDanmakus(danmakuPage.value)
    } else {
      await fetchComments(commentPage.value)
    }
  } catch (err: any) {
    ElMessage.error(err.message || '批量处置失败')
  }
}

async function fetchWordProposals() {
  try {
    const res: any = await adminApi.getWordProposals('PENDING')
    const data = res?.data || {}
    proposalsList.value = data.items || []
    proposalsPendingCount.value = data.pending_count || 0
  } catch (e) {
    console.error('Failed to fetch word proposals:', e)
  }
}

function openWordProposalsDrawer() {
  fetchWordProposals()
  showProposalsDrawer.value = true
}

async function handleDecideProposal(proposalId: string, action: 'ACCEPT' | 'REJECT') {
  try {
    const res: any = await adminApi.decideWordProposal(proposalId, { action })
    ElMessage.success(res?.message || (action === 'ACCEPT' ? '已采纳并录入 DFA 敏感词库！' : '已驳回该违规词建议'))
    proposalsList.value = proposalsList.value.filter(p => p.id !== proposalId)
    proposalsPendingCount.value = Math.max(0, proposalsPendingCount.value - 1)
    if (action === 'ACCEPT') {
      await loadSensitiveWords(1)
      await fetchSensitiveCategoriesStat()
    }
  } catch (err: any) {
    ElMessage.error(err.message || '审批操作失败')
  }
}

async function handleBatchAcceptProposalsInModal() {
  const words = inspectReportData.value?.suggested_words || []
  if (!words.length) return
  let successCount = 0
  for (const w of words) {
    try {
      await adminApi.decideWordProposal(w.id, { action: 'ACCEPT' })
      successCount++
    } catch (e) {
      console.warn('Failed to accept proposal:', w.word, e)
    }
  }
  ElMessage.success(`成功采纳 ${successCount} 条建议新词并热重载 DFA 敏感词库！`)
  inspectReportData.value.suggested_words = []
  await loadSensitiveWords(1)
  await fetchWordProposals()
}

// =========================================================================
// Engine Config
// =========================================================================
function saveEngineConfig() {
  if (!engineForm.value.modelName.trim()) {
    ElMessage.warning('请输入有效的模型名称')
    return
  }
  localStorage.setItem('cinema_active_model', engineForm.value.modelName.trim())
  localStorage.setItem('cinema_temperature', engineForm.value.temperature.toString())
  ElMessage.success(`模型引擎已配置为 [${engineForm.value.modelName.trim()}]，伴读参数已同步！`)
}

function getRoleLabel(role: string): string {
  const map: Record<string, string> = {
    USER: '普通用户',
    CREATOR: '创作者',
    REVIEWER: '审核员',
    ADMIN: '超级管理员'
  }
  return map[role] || role
}

function formatNumber(num: number): string {
  if (!num) return '0'
  return num >= 10000 ? (num / 10000).toFixed(1) + 'w' : num.toLocaleString()
}

// =========================================================================
// RAG Knowledge Studio & Evaluation Dashboard (Feature Complete)
// =========================================================================
const ragSubTab = ref<'benchmark' | 'tools' | 'corpora' | 'chunker' | 'graph'>('benchmark')
const ragRadarChartRef = ref<HTMLDivElement | null>(null)
let ragRadarInstance: echarts.ECharts | null = null

const toolsConfig = ref<any>({
  enable_dense: true,
  enable_bm25: true,
  enable_neo4j: true,
  enable_rrf: true,
  enable_rerank: true,
  enable_crag: true,
  enable_self_rag: true,
  enable_plot_companion_agent: true,
  enable_director_jump_agent: true,
  step_timeout_sec: 2.0,
  total_timeout_sec: 8.0
})
const isSavingToolsConfig = ref(false)

const neo4jProbeState = ref<any>({
  probing: false,
  latency_ms: null,
  is_connected: null,
  message: ''
})

const llmProbeState = ref<any>({
  probing: false,
  latency_ms: null,
  is_connected: null,
  message: ''
})

const ragStats = ref<RAGOverviewStats>({
  total_corpora: 0,
  total_chunks: 0,
  total_evals: 0,
  latest_eval_score: 0.0,
  graph_status: {
    is_connected: false,
    backend: 'embedded_fallback',
    uri: 'bolt://localhost:7687',
    user: 'neo4j',
    total_nodes: 0,
    total_edges: 0,
    message: '正在检测 Neo4j 连通性...'
  },
  judge_config: {
    mode: 'local',
    local: { provider: 'ollama', model_name: 'deepseek-r1:1.5b', base_url: 'http://localhost:11434' },
    cloud: { provider: 'deepseek', model_name: 'deepseek-r1', base_url: 'https://api.deepseek.com', api_key: '' },
    temperature: 0.0,
    timeout_seconds: 30.0
  }
})

const corporaList = ref<RAGCorpusItem[]>([])
const chunksList = ref<RAGChunkItem[]>([])
const evalHistoryList = ref<RAGEvalRunItem[]>([])
const graphEdgesList = ref<any[]>([])
const graphSearchEntity = ref('')

const isSeedingAssets = ref(false)
const isBenchmarking = ref(false)
const showJudgeConfigDialog = ref(false)
const showCreateCorpusDialog = ref(false)

const judgeConfigForm = ref({
  mode: 'local',
  enable_stream: true,
  local: { provider: 'ollama', model_name: 'deepseek-r1:1.5b', base_url: 'http://localhost:11434' },
  cloud: { provider: 'deepseek', model_name: 'deepseek-r1', base_url: 'https://api.deepseek.com', api_key: '', masked_api_key: '' }
})

const newCorpusForm = ref({
  title: '',
  doc_type: 'script',
  strategy: 'parent_child',
  content: '',
  drama_id: 'drama-qianjin-001'
})

const chunkDebugForm = ref({
  strategy: 'sentence_window',
  chunk_size: 250,
  chunk_overlap: 40,
  episode_num: 1,
  text: `1\n00:00:15,000 --> 00:00:22,000\n医生：苏董事长，这份加急 DNA 报告证实，苏婉儿与您并无生物学亲子关系！\n\n2\n00:00:35,000 --> 00:00:43,000\n苏正国拍案震怒：什么？！当年在妇幼保健院，当真是有人故意调换了我的亲生骨肉？！\n\n3\n00:02:35,000 --> 00:02:46,000\n顾夜白亮出至尊黑金卡：苏倾城才是当年的救命恩人，动我未婚妻者死！`
})
const debugChunksResult = ref<any[]>([])

function switchRagSubTab(tab: 'benchmark' | 'tools' | 'corpora' | 'chunker' | 'graph') {
  ragSubTab.value = tab
  if (tab === 'benchmark') {
    nextTick(() => initRagRadarChart())
  } else if (tab === 'tools') {
    loadRagOverview()
  } else if (tab === 'corpora') {
    loadRagCorpora()
  } else if (tab === 'chunker') {
    loadRagChunks()
  } else if (tab === 'graph') {
    loadRagGraph()
  }
}

async function loadRagData() {
  try {
    await Promise.all([
      loadRagOverview(),
      loadRagCorpora(),
      loadRagChunks(),
      loadRagEvalHistory(),
      loadRagGraph()
    ])
    if (ragSubTab.value === 'benchmark') {
      nextTick(() => initRagRadarChart())
    }
  } catch (err: any) {
    console.warn('Load RAG data failed:', err)
  }
}

async function loadRagOverview() {
  try {
    const res = await ragApi.getOverviewStats()
    if (res?.data) {
      ragStats.value = res.data
      if (res.data.tools_config) {
        toolsConfig.value = { ...toolsConfig.value, ...res.data.tools_config }
      }
    }
  } catch (err) {
    console.warn('Load RAG stats error:', err)
  }
}

async function handleProbeNeo4j() {
  neo4jProbeState.value.probing = true
  try {
    const res = await ragApi.probeNeo4j(2.5)
    if (res?.data) {
      neo4jProbeState.value.latency_ms = res.data.latency_ms
      neo4jProbeState.value.is_connected = res.data.is_connected
      neo4jProbeState.value.message = res.data.message
      if (ragStats.value.graph_status) {
        ragStats.value.graph_status.is_connected = res.data.is_connected
        ragStats.value.graph_status.total_nodes = res.data.total_nodes
        ragStats.value.graph_status.total_edges = res.data.total_edges
        ragStats.value.graph_status.message = res.data.message
      }
      if (res.data.is_connected) {
        ElMessage.success(`Neo4j 探测正常！延迟: ${res.data.latency_ms} ms (${res.data.total_nodes} 实体)`)
      } else {
        ElMessage.warning(`Neo4j 连通超时或离线: ${res.data.message}`)
      }
    }
  } catch (err: any) {
    ElMessage.error(err.message || '探测 Neo4j 失败')
  } finally {
    neo4jProbeState.value.probing = false
  }
}

async function handleProbeLlm() {
  llmProbeState.value.probing = true
  try {
    const cfg = ragStats.value.judge_config
    const isCloud = cfg.mode === 'cloud'
    const payload = isCloud ? {
      provider: cfg.cloud?.provider || 'deepseek',
      model_name: cfg.cloud?.model_name || 'deepseek-r1',
      base_url: cfg.cloud?.base_url || 'https://api.deepseek.com',
      api_key: judgeConfigForm.value.cloud?.api_key || ''
    } : {
      provider: cfg.local?.provider || 'ollama',
      model_name: cfg.local?.model_name || 'deepseek-r1:1.5b',
      base_url: cfg.local?.base_url || 'http://localhost:11434'
    }
    const res = await ragApi.probeLlm(payload)
    if (res?.data) {
      llmProbeState.value.latency_ms = res.data.latency_ms
      llmProbeState.value.is_connected = res.data.is_connected
      llmProbeState.value.message = res.data.message
      if (res.data.is_connected) {
        ElMessage.success(`大模型连通正常！首字延迟: ${res.data.latency_ms} ms`)
      } else {
        ElMessage.warning(`大模型探测失败: ${res.data.message}`)
      }
    }
  } catch (err: any) {
    ElMessage.error(err.message || '探测大模型失败')
  } finally {
    llmProbeState.value.probing = false
  }
}

async function handleSaveToolsConfig() {
  isSavingToolsConfig.value = true
  try {
    const res = await ragApi.saveToolsConfig(toolsConfig.value)
    if (res?.data) {
      toolsConfig.value = res.data
      ElMessage.success('RAG 工具与智能体热插拔配置已持久化更新！')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '保存工具配置失败')
  } finally {
    isSavingToolsConfig.value = false
  }
}

async function handleImportAllPresetAssets() {
  isSeedingAssets.value = true
  try {
    const res = await ragApi.importAllPresetAssets(true)
    ElMessage.success('成功全量装载短剧标准知识库（制作规范/平台规则/人物图谱）！')
    await loadRagData()
  } catch (err: any) {
    ElMessage.error(err.message || '装载预置资产失败')
  } finally {
    isSeedingAssets.value = false
  }
}

async function loadRagCorpora() {
  try {
    const res = await ragApi.listCorpora()
    if (res?.data) {
      corporaList.value = res.data
    }
  } catch (err) {
    console.warn('Load corpora error:', err)
  }
}

async function loadRagChunks() {
  try {
    const res = await ragApi.listChunks({ limit: 60 })
    if (res?.data) {
      chunksList.value = res.data
    }
  } catch (err) {
    console.warn('Load chunks error:', err)
  }
}

async function loadRagEvalHistory() {
  try {
    const res = await ragApi.listEvalRuns(20)
    if (res?.data) {
      evalHistoryList.value = res.data
    }
  } catch (err) {
    console.warn('Load eval runs error:', err)
  }
}

async function loadRagGraph(entityName?: string) {
  try {
    const res = await ragApi.getGraphSubgraph(entityName)
    if (res?.data?.edges) {
      graphEdgesList.value = res.data.edges
    } else {
      graphEdgesList.value = []
    }
  } catch (err) {
    console.warn('Load graph subgraph error:', err)
  }
}

function initRagRadarChart() {
  if (!ragRadarChartRef.value) return
  if (!ragRadarInstance) {
    ragRadarInstance = echarts.init(ragRadarChartRef.value)
  }

  const isLight = document.documentElement.getAttribute('data-theme') === 'light'
  const textColor = isLight ? '#1d1d1f' : 'rgba(255, 255, 255, 0.88)'
  const splitLineColor = isLight ? '#d1d1d6' : 'rgba(255, 255, 255, 0.16)'
  const splitAreaColors = isLight 
    ? ['#ffffff', '#f5f5f7'] 
    : ['rgba(255, 255, 255, 0.02)', 'rgba(255, 255, 255, 0.05)']

  const latest = ragStats.value.latest_eval
  const dataValues = latest 
    ? [
        Math.min(1.0, latest.faithfulness || 0.84),
        Math.min(1.0, latest.answer_relevance || 0.75),
        Math.min(1.0, latest.context_precision || 0.78),
        Math.min(1.0, latest.context_recall || 0.72)
      ]
    : [0.85, 0.78, 0.82, 0.76]

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: isLight ? 'rgba(255, 255, 255, 0.98)' : 'rgba(28, 28, 30, 0.95)',
      borderColor: isLight ? '#d1d1d6' : 'rgba(255, 255, 255, 0.2)',
      textStyle: { color: isLight ? '#1d1d1f' : '#ffffff', fontSize: 12 }
    },
    radar: {
      indicator: [
        { name: '忠实度 (Faithfulness)', max: 1.0 },
        { name: '回答相关性 (Relevance)', max: 1.0 },
        { name: '上下文精准 (Precision)', max: 1.0 },
        { name: '上下文召回 (Recall)', max: 1.0 }
      ],
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: textColor,
        fontWeight: isLight ? 700 : 500,
        fontSize: 12
      },
      splitLine: {
        lineStyle: {
          color: splitLineColor,
          width: 1.2
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: splitAreaColors
        }
      },
      axisLine: {
        lineStyle: {
          color: splitLineColor
        }
      }
    },
    series: [
      {
        name: 'RAGAS 四维基准跑分',
        type: 'radar',
        data: [
          {
            value: dataValues,
            name: '当前模型评测指标',
            symbol: 'circle',
            symbolSize: 6,
            itemStyle: {
              color: '#0071E3'
            },
            lineStyle: {
              width: 2.8,
              color: '#0071E3'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(0, 113, 227, 0.45)' },
                { offset: 1, color: 'rgba(0, 113, 227, 0.08)' }
              ])
            }
          }
        ]
      }
    ]
  }

  ragRadarInstance.setOption(option)
}

async function handleInitSampleAssets() {
  isSeedingAssets.value = true
  try {
    await ragApi.initSampleAssets(true)
    ElMessage.success('成功灌入示范资产包与 Neo4j 知识图谱！')
    await loadRagData()
  } catch (err: any) {
    ElMessage.error(err.message || '示范资产初始化失败')
  } finally {
    isSeedingAssets.value = false
  }
}

function openJudgeConfigModal() {
  const cfg = ragStats.value.judge_config
  judgeConfigForm.value = {
    mode: cfg.mode || 'local',
    enable_stream: (cfg as any).enable_stream !== undefined ? (cfg as any).enable_stream : true,
    local: { ...cfg.local },
    cloud: { ...cfg.cloud, api_key: '', masked_api_key: cfg.cloud?.masked_api_key || '' }
  }
  showJudgeConfigDialog.value = true
}

async function handleSaveJudgeConfig() {
  try {
    await ragApi.saveJudgeConfig(judgeConfigForm.value)
    ElMessage.success('评测裁判模型配置已持久化保存！')
    showJudgeConfigDialog.value = false
    await loadRagOverview()
  } catch (err: any) {
    ElMessage.error(err.message || '保存裁判配置失败')
  }
}

async function handleTriggerBenchmark() {
  isBenchmarking.value = true
  try {
    const res = await ragApi.runBenchmark({ max_samples: 20 })
    ElMessage.success(`基准评测完成！综合 F1 得分: ${((res.data.f1_score || 0) * 100).toFixed(1)} 分`)
    await loadRagOverview()
    await loadRagEvalHistory()
    nextTick(() => initRagRadarChart())
  } catch (err: any) {
    ElMessage.error(err.message || '基准评测运行失败')
  } finally {
    isBenchmarking.value = false
  }
}

async function handleCreateCorpus() {
  try {
    await ragApi.createCorpus(newCorpusForm.value)
    ElMessage.success('知识库文档录入成功，已完成自动切片与向量索引！')
    showCreateCorpusDialog.value = false
    newCorpusForm.value = { title: '', doc_type: 'script', strategy: 'parent_child', content: '', drama_id: 'drama-qianjin-001' }
    await loadRagData()
  } catch (err: any) {
    ElMessage.error(err.message || '录入文档失败')
  }
}

async function handleDeleteCorpus(id: string) {
  try {
    await ElMessageBox.confirm('确定要删除该知识库文档及关联所有切片吗？', '提示', { type: 'warning' })
    await ragApi.deleteCorpus(id)
    ElMessage.success('删除成功')
    await loadRagData()
  } catch (e) {}
}

async function handleDebugChunking() {
  if (!chunkDebugForm.value.text.trim()) {
    ElMessage.warning('请输入要切片的测试文本')
    return
  }
  try {
    const res = await ragApi.debugChunkStrategy(chunkDebugForm.value)
    debugChunksResult.value = res?.data?.chunks || []
    ElMessage.success(`切片完成，共生成 ${debugChunksResult.value.length} 个测试切片！`)
  } catch (err: any) {
    ElMessage.error(err.message || '切片测试失败')
  }
}

async function handleSearchGraph() {
  if (!graphSearchEntity.value.trim()) {
    await handleResetGraph()
    return
  }
  await loadRagGraph(graphSearchEntity.value.trim())
}

async function handleResetGraph() {
  graphSearchEntity.value = ''
  await loadRagGraph()
}

async function handleReconnectNeo4j() {
  try {
    const res = await ragApi.reconnectNeo4j()
    if (res?.data?.is_connected) {
      ElMessage.success('成功连通本地 Neo4j 图数据库服务！')
    } else {
      ElMessage.warning('未能连接 Neo4j 实例，系统将继续维持嵌入式图存储降级兜底。')
    }
    await loadRagOverview()
  } catch (err: any) {
    ElMessage.error(err.message || '探测 Neo4j 异常')
  }
}

// =========================================================================
// TAB 11: 登录主页壁纸引擎管理状态与业务逻辑
// =========================================================================
const wallpaperConfig = reactive<WallpaperConfigData>({
  mode: 'gaoleng_qianjin',
  custom_url: '',
  dark_opacity: 0.45,
  light_opacity: 0.18,
  blur_px: 0
})
const isSavingWallpaper = ref(false)
const previewTheme = ref<'dark' | 'light'>('dark')

const previewWallpaperStyle = computed(() => {
  let bgUrl = '/wallpapers/gaoleng_qianjin.png'
  if (wallpaperConfig.mode === 'custom_url' && wallpaperConfig.custom_url) {
    bgUrl = wallpaperConfig.custom_url
  } else if (wallpaperConfig.mode === 'default_aurora') {
    return {
      background: 'linear-gradient(135deg, #0b1528 0%, #152238 50%, #0d1e38 100%)',
      filter: 'none'
    }
  }
  return {
    backgroundImage: `url(${bgUrl})`,
    filter: (wallpaperConfig.blur_px || 0) > 0 ? `blur(${wallpaperConfig.blur_px}px)` : 'none'
  }
})

const previewMaskStyle = computed(() => {
  const isL = previewTheme.value === 'light'
  const op = isL ? (wallpaperConfig.light_opacity ?? 0.18) : (wallpaperConfig.dark_opacity ?? 0.45)
  return {
    backgroundColor: isL ? `rgba(255, 255, 255, ${op})` : `rgba(0, 0, 0, ${op})`
  }
})

async function loadAdminWallpaperConfig() {
  try {
    const res: any = await getAdminWallpaperConfig()
    const d = res?.data?.data || res?.data
    if (d) {
      wallpaperConfig.mode = d.mode || 'gaoleng_qianjin'
      wallpaperConfig.custom_url = d.custom_url || ''
      wallpaperConfig.dark_opacity = d.dark_opacity ?? 0.45
      wallpaperConfig.light_opacity = d.light_opacity ?? 0.18
      wallpaperConfig.blur_px = d.blur_px ?? 0
    }
  } catch (err: any) {
    ElMessage.error(err.message || '获取登录页壁纸配置失败')
  }
}

async function handleSaveWallpaperConfig() {
  isSavingWallpaper.value = true
  try {
    const res: any = await updateAdminWallpaperConfig({
      mode: wallpaperConfig.mode,
      custom_url: wallpaperConfig.custom_url,
      dark_opacity: Number(wallpaperConfig.dark_opacity),
      light_opacity: Number(wallpaperConfig.light_opacity),
      blur_px: Number(wallpaperConfig.blur_px)
    })
    ElMessage.success('登录页面背景壁纸配置已成功更新并在全站生效')
  } catch (err: any) {
    ElMessage.error(err.message || '保存壁纸配置失败')
  } finally {
    isSavingWallpaper.value = false
  }
}

function handleResetWallpaperConfig() {
  wallpaperConfig.mode = 'gaoleng_qianjin'
  wallpaperConfig.custom_url = ''
  wallpaperConfig.dark_opacity = 0.45
  wallpaperConfig.light_opacity = 0.18
  wallpaperConfig.blur_px = 0
  ElMessage.info('已重置为《高冷千金的贴身高手》默认预设，请点击保存生效')
}

</script>

<style scoped>
/* ========================================================================== */
/* Apple HIG Translucent Layout & Responsive Collapsible Sidebar              */
/* ========================================================================== */
.admin-page-root {
  height: 100vh;
  background-color: var(--apple-bg, #0d0d11);
  color: var(--apple-text-primary, #F5F5F7);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.admin-layout-wrapper {
  display: flex;
  flex: 1;
  height: calc(100vh - 64px);
  position: relative;
  overflow: hidden;
}

/* Ambient Backdrops */
.admin-ambient-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.admin-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(140px);
  opacity: 0.12;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: #0071E3;
  top: 10%;
  left: 20%;
}

.orb-2 {
  width: 450px;
  height: 450px;
  background: #30D158;
  bottom: 10%;
  right: 15%;
}

/* ========================================================================== */
/* Dynamic Collapsible Sidebar                                                */
/* ========================================================================== */
.admin-sidebar {
  width: 250px;
  background: rgba(22, 22, 26, 0.85);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  z-index: 30;
  height: 100%;
  flex-shrink: 0;
}

.admin-sidebar.is-collapsed {
  width: 68px;
}

.sidebar-header {
  height: 64px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
  white-space: nowrap;
}

.brand-icon {
  font-size: 20px;
  color: var(--apple-blue, #0071E3);
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.brand-sub {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.45);
  letter-spacing: 0.08em;
}

.sidebar-brand-collapsed {
  width: 100%;
  display: flex;
  justify-content: center;
}

.sidebar-pin-btn {
  background: rgba(255, 255, 255, 0.06);
  border: none;
  color: rgba(255, 255, 255, 0.7);
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.sidebar-pin-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #FFFFFF;
}

.sidebar-nav-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-group-title {
  font-size: 10px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.35);
  letter-spacing: 0.08em;
  padding: 10px 10px 4px 10px;
  text-transform: uppercase;
}

.nav-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.06);
  margin: 8px 4px;
}

.nav-tab-item {
  width: 100%;
  height: 42px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 12px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
  position: relative;
  white-space: nowrap;
}

.nav-tab-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #FFFFFF;
}

.nav-tab-item.active {
  background: rgba(0, 113, 227, 0.2);
  color: #2997FF;
  font-weight: 600;
}

.nav-tab-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  background: #2997FF;
  border-radius: 0 4px 4px 0;
}

.nav-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.nav-label {
  flex: 1;
  text-align: left;
}

.nav-badge {
  background: #FF453A;
  color: #FFFFFF;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 10px;
}

/* ========================================================================== */
/* Main Stage                                                                 */
/* ========================================================================== */
.admin-main-stage {
  flex: 1;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px 32px 60px 32px;
  position: relative;
  z-index: 10;
  max-width: 1600px;
  -webkit-overflow-scrolling: touch;
}

.admin-main-stage.is-rag-view {
  padding: 0;
  max-width: 100%;
  overflow: hidden;
}

.content-section-rag {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.admin-main-stage::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.admin-main-stage::-webkit-scrollbar-track {
  background: transparent;
}
.admin-main-stage::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.16);
  border-radius: 999px;
}
.admin-main-stage::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.32);
}

.stage-top-bar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.bar-breadcrumb {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  font-weight: 500;
}

.bar-headline {
  margin: 4px 0 0 0;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.bar-right {
  display: flex;
  gap: 12px;
}

/* Buttons */
.apple-btn-primary {
  background: #0071E3;
  color: #FFFFFF;
  border: none;
  border-radius: 20px;
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.apple-btn-primary:hover {
  background: #0077ED;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.35);
}

.apple-btn-primary.big-btn {
  padding: 12px 24px;
  font-size: 14px;
}

.apple-btn-primary.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
  border-radius: 12px;
}

.apple-btn-secondary {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 20px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.apple-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.14);
}

.apple-btn-secondary.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
  border-radius: 12px;
}

/* Glass Card */
.glass-card {
  background: rgba(22, 22, 26, 0.85);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 18px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
  padding: 24px;
}

/* ========================================================================== */
/* KPI Metric Cards Grid                                                      */
/* ========================================================================== */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-card {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.kpi-title {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
}

.kpi-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 6px;
}

.kpi-badge.blue { background: rgba(0, 113, 227, 0.2); color: #2997FF; }
.kpi-badge.cyan { background: rgba(100, 210, 255, 0.2); color: #64D2FF; }
.kpi-badge.purple { background: rgba(191, 90, 242, 0.2); color: #BF5AF2; }
.kpi-badge.pink { background: rgba(255, 55, 95, 0.2); color: #FF375F; }
.kpi-badge.indigo { background: rgba(94, 92, 230, 0.2); color: #5E5CE6; }
.kpi-badge.green { background: rgba(48, 209, 88, 0.2); color: #30D158; }
.kpi-badge.amber { background: rgba(255, 159, 10, 0.2); color: #FF9F0A; }
.kpi-badge.red { background: rgba(255, 69, 58, 0.2); color: #FF453A; }

.kpi-number {
  font-size: 28px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.5px;
  margin-bottom: 4px;
}

.kpi-sub {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

/* ========================================================================== */
/* ECharts Block                                                              */
/* ========================================================================== */
.chart-block {
  margin-bottom: 24px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.chart-title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-icon {
  font-size: 26px;
  color: #0071E3;
}

.chart-heading {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.chart-subtext {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.chart-legend-pills {
  display: flex;
  gap: 12px;
}

.legend-pill {
  font-size: 11px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.7);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.history { background: #0071E3; }
.dot.forecast { background: #30D158; }
.dot.bound { background: rgba(48, 209, 88, 0.4); }

.echarts-container {
  width: 100%;
  height: 380px;
}

/* ========================================================================== */
/* Bass Diffusion Viral Ranking                                               */
/* ========================================================================== */
.viral-ranking-block {
  margin-bottom: 24px;
}

.block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.block-icon {
  font-size: 22px;
  color: #FF9F0A;
}

.rank-index {
  font-weight: 700;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.rank-index.rank-1 { color: #FFD60A; }
.rank-index.rank-2 { color: #E5E5EA; }
.rank-index.rank-3 { color: #FF9F0A; }

.score-progress-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-val {
  font-weight: 700;
  font-size: 12px;
  min-width: 32px;
}

.score-bar {
  width: 70px;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, #0071E3, #30D158);
  border-radius: 3px;
}

.growth-text {
  font-weight: 700;
  color: #30D158;
}

/* ========================================================================== */
/* Apple Styled Tables                                                        */
/* ========================================================================== */
.table-card {
  padding: 0;
  overflow: hidden;
}

.table-card-header {
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 6px 14px;
  width: 280px;
}

.table-search-input {
  background: transparent;
  border: none;
  outline: none;
  color: #FFFFFF;
  font-size: 12px;
  width: 100%;
}

.table-search-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.stat-counter {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-right: 12px;
}

.apple-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 13px;
}

.apple-table th {
  background: rgba(255, 255, 255, 0.03);
  padding: 12px 20px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.apple-table td {
  padding: 14px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  vertical-align: middle;
}

.apple-table tr:hover td {
  background: rgba(255, 255, 255, 0.02);
}

.drama-thumb-wrapper {
  width: 96px;
  height: 54px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
  background: #000;
}

.drama-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.multi-poster-tag {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.7);
  color: #FFF;
  font-size: 9px;
  font-weight: 600;
  padding: 1px 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 2px;
}

.drama-title-main {
  font-weight: 600;
  color: #FFFFFF;
  margin-bottom: 4px;
}

.drama-synopsis-sub {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-pill {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.08);
  padding: 3px 8px;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.8);
}

.status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
}

.status-badge.success { background: rgba(48, 209, 88, 0.2); color: #30D158; }
.status-badge.warning { background: rgba(255, 159, 10, 0.2); color: #FF9F0A; }
.status-badge.danger { background: rgba(255, 69, 58, 0.2); color: #FF453A; }

.actions-group {
  display: flex;
  gap: 8px;
}

.btn-text-action {
  background: transparent;
  border: none;
  color: #2997FF;
  font-size: 12px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 6px;
  transition: all 0.15s;
}

.btn-text-action:hover {
  background: rgba(41, 151, 255, 0.12);
}

.btn-text-action.btn-warn {
  color: #FF9F0A;
}

.btn-text-action.btn-warn:hover {
  background: rgba(255, 159, 10, 0.12);
}

.btn-text-action.btn-danger {
  color: #FF453A;
}

.btn-text-action.btn-danger:hover {
  background: rgba(255, 69, 58, 0.12);
}

.btn-text-action.btn-success {
  color: #30D158;
}

.btn-text-action.btn-success:hover {
  background: rgba(48, 209, 88, 0.12);
}

/* ========================================================================== */
/* Sync Section Styles                                                        */
/* ========================================================================== */
.sync-dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.card-header-styled {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.head-icon {
  font-size: 24px;
  color: #0071E3;
}

.sync-mode-selector {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 24px;
}

.mode-radio-box {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 16px 20px;
  display: flex;
  gap: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-radio-box:hover {
  background: rgba(255, 255, 255, 0.07);
}

.mode-radio-box.selected {
  border-color: #0071E3;
  background: rgba(0, 113, 227, 0.12);
}

.radio-content {
  flex: 1;
}

.radio-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.radio-name {
  font-weight: 700;
  font-size: 14px;
}

.recommend-pill {
  background: rgba(48, 209, 88, 0.2);
  color: #30D158;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
}

.radio-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
  line-height: 1.5;
}

.sync-report-card {
  margin-top: 24px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 14px;
  padding: 16px;
  border: 1px solid rgba(48, 209, 88, 0.3);
}

.report-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.report-status-badge {
  color: #30D158;
  font-size: 12px;
  font-weight: 700;
}

.report-mode-tag {
  color: rgba(255, 255, 255, 0.5);
  font-size: 11px;
}

.report-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  text-align: center;
}

.report-stat-item .num {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #FFFFFF;
}

.report-stat-item .label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}

.telemetry-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.telem-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.telem-label {
  color: rgba(255, 255, 255, 0.5);
}

.telem-val {
  color: #FFFFFF;
}

/* ========================================================================== */
/* Carousels Section                                                          */
/* ========================================================================== */
.carousel-preview-img {
  width: 140px;
  height: 78px;
  object-fit: cover;
  border-radius: 8px;
}

.sub-text-col {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

/* ========================================================================== */
/* Users & Applications                                                       */
/* ========================================================================== */
.role-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
}

.role-badge.admin { background: rgba(255, 69, 58, 0.2); color: #FF453A; }
.role-badge.reviewer { background: rgba(255, 159, 10, 0.2); color: #FF9F0A; }
.role-badge.creator { background: rgba(48, 209, 88, 0.2); color: #30D158; }
.role-badge.user { background: rgba(255, 255, 255, 0.1); color: #FFFFFF; }

.privilege-tags {
  display: flex;
  gap: 4px;
}

.priv-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
}

.priv-tag.creator { background: rgba(48, 209, 88, 0.15); color: #30D158; }
.priv-tag.reviewer { background: rgba(255, 159, 10, 0.15); color: #FF9F0A; }
.priv-tag.guest { color: rgba(255, 255, 255, 0.3); }

.dual-subtabs-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.subtab-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  padding: 8px 18px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.subtab-btn.active {
  background: #0071E3;
  color: #FFFFFF;
  border-color: #0071E3;
}

.empty-table-cell {
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  padding: 32px 0 !important;
}

/* ========================================================================== */
/* Engine Config & Form Elements                                              */
/* ========================================================================== */
.engine-config-grid {
  max-width: 680px;
}

.form-group {
  margin-bottom: 18px;
}

.form-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 8px;
}

.apple-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  padding: 10px 14px;
  color: #FFFFFF;
  font-size: 13px;
  outline: none;
}

.apple-input:focus {
  border-color: #0071E3;
}

.apple-textarea {
  width: 100%;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  padding: 10px 14px;
  color: #FFFFFF;
  font-size: 13px;
  outline: none;
  resize: vertical;
}

/* ========================================================================== */
/* Drama Cover & Multi-Poster Governance (Feature 23)                        */
/* ========================================================================== */
.cover-preview-box {
  margin-top: 14px;
  width: 100%;
  min-height: 200px;
  border-radius: 14px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.04);
  border: 1px dashed rgba(255, 255, 255, 0.2);
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.02);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  transition: all 0.25s ease;
}

.cover-preview-box:hover,
.cover-preview-box.is-dragover {
  border-color: #0071E3;
  background: rgba(0, 113, 227, 0.08);
  box-shadow: 0 0 24px rgba(0, 113, 227, 0.2);
}

.preview-img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  display: block;
}

.dashed-micro-glow-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 30px 20px;
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
}

.placeholder-icon {
  color: #0071E3;
}

.placeholder-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.placeholder-text .main-tip {
  font-size: 14px;
  font-weight: 600;
  color: #FFFFFF;
}

.placeholder-text .sub-tip {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}

.cover-hover-prompt {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #FFFFFF;
  font-size: 13px;
  font-weight: 600;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.cover-preview-box:hover .cover-hover-prompt {
  opacity: 1;
}

.cover-url-manual-row {
  display: flex;
  gap: 10px;
  margin-top: 10px;
  align-items: center;
}

.shelf-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.posters-shelf-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 10px;
}

.poster-shelf-card {
  position: relative;
  aspect-ratio: 16 / 9;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.3);
}

.poster-shelf-card.is-main {
  border-color: #0071E3;
  box-shadow: 0 0 12px rgba(0, 113, 227, 0.4);
}

.shelf-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.shelf-card-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.8) 100%);
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 8px;
}

.shelf-main-badge {
  font-size: 10px;
  font-weight: 700;
  background: #0071E3;
  color: #FFFFFF;
  padding: 2px 6px;
  border-radius: 4px;
}

.shelf-btn-set-main {
  font-size: 10px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.2);
  color: #FFFFFF;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.shelf-btn-set-main:hover {
  background: #0071E3;
  border-color: #0071E3;
}

.shelf-btn-del {
  background: rgba(255, 69, 58, 0.3);
  color: #FF453A;
  border: none;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.shelf-btn-del:hover {
  background: #FF453A;
  color: #FFFFFF;
}

.shelf-empty-hint {
  grid-column: 1 / -1;
  text-align: center;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  padding: 20px 0;
}

.form-row-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.full-width {
  grid-column: 1 / -1;
}

/* ========================================================================== */
/* Carousel 16:9 WYSIWYG Live Preview (Feature 24)                            */
/* ========================================================================== */
.carousel-workbench-card {
  margin-bottom: 24px;
}

.workbench-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.workbench-title-box {
  display: flex;
  align-items: center;
  gap: 12px;
}

.workbench-quick-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.dropdown-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
}

.workbench-select {
  min-width: 260px;
}

.carousel-live-preview-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 24px;
  align-items: start;
}

.carousel-preview-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.carousel-preview-container {
  width: 100%;
  border-radius: 14px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
}

.aspect-16-9-box {
  width: 100%;
  aspect-ratio: 16 / 9;
  position: relative;
  overflow: hidden;
  background: #111116;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-bg-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.preview-empty-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
}

.preview-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.1) 0%, rgba(0, 0, 0, 0.85) 100%);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 20px;
}

.preview-tag-badge {
  align-self: flex-start;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 12px;
  background: #0071E3;
  color: #FFFFFF;
  margin-bottom: 8px;
}

.preview-title {
  font-size: 20px;
  font-weight: 700;
  color: #FFFFFF;
  margin: 0 0 4px 0;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}

.preview-subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
}

.preview-ratio-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  background: rgba(0, 0, 0, 0.25);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.preview-badge-status {
  color: #30D158;
  font-weight: 600;
}

.workbench-quick-info {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #FFFFFF;
}

.info-list {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.65);
  display: flex;
  flex-direction: column;
  gap: 8px;
  line-height: 1.6;
}

.carousel-dialog-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 24px;
}

.dialog-preview-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* ========================================================================== */
/* Users Management Full CRUD Toolbar & Cells (Feature 22)                    */
/* ========================================================================== */
.user-toolbar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.user-filters-group {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.economy-summary-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.coin-tag {
  font-size: 12px;
  font-weight: 600;
  color: #FFD60A;
}

.vip-tag-active {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 159, 10, 0.2);
  color: #FF9F0A;
  border: 1px solid rgba(255, 159, 10, 0.4);
}

.vip-tag-none {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.35);
}

.posters-carousel-wrap {
  border-radius: 12px;
  overflow: hidden;
}

.carousel-item-img {
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  position: relative;
}

.img-idx-pill {
  position: absolute;
  bottom: 16px;
  right: 16px;
  background: rgba(0, 0, 0, 0.75);
  color: #FFFFFF;
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 20px;
}

.role-select-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.role-radio-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
}

/* Responsive */
@media (max-width: 1080px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .sync-dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .admin-sidebar {
    position: fixed;
    height: 100%;
  }
  .admin-main-stage {
    padding: 16px;
  }
  .kpi-grid {
    grid-template-columns: 1fr;
  }
}

/* Lexicon & Sandbox Styles */
.lexicon-composite-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
}

@media (max-width: 1200px) {
  .lexicon-composite-grid {
    grid-template-columns: 1fr;
  }
}

.lexicon-filters-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.lexicon-filters-row .search-input {
  flex: 1;
}

.apple-select {
  padding: 8px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--text-primary, #FFFFFF);
  font-size: 13px;
  outline: none;
}

.dfa-sandbox-card {
  height: fit-content;
}

.sandbox-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sandbox-result-box {
  margin-top: 14px;
  padding: 16px;
  border-radius: 14px;
  background: rgba(52, 199, 89, 0.08);
  border: 1px solid rgba(52, 199, 89, 0.3);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sandbox-result-box.is-violation {
  background: rgba(255, 59, 48, 0.08);
  border: 1px solid rgba(255, 59, 48, 0.35);
}

.result-status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.risk-tag-text {
  font-size: 12px;
  font-weight: 600;
  color: #FF453A;
}

.result-detail-line {
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-label {
  color: #8E8E93;
}

.sanitized-code {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  background: rgba(0, 0, 0, 0.4);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 13px;
}

.risk-pill-mini {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 12px;
  background: rgba(255, 59, 48, 0.15);
  color: #FF453A;
  border: 1px solid rgba(255, 59, 48, 0.3);
  font-weight: 600;
}

.violation-reason-cell {
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.raw-snippet {
  color: #FF9F0A;
  font-size: 13px;
}

.matched-words-wrap {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* Announcement Governance Enhancements */
.announcement-tag-badge {
  background: rgba(245, 158, 11, 0.12) !important;
  color: #f59e0b !important;
  border: 1px solid rgba(245, 158, 11, 0.28) !important;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 9999px;
  font-size: 11px;
}

.announcement-content-col {
  max-width: 320px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.announcement-modal-backdrop {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  z-index: 3500 !important;
  background: rgba(0, 0, 0, 0.65) !important;
  backdrop-filter: blur(20px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 20px !important;
}

.apple-btn-danger {
  background: rgba(239, 68, 68, 0.15) !important;
  border: 1px solid rgba(239, 68, 68, 0.35) !important;
  color: #ef4444 !important;
  border-radius: 980px !important;
  padding: 8px 16px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
  cursor: pointer !important;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

.apple-btn-danger:hover {
  background: rgba(239, 68, 68, 0.25) !important;
  border-color: rgba(239, 68, 68, 0.5) !important;
  color: #f87171 !important;
  transform: scale(1.02) !important;
}

.row-selected {
  background: rgba(0, 113, 227, 0.08) !important;
}

/* ========================================================================== */
/* Apple HIG Announcement Broadcast Modal - Solid Physical Glass Card          */
/* ========================================================================== */
.announcement-modal-backdrop {
  position: fixed !important;
  inset: 0 !important;
  z-index: 3500 !important;
  background: rgba(0, 0, 0, 0.68) !important;
  backdrop-filter: blur(24px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 24px !important;
}

.announcement-dialog {
  position: relative !important;
  max-width: 580px !important;
  width: 92% !important;
  background: rgba(24, 25, 30, 0.96) !important;
  backdrop-filter: blur(32px) saturate(190%) !important;
  -webkit-backdrop-filter: blur(32px) saturate(190%) !important;
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
  border-radius: 20px !important;
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.75), 0 0 1px rgba(255, 255, 255, 0.2) inset !important;
  color: #f5f5f7 !important;
  overflow: hidden !important;
  display: flex !important;
  flex-direction: column !important;
  animation: modalCardPop 0.24s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

@keyframes modalCardPop {
  0% { transform: scale(0.94) translateY(12px); opacity: 0; }
  100% { transform: scale(1) translateY(0); opacity: 1; }
}

.announcement-dialog .modal-header {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: space-between !important;
  padding: 18px 24px 16px 24px !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
  background: rgba(255, 255, 255, 0.02) !important;
  box-sizing: border-box !important;
  width: 100% !important;
}

.announcement-dialog .modal-title-wrap {
  display: flex !important;
  align-items: center !important;
  gap: 12px !important;
}

.announcement-dialog .modal-icon-brand {
  color: #0071e3 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.announcement-dialog .modal-title {
  margin: 0 !important;
  font-size: 16px !important;
  font-weight: 700 !important;
  color: #ffffff !important;
  letter-spacing: -0.2px !important;
}

.announcement-dialog .modal-close-btn {
  width: 30px !important;
  height: 30px !important;
  min-width: 30px !important;
  border-radius: 50% !important;
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
  color: rgba(255, 255, 255, 0.8) !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 13px !important;
  cursor: pointer !important;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
  padding: 0 !important;
  line-height: 1 !important;
}

.announcement-dialog .modal-close-btn:hover {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(255, 255, 255, 0.3) !important;
  color: #ffffff !important;
  transform: scale(1.08) !important;
}

.announcement-dialog .modal-body {
  padding: 20px 24px !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 16px !important;
  box-sizing: border-box !important;
}

.announcement-dialog .form-group {
  display: flex !important;
  flex-direction: column !important;
  gap: 8px !important;
  margin: 0 !important;
}

.announcement-dialog .form-label {
  font-size: 13px !important;
  font-weight: 600 !important;
  color: rgba(255, 255, 255, 0.88) !important;
  display: flex !important;
  align-items: center !important;
  gap: 4px !important;
}

.announcement-dialog .form-label .required {
  color: #ef4444 !important;
}

.announcement-dialog .apple-input,
.announcement-dialog .apple-textarea {
  width: 100% !important;
  box-sizing: border-box !important;
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
  border-radius: 12px !important;
  padding: 12px 14px !important;
  color: #f5f5f7 !important;
  font-size: 14px !important;
  outline: none !important;
  transition: all 0.2s ease !important;
}

.announcement-dialog .apple-input:focus,
.announcement-dialog .apple-textarea:focus {
  border-color: #0071e3 !important;
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.25) !important;
  background: rgba(255, 255, 255, 0.08) !important;
}

.announcement-dialog .apple-textarea {
  resize: vertical !important;
  min-height: 90px !important;
  font-family: inherit !important;
  line-height: 1.5 !important;
}

.announcement-dialog .tag-quick-select {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 8px !important;
}

.announcement-dialog .tag-option-pill {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  color: rgba(255, 255, 255, 0.78) !important;
  padding: 6px 14px !important;
  border-radius: 9999px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
}

.announcement-dialog .tag-option-pill:hover {
  background: rgba(255, 255, 255, 0.12) !important;
  color: #ffffff !important;
}

.announcement-dialog .tag-option-pill.active {
  background: rgba(0, 113, 227, 0.22) !important;
  border-color: #0071e3 !important;
  color: #5ac8fa !important;
  font-weight: 600 !important;
  box-shadow: 0 0 10px rgba(0, 113, 227, 0.3) !important;
}

.announcement-dialog .switch-group {
  flex-direction: row !important;
  align-items: center !important;
  justify-content: space-between !important;
  padding: 12px 16px !important;
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 12px !important;
}

.announcement-dialog .switch-label {
  font-size: 13px !important;
  color: rgba(255, 255, 255, 0.85) !important;
}

.announcement-dialog .modal-footer {
  padding: 16px 24px 20px 24px !important;
  border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 12px !important;
  background: rgba(255, 255, 255, 0.02) !important;
  box-sizing: border-box !important;
}

.announcement-dialog .apple-btn-secondary {
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
  color: rgba(255, 255, 255, 0.85) !important;
  padding: 8px 18px !important;
  border-radius: 9999px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
}

.announcement-dialog .apple-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15) !important;
  color: #ffffff !important;
}

.announcement-dialog .apple-btn-primary {
  background: #0071e3 !important;
  border: 1px solid #0077ed !important;
  color: #ffffff !important;
  padding: 8px 20px !important;
  border-radius: 9999px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
  box-shadow: 0 4px 14px rgba(0, 113, 227, 0.35) !important;
}

.announcement-dialog .apple-btn-primary:hover:not(:disabled) {
  background: #0077ed !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 18px rgba(0, 113, 227, 0.45) !important;
}

.announcement-dialog .apple-btn-primary:disabled {
  opacity: 0.4 !important;
  cursor: not-allowed !important;
}

/* ========================================================================== */
/* Apple HIG Announcement Broadcast Modal - Light Theme Adaptation            */
/* ========================================================================== */
[data-theme="light"] .announcement-dialog {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.12) !important;
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.18), 0 0 1px rgba(0, 0, 0, 0.08) inset !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .announcement-dialog .modal-header {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
  background: rgba(0, 0, 0, 0.015) !important;
}

[data-theme="light"] .announcement-dialog .modal-title {
  color: #1d1d1f !important;
}

[data-theme="light"] .announcement-dialog .modal-close-btn {
  background: #f2f2f7 !important;
  border-color: rgba(0, 0, 0, 0.1) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .announcement-dialog .modal-close-btn:hover {
  background: #e5e5ea !important;
  color: #000000 !important;
}

[data-theme="light"] .announcement-dialog .form-label {
  color: #1d1d1f !important;
}

[data-theme="light"] .announcement-dialog .apple-input,
[data-theme="light"] .announcement-dialog .apple-textarea {
  background: #f5f5f7 !important;
  border-color: #d2d2d7 !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .announcement-dialog .apple-input:focus,
[data-theme="light"] .announcement-dialog .apple-textarea:focus {
  background: #ffffff !important;
  border-color: #0071e3 !important;
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.2) !important;
}

[data-theme="light"] .announcement-dialog .tag-option-pill {
  background: #f2f2f7 !important;
  border-color: #d2d2d7 !important;
  color: #3c3c43 !important;
}

[data-theme="light"] .announcement-dialog .tag-option-pill:hover {
  background: #e5e5ea !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .announcement-dialog .tag-option-pill.active {
  background: #e8f2ff !important;
  border-color: #0071e3 !important;
  color: #0071e3 !important;
}

[data-theme="light"] .announcement-dialog .switch-group {
  background: #f9f9fb !important;
  border-color: rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .announcement-dialog .switch-label {
  color: #1d1d1f !important;
}

[data-theme="light"] .announcement-dialog .modal-footer {
  border-top: 1px solid rgba(0, 0, 0, 0.08) !important;
  background: rgba(0, 0, 0, 0.015) !important;
}

[data-theme="light"] .announcement-dialog .apple-btn-secondary {
  background: #f2f2f7 !important;
  border-color: #d2d2d7 !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .announcement-dialog .apple-btn-secondary:hover {
  background: #e5e5ea !important;
}


.tag-quick-select {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.tag-option-pill {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.75);
  padding: 5px 12px;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tag-option-pill:hover,
.tag-option-pill.active {
  background: rgba(0, 113, 227, 0.2);
  border-color: #0071e3;
  color: #2997ff;
}


/* 4号违规词风控智能体专属工作台样式 (Apple HIG 语义化深浅自适应) */
.agent4-subtab-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.agent4-workspace-card {
  padding: 20px 24px;
  border-radius: 16px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

:global([data-theme="dark"]) .agent4-workspace-card {
  background: rgba(22, 22, 26, 0.88);
  border-color: rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
}

.agent4-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.agent-pod-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.8px;
  color: #0071e3;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 113, 227, 0.1);
  display: inline-block;
  margin-bottom: 6px;
}

.agent4-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary, #1d1d1f);
  margin: 0 0 6px 0;
}

:global([data-theme="dark"]) .agent4-title {
  color: #f5f5f7;
}

.agent4-desc {
  font-size: 13px;
  color: var(--text-secondary, #6e6e73);
  margin: 0;
  line-height: 1.5;
}

:global([data-theme="dark"]) .agent4-desc {
  color: #9499a0;
}

.agent4-quick-audit-box {
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--agent-input-bg, #f5f5f7);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.06));
}

:global([data-theme="dark"]) .agent4-quick-audit-box {
  background: rgba(30, 30, 36, 0.7);
  border-color: rgba(255, 255, 255, 0.08);
}

.audit-input-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.audit-result-display {
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--agent-card-surface, #ffffff);
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

:global([data-theme="dark"]) .audit-result-display {
  background: rgba(20, 20, 24, 0.9);
  border-color: rgba(255, 255, 255, 0.1);
}

.result-reason-text {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary, #1d1d1f);
  white-space: pre-wrap;
}

:global([data-theme="dark"]) .result-reason-text {
  color: #e2e8f0;
}


/* 人机回环表格滚动视口与自适应分页栏样式 */
.hitl-table-scroll-container {
  max-height: 440px;
  overflow-y: auto;
  overflow-x: auto;
  border-radius: 10px;
  border: 1px solid var(--agent-card-border, rgba(0, 0, 0, 0.08));
}

.hitl-table-scroll-container::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.hitl-table-scroll-container::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 999px;
}

:global([data-theme="dark"]) .hitl-table-scroll-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
}

.hitl-pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
  padding: 4px 2px;
}

/* ========================================================================= */
/* 互动合规风控 (弹幕/评论机审) Apple HIG 视觉呼吸感与滑动窗口规范样式       */
/* ========================================================================= */
.content-moderation-card {
  padding: 24px !important;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  margin-bottom: 20px;
}

.moderation-main-section {
  padding: 0 4px;
}

.header-action-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 多维分类统计胶囊栏 */
.category-pills-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.category-pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--apple-text-sub, rgba(255, 255, 255, 0.65));
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.category-pill-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--apple-text-main, #ffffff);
  border-color: rgba(255, 255, 255, 0.2);
}

.category-pill-btn.active {
  background: rgba(0, 113, 227, 0.18);
  border-color: #0071e3;
  color: #2997ff;
  box-shadow: 0 0 12px rgba(0, 113, 227, 0.25);
}

.pill-count-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  color: inherit;
}

.category-pill-btn.active .pill-count-badge {
  background: rgba(41, 151, 255, 0.25);
  color: #ffffff;
}

/* 滑动窗口表格滚动区 */
.apple-table-scroll-window {
  max-height: 480px;
  overflow-y: auto;
  overflow-x: auto;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.015);
  border: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 16px;
}

.apple-table-scroll-window::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.apple-table-scroll-window::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.18);
  border-radius: 3px;
}

.apple-table-scroll-window::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
}

/* 统一分页栏 */
.moderation-pagination-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.pagination-summary {
  font-size: 12px;
  color: var(--apple-text-sub, rgba(255, 255, 255, 0.5));
}

/* 4号智能体巡检雷达动态光效 */
.btn-radar {
  position: relative;
  overflow: hidden;
  box-shadow: 0 0 14px rgba(0, 113, 227, 0.3);
}

.btn-radar:not(:disabled):hover {
  box-shadow: 0 0 20px rgba(0, 113, 227, 0.55);
}

/* 自迭代建议词角标 */
.proposal-trigger-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.proposal-count-pill {
  padding: 1px 7px;
  border-radius: 10px;
  background: #ff3b30;
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.3;
}

/* 抽屉样式与卡片 */
.proposals-drawer-body {
  padding: 16px;
  color: var(--apple-text-main, #ffffff);
}

.drawer-top-bar {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(14, 165, 233, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.drawer-tip {
  font-size: 13px;
  line-height: 1.6;
  color: #7dd3fc;
  font-weight: 500;
  margin: 0;
}

[data-theme="light"] .drawer-top-bar {
  background: #f0f9ff !important;
  border: 1px solid #bae6fd !important;
}

[data-theme="light"] .drawer-tip {
  color: #0369a1 !important;
  font-weight: 600 !important;
}

[data-theme="light"] .proposal-card-item {
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03) !important;
}

[data-theme="light"] .prop-word {
  color: #dc2626 !important;
}

[data-theme="light"] .reason-val {
  color: #1e293b !important;
}

[data-theme="light"] .source-val {
  color: #334155 !important;
}

[data-theme="light"] .muted-label {
  color: #64748b !important;
}

.proposals-list-scroll {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: calc(100vh - 160px);
  overflow-y: auto;
}

.proposal-card-item {
  padding: 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.prop-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.prop-word {
  font-size: 16px;
  color: #ff3b30;
}

.prop-badges {
  display: flex;
  gap: 6px;
}

.prop-reason, .prop-source {
  font-size: 13px;
  display: flex;
  gap: 6px;
}

.muted-label {
  color: var(--apple-text-sub, rgba(255, 255, 255, 0.45));
  white-space: nowrap;
}

.source-val {
  color: rgba(255, 255, 255, 0.7);
  word-break: break-all;
}

/* 巡检研判报告模态弹窗 */
.inspect-report-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.inspect-report-modal {
  width: 920px;
  max-width: 95vw;
  max-height: 88vh;
  border-radius: 20px;
  background: rgba(24, 24, 28, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.report-modal-header {
  padding: 24px 28px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.report-badge {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #2997ff;
  display: block;
  margin-bottom: 4px;
}

.report-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  color: #ffffff;
}

.report-meta {
  font-size: 13px;
  color: var(--apple-text-sub, rgba(255, 255, 255, 0.6));
  margin: 6px 0 0 0;
}

.report-modal-body {
  padding: 24px 28px;
  overflow-y: auto;
  flex: 1;
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.violations-table-wrap {
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  max-height: 280px;
  overflow-y: auto;
}

.suggested-words-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.suggested-word-chip {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.chip-meta {
  display: flex;
  gap: 6px;
  margin: 6px 0;
}

.chip-reason {
  font-size: 12px;
  color: var(--apple-text-sub, rgba(255, 255, 255, 0.55));
  margin: 0;
}

.report-modal-footer {
  padding: 16px 28px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  justify-content: flex-end;
}

.empty-ok-state, .empty-drawer-state {
  text-align: center;
  padding: 32px;
  color: var(--apple-text-sub, rgba(255, 255, 255, 0.5));
  font-size: 13px;
}

</style>

<!-- Global Non-Scoped Overrides for Teleported Element Plus Dialogs & Form Elements -->
<style>

/* Global Dual-Theme Overrides for Element Plus Drawer */
html.dark .el-drawer,
[data-theme="dark"] .el-drawer,
.proposals-drawer-glass {
  background-color: rgba(22, 24, 29, 0.98) !important;
  color: #f0f6fc !important;
  border-left: 1px solid rgba(255, 255, 255, 0.12) !important;
  box-shadow: -16px 0 48px rgba(0, 0, 0, 0.65) !important;
}
html.dark .el-drawer__header,
[data-theme="dark"] .el-drawer__header,
.proposals-drawer-glass .el-drawer__header {
  color: #ffffff !important;
  font-weight: 700 !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
  margin-bottom: 0 !important;
  padding: 20px 24px !important;
}
html.dark .el-drawer__close-btn,
[data-theme="dark"] .el-drawer__close-btn,
.proposals-drawer-glass .el-drawer__close-btn {
  color: rgba(255, 255, 255, 0.65) !important;
}
html.dark .el-drawer__close-btn:hover,
[data-theme="dark"] .el-drawer__close-btn:hover,
.proposals-drawer-glass .el-drawer__close-btn:hover {
  color: #ffffff !important;
}

html:not(.dark) .el-drawer,
[data-theme="light"] .el-drawer {
  background-color: #ffffff !important;
  color: #1d1d1f !important;
  border-left: 1px solid rgba(0, 0, 0, 0.1) !important;
  box-shadow: -16px 0 48px rgba(0, 0, 0, 0.12) !important;
}
html:not(.dark) .el-drawer__header,
[data-theme="light"] .el-drawer__header {
  color: #1d1d1f !important;
  font-weight: 700 !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
  margin-bottom: 0 !important;
  padding: 20px 24px !important;
}
html:not(.dark) .el-drawer__close-btn,
[data-theme="light"] .el-drawer__close-btn {
  color: #64748b !important;
}
html:not(.dark) .el-drawer__close-btn:hover,
[data-theme="light"] .el-drawer__close-btn:hover {
  color: #0f172a !important;
}

.el-dialog,
.el-dialog.is-align-center {
  background: rgba(22, 24, 29, 0.95) !important;
  backdrop-filter: blur(28px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
  border-radius: 20px !important;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.08) inset !important;
  color: #f5f5f7 !important;
  overflow: hidden !important;
}

.el-dialog__header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
  padding: 18px 24px !important;
  margin-right: 0 !important;
  background: rgba(255, 255, 255, 0.02) !important;
}

.el-dialog__title {
  color: #ffffff !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  letter-spacing: -0.01em !important;
}

.el-dialog__close {
  color: rgba(255, 255, 255, 0.6) !important;
  font-size: 18px !important;
  transition: all 0.2s ease !important;
}

.el-dialog__close:hover {
  color: #ffffff !important;
  transform: scale(1.1) !important;
}

.el-dialog__body {
  padding: 24px !important;
  color: #e5e5ea !important;
  background: transparent !important;
}

.el-dialog__footer {
  border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
  padding: 16px 24px !important;
  background: rgba(255, 255, 255, 0.02) !important;
}

/* Deep Form Input & Label Visibility Overrides */
.el-dialog .form-label,
.dialog-form .form-label {
  display: block !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  color: rgba(255, 255, 255, 0.85) !important;
  margin-bottom: 8px !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5) !important;
}

.el-dialog .apple-input,
.dialog-form .apple-input,
.el-dialog .apple-select,
.dialog-form .apple-select,
.el-dialog .apple-textarea,
.dialog-form .apple-textarea {
  width: 100% !important;
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.18) !important;
  border-radius: 10px !important;
  padding: 10px 14px !important;
  color: #ffffff !important;
  font-size: 13px !important;
  outline: none !important;
  box-sizing: border-box !important;
  transition: all 0.2s ease !important;
}

.el-dialog .apple-input:focus,
.dialog-form .apple-input:focus,
.el-dialog .apple-select:focus,
.dialog-form .apple-select:focus,
.el-dialog .apple-textarea:focus,
.dialog-form .apple-textarea:focus {
  border-color: #0071e3 !important;
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.35) !important;
  background: rgba(255, 255, 255, 0.12) !important;
}

.el-dialog .apple-input::placeholder,
.dialog-form .apple-input::placeholder,
.el-dialog .apple-textarea::placeholder,
.dialog-form .apple-textarea::placeholder {
  color: rgba(255, 255, 255, 0.38) !important;
}

.el-dialog .apple-input:disabled,
.dialog-form .apple-input:disabled {
  background: rgba(255, 255, 255, 0.04) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  color: rgba(255, 255, 255, 0.45) !important;
  cursor: not-allowed !important;
}

.el-dialog option {
  background: #1c1c1e !important;
  color: #ffffff !important;
}

/* Pagination Dark Apple HIG styling */
.el-pagination.is-background .el-pager li:not(.is-disabled).is-active {
  background-color: #0071e3 !important;
  color: #ffffff !important;
}
.el-pagination.is-background .el-pager li,
.el-pagination.is-background .btn-prev,
.el-pagination.is-background .btn-next {
  background-color: rgba(255, 255, 255, 0.06) !important;
  color: rgba(255, 255, 255, 0.75) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 8px !important;
}
.el-pagination.is-background .el-pager li:hover,
.el-pagination.is-background .btn-prev:hover,
.el-pagination.is-background .btn-next:hover {
  color: #ffffff !important;
  border-color: rgba(0, 113, 227, 0.5) !important;
}

/* ========================================================================== */
/* Admin View - Comprehensive Light Theme Overrides (Apple HIG Unified)       */
/* ========================================================================== */
[data-theme="light"] .admin-page-root {
  background: #f5f6f8 !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .admin-ambient-bg {
  opacity: 0.1 !important;
}

[data-theme="light"] .admin-sidebar {
  background: #ffffff !important;
  border-right: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 2px 0 16px rgba(0, 0, 0, 0.03) !important;
}

[data-theme="light"] .brand-name {
  color: #1d1d1f !important;
}

[data-theme="light"] .brand-sub {
  color: #86868b !important;
}

[data-theme="light"] .sidebar-pin-btn {
  background: rgba(0, 0, 0, 0.04) !important;
  color: #6e6e73 !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .sidebar-pin-btn:hover {
  background: rgba(0, 0, 0, 0.08) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .nav-group-title {
  color: #86868b !important;
}

[data-theme="light"] .nav-tab-item {
  color: #6e6e73 !important;
}

[data-theme="light"] .nav-tab-item:hover {
  background: rgba(0, 0, 0, 0.04) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .nav-tab-item.active {
  background: rgba(0, 113, 227, 0.08) !important;
  color: #0071e3 !important;
  border-left-color: #0071e3 !important;
}

[data-theme="light"] .admin-main-viewport {
  background: #f5f6f8 !important;
}

[data-theme="light"] .admin-tab-header .tab-title {
  color: #1d1d1f !important;
}

[data-theme="light"] .admin-tab-header .tab-desc {
  color: #86868b !important;
}

[data-theme="light"] .table-card.glass-card,
[data-theme="light"] .glass-card {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] #section-agent-hub {
  background: transparent !important;
  color: #18191C !important;
}

[data-theme="light"] #section-agent-hub .acc-header-bar,
[data-theme="light"] #section-agent-hub .tactical-toolbar,
[data-theme="light"] #section-agent-hub .acc-kpi-card,
[data-theme="light"] #section-agent-hub .acc-chart-box,
[data-theme="light"] #section-agent-hub .acc-card-block,
[data-theme="light"] #section-agent-hub .category-config-card,
[data-theme="light"] #section-agent-hub .agent-config-card,
[data-theme="light"] #section-agent-hub .skill-manage-card {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.04) !important;
  color: #18191C !important;
}

[data-theme="light"] #section-agent-hub .acc-subtab-btn {
  background: #f5f5f7 !important;
  border: 1px solid #e5e5ea !important;
  color: #48484a !important;
}

[data-theme="light"] #section-agent-hub .acc-subtab-btn.active {
  background: #0071e3 !important;
  border-color: #0071e3 !important;
  color: #ffffff !important;
}

[data-theme="light"] .tag-pill {
  background: rgba(0, 113, 227, 0.08) !important;
  color: #0071e3 !important;
  border: 1px solid rgba(0, 113, 227, 0.2) !important;
  font-weight: 600 !important;
}

[data-theme="light"] .card-header-styled {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .chart-heading {
  color: #1d1d1f !important;
}

[data-theme="light"] .chart-subtext {
  color: #6e6e73 !important;
}

[data-theme="light"] .mode-radio-box {
  background: #fbfbfd !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
}

[data-theme="light"] .mode-radio-box:hover {
  background: #f5f5f7 !important;
}

[data-theme="light"] .mode-radio-box.selected {
  border-color: #0071e3 !important;
  background: rgba(0, 113, 227, 0.06) !important;
}

[data-theme="light"] .radio-name {
  color: #1d1d1f !important;
}

[data-theme="light"] .radio-desc {
  color: #6e6e73 !important;
}

[data-theme="light"] .sync-report-card {
  background: #f5f6f8 !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .report-stat-item .num {
  color: #1d1d1f !important;
}

[data-theme="light"] .report-stat-item .label {
  color: #6e6e73 !important;
}

[data-theme="light"] .telem-row {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .telem-label {
  color: #6e6e73 !important;
}

[data-theme="light"] .telem-val {
  color: #1d1d1f !important;
}

[data-theme="light"] .kpi-title {
  color: #6e6e73 !important;
}

[data-theme="light"] .kpi-number {
  color: #1d1d1f !important;
}

[data-theme="light"] .kpi-sub {
  color: #86868b !important;
}

[data-theme="light"] .table-card-header {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .stat-counter {
  color: #6e6e73 !important;
}

[data-theme="light"] .table-search-input,
[data-theme="light"] .search-box input {
  color: #1d1d1f !important;
}

[data-theme="light"] .table-search-input::placeholder,
[data-theme="light"] .search-box input::placeholder {
  color: rgba(0, 0, 0, 0.38) !important;
}

[data-theme="light"] .search-box {
  background: rgba(0, 0, 0, 0.04) !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .filter-select {
  background: rgba(0, 0, 0, 0.04) !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .apple-table th {
  background: #f5f6f8 !important;
  color: #6e6e73 !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .apple-table td {
  color: #1d1d1f !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .apple-table tr:hover td {
  background: rgba(0, 0, 0, 0.02) !important;
}

[data-theme="light"] .apple-table-viewport-wrap {
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
}

[data-theme="light"] .user-name-text,
[data-theme="light"] .drama-title-main,
[data-theme="light"] .drama-title-text {
  color: #1d1d1f !important;
}

[data-theme="light"] .user-sub-text,
[data-theme="light"] .drama-synopsis-sub,
[data-theme="light"] .drama-meta-sub {
  color: #6e6e73 !important;
}

/* Subtab Buttons in Light Mode (No more white on white) */
[data-theme="light"] .subtab-btn {
  background: rgba(0, 0, 0, 0.04) !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
  color: #48484a !important;
}

[data-theme="light"] .subtab-btn:hover {
  background: rgba(0, 0, 0, 0.08) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .subtab-btn.active {
  background: #0071e3 !important;
  color: #ffffff !important;
  border-color: #0071e3 !important;
}

/* Stage Top Bar and Refresh Button in Light Mode */
[data-theme="light"] .stage-top-bar {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .bar-breadcrumb {
  color: #6e6e73 !important;
}

[data-theme="light"] .bar-headline {
  color: #1d1d1f !important;
}

[data-theme="light"] .apple-btn-secondary {
  background: rgba(0, 0, 0, 0.05) !important;
  color: #1d1d1f !important;
  border: 1px solid rgba(0, 0, 0, 0.12) !important;
}

[data-theme="light"] .apple-btn-secondary:hover {
  background: rgba(0, 0, 0, 0.09) !important;
  color: #000000 !important;
}

/* BI Legend and Rank Index in Light Mode */
[data-theme="light"] .legend-pill {
  color: #48484a !important;
  font-weight: 600 !important;
}

[data-theme="light"] .kpi-title {
  color: #48484a !important;
  font-weight: 600 !important;
}

[data-theme="light"] .kpi-sub {
  color: #6e6e73 !important;
  font-weight: 500 !important;
}

[data-theme="light"] .kpi-badge.blue { background: rgba(0, 113, 227, 0.12) !important; color: #0071e3 !important; }
[data-theme="light"] .kpi-badge.cyan { background: rgba(0, 150, 214, 0.12) !important; color: #0077aa !important; }
[data-theme="light"] .kpi-badge.purple { background: rgba(147, 51, 234, 0.12) !important; color: #7e22ce !important; }
[data-theme="light"] .kpi-badge.pink { background: rgba(225, 29, 72, 0.12) !important; color: #be123c !important; }
[data-theme="light"] .kpi-badge.indigo { background: rgba(79, 70, 229, 0.12) !important; color: #4338ca !important; }
[data-theme="light"] .kpi-badge.green { background: rgba(22, 163, 74, 0.12) !important; color: #15803d !important; }
[data-theme="light"] .kpi-badge.amber { background: rgba(217, 119, 6, 0.12) !important; color: #b45309 !important; }
[data-theme="light"] .kpi-badge.red { background: rgba(220, 38, 38, 0.12) !important; color: #b91c1c !important; }

[data-theme="light"] .rank-index { color: #86868b !important; }
[data-theme="light"] .rank-index.rank-1 { color: #b45309 !important; }
[data-theme="light"] .rank-index.rank-2 { color: #475569 !important; }
[data-theme="light"] .rank-index.rank-3 { color: #c2410c !important; }
[data-theme="light"] .score-val { color: #1d1d1f !important; }
[data-theme="light"] .empty-table-cell { color: #6e6e73 !important; }
[data-theme="light"] .sub-text-col { color: #6e6e73 !important; }
[data-theme="light"] .dropdown-label { color: #1d1d1f !important; }
[data-theme="light"] .preview-ratio-label { color: #6e6e73 !important; }
[data-theme="light"] .info-title { color: #1d1d1f !important; }
[data-theme="light"] .info-list li { color: #48484a !important; }

[data-theme="light"] .el-dialog {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15) !important;
}

[data-theme="light"] .el-dialog__title {
  color: #1d1d1f !important;
}

[data-theme="light"] .el-dialog__header {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
  background: #f8fafc !important;
}

[data-theme="light"] .el-dialog__body {
  color: #1d1d1f !important;
}

[data-theme="light"] .el-dialog__footer {
  border-top: 1px solid rgba(0, 0, 0, 0.08) !important;
  background: #f8fafc !important;
}

[data-theme="light"] .tag-option-pill {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: #334155;
}

[data-theme="light"] .tag-option-pill.active {
  background: #0071e3;
  border-color: #0071e3;
  color: #ffffff;
}

.voucher-code-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 11px;
  border-radius: 8px;
  background: rgba(0, 113, 227, 0.12);
  border: 1px solid rgba(0, 113, 227, 0.3);
  color: #38bdf8;
  cursor: pointer;
  transition: all 0.18s ease;
}

.voucher-code-pill:hover {
  background: rgba(0, 113, 227, 0.22);
  transform: translateY(-1px);
}

.voucher-code-pill .copy-hint {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.14);
  color: #ffffff;
}

[data-theme="light"] .voucher-code-pill {
  background: #eff6ff;
  border-color: #93c5fd;
  color: #1d4ed8;
}

[data-theme="light"] .voucher-code-pill .copy-hint {
  background: #1d4ed8;
  color: #ffffff;
}

.generated-codes-preview-box {
  margin-top: 12px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.generated-codes-list {
  max-height: 130px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.generated-code-line {
  display: flex;
  justify-content: space-between;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.2);
}

[data-theme="light"] .generated-code-line {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #0f172a;
}

[data-theme="light"] .el-dialog .form-label,
[data-theme="light"] .dialog-form .form-label {
  color: #1d1d1f !important;
}

[data-theme="light"] .apple-input,
[data-theme="light"] .apple-textarea,
[data-theme="light"] .apple-select,
[data-theme="light"] .el-dialog .apple-input,
[data-theme="light"] .dialog-form .apple-input,
[data-theme="light"] .el-dialog .apple-textarea,
[data-theme="light"] .dialog-form .apple-textarea,
[data-theme="light"] .el-dialog .apple-select,
[data-theme="light"] .dialog-form .apple-select,
[data-theme="light"] .search-input {
  background: #ffffff !important;
  border: 1px solid #c7c7cc !important;
  color: #1d1d1f !important;
  font-weight: 500 !important;
}

[data-theme="light"] .apple-input:focus,
[data-theme="light"] .apple-textarea:focus,
[data-theme="light"] .apple-select:focus,
[data-theme="light"] .search-input:focus {
  border-color: #0071e3 !important;
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.18) !important;
  outline: none !important;
}

[data-theme="light"] .apple-input::placeholder,
[data-theme="light"] .apple-textarea::placeholder,
[data-theme="light"] .search-input::placeholder,
[data-theme="light"] .el-dialog .apple-input::placeholder,
[data-theme="light"] .dialog-form .apple-input::placeholder,
[data-theme="light"] .el-dialog .apple-textarea::placeholder,
[data-theme="light"] .dialog-form .apple-textarea::placeholder {
  color: #86868b !important;
  font-weight: 400 !important;
}

[data-theme="light"] option,
[data-theme="light"] .apple-select option,
[data-theme="light"] .el-dialog option {
  background: #ffffff !important;
  color: #1d1d1f !important;
  font-weight: 500 !important;
}

[data-theme="light"] .role-radio-item {
  background: #f5f5f7 !important;
  border: 1px solid #e5e5ea !important;
  color: #1d1d1f !important;
  font-weight: 500 !important;
  transition: all 0.2s ease;
}

[data-theme="light"] .role-radio-item:has(input:checked) {
  border-color: #0071e3 !important;
  background: #f0f7ff !important;
  color: #0071e3 !important;
  font-weight: 600 !important;
}

[data-theme="light"] .el-pagination.is-background .el-pager li,
[data-theme="light"] .el-pagination.is-background .btn-prev,
[data-theme="light"] .el-pagination.is-background .btn-next {
  background-color: rgba(0, 0, 0, 0.04) !important;
  color: #1d1d1f !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
}

[data-theme="light"] .el-pagination.is-background .el-pager li:not(.is-disabled).is-active {
  background-color: #0071e3 !important;
  color: #ffffff !important;
}

/* ========================================================================== */
/* RAG Knowledge Studio & Benchmark Radar Styling (Apple HIG Design)          */
/* ========================================================================== */
.rag-action-bar {
  margin-bottom: 20px;
  padding: 16px 20px;
}
.rag-action-bar .bar-btn-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.rag-benchmark-view .benchmark-grid {
  display: grid;
  grid-template-columns: 1fr 1.3fr;
  gap: 20px;
  margin-top: 16px;
}
@media (max-width: 1200px) {
  .rag-benchmark-view .benchmark-grid {
    grid-template-columns: 1fr;
  }
}
.rag-radar-container {
  width: 100%;
  height: 360px;
}
.radar-score-banner {
  padding: 14px;
  border-radius: 12px;
  background: rgba(0, 113, 227, 0.08);
  border: 1px solid rgba(0, 113, 227, 0.2);
  margin-top: 12px;
}
.score-pill-tag {
  font-size: 15px;
  font-weight: 700;
  color: #0071e3;
  margin-bottom: 6px;
}
.score-metrics-row {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--apple-text-secondary, #86868b);
  flex-wrap: wrap;
}
.score-highlight {
  font-weight: 700;
  color: #30d158;
}
.rag-chunker-view .chunker-grid {
  display: grid;
  grid-template-columns: 1fr 1.3fr;
  gap: 20px;
  margin-top: 16px;
}
@media (max-width: 1200px) {
  .rag-chunker-view .chunker-grid {
    grid-template-columns: 1fr;
  }
}
.debug-results-box {
  margin-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 12px;
}
.debug-res-header {
  font-size: 12px;
  font-weight: 600;
  color: #0071e3;
  margin-bottom: 8px;
}
.debug-cards-scroll {
  max-height: 280px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.debug-chunk-card {
  padding: 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 12px;
}
.chunk-meta-line {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}
.chunk-idx-tag {
  font-weight: 700;
  color: #0071e3;
}
.chunk-strat-tag {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(48, 209, 88, 0.15);
  color: #30d158;
}
.chunk-time-tag, .time-capsule-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 113, 227, 0.15);
  color: #0071e3;
}
.chunk-content-text {
  line-height: 1.5;
  color: var(--apple-text-primary, #f5f5f7);
}
.chunk-parent-hint {
  margin-top: 6px;
  font-size: 11px;
  color: var(--apple-text-secondary, #86868b);
  border-top: 1px dashed rgba(255, 255, 255, 0.08);
  padding-top: 4px;
}
.graph-status-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.status-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.status-indicator-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
}
.status-indicator-dot.live {
  background: #30d158;
  box-shadow: 0 0 10px #30d158;
}
.status-indicator-dot.fallback {
  background: #ff9500;
  box-shadow: 0 0 10px #ff9500;
}
.graph-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}
.graph-uri {
  font-size: 12px;
  color: var(--apple-text-secondary, #86868b);
}
.graph-search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.graph-search-bar .apple-input {
  flex: 1;
  min-width: 260px;
}
.entity-source {
  color: #0071e3;
}
.entity-target {
  color: #bf5af2;
}

/* Light Mode High-Contrast Enforcement */
[data-theme="light"] .rag-action-bar,
[data-theme="light"] .radar-card,
[data-theme="light"] .history-card,
[data-theme="light"] .chunk-debug-card,
[data-theme="light"] .chunk-list-card,
[data-theme="light"] .graph-status-card,
[data-theme="light"] .graph-triples-card {
  background: #ffffff !important;
  border-color: #e5e5ea !important;
  color: #1d1d1f !important;
}
[data-theme="light"] .chart-heading {
  color: #1d1d1f !important;
  font-weight: 700 !important;
}
[data-theme="light"] .chart-subtext {
  color: #48484a !important;
  font-weight: 500 !important;
}
[data-theme="light"] .radar-score-banner {
  background: #f0f7ff !important;
  border-color: #0071e3 !important;
}
[data-theme="light"] .score-metrics-row {
  color: #48484a !important;
  font-weight: 600 !important;
}
[data-theme="light"] .debug-chunk-card {
  background: #f5f5f7 !important;
  border-color: #e5e5ea !important;
}
[data-theme="light"] .chunk-content-text {
  color: #1d1d1f !important;
}
[data-theme="light"] .chunk-parent-hint {
  color: #48484a !important;
}
[data-theme="light"] .graph-title {
  color: #1d1d1f !important;
}
[data-theme="light"] .graph-uri {
  color: #48484a !important;
}
[data-theme="light"] .apple-table th {
  color: #1d1d1f !important;
  font-weight: 700 !important;
  background: #f5f5f7 !important;
  border-bottom: 1px solid #e5e5ea !important;
}
[data-theme="light"] .apple-table td {
  color: #1d1d1f !important;
  border-bottom: 1px solid #f2f2f7 !important;
}
[data-theme="light"] .empty-state,
[data-theme="light"] .empty-hint,
[data-theme="light"] .empty-text {
  color: #48484a !important;
  font-weight: 500 !important;
}
[data-theme="light"] .subtab-btn {
  color: #48484a !important;
  background: #f5f5f7 !important;
  border: 1px solid #e5e5ea !important;
}
[data-theme="light"] .subtab-btn.active {
  color: #ffffff !important;
  background: #0071e3 !important;
  border-color: #0071e3 !important;
  font-weight: 600 !important;
}

/* Health Probe Matrix */
.rag-probe-matrix {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.probe-card {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.probe-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.probe-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}
.probe-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--apple-text-primary, #ffffff);
}
.probe-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 600;
}
.probe-badge.badge-green {
  background: rgba(52, 199, 89, 0.15);
  color: #34c759;
  border: 1px solid rgba(52, 199, 89, 0.3);
}
.probe-badge.badge-orange {
  background: rgba(255, 149, 0, 0.15);
  color: #ff9500;
  border: 1px solid rgba(255, 149, 0, 0.3);
}
.probe-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: var(--apple-text-secondary, #86868b);
}
.detail-item span {
  font-weight: 600;
  color: var(--apple-text-primary, #ffffff);
  margin-right: 4px;
}
.probe-action {
  display: flex;
  justify-content: flex-end;
}
.btn-sm {
  padding: 6px 14px;
  font-size: 12px;
}

/* Tools Lifecycle Grid */
.rag-tools-view {
  margin-top: 10px;
}
.tools-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.tool-category-card {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.category-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 12px;
}
.category-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--apple-text-primary, #ffffff);
}
.category-desc {
  font-size: 12px;
  color: var(--apple-text-secondary, #86868b);
}
.tool-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.tool-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.tool-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.tool-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--apple-text-primary, #ffffff);
}
.tool-desc {
  font-size: 11px;
  color: var(--apple-text-secondary, #86868b);
  line-height: 1.4;
}
.timeout-settings-box {
  margin-top: 10px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.timeout-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--apple-text-primary, #ffffff);
}
.timeout-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--apple-text-secondary, #86868b);
}
.mini-input {
  width: 70px;
  padding: 4px 8px;
  text-align: center;
}

/* Light mode high contrast for tools & probes */
[data-theme="light"] .probe-card,
[data-theme="light"] .tool-category-card {
  background: #ffffff !important;
  border-color: #e5e5ea !important;
}
[data-theme="light"] .probe-name,
[data-theme="light"] .category-title,
[data-theme="light"] .tool-name,
[data-theme="light"] .timeout-title,
[data-theme="light"] .detail-item span {
  color: #1d1d1f !important;
}
[data-theme="light"] .tool-desc,
[data-theme="light"] .category-desc,
[data-theme="light"] .probe-details,
[data-theme="light"] .timeout-row {
  color: #48484a !important;
}
[data-theme="light"] .tool-item,
[data-theme="light"] .timeout-settings-box {
  background: #f5f5f7 !important;
  border-color: #e5e5ea !important;
}

/* Announcement Governance Enhancements */
.announcement-tag-badge {
  background: rgba(245, 158, 11, 0.12) !important;
  color: #f59e0b !important;
  border: 1px solid rgba(245, 158, 11, 0.28) !important;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 9999px;
  font-size: 11px;
}

.announcement-content-col {
  max-width: 320px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.announcement-dialog {
  max-width: 540px;
  width: 92%;
}

.tag-quick-select {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.tag-option-pill {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.75);
  padding: 5px 12px;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tag-option-pill:hover,
.tag-option-pill.active {
  background: rgba(0, 113, 227, 0.2);
  border-color: #0071e3;
  color: #2997ff;
}


/* ========================================================================= */
/* 互动合规风控 (弹幕/评论机审) Apple HIG 视觉呼吸感与滑动窗口规范样式       */
/* ========================================================================= */
.content-moderation-card {
  padding: 24px !important;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  margin-bottom: 20px;
}

.moderation-main-section {
  padding: 0 4px;
}

.header-action-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 多维分类统计胶囊栏 */
.category-pills-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.category-pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--apple-text-sub, rgba(255, 255, 255, 0.65));
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.category-pill-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--apple-text-main, #ffffff);
  border-color: rgba(255, 255, 255, 0.2);
}

.category-pill-btn.active {
  background: rgba(0, 113, 227, 0.18);
  border-color: #0071e3;
  color: #2997ff;
  box-shadow: 0 0 12px rgba(0, 113, 227, 0.25);
}

.pill-count-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  color: inherit;
}

.category-pill-btn.active .pill-count-badge {
  background: rgba(41, 151, 255, 0.25);
  color: #ffffff;
}

/* 滑动窗口表格滚动区 */
.apple-table-scroll-window {
  max-height: 480px;
  overflow-y: auto;
  overflow-x: auto;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.015);
  border: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 16px;
}

.apple-table-scroll-window::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.apple-table-scroll-window::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.18);
  border-radius: 3px;
}

.apple-table-scroll-window::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
}

/* 统一分页栏 */
.moderation-pagination-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.pagination-summary {
  font-size: 12px;
  color: var(--apple-text-sub, rgba(255, 255, 255, 0.5));
}

/* 4号智能体巡检雷达动态光效 */
.btn-radar {
  position: relative;
  overflow: hidden;
  box-shadow: 0 0 14px rgba(0, 113, 227, 0.3);
}

.btn-radar:not(:disabled):hover {
  box-shadow: 0 0 20px rgba(0, 113, 227, 0.55);
}

/* 自迭代建议词角标 */
.proposal-trigger-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.proposal-count-pill {
  padding: 1px 7px;
  border-radius: 10px;
  background: #ff3b30;
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.3;
}

/* 抽屉样式与卡片 */
.proposals-drawer-body {
  padding: 16px;
  color: var(--apple-text-main, #ffffff);
}

.drawer-top-bar {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(14, 165, 233, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.drawer-tip {
  font-size: 13px;
  line-height: 1.6;
  color: #7dd3fc;
  font-weight: 500;
  margin: 0;
}

[data-theme="light"] .drawer-top-bar {
  background: #f0f9ff !important;
  border: 1px solid #bae6fd !important;
}

[data-theme="light"] .drawer-tip {
  color: #0369a1 !important;
  font-weight: 600 !important;
}

[data-theme="light"] .proposal-card-item {
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03) !important;
}

[data-theme="light"] .prop-word {
  color: #dc2626 !important;
}

[data-theme="light"] .reason-val {
  color: #1e293b !important;
}

[data-theme="light"] .source-val {
  color: #334155 !important;
}

[data-theme="light"] .muted-label {
  color: #64748b !important;
}

.proposals-list-scroll {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: calc(100vh - 160px);
  overflow-y: auto;
}

.proposal-card-item {
  padding: 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.prop-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.prop-word {
  font-size: 16px;
  color: #ff3b30;
}

.prop-badges {
  display: flex;
  gap: 6px;
}

.prop-reason, .prop-source {
  font-size: 13px;
  display: flex;
  gap: 6px;
}

.muted-label {
  color: var(--apple-text-sub, rgba(255, 255, 255, 0.45));
  white-space: nowrap;
}

.source-val {
  color: rgba(255, 255, 255, 0.7);
  word-break: break-all;
}

/* 巡检研判报告模态弹窗 */
.inspect-report-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.inspect-report-modal {
  width: 920px;
  max-width: 95vw;
  max-height: 88vh;
  border-radius: 20px;
  background: rgba(24, 24, 28, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.report-modal-header {
  padding: 24px 28px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.report-badge {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #2997ff;
  display: block;
  margin-bottom: 4px;
}

.report-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  color: #ffffff;
}

.report-meta {
  font-size: 13px;
  color: var(--apple-text-sub, rgba(255, 255, 255, 0.6));
  margin: 6px 0 0 0;
}

.report-modal-body {
  padding: 24px 28px;
  overflow-y: auto;
  flex: 1;
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.violations-table-wrap {
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  max-height: 280px;
  overflow-y: auto;
}

.suggested-words-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.suggested-word-chip {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.chip-meta {
  display: flex;
  gap: 6px;
  margin: 6px 0;
}

.chip-reason {
  font-size: 12px;
  color: var(--apple-text-sub, rgba(255, 255, 255, 0.55));
  margin: 0;
}

.report-modal-footer {
  padding: 16px 28px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  justify-content: flex-end;
}

.empty-ok-state, .empty-drawer-state {
  text-align: center;
  padding: 32px;
  color: var(--apple-text-sub, rgba(255, 255, 255, 0.5));
  font-size: 13px;
}



/* Light Mode High-Contrast Overrides for 4号合规官巡检报告模态框 */
[data-theme="light"] .inspect-report-modal {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.16) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .inspect-report-modal .report-modal-header {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
  background: #f8fafc !important;
}

[data-theme="light"] .inspect-report-modal .report-title {
  color: #0f172a !important;
  font-weight: 700 !important;
}

[data-theme="light"] .inspect-report-modal .report-meta {
  color: #475569 !important;
  font-weight: 500 !important;
}

[data-theme="light"] .inspect-report-modal .section-title {
  color: #0f172a !important;
  font-weight: 700 !important;
}

[data-theme="light"] .inspect-report-modal .report-stat-card {
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
}

[data-theme="light"] .inspect-report-modal .stat-lbl {
  color: #64748b !important;
  font-weight: 500 !important;
}

[data-theme="light"] .inspect-report-modal .stat-num {
  color: #0f172a !important;
  font-weight: 700 !important;
}

[data-theme="light"] .inspect-report-modal .violations-table-wrap {
  background: #ffffff !important;
  border: 1px solid #e2e8f0 !important;
}

[data-theme="light"] .inspect-report-modal .apple-table th {
  background: #f1f5f9 !important;
  color: #0f172a !important;
  font-weight: 700 !important;
  border-bottom: 1px solid #cbd5e1 !important;
}

[data-theme="light"] .inspect-report-modal .apple-table td {
  color: #1e293b !important;
  border-bottom: 1px solid #f1f5f9 !important;
}

[data-theme="light"] .inspect-report-modal .suggested-word-chip {
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  color: #0f172a !important;
}

[data-theme="light"] .inspect-report-modal .chip-reason {
  color: #475569 !important;
}

[data-theme="light"] .inspect-report-modal .report-modal-footer {
  border-top: 1px solid rgba(0, 0, 0, 0.08) !important;
  background: #f8fafc !important;
}

[data-theme="light"] .inspect-report-modal .btn-secondary {
  background: #f1f5f9 !important;
  border: 1px solid #cbd5e1 !important;
  color: #1e293b !important;
  font-weight: 600 !important;
}

[data-theme="light"] .inspect-report-modal .btn-secondary:hover {
  background: #e2e8f0 !important;
  color: #0f172a !important;
}



/* 4号巡检动态进度条 HUD */
.inspect-progress-hud {
  margin-bottom: 20px;
  padding: 18px 24px;
  border-radius: 16px;
  background: rgba(22, 24, 29, 0.95);
  border: 1px solid rgba(0, 113, 227, 0.35);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
}

[data-theme="light"] .inspect-progress-hud {
  background: #ffffff !important;
  border: 1px solid #bae6fd !important;
  box-shadow: 0 12px 32px rgba(0, 113, 227, 0.08) !important;
}

.progress-hud-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.hud-indicator-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #0071e3;
}

.hud-indicator-dot.pulse {
  animation: pulse-ring 1.5s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
}

@keyframes pulse-ring {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 113, 227, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(0, 113, 227, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 113, 227, 0); }
}

.hud-title {
  font-size: 14px;
  color: var(--apple-text-main, #ffffff);
}

[data-theme="light"] .hud-title {
  color: #0f172a !important;
}

.hud-percent {
  margin-left: auto;
  font-size: 15px;
  font-weight: 700;
  color: #0071e3;
}

.hud-stage-desc {
  font-size: 12px;
  color: var(--apple-text-sub, rgba(255, 255, 255, 0.6));
  margin: 0;
}

[data-theme="light"] .hud-stage-desc {
  color: #475569 !important;
}

</style>

<style scoped>

/* ========================================================================== */
/* BI 3-Pillar Matrix & Audit Trail Cockpit Styling                          */
/* ========================================================================== */
.bi-matrix-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 1200px) {
  .bi-matrix-grid {
    grid-template-columns: 1fr;
  }
}

.matrix-card {
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.matrix-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.matrix-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.matrix-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.matrix-dot.purple { background: #BF5AF2; box-shadow: 0 0 8px rgba(191, 90, 242, 0.5); }
.matrix-dot.blue { background: #0071E3; box-shadow: 0 0 8px rgba(0, 113, 227, 0.5); }
.matrix-dot.green { background: #30D158; box-shadow: 0 0 8px rgba(48, 209, 88, 0.5); }

.matrix-heading {
  font-size: 13px;
  font-weight: 700;
  color: var(--apple-text-primary, #FFFFFF);
}

.matrix-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}
.matrix-badge.purple { background: rgba(191, 90, 242, 0.15); color: #BF5AF2; border: 1px solid rgba(191, 90, 242, 0.3); }
.matrix-badge.blue { background: rgba(0, 113, 227, 0.15); color: #0071E3; border: 1px solid rgba(0, 113, 227, 0.3); }
.matrix-badge.green { background: rgba(48, 209, 88, 0.15); color: #30D158; border: 1px solid rgba(48, 209, 88, 0.3); }

.matrix-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  background: rgba(255, 255, 255, 0.03);
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.m-stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.m-stat-label {
  font-size: 11px;
  color: var(--apple-text-secondary, #86868B);
}

.m-stat-val {
  font-size: 14px;
  font-weight: 700;
  color: var(--apple-text-primary, #FFFFFF);
  font-variant-numeric: tabular-nums;
}
.m-stat-val.green-text { color: #30D158; }
.m-stat-val.blue-text { color: #0071E3; }
.m-stat-val.amber-text { color: #FF9F0A; }

.matrix-footer-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: var(--apple-text-secondary, #86868B);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 8px;
}

.status-indicator-tag.success {
  color: #30D158;
  font-weight: 600;
}

/* Audit Cockpit Block */
.audit-cockpit-block {
  padding: 20px;
}

.audit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.audit-stats-summary-pills {
  display: flex;
  align-items: center;
  gap: 8px;
}

.audit-pill {
  font-size: 11px;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: var(--apple-text-primary, #FFFFFF);
}
.audit-pill.success {
  background: rgba(48, 209, 88, 0.12);
  color: #30D158;
  border-color: rgba(48, 209, 88, 0.25);
}

.audit-filter-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-label {
  font-size: 11px;
  color: var(--apple-text-secondary, #86868B);
  font-weight: 600;
  white-space: nowrap;
}

.audit-select {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: var(--apple-text-primary, #FFFFFF);
  font-size: 12px;
  border-radius: 8px;
  padding: 5px 10px;
  outline: none;
}

.filter-search-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 240px;
}

.audit-search-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: var(--apple-text-primary, #FFFFFF);
  font-size: 12px;
  border-radius: 8px;
  padding: 5px 12px;
  outline: none;
}

.audit-btn-search {
  background: var(--apple-blue, #0071E3);
  color: #FFFFFF;
  border: none;
  font-size: 12px;
  font-weight: 600;
  padding: 5px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.audit-btn-search:hover {
  filter: brightness(1.1);
}

.audit-table-wrap {
  overflow-x: auto;
}

.user-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--apple-text-primary, #FFFFFF);
}

.role-sub-badge {
  font-size: 10px;
  color: var(--apple-text-secondary, #86868B);
  text-transform: uppercase;
}

.module-action-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.module-tag {
  font-size: 11px;
  font-weight: 600;
  color: #0071E3;
}

.action-tag {
  font-size: 10px;
  color: var(--apple-text-secondary, #86868B);
  font-family: monospace;
}

.audit-summary-cell {
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
}

.btn-detail-pill {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: var(--apple-text-primary, #FFFFFF);
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-detail-pill:hover {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.3);
}

.audit-pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.pagination-info {
  font-size: 11px;
  color: var(--apple-text-secondary, #86868B);
}

.pagination-btns {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-nav-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: var(--apple-text-primary, #FFFFFF);
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
}
.page-nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-indicator {
  font-size: 11px;
  color: var(--apple-text-primary, #FFFFFF);
  font-weight: 600;
}

/* Modal Body */
.audit-modal-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.audit-modal-summary-box {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 12px;
}

.modal-sum-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.audit-json-box {
  background: #0d1117;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.json-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.04);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 11px;
  color: #8b949e;
}

.json-content {
  padding: 12px;
  margin: 0;
  max-height: 280px;
  overflow-y: auto;
  font-family: Consolas, Monaco, monospace;
  font-size: 12px;
  color: #7ee787;
  line-height: 1.45;
}


/* Wallpaper Admin Styling */
.wallpaper-admin-wrap {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.wallpaper-admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-line, rgba(0, 0, 0, 0.08));
  border-radius: 16px;
  backdrop-filter: blur(20px);
  box-shadow: var(--glass-shadow);
  color: var(--text-primary, #18191C);
  transition: all 0.3s ease;
}

[data-theme="dark"] .wallpaper-admin-header {
  background: var(--bg-surface, rgba(24, 25, 28, 0.85));
  border: 1px solid var(--border-glass, rgba(255, 255, 255, 0.1));
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  color: var(--text-primary, #F1F2F3);
}

.section-desc {
  font-size: 13px;
  color: var(--text-secondary, #86868b);
  margin-top: 4px;
}

.wallpaper-config-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 24px;
}

.config-form-card,
.preview-stage-card {
  padding: 24px;
  border-radius: 16px;
  background: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-line, rgba(0, 0, 0, 0.08));
  backdrop-filter: blur(20px);
  box-shadow: var(--glass-shadow);
  color: var(--text-primary, #18191C);
  transition: all 0.3s ease;
}

[data-theme="dark"] .config-form-card,
[data-theme="dark"] .preview-stage-card {
  background: var(--bg-surface, rgba(24, 25, 28, 0.85));
  border: 1px solid var(--border-glass, rgba(255, 255, 255, 0.1));
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  color: var(--text-primary, #F1F2F3);
}

.card-subtitle {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--text-primary, #f5f5f7);
}

.form-group-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary, #f5f5f7);
}

.label-with-value {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.value-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(0, 113, 227, 0.15);
  color: var(--apple-blue, #2997ff);
  font-weight: 600;
}

.mode-selector-capsules {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.mode-capsule-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
  background: var(--bg-secondary, rgba(255, 255, 255, 0.04));
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.mode-capsule-btn:hover {
  background: var(--bg-hover, rgba(255, 255, 255, 0.08));
  border-color: rgba(255, 255, 255, 0.2);
}

.mode-capsule-btn.active {
  background: rgba(0, 113, 227, 0.15);
  border-color: var(--apple-blue, #2997ff);
}

.capsule-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #f5f5f7);
}

.mode-capsule-btn.active .capsule-title {
  color: var(--apple-blue, #2997ff);
}

.capsule-sub {
  font-size: 11px;
  color: var(--text-secondary, #86868b);
  margin-top: 3px;
}

.apple-input-text {
  width: 100%;
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--bg-secondary, rgba(255, 255, 255, 0.04));
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.12));
  color: var(--text-primary, #f5f5f7);
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s ease;
}

.apple-input-text:focus {
  border-color: var(--apple-blue, #2997ff);
}

.apple-range-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--border-color, rgba(255, 255, 255, 0.12));
  outline: none;
  accent-color: var(--apple-blue, #2997ff);
  cursor: pointer;
}

.form-hint {
  font-size: 11px;
  color: var(--text-secondary, #86868b);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.preview-theme-switch {
  display: flex;
  gap: 6px;
  background: var(--bg-secondary, rgba(255, 255, 255, 0.04));
  padding: 3px;
  border-radius: 8px;
}

.preview-toggle-btn {
  padding: 4px 10px;
  border: none;
  background: transparent;
  color: var(--text-secondary, #86868b);
  font-size: 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.preview-toggle-btn.active {
  background: var(--apple-blue, #0071E3);
  color: #ffffff;
}

.preview-viewport-mock {
  position: relative;
  width: 100%;
  height: 380px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.1));
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-bg-layer {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  z-index: 1;
  transition: filter 0.2s ease;
}

.preview-mask-layer {
  position: absolute;
  inset: 0;
  z-index: 2;
  transition: background-color 0.2s ease;
}

.mock-login-box {
  position: relative;
  z-index: 5;
  width: 220px;
  padding: 20px 16px;
  border-radius: 12px;
  background: rgba(30, 30, 32, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(16px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.preview-viewport-mock.light .mock-login-box {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.mock-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 4px;
}

.mock-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary, #ffffff);
}

.preview-viewport-mock.light .mock-title {
  color: #1d1d1f;
}

.mock-sub {
  font-size: 10px;
  color: var(--text-secondary, #86868b);
}

.mock-input-row {
  height: 24px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.preview-viewport-mock.light .mock-input-row {
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.mock-button-row {
  height: 26px;
  border-radius: 6px;
  background: var(--apple-blue, #0071E3);
  margin-top: 4px;
}

</style>
