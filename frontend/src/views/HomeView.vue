<template>
  <div class="apple-bento-portal" id="bili-portal-page">
    <!-- Top Global Apple HIG Header -->
    <GlobalHeader @search="handleHeaderSearch" @userChanged="handleUserChanged" />

    <!-- Centered Big Type Hero Header (Matching Reference Image) -->
    <div class="portal-hero-section" id="bili-banner-hero">
      <div class="hero-inner-container">
        <div class="hero-pill-badge">
          <span class="badge-dot"></span>
          <span>夸克网盘原生直连 · 极速短剧流式分发</span>
        </div>
        <h1 class="hero-big-title">CinemaAgent</h1>
        <p class="hero-sub-title">多媒体互动视听与短剧伴读平台</p>
        
        <!-- Category Filter Pills (Apple Segmented Style) -->
        <nav class="category-pills-bar" id="channel-bar">
          <button
            v-for="cat in categories"
            :key="cat.id"
            class="cat-pill-btn"
            :class="{ active: currentCategory === cat.id }"
            @click="selectCategory(cat.id)"
            :id="'btn-cat-' + cat.id"
          >
            {{ cat.name }}
          </button>
        </nav>
      </div>
    </div>

    <!-- Main Content Container (Max width 1120px Centered) -->
    <main class="portal-main-wrap">
      <!-- Search indicator row if search is active -->
      <div v-if="searchQuery" class="search-feedback-banner">
        <span class="feedback-text">当前检索关键词：<strong>"{{ searchQuery }}"</strong></span>
        <button class="clear-search-btn" @click="clearSearch">清除搜索</button>
      </div>

      <!-- Spotlight Hero Bento: 2x2 Feature Bento Card (Carousel Showcase) -->
      <section 
        v-if="!searchQuery && activeCarousel" 
        class="spotlight-bento-card" 
        id="carousel-banner-box" 
        @click="goToVideo(activeCarousel.video_id)"
        @mouseenter="pauseCarousel"
        @mouseleave="startCarousel"
      >
        <div class="spotlight-cover-side" :style="{ backgroundImage: `url(${activeCarousel.cover_url})` }">
          <div class="spotlight-cover-scrim">
            <span class="spotlight-badge">{{ activeCarousel.tag }}</span>
            <div class="spotlight-stats">
              <span>▶ {{ activeCarousel.play_count_str || '超清直连' }}</span>
              <span>💬 {{ activeCarousel.danmaku_count_str || '互动弹幕' }}</span>
            </div>
          </div>
          <!-- Left and Right arrows -->
          <button class="carousel-arrow-btn prev-btn" @click.stop="prevCarousel" title="上一张">❮</button>
          <button class="carousel-arrow-btn next-btn" @click.stop="nextCarousel" title="下一张">❯</button>
        </div>
        <div class="spotlight-info-side">
          <div class="spotlight-header-row">
            <span class="spotlight-tag-pill">HOT PICK</span>
            <div>
              <span class="spotlight-topic-tag">今日焦点推荐</span>
              <h2 class="spotlight-title">{{ activeCarousel.title }}</h2>
            </div>
          </div>
          <p class="spotlight-desc">{{ activeCarousel.subtitle }}</p>

          <div class="spotlight-actions-area">
            <div class="action-item-row">
              <span class="action-label">DUAL-MODE</span>
              <button class="apple-primary-pill" @click.stop="goToVideo(activeCarousel.video_id)">
                <span>▶ 立即播放 (16:9 / 9:16)</span>
              </button>
            </div>
            <div class="action-item-row">
              <span class="action-label">HIGHLIGHTS</span>
              <button class="apple-secondary-pill" @click.stop="goToVideo(activeCarousel.video_id)">
                <span>🎬 高能瞬间与看点</span>
              </button>
            </div>
          </div>

          <!-- Carousel dots for switcher -->
          <div class="carousel-dots-row">
            <span
              v-for="(c, idx) in carousels"
              :key="c.id"
              class="carousel-dot"
              :class="{ active: currentCarouselIdx === idx }"
              @click.stop="currentCarouselIdx = idx"
            ></span>
          </div>
        </div>
      </section>

      <!-- Section Title: Short Drama Bento Grid -->
      <div class="section-title-bar">
        <div class="title-left">
          <h3 class="section-heading">精选剧集展架</h3>
          <span class="section-subtext">全量适配 16:9 宽屏影院与 9:16 移动端双模式播放</span>
        </div>
        <span class="total-badge">共 {{ filteredVideos.length }} 部短剧</span>
      </div>

      <!-- Bento Grid (Fluid Auto-fill Bilibili Layout) -->
      <section class="bento-cards-grid">
        <article
          v-for="v in filteredVideos"
          :key="v.id"
          class="bento-card bili-video-card"
          @click="openDramaDetail(v)"
          @mouseenter="onCardMouseEnter(v)"
          @mouseleave="onCardMouseLeave(v)"
          :id="'video-card-' + v.id"
        >
          <!-- 16:9 Card Cover Image Thumbnail at Top -->
          <div class="card-thumbnail-box" :style="{ backgroundImage: `url(${getCardActiveCover(v)})` }">
            <div v-if="v.extra_images && v.extra_images.length > 1" class="multi-poster-badge" title="多剧照动态轮播">
              <el-icon :size="12"><Picture /></el-icon>
              <span>{{ (hoveredCardImages[v.id] || 0) + 1 }}/{{ v.extra_images.length }} 剧照</span>
            </div>
            <div class="thumbnail-overlay-scrim">
              <span class="duration-badge">{{ v.duration_str || '02:30' }}</span>
              <div class="thumb-stats">
                <span>▶ {{ v.play_count_str || '10.5万' }}</span>
                <span>💬 {{ v.danmaku_count_str || '820' }}</span>
              </div>
            </div>
          </div>

          <!-- Card Content Body Below Thumbnail -->
          <div class="card-body-wrap">
            <h4 class="card-title" :title="v.title">{{ v.title }}</h4>
            <div class="card-meta-row">
              <span class="card-category-pill">{{ v.category || '短剧精选' }}</span>
              <span class="card-episodes-tag">全 {{ v.episodes_count || 1 }} 集</span>
            </div>
            <p class="card-description-text">{{ v.description }}</p>

            <div class="card-actions-dock">
              <button class="bili-play-pill-btn" @click.stop="openDramaDetail(v)">
                <span>▶ 剧集详情 / 去观看</span>
              </button>
            </div>
          </div>
        </article>
      </section>

      <!-- Empty state if search has no results -->
      <div v-if="filteredVideos.length === 0" class="empty-results-box">
        <div class="empty-icon">🔍</div>
        <h4>未找到与 "{{ searchQuery }}" 匹配的短剧</h4>
        <p>请尝试搜索其他关键词，或点击“清除搜索”返回全部列表。</p>
        <button class="apple-secondary-pill" @click="clearSearch">清除搜索</button>
      </div>

      <!-- Platform Technology Highlights Bento (3-Card Feature Row) -->
      <section class="platform-features-grid">
        <div class="feature-bento-card">
          <div class="feature-icon-box blue-theme">
            <svg class="feat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
              <path d="m13 11-4 6h6l-4 6"/>
            </svg>
          </div>
          <h4 class="feature-title">夸克网盘直连流式点播</h4>
          <p class="feature-desc">OpenList 原生 REST/WebDAV 网关直连，HTTP 206 分片流式转发，超清 4K 秒开无缓冲拖拽。</p>
          <div class="feature-foot-tag">SPEED STREAMING</div>
        </div>

        <div class="feature-bento-card">
          <div class="feature-icon-box purple-theme">
            <svg class="feat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect width="18" height="18" x="3" y="3" rx="2"/>
              <path d="m9 8 7 4-7 4V8Z"/>
              <path d="M3 9h18"/>
            </svg>
          </div>
          <h4 class="feature-title">时间轴切片高能索引</h4>
          <p class="feature-desc">全量解析短剧关键剧情节点，发光时间戳按钮秒级跳转高能反转名场面。</p>
          <div class="feature-foot-tag">TIMELINE INDEX</div>
        </div>

        <div class="feature-bento-card">
          <div class="feature-icon-box rose-theme">
            <svg class="feat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
          </div>
          <h4 class="feature-title">毫秒级实时弹幕风控</h4>
          <p class="feature-desc">WebSocket 4 轨道高并发实时分发，DFA 算法毫秒阻断敏感违规词并接入机审工作台。</p>
          <div class="feature-foot-tag">SAFETY CONTROL</div>
        </div>
      </section>

      <!-- Apple Style Footer Resources Section (Matching Reference Image) -->
      <footer class="portal-footer-section">
        <div class="footer-resources-label">RESOURCES</div>
        <div class="footer-links-row">
          <span class="footer-link">中国联通沃盘</span>
          <span class="footer-dot">·</span>
          <span class="footer-link">OpenList 网关</span>
          <span class="footer-dot">·</span>
          <span class="footer-link">FastAPI 异步基座</span>
          <span class="footer-dot">·</span>
          <span class="footer-link">Vue 3 + Vite</span>
          <span class="footer-dot">·</span>
          <span class="footer-link">本地大模型引擎</span>
        </div>
        <p class="footer-copyright">CinemaAgent Platform © 2026. All Rights Reserved. Designed with Apple Human Interface Guidelines.</p>
      </footer>

      <!-- Apple HIG Drama Detail Modal -->
      <el-dialog
        v-model="dramaDetailModalVisible"
        :show-close="true"
        width="660px"
        class="apple-drama-modal"
        destroy-on-close
        align-center
      >
        <template #header>
          <div class="modal-apple-header">
            <span class="modal-apple-badge">短剧官方档案与剧情介绍</span>
            <span class="modal-apple-sub">OpenList 原生直连 · RAG 知识库已装配</span>
          </div>
        </template>
        
        <div v-if="selectedDrama" class="drama-detail-modal-body">
          <!-- 16:9 画报预览区 -->
          <div class="modal-poster-banner" :style="{ backgroundImage: `url(${modalActivePoster})` }">
            <div class="modal-poster-scrim">
              <span class="modal-category-tag">{{ selectedDrama.category || '微短剧' }}</span>
              <span class="modal-episodes-tag">全 {{ selectedDrama.episodes_count || 1 }} 集</span>
            </div>
          </div>

          <!-- 多剧照画廊缩略图切换 -->
          <div v-if="selectedDrama.extra_images && selectedDrama.extra_images.length > 1" class="modal-gallery-strip">
            <div
              v-for="(imgUrl, pIdx) in selectedDrama.extra_images"
              :key="pIdx"
              class="modal-gallery-thumb"
              :class="{ active: selectedPosterIdx === pIdx }"
              :style="{ backgroundImage: `url(${imgUrl})` }"
              @click="selectedPosterIdx = pIdx"
            ></div>
          </div>

          <!-- 剧名与元数据 -->
          <div class="modal-title-row">
            <h3 class="modal-drama-title">{{ selectedDrama.title }}</h3>
            <div class="modal-stats-badges">
              <span>▶ {{ selectedDrama.play_count_str || '10.5万次播放' }}</span>
              <span>💬 {{ selectedDrama.danmaku_count_str || '820条弹幕' }}</span>
            </div>
          </div>

          <!-- 剧情梗概与知识库沉淀 -->
          <div class="modal-synopsis-card">
            <div class="synopsis-label-row">
              <span class="synopsis-icon">📖</span>
              <span class="synopsis-label">剧情梗概 & 设定背景</span>
              <span class="rag-ready-pill">RAG 剧情伴读已就绪</span>
            </div>
            <p class="synopsis-content-text">{{ selectedDrama.description }}</p>
          </div>

          <!-- 底部行动条 -->
          <div class="modal-actions-bar">
            <button class="apple-modal-cancel-btn" @click="dramaDetailModalVisible = false">
              稍后再看
            </button>
            <button class="apple-modal-watch-btn" @click="startWatching">
              <span>▶ 立即去观看 (进入影院)</span>
            </button>
          </div>
        </div>
      </el-dialog>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Picture } from '@element-plus/icons-vue'
import GlobalHeader from '../components/GlobalHeader.vue'
import { api } from '../api/client'
import { videoApi, type VideoItem, type VideoAlbum } from '../api/video'
import type { UserProfile } from '../api/auth'

const router = useRouter()

const searchQuery = ref('')
const currentCategory = ref('all')
const currentUser = ref<UserProfile | null>(null)
const currentCarouselIdx = ref(0)
const videos = ref<VideoItem[]>([])
let carouselTimer: any = null

const hoveredCardImages = ref<Record<string, number>>({})
let cardHoverIntervals: Record<string, any> = {}

// Apple HIG Drama Detail Modal State
const dramaDetailModalVisible = ref(false)
const selectedDrama = ref<any>(null)
const selectedPosterIdx = ref(0)

const modalActivePoster = computed(() => {
  if (!selectedDrama.value) return ''
  if (selectedDrama.value.extra_images && selectedDrama.value.extra_images.length > 0) {
    return selectedDrama.value.extra_images[selectedPosterIdx.value] || selectedDrama.value.cover_url
  }
  return selectedDrama.value.cover_url
})

function openDramaDetail(video: any) {
  selectedDrama.value = video
  selectedPosterIdx.value = 0
  dramaDetailModalVisible.value = true
}

function startWatching() {
  if (selectedDrama.value) {
    const id = selectedDrama.value.id
    dramaDetailModalVisible.value = false
    goToVideo(id)
  }
}

function onCardMouseEnter(video: any) {
  if (video.extra_images && video.extra_images.length > 1) {
    if (!hoveredCardImages.value[video.id]) {
      hoveredCardImages.value[video.id] = 0
    }
    if (cardHoverIntervals[video.id]) clearInterval(cardHoverIntervals[video.id])
    cardHoverIntervals[video.id] = setInterval(() => {
      const cur = hoveredCardImages.value[video.id] || 0
      hoveredCardImages.value[video.id] = (cur + 1) % video.extra_images.length
    }, 1200)
  }
}

function onCardMouseLeave(video: any) {
  if (cardHoverIntervals[video.id]) {
    clearInterval(cardHoverIntervals[video.id])
    delete cardHoverIntervals[video.id]
  }
  hoveredCardImages.value[video.id] = 0
}

function getCardActiveCover(video: any) {
  if (video.extra_images && video.extra_images.length > 1) {
    const idx = hoveredCardImages.value[video.id] || 0
    return video.extra_images[idx] || video.cover_url
  }
  return video.cover_url
}

const carouselDuration = ref(5000)

function startCarousel() {
  stopCarousel()
  const delay = (activeCarousel.value?.duration_seconds ? activeCarousel.value.duration_seconds * 1000 : carouselDuration.value) || 5000
  carouselTimer = setInterval(() => {
    if (carousels.value.length > 0) {
      currentCarouselIdx.value = (currentCarouselIdx.value + 1) % carousels.value.length
    }
  }, delay)
}

function stopCarousel() {
  if (carouselTimer) {
    clearInterval(carouselTimer)
    carouselTimer = null
  }
}

function pauseCarousel() {
  stopCarousel()
}

function nextCarousel() {
  if (carousels.value.length > 0) {
    currentCarouselIdx.value = (currentCarouselIdx.value + 1) % carousels.value.length
  }
}

function prevCarousel() {
  if (carousels.value.length > 0) {
    currentCarouselIdx.value = (currentCarouselIdx.value - 1 + carousels.value.length) % carousels.value.length
  }
}

const categories = ref([
  { id: 'all', name: '全部' },
  { id: 'hot', name: '🔥 热门' },
  { id: 'short-drama', name: '微短剧' },
  { id: 'reversal', name: '逆袭爽剧' },
  { id: 'eighties', name: '年代逆袭' },
  { id: 'anime', name: '动漫番剧' },
  { id: 'tech-ai', name: '科技AI' },
  { id: 'soundtrack', name: '影视原声' }
])

interface CarouselItem {
  id: string | number
  title: string
  subtitle?: string
  tag?: string
  cover_url: string
  video_id?: string
  duration_seconds?: number
  play_count_str?: string
  danmaku_count_str?: string
}

// Carousels for top showcase
const carousels = ref<CarouselItem[]>([
  {
    id: 1,
    title: '【乘风2026】绝美舞台合唱瞬间，每一帧都是视觉盛宴',
    subtitle: '中国联通沃盘超清原画直连，支持 16:9 极简影院与 9:16 沉浸短剧模式无损自由切换。',
    tag: '本周爆款榜首',
    cover_url: 'https://images.unsplash.com/photo-1518173946687-a4c8a383392e?w=1280&q=80',
    video_id: '03d2e4bb-1bd4-4f93-bfec-a4d4a4f28e5b',
    duration_seconds: 5,
    play_count_str: '28.5万次播放',
    danmaku_count_str: '1,240条弹幕'
  },
  {
    id: 2,
    title: '【战神归来】三年隐忍，今日十万将士恭迎龙王！',
    subtitle: '全网热播百亿播放神剧，高能打脸镜头 AI 秒级锁定。',
    tag: '热血逆袭',
    cover_url: 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=1280&q=80',
    video_id: '03d2e4bb-1bd4-4f93-bfec-a4d4a4f28e5b',
    duration_seconds: 5,
    play_count_str: '19.8万次播放',
    danmaku_count_str: '986条弹幕'
  }
])

const activeCarousel = computed(() => {
  if (carousels.value.length === 0) return null
  return carousels.value[currentCarouselIdx.value % carousels.value.length]
})

// Mock fallback videos with diverse categories
const mockVideos: VideoItem[] = [
  {
    id: '03d2e4bb-1bd4-4f93-bfec-a4d4a4f28e5b',
    title: '【乘风2026】绝美舞台合唱瞬间，每一帧都是视觉盛宴',
    category: '都市逆袭',
    description: '音乐与视觉的双重共鸣，AI 伴读实时解析歌曲编曲意境与主创背后的感人故事。',
    cover_url: 'https://images.unsplash.com/photo-1518173946687-a4c8a383392e?w=800&q=80',
    episodes_count: 3,
    duration_str: '02:45',
    play_count_str: '45.2万',
    danmaku_count_str: '3120',
    creator_name: '星芒厂牌',
    creator_avatar: 'https://api.dicebear.com/7.x/bottts/svg?seed=creator'
  },
  {
    id: '15767eb0-dcb7-4581-bcfa-1f19f20e401f',
    title: '【战神归来】第一集：赘婿受尽白眼，一朝龙王令出',
    category: '战神爽剧',
    description: '开局被丈母娘逐出家族，一通神秘跨国加密电话打破平静，龙王身份呼之欲出。',
    cover_url: 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=800&q=80',
    episodes_count: 12,
    duration_str: '01:58',
    play_count_str: '128.6万',
    danmaku_count_str: '9420',
    creator_name: '战神短剧工作室',
    creator_avatar: 'https://api.dicebear.com/7.x/bottts/svg?seed=god'
  },
  {
    id: '3b92f72a-1123-4819-bf39-2a90184e9123',
    title: '【偏偏宠爱】千亿总裁的假结婚甜心妻子日常',
    category: '现代甜宠',
    description: '契约结婚第一天，高冷禁欲系顾总把民政局红本放在保险箱，眼神却温柔入水。',
    cover_url: 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800&q=80',
    episodes_count: 24,
    duration_str: '02:15',
    play_count_str: '89.4万',
    danmaku_count_str: '6310',
    creator_name: '甜莓影视',
    creator_avatar: 'https://api.dicebear.com/7.x/bottts/svg?seed=sweet'
  },
  {
    id: '4c81a91e-5591-4920-a192-38192a019482',
    title: '【迷雾追踪】午夜凶铃响起，匿名举报者来自未来',
    category: '悬疑烧脑',
    description: '重案刑警在旧档案馆发现一张十年前的未公开录音带，AI 伴读全程协助破案指引。',
    cover_url: 'https://images.unsplash.com/photo-1485846234645-a62644f84728?w=800&q=80',
    episodes_count: 8,
    duration_str: '03:10',
    play_count_str: '34.8万',
    danmaku_count_str: '2410',
    creator_name: '迷案侦探社',
    creator_avatar: 'https://api.dicebear.com/7.x/bottts/svg?seed=detective'
  },
  {
    id: '5f910482-9912-410a-b812-40192a839102',
    title: '【AI 伴读精选】高能台词与经典影视名场面逐帧解构',
    category: 'AI 伴读精选',
    description: '深入镜头语言与戏剧冲突张力，智能提炼编剧创作技巧与爆款短剧反转核心。',
    cover_url: 'https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=800&q=80',
    episodes_count: 6,
    duration_str: '02:50',
    play_count_str: '56.1万',
    danmaku_count_str: '4120',
    creator_name: 'AI 影视工坊',
    creator_avatar: 'https://api.dicebear.com/7.x/bottts/svg?seed=aistudio'
  },
  {
    id: '6b192830-4491-4910-a192-5910283a0192',
    title: '【回村后我成了全省首富】山林里的百亿农业帝国',
    category: '都市逆袭',
    description: '大学毕业返乡创业被邻里嘲笑，偶得沃盘农技数据库，三年带动全村开上超跑。',
    cover_url: 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800&q=80',
    episodes_count: 16,
    duration_str: '02:05',
    play_count_str: '67.9万',
    danmaku_count_str: '3940',
    creator_name: '新农人阿豪',
    creator_avatar: 'https://api.dicebear.com/7.x/bottts/svg?seed=village'
  }
]

onMounted(async () => {
  await fetchVideos()
  startCarousel()
})

onUnmounted(() => {
  stopCarousel()
})

async function fetchVideos() {
  try {
    const res: any = await api.get('/videos/home-feed', {
      params: {
        category: currentCategory.value === 'all' ? undefined : currentCategory.value,
        keyword: searchQuery.value || undefined
      }
    })
    const data = res?.data || res
    if (data?.videos && data.videos.length > 0) {
      videos.value = data.videos.map((v: any) => ({
        id: v.id,
        title: v.title,
        category: v.category,
        description: v.description || `夸克网盘原生驱动直读 · 共${v.duration_str} · 9:16 / 16:9 双模态极速畅享`,
        cover_url: v.cover_url,
        extra_images: Array.isArray(v.extra_images) ? v.extra_images : [],
        episodes_count: v.duration_str?.includes('集') ? parseInt(v.duration_str) : 1,
        duration_str: v.duration_str,
        play_count_str: v.play_count_str,
        danmaku_count_str: v.danmaku_count_str,
        creator_name: v.creator_name || '红果星芒剧场',
        creator_avatar: v.creator_avatar
      }))
    }
    if (data?.carousel_duration_seconds) {
      carouselDuration.value = data.carousel_duration_seconds * 1000
    }
    if (data?.carousels && data.carousels.length > 0) {
      carousels.value = data.carousels
    } else if (videos.value.length > 0) {
      // Build dynamic carousels from top short dramas in library
      carousels.value = videos.value.slice(0, 4).map((v, idx) => ({
        id: idx + 1,
        title: v.title,
        subtitle: `夸克网盘原生直连 · 共${v.duration_str} · 16:9 极简影院与 9:16 沉浸短剧模式无损自由切换`,
        tag: idx === 0 ? '本周爆款榜首' : '精选推荐',
        cover_url: v.cover_url,
        video_id: v.id
      }))
    }
  } catch (err) {
    console.warn('Failed to load dynamic home feed, falling back:', err)
  }
}

const filteredVideos = computed(() => {
  let list = videos.value
  // Filter by category
  if (currentCategory.value !== 'all' && currentCategory.value !== 'hot') {
    const catObj = categories.value.find(c => c.id === currentCategory.value)
    if (catObj) {
      list = list.filter(v => (v.category || '').includes(catObj.name) || catObj.name.includes(v.category || ''))
    }
  }
  // Filter by search query
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(v =>
      (v.title || '').toLowerCase().includes(q) ||
      (v.description || '').toLowerCase().includes(q) ||
      (v.category || '').toLowerCase().includes(q)
    )
  }
  return list
})

function selectCategory(catId: string) {
  currentCategory.value = catId
}

function handleHeaderSearch(kw: string) {
  searchQuery.value = kw
}

function clearSearch() {
  searchQuery.value = ''
}

function handleUserChanged(user: UserProfile | null) {
  currentUser.value = user
}

function goToVideo(id: string) {
  router.push(`/video/${id}`)
}

function getCategoryEmoji(cat?: string): string {
  if (!cat) return '🎬'
  if (cat.includes('战神')) return '⚡'
  if (cat.includes('甜宠')) return '🌸'
  if (cat.includes('悬疑')) return '🔍'
  if (cat.includes('精选') || cat.includes('高能')) return '🔥'
  if (cat.includes('逆袭')) return '🚀'
  return '🎬'
}

function getIconTheme(cat?: string): string {
  if (!cat) return 'pink-theme'
  if (cat.includes('战神')) return 'purple-theme'
  if (cat.includes('甜宠')) return 'rose-theme'
  if (cat.includes('悬疑')) return 'amber-theme'
  if (cat.includes('精选') || cat.includes('高能')) return 'pink-theme'
  return 'blue-theme'
}
</script>

<style scoped>
/* ========================================================================== */
/* Apple HIG Bento Grid Portal Styling                                       */
/* ========================================================================== */
.apple-bento-portal {
  min-height: 100vh;
  padding-bottom: 80px;
}

/* Centered Big Type Hero Header */
.portal-hero-section {
  padding: 64px 24px 36px 24px;
  text-align: center;
}

.hero-inner-container {
  max-width: 800px;
  margin: 0 auto;
}

.hero-pill-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 113, 227, 0.08);
  color: var(--apple-blue);
  font-size: 13px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: var(--apple-radius-pill);
  margin-bottom: 20px;
}

.badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--apple-blue);
}

.hero-big-title {
  margin: 0;
  font-size: 54px;
  font-weight: 800;
  color: var(--apple-text-primary);
  letter-spacing: -0.035em;
  line-height: 1.1;
}

.hero-sub-title {
  margin: 14px 0 32px 0;
  font-size: 18px;
  color: var(--apple-text-tertiary);
  font-weight: 400;
  letter-spacing: -0.01em;
}

/* Category Filter Pills (Apple Segmented Style) */
.category-pills-bar {
  display: inline-flex;
  background: rgba(0, 0, 0, 0.05);
  padding: 5px;
  border-radius: var(--apple-radius-pill);
  gap: 4px;
  max-width: 100%;
  overflow-x: auto;
}

.cat-pill-btn {
  border: none;
  background: transparent;
  color: var(--apple-text-secondary);
  font-size: 14px;
  font-weight: 500;
  padding: 8px 18px;
  border-radius: var(--apple-radius-pill);
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--apple-transition-fast);
}

.cat-pill-btn:hover {
  color: var(--apple-text-primary);
}

.cat-pill-btn.active {
  background: #FFFFFF;
  color: var(--bili-pink);
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(251, 114, 153, 0.16);
  border: 1px solid rgba(251, 114, 153, 0.25);
}

/* Main Wrap (Relaxed Fluid Bilibili Layout) */
.portal-main-wrap {
  max-width: 1720px;
  width: 100%;
  margin: 0 auto;
  padding: 0 40px;
}

/* Search feedback */
.search-feedback-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--apple-card-bg);
  border: 1px solid var(--apple-card-border);
  backdrop-filter: blur(20px);
  padding: 14px 20px;
  border-radius: var(--apple-radius-card);
  margin-bottom: 28px;
}

.clear-search-btn {
  background: var(--apple-gray-btn);
  border: none;
  color: var(--apple-text-primary);
  font-size: 13px;
  padding: 6px 14px;
  border-radius: var(--apple-radius-pill);
  cursor: pointer;
  transition: background var(--apple-transition-fast);
}

.clear-search-btn:hover {
  background: var(--apple-gray-btn-hover);
}

/* ========================================================================== */
/* Spotlight Hero Bento Card (2x2 Big Card)                                  */
/* ========================================================================== */
.spotlight-bento-card {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  background: var(--apple-card-bg);
  border: 1px solid var(--apple-card-border);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-radius: 28px;
  box-shadow: var(--apple-shadow-card);
  overflow: hidden;
  margin-bottom: 40px;
  cursor: pointer;
  transition: all var(--apple-transition-normal);
}

.spotlight-bento-card:hover {
  transform: translateY(-3px) scale(1.008);
  box-shadow: var(--apple-shadow-hover);
}

.spotlight-cover-side {
  position: relative;
  min-height: 340px;
  background-size: cover;
  background-position: center;
}

.spotlight-cover-scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.65) 100%);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 24px;
}

.spotlight-badge {
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(12px);
  color: #FFFFFF;
  font-size: 12px;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: var(--apple-radius-pill);
}

.spotlight-stats {
  display: flex;
  gap: 16px;
  color: #FFFFFF;
  font-size: 13px;
  font-weight: 500;
}

.carousel-arrow-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #FFFFFF;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 2;
  opacity: 0;
  transition: all 0.2s ease;
}

.spotlight-bento-card:hover .carousel-arrow-btn {
  opacity: 1;
}

.carousel-arrow-btn.prev-btn {
  left: 14px;
}

.carousel-arrow-btn.next-btn {
  right: 14px;
}

.carousel-arrow-btn:hover {
  background: rgba(0, 0, 0, 0.85);
  transform: translateY(-50%) scale(1.1);
}

.spotlight-info-side {
  padding: 36px 32px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.spotlight-header-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.spotlight-icon-squircle {
  width: 48px;
  height: 48px;
  border-radius: var(--apple-radius-icon);
  background: linear-gradient(135deg, #0071e3 0%, #60a5fa 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  box-shadow: 0 6px 16px rgba(0, 113, 227, 0.25);
  flex-shrink: 0;
}

.spotlight-topic-tag {
  font-size: 12px;
  font-weight: 600;
  color: var(--apple-blue);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.spotlight-title {
  margin: 4px 0 0 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--apple-text-primary);
  line-height: 1.35;
  letter-spacing: -0.02em;
}

.spotlight-desc {
  font-size: 14px;
  color: var(--apple-text-secondary);
  line-height: 1.6;
  margin: 16px 0;
}

.spotlight-actions-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-top: 1px solid var(--apple-hairline);
  padding-top: 20px;
}

.action-item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.action-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--apple-text-tertiary);
  letter-spacing: 0.06em;
}

.carousel-dots-row {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.carousel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--apple-gray-btn);
  cursor: pointer;
  transition: all var(--apple-transition-fast);
}

.carousel-dot.active {
  width: 24px;
  border-radius: var(--apple-radius-pill);
  background: var(--apple-blue);
}

/* ========================================================================== */
/* Section Titles                                                             */
/* ========================================================================== */
.section-title-bar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 24px;
  padding: 0 4px;
}

.section-heading {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  color: var(--apple-text-primary);
  letter-spacing: -0.02em;
}

.section-subtext {
  font-size: 13px;
  color: var(--apple-text-tertiary);
  margin-top: 4px;
  display: block;
}

.total-badge {
  font-size: 13px;
  color: var(--apple-text-tertiary);
  font-weight: 500;
}

/* ========================================================================== */
/* 3-Column Bento Grid (Directly Matching User Reference Image)              */
/* ========================================================================== */
/* ========================================================================== */
/* Fluid Auto-fill Bilibili Grid & Relaxed Cards                             */
/* ========================================================================== */
.bento-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(285px, 1fr));
  gap: 24px 20px;
  margin-bottom: 56px;
}

.bento-card {
  background: var(--liquid-glass-bg);
  border: 1px solid var(--liquid-glass-border);
  backdrop-filter: var(--liquid-glass-blur);
  -webkit-backdrop-filter: var(--liquid-glass-blur);
  border-radius: 18px;
  box-shadow: var(--liquid-glass-shadow);
  padding: 14px;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: all var(--apple-transition-normal);
}

.bento-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.08), 0 4px 14px rgba(0, 113, 227, 0.15);
  border-color: rgba(0, 113, 227, 0.3);
  background: rgba(255, 255, 255, 0.95);
}

.bento-card:hover .card-title {
  color: var(--bili-pink);
}

/* 16:9 Thumbnail */
.card-thumbnail-box {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 14px;
  background-size: cover;
  background-position: center;
  position: relative;
  overflow: hidden;
  transition: background-image 0.4s ease;
}

.multi-poster-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: #FFFFFF;
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: var(--apple-radius-pill);
  display: flex;
  align-items: center;
  gap: 4px;
  z-index: 5;
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.thumbnail-overlay-scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 45%, rgba(0,0,0,0.75) 100%);
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 8px 10px;
}

.duration-badge {
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(8px);
  color: #FFFFFF;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 6px;
}

.thumb-stats {
  display: flex;
  gap: 8px;
  color: #FFFFFF;
  font-size: 11px;
  font-weight: 500;
}

/* Card Body */
.card-body-wrap {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding-top: 12px;
}

.card-title {
  margin: 0 0 6px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--apple-text-primary);
  line-height: 1.4;
  letter-spacing: -0.015em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  height: 42px;
  transition: color var(--apple-transition-fast);
}

.card-meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.card-category-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(0, 113, 227, 0.08);
  color: #0071e3;
  border: 1px solid rgba(0, 113, 227, 0.15);
}

.card-episodes-tag {
  font-size: 12px;
  color: var(--apple-text-tertiary);
}

.card-description-text {
  font-size: 13px;
  color: var(--apple-text-secondary);
  line-height: 1.5;
  margin: 0 0 14px 0;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-actions-dock {
  border-top: 1px solid var(--apple-hairline);
  padding-top: 10px;
}

.bili-play-pill-btn {
  background: #f1f2f3;
  color: #18191c;
  border: 1px solid rgba(0, 0, 0, 0.06);
  font-size: 13px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 999px;
  width: 100%;
  cursor: pointer;
  transition: all 0.25s ease;
}

.bili-play-pill-btn:hover {
  background: #0071e3;
  color: #ffffff;
  border-color: #0071e3;
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.25);
}

.action-field-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.field-label-tag {
  font-size: 11px;
  font-weight: 700;
  color: var(--apple-text-tertiary);
  letter-spacing: 0.05em;
}

/* Apple Solid Pills */
.apple-primary-pill {
  background: var(--bili-pink);
  color: #FFFFFF;
  border: none;
  border-radius: var(--apple-radius-pill);
  padding: 7px 18px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--apple-transition-fast);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.apple-primary-pill:hover {
  background: #f85b88;
  transform: scale(1.02);
  box-shadow: 0 4px 14px rgba(251, 114, 153, 0.35);
}

.apple-secondary-pill {
  background: var(--apple-gray-btn);
  color: var(--apple-text-primary);
  border: none;
  border-radius: var(--apple-radius-pill);
  padding: 7px 18px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--apple-transition-fast);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.apple-secondary-pill:hover {
  background: var(--apple-gray-btn-hover);
  transform: scale(1.02);
}

.card-btn {
  padding: 6px 14px;
  font-size: 12px;
}

/* Empty state */
.empty-results-box {
  background: var(--apple-card-bg);
  border: 1px solid var(--apple-card-border);
  border-radius: var(--apple-radius-card);
  padding: 48px;
  text-align: center;
  margin: 32px 0;
}

.empty-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

/* ========================================================================== */
/* Platform Technology Highlights Bento Grid                                 */
/* ========================================================================== */
.platform-features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin: 60px 0 40px 0;
}

.feature-bento-card {
  background: var(--apple-card-bg);
  border: 1px solid var(--apple-card-border);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 28px 24px;
  box-shadow: var(--apple-shadow-card), var(--glass-specular);
  display: flex;
  flex-direction: column;
  transition: all var(--apple-transition-normal);
}

.feature-bento-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--apple-shadow-hover), var(--glass-specular);
}

.feature-icon-box {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  transition: transform var(--apple-transition-fast);
}

.feature-bento-card:hover .feature-icon-box {
  transform: scale(1.08);
}

.feat-svg {
  width: 22px;
  height: 22px;
  stroke: currentColor;
}

.feature-icon-box.blue-theme {
  background: rgba(0, 113, 227, 0.12);
  color: var(--apple-blue);
}

.feature-icon-box.purple-theme {
  background: rgba(156, 39, 176, 0.12);
  color: #9c27b0;
}

.feature-icon-box.rose-theme {
  background: rgba(233, 30, 99, 0.12);
  color: #e91e63;
}

button:active, .bili-play-pill-btn:active, .cat-pill-btn:active, .apple-primary-pill:active, .apple-secondary-pill:active {
  transform: scale(0.96) !important;
}

.feature-title {
  margin: 0 0 8px 0;
  font-size: 17px;
  font-weight: 700;
  color: var(--apple-text-primary);
}

.feature-desc {
  font-size: 13px;
  color: var(--apple-text-secondary);
  line-height: 1.6;
  margin: 0 0 16px 0;
  flex: 1;
}

.feature-foot-tag {
  font-size: 10px;
  font-weight: 700;
  color: var(--apple-text-tertiary);
  letter-spacing: 0.08em;
}

/* ========================================================================== */
/* Apple Style Footer Resources Section (Matching Reference Image)           */
/* ========================================================================== */
.portal-footer-section {
  text-align: center;
  padding-top: 40px;
  border-top: 1px solid var(--apple-hairline);
  margin-top: 40px;
}

.footer-resources-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--apple-text-tertiary);
  letter-spacing: 0.1em;
  margin-bottom: 12px;
}

.footer-links-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 13px;
  color: var(--apple-text-secondary);
  margin-bottom: 14px;
}

.footer-link {
  cursor: pointer;
  transition: color var(--apple-transition-fast);
}

.footer-link:hover {
  color: var(--apple-blue);
}

.footer-dot {
  color: var(--apple-text-tertiary);
}

.footer-copyright {
  margin: 0;
  font-size: 12px;
  color: var(--apple-text-tertiary);
}

/* Responsive */
@media (max-width: 900px) {
  .spotlight-bento-card {
    grid-template-columns: 1fr;
  }
  .bento-cards-grid {
    grid-template-columns: 1fr;
  }
  .platform-features-grid {
    grid-template-columns: 1fr;
  }
}

/* Apple HIG Drama Detail Modal */
:deep(.apple-drama-modal) {
  border-radius: 20px;
  background: var(--apple-modal-bg, rgba(28, 28, 30, 0.95)) !important;
  backdrop-filter: blur(28px) saturate(180%);
  border: 1px solid var(--apple-modal-border, rgba(255, 255, 255, 0.12));
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.45);
  overflow: hidden;
}

:deep(.apple-drama-modal .el-dialog__header) {
  padding: 16px 24px;
  border-bottom: 1px solid var(--apple-modal-divider, rgba(255, 255, 255, 0.08));
  margin-right: 0;
}

:deep(.apple-drama-modal .el-dialog__body) {
  padding: 20px 24px 24px;
}

.modal-apple-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.modal-apple-badge {
  font-size: 15px;
  font-weight: 600;
  color: var(--apple-modal-title, #fff);
  letter-spacing: -0.01em;
}

.modal-apple-sub {
  font-size: 11px;
  color: var(--apple-modal-sub, rgba(255, 255, 255, 0.5));
  letter-spacing: 0.02em;
}

.drama-detail-modal-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-poster-banner {
  width: 100%;
  height: 240px;
  border-radius: 14px;
  background-size: cover;
  background-position: center;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.modal-poster-scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8) 0%, transparent 60%);
  display: flex;
  align-items: flex-end;
  padding: 14px 16px;
  gap: 8px;
}

.modal-category-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 100px;
  background: rgba(0, 113, 227, 0.9);
  color: #fff;
}

.modal-episodes-tag {
  font-size: 11px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 100px;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  color: #fff;
}

.modal-gallery-strip {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.modal-gallery-thumb {
  width: 64px;
  height: 40px;
  border-radius: 6px;
  background-size: cover;
  background-position: center;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.modal-gallery-thumb.active {
  border-color: #0071e3;
  transform: scale(1.05);
}

.modal-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-drama-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--apple-modal-title, #fff);
}

.modal-stats-badges {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--apple-modal-sub, rgba(255, 255, 255, 0.55));
}

.modal-synopsis-card {
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--apple-modal-card-bg, rgba(255, 255, 255, 0.05));
  border: 1px solid var(--apple-modal-card-border, rgba(255, 255, 255, 0.08));
}

.synopsis-label-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.synopsis-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--apple-modal-title, rgba(255, 255, 255, 0.85));
}

.rag-ready-pill {
  margin-left: auto;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 100px;
  background: rgba(52, 199, 89, 0.18);
  color: #34c759;
  border: 1px solid rgba(52, 199, 89, 0.35);
}

.synopsis-content-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--apple-modal-text, rgba(255, 255, 255, 0.75));
}

.modal-actions-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}

.apple-modal-cancel-btn {
  padding: 9px 18px;
  border-radius: 100px;
  background: var(--apple-modal-btn-cancel-bg, rgba(255, 255, 255, 0.08));
  border: 1px solid var(--apple-modal-btn-cancel-border, rgba(255, 255, 255, 0.12));
  color: var(--apple-modal-btn-cancel-text, rgba(255, 255, 255, 0.75));
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.apple-modal-cancel-btn:hover {
  background: var(--apple-modal-btn-cancel-hover, rgba(255, 255, 255, 0.14));
}

.apple-modal-watch-btn {
  padding: 9px 24px;
  border-radius: 100px;
  background: #0071e3;
  border: none;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 14px rgba(0, 113, 227, 0.4);
}

.apple-modal-watch-btn:hover {
  background: #0077ed;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 113, 227, 0.55);
}

/* Light Mode Overrides for Drama Detail Modal */
:global(html[data-theme="light"]) :deep(.apple-drama-modal) {
  --apple-modal-bg: #ffffff;
  --apple-modal-border: rgba(0, 0, 0, 0.12);
  --apple-modal-divider: rgba(0, 0, 0, 0.08);
  --apple-modal-title: #1d1d1f;
  --apple-modal-sub: #6e6e73;
  --apple-modal-card-bg: #f5f5f7;
  --apple-modal-card-border: rgba(0, 0, 0, 0.08);
  --apple-modal-text: #333336;
  --apple-modal-btn-cancel-bg: #e5e5ea;
  --apple-modal-btn-cancel-border: rgba(0, 0, 0, 0.12);
  --apple-modal-btn-cancel-text: #1d1d1f;
  --apple-modal-btn-cancel-hover: #d1d1d6;
}

:global(html[data-theme="light"]) .rag-ready-pill {
  background: rgba(52, 199, 89, 0.14);
  color: #248a3d;
  border-color: rgba(52, 199, 89, 0.35);
}
</style>
