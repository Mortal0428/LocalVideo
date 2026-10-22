/// <reference types="../../node_modules/.vue-global-types/vue_3.5_0_0_0.d.ts" />
import { ref, reactive, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { authApi } from '../api/auth';
const router = useRouter();
const route = useRoute();
const currentTab = ref('login');
const showPassword = ref(false);
const isLoading = ref(false);
const feedbackMsg = ref('');
const feedbackType = ref('error');
const genreOptions = ['逆袭爽剧', '年代逆袭', '现代甜宠', '科技AI', '动漫番剧', '悬疑刑侦', '影视原声'];
const loginForm = reactive({
    username: '',
    password: ''
});
const regForm = reactive({
    username: '',
    nickname: '',
    password: '',
    confirmPassword: '',
    preferences: ['逆袭爽剧', '年代逆袭']
});
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
onMounted(() => {
    const saved = localStorage.getItem('cinema_theme') || 'system';
    currentTheme.value = saved;
    if (route.query.tab === 'register' || route.path === '/register') {
        currentTab.value = 'register';
    }
});
function switchTab(tab) {
    currentTab.value = tab;
    feedbackMsg.value = '';
}
function togglePreference(tag) {
    const idx = regForm.preferences.indexOf(tag);
    if (idx >= 0) {
        regForm.preferences.splice(idx, 1);
    }
    else {
        regForm.preferences.push(tag);
    }
}
function showFeedback(msg, type = 'error') {
    feedbackMsg.value = msg;
    feedbackType.value = type;
}
async function handleLogin() {
    if (!loginForm.username.trim() || !loginForm.password.trim()) {
        showFeedback('请输入用户名和密码');
        return;
    }
    isLoading.value = true;
    feedbackMsg.value = '';
    try {
        const res = await authApi.login({
            username: loginForm.username.trim(),
            password: loginForm.password.trim()
        });
        const token = res?.access_token || res?.data?.access_token;
        const user = res?.user || res?.data?.user;
        if (token) {
            localStorage.setItem('token', token);
            localStorage.setItem('cinema_access_token', token);
            localStorage.setItem('user', JSON.stringify(user));
            showFeedback('登录成功，正在进入平台...', 'success');
            setTimeout(() => {
                const redirect = route.query.redirect || '/';
                router.push(redirect);
            }, 500);
        }
        else {
            showFeedback(res?.message || '登录失败，请检查账号密码');
        }
    }
    catch (err) {
        const detail = err?.response?.data?.detail || err?.message || '登录失败';
        showFeedback(`登录错误: ${detail}`);
    }
    finally {
        isLoading.value = false;
    }
}
async function handleRegister() {
    if (!regForm.username.trim()) {
        showFeedback('请输入用户名');
        return;
    }
    if (regForm.password.length < 6) {
        showFeedback('密码长度不得少于 6 位');
        return;
    }
    if (regForm.password !== regForm.confirmPassword) {
        showFeedback('两次输入的密码不一致');
        return;
    }
    isLoading.value = true;
    feedbackMsg.value = '';
    try {
        const res = await authApi.register({
            username: regForm.username.trim(),
            password: regForm.password.trim(),
            nickname: regForm.nickname.trim() || regForm.username.trim(),
            role: 'USER'
        });
        const token = res?.access_token || res?.data?.access_token;
        const user = res?.user || res?.data?.user;
        if (token) {
            localStorage.setItem('token', token);
            localStorage.setItem('user', JSON.stringify(user));
            showFeedback('🎉 注册成功！已自动登录，正在为您开启视听之旅...', 'success');
            setTimeout(() => {
                router.push('/');
            }, 700);
        }
        else {
            showFeedback(res?.message || '注册成功，请使用新账号登录', 'success');
            currentTab.value = 'login';
        }
    }
    catch (err) {
        const detail = err?.response?.data?.detail || err?.message || '注册失败';
        showFeedback(`注册错误: ${detail}`);
    }
    finally {
        isLoading.value = false;
    }
}
async function quickLogin(roleName) {
    isLoading.value = true;
    feedbackMsg.value = '';
    try {
        const res = await authApi.quickSwitch(roleName);
        const token = res?.access_token || res?.data?.access_token;
        const user = res?.user || res?.data?.user;
        if (token) {
            localStorage.setItem('token', token);
            localStorage.setItem('cinema_access_token', token);
            localStorage.setItem('user', JSON.stringify(user));
            showFeedback(`已成功以【${user?.nickname || roleName}】身份快捷登录！`, 'success');
            setTimeout(() => {
                if (roleName === 'admin')
                    router.push('/admin');
                else if (roleName === 'creator')
                    router.push('/creator');
                else
                    router.push('/');
            }, 400);
        }
    }
    catch (err) {
        showFeedback('快捷登录切换失败: ' + (err?.message || '网络异常'));
    }
    finally {
        isLoading.value = false;
    }
}
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['back-home-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['logo-text']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-bento-item']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-text']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-feedback-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-feedback-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['input-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['genre-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-role-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-role-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-role-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-role-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-role-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-role-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['guest-link-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['guest-link-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['guest-link-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['arrow']} */ ;
/** @type {__VLS_StyleScopedClasses['grand-auth-container']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-brand-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-form-card']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "grand-auth-page" },
    id: "auth-center-root",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "aurora-ambient-glow aurora-orb-1" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "aurora-ambient-glow aurora-orb-2" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "aurora-ambient-glow aurora-orb-3" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "auth-floating-bar" },
});
const __VLS_0 = {}.RouterLink;
/** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    to: "/",
    ...{ class: "back-home-pill-btn" },
    id: "btn-login-back-home",
}));
const __VLS_2 = __VLS_1({
    to: "/",
    ...{ class: "back-home-pill-btn" },
    id: "btn-login-back-home",
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
__VLS_3.slots.default;
var __VLS_3;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "theme-switch-pill" },
    id: "login-theme-control",
    title: "切换明暗色彩主题",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.toggleTheme('light');
        } },
    type: "button",
    ...{ class: "theme-icon-btn" },
    ...{ class: ({ active: __VLS_ctx.currentTheme === 'light' }) },
    id: "btn-login-theme-light",
    title: "浅色白天模式",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.toggleTheme('dark');
        } },
    type: "button",
    ...{ class: "theme-icon-btn" },
    ...{ class: ({ active: __VLS_ctx.currentTheme === 'dark' }) },
    id: "btn-login-theme-dark",
    title: "深色夜间模式",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.toggleTheme('system');
        } },
    type: "button",
    ...{ class: "theme-icon-btn" },
    ...{ class: ({ active: __VLS_ctx.currentTheme === 'system' }) },
    id: "btn-login-theme-system",
    title: "跟随系统自动",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "grand-auth-container" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "auth-brand-panel" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "brand-top-bar" },
});
const __VLS_4 = {}.RouterLink;
/** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
// @ts-ignore
const __VLS_5 = __VLS_asFunctionalComponent(__VLS_4, new __VLS_4({
    to: "/",
    ...{ class: "brand-logo-wrap" },
    title: "返回首页大厅",
}));
const __VLS_6 = __VLS_5({
    to: "/",
    ...{ class: "brand-logo-wrap" },
    title: "返回首页大厅",
}, ...__VLS_functionalComponentArgsRest(__VLS_5));
__VLS_7.slots.default;
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "logo-text" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "accent" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "tag-version" },
});
var __VLS_7;
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "brand-badge-pill" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "brand-hero-content" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({
    ...{ class: "hero-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.br)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "gradient-text" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "hero-desc" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-bento-grid" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-bento-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-text" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-bento-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-text" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-bento-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-text" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-bento-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-text" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "brand-footer-stats" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "stat-pill" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-num" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "stat-divider" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "stat-pill" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-num" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "stat-divider" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "stat-pill" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-num" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "auth-form-card" },
    id: "auth-form-container",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "auth-tab-segment" },
    id: "auth-tab-bar",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.switchTab('login');
        } },
    ...{ class: "tab-btn" },
    ...{ class: ({ active: __VLS_ctx.currentTab === 'login' }) },
    id: "tab-btn-login",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.switchTab('register');
        } },
    ...{ class: "tab-btn" },
    ...{ class: ({ active: __VLS_ctx.currentTab === 'register' }) },
    id: "tab-btn-register",
});
const __VLS_8 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({
    name: "fade",
}));
const __VLS_10 = __VLS_9({
    name: "fade",
}, ...__VLS_functionalComponentArgsRest(__VLS_9));
__VLS_11.slots.default;
if (__VLS_ctx.feedbackMsg) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "auth-feedback-banner" },
        ...{ class: (__VLS_ctx.feedbackType) },
        id: "auth-feedback",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "fb-icon" },
    });
    (__VLS_ctx.feedbackType === 'error' ? '⚠️' : '✅');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "fb-text" },
    });
    (__VLS_ctx.feedbackMsg);
}
var __VLS_11;
if (__VLS_ctx.currentTab === 'login') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.form, __VLS_intrinsicElements.form)({
        ...{ onSubmit: (__VLS_ctx.handleLogin) },
        ...{ class: "auth-form" },
        id: "form-login",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
        for: "input-login-username",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "input-wrap" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "input-prefix" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        id: "input-login-username",
        value: (__VLS_ctx.loginForm.username),
        type: "text",
        ...{ class: "form-input" },
        placeholder: "请输入用户名 (如 viewer, creator, admin)",
        required: true,
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "label-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
        for: "input-login-password",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "input-wrap" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "input-prefix" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        id: "input-login-password",
        type: (__VLS_ctx.showPassword ? 'text' : 'password'),
        ...{ class: "form-input" },
        placeholder: "请输入密码",
        required: true,
    });
    (__VLS_ctx.loginForm.password);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.currentTab === 'login'))
                    return;
                __VLS_ctx.showPassword = !__VLS_ctx.showPassword;
            } },
        type: "button",
        ...{ class: "pwd-toggle-btn" },
        id: "btn-toggle-login-pwd",
        title: "显示/隐藏密码",
    });
    (__VLS_ctx.showPassword ? '🙈' : '👁️');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        type: "submit",
        ...{ class: "auth-primary-btn" },
        id: "btn-submit-login",
        disabled: (__VLS_ctx.isLoading),
    });
    if (__VLS_ctx.isLoading) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "spinner" },
        });
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.form, __VLS_intrinsicElements.form)({
        ...{ onSubmit: (__VLS_ctx.handleRegister) },
        ...{ class: "auth-form" },
        id: "form-register",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
        for: "input-reg-username",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "input-wrap" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "input-prefix" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        id: "input-reg-username",
        value: (__VLS_ctx.regForm.username),
        type: "text",
        ...{ class: "form-input" },
        placeholder: "3-20位字母、数字或下划线",
        required: true,
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
        for: "input-reg-nickname",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "input-wrap" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "input-prefix" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        id: "input-reg-nickname",
        value: (__VLS_ctx.regForm.nickname),
        type: "text",
        ...{ class: "form-input" },
        placeholder: "起一个响亮的昵称 (如 追剧大魔王)",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-row-dual" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
        for: "input-reg-password",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "input-wrap" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "input-prefix" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        id: "input-reg-password",
        type: (__VLS_ctx.showPassword ? 'text' : 'password'),
        ...{ class: "form-input" },
        placeholder: "至少 6 位密码",
        required: true,
    });
    (__VLS_ctx.regForm.password);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
        for: "input-reg-confirm-pwd",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "input-wrap" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "input-prefix" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        id: "input-reg-confirm-pwd",
        type: (__VLS_ctx.showPassword ? 'text' : 'password'),
        ...{ class: "form-input" },
        placeholder: "再次输入以确认",
        required: true,
    });
    (__VLS_ctx.regForm.confirmPassword);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "genre-tags-wrap" },
    });
    for (const [tag] of __VLS_getVForSourceType((__VLS_ctx.genreOptions))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!!(__VLS_ctx.currentTab === 'login'))
                        return;
                    __VLS_ctx.togglePreference(tag);
                } },
            key: (tag),
            type: "button",
            ...{ class: "genre-chip" },
            ...{ class: ({ active: __VLS_ctx.regForm.preferences.includes(tag) }) },
        });
        (tag);
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        type: "submit",
        ...{ class: "auth-primary-btn" },
        id: "btn-submit-register",
        disabled: (__VLS_ctx.isLoading),
    });
    if (__VLS_ctx.isLoading) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "spinner" },
        });
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "auth-divider" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "quick-demo-roles" },
    id: "quick-demo-accounts-bar",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.quickLogin('viewer');
        } },
    ...{ class: "demo-role-btn role-viewer" },
    id: "btn-demo-viewer",
    title: "以普通观众身份登录",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "demo-icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "demo-name" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "demo-sub" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.quickLogin('creator');
        } },
    ...{ class: "demo-role-btn role-creator" },
    id: "btn-demo-creator",
    title: "以认证创作者身份登录",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "demo-icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "demo-name" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "demo-sub" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.quickLogin('reviewer');
        } },
    ...{ class: "demo-role-btn role-reviewer" },
    id: "btn-demo-reviewer",
    title: "以内容合规审核员身份登录",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "demo-icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "demo-name" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "demo-sub" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.quickLogin('admin');
        } },
    ...{ class: "demo-role-btn role-admin" },
    id: "btn-demo-admin",
    title: "以超级管理员身份登录",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "demo-icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "demo-name" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "demo-sub" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "guest-access-wrap" },
});
const __VLS_12 = {}.RouterLink;
/** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
// @ts-ignore
const __VLS_13 = __VLS_asFunctionalComponent(__VLS_12, new __VLS_12({
    to: "/",
    ...{ class: "guest-link-btn" },
    id: "btn-guest-entry",
}));
const __VLS_14 = __VLS_13({
    to: "/",
    ...{ class: "guest-link-btn" },
    id: "btn-guest-entry",
}, ...__VLS_functionalComponentArgsRest(__VLS_13));
__VLS_15.slots.default;
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "arrow" },
});
var __VLS_15;
/** @type {__VLS_StyleScopedClasses['grand-auth-page']} */ ;
/** @type {__VLS_StyleScopedClasses['aurora-ambient-glow']} */ ;
/** @type {__VLS_StyleScopedClasses['aurora-orb-1']} */ ;
/** @type {__VLS_StyleScopedClasses['aurora-ambient-glow']} */ ;
/** @type {__VLS_StyleScopedClasses['aurora-orb-2']} */ ;
/** @type {__VLS_StyleScopedClasses['aurora-ambient-glow']} */ ;
/** @type {__VLS_StyleScopedClasses['aurora-orb-3']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-floating-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['back-home-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-switch-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theme-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['grand-auth-container']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-brand-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-top-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-logo-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['logo-text']} */ ;
/** @type {__VLS_StyleScopedClasses['accent']} */ ;
/** @type {__VLS_StyleScopedClasses['tag-version']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-badge-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-hero-content']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-title']} */ ;
/** @type {__VLS_StyleScopedClasses['gradient-text']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-bento-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-bento-item']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-text']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-bento-item']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-text']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-bento-item']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-text']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-bento-item']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-text']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-footer-stats']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-num']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-label']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-num']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-label']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-num']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-label']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-form-card']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-tab-segment']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-feedback-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['fb-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['fb-text']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-form']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['input-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['input-prefix']} */ ;
/** @type {__VLS_StyleScopedClasses['form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['label-row']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['input-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['input-prefix']} */ ;
/** @type {__VLS_StyleScopedClasses['form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['pwd-toggle-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['spinner']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-form']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['input-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['input-prefix']} */ ;
/** @type {__VLS_StyleScopedClasses['form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['input-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['input-prefix']} */ ;
/** @type {__VLS_StyleScopedClasses['form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-row-dual']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['input-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['input-prefix']} */ ;
/** @type {__VLS_StyleScopedClasses['form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['input-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['input-prefix']} */ ;
/** @type {__VLS_StyleScopedClasses['form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['genre-tags-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['genre-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['spinner']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['quick-demo-roles']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-role-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['role-viewer']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-name']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-role-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['role-creator']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-name']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-role-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['role-reviewer']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-name']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-role-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['role-admin']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-name']} */ ;
/** @type {__VLS_StyleScopedClasses['demo-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['guest-access-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['guest-link-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['arrow']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            currentTab: currentTab,
            showPassword: showPassword,
            isLoading: isLoading,
            feedbackMsg: feedbackMsg,
            feedbackType: feedbackType,
            genreOptions: genreOptions,
            loginForm: loginForm,
            regForm: regForm,
            currentTheme: currentTheme,
            toggleTheme: toggleTheme,
            switchTab: switchTab,
            togglePreference: togglePreference,
            handleLogin: handleLogin,
            handleRegister: handleRegister,
            quickLogin: quickLogin,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=LoginView.vue.js.map