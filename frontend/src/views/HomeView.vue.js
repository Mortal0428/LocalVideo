/// <reference types="../../node_modules/.vue-global-types/vue_3.5_0_0_0.d.ts" />
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { Picture } from '@element-plus/icons-vue';
import GlobalHeader from '../components/GlobalHeader.vue';
import { api } from '../api/client';
const router = useRouter();
const searchQuery = ref('');
const currentCategory = ref('all');
const currentUser = ref(null);
const currentCarouselIdx = ref(0);
const videos = ref([]);
let carouselTimer = null;
const hoveredCardImages = ref({});
let cardHoverIntervals = {};
function onCardMouseEnter(video) {
    if (video.extra_images && video.extra_images.length > 1) {
        if (!hoveredCardImages.value[video.id]) {
            hoveredCardImages.value[video.id] = 0;
        }
        if (cardHoverIntervals[video.id])
            clearInterval(cardHoverIntervals[video.id]);
        cardHoverIntervals[video.id] = setInterval(() => {
            const cur = hoveredCardImages.value[video.id] || 0;
            hoveredCardImages.value[video.id] = (cur + 1) % video.extra_images.length;
        }, 1200);
    }
}
function onCardMouseLeave(video) {
    if (cardHoverIntervals[video.id]) {
        clearInterval(cardHoverIntervals[video.id]);
        delete cardHoverIntervals[video.id];
    }
    hoveredCardImages.value[video.id] = 0;
}
function getCardActiveCover(video) {
    if (video.extra_images && video.extra_images.length > 1) {
        const idx = hoveredCardImages.value[video.id] || 0;
        return video.extra_images[idx] || video.cover_url;
    }
    return video.cover_url;
}
const carouselDuration = ref(5000);
function startCarousel() {
    stopCarousel();
    const delay = (activeCarousel.value?.duration_seconds ? activeCarousel.value.duration_seconds * 1000 : carouselDuration.value) || 5000;
    carouselTimer = setInterval(() => {
        if (carousels.value.length > 0) {
            currentCarouselIdx.value = (currentCarouselIdx.value + 1) % carousels.value.length;
        }
    }, delay);
}
function stopCarousel() {
    if (carouselTimer) {
        clearInterval(carouselTimer);
        carouselTimer = null;
    }
}
function pauseCarousel() {
    stopCarousel();
}
function nextCarousel() {
    if (carousels.value.length > 0) {
        currentCarouselIdx.value = (currentCarouselIdx.value + 1) % carousels.value.length;
    }
}
function prevCarousel() {
    if (carousels.value.length > 0) {
        currentCarouselIdx.value = (currentCarouselIdx.value - 1 + carousels.value.length) % carousels.value.length;
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
]);
// Carousels for top showcase
const carousels = ref([
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
]);
const activeCarousel = computed(() => {
    if (carousels.value.length === 0)
        return null;
    return carousels.value[currentCarouselIdx.value % carousels.value.length];
});
// Mock fallback videos with diverse categories
const mockVideos = [
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
];
onMounted(async () => {
    await fetchVideos();
    startCarousel();
});
onUnmounted(() => {
    stopCarousel();
});
async function fetchVideos() {
    try {
        const res = await api.get('/videos/home-feed', {
            params: {
                category: currentCategory.value === 'all' ? undefined : currentCategory.value,
                keyword: searchQuery.value || undefined
            }
        });
        const data = res?.data || res;
        if (data?.videos && data.videos.length > 0) {
            videos.value = data.videos.map((v) => ({
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
            }));
        }
        if (data?.carousel_duration_seconds) {
            carouselDuration.value = data.carousel_duration_seconds * 1000;
        }
        if (data?.carousels && data.carousels.length > 0) {
            carousels.value = data.carousels;
        }
        else if (videos.value.length > 0) {
            // Build dynamic carousels from top short dramas in library
            carousels.value = videos.value.slice(0, 4).map((v, idx) => ({
                id: idx + 1,
                title: v.title,
                subtitle: `夸克网盘原生直连 · 共${v.duration_str} · 16:9 极简影院与 9:16 沉浸短剧模式无损自由切换`,
                tag: idx === 0 ? '本周爆款榜首' : '精选推荐',
                cover_url: v.cover_url,
                video_id: v.id
            }));
        }
    }
    catch (err) {
        console.warn('Failed to load dynamic home feed, falling back:', err);
    }
}
const filteredVideos = computed(() => {
    let list = videos.value;
    // Filter by category
    if (currentCategory.value !== 'all' && currentCategory.value !== 'hot') {
        const catObj = categories.value.find(c => c.id === currentCategory.value);
        if (catObj) {
            list = list.filter(v => (v.category || '').includes(catObj.name) || catObj.name.includes(v.category || ''));
        }
    }
    // Filter by search query
    if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase();
        list = list.filter(v => (v.title || '').toLowerCase().includes(q) ||
            (v.description || '').toLowerCase().includes(q) ||
            (v.category || '').toLowerCase().includes(q));
    }
    return list;
});
function selectCategory(catId) {
    currentCategory.value = catId;
}
function handleHeaderSearch(kw) {
    searchQuery.value = kw;
}
function clearSearch() {
    searchQuery.value = '';
}
function handleUserChanged(user) {
    currentUser.value = user;
}
function goToVideo(id) {
    router.push(`/video/${id}`);
}
function getCategoryEmoji(cat) {
    if (!cat)
        return '🎬';
    if (cat.includes('战神'))
        return '⚡';
    if (cat.includes('甜宠'))
        return '🌸';
    if (cat.includes('悬疑'))
        return '🔍';
    if (cat.includes('精选') || cat.includes('高能'))
        return '🔥';
    if (cat.includes('逆袭'))
        return '🚀';
    return '🎬';
}
function getIconTheme(cat) {
    if (!cat)
        return 'pink-theme';
    if (cat.includes('战神'))
        return 'purple-theme';
    if (cat.includes('甜宠'))
        return 'rose-theme';
    if (cat.includes('悬疑'))
        return 'amber-theme';
    if (cat.includes('精选') || cat.includes('高能'))
        return 'pink-theme';
    return 'blue-theme';
}
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['cat-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['cat-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['clear-search-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-arrow-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-arrow-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-arrow-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-arrow-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-title']} */ ;
/** @type {__VLS_StyleScopedClasses['bili-play-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-secondary-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-icon-box']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-icon-box']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-icon-box']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-icon-box']} */ ;
/** @type {__VLS_StyleScopedClasses['bili-play-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['cat-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-secondary-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-link']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['bento-cards-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['platform-features-grid']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "apple-bento-portal" },
    id: "bili-portal-page",
});
/** @type {[typeof GlobalHeader, ]} */ ;
// @ts-ignore
const __VLS_0 = __VLS_asFunctionalComponent(GlobalHeader, new GlobalHeader({
    ...{ 'onSearch': {} },
    ...{ 'onUserChanged': {} },
}));
const __VLS_1 = __VLS_0({
    ...{ 'onSearch': {} },
    ...{ 'onUserChanged': {} },
}, ...__VLS_functionalComponentArgsRest(__VLS_0));
let __VLS_3;
let __VLS_4;
let __VLS_5;
const __VLS_6 = {
    onSearch: (__VLS_ctx.handleHeaderSearch)
};
const __VLS_7 = {
    onUserChanged: (__VLS_ctx.handleUserChanged)
};
var __VLS_2;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "portal-hero-section" },
    id: "bili-banner-hero",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "hero-inner-container" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "hero-pill-badge" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "badge-dot" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({
    ...{ class: "hero-big-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "hero-sub-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.nav, __VLS_intrinsicElements.nav)({
    ...{ class: "category-pills-bar" },
    id: "channel-bar",
});
for (const [cat] of __VLS_getVForSourceType((__VLS_ctx.categories))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                __VLS_ctx.selectCategory(cat.id);
            } },
        key: (cat.id),
        ...{ class: "cat-pill-btn" },
        ...{ class: ({ active: __VLS_ctx.currentCategory === cat.id }) },
        id: ('btn-cat-' + cat.id),
    });
    (cat.name);
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.main, __VLS_intrinsicElements.main)({
    ...{ class: "portal-main-wrap" },
});
if (__VLS_ctx.searchQuery) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "search-feedback-banner" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "feedback-text" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({});
    (__VLS_ctx.searchQuery);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.clearSearch) },
        ...{ class: "clear-search-btn" },
    });
}
if (!__VLS_ctx.searchQuery && __VLS_ctx.activeCarousel) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ onClick: (...[$event]) => {
                if (!(!__VLS_ctx.searchQuery && __VLS_ctx.activeCarousel))
                    return;
                __VLS_ctx.goToVideo(__VLS_ctx.activeCarousel.video_id);
            } },
        ...{ onMouseenter: (__VLS_ctx.pauseCarousel) },
        ...{ onMouseleave: (__VLS_ctx.startCarousel) },
        ...{ class: "spotlight-bento-card" },
        id: "carousel-banner-box",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "spotlight-cover-side" },
        ...{ style: ({ backgroundImage: `url(${__VLS_ctx.activeCarousel.cover_url})` }) },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "spotlight-cover-scrim" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "spotlight-badge" },
    });
    (__VLS_ctx.activeCarousel.tag);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "spotlight-stats" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.activeCarousel.play_count_str || '超清直连');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.activeCarousel.danmaku_count_str || '互动弹幕');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.prevCarousel) },
        ...{ class: "carousel-arrow-btn prev-btn" },
        title: "上一张",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.nextCarousel) },
        ...{ class: "carousel-arrow-btn next-btn" },
        title: "下一张",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "spotlight-info-side" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "spotlight-header-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "spotlight-tag-pill" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "spotlight-topic-tag" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({
        ...{ class: "spotlight-title" },
    });
    (__VLS_ctx.activeCarousel.title);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "spotlight-desc" },
    });
    (__VLS_ctx.activeCarousel.subtitle);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "spotlight-actions-area" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "action-item-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "action-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(!__VLS_ctx.searchQuery && __VLS_ctx.activeCarousel))
                    return;
                __VLS_ctx.goToVideo(__VLS_ctx.activeCarousel.video_id);
            } },
        ...{ class: "apple-primary-pill" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "action-item-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "action-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(!__VLS_ctx.searchQuery && __VLS_ctx.activeCarousel))
                    return;
                __VLS_ctx.goToVideo(__VLS_ctx.activeCarousel.video_id);
            } },
        ...{ class: "apple-secondary-pill" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "carousel-dots-row" },
    });
    for (const [c, idx] of __VLS_getVForSourceType((__VLS_ctx.carousels))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ onClick: (...[$event]) => {
                    if (!(!__VLS_ctx.searchQuery && __VLS_ctx.activeCarousel))
                        return;
                    __VLS_ctx.currentCarouselIdx = idx;
                } },
            key: (c.id),
            ...{ class: "carousel-dot" },
            ...{ class: ({ active: __VLS_ctx.currentCarouselIdx === idx }) },
        });
    }
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "section-title-bar" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "title-left" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
    ...{ class: "section-heading" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "section-subtext" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "total-badge" },
});
(__VLS_ctx.filteredVideos.length);
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "bento-cards-grid" },
});
for (const [v] of __VLS_getVForSourceType((__VLS_ctx.filteredVideos))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.article, __VLS_intrinsicElements.article)({
        ...{ onClick: (...[$event]) => {
                __VLS_ctx.goToVideo(v.id);
            } },
        ...{ onMouseenter: (...[$event]) => {
                __VLS_ctx.onCardMouseEnter(v);
            } },
        ...{ onMouseleave: (...[$event]) => {
                __VLS_ctx.onCardMouseLeave(v);
            } },
        key: (v.id),
        ...{ class: "bento-card bili-video-card" },
        id: ('video-card-' + v.id),
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "card-thumbnail-box" },
        ...{ style: ({ backgroundImage: `url(${__VLS_ctx.getCardActiveCover(v)})` }) },
    });
    if (v.extra_images && v.extra_images.length > 1) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "multi-poster-badge" },
            title: "多剧照动态轮播",
        });
        const __VLS_8 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({
            size: (12),
        }));
        const __VLS_10 = __VLS_9({
            size: (12),
        }, ...__VLS_functionalComponentArgsRest(__VLS_9));
        __VLS_11.slots.default;
        const __VLS_12 = {}.Picture;
        /** @type {[typeof __VLS_components.Picture, ]} */ ;
        // @ts-ignore
        const __VLS_13 = __VLS_asFunctionalComponent(__VLS_12, new __VLS_12({}));
        const __VLS_14 = __VLS_13({}, ...__VLS_functionalComponentArgsRest(__VLS_13));
        var __VLS_11;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        ((__VLS_ctx.hoveredCardImages[v.id] || 0) + 1);
        (v.extra_images.length);
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "thumbnail-overlay-scrim" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "duration-badge" },
    });
    (v.duration_str || '02:30');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "thumb-stats" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (v.play_count_str || '10.5万');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (v.danmaku_count_str || '820');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "card-body-wrap" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
        ...{ class: "card-title" },
        title: (v.title),
    });
    (v.title);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "card-meta-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "card-category-pill" },
    });
    (v.category || '短剧精选');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "card-episodes-tag" },
    });
    (v.episodes_count || 1);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "card-description-text" },
    });
    (v.description);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "card-actions-dock" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                __VLS_ctx.goToVideo(v.id);
            } },
        ...{ class: "bili-play-pill-btn" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
if (__VLS_ctx.filteredVideos.length === 0) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "empty-results-box" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "empty-icon" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
    (__VLS_ctx.searchQuery);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.clearSearch) },
        ...{ class: "apple-secondary-pill" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "platform-features-grid" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-bento-card" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-icon-box blue-theme" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({
    ...{ class: "feat-svg" },
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    'stroke-width': "2",
    'stroke-linecap': "round",
    'stroke-linejoin': "round",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.path)({
    d: "M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.path)({
    d: "m13 11-4 6h6l-4 6",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
    ...{ class: "feature-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "feature-desc" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-foot-tag" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-bento-card" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-icon-box purple-theme" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({
    ...{ class: "feat-svg" },
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    'stroke-width': "2",
    'stroke-linecap': "round",
    'stroke-linejoin': "round",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.rect)({
    width: "18",
    height: "18",
    x: "3",
    y: "3",
    rx: "2",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.path)({
    d: "m9 8 7 4-7 4V8Z",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.path)({
    d: "M3 9h18",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
    ...{ class: "feature-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "feature-desc" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-foot-tag" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-bento-card" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-icon-box rose-theme" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({
    ...{ class: "feat-svg" },
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    'stroke-width': "2",
    'stroke-linecap': "round",
    'stroke-linejoin': "round",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.path)({
    d: "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.path)({
    d: "m9 12 2 2 4-4",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
    ...{ class: "feature-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "feature-desc" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-foot-tag" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.footer, __VLS_intrinsicElements.footer)({
    ...{ class: "portal-footer-section" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "footer-resources-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "footer-links-row" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "footer-link" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "footer-dot" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "footer-link" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "footer-dot" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "footer-link" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "footer-dot" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "footer-link" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "footer-dot" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "footer-link" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "footer-copyright" },
});
/** @type {__VLS_StyleScopedClasses['apple-bento-portal']} */ ;
/** @type {__VLS_StyleScopedClasses['portal-hero-section']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-inner-container']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-pill-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['badge-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-big-title']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-sub-title']} */ ;
/** @type {__VLS_StyleScopedClasses['category-pills-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['cat-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['portal-main-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['search-feedback-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['feedback-text']} */ ;
/** @type {__VLS_StyleScopedClasses['clear-search-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-cover-side']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-cover-scrim']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-stats']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-arrow-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['prev-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-arrow-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['next-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-info-side']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-header-row']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-tag-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-topic-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-title']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['spotlight-actions-area']} */ ;
/** @type {__VLS_StyleScopedClasses['action-item-row']} */ ;
/** @type {__VLS_StyleScopedClasses['action-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['action-item-row']} */ ;
/** @type {__VLS_StyleScopedClasses['action-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-secondary-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-dots-row']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['section-title-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['title-left']} */ ;
/** @type {__VLS_StyleScopedClasses['section-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['section-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['total-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['bento-cards-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['bili-video-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-thumbnail-box']} */ ;
/** @type {__VLS_StyleScopedClasses['multi-poster-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['thumbnail-overlay-scrim']} */ ;
/** @type {__VLS_StyleScopedClasses['duration-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['thumb-stats']} */ ;
/** @type {__VLS_StyleScopedClasses['card-body-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['card-title']} */ ;
/** @type {__VLS_StyleScopedClasses['card-meta-row']} */ ;
/** @type {__VLS_StyleScopedClasses['card-category-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['card-episodes-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['card-description-text']} */ ;
/** @type {__VLS_StyleScopedClasses['card-actions-dock']} */ ;
/** @type {__VLS_StyleScopedClasses['bili-play-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-results-box']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-secondary-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['platform-features-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-icon-box']} */ ;
/** @type {__VLS_StyleScopedClasses['blue-theme']} */ ;
/** @type {__VLS_StyleScopedClasses['feat-svg']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-title']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-foot-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-icon-box']} */ ;
/** @type {__VLS_StyleScopedClasses['purple-theme']} */ ;
/** @type {__VLS_StyleScopedClasses['feat-svg']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-title']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-foot-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-icon-box']} */ ;
/** @type {__VLS_StyleScopedClasses['rose-theme']} */ ;
/** @type {__VLS_StyleScopedClasses['feat-svg']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-title']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-foot-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['portal-footer-section']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-resources-label']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-links-row']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-link']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-link']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-link']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-link']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-link']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-copyright']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            Picture: Picture,
            GlobalHeader: GlobalHeader,
            searchQuery: searchQuery,
            currentCategory: currentCategory,
            currentCarouselIdx: currentCarouselIdx,
            hoveredCardImages: hoveredCardImages,
            onCardMouseEnter: onCardMouseEnter,
            onCardMouseLeave: onCardMouseLeave,
            getCardActiveCover: getCardActiveCover,
            startCarousel: startCarousel,
            pauseCarousel: pauseCarousel,
            nextCarousel: nextCarousel,
            prevCarousel: prevCarousel,
            categories: categories,
            carousels: carousels,
            activeCarousel: activeCarousel,
            filteredVideos: filteredVideos,
            selectCategory: selectCategory,
            handleHeaderSearch: handleHeaderSearch,
            clearSearch: clearSearch,
            handleUserChanged: handleUserChanged,
            goToVideo: goToVideo,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=HomeView.vue.js.map