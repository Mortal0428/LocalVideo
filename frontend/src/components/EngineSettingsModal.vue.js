import { ref, computed, watch } from 'vue';
import { adminApi } from '../api/admin';
const props = defineProps();
const emit = defineEmits();
const loading = ref(false);
const saving = ref(false);
const testingChat = ref(false);
const testingEmb = ref(false);
const userRole = ref('USER');
const isAdmin = ref(false);
const chatProvider = ref('mimo');
const chatModel = ref('mimo-v2.6-flash');
const chatBaseUrl = ref('https://api.xiaomimimo.com/v1');
const chatApiKey = ref('');
const chatTestResult = ref(null);
const embProvider = ref('ollama');
const embModel = ref('qwen3-embedding:0.6b');
const embBaseUrl = ref('http://localhost:11434');
const embApiKey = ref('');
const embTestResult = ref(null);
const saveNotice = ref(null);
const probeData = ref({
    ollama: { running: false, chat_models: [], embedding_models: [], all_models: [] },
    deepseek: { configured: false, masked_key: '', supported_models: ['deepseek-chat', 'deepseek-reasoner'] },
    mimo: { configured: false, masked_key: '', supported_models: ['mimo-v1', 'mimo-v1-chat', 'mimo-v1-pro'] },
    openai: { configured: false, masked_key: '', supported_models: ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'] }
});
const chatSuggestions = computed(() => {
    if (chatProvider.value === 'ollama') {
        return probeData.value.ollama?.chat_models?.length ? probeData.value.ollama.chat_models : ['deepseek-r1:1.5b', 'qwen3.5:2b'];
    }
    if (chatProvider.value === 'deepseek')
        return ['deepseek-chat', 'deepseek-reasoner'];
    if (chatProvider.value === 'mimo')
        return ['mimo-v2.6-flash', 'mimo-v1-chat', 'mimo-v1-pro'];
    if (chatProvider.value === 'openai')
        return ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'];
    return [];
});
const embSuggestions = computed(() => {
    if (embProvider.value === 'ollama') {
        return probeData.value.ollama?.embedding_models?.length ? probeData.value.ollama.embedding_models : ['qwen3-embedding:0.6b', 'bge-m3:latest'];
    }
    return ['text-embedding-3-small', 'text-embedding-3-large'];
});
const getRoleLabel = (role) => {
    const map = {
        USER: '普通用户',
        CREATOR: '创作者',
        REVIEWER: '审核员',
        ADMIN: '系统管理员',
        GUEST: '游客'
    };
    return map[role] || role;
};
const checkUserPermission = () => {
    try {
        const raw = localStorage.getItem('user');
        if (raw) {
            const user = JSON.parse(raw);
            userRole.value = user.role || 'USER';
            isAdmin.value = user.role === 'ADMIN';
        }
        else {
            userRole.value = 'GUEST';
            isAdmin.value = false;
        }
    }
    catch {
        isAdmin.value = false;
    }
};
const switchChatProvider = (p) => {
    chatProvider.value = p;
    chatTestResult.value = null;
    if (p === 'ollama') {
        chatBaseUrl.value = 'http://localhost:11434';
        chatModel.value = probeData.value.ollama?.chat_models?.[0] || 'deepseek-r1:1.5b';
    }
    else if (p === 'deepseek') {
        chatBaseUrl.value = 'https://api.deepseek.com';
        chatModel.value = 'deepseek-chat';
    }
    else if (p === 'mimo') {
        chatBaseUrl.value = 'https://api.xiaomimimo.com/v1';
        chatModel.value = 'mimo-v2.6-flash';
    }
    else if (p === 'openai') {
        chatBaseUrl.value = 'https://api.openai.com/v1';
        chatModel.value = 'gpt-4o-mini';
    }
};
const switchEmbProvider = (p) => {
    embProvider.value = p;
    embTestResult.value = null;
    if (p === 'ollama') {
        embBaseUrl.value = 'http://localhost:11434';
        embModel.value = probeData.value.ollama?.embedding_models?.[0] || 'qwen3-embedding:0.6b';
    }
    else {
        embBaseUrl.value = 'https://api.openai.com/v1';
        embModel.value = 'text-embedding-3-small';
    }
};
const quickSwitchToAdmin = async () => {
    try {
        const res = await fetch('/api/v1/auth/quick-switch/ADMIN', { method: 'POST' });
        if (res.ok) {
            const json = await res.json();
            const token = json.access_token || json.data?.access_token;
            const user = json.user || json.data?.user;
            if (token) {
                localStorage.setItem('cinema_access_token', token);
                localStorage.setItem('token', token);
                localStorage.setItem('user', JSON.stringify(user));
                userRole.value = 'ADMIN';
                isAdmin.value = true;
                saveNotice.value = {
                    status: 'success',
                    message: '已成功切换至系统管理员 (ADMIN) 身份，已解锁模型配置权限！'
                };
            }
        }
    }
    catch (err) {
        console.error('Failed to switch to admin:', err);
    }
};
const loadData = async () => {
    loading.value = true;
    chatTestResult.value = null;
    embTestResult.value = null;
    saveNotice.value = null;
    checkUserPermission();
    try {
        // 1. Load Dual Settings
        const dualRes = await adminApi.getDualModelSettings();
        const dualData = dualRes?.data || dualRes;
        if (dualData?.chat_engine) {
            chatProvider.value = dualData.chat_engine.provider || 'mimo';
            chatModel.value = dualData.chat_engine.model_name || 'mimo-v2.6-flash';
            chatBaseUrl.value = dualData.chat_engine.base_url || 'https://api.xiaomimimo.com/v1';
            chatApiKey.value = dualData.chat_engine.api_key || '';
        }
        if (dualData?.embedding_engine) {
            embProvider.value = dualData.embedding_engine.provider || 'ollama';
            embModel.value = dualData.embedding_engine.model_name || 'qwen3-embedding:0.6b';
            embBaseUrl.value = dualData.embedding_engine.base_url || 'http://localhost:11434';
            embApiKey.value = dualData.embedding_engine.api_key || '';
        }
        // 2. Load Probe Telemetry
        const probeRes = await fetch('/api/v1/models/probe');
        if (probeRes.ok) {
            const json = await probeRes.json();
            if (json.code === 200 && json.data) {
                probeData.value = json.data;
            }
        }
    }
    catch (err) {
        console.error('Failed to load dual engine settings:', err);
    }
    finally {
        loading.value = false;
    }
};
const testChatEngine = async () => {
    testingChat.value = true;
    chatTestResult.value = null;
    try {
        const res = await adminApi.testChatConnection({
            provider: chatProvider.value,
            model: chatModel.value.trim(),
            base_url: chatBaseUrl.value.trim(),
            api_key: chatApiKey.value.trim() || undefined
        });
        const data = res?.data || res;
        if (res?.code === 200 || data?.code === 200) {
            chatTestResult.value = {
                status: 'success',
                message: data.reply || '对话推理模型连通成功！'
            };
        }
        else {
            chatTestResult.value = {
                status: 'failed',
                message: data.detail || '对话模型连接失败'
            };
        }
    }
    catch (err) {
        chatTestResult.value = {
            status: 'failed',
            message: err.message || '网络连接异常'
        };
    }
    finally {
        testingChat.value = false;
    }
};
const testEmbEngine = async () => {
    testingEmb.value = true;
    embTestResult.value = null;
    try {
        const res = await adminApi.testEmbeddingConnection({
            provider: embProvider.value,
            model: embModel.value.trim(),
            base_url: embBaseUrl.value.trim(),
            api_key: embApiKey.value.trim() || undefined
        });
        const data = res?.data || res;
        if (res?.code === 200 || data?.code === 200) {
            embTestResult.value = {
                status: 'success',
                message: data.reply || '向量嵌入模型计算正常！'
            };
        }
        else {
            embTestResult.value = {
                status: 'failed',
                message: data.detail || '向量模型测试失败'
            };
        }
    }
    catch (err) {
        embTestResult.value = {
            status: 'failed',
            message: err.message || '向量服务连接失败'
        };
    }
    finally {
        testingEmb.value = false;
    }
};
const saveDualConfig = async () => {
    if (!isAdmin.value) {
        saveNotice.value = {
            status: 'failed',
            message: '权限不足：仅系统管理员 (ADMIN) 可修改全局模型配置！'
        };
        return;
    }
    saving.value = true;
    saveNotice.value = null;
    try {
        const payload = {
            chat_engine: {
                provider: chatProvider.value,
                model_name: chatModel.value.trim(),
                base_url: chatBaseUrl.value.trim(),
                api_key: chatApiKey.value.trim() || undefined
            },
            embedding_engine: {
                provider: embProvider.value,
                model_name: embModel.value.trim(),
                base_url: embBaseUrl.value.trim(),
                api_key: embApiKey.value.trim() || undefined
            }
        };
        const res = await adminApi.updateDualModelSettings(payload);
        saveNotice.value = {
            status: 'success',
            message: '双轨大模型配置已成功保存并实时热重载生效！'
        };
        emit('updated', res?.data || payload);
        setTimeout(() => {
            close();
        }, 1200);
    }
    catch (err) {
        saveNotice.value = {
            status: 'failed',
            message: err.message || '保存配置失败'
        };
    }
    finally {
        saving.value = false;
    }
};
const close = () => {
    emit('update:modelValue', false);
};
watch(() => props.modelValue, (val) => {
    if (val) {
        loadData();
    }
});
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['close-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-status-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-status-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-status-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['provider-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['custom-input']} */ ;
/** @type {__VLS_StyleScopedClasses['custom-input']} */ ;
/** @type {__VLS_StyleScopedClasses['suggest-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['suggest-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['test-inline-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['test-feedback-box']} */ ;
/** @type {__VLS_StyleScopedClasses['success']} */ ;
/** @type {__VLS_StyleScopedClasses['test-feedback-box']} */ ;
/** @type {__VLS_StyleScopedClasses['failed']} */ ;
/** @type {__VLS_StyleScopedClasses['global-save-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['success']} */ ;
/** @type {__VLS_StyleScopedClasses['global-save-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['failed']} */ ;
/** @type {__VLS_StyleScopedClasses['cancel-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['save-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['save-btn']} */ ;
// CSS variable injection 
// CSS variable injection end 
const __VLS_0 = {}.Teleport;
/** @type {[typeof __VLS_components.Teleport, typeof __VLS_components.Teleport, ]} */ ;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    to: "body",
}));
const __VLS_2 = __VLS_1({
    to: "body",
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
__VLS_3.slots.default;
if (__VLS_ctx.modelValue) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ onClick: (__VLS_ctx.close) },
        ...{ class: "settings-modal-overlay" },
        id: "modal-engine-settings-backdrop",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "settings-modal-card fade-in-up dual-engine-modal" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "header-title-box" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "header-icon" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "modal-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "modal-subtitle" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.close) },
        ...{ class: "close-btn" },
        id: "btn-close-engine-modal",
        title: "关闭",
    });
    if (!__VLS_ctx.isAdmin) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "admin-notice-banner read-only" },
            id: "engine-readonly-notice",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "notice-info" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "notice-icon" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "notice-title" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "notice-desc" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({});
        (__VLS_ctx.getRoleLabel(__VLS_ctx.userRole));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.quickSwitchToAdmin) },
            type: "button",
            ...{ class: "switch-admin-btn" },
            id: "btn-switch-admin-in-modal",
        });
    }
    if (__VLS_ctx.loading) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "loading-state" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "loading-spinner" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "modal-dual-grid" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "engine-card glass-panel" },
            id: "card-chat-engine",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "card-head-line" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "head-left" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "engine-badge chat-badge" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
            ...{ class: "engine-name" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "engine-status-tag" },
            ...{ class: (__VLS_ctx.chatTestResult?.status || 'idle') },
        });
        (__VLS_ctx.chatTestResult?.status === 'success' ? '连通正常' : (__VLS_ctx.chatTestResult?.status === 'failed' ? '连接异常' : '未检测'));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "engine-intro" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "provider-switch-group" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.modelValue))
                        return;
                    if (!!(__VLS_ctx.loading))
                        return;
                    __VLS_ctx.switchChatProvider('ollama');
                } },
            type: "button",
            ...{ class: "provider-pill-btn" },
            ...{ class: ({ active: __VLS_ctx.chatProvider === 'ollama' }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "pill-badge" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.modelValue))
                        return;
                    if (!!(__VLS_ctx.loading))
                        return;
                    __VLS_ctx.switchChatProvider('deepseek');
                } },
            type: "button",
            ...{ class: "provider-pill-btn" },
            ...{ class: ({ active: __VLS_ctx.chatProvider === 'deepseek' }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "pill-badge cloud-deepseek" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.modelValue))
                        return;
                    if (!!(__VLS_ctx.loading))
                        return;
                    __VLS_ctx.switchChatProvider('mimo');
                } },
            type: "button",
            ...{ class: "provider-pill-btn" },
            ...{ class: ({ active: __VLS_ctx.chatProvider === 'mimo' }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "pill-badge cloud-mimo" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.modelValue))
                        return;
                    if (!!(__VLS_ctx.loading))
                        return;
                    __VLS_ctx.switchChatProvider('openai');
                } },
            type: "button",
            ...{ class: "provider-pill-btn" },
            ...{ class: ({ active: __VLS_ctx.chatProvider === 'openai' }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "pill-badge cloud-openai" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "engine-form-stack" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "form-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "form-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            value: (__VLS_ctx.chatBaseUrl),
            type: "text",
            ...{ class: "custom-input" },
            placeholder: "如 http://localhost:11434 或 https://api.xiaomimimo.com/v1",
            disabled: (!__VLS_ctx.isAdmin),
            id: "input-chat-base-url",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "form-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "form-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            value: (__VLS_ctx.chatModel),
            type: "text",
            ...{ class: "custom-input" },
            placeholder: "如 deepseek-r1:1.5b, mimo-v2.6-flash, gpt-4o-mini",
            disabled: (!__VLS_ctx.isAdmin),
            id: "input-chat-model",
        });
        if (__VLS_ctx.chatSuggestions.length) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "suggest-tags-row" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "suggest-title" },
            });
            for (const [m] of __VLS_getVForSourceType((__VLS_ctx.chatSuggestions))) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                    ...{ onClick: (...[$event]) => {
                            if (!(__VLS_ctx.modelValue))
                                return;
                            if (!!(__VLS_ctx.loading))
                                return;
                            if (!(__VLS_ctx.chatSuggestions.length))
                                return;
                            __VLS_ctx.chatModel = m;
                        } },
                    key: (m),
                    type: "button",
                    ...{ class: "suggest-chip" },
                    ...{ class: ({ active: __VLS_ctx.chatModel === m }) },
                    disabled: (!__VLS_ctx.isAdmin),
                });
                (m);
            }
        }
        if (__VLS_ctx.chatProvider !== 'ollama') {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "form-item" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
                ...{ class: "form-label" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
                type: "password",
                ...{ class: "custom-input" },
                placeholder: "sk-...",
                disabled: (!__VLS_ctx.isAdmin),
                id: "input-chat-api-key",
            });
            (__VLS_ctx.chatApiKey);
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "test-action-line" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.testChatEngine) },
            type: "button",
            ...{ class: "test-inline-btn" },
            id: "btn-test-chat-engine",
            disabled: (__VLS_ctx.testingChat),
        });
        (__VLS_ctx.testingChat ? '正在测试对话连通性...' : '⚡ 测试对话模型连通性');
        if (__VLS_ctx.chatTestResult) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "test-feedback-box" },
                ...{ class: (__VLS_ctx.chatTestResult.status) },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
            (__VLS_ctx.chatTestResult.status === 'success' ? '✅' : '❌');
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
            (__VLS_ctx.chatTestResult.message);
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "engine-card glass-panel" },
            id: "card-embedding-engine",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "card-head-line" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "head-left" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "engine-badge emb-badge" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
            ...{ class: "engine-name" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "engine-status-tag" },
            ...{ class: (__VLS_ctx.embTestResult?.status || 'idle') },
        });
        (__VLS_ctx.embTestResult?.status === 'success' ? '计算正常' : (__VLS_ctx.embTestResult?.status === 'failed' ? '计算异常' : '未检测'));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "engine-intro" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "provider-switch-group" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.modelValue))
                        return;
                    if (!!(__VLS_ctx.loading))
                        return;
                    __VLS_ctx.switchEmbProvider('ollama');
                } },
            type: "button",
            ...{ class: "provider-pill-btn" },
            ...{ class: ({ active: __VLS_ctx.embProvider === 'ollama' }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "pill-badge" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.modelValue))
                        return;
                    if (!!(__VLS_ctx.loading))
                        return;
                    __VLS_ctx.switchEmbProvider('openai');
                } },
            type: "button",
            ...{ class: "provider-pill-btn" },
            ...{ class: ({ active: __VLS_ctx.embProvider === 'openai' }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "pill-badge cloud-openai" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "engine-form-stack" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "form-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "form-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            value: (__VLS_ctx.embBaseUrl),
            type: "text",
            ...{ class: "custom-input" },
            placeholder: "http://localhost:11434",
            disabled: (!__VLS_ctx.isAdmin),
            id: "input-emb-base-url",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "form-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "form-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            value: (__VLS_ctx.embModel),
            type: "text",
            ...{ class: "custom-input" },
            placeholder: "如 qwen3-embedding:0.6b, bge-m3:latest",
            disabled: (!__VLS_ctx.isAdmin),
            id: "input-emb-model",
        });
        if (__VLS_ctx.embSuggestions.length) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "suggest-tags-row" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "suggest-title" },
            });
            for (const [m] of __VLS_getVForSourceType((__VLS_ctx.embSuggestions))) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                    ...{ onClick: (...[$event]) => {
                            if (!(__VLS_ctx.modelValue))
                                return;
                            if (!!(__VLS_ctx.loading))
                                return;
                            if (!(__VLS_ctx.embSuggestions.length))
                                return;
                            __VLS_ctx.embModel = m;
                        } },
                    key: (m),
                    type: "button",
                    ...{ class: "suggest-chip" },
                    ...{ class: ({ active: __VLS_ctx.embModel === m }) },
                    disabled: (!__VLS_ctx.isAdmin),
                });
                (m);
            }
        }
        if (__VLS_ctx.embProvider !== 'ollama') {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "form-item" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
                ...{ class: "form-label" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
                type: "password",
                ...{ class: "custom-input" },
                placeholder: "sk-...",
                disabled: (!__VLS_ctx.isAdmin),
                id: "input-emb-api-key",
            });
            (__VLS_ctx.embApiKey);
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "test-action-line" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.testEmbEngine) },
            type: "button",
            ...{ class: "test-inline-btn" },
            id: "btn-test-emb-engine",
            disabled: (__VLS_ctx.testingEmb),
        });
        (__VLS_ctx.testingEmb ? '正在测试向量计算...' : '⚡ 测试向量嵌入连通性');
        if (__VLS_ctx.embTestResult) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "test-feedback-box" },
                ...{ class: (__VLS_ctx.embTestResult.status) },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
            (__VLS_ctx.embTestResult.status === 'success' ? '✅' : '❌');
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
            (__VLS_ctx.embTestResult.message);
        }
    }
    if (__VLS_ctx.saveNotice) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "global-save-banner" },
            ...{ class: (__VLS_ctx.saveNotice.status) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (__VLS_ctx.saveNotice.status === 'success' ? '✅' : '❌');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (__VLS_ctx.saveNotice.message);
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-footer" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "footer-left" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "version-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "footer-right" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.close) },
        type: "button",
        ...{ class: "action-btn cancel-btn" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.saveDualConfig) },
        type: "button",
        ...{ class: "action-btn save-btn" },
        id: "btn-save-engine-config",
        disabled: (__VLS_ctx.saving || !__VLS_ctx.isAdmin),
        title: (!__VLS_ctx.isAdmin ? '仅管理员可保存' : '保存模型配置并毫秒级热重载'),
    });
    (__VLS_ctx.saving ? '保存中...' : (__VLS_ctx.isAdmin ? '保存并热生效' : '只读锁定'));
}
var __VLS_3;
/** @type {__VLS_StyleScopedClasses['settings-modal-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['settings-modal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['fade-in-up']} */ ;
/** @type {__VLS_StyleScopedClasses['dual-engine-modal']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-header']} */ ;
/** @type {__VLS_StyleScopedClasses['header-title-box']} */ ;
/** @type {__VLS_StyleScopedClasses['header-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-title']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-subtitle']} */ ;
/** @type {__VLS_StyleScopedClasses['close-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-notice-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['read-only']} */ ;
/** @type {__VLS_StyleScopedClasses['notice-info']} */ ;
/** @type {__VLS_StyleScopedClasses['notice-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['notice-title']} */ ;
/** @type {__VLS_StyleScopedClasses['notice-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['switch-admin-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['loading-state']} */ ;
/** @type {__VLS_StyleScopedClasses['loading-spinner']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-dual-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['card-head-line']} */ ;
/** @type {__VLS_StyleScopedClasses['head-left']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['chat-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-name']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-status-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-intro']} */ ;
/** @type {__VLS_StyleScopedClasses['provider-switch-group']} */ ;
/** @type {__VLS_StyleScopedClasses['provider-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['provider-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['cloud-deepseek']} */ ;
/** @type {__VLS_StyleScopedClasses['provider-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['cloud-mimo']} */ ;
/** @type {__VLS_StyleScopedClasses['provider-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['cloud-openai']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-form-stack']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['custom-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['custom-input']} */ ;
/** @type {__VLS_StyleScopedClasses['suggest-tags-row']} */ ;
/** @type {__VLS_StyleScopedClasses['suggest-title']} */ ;
/** @type {__VLS_StyleScopedClasses['suggest-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['custom-input']} */ ;
/** @type {__VLS_StyleScopedClasses['test-action-line']} */ ;
/** @type {__VLS_StyleScopedClasses['test-inline-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['test-feedback-box']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['card-head-line']} */ ;
/** @type {__VLS_StyleScopedClasses['head-left']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['emb-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-name']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-status-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-intro']} */ ;
/** @type {__VLS_StyleScopedClasses['provider-switch-group']} */ ;
/** @type {__VLS_StyleScopedClasses['provider-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['provider-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['cloud-openai']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-form-stack']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['custom-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['custom-input']} */ ;
/** @type {__VLS_StyleScopedClasses['suggest-tags-row']} */ ;
/** @type {__VLS_StyleScopedClasses['suggest-title']} */ ;
/** @type {__VLS_StyleScopedClasses['suggest-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['custom-input']} */ ;
/** @type {__VLS_StyleScopedClasses['test-action-line']} */ ;
/** @type {__VLS_StyleScopedClasses['test-inline-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['test-feedback-box']} */ ;
/** @type {__VLS_StyleScopedClasses['global-save-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-left']} */ ;
/** @type {__VLS_StyleScopedClasses['version-label']} */ ;
/** @type {__VLS_StyleScopedClasses['footer-right']} */ ;
/** @type {__VLS_StyleScopedClasses['action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['cancel-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['save-btn']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            loading: loading,
            saving: saving,
            testingChat: testingChat,
            testingEmb: testingEmb,
            userRole: userRole,
            isAdmin: isAdmin,
            chatProvider: chatProvider,
            chatModel: chatModel,
            chatBaseUrl: chatBaseUrl,
            chatApiKey: chatApiKey,
            chatTestResult: chatTestResult,
            embProvider: embProvider,
            embModel: embModel,
            embBaseUrl: embBaseUrl,
            embApiKey: embApiKey,
            embTestResult: embTestResult,
            saveNotice: saveNotice,
            chatSuggestions: chatSuggestions,
            embSuggestions: embSuggestions,
            getRoleLabel: getRoleLabel,
            switchChatProvider: switchChatProvider,
            switchEmbProvider: switchEmbProvider,
            quickSwitchToAdmin: quickSwitchToAdmin,
            testChatEngine: testChatEngine,
            testEmbEngine: testEmbEngine,
            saveDualConfig: saveDualConfig,
            close: close,
        };
    },
    __typeEmits: {},
    __typeProps: {},
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
    __typeEmits: {},
    __typeProps: {},
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=EngineSettingsModal.vue.js.map