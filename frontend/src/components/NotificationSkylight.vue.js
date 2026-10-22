import { ref, computed, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { notificationApi } from '../api/user';
import { Bell, Check, Notification, ChatDotRound, StarFilled } from '@element-plus/icons-vue';
const props = withDefaults(defineProps(), {
    modelValue: false,
    unreadCounts: () => ({ total: 0, announcements: 0, replies: 0, likes: 0 })
});
const emit = defineEmits();
const router = useRouter();
const activeCategory = ref('ANNOUNCEMENT');
const notifications = ref([]);
const isLoading = ref(false);
const isMarkingAll = ref(false);
const currentTabUnread = computed(() => {
    if (activeCategory.value === 'ANNOUNCEMENT')
        return props.unreadCounts.announcements;
    if (activeCategory.value === 'REPLY')
        return props.unreadCounts.replies;
    if (activeCategory.value === 'LIKE')
        return props.unreadCounts.likes;
    return 0;
});
function closeDrawer() {
    emit('update:modelValue', false);
}
function selectTab(cat) {
    activeCategory.value = cat;
    fetchFeed(cat);
}
async function fetchFeed(cat) {
    isLoading.value = true;
    try {
        const res = await notificationApi.getNotifications(cat, 1, 30);
        if (res?.data?.items) {
            notifications.value = res.data.items;
        }
        else {
            notifications.value = [];
        }
    }
    catch (err) {
        console.warn('Failed to load notifications:', err);
        notifications.value = [];
    }
    finally {
        isLoading.value = false;
    }
}
async function handleMarkAllRead() {
    if (isMarkingAll.value)
        return;
    isMarkingAll.value = true;
    try {
        await notificationApi.markAllRead(activeCategory.value);
        // Mark local items as read
        notifications.value.forEach(item => { item.is_read = true; });
        emit('unreadCountChanged');
    }
    catch (err) {
        console.error('Failed to mark all read:', err);
    }
    finally {
        isMarkingAll.value = false;
    }
}
async function handleNotificationClick(item) {
    // 1. Mark single notification as read if unread
    if (!item.is_read) {
        try {
            await notificationApi.markRead(item.id);
            item.is_read = true;
            emit('unreadCountChanged');
        }
        catch (e) {
            console.warn('Failed to mark notification read:', e);
        }
    }
    // 2. Direct jump according to notification type
    closeDrawer();
    if (item.category === 'REPLY') {
        if (item.video_id) {
            let url = `/play?videoId=${item.video_id}`;
            if (item.episode_id)
                url += `&episodeId=${item.episode_id}`;
            if (item.comment_id)
                url += `&commentId=${item.comment_id}`;
            router.push(url);
        }
    }
    else if (item.category === 'LIKE') {
        if (item.video_id) {
            let url = `/play?videoId=${item.video_id}`;
            if (item.episode_id)
                url += `&episodeId=${item.episode_id}`;
            router.push(url);
        }
    }
    else if (item.category === 'ANNOUNCEMENT') {
        if (item.video_id) {
            router.push(`/play?videoId=${item.video_id}`);
        }
    }
}
watch(() => props.modelValue, (val) => {
    if (val) {
        fetchFeed(activeCategory.value);
    }
});
onMounted(() => {
    if (props.modelValue) {
        fetchFeed(activeCategory.value);
    }
});
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_withDefaultsArg = (function (t) { return t; })({
    modelValue: false,
    unreadCounts: () => ({ total: 0, announcements: 0, replies: 0, likes: 0 })
});
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['notification-skylight-drawer']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-header']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-action-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-action-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-action-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-close-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-tab-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-icon-circle']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-card']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-card']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-card']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-card']} */ ;
// CSS variable injection 
// CSS variable injection end 
if (__VLS_ctx.modelValue) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "skylight-wrapper" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ onClick: (__VLS_ctx.closeDrawer) },
        ...{ class: "skylight-backdrop" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.aside, __VLS_intrinsicElements.aside)({
        ...{ class: "notification-skylight-drawer" },
        id: "notification-skylight-drawer",
        role: "dialog",
        'aria-label': "通知天窗",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.header, __VLS_intrinsicElements.header)({
        ...{ class: "skylight-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "skylight-header-left" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "skylight-icon-squircle" },
    });
    const __VLS_0 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
        size: (16),
    }));
    const __VLS_2 = __VLS_1({
        size: (16),
    }, ...__VLS_functionalComponentArgsRest(__VLS_1));
    __VLS_3.slots.default;
    const __VLS_4 = {}.Bell;
    /** @type {[typeof __VLS_components.Bell, ]} */ ;
    // @ts-ignore
    const __VLS_5 = __VLS_asFunctionalComponent(__VLS_4, new __VLS_4({}));
    const __VLS_6 = __VLS_5({}, ...__VLS_functionalComponentArgsRest(__VLS_5));
    var __VLS_3;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "skylight-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "skylight-subtitle" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "skylight-header-right" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.handleMarkAllRead) },
        type: "button",
        ...{ class: "skylight-action-pill" },
        id: "btn-skylight-mark-all-read",
        disabled: (__VLS_ctx.isMarkingAll || __VLS_ctx.currentTabUnread === 0),
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
    const __VLS_12 = {}.Check;
    /** @type {[typeof __VLS_components.Check, ]} */ ;
    // @ts-ignore
    const __VLS_13 = __VLS_asFunctionalComponent(__VLS_12, new __VLS_12({}));
    const __VLS_14 = __VLS_13({}, ...__VLS_functionalComponentArgsRest(__VLS_13));
    var __VLS_11;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.closeDrawer) },
        type: "button",
        ...{ class: "skylight-close-btn" },
        id: "btn-close-skylight",
        title: "关闭天窗",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "skylight-tab-bar" },
        role: "tablist",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.modelValue))
                    return;
                __VLS_ctx.selectTab('ANNOUNCEMENT');
            } },
        type: "button",
        ...{ class: "skylight-tab-btn" },
        ...{ class: ({ active: __VLS_ctx.activeCategory === 'ANNOUNCEMENT' }) },
        id: "skylight-tab-announcements",
        role: "tab",
        'aria-selected': (__VLS_ctx.activeCategory === 'ANNOUNCEMENT'),
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    if (__VLS_ctx.unreadCounts.announcements > 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "skylight-tab-badge" },
        });
        (__VLS_ctx.unreadCounts.announcements > 99 ? '99+' : __VLS_ctx.unreadCounts.announcements);
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.modelValue))
                    return;
                __VLS_ctx.selectTab('REPLY');
            } },
        type: "button",
        ...{ class: "skylight-tab-btn" },
        ...{ class: ({ active: __VLS_ctx.activeCategory === 'REPLY' }) },
        id: "skylight-tab-replies",
        role: "tab",
        'aria-selected': (__VLS_ctx.activeCategory === 'REPLY'),
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    if (__VLS_ctx.unreadCounts.replies > 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "skylight-tab-badge" },
        });
        (__VLS_ctx.unreadCounts.replies > 99 ? '99+' : __VLS_ctx.unreadCounts.replies);
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.modelValue))
                    return;
                __VLS_ctx.selectTab('LIKE');
            } },
        type: "button",
        ...{ class: "skylight-tab-btn" },
        ...{ class: ({ active: __VLS_ctx.activeCategory === 'LIKE' }) },
        id: "skylight-tab-likes",
        role: "tab",
        'aria-selected': (__VLS_ctx.activeCategory === 'LIKE'),
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    if (__VLS_ctx.unreadCounts.likes > 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "skylight-tab-badge" },
        });
        (__VLS_ctx.unreadCounts.likes > 99 ? '99+' : __VLS_ctx.unreadCounts.likes);
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "skylight-body" },
    });
    if (__VLS_ctx.isLoading) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "skylight-loading-state" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "skylight-spinner" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    else if (__VLS_ctx.notifications.length === 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "skylight-empty-state" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty-icon-circle" },
        });
        const __VLS_16 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_17 = __VLS_asFunctionalComponent(__VLS_16, new __VLS_16({
            size: (24),
        }));
        const __VLS_18 = __VLS_17({
            size: (24),
        }, ...__VLS_functionalComponentArgsRest(__VLS_17));
        __VLS_19.slots.default;
        const __VLS_20 = {}.Check;
        /** @type {[typeof __VLS_components.Check, ]} */ ;
        // @ts-ignore
        const __VLS_21 = __VLS_asFunctionalComponent(__VLS_20, new __VLS_20({}));
        const __VLS_22 = __VLS_21({}, ...__VLS_functionalComponentArgsRest(__VLS_21));
        var __VLS_19;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "empty-title" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "empty-desc" },
        });
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "skylight-list" },
        });
        for (const [item] of __VLS_getVForSourceType((__VLS_ctx.notifications))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.article, __VLS_intrinsicElements.article)({
                ...{ onClick: (...[$event]) => {
                        if (!(__VLS_ctx.modelValue))
                            return;
                        if (!!(__VLS_ctx.isLoading))
                            return;
                        if (!!(__VLS_ctx.notifications.length === 0))
                            return;
                        __VLS_ctx.handleNotificationClick(item);
                    } },
                key: (item.id),
                ...{ class: "skylight-card" },
                ...{ class: ({ unread: !item.is_read }) },
            });
            if (!item.is_read) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                    ...{ class: "unread-dot" },
                    'aria-label': "未读",
                });
            }
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "card-avatar-wrap" },
            });
            if (item.sender_avatar) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
                    src: (item.sender_avatar),
                    ...{ class: "card-avatar-img" },
                    alt: "头像",
                });
            }
            else {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "card-avatar-fallback" },
                });
                const __VLS_24 = {}.ElIcon;
                /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
                // @ts-ignore
                const __VLS_25 = __VLS_asFunctionalComponent(__VLS_24, new __VLS_24({
                    size: (16),
                }));
                const __VLS_26 = __VLS_25({
                    size: (16),
                }, ...__VLS_functionalComponentArgsRest(__VLS_25));
                __VLS_27.slots.default;
                if (item.category === 'ANNOUNCEMENT') {
                    const __VLS_28 = {}.Notification;
                    /** @type {[typeof __VLS_components.Notification, ]} */ ;
                    // @ts-ignore
                    const __VLS_29 = __VLS_asFunctionalComponent(__VLS_28, new __VLS_28({}));
                    const __VLS_30 = __VLS_29({}, ...__VLS_functionalComponentArgsRest(__VLS_29));
                }
                else if (item.category === 'REPLY') {
                    const __VLS_32 = {}.ChatDotRound;
                    /** @type {[typeof __VLS_components.ChatDotRound, ]} */ ;
                    // @ts-ignore
                    const __VLS_33 = __VLS_asFunctionalComponent(__VLS_32, new __VLS_32({}));
                    const __VLS_34 = __VLS_33({}, ...__VLS_functionalComponentArgsRest(__VLS_33));
                }
                else {
                    const __VLS_36 = {}.StarFilled;
                    /** @type {[typeof __VLS_components.StarFilled, ]} */ ;
                    // @ts-ignore
                    const __VLS_37 = __VLS_asFunctionalComponent(__VLS_36, new __VLS_36({}));
                    const __VLS_38 = __VLS_37({}, ...__VLS_functionalComponentArgsRest(__VLS_37));
                }
                var __VLS_27;
            }
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "card-info-wrap" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "card-top-row" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "card-sender-name" },
            });
            (item.sender_name || '系统通知');
            __VLS_asFunctionalElement(__VLS_intrinsicElements.time, __VLS_intrinsicElements.time)({
                ...{ class: "card-time-text" },
            });
            (item.created_at);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
                ...{ class: "card-title" },
            });
            (item.title);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
                ...{ class: "card-content-text" },
            });
            (item.content);
        }
    }
}
/** @type {__VLS_StyleScopedClasses['skylight-wrapper']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-backdrop']} */ ;
/** @type {__VLS_StyleScopedClasses['notification-skylight-drawer']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-header']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-header-left']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-icon-squircle']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-title']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-subtitle']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-header-right']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-action-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-close-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-tab-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-tab-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-tab-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-tab-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-body']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-loading-state']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-spinner']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-empty-state']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-icon-circle']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-title']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-list']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-card']} */ ;
/** @type {__VLS_StyleScopedClasses['unread-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['card-avatar-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['card-avatar-img']} */ ;
/** @type {__VLS_StyleScopedClasses['card-avatar-fallback']} */ ;
/** @type {__VLS_StyleScopedClasses['card-info-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['card-top-row']} */ ;
/** @type {__VLS_StyleScopedClasses['card-sender-name']} */ ;
/** @type {__VLS_StyleScopedClasses['card-time-text']} */ ;
/** @type {__VLS_StyleScopedClasses['card-title']} */ ;
/** @type {__VLS_StyleScopedClasses['card-content-text']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            Bell: Bell,
            Check: Check,
            Notification: Notification,
            ChatDotRound: ChatDotRound,
            StarFilled: StarFilled,
            activeCategory: activeCategory,
            notifications: notifications,
            isLoading: isLoading,
            isMarkingAll: isMarkingAll,
            currentTabUnread: currentTabUnread,
            closeDrawer: closeDrawer,
            selectTab: selectTab,
            handleMarkAllRead: handleMarkAllRead,
            handleNotificationClick: handleNotificationClick,
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
//# sourceMappingURL=NotificationSkylight.vue.js.map