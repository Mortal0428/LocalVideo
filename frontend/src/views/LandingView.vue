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
        <span class="brand-badge-pill">QUARK & WOPAN POWERED</span>
        <span class="brand-title-text">CinemaAgent</span>
      </div>

      <div class="nav-links-cluster">
        <button class="nav-glass-link" @click="goToPortal">视听大厅</button>
        <button class="nav-glass-link" @click="goToCreator">创作者中心</button>
        <button v-if="isAdmin" class="nav-glass-link admin-highlight" @click="goToAdmin">后台管理</button>
        <button class="nav-cta-btn" @click="goToPortal">立即入场体验</button>
      </div>
    </header>

    <!-- Main Hero Presentation -->
    <main class="landing-hero-content">
      <div class="hero-tag-badge">
        <span class="pulse-dot"></span>
        <span>新一代短剧视听与多模态伴读平台</span>
      </div>

      <h1 class="landing-headline">
        沉浸短剧视听<br />
        <span class="gradient-text">网盘原画直驱 · AI剧情伴读</span>
      </h1>

      <p class="landing-subtext">
        集成夸克网盘与联通沃盘原生驱动，零本地存储压力的 4K 分片秒开。<br />
        自研横竖屏双模态自由热切换与本地 Ollama / 小米 MiMo 智能体剧情高能伴读。
      </p>

      <!-- Primary Action Buttons -->
      <div class="landing-actions-group">
        <button class="primary-apple-cta" id="btn-enter-portal" @click="goToPortal">
          <span>进入视听大厅</span>
          <span class="arrow-glyph">→</span>
        </button>
        <button class="secondary-apple-cta" id="btn-enter-creator" @click="goToCreator">
          <span>创作者入驻 & 云盘管理</span>
        </button>
      </div>

      <!-- Feature Grid Cards -->
      <section class="landing-features-grid">
        <div class="feature-glass-card">
          <div class="card-accent-tag">STORAGE DRIVER</div>
          <h3>夸克 / 沃盘 原生云直存</h3>
          <p>
            支持夸克网盘与联通云盘直连，创作者一键新建网盘剧集文件夹并极速上传，用户享受 HTTP 206 原画分片流式秒播。
          </p>
        </div>

        <div class="feature-glass-card">
          <div class="card-accent-tag">DUAL-MODE PLAYER</div>
          <h3>16:9 与 9:16 无损双模态</h3>
          <p>
            既有大屏极简宽屏影院的恢弘质感，又有一键平滑过渡至 9:16 移动端沉浸胶囊，切换时音视频零卡顿、弹幕不断流。
          </p>
        </div>

        <div class="feature-glass-card">
          <div class="card-accent-tag">AI COMPANION RAG</div>
          <h3>多引擎时间轴伴读智能体</h3>
          <p>
            自由探测本地 Ollama (Qwen/DeepSeek/BGE) 与小米云端 MiMo 大模型，高能看点秒级直达，追剧答疑无微不至。
          </p>
        </div>
      </section>

      <!-- User Role Architecture Walkthrough -->
      <section class="role-architecture-banner">
        <div class="role-card-item">
          <span class="role-chip user-chip">普通用户</span>
          <h4>沉浸追剧 & 弹幕互动</h4>
          <p>免登探索海量短剧，随时发送分片实时弹幕，点击高能看点精准跳转。</p>
        </div>
        <div class="role-card-arrow">➜</div>
        <div class="role-card-item highlight-card">
          <span class="role-chip creator-chip">创作者身份</span>
          <h4>创作者工作台 & 云盘上传</h4>
          <p>任意用户一键申请成为创作者，解锁夸克云盘树形目录浏览、新建文件夹与分片转码上架。</p>
        </div>
        <div class="role-card-arrow">➜</div>
        <div class="role-card-item">
          <span class="role-chip admin-chip">平台管理员</span>
          <h4>全量用户与风控中台</h4>
          <p>统筹全站用户状态、封禁违规账号、审核创作者资质与流媒体健康度监控。</p>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="landing-footer">
      <span>CinemaAgent © 2026 · 基于 Apple HIG 与 Bilibili 美学规范构建</span>
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
</script>

<style scoped>
.landing-page-container {
  min-height: 100vh;
  background-color: #f5f5f7;
  color: #1d1d1f;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", sans-serif;
  position: relative;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}

/* Ambient Aurora Orbs */
.landing-ambient-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.aurora-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.55;
  animation: floatOrb 18s ease-in-out infinite alternate;
}

.orb-1 {
  width: 55vw;
  height: 55vw;
  top: -15vw;
  left: -10vw;
  background: radial-gradient(circle, rgba(162, 210, 255, 0.45) 0%, rgba(162, 210, 255, 0) 70%);
}

.orb-2 {
  width: 50vw;
  height: 50vw;
  top: 15vh;
  right: -10vw;
  background: radial-gradient(circle, rgba(200, 180, 255, 0.4) 0%, rgba(200, 180, 255, 0) 70%);
  animation-duration: 22s;
}

.orb-3 {
  width: 45vw;
  height: 45vw;
  bottom: -10vh;
  left: 25vw;
  background: radial-gradient(circle, rgba(251, 114, 153, 0.25) 0%, rgba(251, 114, 153, 0) 70%);
  animation-duration: 26s;
}

@keyframes floatOrb {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(25px, 35px) scale(1.05); }
  100% { transform: translate(-20px, 15px) scale(0.96); }
}

/* Navigation */
.landing-nav-bar {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 48px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(24px) saturate(180%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.8);
}

.nav-brand-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.brand-badge-pill {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(0, 113, 227, 0.1);
  color: #0071e3;
  border: 1px solid rgba(0, 113, 227, 0.2);
}

.brand-title-text {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #18191c;
}

.nav-links-cluster {
  display: flex;
  align-items: center;
  gap: 14px;
}

.nav-glass-link {
  background: transparent;
  border: none;
  font-size: 14px;
  font-weight: 500;
  color: #505050;
  padding: 8px 14px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.25, 1, 0.5, 1);
}

.nav-glass-link:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #18191c;
}

.nav-glass-link.admin-highlight {
  color: #8b5cf6;
  font-weight: 600;
}

.nav-cta-btn {
  background: #0071e3;
  color: #ffffff;
  border: none;
  font-size: 13px;
  font-weight: 600;
  padding: 8px 18px;
  border-radius: 999px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.25);
  transition: all 0.25s cubic-bezier(0.25, 1, 0.5, 1);
}

.nav-cta-btn:hover {
  background: #0077ed;
  transform: scale(1.02);
  box-shadow: 0 6px 16px rgba(0, 113, 227, 0.35);
}

/* Main Content */
.landing-hero-content {
  position: relative;
  z-index: 5;
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 60px 32px 80px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-tag-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  backdrop-filter: blur(12px);
  padding: 6px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: #333336;
  margin-bottom: 24px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #34c759;
  box-shadow: 0 0 8px rgba(52, 199, 89, 0.7);
}

.landing-headline {
  font-size: 54px;
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.03em;
  color: #18191c;
  margin: 0 0 20px;
}

.gradient-text {
  background: linear-gradient(135deg, #0071e3 0%, #8b5cf6 50%, #fb7299 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.landing-subtext {
  font-size: 18px;
  line-height: 1.6;
  color: #616166;
  max-width: 720px;
  margin: 0 auto 36px;
}

/* Buttons */
.landing-actions-group {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 64px;
}

.primary-apple-cta {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: #0071e3;
  color: #ffffff;
  border: none;
  font-size: 16px;
  font-weight: 600;
  padding: 14px 32px;
  border-radius: 999px;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(0, 113, 227, 0.3);
  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
}

.primary-apple-cta:hover {
  background: #0077ed;
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 10px 24px rgba(0, 113, 227, 0.4);
}

.secondary-apple-cta {
  background: #e5e5ea;
  color: #1d1d1f;
  border: none;
  font-size: 16px;
  font-weight: 600;
  padding: 14px 28px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
}

.secondary-apple-cta:hover {
  background: #d8d8de;
  transform: translateY(-2px);
}

/* Features Grid */
.landing-features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  width: 100%;
  margin-bottom: 56px;
  text-align: left;
}

.feature-glass-card {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(28px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.85);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
  border-radius: 24px;
  padding: 32px 28px;
  transition: all 0.35s cubic-bezier(0.25, 1, 0.5, 1);
}

.feature-glass-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.08);
}

.card-accent-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #0071e3;
  margin-bottom: 12px;
}

.feature-glass-card h3 {
  font-size: 20px;
  font-weight: 700;
  color: #18191c;
  margin: 0 0 12px;
}

.feature-glass-card p {
  font-size: 14px;
  line-height: 1.6;
  color: #6e6e73;
  margin: 0;
}

/* Role Architecture Banner */
.role-architecture-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  width: 100%;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 24px;
  padding: 32px 24px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.03);
}

.role-card-item {
  flex: 1;
  text-align: left;
  padding: 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.6);
}

.role-card-item.highlight-card {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 16px rgba(0, 113, 227, 0.12);
  border-color: rgba(0, 113, 227, 0.2);
}

.role-chip {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
  margin-bottom: 8px;
}

.user-chip { background: #e5e5ea; color: #1d1d1f; }
.creator-chip { background: rgba(0, 113, 227, 0.12); color: #0071e3; }
.admin-chip { background: rgba(139, 92, 246, 0.12); color: #8b5cf6; }

.role-card-item h4 {
  font-size: 16px;
  font-weight: 700;
  color: #18191c;
  margin: 0 0 6px;
}

.role-card-item p {
  font-size: 13px;
  line-height: 1.5;
  color: #6e6e73;
  margin: 0;
}

.role-card-arrow {
  color: #a1a1a6;
  font-size: 20px;
}

/* Footer */
.landing-footer {
  text-align: center;
  padding: 24px;
  font-size: 13px;
  color: #86868b;
  position: relative;
  z-index: 5;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

@media (max-width: 900px) {
  .landing-headline { font-size: 38px; }
  .landing-features-grid { grid-template-columns: 1fr; }
  .role-architecture-banner { flex-direction: column; }
  .role-card-arrow { transform: rotate(90deg); }
}
</style>
