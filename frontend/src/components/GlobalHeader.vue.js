/// <reference types="../../node_modules/.vue-global-types/vue_3.5_0_0_0.d.ts" />
import { ref, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { authApi } from '../api/auth';
import { notificationApi } from '../api/user';
import { useUserStore } from '../stores/user';
import { Sunny, Moon, Monitor, Setting, Upload, Film, Lock, Warning, Bell } from '@element-plus/icons-vue';
import EngineSettingsModal from './EngineSettingsModal.vue';
import NotificationSkylight from './NotificationSkylight.vue';
const emit = defineEmits();
const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const defaultAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=apple';
const searchKeyword = ref('');
const currentUser = userStore.currentUser;
const showAuthModal = ref(false);
const showSettingsModal = ref(false);
const showSkylightDrawer = ref(false);
const unreadCounts = ref({ total: 0, announcements: 0, replies: 0, likes: 0 });
const authMode = ref('login');
const modalHintText = ref('');
const authError = ref('');
const isSubmitting = ref(false);
const currentTheme = ref('system');
async function fetchUnreadCount() {
    const token = localStorage.getItem('cinema_access_token') || localStorage.getItem('token');
    if (!token) {
        unreadCounts.value = { total: 0, announcements: 0, replies: 0, likes: 0 };
        return;
    }
    try {
        const res = await notificationApi.getUnreadCount();
        if (res?.data) {
            unreadCounts.value = res.data;
        }
    }
    catch (err) {
        // ignore
    }
}
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
const onModelEngineUpdated = (cfg) => {
    console.log('Active model engine updated:', cfg);
};
const authForm = ref({
    username: '',
    password: '',
    nickname: '',
    role: 'USER'
});
onMounted(async () => {
    const saved = localStorage.getItem('cinema_theme') || 'system';
    currentTheme.value = saved;
    await userStore.refreshProfile();
    emit('userChanged', currentUser.value);
    await fetchUnreadCount();
});
watch(() => route.path, async () => {
    await userStore.refreshProfile();
    emit('userChanged', currentUser.value);
    await fetchUnreadCount();
});
async function restoreUserSession() {
    const profile = await userStore.refreshProfile();
    emit('userChanged', profile);
    await fetchUnreadCount();
    return profile;
}
function handleSearch() {
    emit('search', searchKeyword.value.trim());
}
function getRoleLabel(role) {
    const map = {
        USER: '普通用户',
        CREATOR: '创作者',
        REVIEWER: '审核员',
        ADMIN: '管理员'
    };
    return map[role] || role;
}
async function switchRole(roleName) {
    try {
        const res = await authApi.quickSwitch(roleName);
        const token = res?.access_token || res?.data?.access_token;
        const userObj = res?.user || res?.data?.user;
        if (token && userObj) {
            userStore.setUser(userObj, token);
            emit('userChanged', userObj);
            window.location.reload();
        }
    }
    catch (err) {
        console.error('Failed to switch demo role via quickSwitch:', err);
    }
}
function openAuthModal(hint = '') {
    modalHintText.value = hint;
    authError.value = '';
    authForm.value = {
        username: '',
        password: '',
        nickname: '',
        role: 'USER'
    };
    showAuthModal.value = true;
}
function fillQuickAccount(u, p) {
    authForm.value.username = u;
    authForm.value.password = p;
    authMode.value = 'login';
}
async function handleAuthSubmit() {
    authError.value = '';
    isSubmitting.value = true;
    try {
        if (authMode.value === 'login') {
            const res = await authApi.login({
                username: authForm.value.username.trim(),
                password: authForm.value.password.trim()
            });
            const token = res?.access_token || res?.data?.access_token;
            const userObj = res?.user || res?.data?.user;
            if (token) {
                if (userObj) {
                    userStore.setUser(userObj, token);
                }
                emit('userChanged', currentUser.value);
                showAuthModal.value = false;
            }
            else {
                authError.value = res?.message || '登录失败，请检查账号密码';
            }
        }
        else {
            const res = await authApi.register({
                username: authForm.value.username.trim(),
                password: authForm.value.password.trim(),
                nickname: authForm.value.nickname.trim() || undefined,
                role: authForm.value.role
            });
            const token = res?.access_token || res?.data?.access_token;
            const userObj = res?.user || res?.data?.user;
            if (token) {
                if (userObj) {
                    userStore.setUser(userObj, token);
                }
                emit('userChanged', currentUser.value);
                showAuthModal.value = false;
            }
            else {
                authError.value = res?.message || '注册失败';
            }
        }
    }
    catch (err) {
        authError.value = err.response?.data?.detail || err.message || '网络请求错误';
    }
    finally {
        isSubmitting.value = false;
    }
}
function handleLogout() {
    userStore.clearUser();
    emit('userChanged', null);
    window.location.href = '/';
}
function handleCreatorUpload() {
    router.push('/creator');
}
const __VLS_exposed = {
    openAuthModal,
    restoreUserSession
};
defineExpose(__VLS_exposed);
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['apple-logo-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-item']} */ ;
/** @type {__VLS_StyleScopedClasses['search-capsule-box']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-search-input']} */ ;
/** @type {__VLS_StyleScopedClasses['search-submit-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['segment-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['segment-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-item']} */ ;
/** @type {__VLS_StyleScopedClasses['segment-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-secondary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-settings-trigger-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-settings-trigger-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-publish-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-bell-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['user-profile-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['user-profile-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['user-profile-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['user-profile-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['user-profile-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['user-profile-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['user-profile-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-name']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-role']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-role']} */ ;
/** @type {__VLS_StyleScopedClasses['user']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-role']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-role']} */ ;
/** @type {__VLS_StyleScopedClasses['creator']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-role']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-role']} */ ;
/** @type {__VLS_StyleScopedClasses['reviewer']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-role']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-role']} */ ;
/** @type {__VLS_StyleScopedClasses['admin']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-logout-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-logout-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-close-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['role-option-label']} */ ;
/** @type {__VLS_StyleScopedClasses['helper-pill']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.header, __VLS_intrinsicElements.header)({
    ...{ class: "apple-global-header" },
    id: "bili-global-header",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "header-inner" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "header-left" },
});
const __VLS_0 = {}.RouterLink;
/** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    to: "/",
    ...{ class: "apple-logo-badge" },
    id: "nav-logo-link",
}));
const __VLS_2 = __VLS_1({
    to: "/",
    ...{ class: "apple-logo-badge" },
    id: "nav-logo-link",
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
__VLS_3.slots.default;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "logo-icon-squircle" },
});
const __VLS_4 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_5 = __VLS_asFunctionalComponent(__VLS_4, new __VLS_4({
    size: (18),
}));
const __VLS_6 = __VLS_5({
    size: (18),
}, ...__VLS_functionalComponentArgsRest(__VLS_5));
__VLS_7.slots.default;
const __VLS_8 = {}.Film;
/** @type {[typeof __VLS_components.Film, ]} */ ;
// @ts-ignore
const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({}));
const __VLS_10 = __VLS_9({}, ...__VLS_functionalComponentArgsRest(__VLS_9));
var __VLS_7;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "logo-text-wrap" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "logo-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "logo-caption" },
});
var __VLS_3;
__VLS_asFunctionalElement(__VLS_intrinsicElements.nav, __VLS_intrinsicElements.nav)({
    ...{ class: "header-nav" },
});
const __VLS_12 = {}.RouterLink;
/** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
// @ts-ignore
const __VLS_13 = __VLS_asFunctionalComponent(__VLS_12, new __VLS_12({
    to: "/landing",
    ...{ class: "nav-item" },
    activeClass: "active",
}));
const __VLS_14 = __VLS_13({
    to: "/landing",
    ...{ class: "nav-item" },
    activeClass: "active",
}, ...__VLS_functionalComponentArgsRest(__VLS_13));
__VLS_15.slots.default;
var __VLS_15;
const __VLS_16 = {}.RouterLink;
/** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
// @ts-ignore
const __VLS_17 = __VLS_asFunctionalComponent(__VLS_16, new __VLS_16({
    to: "/",
    ...{ class: "nav-item" },
    activeClass: "active",
}));
const __VLS_18 = __VLS_17({
    to: "/",
    ...{ class: "nav-item" },
    activeClass: "active",
}, ...__VLS_functionalComponentArgsRest(__VLS_17));
__VLS_19.slots.default;
var __VLS_19;
const __VLS_20 = {}.RouterLink;
/** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
// @ts-ignore
const __VLS_21 = __VLS_asFunctionalComponent(__VLS_20, new __VLS_20({
    to: "/creator",
    ...{ class: "nav-item" },
    activeClass: "active",
}));
const __VLS_22 = __VLS_21({
    to: "/creator",
    ...{ class: "nav-item" },
    activeClass: "active",
}, ...__VLS_functionalComponentArgsRest(__VLS_21));
__VLS_23.slots.default;
var __VLS_23;
const __VLS_24 = {}.RouterLink;
/** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
// @ts-ignore
const __VLS_25 = __VLS_asFunctionalComponent(__VLS_24, new __VLS_24({
    to: "/user/space",
    ...{ class: "nav-item user-space-link" },
    activeClass: "active",
}));
const __VLS_26 = __VLS_25({
    to: "/user/space",
    ...{ class: "nav-item user-space-link" },
    activeClass: "active",
}, ...__VLS_functionalComponentArgsRest(__VLS_25));
__VLS_27.slots.default;
var __VLS_27;
if (__VLS_ctx.currentUser?.role === 'ADMIN') {
    const __VLS_28 = {}.RouterLink;
    /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
    // @ts-ignore
    const __VLS_29 = __VLS_asFunctionalComponent(__VLS_28, new __VLS_28({
        to: "/admin",
        ...{ class: "nav-item admin-nav-link" },
        activeClass: "active",
    }));
    const __VLS_30 = __VLS_29({
        to: "/admin",
        ...{ class: "nav-item admin-nav-link" },
        activeClass: "active",
    }, ...__VLS_functionalComponentArgsRest(__VLS_29));
    __VLS_31.slots.default;
    var __VLS_31;
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "header-center" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "search-capsule-box" },
    id: "header-search-bar",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({
    viewBox: "0 0 24 24",
    ...{ class: "search-prefix-icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.path)({
    fill: "currentColor",
    d: "M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ onKeyup: (__VLS_ctx.handleSearch) },
    value: (__VLS_ctx.searchKeyword),
    type: "text",
    id: "home-search-input",
    ...{ class: "apple-search-input" },
    placeholder: "搜索短剧、镜头秒数、台词或题材...",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.handleSearch) },
    ...{ class: "search-submit-btn" },
    id: "btn-search",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "header-right" },
});
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
const __VLS_32 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_33 = __VLS_asFunctionalComponent(__VLS_32, new __VLS_32({
    size: (14),
}));
const __VLS_34 = __VLS_33({
    size: (14),
}, ...__VLS_functionalComponentArgsRest(__VLS_33));
__VLS_35.slots.default;
const __VLS_36 = {}.Sunny;
/** @type {[typeof __VLS_components.Sunny, ]} */ ;
// @ts-ignore
const __VLS_37 = __VLS_asFunctionalComponent(__VLS_36, new __VLS_36({}));
const __VLS_38 = __VLS_37({}, ...__VLS_functionalComponentArgsRest(__VLS_37));
var __VLS_35;
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
const __VLS_40 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_41 = __VLS_asFunctionalComponent(__VLS_40, new __VLS_40({
    size: (14),
}));
const __VLS_42 = __VLS_41({
    size: (14),
}, ...__VLS_functionalComponentArgsRest(__VLS_41));
__VLS_43.slots.default;
const __VLS_44 = {}.Moon;
/** @type {[typeof __VLS_components.Moon, ]} */ ;
// @ts-ignore
const __VLS_45 = __VLS_asFunctionalComponent(__VLS_44, new __VLS_44({}));
const __VLS_46 = __VLS_45({}, ...__VLS_functionalComponentArgsRest(__VLS_45));
var __VLS_43;
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
const __VLS_48 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_49 = __VLS_asFunctionalComponent(__VLS_48, new __VLS_48({
    size: (14),
}));
const __VLS_50 = __VLS_49({
    size: (14),
}, ...__VLS_functionalComponentArgsRest(__VLS_49));
__VLS_51.slots.default;
const __VLS_52 = {}.Monitor;
/** @type {[typeof __VLS_components.Monitor, ]} */ ;
// @ts-ignore
const __VLS_53 = __VLS_asFunctionalComponent(__VLS_52, new __VLS_52({}));
const __VLS_54 = __VLS_53({}, ...__VLS_functionalComponentArgsRest(__VLS_53));
var __VLS_51;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "skylight-trigger-wrap" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.showSkylightDrawer = !__VLS_ctx.showSkylightDrawer;
        } },
    type: "button",
    ...{ class: "skylight-bell-btn" },
    id: "btn-notification-skylight",
    title: "通知天窗",
});
const __VLS_56 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_57 = __VLS_asFunctionalComponent(__VLS_56, new __VLS_56({
    size: (16),
}));
const __VLS_58 = __VLS_57({
    size: (16),
}, ...__VLS_functionalComponentArgsRest(__VLS_57));
__VLS_59.slots.default;
const __VLS_60 = {}.Bell;
/** @type {[typeof __VLS_components.Bell, ]} */ ;
// @ts-ignore
const __VLS_61 = __VLS_asFunctionalComponent(__VLS_60, new __VLS_60({}));
const __VLS_62 = __VLS_61({}, ...__VLS_functionalComponentArgsRest(__VLS_61));
var __VLS_59;
if (__VLS_ctx.unreadCounts.total > 0) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "skylight-unread-badge" },
        id: "skylight-unread-badge",
    });
    (__VLS_ctx.unreadCounts.total > 99 ? '99+' : __VLS_ctx.unreadCounts.total);
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "user-state-area" },
});
if (__VLS_ctx.currentUser) {
    const __VLS_64 = {}.RouterLink;
    /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
    // @ts-ignore
    const __VLS_65 = __VLS_asFunctionalComponent(__VLS_64, new __VLS_64({
        to: "/user/space",
        ...{ class: "user-profile-chip" },
        id: "user-profile-badge",
        title: "前往个人空间",
    }));
    const __VLS_66 = __VLS_65({
        to: "/user/space",
        ...{ class: "user-profile-chip" },
        id: "user-profile-badge",
        title: "前往个人空间",
    }, ...__VLS_functionalComponentArgsRest(__VLS_65));
    __VLS_67.slots.default;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
        src: (__VLS_ctx.currentUser.avatar_url || __VLS_ctx.defaultAvatar),
        ...{ class: "chip-avatar" },
        id: "user-avatar-img",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "chip-info" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "chip-name" },
        id: "user-display-name",
    });
    (__VLS_ctx.currentUser.nickname || __VLS_ctx.currentUser.username);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "chip-role" },
        ...{ class: (__VLS_ctx.currentUser.role.toLowerCase()) },
        id: "user-role-badge",
    });
    (__VLS_ctx.getRoleLabel(__VLS_ctx.currentUser.role));
    var __VLS_67;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.handleLogout) },
        ...{ class: "apple-secondary-btn chip-logout-btn" },
        id: "btn-logout",
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "guest-label-pill" },
        id: "guest-badge",
    });
    const __VLS_68 = {}.RouterLink;
    /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
    // @ts-ignore
    const __VLS_69 = __VLS_asFunctionalComponent(__VLS_68, new __VLS_68({
        to: "/login",
        ...{ class: "apple-primary-btn" },
        id: "btn-open-login",
    }));
    const __VLS_70 = __VLS_69({
        to: "/login",
        ...{ class: "apple-primary-btn" },
        id: "btn-open-login",
    }, ...__VLS_functionalComponentArgsRest(__VLS_69));
    __VLS_71.slots.default;
    var __VLS_71;
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.showSettingsModal = true;
        } },
    type: "button",
    ...{ class: "engine-settings-trigger-btn" },
    id: "btn-engine-settings",
    title: "配置本地/云端模型引擎",
});
const __VLS_72 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_73 = __VLS_asFunctionalComponent(__VLS_72, new __VLS_72({
    ...{ class: "btn-icon" },
}));
const __VLS_74 = __VLS_73({
    ...{ class: "btn-icon" },
}, ...__VLS_functionalComponentArgsRest(__VLS_73));
__VLS_75.slots.default;
const __VLS_76 = {}.Setting;
/** @type {[typeof __VLS_components.Setting, ]} */ ;
// @ts-ignore
const __VLS_77 = __VLS_asFunctionalComponent(__VLS_76, new __VLS_76({}));
const __VLS_78 = __VLS_77({}, ...__VLS_functionalComponentArgsRest(__VLS_77));
var __VLS_75;
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.handleCreatorUpload) },
    ...{ class: "apple-primary-btn creator-publish-btn" },
    id: "btn-creator-upload",
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
const __VLS_84 = {}.Upload;
/** @type {[typeof __VLS_components.Upload, ]} */ ;
// @ts-ignore
const __VLS_85 = __VLS_asFunctionalComponent(__VLS_84, new __VLS_84({}));
const __VLS_86 = __VLS_85({}, ...__VLS_functionalComponentArgsRest(__VLS_85));
var __VLS_83;
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
const __VLS_88 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_89 = __VLS_asFunctionalComponent(__VLS_88, new __VLS_88({
    name: "apple-modal-fade",
}));
const __VLS_90 = __VLS_89({
    name: "apple-modal-fade",
}, ...__VLS_functionalComponentArgsRest(__VLS_89));
__VLS_91.slots.default;
if (__VLS_ctx.showAuthModal) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showAuthModal))
                    return;
                __VLS_ctx.showAuthModal = false;
            } },
        ...{ class: "apple-modal-backdrop" },
        id: "modal-auth-backdrop",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "apple-modal-card" },
        id: "modal-auth-card",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-card-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-title-wrap" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-icon-squircle" },
    });
    const __VLS_92 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_93 = __VLS_asFunctionalComponent(__VLS_92, new __VLS_92({
        size: (20),
    }));
    const __VLS_94 = __VLS_93({
        size: (20),
    }, ...__VLS_functionalComponentArgsRest(__VLS_93));
    __VLS_95.slots.default;
    const __VLS_96 = {}.Lock;
    /** @type {[typeof __VLS_components.Lock, ]} */ ;
    // @ts-ignore
    const __VLS_97 = __VLS_asFunctionalComponent(__VLS_96, new __VLS_96({}));
    const __VLS_98 = __VLS_97({}, ...__VLS_functionalComponentArgsRest(__VLS_97));
    var __VLS_95;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "modal-title" },
    });
    (__VLS_ctx.authMode === 'login' ? '账号登录' : '注册新账号');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "modal-subtitle" },
    });
    (__VLS_ctx.modalHintText || '登录后畅享全部互动点赞与 AI 伴读特权');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showAuthModal))
                    return;
                __VLS_ctx.showAuthModal = false;
            } },
        ...{ class: "modal-close-icon-btn" },
        id: "btn-close-auth-modal",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-tab-segment" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showAuthModal))
                    return;
                __VLS_ctx.authMode = 'login';
            } },
        ...{ class: "tab-btn" },
        ...{ class: ({ active: __VLS_ctx.authMode === 'login' }) },
        id: "tab-switch-login",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showAuthModal))
                    return;
                __VLS_ctx.authMode = 'register';
            } },
        ...{ class: "tab-btn" },
        ...{ class: ({ active: __VLS_ctx.authMode === 'register' }) },
        id: "tab-switch-register",
    });
    if (__VLS_ctx.authError) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "modal-error-banner" },
            id: "auth-error-msg",
        });
        const __VLS_100 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_101 = __VLS_asFunctionalComponent(__VLS_100, new __VLS_100({
            ...{ class: "err-icon" },
        }));
        const __VLS_102 = __VLS_101({
            ...{ class: "err-icon" },
        }, ...__VLS_functionalComponentArgsRest(__VLS_101));
        __VLS_103.slots.default;
        const __VLS_104 = {}.Warning;
        /** @type {[typeof __VLS_components.Warning, ]} */ ;
        // @ts-ignore
        const __VLS_105 = __VLS_asFunctionalComponent(__VLS_104, new __VLS_104({}));
        const __VLS_106 = __VLS_105({}, ...__VLS_functionalComponentArgsRest(__VLS_105));
        var __VLS_103;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (__VLS_ctx.authError);
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.form, __VLS_intrinsicElements.form)({
        ...{ onSubmit: (__VLS_ctx.handleAuthSubmit) },
        ...{ class: "modal-form" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-field-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "field-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        value: (__VLS_ctx.authForm.username),
        type: "text",
        id: "input-auth-username",
        ...{ class: "apple-form-input" },
        placeholder: "请输入用户名（如 cinema_fan）",
        required: true,
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-field-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "field-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        type: "password",
        id: "input-auth-password",
        ...{ class: "apple-form-input" },
        placeholder: "请输入密码（不少于 6 位）",
        required: true,
    });
    (__VLS_ctx.authForm.password);
    if (__VLS_ctx.authMode === 'register') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "form-field-group" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "field-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            value: (__VLS_ctx.authForm.nickname),
            type: "text",
            id: "input-auth-nickname",
            ...{ class: "apple-form-input" },
            placeholder: "您的专属剧迷昵称",
        });
    }
    if (__VLS_ctx.authMode === 'register') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "form-field-group" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "field-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "role-select-grid" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "role-option-label" },
            ...{ class: ({ selected: __VLS_ctx.authForm.role === 'USER' }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            type: "radio",
            value: "USER",
        });
        (__VLS_ctx.authForm.role);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "role-option-label" },
            ...{ class: ({ selected: __VLS_ctx.authForm.role === 'CREATOR' }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            type: "radio",
            value: "CREATOR",
        });
        (__VLS_ctx.authForm.role);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-actions-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        type: "submit",
        ...{ class: "apple-primary-btn modal-submit-btn" },
        id: "btn-submit-auth",
        disabled: (__VLS_ctx.isSubmitting),
    });
    (__VLS_ctx.isSubmitting ? '正在验证中...' : (__VLS_ctx.authMode === 'login' ? '立即登录' : '完成注册并登录'));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "test-accounts-helper" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "helper-caption" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "helper-pills-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showAuthModal))
                    return;
                __VLS_ctx.fillQuickAccount('user', 'user123');
            } },
        ...{ class: "helper-pill" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showAuthModal))
                    return;
                __VLS_ctx.fillQuickAccount('creator', 'creator123');
            } },
        ...{ class: "helper-pill" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showAuthModal))
                    return;
                __VLS_ctx.fillQuickAccount('reviewer', 'reviewer123');
            } },
        ...{ class: "helper-pill" },
    });
}
var __VLS_91;
/** @type {[typeof EngineSettingsModal, ]} */ ;
// @ts-ignore
const __VLS_108 = __VLS_asFunctionalComponent(EngineSettingsModal, new EngineSettingsModal({
    ...{ 'onUpdated': {} },
    modelValue: (__VLS_ctx.showSettingsModal),
}));
const __VLS_109 = __VLS_108({
    ...{ 'onUpdated': {} },
    modelValue: (__VLS_ctx.showSettingsModal),
}, ...__VLS_functionalComponentArgsRest(__VLS_108));
let __VLS_111;
let __VLS_112;
let __VLS_113;
const __VLS_114 = {
    onUpdated: (__VLS_ctx.onModelEngineUpdated)
};
var __VLS_110;
/** @type {[typeof NotificationSkylight, ]} */ ;
// @ts-ignore
const __VLS_115 = __VLS_asFunctionalComponent(NotificationSkylight, new NotificationSkylight({
    ...{ 'onUnreadCountChanged': {} },
    modelValue: (__VLS_ctx.showSkylightDrawer),
    unreadCounts: (__VLS_ctx.unreadCounts),
}));
const __VLS_116 = __VLS_115({
    ...{ 'onUnreadCountChanged': {} },
    modelValue: (__VLS_ctx.showSkylightDrawer),
    unreadCounts: (__VLS_ctx.unreadCounts),
}, ...__VLS_functionalComponentArgsRest(__VLS_115));
let __VLS_118;
let __VLS_119;
let __VLS_120;
const __VLS_121 = {
    onUnreadCountChanged: (__VLS_ctx.fetchUnreadCount)
};
var __VLS_117;
/** @type {__VLS_StyleScopedClasses['apple-global-header']} */ ;
/** @type {__VLS_StyleScopedClasses['header-inner']} */ ;
/** @type {__VLS_StyleScopedClasses['header-left']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-logo-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['logo-icon-squircle']} */ ;
/** @type {__VLS_StyleScopedClasses['logo-text-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['logo-title']} */ ;
/** @type {__VLS_StyleScopedClasses['logo-caption']} */ ;
/** @type {__VLS_StyleScopedClasses['header-nav']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-item']} */ ;
/** @type {__VLS_StyleScopedClasses['user-space-link']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-item']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-nav-link']} */ ;
/** @type {__VLS_StyleScopedClasses['header-center']} */ ;
/** @type {__VLS_StyleScopedClasses['search-capsule-box']} */ ;
/** @type {__VLS_StyleScopedClasses['search-prefix-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-search-input']} */ ;
/** @type {__VLS_StyleScopedClasses['search-submit-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['header-right']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-switch-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-trigger-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-bell-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-unread-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['user-state-area']} */ ;
/** @type {__VLS_StyleScopedClasses['user-profile-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-avatar']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-info']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-name']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-role']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-secondary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['chip-logout-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['guest-label-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-settings-trigger-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-publish-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-modal-backdrop']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-modal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-title-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-icon-squircle']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-title']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-subtitle']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-close-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-tab-segment']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-error-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['err-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-form']} */ ;
/** @type {__VLS_StyleScopedClasses['form-field-group']} */ ;
/** @type {__VLS_StyleScopedClasses['field-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-field-group']} */ ;
/** @type {__VLS_StyleScopedClasses['field-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-field-group']} */ ;
/** @type {__VLS_StyleScopedClasses['field-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-field-group']} */ ;
/** @type {__VLS_StyleScopedClasses['field-label']} */ ;
/** @type {__VLS_StyleScopedClasses['role-select-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['role-option-label']} */ ;
/** @type {__VLS_StyleScopedClasses['role-option-label']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-actions-row']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-submit-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['test-accounts-helper']} */ ;
/** @type {__VLS_StyleScopedClasses['helper-caption']} */ ;
/** @type {__VLS_StyleScopedClasses['helper-pills-row']} */ ;
/** @type {__VLS_StyleScopedClasses['helper-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['helper-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['helper-pill']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            Sunny: Sunny,
            Moon: Moon,
            Monitor: Monitor,
            Setting: Setting,
            Upload: Upload,
            Film: Film,
            Lock: Lock,
            Warning: Warning,
            Bell: Bell,
            EngineSettingsModal: EngineSettingsModal,
            NotificationSkylight: NotificationSkylight,
            defaultAvatar: defaultAvatar,
            searchKeyword: searchKeyword,
            currentUser: currentUser,
            showAuthModal: showAuthModal,
            showSettingsModal: showSettingsModal,
            showSkylightDrawer: showSkylightDrawer,
            unreadCounts: unreadCounts,
            authMode: authMode,
            modalHintText: modalHintText,
            authError: authError,
            isSubmitting: isSubmitting,
            currentTheme: currentTheme,
            fetchUnreadCount: fetchUnreadCount,
            toggleTheme: toggleTheme,
            onModelEngineUpdated: onModelEngineUpdated,
            authForm: authForm,
            handleSearch: handleSearch,
            getRoleLabel: getRoleLabel,
            fillQuickAccount: fillQuickAccount,
            handleAuthSubmit: handleAuthSubmit,
            handleLogout: handleLogout,
            handleCreatorUpload: handleCreatorUpload,
        };
    },
    __typeEmits: {},
});
export default (await import('vue')).defineComponent({
    setup() {
        return {
            ...__VLS_exposed,
        };
    },
    __typeEmits: {},
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=GlobalHeader.vue.js.map