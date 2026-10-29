<template>
  <div class="landing-page-container">
    <!-- Ambient Aurora Orbs Background -->
    <div class="landing-ambient-bg">
      <div class="aurora-orb orb-1"></div>
      <div class="aurora-orb orb-2"></div>
      <div class="aurora-orb orb-3"></div>
    </div>

    <!-- Navigation Header -->
    <header class="landing-nav-bar">
      <div class="nav-brand-wrap" @click="goToPortal">
        <span class="brand-badge-pill">AGENT MESH & GRAPH RAG POWERED</span>
        <span class="brand-title-text">CinemaAgent</span>
      </div>

      <div class="nav-links-cluster">
        <button class="nav-glass-link" @click="goToPortal" id="nav-btn-portal">视听大厅</button>
        <button class="nav-glass-link" @click="goToCreator" id="nav-btn-creator">创作者中心</button>
        <button class="nav-glass-link" @click="goToAgentHub" id="nav-btn-agenthub">智能体战术大屏</button>
        <button v-if="isAdmin" class="nav-glass-link admin-highlight" @click="goToAdmin" id="nav-btn-admin">后台控制台</button>
        <button class="nav-cta-btn" @click="goToPortal" id="nav-btn-cta">立即入场体验</button>
      </div>
    </header>

    <!-- Main Hero Presentation -->
    <main class="landing-hero-content">
      <div class="hero-tag-badge">
        <span class="pulse-dot"></span>
        <span>工业级智能体影视协同与知识中台平台</span>
      </div>

      <h1 class="landing-headline">
        CinemaAgent 短剧视听新纪元<br />
        <span class="gradient-text">九大专家调度网关 · 工业级 Graph RAG 知识中台</span>
      </h1>

      <p class="landing-subtext">
        深度融合九大多模态专家智能体圆桌会话、Neo4j 实体关系图谱混合召回、全链路全用户全操作审计留痕、<br />
        16:9 与 9:16 原生流媒体及灵宠小茜交互伴读，赋能短剧生产、消费、审核与知识沉淀全生命周期。
      </p>

      <!-- Primary Action Buttons -->
      <div class="landing-actions-group">
        <button class="primary-apple-cta" id="btn-enter-portal" @click="goToPortal">
          <span>进入视听大厅</span>
          <svg viewBox="0 0 24 24" class="cta-arrow-svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </button>
        <button class="secondary-apple-cta" id="btn-enter-creator" @click="goToCreator">
          <span>创作者入驻 & 云盘管理</span>
        </button>
        <button class="secondary-apple-cta tactical-cta" id="btn-enter-agent-hub" @click="goToAgentHub">
          <span>探索智能体战术大屏</span>
        </button>
      </div>

      <!-- Section Title: Core Capabilities -->
      <div class="section-divider-title">
        <span class="divider-badge">CORE CAPABILITIES</span>
        <h2>六大工业级核心能力矩阵</h2>
        <p>从大模型编排到底层图存储，打造全链路高可用视听与知识底座</p>
      </div>

      <!-- 6-Feature Grid Cards -->
      <section class="landing-features-grid">
        <!-- Feature 1: Agent Mesh -->
        <div class="feature-glass-card">
          <div class="card-icon-wrap">
            <svg viewBox="0 0 24 24" class="feature-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
              <path d="M2 17l10 5 10-5"></path>
              <path d="M2 12l10 5 10-5"></path>
            </svg>
          </div>
          <div class="card-accent-tag">AGENT MESH & ROUNDTABLE</div>
          <h3>九大专家智能体协同网关</h3>
          <p>
            编剧、导演、知识中台、合规风控、宣发运营等九大多角色协同，圆桌多轮深度研讨，右侧交付物抽屉实时沉淀大纲、分镜脚本与宣发策略。
          </p>
          <div class="card-sub-pills">
            <span class="sub-pill">多角色圆桌会话</span>
            <span class="sub-pill">交付物工作台抽屉</span>
            <span class="sub-pill">历史会话动态回溯</span>
          </div>
        </div>

        <!-- Feature 2: Graph RAG -->
        <div class="feature-glass-card">
          <div class="card-icon-wrap">
            <svg viewBox="0 0 24 24" class="feature-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="18" cy="5" r="3"></circle>
              <circle cx="6" cy="12" r="3"></circle>
              <circle cx="18" cy="19" r="3"></circle>
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
            </svg>
          </div>
          <div class="card-accent-tag">MODULAR GRAPH RAG</div>
          <h3>工业级 Graph RAG 知识中台</h3>
          <p>
            人物实体三元组抽取并写入 Neo4j 关系图谱，时间轴防剧透门控，向量 + BM25 + Neo4j Cypher 三路混合召回、RRF 倒排融合与 Cross-Encoder 重排，内置 RAGAS 四维基准评测。
          </p>
          <div class="card-sub-pills">
            <span class="sub-pill">Neo4j 图谱三元组</span>
            <span class="sub-pill">时间轴防剧透召回</span>
            <span class="sub-pill">RAGAS 四维基准跑分</span>
          </div>
        </div>

        <!-- Feature 3: Audit Trail -->
        <div class="feature-glass-card">
          <div class="card-icon-wrap">
            <svg viewBox="0 0 24 24" class="feature-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
          </div>
          <div class="card-accent-tag">AUDIT OBSERVABILITY</div>
          <h3>全链路全用户全操作审计系统</h3>
          <p>
            鉴权流水、播放行为、智能体调用与管理操作毫秒级全链路留痕，支持多维复合过滤、操作分类、高可用分页与原始请求/响应 JSON 上下文深度追溯。
          </p>
          <div class="card-sub-pills">
            <span class="sub-pill">毫秒级操作溯源</span>
            <span class="sub-pill">原始 JSON 上下文抽屉</span>
            <span class="sub-pill">全角色操作审计</span>
          </div>
        </div>

        <!-- Feature 4: Dual Stream & Pet -->
        <div class="feature-glass-card">
          <div class="card-icon-wrap">
            <svg viewBox="0 0 24 24" class="feature-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="2" width="20" height="15" rx="2"></rect>
              <line x1="2" y1="20" x2="22" y2="20"></line>
            </svg>
          </div>
          <div class="card-accent-tag">DUAL-MODE STREAM & PET</div>
          <h3>16:9 / 9:16 双模流媒体 & 灵宠伴侣</h3>
          <p>
            9:16 沉浸竖屏抗挤压流式双层控制架构，4K 夸克/沃盘分片秒播；具备视听交互能力的桌面伴侣灵宠小茜，剧情伴读、高能解密与沉浸式陪伴。
          </p>
          <div class="card-sub-pills">
            <span class="sub-pill">9:16 竖屏抗挤压架构</span>
            <span class="sub-pill">灵宠小茜视听伴读</span>
            <span class="sub-pill">4K 原画流式切片</span>
          </div>
        </div>

        <!-- Feature 5: Cloud Driver & Coin -->
        <div class="feature-glass-card">
          <div class="card-icon-wrap">
            <svg viewBox="0 0 24 24" class="feature-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="9"></circle>
              <path d="M14.8 9A2 2 0 0 0 13 8h-2a2 2 0 0 0 0 4h2a2 2 0 0 1 0 4h-2a2 2 0 0 1-1.8-1"></path>
              <line x1="12" y1="6" x2="12" y2="8"></line>
              <line x1="12" y1="16" x2="12" y2="18"></line>
            </svg>
          </div>
          <div class="card-accent-tag">CLOUD STORAGE & COIN ECONOMY</div>
          <h3>云端网盘直驱与闭环金币微经济</h3>
          <p>
            夸克网盘与联通云盘直连 206 范围断点切片，零本地存储压力；每日签到领币、看广告激励、短剧投币打赏与全站热度值联动、VIP 会员兑换。
          </p>
          <div class="card-sub-pills">
            <span class="sub-pill">夸克/联通直连秒播</span>
            <span class="sub-pill">投币打赏热度联动</span>
            <span class="sub-pill">金币兑换 VIP 特权</span>
          </div>
        </div>

        <!-- Feature 6: Enterprise BI -->
        <div class="feature-glass-card">
          <div class="card-icon-wrap">
            <svg viewBox="0 0 24 24" class="feature-svg" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="20" x2="18" y2="10"></line>
              <line x1="12" y1="20" x2="12" y2="4"></line>
              <line x1="6" y1="20" x2="6" y2="14"></line>
            </svg>
          </div>
          <div class="card-accent-tag">ENTERPRISE BI DASHBOARD</div>
          <h3>企业级 BI 智能驾驶舱</h3>
          <p>
            全站视听流媒体、弹幕活跃度、评论互动、点赞投币、用户增长、智能体调用频次与 RAG 耗时监控的多维 ECharts 动态大屏，驱动数据化决策。
          </p>
          <div class="card-sub-pills">
            <span class="sub-pill">ECharts 多维时序看板</span>
            <span class="sub-pill">智能体调用频次分析</span>
            <span class="sub-pill">全链路审计透视</span>
          </div>
        </div>
      </section>

      <!-- Section Title: System Architecture -->
      <div class="section-divider-title">
        <span class="divider-badge">ARCHITECTURE STACK</span>
        <h2>工业级平台全景分层架构</h2>
        <p>高内聚、低耦合的模块化设计，支撑海量并发与复杂智能体协同</p>
      </div>

      <!-- Bento Grid Architecture Visualization -->
      <section class="architecture-bento-grid">
        <div class="bento-layer-card">
          <div class="layer-header">
            <span class="layer-tag">LAYER 4</span>
            <h4>多端应用呈现与交互层 (Presentation Tier)</h4>
          </div>
          <p class="layer-desc">原生 16:9 影院模式 · 9:16 移动竖屏沉浸控制 · 桌面灵宠小茜悬浮伴侣 · 管理端独立中台顶栏</p>
        </div>

        <div class="bento-layer-card">
          <div class="layer-header">
            <span class="layer-tag">LAYER 3</span>
            <h4>业务治理与金币微生态层 (Business & Economy Tier)</h4>
          </div>
          <p class="layer-desc">两级楼中楼评论树 · 短剧投币打赏与热度值算法 · 创作者云盘挂载 · 弹幕关键词合规机审治理</p>
        </div>

        <div class="bento-layer-card highlight-bento">
          <div class="layer-header">
            <span class="layer-tag">LAYER 2</span>
            <h4>智能体网关与 Graph RAG 知识中台 (Agent Mesh & Knowledge Tier)</h4>
          </div>
          <p class="layer-desc">九大多模态专家集群 · 多角色圆桌协同对话 · 时间轴防剧透三路混合召回 · Self-RAG 反思门控与 RAGAS 评测</p>
        </div>

        <div class="bento-layer-card">
          <div class="layer-header">
            <span class="layer-tag">LAYER 1</span>
            <h4>基础设施与混合持久化层 (Infrastructure & Storage Tier)</h4>
          </div>
          <p class="layer-desc">夸克/联通 206 范围断点切片 · Neo4j 实体关系图谱 · MySQL 全链路操作审计日志 · Ollama / MiMo 模型底座</p>
        </div>
      </section>

      <!-- Section Title: Role Ecosystem -->
      <div class="section-divider-title">
        <span class="divider-badge">ROLE ECOSYSTEM</span>
        <h2>四大多端角色流转闭环</h2>
        <p>普通观众、创作者、合规风控员与超级管理员各司其职、无缝流转</p>
      </div>

      <!-- User Role Architecture Walkthrough -->
      <section class="role-architecture-banner">
        <div class="role-card-item">
          <span class="role-chip user-chip">普通观众</span>
          <h4>沉浸追剧 & 灵宠伴读</h4>
          <p>4K 极速秒播短剧、实时弹幕点赞投币、唤醒灵宠小茜剧情解密，每日签到领取金币兑换 VIP 特权。</p>
        </div>
        <div class="role-card-connector">
          <svg viewBox="0 0 24 24" class="connector-svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </div>
        <div class="role-card-item highlight-card">
          <span class="role-chip creator-chip">认证创作者</span>
          <h4>创作者工作台 & 网盘映射</h4>
          <p>一键挂载夸克/联通云盘目录，自动化映射剧集资产并切片上架，直观监控短剧投币热度与用户互动。</p>
        </div>
        <div class="role-card-connector">
          <svg viewBox="0 0 24 24" class="connector-svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </div>
        <div class="role-card-item">
          <span class="role-chip reviewer-chip">合规审核员</span>
          <h4>弹幕治理与安全仲裁</h4>
          <p>全量弹幕明细检索、批量违规下架、关键词屏蔽库维护，以及智能体内容合规阻断结果在线仲裁。</p>
        </div>
        <div class="role-card-connector">
          <svg viewBox="0 0 24 24" class="connector-svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </div>
        <div class="role-card-item">
          <span class="role-chip admin-chip">超级管理员</span>
          <h4>全域控制与审计看板</h4>
          <p>九大智能体战术调度、全局大模型热重载、全链路全用户审计深度追溯，以及登录主页壁纸引擎可视化调优。</p>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="landing-footer">
      <div class="footer-left">
        <span class="footer-brand">CinemaAgent</span>
        <span class="footer-copy">© 2026 · 基于 Apple HIG 与工业级多智能体协同架构构建</span>
      </div>
      <div class="footer-right">
        <span class="status-indicator-pill">
          <span class="status-dot"></span>
          <span>SYSTEM READY · AGENT MESH ONLINE</span>
        </span>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const user = computed(() => {
  try {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
})

const isAdmin = computed(() => user.value?.role === 'ADMIN')

const goToPortal = () => {
  router.push('/')
}

const goToCreator = () => {
  router.push('/creator')
}

const goToAdmin = () => {
  router.push('/admin')
}

const goToAgentHub = () => {
  router.push('/admin?tab=agent-hub')
}
</script>

<style scoped>
.landing-page-container {
  min-height: 100vh;
  background-color: var(--bg-primary, #0d0e12);
  color: var(--text-primary, #f5f5f7);
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", sans-serif;
  position: relative;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}

/* Light Theme Variables */
[data-theme="light"] .landing-page-container {
  background-color: #f5f5f7;
  color: #1d1d1f;
}

/* Ambient Aurora Orbs */
.landing-ambient-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}

.aurora-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.28;
  animation: orb-drift 18s ease-in-out infinite alternate;
}

.orb-1 {
  width: 550px;
  height: 550px;
  background: radial-gradient(circle, #0071E3 0%, rgba(0, 113, 227, 0) 70%);
  top: -120px;
  left: 15%;
}

.orb-2 {
  width: 480px;
  height: 480px;
  background: radial-gradient(circle, #bf5af2 0%, rgba(191, 90, 242, 0) 70%);
  top: 150px;
  right: 10%;
  animation-duration: 22s;
  animation-delay: -5s;
}

.orb-3 {
  width: 520px;
  height: 520px;
  background: radial-gradient(circle, #30d158 0%, rgba(48, 209, 88, 0) 70%);
  bottom: 200px;
  left: 25%;
  animation-duration: 26s;
  animation-delay: -10s;
}

@keyframes orb-drift {
  0% { transform: translateY(0) scale(1); }
  50% { transform: translateY(40px) scale(1.08); }
  100% { transform: translateY(-30px) scale(0.95); }
}

/* Nav Bar */
.landing-nav-bar {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 48px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  background: rgba(13, 14, 18, 0.72);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

[data-theme="light"] .landing-nav-bar {
  background: rgba(245, 245, 247, 0.82);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.nav-brand-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.brand-badge-pill {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(0, 113, 227, 0.18);
  color: #2997ff;
  border: 1px solid rgba(0, 113, 227, 0.3);
}

.brand-title-text {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.nav-links-cluster {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-glass-link {
  background: transparent;
  border: 1px solid transparent;
  color: rgba(245, 245, 247, 0.78);
  padding: 7px 14px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

[data-theme="light"] .nav-glass-link {
  color: #48484a;
}

.nav-glass-link:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

[data-theme="light"] .nav-glass-link:hover {
  background: rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.1);
  color: #1d1d1f;
}

.nav-glass-link.admin-highlight {
  color: #ff9f0a;
  border-color: rgba(255, 159, 10, 0.25);
  background: rgba(255, 159, 10, 0.08);
}

.nav-cta-btn {
  background: #0071E3;
  color: #ffffff;
  border: none;
  padding: 8px 18px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 14px rgba(0, 113, 227, 0.35);
}

.nav-cta-btn:hover {
  background: #0077ED;
  transform: translateY(-1px);
}

/* Hero Section */
.landing-hero-content {
  position: relative;
  z-index: 5;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64px 24px 80px;
  max-width: 1240px;
  margin: 0 auto;
  text-align: center;
}

.hero-tag-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  font-size: 12px;
  font-weight: 600;
  color: #2997ff;
  margin-bottom: 24px;
}

[data-theme="light"] .hero-tag-badge {
  background: rgba(0, 113, 227, 0.08);
  border-color: rgba(0, 113, 227, 0.2);
  color: #0071e3;
}

.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #30d158;
  box-shadow: 0 0 8px #30d158;
  animation: pulse-glow 2s infinite;
}

@keyframes pulse-glow {
  0% { transform: scale(0.9); opacity: 0.8; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.8; }
}

.landing-headline {
  font-size: 46px;
  font-weight: 800;
  line-height: 1.18;
  letter-spacing: -0.03em;
  margin-bottom: 20px;
}

.gradient-text {
  background: linear-gradient(135deg, #2997ff 0%, #bf5af2 60%, #ff375f 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.landing-subtext {
  font-size: 16px;
  line-height: 1.6;
  color: rgba(245, 245, 247, 0.72);
  max-width: 820px;
  margin-bottom: 36px;
}

[data-theme="light"] .landing-subtext {
  color: #6e6e73;
}

.landing-actions-group {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 72px;
  flex-wrap: wrap;
  justify-content: center;
}

.primary-apple-cta {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 13px 28px;
  border-radius: 999px;
  background: #0071E3;
  color: #ffffff;
  font-size: 15px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 6px 20px rgba(0, 113, 227, 0.4);
}

.primary-apple-cta:hover {
  background: #0077ED;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 113, 227, 0.5);
}

.cta-arrow-svg {
  width: 16px;
  height: 16px;
  transition: transform 0.2s ease;
}

.primary-apple-cta:hover .cta-arrow-svg {
  transform: translateX(3px);
}

.secondary-apple-cta {
  padding: 13px 26px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: #f5f5f7;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

[data-theme="light"] .secondary-apple-cta {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.14);
  color: #1d1d1f;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.secondary-apple-cta:hover {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.28);
  transform: translateY(-1px);
}

[data-theme="light"] .secondary-apple-cta:hover {
  background: #fbfbfd;
  border-color: rgba(0, 0, 0, 0.24);
}

.secondary-apple-cta.tactical-cta {
  background: rgba(191, 90, 242, 0.12);
  border-color: rgba(191, 90, 242, 0.3);
  color: #bf5af2;
}

.secondary-apple-cta.tactical-cta:hover {
  background: rgba(191, 90, 242, 0.2);
}

/* Section Title Divider */
.section-divider-title {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 36px;
}

.divider-badge {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #2997ff;
  margin-bottom: 8px;
}

.section-divider-title h2 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: -0.02em;
}

.section-divider-title p {
  font-size: 14px;
  color: rgba(245, 245, 247, 0.65);
}

[data-theme="light"] .section-divider-title p {
  color: #86868b;
}

/* 6-Feature Grid */
.landing-features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  width: 100%;
  margin-bottom: 72px;
  text-align: left;
}

.feature-glass-card {
  padding: 28px 24px;
  border-radius: 20px;
  background: rgba(28, 28, 30, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  display: flex;
  flex-direction: column;
  transition: all 0.25s ease;
}

[data-theme="light"] .feature-glass-card {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

.feature-glass-card:hover {
  transform: translateY(-3px);
  border-color: rgba(0, 113, 227, 0.4);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
}

.card-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(0, 113, 227, 0.12);
  border: 1px solid rgba(0, 113, 227, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2997ff;
  margin-bottom: 16px;
}

.feature-svg {
  width: 22px;
  height: 22px;
}

.card-accent-tag {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #2997ff;
  margin-bottom: 6px;
}

.feature-glass-card h3 {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 10px;
  color: #f5f5f7;
}

[data-theme="light"] .feature-glass-card h3 {
  color: #1d1d1f;
}

.feature-glass-card p {
  font-size: 13px;
  line-height: 1.6;
  color: rgba(245, 245, 247, 0.7);
  flex-grow: 1;
  margin-bottom: 16px;
}

[data-theme="light"] .feature-glass-card p {
  color: #6e6e73;
}

.card-sub-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.sub-pill {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(245, 245, 247, 0.8);
}

[data-theme="light"] .sub-pill {
  background: #f5f5f7;
  border-color: #e5e5ea;
  color: #48484a;
}

/* Architecture Bento Grid */
.architecture-bento-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 100%;
  margin-bottom: 72px;
  text-align: left;
}

.bento-layer-card {
  padding: 20px 24px;
  border-radius: 16px;
  background: rgba(28, 28, 30, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(16px);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

[data-theme="light"] .bento-layer-card {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.bento-layer-card.highlight-bento {
  border-color: rgba(0, 113, 227, 0.4);
  background: rgba(0, 113, 227, 0.08);
}

.layer-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.layer-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.08);
  color: #2997ff;
}

.layer-header h4 {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
}

.layer-desc {
  font-size: 13px;
  color: rgba(245, 245, 247, 0.68);
  margin: 0;
}

[data-theme="light"] .layer-desc {
  color: #6e6e73;
}

/* Role Banner */
.role-architecture-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  margin-bottom: 32px;
}

.role-card-item {
  flex: 1;
  padding: 22px 18px;
  border-radius: 16px;
  background: rgba(28, 28, 30, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  text-align: left;
  backdrop-filter: blur(16px);
}

[data-theme="light"] .role-card-item {
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.role-card-item.highlight-card {
  border-color: rgba(48, 209, 88, 0.35);
  background: rgba(48, 209, 88, 0.06);
}

.role-chip {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  margin-bottom: 10px;
}

.user-chip { background: rgba(0, 113, 227, 0.2); color: #2997ff; }
.creator-chip { background: rgba(48, 209, 88, 0.2); color: #30d158; }
.reviewer-chip { background: rgba(255, 159, 10, 0.2); color: #ff9f0a; }
.admin-chip { background: rgba(191, 90, 242, 0.2); color: #bf5af2; }

.role-card-item h4 {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 6px 0;
}

.role-card-item p {
  font-size: 12px;
  line-height: 1.5;
  color: rgba(245, 245, 247, 0.65);
  margin: 0;
}

[data-theme="light"] .role-card-item p {
  color: #6e6e73;
}

.role-card-connector {
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.2);
}

[data-theme="light"] .role-card-connector {
  color: rgba(0, 0, 0, 0.2);
}

.connector-svg {
  width: 18px;
  height: 18px;
}

/* Footer */
.landing-footer {
  position: relative;
  z-index: 5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 48px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(13, 14, 18, 0.85);
  font-size: 12px;
}

[data-theme="light"] .landing-footer {
  background: #f5f5f7;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.footer-brand {
  font-weight: 700;
  color: #2997ff;
}

.footer-copy {
  color: rgba(245, 245, 247, 0.5);
}

[data-theme="light"] .footer-copy {
  color: #86868b;
}

.status-indicator-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(48, 209, 88, 0.12);
  border: 1px solid rgba(48, 209, 88, 0.25);
  color: #30d158;
  font-weight: 600;
  font-size: 10px;
  letter-spacing: 0.04em;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #30d158;
}

/* Responsive */
@media (max-width: 1024px) {
  .landing-features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .role-architecture-banner {
    flex-direction: column;
  }
  .role-card-connector {
    transform: rotate(90deg);
    margin: 4px 0;
  }
}

@media (max-width: 640px) {
  .landing-features-grid {
    grid-template-columns: 1fr;
  }
  .landing-headline {
    font-size: 32px;
  }
  .landing-nav-bar {
    padding: 12px 16px;
  }
}
</style>
