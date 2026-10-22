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
          <div class="nav-group-title" v-if="isSidebarExpanded">模型与系统引擎</div>
          <div class="nav-divider" v-else></div>

          <button 
            class="nav-tab-item" 
            :class="{ active: currentTab === 'engine' }" 
            @click="selectTab('engine')"
            id="admin-tab-engine"
            title="本地/云端模型引擎与 RAG 参数"
          >
            <el-icon class="nav-icon"><Setting /></el-icon>
            <span class="nav-label" v-if="isSidebarExpanded">模型引擎设置</span>
          </button>
        </nav>
      </aside>

      <!-- Main Stage Workspace -->
      <main class="admin-main-stage">
        <!-- Top Action Bar -->
        <header class="stage-top-bar">
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
        <section v-if="currentTab === 'bi'" class="content-section" id="section-bi">
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
        </section>

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
                        <span>❤️ {{ formatNumber(d.like_count) }}</span>
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
                        <span class="coin-tag">💰 {{ u.coins ?? 50 }} 币</span>
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
        <section v-if="currentTab === 'contents'" class="content-section" id="section-contents">
          <div class="dual-subtabs-row">
            <button 
              class="subtab-btn" 
              :class="{ active: contentSubTab === 'queue' }"
              @click="switchContentSubTab('queue')"
              id="subtab-review-queue"
            >
              <span>机审待办工单 ({{ reviewQueueList.length }})</span>
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
              <span>弹幕机审列表 ({{ danmakusList.length }})</span>
            </button>
            <button 
              class="subtab-btn" 
              :class="{ active: contentSubTab === 'comments' }"
              @click="switchContentSubTab('comments')"
              id="subtab-comments"
            >
              <span>剧迷评论列表 ({{ commentsList.length }})</span>
            </button>
          </div>

          <!-- SUBTAB 1: 机审待办工单流 -->
          <div v-if="contentSubTab === 'queue'" class="table-card glass-card" id="card-review-queue">
            <div class="table-card-header">
              <div>
                <h3 class="chart-heading">社区内容风控工单待办流</h3>
                <p class="chart-subtext">由 DFA 自动状态机实时拦截并标记的违规发言，支持审核员 1 键放行或驳回清理</p>
              </div>
              <span class="stat-counter">待审工单 {{ reviewQueueList.length }} 笔</span>
            </div>

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
                <tr v-for="item in reviewQueueList" :key="item.id" :id="'review-row-' + item.id">
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

          <!-- SUBTAB 2: DFA 敏感词库治理 & 实时沙盒 -->
          <div v-if="contentSubTab === 'lexicon'" class="lexicon-composite-grid" id="card-sensitive-lexicon">
            <!-- Left: Lexicon Table -->
            <div class="table-card glass-card">
              <div class="table-card-header">
                <div>
                  <h3 class="chart-heading">DFA 前缀树敏感词库</h3>
                  <p class="chart-subtext">实时同步 MySQL 与内存 Trie 树，支持添加自定义敏感词及分类治理</p>
                </div>
                <button class="apple-btn-primary" @click="openAddWordModal" id="btn-add-sensitive-word">
                  <el-icon><Plus /></el-icon>
                  <span>录入敏感词</span>
                </button>
              </div>

              <!-- Filter Bar -->
              <div class="lexicon-filters-row">
                <input 
                  v-model="sensitiveWordSearch" 
                  type="text" 
                  class="apple-input search-input" 
                  placeholder="搜索敏感词..." 
                  @input="loadSensitiveWords"
                  id="input-search-word"
                />
                <select v-model="sensitiveWordCategory" class="apple-select" @change="loadSensitiveWords">
                  <option value="ALL">全部分类</option>
                  <option value="涉政">涉政</option>
                  <option value="暴恐">暴恐</option>
                  <option value="违禁">违禁</option>
                  <option value="涉黄">涉黄</option>
                  <option value="辱骂">辱骂</option>
                  <option value="广告">广告</option>
                </select>
                <select v-model="sensitiveWordLevel" class="apple-select" @change="loadSensitiveWords">
                  <option value="ALL">全部风险等级</option>
                  <option value="HIGH">高风险 (HIGH)</option>
                  <option value="MEDIUM">中风险 (MEDIUM)</option>
                  <option value="LOW">低风险 (LOW)</option>
                </select>
              </div>

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
                    <td colspan="5" class="empty-table-cell">暂无自定义敏感词记录</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Right: DFA Live Testing Sandbox -->
            <div class="glass-card dfa-sandbox-card" id="card-dfa-sandbox">
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
                      {{ dfaTestResult.has_violation ? '⚠️ 命中违禁词！' : '✅ 检测通过（安全无违规）' }}
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
          <div v-if="contentSubTab === 'danmakus'" class="table-card glass-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <div style="display: flex; gap: 12px; align-items: center;">
                <input
                  v-model="danmakuSearchQuery"
                  type="text"
                  placeholder="搜索弹幕内容/关键词..."
                  class="apple-input"
                  style="width: 260px;"
                  @keyup.enter="fetchDanmakus"
                />
                <button class="btn-action" @click="fetchDanmakus">
                  <el-icon><Search /></el-icon>
                  <span>筛选</span>
                </button>
              </div>
              <div>
                <button
                  id="btn-batch-delete-danmakus"
                  class="btn-action btn-danger"
                  :disabled="selectedDanmakuIds.length === 0"
                  @click="handleBatchDeleteDanmakus"
                >
                  <el-icon><Delete /></el-icon>
                  <span>批量下架违规 ({{ selectedDanmakuIds.length }})</span>
                </button>
              </div>
            </div>
            <table class="apple-table">
              <thead>
                <tr>
                  <th style="width: 40px;">
                    <input
                      type="checkbox"
                      :checked="selectedDanmakuIds.length > 0 && selectedDanmakuIds.length === danmakusList.length"
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
                <tr v-for="dm in danmakusList" :key="dm.id">
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
              </tbody>
            </table>
          </div>

          <!-- SUBTAB 4: 剧迷评论列表 -->
          <div v-if="contentSubTab === 'comments'" class="table-card glass-card">
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
                <tr v-for="cm in commentsList" :key="cm.id">
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
              </tbody>
            </table>
          </div>
        </section>

        <!-- ================================================================= -->
        <!-- TAB 8: 大模型与 RAG 引擎                                          -->
        <!-- ================================================================= -->
        <section v-if="currentTab === 'engine'" class="content-section" id="section-engine">
          <div class="engine-config-grid">
            <div class="glass-card engine-card">
              <div class="card-header-styled">
                <el-icon class="head-icon"><Setting /></el-icon>
                <div>
                  <h3 class="chart-heading">伴读助手与 RAG 大模型配置</h3>
                  <p class="chart-subtext">支持自主输入模型标识（如 deepseek-r1, qwen-2.5-72b），无内置预定锁定</p>
                </div>
              </div>

              <div class="engine-form">
                <div class="form-group">
                  <label class="form-label">大模型名称 (自定义输入)</label>
                  <input v-model="engineForm.modelName" class="apple-input" placeholder="输入大模型名称（如 deepseek-r1:7b）" />
                </div>

                <div class="form-group">
                  <label class="form-label">模型推理温度 (Temperature: {{ engineForm.temperature }})</label>
                  <el-slider v-model="engineForm.temperature" :min="0" :max="1" :step="0.05" />
                </div>

                <div class="form-group">
                  <label class="form-label">伴读助手人设提示词 (System Prompt)</label>
                  <textarea v-model="engineForm.prompt" class="apple-textarea" rows="4"></textarea>
                </div>

                <button class="apple-btn-primary" @click="saveEngineConfig">
                  <el-icon><Check /></el-icon>
                  <span>保存模型引擎配置</span>
                </button>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>

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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminHeader from '../components/AdminHeader.vue'
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
  Promotion
} from '@element-plus/icons-vue'
import { 
  adminApi, 
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
  type SensitiveWordTestResult
} from '../api/admin'

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
const currentTab = ref<'bi' | 'dramas' | 'sync' | 'carousels' | 'users' | 'applications' | 'contents' | 'engine'>('bi')

const tabTitleMap: Record<string, string> = {
  bi: 'BI 全景驾驶舱与预测走势',
  dramas: '短剧资产编目与封面治理',
  sync: '网盘增量/全量同步中心',
  carousels: '首页 5 秒焦点轮播运营调度',
  users: '用户管理与 RBAC 权限流转',
  applications: '资质双轨入驻审批 (创作者/审核员)',
  contents: '互动合规风控 (弹幕/评论机审)',
  engine: '模型引擎与 RAG 参数配置'
}

const currentTabTitle = computed(() => tabTitleMap[currentTab.value] || '管理控制台')

function selectTab(tab: any) {
  currentTab.value = tab
  if (tab === 'bi') {
    nextTick(() => initBiChart())
  }
}

// Data States
const loading = ref(false)
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
const contentSubTab = ref<'queue' | 'lexicon' | 'danmakus' | 'comments'>('queue')
const reviewQueueList = ref<ReviewQueueItem[]>([])
const sensitiveWordsList = ref<SensitiveWordItem[]>([])
const sensitiveWordsTotal = ref(0)
const sensitiveWordSearch = ref('')
const sensitiveWordCategory = ref('ALL')
const sensitiveWordLevel = ref('ALL')
const showAddWordDialog = ref(false)
const newWordForm = ref({ word: '', category: '违禁', level: 'HIGH' })
const dfaTestText = ref('')
const dfaTestResult = ref<SensitiveWordTestResult | null>(null)
const dfaTesting = ref(false)
const danmakusList = ref<AdminDanmakuItem[]>([])
const selectedDanmakuIds = ref<string[]>([])
const danmakuSearchQuery = ref('')
const commentsList = ref<AdminCommentItem[]>([])

// Engine Form
const engineForm = ref({
  modelName: localStorage.getItem('cinema_active_model') || 'deepseek-r1:7b',
  temperature: 0.7,
  prompt: '你是一位精通短剧镜头语言与剧情反转的电影解说伴读助手。'
})

const route = useRoute()

let themeObserver: MutationObserver | null = null

onMounted(async () => {
  if (route.query.tab && typeof route.query.tab === 'string') {
    currentTab.value = route.query.tab as any
  }
  await loadAllData()
  window.addEventListener('resize', handleWindowResize)

  themeObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.type === 'attributes' && m.attributeName === 'data-theme') {
        if (currentTab.value === 'bi') {
          initBiChart()
        }
      }
    }
  })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleWindowResize)
  if (themeObserver) {
    themeObserver.disconnect()
    themeObserver = null
  }
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

function handleWindowResize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

async function loadAllData() {
  loading.value = true
  try {
    await Promise.all([
      loadBiOverview(),
      loadBiTrends(),
      loadDramas(),
      loadDramaOptions(),
      loadCarousels(),
      loadUsers(),
      loadApplications(),
      loadContents()
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
async function loadBiOverview() {
  const res: any = await adminApi.getBiMetrics()
  const data = res?.data || res
  if (data?.bi_cards) {
    biMetrics.value = data.bi_cards
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

  // Confidence Bounds for prediction
  const upperData = [
    ...history.views.slice(0, -1).map(() => null),
    lastHistoryVal,
    ...prediction.upper_bound
  ]
  const lowerData = [
    ...history.views.slice(0, -1).map(() => null),
    lastHistoryVal,
    ...prediction.lower_bound
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
        name: '置信区间上限',
        type: 'line',
        data: upperData,
        lineStyle: { opacity: 0 },
        stack: 'confidence-band',
        symbol: 'none'
      },
      {
        name: '置信区间带 (95%)',
        type: 'line',
        data: lowerData,
        lineStyle: { opacity: 0 },
        areaStyle: {
          color: 'rgba(48, 209, 88, 0.15)'
        },
        stack: 'confidence-band',
        symbol: 'none'
      }
    ]
  }

  chartInstance.setOption(option)
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
function switchContentSubTab(tab: 'queue' | 'lexicon' | 'danmakus' | 'comments') {
  contentSubTab.value = tab
  if (tab === 'queue') {
    loadReviewQueue()
  } else if (tab === 'lexicon') {
    loadSensitiveWords()
  }
}

async function loadContents() {
  try {
    const [dmRes, cmRes, qRes, swRes]: any = await Promise.all([
      adminApi.getDanmakus({ per_page: 50 }),
      adminApi.getComments({ per_page: 50 }),
      adminApi.getReviewQueue('PENDING'),
      adminApi.getSensitiveWords({ per_page: 100 })
    ])
    danmakusList.value = dmRes?.data?.items || dmRes?.items || []
    commentsList.value = cmRes?.data?.items || cmRes?.items || []
    reviewQueueList.value = qRes?.data || qRes || []
    const swData = swRes?.data || swRes || {}
    sensitiveWordsList.value = swData?.items || []
    sensitiveWordsTotal.value = swData?.total || 0
  } catch (e) {
    console.error('Error loading content moderation records:', e)
  }
}

async function loadReviewQueue() {
  try {
    const res: any = await adminApi.getReviewQueue('PENDING')
    reviewQueueList.value = res?.data || res || []
  } catch (e) {
    console.error('Failed to load review queue:', e)
  }
}

async function handleReviewDecision(reviewId: string, decision: 'APPROVED' | 'REJECTED') {
  try {
    await adminApi.makeReviewDecision(reviewId, decision)
    reviewQueueList.value = reviewQueueList.value.filter(r => r.id !== reviewId)
    ElMessage.success(`风控裁决已生效：${decision === 'APPROVED' ? '放行通过' : '违规驳回并清理'}`)
  } catch (err: any) {
    ElMessage.error(err.message || '裁决操作失败')
  }
}

async function loadSensitiveWords() {
  try {
    const res: any = await adminApi.getSensitiveWords({
      query: sensitiveWordSearch.value.trim() || undefined,
      category: sensitiveWordCategory.value !== 'ALL' ? sensitiveWordCategory.value : undefined,
      level: sensitiveWordLevel.value !== 'ALL' ? sensitiveWordLevel.value : undefined,
      per_page: 100
    })
    const data = res?.data || res
    sensitiveWordsList.value = data?.items || []
    sensitiveWordsTotal.value = data?.total || 0
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
    ElMessage.success(`敏感词 [${newWordForm.value.word.trim()}] 录入成功，DFA 树已即刻热重载！`)
    await loadSensitiveWords()
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

async function fetchDanmakus() {
  try {
    const dmRes: any = await adminApi.getDanmakus({
      per_page: 50,
      keyword: danmakuSearchQuery.value.trim() || undefined
    })
    danmakusList.value = dmRes?.data?.items || dmRes?.items || []
  } catch (e: any) {
    ElMessage.error(e.message || '查询弹幕列表失败')
  }
}

function toggleSelectAllDanmakus(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.checked) {
    selectedDanmakuIds.value = danmakusList.value.map(d => d.id)
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
    selectedDanmakuIds.value = []
  } catch (err: any) {
    ElMessage.error(err.message || '批量删除失败')
  }
}

async function handleDeleteDanmaku(id: string) {
  try {
    await adminApi.deleteDanmaku(id)
    danmakusList.value = danmakusList.value.filter(d => d.id !== id)
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
    ElMessage.success('违规评论已清理')
  } catch (err: any) {
    ElMessage.error(err.message || '删除失败')
  }
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
</script>

<style scoped>
/* ========================================================================== */
/* Apple HIG Translucent Layout & Responsive Collapsible Sidebar              */
/* ========================================================================== */
.admin-page-root {
  min-height: 100vh;
  background-color: var(--apple-bg, #0d0d11);
  color: var(--apple-text-primary, #F5F5F7);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow-x: hidden;
}

.admin-layout-wrapper {
  display: flex;
  flex: 1;
  min-height: calc(100vh - 64px);
  position: relative;
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
  position: sticky;
  top: 64px;
  height: calc(100vh - 64px);
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
  padding: 24px 32px 60px 32px;
  position: relative;
  z-index: 10;
  max-width: 1600px;
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
</style>

<!-- Global Non-Scoped Overrides for Teleported Element Plus Dialogs & Form Elements -->
<style>
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

[data-theme="light"] .el-dialog .form-label,
[data-theme="light"] .dialog-form .form-label {
  color: #1d1d1f !important;
}

[data-theme="light"] .el-dialog .apple-input,
[data-theme="light"] .dialog-form .apple-input,
[data-theme="light"] .el-dialog .apple-textarea,
[data-theme="light"] .dialog-form .apple-textarea,
[data-theme="light"] .el-dialog .apple-select,
[data-theme="light"] .dialog-form .apple-select {
  background: rgba(0, 0, 0, 0.03) !important;
  border: 1px solid rgba(0, 0, 0, 0.12) !important;
  color: #1d1d1f !important;
}

[data-theme="light"] .el-dialog .apple-input::placeholder,
[data-theme="light"] .dialog-form .apple-input::placeholder,
[data-theme="light"] .el-dialog .apple-textarea::placeholder,
[data-theme="light"] .dialog-form .apple-textarea::placeholder {
  color: rgba(0, 0, 0, 0.38) !important;
}

[data-theme="light"] .el-dialog option {
  background: #ffffff !important;
  color: #1d1d1f !important;
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
</style>
