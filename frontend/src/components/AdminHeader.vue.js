/// <reference types="../../node_modules/.vue-global-types/vue_3.5_0_0_0.d.ts" />
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { api } from '../api/client';
import { useUserStore } from '../stores/user';
import { Sunny, Moon, Monitor, Setting, Platform, VideoCamera, Cpu, DataAnalysis, Refresh, Bell, ArrowDown, ArrowRight, Film, SwitchButton, CircleCheckFilled } from '@element-plus/icons-vue';
import EngineSettingsModal from './EngineSettingsModal.vue';
const props = withDefaults(defineProps(), {
    mode: 'admin',
    activeTab: ''
});
const emit = defineEmits();
const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
// State
const currentUser = userStore.currentUser;
const defaultAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=apple-admin';
const userAvatar = computed(() => currentUser.value?.avatar_url || defaultAvatar);
const userDisplayName = computed(() => currentUser.value?.nickname || currentUser.value?.username || (props.mode === 'admin' ? '系统管理员' : '签约创作者'));
const userRoleLabel = computed(() => {
    const role = currentUser.value?.role;
    if (role === 'ADMIN')
        return '超级管理员';
    if (role === 'CREATOR')
        return '签约创作者';
    if (role === 'REVIEWER')
        return '社区审核员';
    return props.mode === 'admin' ? '超级管理员' : '签约创作者';
});
const userRoleClass = computed(() => {
    const role = currentUser.value?.role?.toLowerCase() || '';
    return role || (props.mode === 'admin' ? 'admin' : 'creator');
});
// Theme Switching
const currentTheme = ref('system');
const toggleTheme = (mode) => {
    currentTheme.value = mode;
    localStorage.setItem('cinema_theme', mode);
    if (mode === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
    else if (mode === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    }
    else {
        const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    }
};
// Overlays state
const showTelemetryPopover = ref(false);
const showSkylightDrawer = ref(false);
const showProfileMenu = ref(false);
const showSettingsModal = ref(false);
const closeAllOverlays = () => {
    showTelemetryPopover.value = false;
    showSkylightDrawer.value = false;
    showProfileMenu.value = false;
};
const toggleTelemetryPopover = () => {
    showTelemetryPopover.value = !showTelemetryPopover.value;
    if (showTelemetryPopover.value) {
        showSkylightDrawer.value = false;
        showProfileMenu.value = false;
    }
};
const toggleSkylightDrawer = () => {
    showSkylightDrawer.value = !showSkylightDrawer.value;
    if (showSkylightDrawer.value) {
        showTelemetryPopover.value = false;
        showProfileMenu.value = false;
    }
};
const toggleProfileMenu = () => {
    showProfileMenu.value = !showProfileMenu.value;
    if (showProfileMenu.value) {
        showTelemetryPopover.value = false;
        showSkylightDrawer.value = false;
    }
};
const telemetry = ref({
    status: 'healthy',
    circuit_state: 'CLOSED',
    active_provider: 'ollama',
    active_model: 'deepseek-r1:1.5b',
    latency_ms: 1.0,
    uptime_seconds: 86400,
    pending_reviews_count: 0,
    consecutive_failures: 0,
    recovery_countdown_seconds: 0
});
const isFetchingTelemetry = ref(false);
async function fetchTelemetry() {
    isFetchingTelemetry.value = true;
    try {
        const res = await api.get('/system/telemetry');
        if (res && res.status) {
            telemetry.value = {
                status: res.status,
                circuit_state: res.circuit_state || 'CLOSED',
                active_provider: res.active_provider || 'ollama',
                active_model: res.active_model || 'deepseek-r1:1.5b',
                latency_ms: typeof res.latency_ms === 'number' ? res.latency_ms : 1.0,
                uptime_seconds: res.uptime_seconds || 86400,
                pending_reviews_count: res.pending_reviews_count || 0,
                consecutive_failures: res.consecutive_failures || 0,
                recovery_countdown_seconds: res.recovery_countdown_seconds || 0
            };
        }
    }
    catch (err) {
        console.warn('System telemetry fetch fallback:', err);
    }
    finally {
        isFetchingTelemetry.value = false;
    }
}
let telemetryTimer = null;
onMounted(async () => {
    const saved = localStorage.getItem('cinema_theme') || 'system';
    currentTheme.value = saved;
    await userStore.refreshProfile();
    emit('userChanged', currentUser.value);
    await fetchTelemetry();
    telemetryTimer = setInterval(fetchTelemetry, 10000);
});
onUnmounted(() => {
    if (telemetryTimer) {
        clearInterval(telemetryTimer);
        telemetryTimer = null;
    }
});
watch(() => route.path, async () => {
    await userStore.refreshProfile();
    emit('userChanged', currentUser.value);
});
const latencyClass = computed(() => {
    const lat = telemetry.value.latency_ms;
    if (lat < 100)
        return 'latency-fast';
    if (lat < 500)
        return 'latency-normal';
    return 'latency-slow';
});
const circuitClass = computed(() => {
    const state = telemetry.value.circuit_state;
    if (state === 'CLOSED')
        return 'circuit-closed';
    if (state === 'OPEN')
        return 'circuit-open';
    return 'circuit-half-open';
});
function formatUptime(seconds) {
    if (!seconds || seconds <= 0)
        return '1天 0小时';
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (d > 0)
        return `${d}天 ${h}小时`;
    if (h > 0)
        return `${h}小时 ${m}分钟`;
    return `${m}分钟`;
}
function openEngineModal() {
    showTelemetryPopover.value = false;
    showSettingsModal.value = true;
}
function onEngineConfigUpdated() {
    fetchTelemetry();
}
// Active Tab Display
const tabNameMap = {
    bi: 'BI 智能驾驶舱',
    dramas: '短剧资产编目',
    sync: '网盘集群同步',
    carousels: '首页焦点展架',
    users: '用户权限流转',
    applications: '入驻资质审核',
    contents: '互动合规机审',
    engine: '模型引擎底座',
    creator: '创作者工作台',
    disk: '网盘空间管理',
    upload: '视频原画上传'
};
const activeTabTitle = computed(() => {
    if (props.activeTab && tabNameMap[props.activeTab]) {
        return tabNameMap[props.activeTab];
    }
    return '';
});
const notificationItems = computed(() => {
    const list = [];
    if (telemetry.value.pending_reviews_count > 0) {
        list.push({
            id: 'pending-reviews',
            category: '合规待办',
            categoryClass: 'cat-review',
            title: `有 ${telemetry.value.pending_reviews_count} 条待审核工单等待处置`,
            description: '包括弹幕违规关键词机审记录与创作者入驻申请。',
            time: '刚刚',
            level: 'warning',
            targetTab: 'contents'
        });
    }
    else {
        list.push({
            id: 'pending-reviews-clean',
            category: '合规治理',
            categoryClass: 'cat-review',
            title: '社区互动内容机审队列就绪',
            description: 'DFA 字典树前台实时拦截生效，未决弹幕工单均已处理完毕。',
            time: '实时',
            level: 'info',
            targetTab: 'contents'
        });
    }
    list.push({
        id: 'model-telemetry-ready',
        category: '模型底座',
        categoryClass: 'cat-engine',
        title: `当前算力引擎就绪 (${telemetry.value.active_provider}: ${telemetry.value.active_model})`,
        description: `断路器处于 ${telemetry.value.circuit_state} 模式，单次探测时延 ${telemetry.value.latency_ms}ms。`,
        time: '刚刚更新',
        level: 'info',
        targetTab: 'engine'
    });
    list.push({
        id: 'pan-cluster-active',
        category: '网盘集群',
        categoryClass: 'cat-storage',
        title: '夸克 · 沃盘双驱动分布式直连',
        description: 'HTTP 206 流式视频点播通道与大文件分片转存正常就绪。',
        time: '常驻在线',
        level: 'info',
        targetTab: 'sync'
    });
    return list;
});
const notificationBadgeCount = computed(() => {
    return telemetry.value.pending_reviews_count > 0 ? telemetry.value.pending_reviews_count : 1;
});
function handleSkylightDirect(item) {
    showSkylightDrawer.value = false;
    if (item.targetTab) {
        emit('selectTab', item.targetTab);
        if (props.mode === 'admin') {
            router.push({ path: '/admin', query: { tab: item.targetTab } });
        }
    }
    else if (item.targetRoute) {
        router.push(item.targetRoute);
    }
}
// User Actions
function goToSpectatorHall() {
    showProfileMenu.value = false;
    router.push('/');
}
function goToCreatorStudio() {
    showProfileMenu.value = false;
    router.push('/creator');
}
function goToCreatorBI() {
    showProfileMenu.value = false;
    emit('selectTab', 'bi');
    router.push({ path: '/creator', query: { tab: 'bi' } });
}
function goToAdminConsole() {
    showProfileMenu.value = false;
    router.push('/admin');
}
function handleLogout() {
    showProfileMenu.value = false;
    userStore.clearUser();
    emit('userChanged', null);
    router.push('/login');
}
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_withDefaultsArg = (function (t) { return t; })({
    mode: 'admin',
    activeTab: ''
});
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['admin-brand-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-icon-squircle']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-capsule']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-capsule']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-capsule']} */ ;
/** @type {__VLS_StyleScopedClasses['latency-fast']} */ ;
/** @type {__VLS_StyleScopedClasses['latency-normal']} */ ;
/** @type {__VLS_StyleScopedClasses['circuit-closed']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-metric-item']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-value']} */ ;
/** @type {__VLS_StyleScopedClasses['refresh-telemetry-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['refresh-telemetry-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['configure-engine-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['configure-engine-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-switch-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-engine-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-profile-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-profile-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-profile-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-role']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-role']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-item']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-item']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-item']} */ ;
/** @type {__VLS_StyleScopedClasses['logout-item']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-item-card']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-item-card']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-item-card']} */ ;
/** @type {__VLS_StyleScopedClasses['item-left-accent']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-item-card']} */ ;
/** @type {__VLS_StyleScopedClasses['item-left-accent']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-direct-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['profile-dropdown-card']} */ ;
/** @type {__VLS_StyleScopedClasses['popover-fade-enter-from']} */ ;
/** @type {__VLS_StyleScopedClasses['profile-dropdown-card']} */ ;
/** @type {__VLS_StyleScopedClasses['popover-fade-leave-to']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.header, __VLS_intrinsicElements.header)({
    ...{ class: "apple-admin-header" },
    id: "admin-header",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "admin-header-inner" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "header-left" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "admin-brand-badge" },
    id: "admin-brand-badge",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "brand-icon-squircle" },
});
const __VLS_0 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    size: (18),
}));
const __VLS_2 = __VLS_1({
    size: (18),
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
__VLS_3.slots.default;
if (__VLS_ctx.mode === 'admin') {
    const __VLS_4 = {}.Platform;
    /** @type {[typeof __VLS_components.Platform, ]} */ ;
    // @ts-ignore
    const __VLS_5 = __VLS_asFunctionalComponent(__VLS_4, new __VLS_4({}));
    const __VLS_6 = __VLS_5({}, ...__VLS_functionalComponentArgsRest(__VLS_5));
}
else {
    const __VLS_8 = {}.VideoCamera;
    /** @type {[typeof __VLS_components.VideoCamera, ]} */ ;
    // @ts-ignore
    const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({}));
    const __VLS_10 = __VLS_9({}, ...__VLS_functionalComponentArgsRest(__VLS_9));
}
var __VLS_3;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "brand-text-wrap" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "brand-title" },
});
(__VLS_ctx.mode === 'admin' ? 'CinemaAgent 控制中台' : 'CinemaAgent 创作者工作台');
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "brand-caption" },
});
(__VLS_ctx.mode === 'admin' ? 'ENTERPRISE ADMIN' : 'CREATOR CLOUD STUDIO');
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "cluster-env-tag" },
    id: "cluster-env-tag",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "cluster-dot" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
if (__VLS_ctx.activeTabTitle) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "header-breadcrumb" },
        id: "header-breadcrumb-tag",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "breadcrumb-sep" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "breadcrumb-current" },
    });
    (__VLS_ctx.activeTabTitle);
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "header-center" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ onClick: (__VLS_ctx.toggleTelemetryPopover) },
    ...{ class: "telemetry-capsule" },
    id: "system-health-indicator",
    ...{ class: ({
            'is-healthy': __VLS_ctx.telemetry.status === 'healthy',
            'is-degraded': __VLS_ctx.telemetry.status === 'degraded',
            'is-down': __VLS_ctx.telemetry.status === 'down'
        }) },
    title: "点击查看大模型底层遥测与断路器状态",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "health-dot" },
    ...{ class: ({
            'pulse-green': __VLS_ctx.telemetry.status === 'healthy',
            'pulse-yellow': __VLS_ctx.telemetry.status === 'degraded',
            'pulse-red': __VLS_ctx.telemetry.status === 'down'
        }) },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "health-status-text" },
});
(__VLS_ctx.telemetry.status === 'healthy' ? '系统服务在线正常' : __VLS_ctx.telemetry.status === 'degraded' ? '服务降级运行中' : '系统故障离线');
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "capsule-divider" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "model-badge-inline" },
});
const __VLS_12 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_13 = __VLS_asFunctionalComponent(__VLS_12, new __VLS_12({
    size: (13),
    ...{ class: "model-icon" },
}));
const __VLS_14 = __VLS_13({
    size: (13),
    ...{ class: "model-icon" },
}, ...__VLS_functionalComponentArgsRest(__VLS_13));
__VLS_15.slots.default;
const __VLS_16 = {}.Cpu;
/** @type {[typeof __VLS_components.Cpu, ]} */ ;
// @ts-ignore
const __VLS_17 = __VLS_asFunctionalComponent(__VLS_16, new __VLS_16({}));
const __VLS_18 = __VLS_17({}, ...__VLS_functionalComponentArgsRest(__VLS_17));
var __VLS_15;
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "model-name-text" },
});
(__VLS_ctx.telemetry.active_provider);
(__VLS_ctx.telemetry.active_model);
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "latency-badge" },
    ...{ class: (__VLS_ctx.latencyClass) },
});
(__VLS_ctx.telemetry.latency_ms > 0 ? __VLS_ctx.telemetry.latency_ms.toFixed(1) : '1.0');
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "circuit-pill" },
    ...{ class: (__VLS_ctx.circuitClass) },
});
(__VLS_ctx.telemetry.circuit_state || 'CLOSED');
const __VLS_20 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_21 = __VLS_asFunctionalComponent(__VLS_20, new __VLS_20({
    name: "popover-fade",
}));
const __VLS_22 = __VLS_21({
    name: "popover-fade",
}, ...__VLS_functionalComponentArgsRest(__VLS_21));
__VLS_23.slots.default;
if (__VLS_ctx.showTelemetryPopover) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telemetry-popover-card" },
        id: "telemetry-popover-card",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "popover-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "popover-title" },
    });
    const __VLS_24 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_25 = __VLS_asFunctionalComponent(__VLS_24, new __VLS_24({}));
    const __VLS_26 = __VLS_25({}, ...__VLS_functionalComponentArgsRest(__VLS_25));
    __VLS_27.slots.default;
    const __VLS_28 = {}.DataAnalysis;
    /** @type {[typeof __VLS_components.DataAnalysis, ]} */ ;
    // @ts-ignore
    const __VLS_29 = __VLS_asFunctionalComponent(__VLS_28, new __VLS_28({}));
    const __VLS_30 = __VLS_29({}, ...__VLS_functionalComponentArgsRest(__VLS_29));
    var __VLS_27;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showTelemetryPopover))
                    return;
                __VLS_ctx.showTelemetryPopover = false;
            } },
        ...{ class: "popover-close-btn" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telemetry-grid" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telemetry-metric-item" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "metric-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "metric-value highlight" },
    });
    (__VLS_ctx.telemetry.active_provider);
    (__VLS_ctx.telemetry.active_model);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telemetry-metric-item" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "metric-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "metric-value" },
        ...{ class: (__VLS_ctx.circuitClass) },
    });
    (__VLS_ctx.telemetry.circuit_state === 'CLOSED' ? 'CLOSED (熔断器闭合 · 就绪)' : __VLS_ctx.telemetry.circuit_state === 'OPEN' ? 'OPEN (触发熔断 · 降级保护)' : 'HALF-OPEN (半开试探中)');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telemetry-metric-item" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "metric-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "metric-value" },
    });
    (__VLS_ctx.telemetry.latency_ms);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telemetry-metric-item" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "metric-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "metric-value" },
    });
    (__VLS_ctx.formatUptime(__VLS_ctx.telemetry.uptime_seconds));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telemetry-metric-item" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "metric-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "metric-value" },
    });
    (__VLS_ctx.telemetry.pending_reviews_count);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telemetry-metric-item" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "metric-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "metric-value" },
    });
    (__VLS_ctx.telemetry.consecutive_failures || 0);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "popover-footer" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.fetchTelemetry) },
        type: "button",
        ...{ class: "refresh-telemetry-btn" },
        disabled: (__VLS_ctx.isFetchingTelemetry),
    });
    const __VLS_32 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_33 = __VLS_asFunctionalComponent(__VLS_32, new __VLS_32({
        ...{ class: ({ 'is-loading': __VLS_ctx.isFetchingTelemetry }) },
    }));
    const __VLS_34 = __VLS_33({
        ...{ class: ({ 'is-loading': __VLS_ctx.isFetchingTelemetry }) },
    }, ...__VLS_functionalComponentArgsRest(__VLS_33));
    __VLS_35.slots.default;
    const __VLS_36 = {}.Refresh;
    /** @type {[typeof __VLS_components.Refresh, ]} */ ;
    // @ts-ignore
    const __VLS_37 = __VLS_asFunctionalComponent(__VLS_36, new __VLS_36({}));
    const __VLS_38 = __VLS_37({}, ...__VLS_functionalComponentArgsRest(__VLS_37));
    var __VLS_35;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.isFetchingTelemetry ? '刷新遥测中...' : '即刻刷新遥测状态');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.openEngineModal) },
        type: "button",
        ...{ class: "configure-engine-btn" },
    });
    const __VLS_40 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_41 = __VLS_asFunctionalComponent(__VLS_40, new __VLS_40({}));
    const __VLS_42 = __VLS_41({}, ...__VLS_functionalComponentArgsRest(__VLS_41));
    __VLS_43.slots.default;
    const __VLS_44 = {}.Setting;
    /** @type {[typeof __VLS_components.Setting, ]} */ ;
    // @ts-ignore
    const __VLS_45 = __VLS_asFunctionalComponent(__VLS_44, new __VLS_44({}));
    const __VLS_46 = __VLS_45({}, ...__VLS_functionalComponentArgsRest(__VLS_45));
    var __VLS_43;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
var __VLS_23;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "header-right" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "skylight-wrap" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.toggleSkylightDrawer) },
    type: "button",
    ...{ class: "skylight-btn" },
    id: "admin-notification-skylight-btn",
    ...{ class: ({ active: __VLS_ctx.showSkylightDrawer }) },
    title: "查看全局通知与中台待办",
});
const __VLS_48 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_49 = __VLS_asFunctionalComponent(__VLS_48, new __VLS_48({
    size: (16),
}));
const __VLS_50 = __VLS_49({
    size: (16),
}, ...__VLS_functionalComponentArgsRest(__VLS_49));
__VLS_51.slots.default;
const __VLS_52 = {}.Bell;
/** @type {[typeof __VLS_components.Bell, ]} */ ;
// @ts-ignore
const __VLS_53 = __VLS_asFunctionalComponent(__VLS_52, new __VLS_52({}));
const __VLS_54 = __VLS_53({}, ...__VLS_functionalComponentArgsRest(__VLS_53));
var __VLS_51;
if (__VLS_ctx.notificationBadgeCount > 0) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "skylight-badge-count" },
    });
    (__VLS_ctx.notificationBadgeCount > 99 ? '99+' : __VLS_ctx.notificationBadgeCount);
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "theme-switch-pill" },
    id: "theme-switch-control",
    title: "切换明暗色彩主题 (浅色/深色/跟随系统)",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.toggleTheme('light');
        } },
    type: "button",
    ...{ class: "theme-icon-btn" },
    ...{ class: ({ active: __VLS_ctx.currentTheme === 'light' }) },
    id: "btn-theme-light",
    title: "明亮白天模式",
});
const __VLS_56 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_57 = __VLS_asFunctionalComponent(__VLS_56, new __VLS_56({
    size: (14),
}));
const __VLS_58 = __VLS_57({
    size: (14),
}, ...__VLS_functionalComponentArgsRest(__VLS_57));
__VLS_59.slots.default;
const __VLS_60 = {}.Sunny;
/** @type {[typeof __VLS_components.Sunny, ]} */ ;
// @ts-ignore
const __VLS_61 = __VLS_asFunctionalComponent(__VLS_60, new __VLS_60({}));
const __VLS_62 = __VLS_61({}, ...__VLS_functionalComponentArgsRest(__VLS_61));
var __VLS_59;
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.toggleTheme('dark');
        } },
    type: "button",
    ...{ class: "theme-icon-btn" },
    ...{ class: ({ active: __VLS_ctx.currentTheme === 'dark' }) },
    id: "btn-theme-dark",
    title: "深色暗黑模式",
});
const __VLS_64 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_65 = __VLS_asFunctionalComponent(__VLS_64, new __VLS_64({
    size: (14),
}));
const __VLS_66 = __VLS_65({
    size: (14),
}, ...__VLS_functionalComponentArgsRest(__VLS_65));
__VLS_67.slots.default;
const __VLS_68 = {}.Moon;
/** @type {[typeof __VLS_components.Moon, ]} */ ;
// @ts-ignore
const __VLS_69 = __VLS_asFunctionalComponent(__VLS_68, new __VLS_68({}));
const __VLS_70 = __VLS_69({}, ...__VLS_functionalComponentArgsRest(__VLS_69));
var __VLS_67;
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.toggleTheme('system');
        } },
    type: "button",
    ...{ class: "theme-icon-btn" },
    ...{ class: ({ active: __VLS_ctx.currentTheme === 'system' }) },
    id: "btn-theme-system",
    title: "跟随操作系统自动切换",
});
const __VLS_72 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_73 = __VLS_asFunctionalComponent(__VLS_72, new __VLS_72({
    size: (14),
}));
const __VLS_74 = __VLS_73({
    size: (14),
}, ...__VLS_functionalComponentArgsRest(__VLS_73));
__VLS_75.slots.default;
const __VLS_76 = {}.Monitor;
/** @type {[typeof __VLS_components.Monitor, ]} */ ;
// @ts-ignore
const __VLS_77 = __VLS_asFunctionalComponent(__VLS_76, new __VLS_76({}));
const __VLS_78 = __VLS_77({}, ...__VLS_functionalComponentArgsRest(__VLS_77));
var __VLS_75;
if (__VLS_ctx.mode === 'admin') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.mode === 'admin'))
                    return;
                __VLS_ctx.showSettingsModal = true;
            } },
        type: "button",
        ...{ class: "admin-engine-btn" },
        id: "btn-engine-settings",
        title: "配置全局本地与云端模型引擎",
    });
    const __VLS_80 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_81 = __VLS_asFunctionalComponent(__VLS_80, new __VLS_80({
        ...{ class: "btn-icon" },
    }));
    const __VLS_82 = __VLS_81({
        ...{ class: "btn-icon" },
    }, ...__VLS_functionalComponentArgsRest(__VLS_81));
    __VLS_83.slots.default;
    const __VLS_84 = {}.Setting;
    /** @type {[typeof __VLS_components.Setting, ]} */ ;
    // @ts-ignore
    const __VLS_85 = __VLS_asFunctionalComponent(__VLS_84, new __VLS_84({}));
    const __VLS_86 = __VLS_85({}, ...__VLS_functionalComponentArgsRest(__VLS_85));
    var __VLS_83;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "admin-profile-wrapper" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ onClick: (__VLS_ctx.toggleProfileMenu) },
    ...{ class: "admin-profile-chip" },
    id: "admin-profile-chip",
    title: "管理人员身份与工作台切换",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
    src: (__VLS_ctx.userAvatar),
    ...{ class: "chip-avatar" },
    id: "admin-avatar-img",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "chip-info" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "chip-name" },
    id: "admin-display-name",
});
(__VLS_ctx.userDisplayName);
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "chip-role" },
    ...{ class: (__VLS_ctx.userRoleClass) },
    id: "admin-role-badge",
});
(__VLS_ctx.userRoleLabel);
const __VLS_88 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_89 = __VLS_asFunctionalComponent(__VLS_88, new __VLS_88({
    size: (12),
    ...{ class: "arrow-icon" },
}));
const __VLS_90 = __VLS_89({
    size: (12),
    ...{ class: "arrow-icon" },
}, ...__VLS_functionalComponentArgsRest(__VLS_89));
__VLS_91.slots.default;
const __VLS_92 = {}.ArrowDown;
/** @type {[typeof __VLS_components.ArrowDown, ]} */ ;
// @ts-ignore
const __VLS_93 = __VLS_asFunctionalComponent(__VLS_92, new __VLS_92({}));
const __VLS_94 = __VLS_93({}, ...__VLS_functionalComponentArgsRest(__VLS_93));
var __VLS_91;
const __VLS_96 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_97 = __VLS_asFunctionalComponent(__VLS_96, new __VLS_96({
    name: "popover-fade",
}));
const __VLS_98 = __VLS_97({
    name: "popover-fade",
}, ...__VLS_functionalComponentArgsRest(__VLS_97));
__VLS_99.slots.default;
if (__VLS_ctx.showProfileMenu) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "profile-dropdown-card" },
        id: "admin-profile-dropdown",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "dropdown-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "user-meta" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "user-name" },
    });
    (__VLS_ctx.userDisplayName);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "user-sub" },
    });
    (__VLS_ctx.currentUser?.username || '未登录');
    (__VLS_ctx.userRoleLabel);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "dropdown-body" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.goToSpectatorHall) },
        type: "button",
        ...{ class: "dropdown-item" },
    });
    const __VLS_100 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_101 = __VLS_asFunctionalComponent(__VLS_100, new __VLS_100({}));
    const __VLS_102 = __VLS_101({}, ...__VLS_functionalComponentArgsRest(__VLS_101));
    __VLS_103.slots.default;
    const __VLS_104 = {}.Film;
    /** @type {[typeof __VLS_components.Film, ]} */ ;
    // @ts-ignore
    const __VLS_105 = __VLS_asFunctionalComponent(__VLS_104, new __VLS_104({}));
    const __VLS_106 = __VLS_105({}, ...__VLS_functionalComponentArgsRest(__VLS_105));
    var __VLS_103;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    if (__VLS_ctx.mode === 'admin') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.goToCreatorStudio) },
            type: "button",
            ...{ class: "dropdown-item" },
        });
        const __VLS_108 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_109 = __VLS_asFunctionalComponent(__VLS_108, new __VLS_108({}));
        const __VLS_110 = __VLS_109({}, ...__VLS_functionalComponentArgsRest(__VLS_109));
        __VLS_111.slots.default;
        const __VLS_112 = {}.VideoCamera;
        /** @type {[typeof __VLS_components.VideoCamera, ]} */ ;
        // @ts-ignore
        const __VLS_113 = __VLS_asFunctionalComponent(__VLS_112, new __VLS_112({}));
        const __VLS_114 = __VLS_113({}, ...__VLS_functionalComponentArgsRest(__VLS_113));
        var __VLS_111;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.goToCreatorBI) },
            type: "button",
            ...{ class: "dropdown-item" },
            id: "btn-creator-goto-bi",
        });
        const __VLS_116 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_117 = __VLS_asFunctionalComponent(__VLS_116, new __VLS_116({}));
        const __VLS_118 = __VLS_117({}, ...__VLS_functionalComponentArgsRest(__VLS_117));
        __VLS_119.slots.default;
        const __VLS_120 = {}.DataAnalysis;
        /** @type {[typeof __VLS_components.DataAnalysis, ]} */ ;
        // @ts-ignore
        const __VLS_121 = __VLS_asFunctionalComponent(__VLS_120, new __VLS_120({}));
        const __VLS_122 = __VLS_121({}, ...__VLS_functionalComponentArgsRest(__VLS_121));
        var __VLS_119;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "dropdown-divider" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.handleLogout) },
        type: "button",
        ...{ class: "dropdown-item logout-item" },
        id: "btn-logout",
    });
    const __VLS_124 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_125 = __VLS_asFunctionalComponent(__VLS_124, new __VLS_124({}));
    const __VLS_126 = __VLS_125({}, ...__VLS_functionalComponentArgsRest(__VLS_125));
    __VLS_127.slots.default;
    const __VLS_128 = {}.SwitchButton;
    /** @type {[typeof __VLS_components.SwitchButton, ]} */ ;
    // @ts-ignore
    const __VLS_129 = __VLS_asFunctionalComponent(__VLS_128, new __VLS_128({}));
    const __VLS_130 = __VLS_129({}, ...__VLS_functionalComponentArgsRest(__VLS_129));
    var __VLS_127;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
var __VLS_99;
const __VLS_132 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_133 = __VLS_asFunctionalComponent(__VLS_132, new __VLS_132({
    name: "skylight-slide",
}));
const __VLS_134 = __VLS_133({
    name: "skylight-slide",
}, ...__VLS_functionalComponentArgsRest(__VLS_133));
__VLS_135.slots.default;
if (__VLS_ctx.showSkylightDrawer) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "notification-skylight-drawer" },
        id: "notification-skyway-drawer",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "skylight-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "skylight-title-box" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "skylight-icon-squircle" },
    });
    const __VLS_136 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_137 = __VLS_asFunctionalComponent(__VLS_136, new __VLS_136({
        size: (16),
    }));
    const __VLS_138 = __VLS_137({
        size: (16),
    }, ...__VLS_functionalComponentArgsRest(__VLS_137));
    __VLS_139.slots.default;
    const __VLS_140 = {}.Bell;
    /** @type {[typeof __VLS_components.Bell, ]} */ ;
    // @ts-ignore
    const __VLS_141 = __VLS_asFunctionalComponent(__VLS_140, new __VLS_140({}));
    const __VLS_142 = __VLS_141({}, ...__VLS_functionalComponentArgsRest(__VLS_141));
    var __VLS_139;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
        ...{ class: "skylight-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "skylight-subtitle" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "skylight-actions" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "skylight-count-pill" },
    });
    (__VLS_ctx.notificationItems.length);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showSkylightDrawer))
                    return;
                __VLS_ctx.showSkylightDrawer = false;
            } },
        ...{ class: "skylight-close-btn" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "skylight-body" },
    });
    for (const [item, idx] of __VLS_getVForSourceType((__VLS_ctx.notificationItems))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            key: (idx),
            ...{ class: "skylight-item-card" },
            ...{ class: (item.level) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "item-left-accent" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "item-content-wrap" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "item-header-row" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "item-category-tag" },
            ...{ class: (item.categoryClass) },
        });
        (item.category);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "item-time-text" },
        });
        (item.time);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h5, __VLS_intrinsicElements.h5)({
            ...{ class: "item-title" },
        });
        (item.title);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "item-desc" },
        });
        (item.description);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "item-action-wrap" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.showSkylightDrawer))
                        return;
                    __VLS_ctx.handleSkylightDirect(item);
                } },
            type: "button",
            ...{ class: "skylight-direct-btn" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        const __VLS_144 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_145 = __VLS_asFunctionalComponent(__VLS_144, new __VLS_144({
            size: (12),
        }));
        const __VLS_146 = __VLS_145({
            size: (12),
        }, ...__VLS_functionalComponentArgsRest(__VLS_145));
        __VLS_147.slots.default;
        const __VLS_148 = {}.ArrowRight;
        /** @type {[typeof __VLS_components.ArrowRight, ]} */ ;
        // @ts-ignore
        const __VLS_149 = __VLS_asFunctionalComponent(__VLS_148, new __VLS_148({}));
        const __VLS_150 = __VLS_149({}, ...__VLS_functionalComponentArgsRest(__VLS_149));
        var __VLS_147;
    }
    if (__VLS_ctx.notificationItems.length === 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "skylight-empty-box" },
        });
        const __VLS_152 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_153 = __VLS_asFunctionalComponent(__VLS_152, new __VLS_152({
            size: (32),
            ...{ class: "empty-icon" },
        }));
        const __VLS_154 = __VLS_153({
            size: (32),
            ...{ class: "empty-icon" },
        }, ...__VLS_functionalComponentArgsRest(__VLS_153));
        __VLS_155.slots.default;
        const __VLS_156 = {}.CircleCheckFilled;
        /** @type {[typeof __VLS_components.CircleCheckFilled, ]} */ ;
        // @ts-ignore
        const __VLS_157 = __VLS_asFunctionalComponent(__VLS_156, new __VLS_156({}));
        const __VLS_158 = __VLS_157({}, ...__VLS_functionalComponentArgsRest(__VLS_157));
        var __VLS_155;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "empty-title" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "empty-desc" },
        });
    }
}
var __VLS_135;
if (__VLS_ctx.showSkylightDrawer || __VLS_ctx.showTelemetryPopover || __VLS_ctx.showProfileMenu) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ onClick: (__VLS_ctx.closeAllOverlays) },
        ...{ class: "admin-header-backdrop" },
    });
}
/** @type {[typeof EngineSettingsModal, ]} */ ;
// @ts-ignore
const __VLS_160 = __VLS_asFunctionalComponent(EngineSettingsModal, new EngineSettingsModal({
    ...{ 'onUpdated': {} },
    modelValue: (__VLS_ctx.showSettingsModal),
}));
const __VLS_161 = __VLS_160({
    ...{ 'onUpdated': {} },
    modelValue: (__VLS_ctx.showSettingsModal),
}, ...__VLS_functionalComponentArgsRest(__VLS_160));
let __VLS_163;
let __VLS_164;
let __VLS_165;
const __VLS_166 = {
    onUpdated: (__VLS_ctx.onEngineConfigUpdated)
};
var __VLS_162;
/** @type {__VLS_StyleScopedClasses['apple-admin-header']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-header-inner']} */ ;
/** @type {__VLS_StyleScopedClasses['header-left']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-brand-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-icon-squircle']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-text-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-title']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-caption']} */ ;
/** @type {__VLS_StyleScopedClasses['cluster-env-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['cluster-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['header-breadcrumb']} */ ;
/** @type {__VLS_StyleScopedClasses['breadcrumb-sep']} */ ;
/** @type {__VLS_StyleScopedClasses['breadcrumb-current']} */ ;
/** @type {__VLS_StyleScopedClasses['header-center']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-capsule']} */ ;
/** @type {__VLS_StyleScopedClasses['health-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['health-status-text']} */ ;
/** @type {__VLS_StyleScopedClasses['capsule-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['model-badge-inline']} */ ;
/** @type {__VLS_StyleScopedClasses['model-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['model-name-text']} */ ;
/** @type {__VLS_StyleScopedClasses['latency-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['circuit-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-popover-card']} */ ;
/** @type {__VLS_StyleScopedClasses['popover-header']} */ ;
/** @type {__VLS_StyleScopedClasses['popover-title']} */ ;
/** @type {__VLS_StyleScopedClasses['popover-close-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-metric-item']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-label']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-value']} */ ;
/** @type {__VLS_StyleScopedClasses['highlight']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-metric-item']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-label']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-value']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-metric-item']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-label']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-value']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-metric-item']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-label']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-value']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-metric-item']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-label']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-value']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-metric-item']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-label']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-value']} */ ;
/** @type {__VLS_StyleScopedClasses['popover-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['refresh-telemetry-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['configure-engine-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['header-right']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-badge-count']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-switch-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-engine-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-profile-wrapper']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-profile-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-avatar']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-info']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-name']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-role']} */ ;
/** @type {__VLS_StyleScopedClasses['arrow-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['profile-dropdown-card']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-header']} */ ;
/** @type {__VLS_StyleScopedClasses['user-meta']} */ ;
/** @type {__VLS_StyleScopedClasses['user-name']} */ ;
/** @type {__VLS_StyleScopedClasses['user-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-body']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-item']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-item']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-item']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-item']} */ ;
/** @type {__VLS_StyleScopedClasses['logout-item']} */ ;
/** @type {__VLS_StyleScopedClasses['notification-skylight-drawer']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-header']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-title-box']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-icon-squircle']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-title']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-subtitle']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-count-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-close-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-body']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-item-card']} */ ;
/** @type {__VLS_StyleScopedClasses['item-left-accent']} */ ;
/** @type {__VLS_StyleScopedClasses['item-content-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['item-header-row']} */ ;
/** @type {__VLS_StyleScopedClasses['item-category-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['item-time-text']} */ ;
/** @type {__VLS_StyleScopedClasses['item-title']} */ ;
/** @type {__VLS_StyleScopedClasses['item-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['item-action-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-direct-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-empty-box']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-title']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-header-backdrop']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            Sunny: Sunny,
            Moon: Moon,
            Monitor: Monitor,
            Setting: Setting,
            Platform: Platform,
            VideoCamera: VideoCamera,
            Cpu: Cpu,
            DataAnalysis: DataAnalysis,
            Refresh: Refresh,
            Bell: Bell,
            ArrowDown: ArrowDown,
            ArrowRight: ArrowRight,
            Film: Film,
            SwitchButton: SwitchButton,
            CircleCheckFilled: CircleCheckFilled,
            EngineSettingsModal: EngineSettingsModal,
            currentUser: currentUser,
            userAvatar: userAvatar,
            userDisplayName: userDisplayName,
            userRoleLabel: userRoleLabel,
            userRoleClass: userRoleClass,
            currentTheme: currentTheme,
            toggleTheme: toggleTheme,
            showTelemetryPopover: showTelemetryPopover,
            showSkylightDrawer: showSkylightDrawer,
            showProfileMenu: showProfileMenu,
            showSettingsModal: showSettingsModal,
            closeAllOverlays: closeAllOverlays,
            toggleTelemetryPopover: toggleTelemetryPopover,
            toggleSkylightDrawer: toggleSkylightDrawer,
            toggleProfileMenu: toggleProfileMenu,
            telemetry: telemetry,
            isFetchingTelemetry: isFetchingTelemetry,
            fetchTelemetry: fetchTelemetry,
            latencyClass: latencyClass,
            circuitClass: circuitClass,
            formatUptime: formatUptime,
            openEngineModal: openEngineModal,
            onEngineConfigUpdated: onEngineConfigUpdated,
            activeTabTitle: activeTabTitle,
            notificationItems: notificationItems,
            notificationBadgeCount: notificationBadgeCount,
            handleSkylightDirect: handleSkylightDirect,
            goToSpectatorHall: goToSpectatorHall,
            goToCreatorStudio: goToCreatorStudio,
            goToCreatorBI: goToCreatorBI,
            handleLogout: handleLogout,
        };
    },
    __typeEmits: {},
    __typeProps: {},
    props: {},
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
    __typeEmits: {},
    __typeProps: {},
    props: {},
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=AdminHeader.vue.js.map