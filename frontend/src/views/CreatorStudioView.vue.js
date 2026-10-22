/// <reference types="../../node_modules/.vue-global-types/vue_3.5_0_0_0.d.ts" />
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import AdminHeader from '../components/AdminHeader.vue';
import { Refresh, Folder, Upload, Film, Top, VideoCamera, Check, Promotion, Loading, VideoPlay, DataAnalysis, TrendCharts, Star } from '@element-plus/icons-vue';
import { creatorApi } from '../api/creator';
import { authApi } from '../api/auth';
const router = useRouter();
const route = useRoute();
const user = ref(null);
const loadUser = async () => {
    try {
        const raw = localStorage.getItem('user');
        if (raw)
            user.value = JSON.parse(raw);
    }
    catch { }
    const token = localStorage.getItem('cinema_access_token') || localStorage.getItem('token');
    if (token) {
        try {
            const res = await authApi.getMe();
            if (res?.data) {
                user.value = res.data;
                localStorage.setItem('user', JSON.stringify(res.data));
            }
        }
        catch (e) {
            console.warn('Failed to refresh user:', e);
        }
    }
};
const handleUserChanged = (u) => {
    user.value = u;
    if (isCreator.value) {
        fetchPanTree();
        fetchMyDramas();
    }
};
const isCreator = computed(() => {
    if (!user.value)
        return false;
    return !!user.value.is_creator || user.value.role === 'CREATOR' || user.value.role === 'ADMIN';
});
// Application Form
const applyForm = ref({
    creator_name: '',
    bio: ''
});
const applySubmitting = ref(false);
const applyMessage = ref('');
const submitApply = async () => {
    if (!applyForm.value.creator_name.trim()) {
        applyForm.value.creator_name = user.value?.nickname || user.value?.username || '影视创作者';
    }
    applySubmitting.value = true;
    applyMessage.value = '';
    try {
        const res = await creatorApi.apply(applyForm.value);
        if (res.code === 200) {
            applyMessage.value = '恭喜！您已成功开通创作者权限！';
            // Update stored user
            if (res.data) {
                user.value = { ...user.value, ...res.data, is_creator: true, role: 'CREATOR' };
                localStorage.setItem('user', JSON.stringify(user.value));
                loadUser();
            }
            setTimeout(() => {
                activeTab.value = 'disk';
                fetchPanTree();
            }, 800);
        }
        else {
            applyMessage.value = res.message || '申请失败，请稍后重试';
        }
    }
    catch (err) {
        applyMessage.value = err.response?.data?.detail || err.message || '申请失败';
    }
    finally {
        applySubmitting.value = false;
    }
};
// Workspace state
const activeTab = ref('disk');
// BI Analytics State
const totalViews = computed(() => myDramas.value.reduce((acc, d) => acc + (d.play_count || 0), 0));
const totalLikes = computed(() => myDramas.value.reduce((acc, d) => acc + (d.like_count || 0), 0));
const totalCoins = computed(() => myDramas.value.reduce((acc, d) => acc + (d.coin_count || 0), 0));
const avgViralScore = computed(() => {
    if (!myDramas.value.length)
        return 88;
    const sum = myDramas.value.reduce((acc, d) => acc + (d.viral_score || 88), 0);
    return Math.round(sum / myDramas.value.length);
});
const handleSelectTab = (tab) => {
    if (['disk', 'upload', 'dramas', 'bi'].includes(tab)) {
        activeTab.value = tab;
    }
};
// Cloud Disk Tree
const currentPath = ref('/kuake/红果项目资源目录');
const parentPath = ref('/kuake');
const panFolders = ref([]);
const panFiles = ref([]);
const panLoading = ref(false);
const fetchPanTree = async (path) => {
    panLoading.value = true;
    const target = path || currentPath.value;
    try {
        const res = await creatorApi.getPanTree(target);
        if (res.code === 200 && res.data) {
            currentPath.value = res.data.current_path;
            parentPath.value = res.data.parent_path;
            panFolders.value = res.data.folders || [];
            panFiles.value = res.data.files || [];
            uploadTargetFolder.value = res.data.current_path;
        }
    }
    catch (err) {
        console.error('Failed to list pan files:', err);
    }
    finally {
        panLoading.value = false;
    }
};
const enterFolder = (folderPath) => {
    fetchPanTree(folderPath);
};
const navigateUp = () => {
    if (parentPath.value) {
        fetchPanTree(parentPath.value);
    }
};
// Mkdir Modal
const showNewFolderModal = ref(false);
const newFolderName = ref('');
const mkdirLoading = ref(false);
const confirmMkdir = async () => {
    if (!newFolderName.value.trim())
        return;
    mkdirLoading.value = true;
    try {
        const res = await creatorApi.mkdir(newFolderName.value.trim(), currentPath.value);
        if (res.code === 200) {
            showNewFolderModal.value = false;
            newFolderName.value = '';
            fetchPanTree(currentPath.value);
        }
    }
    catch (err) {
        alert(err.response?.data?.detail || '创建文件夹失败');
    }
    finally {
        mkdirLoading.value = false;
    }
};
// Upload Form
const uploadTargetFolder = ref('/kuake/红果项目资源目录');
const uploadDramaTitle = ref('');
const uploadEpisodeTitle = ref('');
const uploadEpisodeNum = ref(1);
const uploadCategory = ref('短剧精选');
const selectedFile = ref(null);
const isDragging = ref(false);
const fileInputRef = ref(null);
const isUploading = ref(false);
const uploadProgress = ref(0);
const uploadStatusText = ref('');
const uploadFeedback = ref('');
const uploadFeedbackType = ref('success');
const triggerFileInput = () => {
    fileInputRef.value?.click();
};
const handleFileSelect = (e) => {
    const target = e.target;
    if (target.files && target.files.length > 0) {
        selectedFile.value = target.files[0];
        if (!uploadDramaTitle.value) {
            uploadDramaTitle.value = selectedFile.value.name.replace(/\.[^/.]+$/, '');
        }
    }
};
const handleFileDrop = (e) => {
    isDragging.value = false;
    if (e.dataTransfer && e.dataTransfer.files.length > 0) {
        selectedFile.value = e.dataTransfer.files[0];
        if (!uploadDramaTitle.value) {
            uploadDramaTitle.value = selectedFile.value.name.replace(/\.[^/.]+$/, '');
        }
    }
};
const startUpload = async () => {
    if (!selectedFile.value)
        return;
    isUploading.value = true;
    uploadProgress.value = 15;
    uploadStatusText.value = '正在上传分片数据...';
    uploadFeedback.value = '';
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    formData.append('target_folder', uploadTargetFolder.value);
    formData.append('drama_title', uploadDramaTitle.value);
    formData.append('episode_title', uploadEpisodeTitle.value);
    formData.append('episode_num', String(uploadEpisodeNum.value));
    formData.append('category', uploadCategory.value);
    try {
        uploadProgress.value = 55;
        uploadStatusText.value = '提取 FFmpeg 首帧海报与转码元数据...';
        const res = await creatorApi.uploadVideo(formData);
        uploadProgress.value = 100;
        uploadStatusText.value = '已存入夸克网盘并同步上架！';
        uploadFeedback.value = res.message || '上传成功！';
        uploadFeedbackType.value = 'success';
        selectedFile.value = null;
        fetchMyDramas();
    }
    catch (err) {
        uploadFeedback.value = err.response?.data?.detail || err.message || '上传处理失败';
        uploadFeedbackType.value = 'error';
        uploadProgress.value = 0;
    }
    finally {
        isUploading.value = false;
    }
};
// My Dramas
const myDramas = ref([]);
const isSyncingDramas = ref(false);
const handleSyncQuarkDramas = async () => {
    isSyncingDramas.value = true;
    try {
        const res = await creatorApi.syncDramas();
        alert(res.message || '夸克网盘短剧同步成功！');
        await fetchPanTree();
        await fetchMyDramas();
    }
    catch (err) {
        alert('同步失败: ' + (err.response?.data?.detail || err.message || '网络错误'));
    }
    finally {
        isSyncingDramas.value = false;
    }
};
const fetchMyDramas = async () => {
    try {
        const res = await creatorApi.getMyDramas();
        if (res.code === 200 && res.data) {
            myDramas.value = res.data;
        }
    }
    catch (err) {
        console.error('Failed to load dramas:', err);
    }
};
const goToPlay = (dramaId) => {
    router.push(`/video/${dramaId}`);
};
// Edit Drama State & Handlers
const showEditDramaModal = ref(false);
const editingDrama = ref(null);
const dramaForm = ref({
    title: '',
    category: '短剧精选',
    description: '',
    cover_url: ''
});
const openEditDramaModal = (drama) => {
    editingDrama.value = drama;
    dramaForm.value = {
        title: drama.title,
        category: drama.category || '短剧精选',
        description: drama.description || '',
        cover_url: drama.cover_url || ''
    };
    showEditDramaModal.value = true;
};
const confirmUpdateDrama = async () => {
    if (!editingDrama.value || !dramaForm.value.title.trim())
        return;
    try {
        const res = await creatorApi.updateDrama(editingDrama.value.id, dramaForm.value);
        if (res.code === 200 && res.data) {
            editingDrama.value.title = res.data.title;
            editingDrama.value.category = res.data.category;
            editingDrama.value.description = res.data.description;
            editingDrama.value.cover_url = res.data.cover_url;
            showEditDramaModal.value = false;
            alert(`短剧《${res.data.title}》信息已成功更新！`);
        }
    }
    catch (err) {
        alert('保存失败: ' + (err.response?.data?.detail || err.message));
    }
};
const toggleDramaStatus = async (drama) => {
    const target = (drama.status === 'READY' || drama.status === 'PUBLISHED') ? 'HIDDEN' : 'READY';
    try {
        const res = await creatorApi.updateDrama(drama.id, { status: target });
        if (res.code === 200) {
            drama.status = target;
            alert(`短剧《${drama.title}》已${target === 'READY' ? '重新上架' : '屏蔽下线'}`);
        }
    }
    catch (err) {
        alert('状态更新失败: ' + (err.response?.data?.detail || err.message));
    }
};
const handleDeleteDrama = async (drama) => {
    if (!confirm(`确定要从平台删除短剧《${drama.title}》及其全部分集记录吗？`))
        return;
    try {
        await creatorApi.deleteDrama(drama.id);
        myDramas.value = myDramas.value.filter(d => d.id !== drama.id);
        alert(`短剧《${drama.title}》已成功删除！`);
    }
    catch (err) {
        alert('删除失败: ' + (err.response?.data?.detail || err.message));
    }
};
// Episodes Drawer State & Handlers
const showEpisodesDrawer = ref(false);
const selectedDrama = ref(null);
const episodesList = ref([]);
const episodesLoading = ref(false);
const manageEpisodes = async (drama) => {
    selectedDrama.value = drama;
    showEpisodesDrawer.value = true;
    episodesLoading.value = true;
    try {
        const res = await creatorApi.getDramaEpisodes(drama.id);
        if (res.code === 200 && res.data) {
            episodesList.value = res.data.episodes || [];
        }
    }
    catch (err) {
        alert('加载分集失败: ' + (err.response?.data?.detail || err.message));
    }
    finally {
        episodesLoading.value = false;
    }
};
const saveEpisodeChanges = async (ep) => {
    try {
        const res = await creatorApi.updateEpisode(ep.id, {
            title: ep.title,
            episode_num: ep.episode_num,
            climax_seconds: ep.climax_seconds ?? undefined
        });
        if (res.code === 200) {
            alert(`第 ${ep.episode_num} 集信息已成功保存！`);
        }
    }
    catch (err) {
        alert('保存分集失败: ' + (err.response?.data?.detail || err.message));
    }
};
// Utilities
const formatBytes = (bytes) => {
    if (!bytes)
        return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};
const formatDate = (isoStr) => {
    if (!isoStr)
        return '-';
    try {
        return new Date(isoStr).toLocaleDateString();
    }
    catch {
        return isoStr;
    }
};
const formatNumber = (num) => {
    if (!num)
        return '0';
    if (num >= 10000)
        return (num / 10000).toFixed(1) + 'w';
    if (num >= 1000)
        return (num / 1000).toFixed(1) + 'k';
    return String(num);
};
onMounted(async () => {
    await loadUser();
    if (route.query.tab && ['disk', 'upload', 'dramas', 'bi'].includes(String(route.query.tab))) {
        activeTab.value = String(route.query.tab);
    }
    if (isCreator.value) {
        fetchPanTree();
        fetchMyDramas();
    }
});
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['primary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['primary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['secondary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['submit-apply-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['pan-item-card']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-row']} */ ;
/** @type {__VLS_StyleScopedClasses['file-drop-box']} */ ;
/** @type {__VLS_StyleScopedClasses['file-drop-box']} */ ;
/** @type {__VLS_StyleScopedClasses['dropzone-idle']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-feedback-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-feedback-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-danger-text']} */ ;
/** @type {__VLS_StyleScopedClasses['close-x-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-table']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-table']} */ ;
/** @type {__VLS_StyleScopedClasses['table-inline-input']} */ ;
/** @type {__VLS_StyleScopedClasses['table-inline-input']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-value-num']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-bi-table']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-bi-table']} */ ;
/** @type {__VLS_StyleScopedClasses['status-indicator-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['status-indicator-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['insight-head']} */ ;
/** @type {__VLS_StyleScopedClasses['insight-card']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-studio-container']} */ ;
/** @type {__VLS_StyleScopedClasses['studio-page-title']} */ ;
/** @type {__VLS_StyleScopedClasses['bi-card-title']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-value-num']} */ ;
/** @type {__VLS_StyleScopedClasses['insight-head']} */ ;
/** @type {__VLS_StyleScopedClasses['panel-section-title']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-card-title']} */ ;
/** @type {__VLS_StyleScopedClasses['studio-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-label']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-hint']} */ ;
/** @type {__VLS_StyleScopedClasses['insight-card']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-card-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['time-label']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-bi-table-card']} */ ;
/** @type {__VLS_StyleScopedClasses['insight-card']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-content-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['my-drama-card']} */ ;
/** @type {__VLS_StyleScopedClasses['pan-item-card']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-builder-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-bi-table']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-table']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-bi-table']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-table']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['table-inline-input']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['table-inline-input']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "creator-studio-container" },
    id: "creator-studio-page",
});
/** @type {[typeof AdminHeader, ]} */ ;
// @ts-ignore
const __VLS_0 = __VLS_asFunctionalComponent(AdminHeader, new AdminHeader({
    ...{ 'onSelectTab': {} },
    ...{ 'onUserChanged': {} },
    mode: "creator",
    activeTab: (__VLS_ctx.activeTab),
}));
const __VLS_1 = __VLS_0({
    ...{ 'onSelectTab': {} },
    ...{ 'onUserChanged': {} },
    mode: "creator",
    activeTab: (__VLS_ctx.activeTab),
}, ...__VLS_functionalComponentArgsRest(__VLS_0));
let __VLS_3;
let __VLS_4;
let __VLS_5;
const __VLS_6 = {
    onSelectTab: (__VLS_ctx.handleSelectTab)
};
const __VLS_7 = {
    onUserChanged: (__VLS_ctx.handleUserChanged)
};
var __VLS_2;
__VLS_asFunctionalElement(__VLS_intrinsicElements.main, __VLS_intrinsicElements.main)({
    ...{ class: "studio-main-body" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "studio-ambient-bg" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "studio-orb orb-a" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "studio-orb orb-b" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "studio-top-bar" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "studio-badge-pill" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({
    ...{ class: "studio-page-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "studio-subtext" },
});
if (__VLS_ctx.isCreator) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "studio-top-actions" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.handleSyncQuarkDramas) },
        ...{ class: "secondary-pill-btn" },
        id: "btn-sync-quark-dramas",
        disabled: (__VLS_ctx.isSyncingDramas),
    });
    if (__VLS_ctx.isSyncingDramas) {
        const __VLS_8 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({
            ...{ class: "is-loading" },
        }));
        const __VLS_10 = __VLS_9({
            ...{ class: "is-loading" },
        }, ...__VLS_functionalComponentArgsRest(__VLS_9));
        __VLS_11.slots.default;
        const __VLS_12 = {}.Loading;
        /** @type {[typeof __VLS_components.Loading, ]} */ ;
        // @ts-ignore
        const __VLS_13 = __VLS_asFunctionalComponent(__VLS_12, new __VLS_12({}));
        const __VLS_14 = __VLS_13({}, ...__VLS_functionalComponentArgsRest(__VLS_13));
        var __VLS_11;
    }
    else {
        const __VLS_16 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_17 = __VLS_asFunctionalComponent(__VLS_16, new __VLS_16({}));
        const __VLS_18 = __VLS_17({}, ...__VLS_functionalComponentArgsRest(__VLS_17));
        __VLS_19.slots.default;
        const __VLS_20 = {}.Refresh;
        /** @type {[typeof __VLS_components.Refresh, ]} */ ;
        // @ts-ignore
        const __VLS_21 = __VLS_asFunctionalComponent(__VLS_20, new __VLS_20({}));
        const __VLS_22 = __VLS_21({}, ...__VLS_functionalComponentArgsRest(__VLS_21));
        var __VLS_19;
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.isSyncingDramas ? '正在扫描网盘...' : '一键映射网盘短剧');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.isCreator))
                    return;
                __VLS_ctx.showNewFolderModal = true;
            } },
        ...{ class: "primary-pill-btn" },
        id: "btn-open-mkdir-modal",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
if (!__VLS_ctx.isCreator) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "apply-creator-card" },
        id: "creator-apply-box",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "apply-header-wrap" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "apply-icon-orb" },
    });
    const __VLS_24 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_25 = __VLS_asFunctionalComponent(__VLS_24, new __VLS_24({
        size: (24),
    }));
    const __VLS_26 = __VLS_25({
        size: (24),
    }, ...__VLS_functionalComponentArgsRest(__VLS_25));
    __VLS_27.slots.default;
    const __VLS_28 = {}.VideoCamera;
    /** @type {[typeof __VLS_components.VideoCamera, ]} */ ;
    // @ts-ignore
    const __VLS_29 = __VLS_asFunctionalComponent(__VLS_28, new __VLS_28({}));
    const __VLS_30 = __VLS_29({}, ...__VLS_functionalComponentArgsRest(__VLS_29));
    var __VLS_27;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({
        ...{ class: "apply-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "apply-desc" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "apply-form-body" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-item-field" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        value: (__VLS_ctx.applyForm.creator_name),
        type: "text",
        ...{ class: "apple-text-input" },
        placeholder: "例如：短剧大爆炸、影视剪辑社",
        id: "input-creator-name",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-item-field" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        value: (__VLS_ctx.applyForm.bio),
        type: "text",
        ...{ class: "apple-text-input" },
        placeholder: "例如：专注都市爽剧、热血战神与甜宠短剧制作",
        id: "input-creator-bio",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "apply-action-bar" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.submitApply) },
        ...{ class: "submit-apply-btn" },
        disabled: (__VLS_ctx.applySubmitting),
        id: "btn-submit-creator-apply",
    });
    (__VLS_ctx.applySubmitting ? '申请提交中...' : '一键开通创作者权限');
    if (__VLS_ctx.applyMessage) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "apply-feedback-msg" },
        });
        (__VLS_ctx.applyMessage);
    }
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "creator-workspace-area" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "studio-tabs-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!!(!__VLS_ctx.isCreator))
                    return;
                __VLS_ctx.activeTab = 'disk';
            } },
        ...{ class: "tab-btn" },
        ...{ class: ({ active: __VLS_ctx.activeTab === 'disk' }) },
        id: "tab-pan-tree",
    });
    const __VLS_32 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_33 = __VLS_asFunctionalComponent(__VLS_32, new __VLS_32({}));
    const __VLS_34 = __VLS_33({}, ...__VLS_functionalComponentArgsRest(__VLS_33));
    __VLS_35.slots.default;
    const __VLS_36 = {}.Folder;
    /** @type {[typeof __VLS_components.Folder, ]} */ ;
    // @ts-ignore
    const __VLS_37 = __VLS_asFunctionalComponent(__VLS_36, new __VLS_36({}));
    const __VLS_38 = __VLS_37({}, ...__VLS_functionalComponentArgsRest(__VLS_37));
    var __VLS_35;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!!(!__VLS_ctx.isCreator))
                    return;
                __VLS_ctx.activeTab = 'upload';
            } },
        ...{ class: "tab-btn" },
        ...{ class: ({ active: __VLS_ctx.activeTab === 'upload' }) },
        id: "tab-video-upload",
    });
    const __VLS_40 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_41 = __VLS_asFunctionalComponent(__VLS_40, new __VLS_40({}));
    const __VLS_42 = __VLS_41({}, ...__VLS_functionalComponentArgsRest(__VLS_41));
    __VLS_43.slots.default;
    const __VLS_44 = {}.Upload;
    /** @type {[typeof __VLS_components.Upload, ]} */ ;
    // @ts-ignore
    const __VLS_45 = __VLS_asFunctionalComponent(__VLS_44, new __VLS_44({}));
    const __VLS_46 = __VLS_45({}, ...__VLS_functionalComponentArgsRest(__VLS_45));
    var __VLS_43;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!!(!__VLS_ctx.isCreator))
                    return;
                __VLS_ctx.activeTab = 'dramas';
            } },
        ...{ class: "tab-btn" },
        ...{ class: ({ active: __VLS_ctx.activeTab === 'dramas' }) },
        id: "tab-my-dramas",
    });
    const __VLS_48 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_49 = __VLS_asFunctionalComponent(__VLS_48, new __VLS_48({}));
    const __VLS_50 = __VLS_49({}, ...__VLS_functionalComponentArgsRest(__VLS_49));
    __VLS_51.slots.default;
    const __VLS_52 = {}.Film;
    /** @type {[typeof __VLS_components.Film, ]} */ ;
    // @ts-ignore
    const __VLS_53 = __VLS_asFunctionalComponent(__VLS_52, new __VLS_52({}));
    const __VLS_54 = __VLS_53({}, ...__VLS_functionalComponentArgsRest(__VLS_53));
    var __VLS_51;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.myDramas.length);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!!(!__VLS_ctx.isCreator))
                    return;
                __VLS_ctx.activeTab = 'bi';
            } },
        ...{ class: "tab-btn" },
        ...{ class: ({ active: __VLS_ctx.activeTab === 'bi' }) },
        id: "tab-creator-bi",
    });
    const __VLS_56 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_57 = __VLS_asFunctionalComponent(__VLS_56, new __VLS_56({}));
    const __VLS_58 = __VLS_57({}, ...__VLS_functionalComponentArgsRest(__VLS_57));
    __VLS_59.slots.default;
    const __VLS_60 = {}.DataAnalysis;
    /** @type {[typeof __VLS_components.DataAnalysis, ]} */ ;
    // @ts-ignore
    const __VLS_61 = __VLS_asFunctionalComponent(__VLS_60, new __VLS_60({}));
    const __VLS_62 = __VLS_61({}, ...__VLS_functionalComponentArgsRest(__VLS_61));
    var __VLS_59;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    if (__VLS_ctx.activeTab === 'disk') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "tab-content-panel" },
            id: "panel-disk-tree",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "pan-breadcrumb-bar" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "breadcrumb-left" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "path-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "current-path-text" },
            id: "current-cloud-path",
        });
        (__VLS_ctx.currentPath);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "breadcrumb-right" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.navigateUp) },
            ...{ class: "secondary-pill-btn" },
            disabled: (__VLS_ctx.currentPath === '/kuake' || __VLS_ctx.currentPath === '/'),
            id: "btn-navigate-up",
        });
        const __VLS_64 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_65 = __VLS_asFunctionalComponent(__VLS_64, new __VLS_64({}));
        const __VLS_66 = __VLS_65({}, ...__VLS_functionalComponentArgsRest(__VLS_65));
        __VLS_67.slots.default;
        const __VLS_68 = {}.Top;
        /** @type {[typeof __VLS_components.Top, ]} */ ;
        // @ts-ignore
        const __VLS_69 = __VLS_asFunctionalComponent(__VLS_68, new __VLS_68({}));
        const __VLS_70 = __VLS_69({}, ...__VLS_functionalComponentArgsRest(__VLS_69));
        var __VLS_67;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!!(!__VLS_ctx.isCreator))
                        return;
                    if (!(__VLS_ctx.activeTab === 'disk'))
                        return;
                    __VLS_ctx.fetchPanTree(__VLS_ctx.currentPath);
                } },
            ...{ class: "secondary-pill-btn" },
            id: "btn-refresh-pan",
        });
        const __VLS_72 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_73 = __VLS_asFunctionalComponent(__VLS_72, new __VLS_72({}));
        const __VLS_74 = __VLS_73({}, ...__VLS_functionalComponentArgsRest(__VLS_73));
        __VLS_75.slots.default;
        const __VLS_76 = {}.Refresh;
        /** @type {[typeof __VLS_components.Refresh, ]} */ ;
        // @ts-ignore
        const __VLS_77 = __VLS_asFunctionalComponent(__VLS_76, new __VLS_76({}));
        const __VLS_78 = __VLS_77({}, ...__VLS_functionalComponentArgsRest(__VLS_77));
        var __VLS_75;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        if (__VLS_ctx.panLoading) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "pan-loading-box" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "spinner" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        }
        else {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "pan-items-grid" },
            });
            for (const [folder] of __VLS_getVForSourceType((__VLS_ctx.panFolders))) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ onClick: (...[$event]) => {
                            if (!!(!__VLS_ctx.isCreator))
                                return;
                            if (!(__VLS_ctx.activeTab === 'disk'))
                                return;
                            if (!!(__VLS_ctx.panLoading))
                                return;
                            __VLS_ctx.enterFolder(folder.path);
                        } },
                    key: (folder.path),
                    ...{ class: "pan-item-card folder-card" },
                    id: ('folder-' + folder.name),
                });
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "item-glyph-icon" },
                });
                const __VLS_80 = {}.ElIcon;
                /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
                // @ts-ignore
                const __VLS_81 = __VLS_asFunctionalComponent(__VLS_80, new __VLS_80({
                    size: (28),
                }));
                const __VLS_82 = __VLS_81({
                    size: (28),
                }, ...__VLS_functionalComponentArgsRest(__VLS_81));
                __VLS_83.slots.default;
                const __VLS_84 = {}.Folder;
                /** @type {[typeof __VLS_components.Folder, ]} */ ;
                // @ts-ignore
                const __VLS_85 = __VLS_asFunctionalComponent(__VLS_84, new __VLS_84({}));
                const __VLS_86 = __VLS_85({}, ...__VLS_functionalComponentArgsRest(__VLS_85));
                var __VLS_83;
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "item-meta-wrap" },
                });
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "item-main-title" },
                });
                (folder.name);
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "item-sub-meta" },
                });
            }
            for (const [file] of __VLS_getVForSourceType((__VLS_ctx.panFiles))) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    key: (file.path),
                    ...{ class: "pan-item-card file-card" },
                    id: ('file-' + file.name),
                });
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "item-glyph-icon" },
                });
                const __VLS_88 = {}.ElIcon;
                /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
                // @ts-ignore
                const __VLS_89 = __VLS_asFunctionalComponent(__VLS_88, new __VLS_88({
                    size: (28),
                }));
                const __VLS_90 = __VLS_89({
                    size: (28),
                }, ...__VLS_functionalComponentArgsRest(__VLS_89));
                __VLS_91.slots.default;
                const __VLS_92 = {}.Film;
                /** @type {[typeof __VLS_components.Film, ]} */ ;
                // @ts-ignore
                const __VLS_93 = __VLS_asFunctionalComponent(__VLS_92, new __VLS_92({}));
                const __VLS_94 = __VLS_93({}, ...__VLS_functionalComponentArgsRest(__VLS_93));
                var __VLS_91;
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "item-meta-wrap" },
                });
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "item-main-title" },
                });
                (file.name);
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "item-sub-meta" },
                });
                (__VLS_ctx.formatBytes(file.size));
                (__VLS_ctx.formatDate(file.modified));
            }
            if (__VLS_ctx.panFolders.length === 0 && __VLS_ctx.panFiles.length === 0) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "empty-pan-box" },
                });
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "empty-pan-icon" },
                });
                const __VLS_96 = {}.ElIcon;
                /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
                // @ts-ignore
                const __VLS_97 = __VLS_asFunctionalComponent(__VLS_96, new __VLS_96({
                    size: (48),
                }));
                const __VLS_98 = __VLS_97({
                    size: (48),
                }, ...__VLS_functionalComponentArgsRest(__VLS_97));
                __VLS_99.slots.default;
                const __VLS_100 = {}.Folder;
                /** @type {[typeof __VLS_components.Folder, ]} */ ;
                // @ts-ignore
                const __VLS_101 = __VLS_asFunctionalComponent(__VLS_100, new __VLS_100({}));
                const __VLS_102 = __VLS_101({}, ...__VLS_functionalComponentArgsRest(__VLS_101));
                var __VLS_99;
                __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
                __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
            }
        }
    }
    if (__VLS_ctx.activeTab === 'upload') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "tab-content-panel" },
            id: "panel-video-upload",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "upload-builder-grid" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "upload-form-side" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
            ...{ class: "panel-section-title" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "form-item-field" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "form-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            value: (__VLS_ctx.uploadTargetFolder),
            type: "text",
            ...{ class: "apple-text-input" },
            placeholder: "/kuake/红果项目资源目录",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "form-item-field" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "form-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            value: (__VLS_ctx.uploadDramaTitle),
            type: "text",
            ...{ class: "apple-text-input" },
            placeholder: "例如：战神归来：龙王令",
            id: "input-drama-title",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "form-item-row" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "form-item-field half" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "form-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            type: "number",
            min: "1",
            ...{ class: "apple-text-input" },
            id: "input-episode-num",
        });
        (__VLS_ctx.uploadEpisodeNum);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "form-item-field half" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "form-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
            value: (__VLS_ctx.uploadCategory),
            ...{ class: "apple-text-input" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "都市战神",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "悬疑逆袭",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "古装穿越",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "豪门甜宠",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "短剧精选",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "form-item-field" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "form-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            value: (__VLS_ctx.uploadEpisodeTitle),
            type: "text",
            ...{ class: "apple-text-input" },
            placeholder: "例如：第 1 集：龙王卸甲归来",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "upload-dropzone-side" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ onDragover: (...[$event]) => {
                    if (!!(!__VLS_ctx.isCreator))
                        return;
                    if (!(__VLS_ctx.activeTab === 'upload'))
                        return;
                    __VLS_ctx.isDragging = true;
                } },
            ...{ onDragleave: (...[$event]) => {
                    if (!!(!__VLS_ctx.isCreator))
                        return;
                    if (!(__VLS_ctx.activeTab === 'upload'))
                        return;
                    __VLS_ctx.isDragging = false;
                } },
            ...{ onDrop: (__VLS_ctx.handleFileDrop) },
            ...{ onClick: (__VLS_ctx.triggerFileInput) },
            ...{ class: "file-drop-box" },
            ...{ class: ({ dragging: __VLS_ctx.isDragging, 'has-file': !!__VLS_ctx.selectedFile }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            ...{ onChange: (__VLS_ctx.handleFileSelect) },
            ref: "fileInputRef",
            type: "file",
            accept: "video/mp4,video/x-matroska,video/quicktime",
            ...{ style: {} },
            id: "file-input-raw",
        });
        /** @type {typeof __VLS_ctx.fileInputRef} */ ;
        if (!__VLS_ctx.selectedFile) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "dropzone-idle" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "drop-icon" },
            });
            const __VLS_104 = {}.ElIcon;
            /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
            // @ts-ignore
            const __VLS_105 = __VLS_asFunctionalComponent(__VLS_104, new __VLS_104({
                size: (48),
            }));
            const __VLS_106 = __VLS_105({
                size: (48),
            }, ...__VLS_functionalComponentArgsRest(__VLS_105));
            __VLS_107.slots.default;
            const __VLS_108 = {}.VideoPlay;
            /** @type {[typeof __VLS_components.VideoPlay, ]} */ ;
            // @ts-ignore
            const __VLS_109 = __VLS_asFunctionalComponent(__VLS_108, new __VLS_108({}));
            const __VLS_110 = __VLS_109({}, ...__VLS_functionalComponentArgsRest(__VLS_109));
            var __VLS_107;
            __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
        }
        else {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "dropzone-file-selected" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "file-success-icon" },
            });
            const __VLS_112 = {}.ElIcon;
            /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
            // @ts-ignore
            const __VLS_113 = __VLS_asFunctionalComponent(__VLS_112, new __VLS_112({
                size: (28),
            }));
            const __VLS_114 = __VLS_113({
                size: (28),
            }, ...__VLS_functionalComponentArgsRest(__VLS_113));
            __VLS_115.slots.default;
            const __VLS_116 = {}.Check;
            /** @type {[typeof __VLS_components.Check, ]} */ ;
            // @ts-ignore
            const __VLS_117 = __VLS_asFunctionalComponent(__VLS_116, new __VLS_116({}));
            const __VLS_118 = __VLS_117({}, ...__VLS_functionalComponentArgsRest(__VLS_117));
            var __VLS_115;
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "selected-name" },
            });
            (__VLS_ctx.selectedFile.name);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "selected-size" },
            });
            (__VLS_ctx.formatBytes(__VLS_ctx.selectedFile.size));
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!!(!__VLS_ctx.isCreator))
                            return;
                        if (!(__VLS_ctx.activeTab === 'upload'))
                            return;
                        if (!!(!__VLS_ctx.selectedFile))
                            return;
                        __VLS_ctx.selectedFile = null;
                    } },
                ...{ class: "remove-file-btn" },
            });
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "upload-action-dock" },
        });
        if (__VLS_ctx.uploadProgress > 0) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "progress-track-wrap" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "progress-bar-fill" },
                ...{ style: ({ width: __VLS_ctx.uploadProgress + '%' }) },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "progress-label" },
            });
            (__VLS_ctx.uploadProgress);
            (__VLS_ctx.uploadStatusText);
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.startUpload) },
            ...{ class: "primary-pill-btn full-width" },
            disabled: (!__VLS_ctx.selectedFile || __VLS_ctx.isUploading),
            id: "btn-start-upload",
        });
        if (__VLS_ctx.isUploading) {
            const __VLS_120 = {}.ElIcon;
            /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
            // @ts-ignore
            const __VLS_121 = __VLS_asFunctionalComponent(__VLS_120, new __VLS_120({
                ...{ class: "is-loading" },
            }));
            const __VLS_122 = __VLS_121({
                ...{ class: "is-loading" },
            }, ...__VLS_functionalComponentArgsRest(__VLS_121));
            __VLS_123.slots.default;
            const __VLS_124 = {}.Loading;
            /** @type {[typeof __VLS_components.Loading, ]} */ ;
            // @ts-ignore
            const __VLS_125 = __VLS_asFunctionalComponent(__VLS_124, new __VLS_124({}));
            const __VLS_126 = __VLS_125({}, ...__VLS_functionalComponentArgsRest(__VLS_125));
            var __VLS_123;
        }
        else {
            const __VLS_128 = {}.ElIcon;
            /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
            // @ts-ignore
            const __VLS_129 = __VLS_asFunctionalComponent(__VLS_128, new __VLS_128({}));
            const __VLS_130 = __VLS_129({}, ...__VLS_functionalComponentArgsRest(__VLS_129));
            __VLS_131.slots.default;
            const __VLS_132 = {}.Promotion;
            /** @type {[typeof __VLS_components.Promotion, ]} */ ;
            // @ts-ignore
            const __VLS_133 = __VLS_asFunctionalComponent(__VLS_132, new __VLS_132({}));
            const __VLS_134 = __VLS_133({}, ...__VLS_functionalComponentArgsRest(__VLS_133));
            var __VLS_131;
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (__VLS_ctx.isUploading ? '正在上传并转存网盘中...' : '开始上传至夸克网盘并上架');
        if (__VLS_ctx.uploadFeedback) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "upload-feedback-badge" },
                ...{ class: (__VLS_ctx.uploadFeedbackType) },
            });
            (__VLS_ctx.uploadFeedback);
        }
    }
    if (__VLS_ctx.activeTab === 'dramas') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "tab-content-panel" },
            id: "panel-my-dramas",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "dramas-list-grid" },
        });
        for (const [drama] of __VLS_getVForSourceType((__VLS_ctx.myDramas))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                key: (drama.id),
                ...{ class: "my-drama-card" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "drama-cover-box" },
                ...{ style: ({ backgroundImage: `url(${drama.cover_url})` }) },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "status-chip" },
            });
            (drama.status);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "drama-info-box" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
                ...{ class: "drama-card-title" },
            });
            (drama.title);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "drama-card-tags" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "tag-pill" },
            });
            (drama.category);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "tag-pill" },
            });
            (drama.episodes_count);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "tag-pill" },
            });
            (drama.play_count);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
                ...{ class: "drama-card-desc" },
            });
            (drama.description);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "drama-card-footer" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "time-label" },
            });
            (drama.created_at);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "drama-actions-group" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!!(!__VLS_ctx.isCreator))
                            return;
                        if (!(__VLS_ctx.activeTab === 'dramas'))
                            return;
                        __VLS_ctx.manageEpisodes(drama);
                    } },
                ...{ class: "secondary-pill-btn btn-xs" },
                id: ('btn-episodes-' + drama.id),
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!!(!__VLS_ctx.isCreator))
                            return;
                        if (!(__VLS_ctx.activeTab === 'dramas'))
                            return;
                        __VLS_ctx.openEditDramaModal(drama);
                    } },
                ...{ class: "secondary-pill-btn btn-xs" },
                id: ('btn-edit-drama-' + drama.id),
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!!(!__VLS_ctx.isCreator))
                            return;
                        if (!(__VLS_ctx.activeTab === 'dramas'))
                            return;
                        __VLS_ctx.toggleDramaStatus(drama);
                    } },
                ...{ class: "secondary-pill-btn btn-xs" },
                id: ('btn-status-' + drama.id),
            });
            (drama.status === 'READY' || drama.status === 'PUBLISHED' ? '屏蔽' : '上架');
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!!(!__VLS_ctx.isCreator))
                            return;
                        if (!(__VLS_ctx.activeTab === 'dramas'))
                            return;
                        __VLS_ctx.handleDeleteDrama(drama);
                    } },
                ...{ class: "secondary-pill-btn btn-xs btn-danger-text" },
                id: ('btn-del-drama-' + drama.id),
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!!(!__VLS_ctx.isCreator))
                            return;
                        if (!(__VLS_ctx.activeTab === 'dramas'))
                            return;
                        __VLS_ctx.goToPlay(drama.id);
                    } },
                ...{ class: "play-action-btn" },
            });
        }
    }
    if (__VLS_ctx.activeTab === 'bi') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "tab-content-panel" },
            id: "panel-creator-bi",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "creator-kpi-grid" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-bento-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-header-row" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "kpi-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "kpi-badge blue" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-value-num" },
        });
        (__VLS_ctx.formatNumber(__VLS_ctx.totalViews));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-hint" },
        });
        (__VLS_ctx.myDramas.length);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-bento-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-header-row" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "kpi-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "kpi-badge pink" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-value-num" },
        });
        (__VLS_ctx.formatNumber(__VLS_ctx.totalLikes));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-hint" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-bento-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-header-row" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "kpi-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "kpi-badge amber" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-value-num text-amber" },
        });
        (__VLS_ctx.totalCoins);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-hint" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-bento-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-header-row" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "kpi-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "kpi-badge green" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-value-num" },
        });
        (__VLS_ctx.avgViralScore);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "kpi-hint" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "creator-bi-table-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "card-title-row" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "title-wrap" },
        });
        const __VLS_136 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_137 = __VLS_asFunctionalComponent(__VLS_136, new __VLS_136({
            size: (18),
            ...{ class: "title-icon" },
        }));
        const __VLS_138 = __VLS_137({
            size: (18),
            ...{ class: "title-icon" },
        }, ...__VLS_functionalComponentArgsRest(__VLS_137));
        __VLS_139.slots.default;
        const __VLS_140 = {}.TrendCharts;
        /** @type {[typeof __VLS_components.TrendCharts, ]} */ ;
        // @ts-ignore
        const __VLS_141 = __VLS_asFunctionalComponent(__VLS_140, new __VLS_140({}));
        const __VLS_142 = __VLS_141({}, ...__VLS_functionalComponentArgsRest(__VLS_141));
        var __VLS_139;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
            ...{ class: "bi-card-title" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "bi-card-badge" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "table-container" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.table, __VLS_intrinsicElements.table)({
            ...{ class: "creator-bi-table" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.thead, __VLS_intrinsicElements.thead)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tbody, __VLS_intrinsicElements.tbody)({});
        for (const [item] of __VLS_getVForSourceType((__VLS_ctx.myDramas))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({
                key: (item.id),
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                ...{ class: "font-bold" },
            });
            (item.title);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "bi-tag-pill" },
            });
            (item.category);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            (item.total_episodes || item.episodes_count || 0);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            (__VLS_ctx.formatNumber(item.view_count || item.play_count || 0));
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            (__VLS_ctx.formatNumber(item.like_count || 0));
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                ...{ class: "text-amber font-bold" },
            });
            (item.coin_count || 0);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "score-pill" },
            });
            (item.viral_score || 88);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "status-indicator-tag" },
                ...{ class: (item.status === 'READY' || item.status === 'PUBLISHED' ? 'tag-pub' : 'tag-draft') },
            });
            (item.status === 'READY' || item.status === 'PUBLISHED' ? '上架公映' : '草稿归档');
        }
        if (__VLS_ctx.myDramas.length === 0) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                colspan: "8",
                ...{ class: "text-center py-6 text-sub" },
            });
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "creator-insights-grid" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "insight-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "insight-head" },
        });
        const __VLS_144 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_145 = __VLS_asFunctionalComponent(__VLS_144, new __VLS_144({
            ...{ class: "insight-icon" },
        }));
        const __VLS_146 = __VLS_145({
            ...{ class: "insight-icon" },
        }, ...__VLS_functionalComponentArgsRest(__VLS_145));
        __VLS_147.slots.default;
        const __VLS_148 = {}.VideoPlay;
        /** @type {[typeof __VLS_components.VideoPlay, ]} */ ;
        // @ts-ignore
        const __VLS_149 = __VLS_asFunctionalComponent(__VLS_148, new __VLS_148({}));
        const __VLS_150 = __VLS_149({}, ...__VLS_functionalComponentArgsRest(__VLS_149));
        var __VLS_147;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "insight-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "insight-head" },
        });
        const __VLS_152 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_153 = __VLS_asFunctionalComponent(__VLS_152, new __VLS_152({
            ...{ class: "insight-icon" },
        }));
        const __VLS_154 = __VLS_153({
            ...{ class: "insight-icon" },
        }, ...__VLS_functionalComponentArgsRest(__VLS_153));
        __VLS_155.slots.default;
        const __VLS_156 = {}.Star;
        /** @type {[typeof __VLS_components.Star, ]} */ ;
        // @ts-ignore
        const __VLS_157 = __VLS_asFunctionalComponent(__VLS_156, new __VLS_156({}));
        const __VLS_158 = __VLS_157({}, ...__VLS_functionalComponentArgsRest(__VLS_157));
        var __VLS_155;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    }
}
if (__VLS_ctx.showNewFolderModal) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-backdrop-scrim" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-glass-card" },
        id: "modal-mkdir",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "modal-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "modal-subtext" },
    });
    (__VLS_ctx.currentPath);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-item-field" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        ...{ onKeyup: (__VLS_ctx.confirmMkdir) },
        value: (__VLS_ctx.newFolderName),
        type: "text",
        ...{ class: "apple-text-input" },
        placeholder: "例如：重生之狂傲仙尊",
        id: "input-mkdir-name",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-actions-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showNewFolderModal))
                    return;
                __VLS_ctx.showNewFolderModal = false;
            } },
        ...{ class: "secondary-pill-btn" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.confirmMkdir) },
        ...{ class: "primary-pill-btn" },
        disabled: (!__VLS_ctx.newFolderName.trim() || __VLS_ctx.mkdirLoading),
        id: "btn-confirm-mkdir",
    });
    (__VLS_ctx.mkdirLoading ? '正在创建...' : '确认新建');
}
if (__VLS_ctx.showEditDramaModal) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-backdrop-scrim" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-glass-card" },
        id: "modal-edit-drama",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "modal-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "modal-subtext" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-item-field" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        value: (__VLS_ctx.dramaForm.title),
        type: "text",
        ...{ class: "apple-text-input" },
        id: "input-edit-drama-title",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-item-field" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
        value: (__VLS_ctx.dramaForm.category),
        ...{ class: "apple-text-input" },
        id: "select-edit-drama-category",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "都市战神",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "悬疑逆袭",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "古装穿越",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "豪门甜宠",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "短剧精选",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-item-field" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        value: (__VLS_ctx.dramaForm.cover_url),
        type: "text",
        ...{ class: "apple-text-input" },
        id: "input-edit-drama-cover",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-item-field" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.textarea, __VLS_intrinsicElements.textarea)({
        value: (__VLS_ctx.dramaForm.description),
        ...{ class: "apple-text-input" },
        rows: "3",
        id: "input-edit-drama-desc",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-actions-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showEditDramaModal))
                    return;
                __VLS_ctx.showEditDramaModal = false;
            } },
        ...{ class: "secondary-pill-btn" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.confirmUpdateDrama) },
        ...{ class: "primary-pill-btn" },
        id: "btn-save-drama-edit",
    });
}
if (__VLS_ctx.showEpisodesDrawer) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-backdrop-scrim" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-glass-card modal-wide" },
        id: "modal-manage-episodes",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "drawer-header-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "modal-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "modal-subtext" },
    });
    (__VLS_ctx.selectedDrama?.title);
    (__VLS_ctx.episodesList.length);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showEpisodesDrawer))
                    return;
                __VLS_ctx.showEpisodesDrawer = false;
            } },
        ...{ class: "close-x-btn" },
    });
    if (__VLS_ctx.episodesLoading) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "pan-loading-box" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "spinner" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "episodes-manage-table-wrap" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.table, __VLS_intrinsicElements.table)({
            ...{ class: "creator-table" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.thead, __VLS_intrinsicElements.thead)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
            ...{ style: {} },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
            ...{ style: {} },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tbody, __VLS_intrinsicElements.tbody)({});
        for (const [ep] of __VLS_getVForSourceType((__VLS_ctx.episodesList))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({
                key: (ep.id),
                id: ('ep-row-' + ep.id),
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                ...{ class: "font-bold" },
            });
            (ep.episode_num);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
                ...{ class: "table-inline-input" },
                placeholder: "分集标题",
            });
            (ep.title);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                ...{ class: "sub-text-col" },
            });
            (ep.duration_seconds ? ep.duration_seconds + 's' : '-');
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "climax-input-wrap" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
                type: "number",
                step: "0.5",
                min: "0",
                ...{ class: "table-inline-input mini" },
                placeholder: "如 35.5",
            });
            (ep.climax_seconds);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "sec-unit" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!(__VLS_ctx.showEpisodesDrawer))
                            return;
                        if (!!(__VLS_ctx.episodesLoading))
                            return;
                        __VLS_ctx.saveEpisodeChanges(ep);
                    } },
                ...{ class: "secondary-pill-btn btn-xs" },
                id: ('btn-save-ep-' + ep.id),
            });
        }
        if (__VLS_ctx.episodesList.length === 0) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                colspan: "5",
                ...{ class: "empty-table-cell" },
            });
        }
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-actions-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showEpisodesDrawer))
                    return;
                __VLS_ctx.showEpisodesDrawer = false;
            } },
        ...{ class: "primary-pill-btn" },
    });
}
/** @type {__VLS_StyleScopedClasses['creator-studio-container']} */ ;
/** @type {__VLS_StyleScopedClasses['studio-main-body']} */ ;
/** @type {__VLS_StyleScopedClasses['studio-ambient-bg']} */ ;
/** @type {__VLS_StyleScopedClasses['studio-orb']} */ ;
/** @type {__VLS_StyleScopedClasses['orb-a']} */ ;
/** @type {__VLS_StyleScopedClasses['studio-orb']} */ ;
/** @type {__VLS_StyleScopedClasses['orb-b']} */ ;
/** @type {__VLS_StyleScopedClasses['studio-top-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['studio-badge-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['studio-page-title']} */ ;
/** @type {__VLS_StyleScopedClasses['studio-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['studio-top-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['secondary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['is-loading']} */ ;
/** @type {__VLS_StyleScopedClasses['primary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['apply-creator-card']} */ ;
/** @type {__VLS_StyleScopedClasses['apply-header-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['apply-icon-orb']} */ ;
/** @type {__VLS_StyleScopedClasses['apply-title']} */ ;
/** @type {__VLS_StyleScopedClasses['apply-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['apply-form-body']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-field']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-field']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['apply-action-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['submit-apply-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['apply-feedback-msg']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-workspace-area']} */ ;
/** @type {__VLS_StyleScopedClasses['studio-tabs-row']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-content-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['pan-breadcrumb-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['breadcrumb-left']} */ ;
/** @type {__VLS_StyleScopedClasses['path-label']} */ ;
/** @type {__VLS_StyleScopedClasses['current-path-text']} */ ;
/** @type {__VLS_StyleScopedClasses['breadcrumb-right']} */ ;
/** @type {__VLS_StyleScopedClasses['secondary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['secondary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['pan-loading-box']} */ ;
/** @type {__VLS_StyleScopedClasses['spinner']} */ ;
/** @type {__VLS_StyleScopedClasses['pan-items-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['pan-item-card']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-card']} */ ;
/** @type {__VLS_StyleScopedClasses['item-glyph-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['item-meta-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['item-main-title']} */ ;
/** @type {__VLS_StyleScopedClasses['item-sub-meta']} */ ;
/** @type {__VLS_StyleScopedClasses['pan-item-card']} */ ;
/** @type {__VLS_StyleScopedClasses['file-card']} */ ;
/** @type {__VLS_StyleScopedClasses['item-glyph-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['item-meta-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['item-main-title']} */ ;
/** @type {__VLS_StyleScopedClasses['item-sub-meta']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-pan-box']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-pan-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-content-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-builder-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-form-side']} */ ;
/** @type {__VLS_StyleScopedClasses['panel-section-title']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-field']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-field']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-row']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-field']} */ ;
/** @type {__VLS_StyleScopedClasses['half']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-field']} */ ;
/** @type {__VLS_StyleScopedClasses['half']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-field']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-dropzone-side']} */ ;
/** @type {__VLS_StyleScopedClasses['file-drop-box']} */ ;
/** @type {__VLS_StyleScopedClasses['dropzone-idle']} */ ;
/** @type {__VLS_StyleScopedClasses['drop-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['dropzone-file-selected']} */ ;
/** @type {__VLS_StyleScopedClasses['file-success-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['selected-name']} */ ;
/** @type {__VLS_StyleScopedClasses['selected-size']} */ ;
/** @type {__VLS_StyleScopedClasses['remove-file-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-action-dock']} */ ;
/** @type {__VLS_StyleScopedClasses['progress-track-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['progress-bar-fill']} */ ;
/** @type {__VLS_StyleScopedClasses['progress-label']} */ ;
/** @type {__VLS_StyleScopedClasses['primary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['full-width']} */ ;
/** @type {__VLS_StyleScopedClasses['is-loading']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-feedback-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-content-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['dramas-list-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['my-drama-card']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-cover-box']} */ ;
/** @type {__VLS_StyleScopedClasses['status-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-info-box']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-card-title']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-card-tags']} */ ;
/** @type {__VLS_StyleScopedClasses['tag-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['tag-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['tag-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-card-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-card-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['time-label']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-actions-group']} */ ;
/** @type {__VLS_StyleScopedClasses['secondary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-xs']} */ ;
/** @type {__VLS_StyleScopedClasses['secondary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-xs']} */ ;
/** @type {__VLS_StyleScopedClasses['secondary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-xs']} */ ;
/** @type {__VLS_StyleScopedClasses['secondary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-xs']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-danger-text']} */ ;
/** @type {__VLS_StyleScopedClasses['play-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tab-content-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-kpi-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-header-row']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-label']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['blue']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-value-num']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-hint']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-header-row']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-label']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['pink']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-value-num']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-hint']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-header-row']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-label']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['amber']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-value-num']} */ ;
/** @type {__VLS_StyleScopedClasses['text-amber']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-hint']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-header-row']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-label']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['green']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-value-num']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-hint']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-bi-table-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-title-row']} */ ;
/** @type {__VLS_StyleScopedClasses['title-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['title-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['bi-card-title']} */ ;
/** @type {__VLS_StyleScopedClasses['bi-card-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['table-container']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-bi-table']} */ ;
/** @type {__VLS_StyleScopedClasses['font-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['bi-tag-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['text-amber']} */ ;
/** @type {__VLS_StyleScopedClasses['font-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['score-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['status-indicator-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['text-center']} */ ;
/** @type {__VLS_StyleScopedClasses['py-6']} */ ;
/** @type {__VLS_StyleScopedClasses['text-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-insights-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['insight-card']} */ ;
/** @type {__VLS_StyleScopedClasses['insight-head']} */ ;
/** @type {__VLS_StyleScopedClasses['insight-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['insight-card']} */ ;
/** @type {__VLS_StyleScopedClasses['insight-head']} */ ;
/** @type {__VLS_StyleScopedClasses['insight-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-backdrop-scrim']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-title']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-field']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-actions-row']} */ ;
/** @type {__VLS_StyleScopedClasses['secondary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['primary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-backdrop-scrim']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-title']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-field']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-field']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-field']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-item-field']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-text-input']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-actions-row']} */ ;
/** @type {__VLS_StyleScopedClasses['secondary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['primary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-backdrop-scrim']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-wide']} */ ;
/** @type {__VLS_StyleScopedClasses['drawer-header-row']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-title']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['close-x-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['pan-loading-box']} */ ;
/** @type {__VLS_StyleScopedClasses['spinner']} */ ;
/** @type {__VLS_StyleScopedClasses['episodes-manage-table-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-table']} */ ;
/** @type {__VLS_StyleScopedClasses['font-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['table-inline-input']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-text-col']} */ ;
/** @type {__VLS_StyleScopedClasses['climax-input-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['table-inline-input']} */ ;
/** @type {__VLS_StyleScopedClasses['mini']} */ ;
/** @type {__VLS_StyleScopedClasses['sec-unit']} */ ;
/** @type {__VLS_StyleScopedClasses['secondary-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-xs']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-table-cell']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-actions-row']} */ ;
/** @type {__VLS_StyleScopedClasses['primary-pill-btn']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            AdminHeader: AdminHeader,
            Refresh: Refresh,
            Folder: Folder,
            Upload: Upload,
            Film: Film,
            Top: Top,
            VideoCamera: VideoCamera,
            Check: Check,
            Promotion: Promotion,
            Loading: Loading,
            VideoPlay: VideoPlay,
            DataAnalysis: DataAnalysis,
            TrendCharts: TrendCharts,
            Star: Star,
            handleUserChanged: handleUserChanged,
            isCreator: isCreator,
            applyForm: applyForm,
            applySubmitting: applySubmitting,
            applyMessage: applyMessage,
            submitApply: submitApply,
            activeTab: activeTab,
            totalViews: totalViews,
            totalLikes: totalLikes,
            totalCoins: totalCoins,
            avgViralScore: avgViralScore,
            handleSelectTab: handleSelectTab,
            currentPath: currentPath,
            panFolders: panFolders,
            panFiles: panFiles,
            panLoading: panLoading,
            fetchPanTree: fetchPanTree,
            enterFolder: enterFolder,
            navigateUp: navigateUp,
            showNewFolderModal: showNewFolderModal,
            newFolderName: newFolderName,
            mkdirLoading: mkdirLoading,
            confirmMkdir: confirmMkdir,
            uploadTargetFolder: uploadTargetFolder,
            uploadDramaTitle: uploadDramaTitle,
            uploadEpisodeTitle: uploadEpisodeTitle,
            uploadEpisodeNum: uploadEpisodeNum,
            uploadCategory: uploadCategory,
            selectedFile: selectedFile,
            isDragging: isDragging,
            fileInputRef: fileInputRef,
            isUploading: isUploading,
            uploadProgress: uploadProgress,
            uploadStatusText: uploadStatusText,
            uploadFeedback: uploadFeedback,
            uploadFeedbackType: uploadFeedbackType,
            triggerFileInput: triggerFileInput,
            handleFileSelect: handleFileSelect,
            handleFileDrop: handleFileDrop,
            startUpload: startUpload,
            myDramas: myDramas,
            isSyncingDramas: isSyncingDramas,
            handleSyncQuarkDramas: handleSyncQuarkDramas,
            goToPlay: goToPlay,
            showEditDramaModal: showEditDramaModal,
            dramaForm: dramaForm,
            openEditDramaModal: openEditDramaModal,
            confirmUpdateDrama: confirmUpdateDrama,
            toggleDramaStatus: toggleDramaStatus,
            handleDeleteDrama: handleDeleteDrama,
            showEpisodesDrawer: showEpisodesDrawer,
            selectedDrama: selectedDrama,
            episodesList: episodesList,
            episodesLoading: episodesLoading,
            manageEpisodes: manageEpisodes,
            saveEpisodeChanges: saveEpisodeChanges,
            formatBytes: formatBytes,
            formatDate: formatDate,
            formatNumber: formatNumber,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=CreatorStudioView.vue.js.map