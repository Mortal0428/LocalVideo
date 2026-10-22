/// <reference types="../../node_modules/.vue-global-types/vue_3.5_0_0_0.d.ts" />
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import GlobalHeader from '../components/GlobalHeader.vue';
import { userApi } from '../api/user';
import { favoritesApi } from '../api/favorites';
const router = useRouter();
const profile = ref(null);
const historyList = ref([]);
const likesList = ref([]);
const activeTab = ref('history');
// Economy & VIP Center State (Feature 21)
const walletData = ref({
    balance: 50,
    total_earned: 50,
    total_spent: 0,
    has_signed_today: false,
    ad_watch_count_today: 0
});
const isSigningIn = ref(false);
const isWatchingAd = ref(false);
const adCountdownText = ref('');
const isExchangingVip = ref(false);
const isUserVip = computed(() => {
    if (!profile.value)
        return false;
    if (profile.value.is_vip)
        return true;
    if (profile.value.vip_expire_at) {
        return new Date(profile.value.vip_expire_at).getTime() > Date.now();
    }
    return false;
});
const vipExpiryDisplay = computed(() => {
    if (!profile.value?.vip_expire_at)
        return '未开通';
    const d = new Date(profile.value.vip_expire_at);
    if (d.getTime() <= Date.now())
        return '已到期';
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
});
async function loadWalletData() {
    try {
        const res = await userApi.getCoinWallet();
        if (res?.data) {
            walletData.value = res.data;
        }
    }
    catch (err) {
        console.warn('Failed to load coin wallet:', err);
    }
}
async function handleDailySignIn() {
    if (walletData.value.has_signed_today || isSigningIn.value)
        return;
    isSigningIn.value = true;
    try {
        const res = await userApi.dailySignIn();
        if (res?.data) {
            walletData.value.balance = res.data.balance;
            walletData.value.has_signed_today = true;
            walletData.value.total_earned += res.data.reward || 10;
        }
    }
    catch (err) {
        alert(err?.response?.data?.detail || err?.message || '签到失败');
    }
    finally {
        isSigningIn.value = false;
    }
}
async function handleWatchAd() {
    if (isWatchingAd.value)
        return;
    isWatchingAd.value = true;
    adCountdownText.value = '正在观看广告 (5s)...';
    // Call reward API immediately to ensure instant persistence
    try {
        const res = await userApi.watchAdReward();
        if (res?.data) {
            walletData.value.balance = res.data.balance;
            walletData.value.total_earned += res.data.reward || 5;
        }
    }
    catch (err) {
        console.warn('Ad reward API error:', err);
    }
    // Visual countdown
    let left = 4;
    const timer = setInterval(() => {
        if (left > 0) {
            adCountdownText.value = `正在观看广告 (${left}s)...`;
            left--;
        }
        else {
            clearInterval(timer);
            isWatchingAd.value = false;
            adCountdownText.value = '';
        }
    }, 1000);
}
async function handleExchangeVip(days, cost) {
    if (walletData.value.balance < cost || isExchangingVip.value)
        return;
    isExchangingVip.value = true;
    try {
        const res = await userApi.exchangeVip({ days, cost });
        if (res?.data) {
            walletData.value.balance = res.data.balance;
            walletData.value.total_spent += cost;
            if (profile.value) {
                profile.value.vip_expire_at = res.data.vip_expire_at;
                profile.value.is_vip = true;
            }
        }
    }
    catch (err) {
        alert(err?.response?.data?.detail || err?.message || 'VIP 兑换失败');
    }
    finally {
        isExchangingVip.value = false;
    }
}
// Multi-level Favorites State
const foldersList = ref([]);
const currentFolderId = ref('');
const currentFolder = computed(() => foldersList.value.find(f => f.id === currentFolderId.value));
const folderItems = ref([]);
const folderItemsLoading = ref(false);
const totalFavoritesCount = computed(() => {
    return foldersList.value.reduce((sum, f) => sum + (f.item_count || 0), 0);
});
const showFolderModal = ref(false);
const editingFolderId = ref(null);
const isSubmittingFolder = ref(false);
const folderForm = reactive({
    name: '',
    description: '',
    is_public: false
});
const defaultAvatar = 'https://api.dicebear.com/7.x/bottts/svg?seed=default_viewer';
const defaultCover = 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=640&q=80';
const avatarSeeds = ['viewer_1', 'creator_pro', 'drama_queen', 'cyber_cat', 'speed_stream'];
const editForm = reactive({
    nickname: '',
    bio: '',
    avatar_url: ''
});
const applyForm = reactive({
    creator_name: '',
    bio: ''
});
const showApplyModal = ref(false);
const isApplying = ref(false);
const isSaving = ref(false);
const saveNotice = ref('');
onMounted(async () => {
    await loadUserData();
    await loadFoldersData();
    await loadWalletData();
});
async function loadUserData() {
    try {
        const pRes = await userApi.getProfile();
        const pData = pRes?.data || pRes;
        profile.value = pData;
        editForm.nickname = pData?.nickname || '';
        editForm.bio = pData?.creator_bio || '';
        editForm.avatar_url = pData?.avatar_url || '';
        applyForm.creator_name = (pData?.nickname || pData?.username) + '的创作空间';
        // Load history and likes
        const hRes = await userApi.getHistory();
        historyList.value = hRes?.data || [];
        const lRes = await userApi.getLikes();
        likesList.value = lRes?.data || [];
    }
    catch (err) {
        console.warn('Failed to load user profile, checking local auth state:', err);
        const localUser = localStorage.getItem('user');
        if (localUser) {
            try {
                const u = JSON.parse(localUser);
                profile.value = {
                    ...u,
                    stats: { history_count: 0, likes_count: 0, creator_videos_count: 0 }
                };
            }
            catch (e) { }
        }
        else {
            router.push('/login?redirect=/user/space');
        }
    }
}
async function loadFoldersData() {
    try {
        const res = await favoritesApi.getFolders();
        const data = res?.data || res;
        foldersList.value = Array.isArray(data) ? data : [];
        if (foldersList.value.length > 0) {
            if (!currentFolderId.value || !foldersList.value.some(f => f.id === currentFolderId.value)) {
                currentFolderId.value = foldersList.value[0].id;
            }
            await loadFolderItems(currentFolderId.value);
        }
    }
    catch (err) {
        console.warn('Failed to load favorite folders:', err);
    }
}
async function selectFolder(folderId) {
    currentFolderId.value = folderId;
    await loadFolderItems(folderId);
}
async function loadFolderItems(folderId) {
    if (!folderId)
        return;
    folderItemsLoading.value = true;
    try {
        const res = await favoritesApi.getFolderItems(folderId);
        const data = res?.data || res;
        folderItems.value = Array.isArray(data) ? data : [];
    }
    catch (err) {
        console.warn('Failed to load folder items:', err);
        folderItems.value = [];
    }
    finally {
        folderItemsLoading.value = false;
    }
}
function openCreateFolderModal() {
    editingFolderId.value = null;
    folderForm.name = '';
    folderForm.description = '';
    folderForm.is_public = false;
    showFolderModal.value = true;
}
function openEditFolderModal(f) {
    editingFolderId.value = f.id;
    folderForm.name = f.name;
    folderForm.description = f.description || '';
    folderForm.is_public = f.is_public;
    showFolderModal.value = true;
}
async function submitFolderForm() {
    const name = folderForm.name.trim();
    if (!name)
        return;
    isSubmittingFolder.value = true;
    try {
        if (editingFolderId.value) {
            await favoritesApi.updateFolder(editingFolderId.value, {
                name,
                description: folderForm.description,
                is_public: folderForm.is_public
            });
        }
        else {
            const res = await favoritesApi.createFolder({
                name,
                description: folderForm.description,
                is_public: folderForm.is_public
            });
            const created = res?.data || res;
            if (created && created.id) {
                currentFolderId.value = created.id;
            }
        }
        showFolderModal.value = false;
        await loadFoldersData();
    }
    catch (err) {
        alert(err?.response?.data?.detail || '操作失败，请重试');
    }
    finally {
        isSubmittingFolder.value = false;
    }
}
async function handleDeleteFolder(folderId) {
    if (!confirm('确认删除该收藏夹？其中的收藏短剧将被清空。'))
        return;
    try {
        await favoritesApi.deleteFolder(folderId);
        currentFolderId.value = '';
        await loadFoldersData();
    }
    catch (err) {
        alert(err?.response?.data?.detail || '删除失败');
    }
}
async function handleRemoveFromFolder(videoId) {
    if (!currentFolderId.value)
        return;
    try {
        await favoritesApi.removeFolderItem(currentFolderId.value, videoId);
        await loadFolderItems(currentFolderId.value);
        const f = foldersList.value.find(f => f.id === currentFolderId.value);
        if (f && f.item_count > 0) {
            f.item_count -= 1;
        }
    }
    catch (err) {
        alert(err?.response?.data?.detail || '移除失败');
    }
}
function formatDate(isoStr) {
    if (!isoStr)
        return '';
    try {
        const d = new Date(isoStr);
        return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`;
    }
    catch (e) {
        return isoStr;
    }
}
function getRoleBadgeText(role) {
    switch (role) {
        case 'CREATOR': return '🎬 认证创作者';
        case 'ADMIN': return '⚡ 超级管理员';
        case 'REVIEWER': return '🛡️ 内容审核员';
        default: return '👤 普通观众';
    }
}
function formatDuration(seconds) {
    if (!seconds || seconds <= 0)
        return '00:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}
function openApplyModal() {
    showApplyModal.value = true;
}
const showReviewerModal = ref(false);
const isApplyingReviewer = ref(false);
const reviewerForm = reactive({
    reviewer_name: '',
    bio: ''
});
function openReviewerModal() {
    reviewerForm.reviewer_name = (profile.value?.nickname || profile.value?.username || '') + '（内容审核）';
    reviewerForm.bio = '';
    showReviewerModal.value = true;
}
async function submitCreatorApplication() {
    isApplying.value = true;
    try {
        const res = await userApi.applyCreator({
            creator_name: applyForm.creator_name,
            bio: applyForm.bio
        });
        alert(res?.message || '创作者资质申请已成功提交！请等待管理员在管理中台审核。');
        showApplyModal.value = false;
        await loadUserData();
    }
    catch (err) {
        alert('申请提交失败: ' + (err?.message || '网络错误'));
    }
    finally {
        isApplying.value = false;
    }
}
async function submitReviewerApplication() {
    isApplyingReviewer.value = true;
    try {
        const res = await userApi.applyReviewer({
            reviewer_name: reviewerForm.reviewer_name,
            bio: reviewerForm.bio
        });
        alert(res?.message || '审核员资质申请已成功提交！请等待管理员在管理中台审核通过。');
        showReviewerModal.value = false;
        await loadUserData();
    }
    catch (err) {
        alert('审核员申请失败: ' + (err?.message || '网络错误'));
    }
    finally {
        isApplyingReviewer.value = false;
    }
}
async function saveProfile() {
    isSaving.value = true;
    saveNotice.value = '';
    try {
        await userApi.updateProfile({
            nickname: editForm.nickname,
            bio: editForm.bio,
            avatar_url: editForm.avatar_url
        });
        saveNotice.value = '✅ 资料修改已生效';
        await loadUserData();
        setTimeout(() => { saveNotice.value = ''; }, 3000);
    }
    catch (err) {
        saveNotice.value = '❌ 保存失败: ' + (err?.message || '网络错误');
    }
    finally {
        isSaving.value = false;
    }
}
function handleLogout() {
    localStorage.removeItem('cinema_access_token');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['role-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['role-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['role-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['role-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['action-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['action-btn-danger']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-card']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-text']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-text']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['history-card']} */ ;
/** @type {__VLS_StyleScopedClasses['like-info']} */ ;
/** @type {__VLS_StyleScopedClasses['form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['avatar-preset-item']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-header']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-pill-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-folder-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-folder-action']} */ ;
/** @type {__VLS_StyleScopedClasses['edit']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-folder-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-folder-action']} */ ;
/** @type {__VLS_StyleScopedClasses['delete']} */ ;
/** @type {__VLS_StyleScopedClasses['fav-drama-card']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-remove-fav']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-play-direct']} */ ;
/** @type {__VLS_StyleScopedClasses['switch-container']} */ ;
/** @type {__VLS_StyleScopedClasses['switch-slider']} */ ;
/** @type {__VLS_StyleScopedClasses['switch-container']} */ ;
/** @type {__VLS_StyleScopedClasses['switch-slider']} */ ;
/** @type {__VLS_StyleScopedClasses['switch-container']} */ ;
/** @type {__VLS_StyleScopedClasses['switch-slider']} */ ;
/** @type {__VLS_StyleScopedClasses['economy-bento-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['economy-card']} */ ;
/** @type {__VLS_StyleScopedClasses['wstat-value']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-bento-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-signin']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-signin']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-ad']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-ad']} */ ;
/** @type {__VLS_StyleScopedClasses['vip-status-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-exchange']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-exchange']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "user-space-page" },
    id: "user-space-root",
});
/** @type {[typeof GlobalHeader, ]} */ ;
// @ts-ignore
const __VLS_0 = __VLS_asFunctionalComponent(GlobalHeader, new GlobalHeader({}));
const __VLS_1 = __VLS_0({}, ...__VLS_functionalComponentArgsRest(__VLS_0));
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "space-ambient-glow glow-top" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "space-ambient-glow glow-bottom" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "space-container" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.header, __VLS_intrinsicElements.header)({
    ...{ class: "space-hero-card" },
    id: "user-hero-card",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "hero-avatar-wrap" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
    src: (__VLS_ctx.profile?.avatar_url || __VLS_ctx.defaultAvatar),
    ...{ class: "hero-avatar" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "role-badge" },
    ...{ class: ('role-' + (__VLS_ctx.profile?.role?.toLowerCase() || 'user')) },
});
(__VLS_ctx.getRoleBadgeText(__VLS_ctx.profile?.role));
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "hero-info" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "hero-name-row" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({
    ...{ class: "hero-nickname" },
    id: "profile-nickname",
});
(__VLS_ctx.profile?.nickname || __VLS_ctx.profile?.username || '剧迷朋友');
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "hero-username" },
});
(__VLS_ctx.profile?.username);
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "status-pill status-active" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "hero-bio" },
});
(__VLS_ctx.profile?.creator_bio || '这个人很低调，还没有写个人简介~');
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "hero-stats-row" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.activeTab = 'history';
        } },
    ...{ class: "stat-item" },
    id: "stat-history-tab",
    ...{ style: {} },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-val" },
    id: "stat-history-count",
});
(__VLS_ctx.profile?.stats?.history_count || __VLS_ctx.historyList.length || 0);
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-lbl" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "stat-sep" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.activeTab = 'likes';
        } },
    ...{ class: "stat-item" },
    id: "stat-likes-tab",
    ...{ style: {} },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-val" },
    id: "stat-likes-count",
});
(__VLS_ctx.profile?.stats?.likes_count || __VLS_ctx.likesList.length || 0);
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-lbl" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "stat-sep" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.activeTab = 'favorites';
        } },
    ...{ class: "stat-item" },
    id: "stat-favorites-tab",
    ...{ style: {} },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-val" },
    id: "stat-favorites-count",
});
(__VLS_ctx.totalFavoritesCount);
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-lbl" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "stat-sep" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "stat-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-val" },
});
(__VLS_ctx.profile?.stats?.creator_videos_count || 0);
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "stat-lbl" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "hero-actions" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.activeTab = 'profile';
        } },
    ...{ class: "action-btn-secondary" },
    title: "编辑个人资料",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "economy-bento-grid" },
    id: "economy-bento-section",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "economy-card glass-panel" },
    id: "user-wallet-card",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "card-header-row" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "header-icon-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "card-emoji" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
    ...{ class: "card-heading" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "card-subheading" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "wallet-badge-pill" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "balance-num" },
});
(__VLS_ctx.walletData.balance);
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "balance-unit" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "wallet-stats-strip" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "wallet-stat-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "wstat-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "wstat-value" },
});
(__VLS_ctx.walletData.total_earned);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "wallet-stat-sep" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "wallet-stat-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "wstat-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "wstat-value" },
});
(__VLS_ctx.walletData.total_spent);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "wallet-stat-sep" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "wallet-stat-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "wstat-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "wstat-value" },
    ...{ class: ({ 'text-success': __VLS_ctx.walletData.has_signed_today }) },
});
(__VLS_ctx.walletData.has_signed_today ? '已完成' : '待领取');
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "economy-actions-row" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.handleDailySignIn) },
    ...{ class: "apple-bento-btn btn-signin" },
    id: "btn-daily-signin",
    disabled: (__VLS_ctx.walletData.has_signed_today || __VLS_ctx.isSigningIn),
});
if (__VLS_ctx.walletData.has_signed_today) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
else if (__VLS_ctx.isSigningIn) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.handleWatchAd) },
    ...{ class: "apple-bento-btn btn-ad" },
    id: "btn-watch-ad",
    disabled: (__VLS_ctx.isWatchingAd),
});
if (__VLS_ctx.isWatchingAd) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.adCountdownText);
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "economy-card glass-panel" },
    id: "user-vip-card",
    ...{ class: ({ 'is-vip-active': __VLS_ctx.isUserVip }) },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "card-header-row" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "header-icon-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "card-emoji" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
    ...{ class: "card-heading" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "card-subheading" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "vip-status-pill" },
    ...{ class: ({ active: __VLS_ctx.isUserVip }) },
});
(__VLS_ctx.isUserVip ? 'VIP 会员生效中' : '普通用户');
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "vip-expiry-box" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "vip-expiry-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "vip-expiry-val" },
});
(__VLS_ctx.vipExpiryDisplay);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "vip-tiers-grid" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "vip-tier-card" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "tier-info" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "tier-name" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "tier-cost" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.handleExchangeVip(7, 100);
        } },
    ...{ class: "apple-bento-btn mini btn-exchange" },
    id: "btn-exchange-vip-7d",
    disabled: (__VLS_ctx.walletData.balance < 100 || __VLS_ctx.isExchangingVip),
});
(__VLS_ctx.walletData.balance < 100 ? '金币不足' : '立即兑换');
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "vip-tier-card" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "tier-info" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "tier-name" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "tier-cost" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.handleExchangeVip(30, 200);
        } },
    ...{ class: "apple-bento-btn mini btn-exchange" },
    id: "btn-exchange-vip-30d",
    disabled: (__VLS_ctx.walletData.balance < 200 || __VLS_ctx.isExchangingVip),
});
(__VLS_ctx.walletData.balance < 200 ? '金币不足' : '立即兑换');
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "creator-qualification-grid" },
    id: "dual-qualification-box",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "qual-card glass-panel" },
    ...{ class: ({ 'is-active': __VLS_ctx.profile?.role === 'ADMIN' || __VLS_ctx.profile?.role === 'CREATOR' || __VLS_ctx.profile?.is_creator }) },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "qual-content" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "qual-icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "qual-text" },
});
if (__VLS_ctx.profile?.role === 'ADMIN' || __VLS_ctx.profile?.role === 'CREATOR' || __VLS_ctx.profile?.is_creator) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
}
else if (__VLS_ctx.profile?.creator_application_status === 'PENDING') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "qual-action-wrap" },
});
if (__VLS_ctx.profile?.role === 'ADMIN' || __VLS_ctx.profile?.role === 'CREATOR' || __VLS_ctx.profile?.is_creator) {
    const __VLS_3 = {}.RouterLink;
    /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
    // @ts-ignore
    const __VLS_4 = __VLS_asFunctionalComponent(__VLS_3, new __VLS_3({
        to: "/creator",
        ...{ class: "qual-action-btn btn-enter-creator" },
        id: "btn-enter-studio",
    }));
    const __VLS_5 = __VLS_4({
        to: "/creator",
        ...{ class: "qual-action-btn btn-enter-creator" },
        id: "btn-enter-studio",
    }, ...__VLS_functionalComponentArgsRest(__VLS_4));
    __VLS_6.slots.default;
    var __VLS_6;
}
else if (__VLS_ctx.profile?.creator_application_status === 'PENDING') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ class: "qual-action-btn btn-pending" },
        disabled: true,
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.openApplyModal) },
        ...{ class: "qual-action-btn btn-apply-creator" },
        id: "btn-apply-creator",
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "qual-card glass-panel" },
    ...{ class: ({ 'is-active': __VLS_ctx.profile?.role === 'ADMIN' || __VLS_ctx.profile?.role === 'REVIEWER' || __VLS_ctx.profile?.is_reviewer }) },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "qual-content" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "qual-icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "qual-text" },
});
if (__VLS_ctx.profile?.role === 'ADMIN' || __VLS_ctx.profile?.role === 'REVIEWER' || __VLS_ctx.profile?.is_reviewer) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
}
else if (__VLS_ctx.profile?.reviewer_application_status === 'PENDING') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "qual-action-wrap" },
});
if (__VLS_ctx.profile?.role === 'ADMIN' || __VLS_ctx.profile?.role === 'REVIEWER' || __VLS_ctx.profile?.is_reviewer) {
    const __VLS_7 = {}.RouterLink;
    /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
    // @ts-ignore
    const __VLS_8 = __VLS_asFunctionalComponent(__VLS_7, new __VLS_7({
        to: "/admin?tab=contents",
        ...{ class: "qual-action-btn btn-enter-reviewer" },
        id: "btn-enter-reviewer-space",
    }));
    const __VLS_9 = __VLS_8({
        to: "/admin?tab=contents",
        ...{ class: "qual-action-btn btn-enter-reviewer" },
        id: "btn-enter-reviewer-space",
    }, ...__VLS_functionalComponentArgsRest(__VLS_8));
    __VLS_10.slots.default;
    var __VLS_10;
}
else if (__VLS_ctx.profile?.reviewer_application_status === 'PENDING') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ class: "qual-action-btn btn-pending" },
        disabled: true,
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.openReviewerModal) },
        ...{ class: "qual-action-btn btn-apply-reviewer" },
        id: "btn-apply-reviewer",
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "space-tabs-section" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "space-tab-bar" },
    id: "space-tab-bar",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.activeTab = 'history';
        } },
    ...{ class: "tab-btn" },
    ...{ class: ({ active: __VLS_ctx.activeTab === 'history' }) },
    id: "tab-btn-space-history",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(__VLS_ctx.historyList.length);
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.activeTab = 'likes';
        } },
    ...{ class: "tab-btn" },
    ...{ class: ({ active: __VLS_ctx.activeTab === 'likes' }) },
    id: "tab-btn-space-likes",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(__VLS_ctx.likesList.length);
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.activeTab = 'favorites';
        } },
    ...{ class: "tab-btn" },
    ...{ class: ({ active: __VLS_ctx.activeTab === 'favorites' }) },
    id: "tab-btn-space-favorites",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(__VLS_ctx.totalFavoritesCount);
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.activeTab = 'profile';
        } },
    ...{ class: "tab-btn" },
    ...{ class: ({ active: __VLS_ctx.activeTab === 'profile' }) },
    id: "tab-btn-space-profile",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
if (__VLS_ctx.activeTab === 'history') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "tab-pane" },
        id: "pane-history",
    });
    if (__VLS_ctx.historyList.length === 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty-state-box" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty-icon" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty-title" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "empty-sub" },
        });
        const __VLS_11 = {}.RouterLink;
        /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
        // @ts-ignore
        const __VLS_12 = __VLS_asFunctionalComponent(__VLS_11, new __VLS_11({
            to: "/",
            ...{ class: "action-btn-primary" },
        }));
        const __VLS_13 = __VLS_12({
            to: "/",
            ...{ class: "action-btn-primary" },
        }, ...__VLS_functionalComponentArgsRest(__VLS_12));
        __VLS_14.slots.default;
        var __VLS_14;
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "history-grid" },
            id: "history-items-grid",
        });
        for (const [item] of __VLS_getVForSourceType((__VLS_ctx.historyList))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                key: (item.history_id),
                ...{ class: "history-card" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "history-cover-wrap" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
                src: (item.cover_url || __VLS_ctx.defaultCover),
                ...{ class: "history-cover" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "progress-bar-wrap" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "progress-bar-fill" },
                ...{ style: ({ width: item.progress_pct + '%' }) },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "ep-badge" },
            });
            (item.episode_num);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "history-details" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
                ...{ class: "history-drama-title" },
            });
            (item.drama_title);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "history-ep-title" },
            });
            (item.episode_title);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "history-progress-text" },
            });
            (__VLS_ctx.formatDuration(item.progress_seconds));
            (__VLS_ctx.formatDuration(item.duration_seconds));
            (item.progress_pct);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "history-footer" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "history-time" },
            });
            (item.updated_at);
            const __VLS_15 = {}.RouterLink;
            /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
            // @ts-ignore
            const __VLS_16 = __VLS_asFunctionalComponent(__VLS_15, new __VLS_15({
                to: ('/play?videoId=' + item.video_id + '&episodeId=' + (item.episode_id || item.last_episode_id) + '&time=' + (item.progress_seconds || 0)),
                ...{ class: "continue-play-btn" },
            }));
            const __VLS_17 = __VLS_16({
                to: ('/play?videoId=' + item.video_id + '&episodeId=' + (item.episode_id || item.last_episode_id) + '&time=' + (item.progress_seconds || 0)),
                ...{ class: "continue-play-btn" },
            }, ...__VLS_functionalComponentArgsRest(__VLS_16));
            __VLS_18.slots.default;
            var __VLS_18;
        }
    }
}
else if (__VLS_ctx.activeTab === 'likes') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "tab-pane" },
        id: "pane-likes",
    });
    if (__VLS_ctx.likesList.length === 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty-state-box" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty-icon" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty-title" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "empty-sub" },
        });
        const __VLS_19 = {}.RouterLink;
        /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
        // @ts-ignore
        const __VLS_20 = __VLS_asFunctionalComponent(__VLS_19, new __VLS_19({
            to: "/",
            ...{ class: "action-btn-primary" },
        }));
        const __VLS_21 = __VLS_20({
            to: "/",
            ...{ class: "action-btn-primary" },
        }, ...__VLS_functionalComponentArgsRest(__VLS_20));
        __VLS_22.slots.default;
        var __VLS_22;
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "likes-grid" },
        });
        for (const [like] of __VLS_getVForSourceType((__VLS_ctx.likesList))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                key: (like.like_id),
                ...{ class: "like-card" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
                src: (like.cover_url || __VLS_ctx.defaultCover),
                ...{ class: "like-cover" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "like-info" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
            (like.drama_title);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
            (like.episode_title);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "like-footer" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "like-time" },
            });
            (like.created_at);
            const __VLS_23 = {}.RouterLink;
            /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
            // @ts-ignore
            const __VLS_24 = __VLS_asFunctionalComponent(__VLS_23, new __VLS_23({
                to: ('/play?videoId=' + like.video_id),
                ...{ class: "play-link" },
            }));
            const __VLS_25 = __VLS_24({
                to: ('/play?videoId=' + like.video_id),
                ...{ class: "play-link" },
            }, ...__VLS_functionalComponentArgsRest(__VLS_24));
            __VLS_26.slots.default;
            var __VLS_26;
        }
    }
}
else if (__VLS_ctx.activeTab === 'favorites') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "tab-pane" },
        id: "pane-favorites",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "favorites-toolbar" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "toolbar-left" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "pane-section-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "pane-section-sub" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "toolbar-right" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.openCreateFolderModal) },
        ...{ class: "action-btn-primary mini" },
        id: "btn-open-create-folder",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "folders-pill-nav" },
        id: "folders-pill-nav",
    });
    for (const [folder] of __VLS_getVForSourceType((__VLS_ctx.foldersList))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!!(__VLS_ctx.activeTab === 'history'))
                        return;
                    if (!!(__VLS_ctx.activeTab === 'likes'))
                        return;
                    if (!(__VLS_ctx.activeTab === 'favorites'))
                        return;
                    __VLS_ctx.selectFolder(folder.id);
                } },
            key: (folder.id),
            ...{ class: "folder-pill-btn" },
            ...{ class: ({ active: __VLS_ctx.currentFolderId === folder.id }) },
            id: ('pill-folder-' + folder.id),
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "folder-pill-name" },
        });
        (folder.name);
        if (folder.is_default) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "folder-pill-badge default" },
            });
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "folder-pill-badge" },
            ...{ class: (folder.is_public ? 'public' : 'private') },
        });
        (folder.is_public ? '公开' : '私密');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "folder-pill-count" },
        });
        (folder.item_count);
    }
    if (__VLS_ctx.currentFolder) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "active-folder-header" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "folder-meta-text" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "folder-title-line" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
            ...{ class: "current-folder-title" },
            id: "current-folder-title",
        });
        (__VLS_ctx.currentFolder.name);
        if (__VLS_ctx.currentFolder.is_default) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "tag-default-capsule" },
            });
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "tag-privacy-capsule" },
            ...{ class: (__VLS_ctx.currentFolder.is_public ? 'public' : 'private') },
        });
        (__VLS_ctx.currentFolder.is_public ? '公开剧单' : '私密珍藏');
        if (__VLS_ctx.currentFolder.updated_at) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "folder-updated-date" },
            });
            (__VLS_ctx.formatDate(__VLS_ctx.currentFolder.updated_at));
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "current-folder-desc" },
        });
        (__VLS_ctx.currentFolder.description || '暂无简介');
        if (!__VLS_ctx.currentFolder.is_default) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "folder-header-actions" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!!(__VLS_ctx.activeTab === 'history'))
                            return;
                        if (!!(__VLS_ctx.activeTab === 'likes'))
                            return;
                        if (!(__VLS_ctx.activeTab === 'favorites'))
                            return;
                        if (!(__VLS_ctx.currentFolder))
                            return;
                        if (!(!__VLS_ctx.currentFolder.is_default))
                            return;
                        __VLS_ctx.openEditFolderModal(__VLS_ctx.currentFolder);
                    } },
                ...{ class: "btn-folder-action edit" },
                id: "btn-edit-folder",
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!!(__VLS_ctx.activeTab === 'history'))
                            return;
                        if (!!(__VLS_ctx.activeTab === 'likes'))
                            return;
                        if (!(__VLS_ctx.activeTab === 'favorites'))
                            return;
                        if (!(__VLS_ctx.currentFolder))
                            return;
                        if (!(!__VLS_ctx.currentFolder.is_default))
                            return;
                        __VLS_ctx.handleDeleteFolder(__VLS_ctx.currentFolder.id);
                    } },
                ...{ class: "btn-folder-action delete" },
                id: "btn-delete-folder",
            });
        }
    }
    if (__VLS_ctx.folderItemsLoading) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "loading-state-box" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    else if (__VLS_ctx.folderItems.length === 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty-state-box" },
            id: "empty-folder-items",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty-icon" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty-title" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "empty-sub" },
        });
        const __VLS_27 = {}.RouterLink;
        /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
        // @ts-ignore
        const __VLS_28 = __VLS_asFunctionalComponent(__VLS_27, new __VLS_27({
            to: "/",
            ...{ class: "action-btn-primary" },
        }));
        const __VLS_29 = __VLS_28({
            to: "/",
            ...{ class: "action-btn-primary" },
        }, ...__VLS_functionalComponentArgsRest(__VLS_28));
        __VLS_30.slots.default;
        var __VLS_30;
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "favorites-drama-grid" },
            id: "favorites-items-grid",
        });
        for (const [item] of __VLS_getVForSourceType((__VLS_ctx.folderItems))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                key: (item.id),
                ...{ class: "fav-drama-card" },
                id: ('fav-item-' + item.video_id),
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "fav-cover-wrap" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
                src: (item.video?.cover_url || __VLS_ctx.defaultCover),
                ...{ class: "fav-cover-img" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "fav-episodes-badge" },
            });
            (item.video?.total_episodes || 1);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "fav-category-badge" },
            });
            (item.video?.category || '短剧');
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "fav-card-body" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
                ...{ class: "fav-drama-title" },
            });
            (item.video?.title);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
                ...{ class: "fav-drama-desc" },
            });
            (item.video?.summary || '精选优质短剧');
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "fav-card-meta-line" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "fav-author" },
            });
            (item.video?.author || '官方精选');
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "fav-card-actions" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!!(__VLS_ctx.activeTab === 'history'))
                            return;
                        if (!!(__VLS_ctx.activeTab === 'likes'))
                            return;
                        if (!(__VLS_ctx.activeTab === 'favorites'))
                            return;
                        if (!!(__VLS_ctx.folderItemsLoading))
                            return;
                        if (!!(__VLS_ctx.folderItems.length === 0))
                            return;
                        __VLS_ctx.handleRemoveFromFolder(item.video_id);
                    } },
                ...{ class: "btn-remove-fav" },
                id: "btn-remove-favorite",
                title: "从当前收藏夹移出",
            });
            const __VLS_31 = {}.RouterLink;
            /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
            // @ts-ignore
            const __VLS_32 = __VLS_asFunctionalComponent(__VLS_31, new __VLS_31({
                to: ('/video/' + item.video_id),
                ...{ class: "btn-play-direct" },
                id: "btn-direct-play",
                title: "立即打开播放器播放",
            }));
            const __VLS_33 = __VLS_32({
                to: ('/video/' + item.video_id),
                ...{ class: "btn-play-direct" },
                id: "btn-direct-play",
                title: "立即打开播放器播放",
            }, ...__VLS_functionalComponentArgsRest(__VLS_32));
            __VLS_34.slots.default;
            var __VLS_34;
        }
    }
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "tab-pane" },
        id: "pane-profile",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "profile-edit-box" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "edit-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.form, __VLS_intrinsicElements.form)({
        ...{ onSubmit: (__VLS_ctx.saveProfile) },
        ...{ class: "profile-form" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        type: "text",
        ...{ class: "form-input readonly" },
        value: (__VLS_ctx.profile?.username),
        readonly: true,
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        value: (__VLS_ctx.editForm.nickname),
        type: "text",
        ...{ class: "form-input" },
        id: "input-edit-nickname",
        placeholder: "请输入您的昵称",
        required: true,
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.textarea, __VLS_intrinsicElements.textarea)({
        value: (__VLS_ctx.editForm.bio),
        ...{ class: "form-textarea" },
        id: "input-edit-bio",
        rows: "3",
        placeholder: "介绍一下自己，或者分享喜欢的短剧类型...",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "avatar-presets-row" },
    });
    for (const [seed] of __VLS_getVForSourceType((__VLS_ctx.avatarSeeds))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
            ...{ onClick: (...[$event]) => {
                    if (!!(__VLS_ctx.activeTab === 'history'))
                        return;
                    if (!!(__VLS_ctx.activeTab === 'likes'))
                        return;
                    if (!!(__VLS_ctx.activeTab === 'favorites'))
                        return;
                    __VLS_ctx.editForm.avatar_url = 'https://api.dicebear.com/7.x/bottts/svg?seed=' + seed;
                } },
            key: (seed),
            src: ('https://api.dicebear.com/7.x/bottts/svg?seed=' + seed),
            ...{ class: "avatar-preset-item" },
            ...{ class: ({ selected: __VLS_ctx.editForm.avatar_url.includes(seed) }) },
        });
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "edit-actions-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        type: "submit",
        ...{ class: "auth-primary-btn" },
        id: "btn-save-profile",
        disabled: (__VLS_ctx.isSaving),
    });
    (__VLS_ctx.isSaving ? '保存中...' : '保存资料修改');
    if (__VLS_ctx.saveNotice) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "save-notice" },
        });
        (__VLS_ctx.saveNotice);
    }
}
const __VLS_35 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_36 = __VLS_asFunctionalComponent(__VLS_35, new __VLS_35({
    name: "fade",
}));
const __VLS_37 = __VLS_36({
    name: "fade",
}, ...__VLS_functionalComponentArgsRest(__VLS_36));
__VLS_38.slots.default;
if (__VLS_ctx.showApplyModal) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-overlay" },
        id: "creator-apply-modal",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showApplyModal))
                    return;
                __VLS_ctx.showApplyModal = false;
            } },
        ...{ class: "modal-close-btn" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-body" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "modal-desc" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        value: (__VLS_ctx.applyForm.creator_name),
        type: "text",
        ...{ class: "form-input" },
        id: "input-apply-creator-name",
        placeholder: "例如：星芒微影工作室",
        required: true,
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.textarea, __VLS_intrinsicElements.textarea)({
        value: (__VLS_ctx.applyForm.bio),
        ...{ class: "form-textarea" },
        id: "input-apply-creator-bio",
        rows: "2",
        placeholder: "例如：专注逆袭爽剧与年代励志题材创作",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-footer" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showApplyModal))
                    return;
                __VLS_ctx.showApplyModal = false;
            } },
        ...{ class: "btn-cancel" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.submitCreatorApplication) },
        ...{ class: "btn-confirm" },
        id: "btn-confirm-apply-creator",
        disabled: (__VLS_ctx.isApplying),
    });
    (__VLS_ctx.isApplying ? '正在提交...' : '提交创作者申请');
}
var __VLS_38;
const __VLS_39 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_40 = __VLS_asFunctionalComponent(__VLS_39, new __VLS_39({
    name: "modal-fade",
}));
const __VLS_41 = __VLS_40({
    name: "modal-fade",
}, ...__VLS_functionalComponentArgsRest(__VLS_40));
__VLS_42.slots.default;
if (__VLS_ctx.showReviewerModal) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showReviewerModal))
                    return;
                __VLS_ctx.showReviewerModal = false;
            } },
        ...{ class: "modal-overlay" },
        id: "modal-reviewer-overlay",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-content glass-panel" },
        id: "modal-reviewer-box",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showReviewerModal))
                    return;
                __VLS_ctx.showReviewerModal = false;
            } },
        ...{ class: "btn-close" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-body" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "modal-desc" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        value: (__VLS_ctx.reviewerForm.reviewer_name),
        type: "text",
        ...{ class: "form-input" },
        id: "input-apply-reviewer-name",
        placeholder: "例如：影视合规专员",
        required: true,
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.textarea, __VLS_intrinsicElements.textarea)({
        value: (__VLS_ctx.reviewerForm.bio),
        ...{ class: "form-textarea" },
        id: "input-apply-reviewer-bio",
        rows: "2",
        placeholder: "例如：具备2年短视频内容风控与版权审核经验",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-footer" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showReviewerModal))
                    return;
                __VLS_ctx.showReviewerModal = false;
            } },
        ...{ class: "btn-cancel" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.submitReviewerApplication) },
        ...{ class: "btn-confirm" },
        id: "btn-confirm-apply-reviewer",
        disabled: (__VLS_ctx.isApplyingReviewer),
    });
    (__VLS_ctx.isApplyingReviewer ? '正在提交...' : '提交审核员入驻申请');
}
var __VLS_42;
const __VLS_43 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_44 = __VLS_asFunctionalComponent(__VLS_43, new __VLS_43({
    name: "modal-fade",
}));
const __VLS_45 = __VLS_44({
    name: "modal-fade",
}, ...__VLS_functionalComponentArgsRest(__VLS_44));
__VLS_46.slots.default;
if (__VLS_ctx.showFolderModal) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showFolderModal))
                    return;
                __VLS_ctx.showFolderModal = false;
            } },
        ...{ class: "modal-overlay" },
        id: "modal-create-folder",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-content glass-panel" },
        id: "modal-folder-box",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    (__VLS_ctx.editingFolderId ? '编辑收藏夹 📁' : '新建剧单收藏夹 ✨');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showFolderModal))
                    return;
                __VLS_ctx.showFolderModal = false;
            } },
        ...{ class: "btn-close" },
        id: "btn-close-folder-modal",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-body" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ style: {} },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        value: (__VLS_ctx.folderForm.name),
        type: "text",
        ...{ class: "form-input" },
        id: "input-folder-name",
        placeholder: "例如：高能反转爽剧合集",
        maxlength: "50",
        required: true,
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.textarea, __VLS_intrinsicElements.textarea)({
        value: (__VLS_ctx.folderForm.description),
        ...{ class: "form-textarea" },
        id: "input-folder-desc",
        rows: "2",
        placeholder: "简要描述此收藏夹收录的短剧主题...",
        maxlength: "200",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group-switch" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "switch-container" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        type: "checkbox",
        id: "checkbox-create-public",
    });
    (__VLS_ctx.folderForm.is_public);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "switch-slider" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "switch-labels" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "switch-title" },
    });
    (__VLS_ctx.folderForm.is_public ? '公开收藏夹' : '私密收藏夹');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "switch-desc" },
    });
    (__VLS_ctx.folderForm.is_public ? '所有人可在您的主页探索此收藏夹' : '仅自己登录可见');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-footer" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showFolderModal))
                    return;
                __VLS_ctx.showFolderModal = false;
            } },
        ...{ class: "btn-cancel" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.submitFolderForm) },
        ...{ class: "btn-confirm" },
        id: "btn-submit-create-folder",
        disabled: (!__VLS_ctx.folderForm.name.trim() || __VLS_ctx.isSubmittingFolder),
    });
    (__VLS_ctx.isSubmittingFolder ? '正在处理...' : (__VLS_ctx.editingFolderId ? '保存修改' : '立即创建'));
}
var __VLS_46;
/** @type {__VLS_StyleScopedClasses['user-space-page']} */ ;
/** @type {__VLS_StyleScopedClasses['space-ambient-glow']} */ ;
/** @type {__VLS_StyleScopedClasses['glow-top']} */ ;
/** @type {__VLS_StyleScopedClasses['space-ambient-glow']} */ ;
/** @type {__VLS_StyleScopedClasses['glow-bottom']} */ ;
/** @type {__VLS_StyleScopedClasses['space-container']} */ ;
/** @type {__VLS_StyleScopedClasses['space-hero-card']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-avatar-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-avatar']} */ ;
/** @type {__VLS_StyleScopedClasses['role-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-info']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-name-row']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-nickname']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-username']} */ ;
/** @type {__VLS_StyleScopedClasses['status-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['status-active']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-bio']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-stats-row']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-val']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-lbl']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-sep']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-val']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-lbl']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-sep']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-val']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-lbl']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-sep']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-val']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-lbl']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['action-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['economy-bento-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['economy-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['card-header-row']} */ ;
/** @type {__VLS_StyleScopedClasses['header-icon-title']} */ ;
/** @type {__VLS_StyleScopedClasses['card-emoji']} */ ;
/** @type {__VLS_StyleScopedClasses['card-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['card-subheading']} */ ;
/** @type {__VLS_StyleScopedClasses['wallet-badge-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['balance-num']} */ ;
/** @type {__VLS_StyleScopedClasses['balance-unit']} */ ;
/** @type {__VLS_StyleScopedClasses['wallet-stats-strip']} */ ;
/** @type {__VLS_StyleScopedClasses['wallet-stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['wstat-label']} */ ;
/** @type {__VLS_StyleScopedClasses['wstat-value']} */ ;
/** @type {__VLS_StyleScopedClasses['wallet-stat-sep']} */ ;
/** @type {__VLS_StyleScopedClasses['wallet-stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['wstat-label']} */ ;
/** @type {__VLS_StyleScopedClasses['wstat-value']} */ ;
/** @type {__VLS_StyleScopedClasses['wallet-stat-sep']} */ ;
/** @type {__VLS_StyleScopedClasses['wallet-stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['wstat-label']} */ ;
/** @type {__VLS_StyleScopedClasses['wstat-value']} */ ;
/** @type {__VLS_StyleScopedClasses['economy-actions-row']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-bento-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-signin']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-bento-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-ad']} */ ;
/** @type {__VLS_StyleScopedClasses['economy-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['card-header-row']} */ ;
/** @type {__VLS_StyleScopedClasses['header-icon-title']} */ ;
/** @type {__VLS_StyleScopedClasses['card-emoji']} */ ;
/** @type {__VLS_StyleScopedClasses['card-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['card-subheading']} */ ;
/** @type {__VLS_StyleScopedClasses['vip-status-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['vip-expiry-box']} */ ;
/** @type {__VLS_StyleScopedClasses['vip-expiry-label']} */ ;
/** @type {__VLS_StyleScopedClasses['vip-expiry-val']} */ ;
/** @type {__VLS_StyleScopedClasses['vip-tiers-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['vip-tier-card']} */ ;
/** @type {__VLS_StyleScopedClasses['tier-info']} */ ;
/** @type {__VLS_StyleScopedClasses['tier-name']} */ ;
/** @type {__VLS_StyleScopedClasses['tier-cost']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-bento-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['mini']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-exchange']} */ ;
/** @type {__VLS_StyleScopedClasses['vip-tier-card']} */ ;
/** @type {__VLS_StyleScopedClasses['tier-info']} */ ;
/** @type {__VLS_StyleScopedClasses['tier-name']} */ ;
/** @type {__VLS_StyleScopedClasses['tier-cost']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-bento-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['mini']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-exchange']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-qualification-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-content']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-text']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-action-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-enter-creator']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-pending']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-apply-creator']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-content']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-text']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-action-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-enter-reviewer']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-pending']} */ ;
/** @type {__VLS_StyleScopedClasses['qual-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-apply-reviewer']} */ ;
/** @type {__VLS_StyleScopedClasses['space-tabs-section']} */ ;
/** @type {__VLS_StyleScopedClasses['space-tab-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-pane']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-state-box']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-title']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['action-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['history-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['history-card']} */ ;
/** @type {__VLS_StyleScopedClasses['history-cover-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['history-cover']} */ ;
/** @type {__VLS_StyleScopedClasses['progress-bar-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['progress-bar-fill']} */ ;
/** @type {__VLS_StyleScopedClasses['ep-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['history-details']} */ ;
/** @type {__VLS_StyleScopedClasses['history-drama-title']} */ ;
/** @type {__VLS_StyleScopedClasses['history-ep-title']} */ ;
/** @type {__VLS_StyleScopedClasses['history-progress-text']} */ ;
/** @type {__VLS_StyleScopedClasses['history-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['history-time']} */ ;
/** @type {__VLS_StyleScopedClasses['continue-play-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-pane']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-state-box']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-title']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['action-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['likes-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['like-card']} */ ;
/** @type {__VLS_StyleScopedClasses['like-cover']} */ ;
/** @type {__VLS_StyleScopedClasses['like-info']} */ ;
/** @type {__VLS_StyleScopedClasses['like-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['like-time']} */ ;
/** @type {__VLS_StyleScopedClasses['play-link']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-pane']} */ ;
/** @type {__VLS_StyleScopedClasses['favorites-toolbar']} */ ;
/** @type {__VLS_StyleScopedClasses['toolbar-left']} */ ;
/** @type {__VLS_StyleScopedClasses['pane-section-title']} */ ;
/** @type {__VLS_StyleScopedClasses['pane-section-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['toolbar-right']} */ ;
/** @type {__VLS_StyleScopedClasses['action-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['mini']} */ ;
/** @type {__VLS_StyleScopedClasses['folders-pill-nav']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-pill-name']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-pill-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['default']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-pill-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-pill-count']} */ ;
/** @type {__VLS_StyleScopedClasses['active-folder-header']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-meta-text']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-title-line']} */ ;
/** @type {__VLS_StyleScopedClasses['current-folder-title']} */ ;
/** @type {__VLS_StyleScopedClasses['tag-default-capsule']} */ ;
/** @type {__VLS_StyleScopedClasses['tag-privacy-capsule']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-updated-date']} */ ;
/** @type {__VLS_StyleScopedClasses['current-folder-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-header-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-folder-action']} */ ;
/** @type {__VLS_StyleScopedClasses['edit']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-folder-action']} */ ;
/** @type {__VLS_StyleScopedClasses['delete']} */ ;
/** @type {__VLS_StyleScopedClasses['loading-state-box']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-state-box']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-title']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['action-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['favorites-drama-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['fav-drama-card']} */ ;
/** @type {__VLS_StyleScopedClasses['fav-cover-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['fav-cover-img']} */ ;
/** @type {__VLS_StyleScopedClasses['fav-episodes-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['fav-category-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['fav-card-body']} */ ;
/** @type {__VLS_StyleScopedClasses['fav-drama-title']} */ ;
/** @type {__VLS_StyleScopedClasses['fav-drama-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['fav-card-meta-line']} */ ;
/** @type {__VLS_StyleScopedClasses['fav-author']} */ ;
/** @type {__VLS_StyleScopedClasses['fav-card-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-remove-fav']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-play-direct']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-pane']} */ ;
/** @type {__VLS_StyleScopedClasses['profile-edit-box']} */ ;
/** @type {__VLS_StyleScopedClasses['edit-title']} */ ;
/** @type {__VLS_StyleScopedClasses['profile-form']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['readonly']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['form-textarea']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['avatar-presets-row']} */ ;
/** @type {__VLS_StyleScopedClasses['avatar-preset-item']} */ ;
/** @type {__VLS_StyleScopedClasses['edit-actions-row']} */ ;
/** @type {__VLS_StyleScopedClasses['auth-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['save-notice']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-header']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-close-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-body']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['form-textarea']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-cancel']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-confirm']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-content']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-header']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-close']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-body']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['form-textarea']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-cancel']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-confirm']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-content']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-header']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-close']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-body']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['form-textarea']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group-switch']} */ ;
/** @type {__VLS_StyleScopedClasses['switch-container']} */ ;
/** @type {__VLS_StyleScopedClasses['switch-slider']} */ ;
/** @type {__VLS_StyleScopedClasses['switch-labels']} */ ;
/** @type {__VLS_StyleScopedClasses['switch-title']} */ ;
/** @type {__VLS_StyleScopedClasses['switch-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-cancel']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-confirm']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            GlobalHeader: GlobalHeader,
            profile: profile,
            historyList: historyList,
            likesList: likesList,
            activeTab: activeTab,
            walletData: walletData,
            isSigningIn: isSigningIn,
            isWatchingAd: isWatchingAd,
            adCountdownText: adCountdownText,
            isExchangingVip: isExchangingVip,
            isUserVip: isUserVip,
            vipExpiryDisplay: vipExpiryDisplay,
            handleDailySignIn: handleDailySignIn,
            handleWatchAd: handleWatchAd,
            handleExchangeVip: handleExchangeVip,
            foldersList: foldersList,
            currentFolderId: currentFolderId,
            currentFolder: currentFolder,
            folderItems: folderItems,
            folderItemsLoading: folderItemsLoading,
            totalFavoritesCount: totalFavoritesCount,
            showFolderModal: showFolderModal,
            editingFolderId: editingFolderId,
            isSubmittingFolder: isSubmittingFolder,
            folderForm: folderForm,
            defaultAvatar: defaultAvatar,
            defaultCover: defaultCover,
            avatarSeeds: avatarSeeds,
            editForm: editForm,
            applyForm: applyForm,
            showApplyModal: showApplyModal,
            isApplying: isApplying,
            isSaving: isSaving,
            saveNotice: saveNotice,
            selectFolder: selectFolder,
            openCreateFolderModal: openCreateFolderModal,
            openEditFolderModal: openEditFolderModal,
            submitFolderForm: submitFolderForm,
            handleDeleteFolder: handleDeleteFolder,
            handleRemoveFromFolder: handleRemoveFromFolder,
            formatDate: formatDate,
            getRoleBadgeText: getRoleBadgeText,
            formatDuration: formatDuration,
            openApplyModal: openApplyModal,
            showReviewerModal: showReviewerModal,
            isApplyingReviewer: isApplyingReviewer,
            reviewerForm: reviewerForm,
            openReviewerModal: openReviewerModal,
            submitCreatorApplication: submitCreatorApplication,
            submitReviewerApplication: submitReviewerApplication,
            saveProfile: saveProfile,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=UserProfileView.vue.js.map