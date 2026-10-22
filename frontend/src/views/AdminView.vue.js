/// <reference types="../../node_modules/.vue-global-types/vue_3.5_0_0_0.d.ts" />
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import * as echarts from 'echarts';
import { ElMessage, ElMessageBox } from 'element-plus';
import AdminHeader from '../components/AdminHeader.vue';
import { DataLine, TrendCharts, Film, Refresh, Picture, User, Check, Close, Setting, Search, Delete, Edit, Plus, Switch, Lock, Unlock, View, Hide, Fold, Expand, DocumentChecked, ChatLineSquare, Rank, Upload, Promotion } from '@element-plus/icons-vue';
import { adminApi } from '../api/admin';
// Sidebar State
const isSidebarPinned = ref(true);
const isSidebarHovered = ref(false);
const isSidebarExpanded = computed(() => isSidebarPinned.value || isSidebarHovered.value);
function onSidebarMouseEnter() {
    if (!isSidebarPinned.value) {
        isSidebarHovered.value = true;
    }
}
function onSidebarMouseLeave() {
    if (!isSidebarPinned.value) {
        isSidebarHovered.value = false;
    }
}
function toggleSidebarPin() {
    isSidebarPinned.value = !isSidebarPinned.value;
    isSidebarHovered.value = false;
}
// Navigation Tab State
const currentTab = ref('bi');
const tabTitleMap = {
    bi: 'BI 全景驾驶舱与预测走势',
    dramas: '短剧资产编目与封面治理',
    sync: '网盘增量/全量同步中心',
    carousels: '首页 5 秒焦点轮播运营调度',
    users: '用户管理与 RBAC 权限流转',
    applications: '资质双轨入驻审批 (创作者/审核员)',
    contents: '互动合规风控 (弹幕/评论机审)',
    engine: '模型引擎与 RAG 参数配置'
};
const currentTabTitle = computed(() => tabTitleMap[currentTab.value] || '管理控制台');
function selectTab(tab) {
    currentTab.value = tab;
    if (tab === 'bi') {
        nextTick(() => initBiChart());
    }
}
// Data States
const loading = ref(false);
const biMetrics = ref({
    total_views: 0,
    total_danmakus: 0,
    total_comments: 0,
    total_likes: 0,
    total_users: 0,
    active_creators: 0,
    active_reviewers: 0,
    banned_users: 0,
    pending_applications: 0,
    total_dramas: 0,
    total_episodes: 0
});
// ECharts Instance & Trends Data
const biChartRef = ref(null);
let chartInstance = null;
const biTrendsData = ref(null);
const viralRankings = computed(() => biTrendsData.value?.viral_rankings || []);
// Dramas State
const dramasList = ref([]);
const dramaSearchKeyword = ref('');
const dramaPage = ref(1);
const dramaPageSize = ref(10);
const selectedDramaIds = ref([]);
const defaultDramaPoster = "data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%22320%22%20height%3D%22480%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cdefs%3E%3ClinearGradient%20id%3D%22g%22%20x1%3D%220%25%22%20y1%3D%220%25%22%20x2%3D%22100%25%22%20y2%3D%22100%25%22%3E%3Cstop%20offset%3D%220%25%22%20stop-color%3D%22%231c1d22%22%2F%3E%3Cstop%20offset%3D%22100%25%22%20stop-color%3D%22%232c2d35%22%2F%3E%3C%2FlinearGradient%3E%3C%2Fdefs%3E%3Crect%20width%3D%22100%25%22%20height%3D%22100%25%22%20fill%3D%22url(%23g)%22%2F%3E%3Ctext%20x%3D%2250%25%22%20y%3D%2250%25%22%20fill%3D%22%238e8e93%22%20font-size%3D%2218%22%20font-family%3D%22sans-serif%22%20text-anchor%3D%22middle%22%20dy%3D%22.3em%22%3E%E5%AE%98%E6%96%B9%E6%B5%B7%E6%8A%A5%3C%2Ftext%3E%3C%2Fsvg%3E";
const filteredDramas = computed(() => {
    if (!dramaSearchKeyword.value.trim())
        return dramasList.value;
    const kw = dramaSearchKeyword.value.toLowerCase();
    return dramasList.value.filter(d => d.title.toLowerCase().includes(kw) || (d.category || '').toLowerCase().includes(kw));
});
const paginatedDramas = computed(() => {
    const start = (dramaPage.value - 1) * dramaPageSize.value;
    return filteredDramas.value.slice(start, start + dramaPageSize.value);
});
const isAllDramasSelected = computed(() => {
    return paginatedDramas.value.length > 0 && paginatedDramas.value.every(d => selectedDramaIds.value.includes(d.id));
});
function toggleSelectAllDramas() {
    if (isAllDramasSelected.value) {
        selectedDramaIds.value = selectedDramaIds.value.filter(id => !paginatedDramas.value.some(d => d.id === id));
    }
    else {
        const curIds = paginatedDramas.value.map(d => d.id);
        selectedDramaIds.value = Array.from(new Set([...selectedDramaIds.value, ...curIds]));
    }
}
async function handleBatchDeleteDramas() {
    if (selectedDramaIds.value.length === 0)
        return;
    try {
        await ElMessageBox.confirm(`确定要批量彻底删除选中的 ${selectedDramaIds.value.length} 部短剧作品吗？其剧集资源也将一并移除！`, '批量删除短剧', {
            type: 'warning',
            confirmButtonText: '确定删除',
            cancelButtonText: '取消'
        });
        const res = await adminApi.batchDeleteDramas(selectedDramaIds.value);
        ElMessage.success(res?.message || '批量删除短剧成功！');
        selectedDramaIds.value = [];
        await loadDramas();
    }
    catch (err) { }
}
// Edit Cover & Metadata State
const showEditCoverDialog = ref(false);
const editingDrama = ref(null);
const editingCoverUrl = ref('');
const editingDramaPosters = ref([]);
const editingDramaMeta = ref({
    id: '',
    title: '',
    category: '',
    summary: '',
    status: 'PUBLISHED'
});
const imageUploadInputRef = ref(null);
const uploadingImage = ref(false);
const isCoverDragOver = ref(false);
const coverImgError = ref(false);
// Posters Carousel Dialog
const showPostersCarouselDialog = ref(false);
const activeDramaForPosters = ref(null);
// Sync State
const syncMode = ref('incremental');
const isSyncing = ref(false);
const syncResult = ref(null);
// Carousels State
const carouselsList = ref([]);
const showCarouselDialog = ref(false);
const isEditingCarousel = ref(false);
const dramaOptionsList = ref([]);
const selectedCarouselDramaId = ref('');
const selectedCarouselDramaModalId = ref('');
const workbenchImgError = ref(false);
const carouselForm = ref({
    title: '',
    subtitle: '',
    tag: '本周爆款榜首',
    cover_url: '',
    video_id: '',
    sort_order: 1,
    is_active: true
});
const selectedWorkbenchDrama = computed(() => {
    return dramaOptionsList.value.find(d => d.id === selectedCarouselDramaId.value);
});
const workbenchPreviewCover = computed(() => {
    if (selectedWorkbenchDrama.value?.cover_url) {
        return selectedWorkbenchDrama.value.cover_url;
    }
    return carouselsList.value[0]?.cover_url || '';
});
const workbenchPreviewTitle = computed(() => {
    if (selectedWorkbenchDrama.value?.title) {
        return selectedWorkbenchDrama.value.title;
    }
    return carouselsList.value[0]?.title || '首屏焦点画报推荐';
});
const workbenchPreviewSubtitle = computed(() => {
    if (selectedWorkbenchDrama.value?.category) {
        return selectedWorkbenchDrama.value.category + ' · 全网独家热播';
    }
    return carouselsList.value[0]?.subtitle || '沉浸式观剧，连播爽不停';
});
const workbenchPreviewTag = computed(() => {
    return carouselsList.value[0]?.tag || '本周爆款榜首';
});
// Users State
const usersList = ref([]);
const userSearchKeyword = ref('');
const userFilterRole = ref('ALL');
const userFilterStatus = ref('ALL');
const userTotalCount = ref(0);
const userPage = ref(1);
const userPageSize = ref(10);
const selectedUserIds = ref([]);
const isAllUsersSelected = computed(() => {
    return usersList.value.length > 0 && selectedUserIds.value.length === usersList.value.length;
});
function toggleSelectAllUsers() {
    if (isAllUsersSelected.value) {
        selectedUserIds.value = [];
    }
    else {
        selectedUserIds.value = usersList.value.map(u => u.id);
    }
}
async function handleBatchDeleteUsers() {
    if (selectedUserIds.value.length === 0)
        return;
    try {
        await ElMessageBox.confirm(`确定要批量永久删除选中的 ${selectedUserIds.value.length} 个用户账号吗？此操作将级联删除其全部关联数据！`, '批量删除确认', {
            type: 'warning',
            confirmButtonText: '确定删除',
            cancelButtonText: '取消'
        });
        const res = await adminApi.batchDeleteUsers(selectedUserIds.value);
        ElMessage.success(res?.message || '批量删除成功！');
        selectedUserIds.value = [];
        await loadUsers();
    }
    catch (err) { }
}
const showRoleDialog = ref(false);
const selectedUserForRole = ref(null);
const selectedRole = ref('USER');
// User CRUD Modals
const showAddUserDialog = ref(false);
const addUserForm = ref({
    username: '',
    password: '',
    nickname: '',
    role: 'USER',
    coins: 50,
    vip_days: 0
});
const showEditUserDialog = ref(false);
const selectedUserForEdit = ref(null);
const editUserForm = ref({
    id: '',
    username: '',
    nickname: '',
    password: '',
    role: 'USER',
    status: 'ACTIVE',
    coins_adjustment: 0,
    vip_days: 0
});
// Applications State
const applicationSubTab = ref('creators');
const pendingCreators = ref([]);
const pendingReviewers = ref([]);
const pendingCount = computed(() => pendingCreators.value.length + pendingReviewers.value.length);
// Content Moderation State
const contentSubTab = ref('queue');
const reviewQueueList = ref([]);
const sensitiveWordsList = ref([]);
const sensitiveWordsTotal = ref(0);
const sensitiveWordSearch = ref('');
const sensitiveWordCategory = ref('ALL');
const sensitiveWordLevel = ref('ALL');
const showAddWordDialog = ref(false);
const newWordForm = ref({ word: '', category: '违禁', level: 'HIGH' });
const dfaTestText = ref('');
const dfaTestResult = ref(null);
const dfaTesting = ref(false);
const danmakusList = ref([]);
const selectedDanmakuIds = ref([]);
const danmakuSearchQuery = ref('');
const commentsList = ref([]);
// Engine Form
const engineForm = ref({
    modelName: localStorage.getItem('cinema_active_model') || 'deepseek-r1:7b',
    temperature: 0.7,
    prompt: '你是一位精通短剧镜头语言与剧情反转的电影解说伴读助手。'
});
const route = useRoute();
let themeObserver = null;
onMounted(async () => {
    if (route.query.tab && typeof route.query.tab === 'string') {
        currentTab.value = route.query.tab;
    }
    await loadAllData();
    window.addEventListener('resize', handleWindowResize);
    themeObserver = new MutationObserver((mutations) => {
        for (const m of mutations) {
            if (m.type === 'attributes' && m.attributeName === 'data-theme') {
                if (currentTab.value === 'bi') {
                    initBiChart();
                }
            }
        }
    });
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
});
onUnmounted(() => {
    window.removeEventListener('resize', handleWindowResize);
    if (themeObserver) {
        themeObserver.disconnect();
        themeObserver = null;
    }
    if (chartInstance) {
        chartInstance.dispose();
        chartInstance = null;
    }
});
function handleWindowResize() {
    if (chartInstance) {
        chartInstance.resize();
    }
}
async function loadAllData() {
    loading.value = true;
    try {
        await Promise.all([
            loadBiOverview(),
            loadBiTrends(),
            loadDramas(),
            loadDramaOptions(),
            loadCarousels(),
            loadUsers(),
            loadApplications(),
            loadContents()
        ]);
    }
    catch (e) {
        console.error('Failed to load admin overview data:', e);
    }
    finally {
        loading.value = false;
    }
}
async function refreshCurrentTab() {
    loading.value = true;
    try {
        if (currentTab.value === 'bi') {
            await Promise.all([loadBiOverview(), loadBiTrends()]);
        }
        else if (currentTab.value === 'dramas') {
            await loadDramas();
        }
        else if (currentTab.value === 'carousels') {
            await loadCarousels();
        }
        else if (currentTab.value === 'users') {
            await loadUsers();
        }
        else if (currentTab.value === 'applications') {
            await loadApplications();
        }
        else if (currentTab.value === 'contents') {
            await loadContents();
        }
        ElMessage.success('数据已更新至最新状态');
    }
    catch (err) {
        ElMessage.error(err.message || '刷新失败');
    }
    finally {
        loading.value = false;
    }
}
// =========================================================================
// BI & ECharts
// =========================================================================
async function loadBiOverview() {
    const res = await adminApi.getBiMetrics();
    const data = res?.data || res;
    if (data?.bi_cards) {
        biMetrics.value = data.bi_cards;
    }
}
async function loadBiTrends() {
    const res = await adminApi.getBiTrends();
    const data = res?.data || res;
    if (data) {
        biTrendsData.value = data;
        nextTick(() => {
            initBiChart();
        });
    }
}
function initBiChart() {
    if (!biChartRef.value || !biTrendsData.value)
        return;
    if (!chartInstance) {
        chartInstance = echarts.init(biChartRef.value);
    }
    const { history, prediction } = biTrendsData.value;
    const allDates = [...history.dates, ...prediction.dates];
    // Construct series data
    // History series: real values for history dates, null for prediction dates
    const historySeriesData = [
        ...history.views,
        ...prediction.dates.map(() => null)
    ];
    // Prediction series: bridges from last history date
    const lastHistoryVal = history.views[history.views.length - 1];
    const forecastSeriesData = [
        ...history.views.slice(0, -1).map(() => null),
        lastHistoryVal,
        ...prediction.forecast_views
    ];
    // Confidence Bounds for prediction
    const upperData = [
        ...history.views.slice(0, -1).map(() => null),
        lastHistoryVal,
        ...prediction.upper_bound
    ];
    const lowerData = [
        ...history.views.slice(0, -1).map(() => null),
        lastHistoryVal,
        ...prediction.lower_bound
    ];
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const axisTextColor = isLight ? '#48484a' : 'rgba(255, 255, 255, 0.65)';
    const axisLineColor = isLight ? 'rgba(0, 0, 0, 0.15)' : 'rgba(255, 255, 255, 0.2)';
    const splitLineColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';
    const tooltipBg = isLight ? 'rgba(255, 255, 255, 0.96)' : 'rgba(28, 28, 30, 0.92)';
    const tooltipBorder = isLight ? 'rgba(0, 0, 0, 0.12)' : 'rgba(255, 255, 255, 0.15)';
    const tooltipTextColor = isLight ? '#1d1d1f' : '#FFFFFF';
    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            backgroundColor: tooltipBg,
            borderColor: tooltipBorder,
            textStyle: { color: tooltipTextColor, fontSize: 12 },
            formatter: (params) => {
                let str = `<div style="font-weight: bold; margin-bottom: 4px;">${params[0].axisValue}</div>`;
                params.forEach((item) => {
                    if (item.value !== null && item.value !== undefined && item.seriesName !== '置信区间下限') {
                        const valFormatted = Number(item.value).toLocaleString();
                        str += `<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${item.color};margin-right:6px;"></span>${item.seriesName}: <b>${valFormatted} 次</b></div>`;
                    }
                });
                return str;
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '8%',
            top: '12%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: allDates,
            axisLine: { lineStyle: { color: axisLineColor } },
            axisLabel: { color: axisTextColor, fontSize: 11, fontWeight: isLight ? 600 : 400 }
        },
        yAxis: {
            type: 'value',
            splitLine: { lineStyle: { color: splitLineColor } },
            axisLine: { show: true, lineStyle: { color: axisLineColor } },
            axisLabel: {
                color: axisTextColor,
                fontSize: 11,
                fontWeight: isLight ? 600 : 400,
                formatter: (val) => {
                    return val >= 10000 ? (val / 10000).toFixed(1) + 'w' : val.toString();
                }
            }
        },
        series: [
            {
                name: '历史实测播放',
                type: 'line',
                smooth: true,
                data: historySeriesData,
                symbol: 'circle',
                symbolSize: 6,
                itemStyle: { color: '#0071E3' },
                lineStyle: { width: 3, color: '#0071E3' },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(0, 113, 227, 0.4)' },
                        { offset: 1, color: 'rgba(0, 113, 227, 0.0)' }
                    ])
                }
            },
            {
                name: 'AI 预测走势 (Holt-Winters)',
                type: 'line',
                smooth: true,
                data: forecastSeriesData,
                symbol: 'diamond',
                symbolSize: 7,
                itemStyle: { color: '#30D158' },
                lineStyle: { width: 3, type: 'dashed', color: '#30D158' }
            },
            {
                name: '置信区间上限',
                type: 'line',
                data: upperData,
                lineStyle: { opacity: 0 },
                stack: 'confidence-band',
                symbol: 'none'
            },
            {
                name: '置信区间带 (95%)',
                type: 'line',
                data: lowerData,
                lineStyle: { opacity: 0 },
                areaStyle: {
                    color: 'rgba(48, 209, 88, 0.15)'
                },
                stack: 'confidence-band',
                symbol: 'none'
            }
        ]
    };
    chartInstance.setOption(option);
}
// =========================================================================
// Dramas Management
// =========================================================================
async function loadDramas() {
    const res = await adminApi.getDramas({ per_page: 100 });
    const data = res?.data || res;
    if (data?.items) {
        dramasList.value = data.items;
    }
}
function filterDramas() { }
async function toggleDramaStatus(drama) {
    const target = drama.status === 'PUBLISHED' ? 'HIDDEN' : 'PUBLISHED';
    try {
        await adminApi.toggleDramaStatus(drama.id, target);
        drama.status = target;
        ElMessage.success(`短剧《${drama.title}》已成功${target === 'PUBLISHED' ? '上架发布' : '屏蔽下线'}`);
    }
    catch (err) {
        ElMessage.error(err.message || '修改状态失败');
    }
}
// =========================================================================
// Drama Cover & Metadata Governance (Feature 23)
// =========================================================================
function openEditCoverModal(drama) {
    editingDrama.value = drama;
    editingCoverUrl.value = drama.effective_cover || drama.custom_cover_url || drama.cover_url || '';
    coverImgError.value = false;
    editingDramaPosters.value = [...(drama.extra_images || [])];
    if (editingCoverUrl.value && !editingDramaPosters.value.includes(editingCoverUrl.value)) {
        editingDramaPosters.value.unshift(editingCoverUrl.value);
    }
    editingDramaMeta.value = {
        id: drama.id,
        title: drama.title,
        category: drama.category || '微短剧',
        summary: drama.summary || '',
        status: drama.status || 'PUBLISHED'
    };
    showEditCoverDialog.value = true;
}
function triggerUploadImage() {
    imageUploadInputRef.value?.click();
}
async function handleImageFileSelected(e) {
    const target = e.target;
    const file = target.files?.[0];
    if (file) {
        await doUploadImageFile(file);
    }
    target.value = '';
}
async function handleCoverDrop(e) {
    isCoverDragOver.value = false;
    const file = e.dataTransfer?.files?.[0];
    if (file) {
        await doUploadImageFile(file);
    }
}
async function doUploadImageFile(file) {
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
        ElMessage.error('仅支持 JPG, PNG, WEBP 格式图片');
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        ElMessage.error('图片体积不能超过 10MB');
        return;
    }
    uploadingImage.value = true;
    try {
        const res = await adminApi.uploadImage(file);
        const url = res?.data?.url || res?.url;
        if (url) {
            editingCoverUrl.value = url;
            coverImgError.value = false;
            if (!editingDramaPosters.value.includes(url)) {
                editingDramaPosters.value.push(url);
            }
            ElMessage.success('图片安全上传成功！');
        }
    }
    catch (err) {
        ElMessage.error(err.message || '图片上传失败');
    }
    finally {
        uploadingImage.value = false;
    }
}
function setAsMainCover(imgUrl) {
    editingCoverUrl.value = imgUrl;
    coverImgError.value = false;
    ElMessage.success('已设为主封面');
}
function removePoster(idx) {
    editingDramaPosters.value.splice(idx, 1);
}
async function confirmUpdateCover() {
    if (!editingDrama.value)
        return;
    try {
        await adminApi.updateDrama(editingDrama.value.id, {
            title: editingDramaMeta.value.title,
            category: editingDramaMeta.value.category,
            summary: editingDramaMeta.value.summary,
            status: editingDramaMeta.value.status
        });
        if (editingCoverUrl.value.trim()) {
            await adminApi.updateDramaCover(editingDrama.value.id, editingCoverUrl.value.trim());
            editingDrama.value.custom_cover_url = editingCoverUrl.value.trim();
            editingDrama.value.effective_cover = editingCoverUrl.value.trim();
        }
        await adminApi.updateDramaPosters(editingDrama.value.id, editingDramaPosters.value);
        editingDrama.value.extra_images = [...editingDramaPosters.value];
        showEditCoverDialog.value = false;
        ElMessage.success('短剧信息与封面画报已成功保存！');
        await loadDramas();
        await loadDramaOptions();
    }
    catch (err) {
        ElMessage.error(err.message || '保存短剧封面与元数据失败');
    }
}
function openPosterCarousel(drama) {
    activeDramaForPosters.value = drama;
    showPostersCarouselDialog.value = true;
}
async function handleDeleteDrama(drama) {
    try {
        await ElMessageBox.confirm(`确定要从平台物理删除短剧《${drama.title}》及其全部分集记录吗？此操作无法撤销。`, '危险删除提示', { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' });
        await adminApi.deleteDrama(drama.id);
        dramasList.value = dramasList.value.filter(d => d.id !== drama.id);
        ElMessage.success(`短剧《${drama.title}》已彻底移除`);
    }
    catch (e) {
        // cancelled
    }
}
// =========================================================================
// Sync Pan
// =========================================================================
function openSyncDialog() {
    currentTab.value = 'sync';
}
async function executeSync() {
    isSyncing.value = true;
    syncResult.value = null;
    try {
        const res = await adminApi.syncPanAll(syncMode.value);
        const data = res?.data || res;
        syncResult.value = data;
        ElMessage.success(`网盘同步成功完成！共映射 ${data.total_synced_dramas} 部短剧，新增 ${data.new_episodes_added} 集`);
        await loadDramas();
    }
    catch (err) {
        ElMessage.error(err.message || '网盘同步失败，请检查 OpenList 网关是否在线');
    }
    finally {
        isSyncing.value = false;
    }
}
// =========================================================================
// Carousels (Feature 24: 16:9 WYSIWYG Live Preview)
// =========================================================================
async function loadDramaOptions() {
    try {
        const res = await adminApi.getDramaOptions();
        const data = res?.data || res;
        if (Array.isArray(data)) {
            dramaOptionsList.value = data;
            if (data.length > 0 && !selectedCarouselDramaId.value) {
                selectedCarouselDramaId.value = data[0].id;
            }
        }
    }
    catch (e) {
        console.error('Failed to load drama options:', e);
    }
}
function handleQuickSelectDrama() {
    workbenchImgError.value = false;
}
function applyWorkbenchToModal() {
    const d = selectedWorkbenchDrama.value;
    if (!d)
        return;
    isEditingCarousel.value = false;
    selectedCarouselDramaModalId.value = d.id;
    carouselForm.value = {
        title: d.title,
        subtitle: (d.category || '短剧') + ' · 独播首发',
        tag: '今日焦点推荐',
        cover_url: d.cover_url,
        video_id: d.id,
        sort_order: carouselsList.value.length + 1,
        is_active: true
    };
    showCarouselDialog.value = true;
}
function handleModalSelectDrama() {
    const d = dramaOptionsList.value.find(item => item.id === selectedCarouselDramaModalId.value);
    if (d) {
        carouselForm.value.video_id = d.id;
        carouselForm.value.title = d.title;
        carouselForm.value.cover_url = d.cover_url;
        carouselForm.value.subtitle = (d.category || '短剧') + ' · 独播首发';
    }
}
async function loadCarousels() {
    const res = await adminApi.getCarousels();
    const data = res?.data || res;
    if (Array.isArray(data)) {
        carouselsList.value = data;
    }
}
function openCreateCarouselModal() {
    isEditingCarousel.value = false;
    selectedCarouselDramaModalId.value = '';
    carouselForm.value = {
        title: '',
        subtitle: '',
        tag: '今日焦点推荐',
        cover_url: '',
        video_id: '',
        sort_order: carouselsList.value.length + 1,
        is_active: true
    };
    showCarouselDialog.value = true;
}
function openEditCarouselModal(item) {
    isEditingCarousel.value = true;
    selectedCarouselDramaModalId.value = item.video_id || '';
    carouselForm.value = { ...item };
    showCarouselDialog.value = true;
}
async function saveCarousel() {
    if (!carouselForm.value.title || !carouselForm.value.cover_url) {
        ElMessage.warning('请填写标题文案与海报图片地址');
        return;
    }
    try {
        if (isEditingCarousel.value && carouselForm.value.id) {
            await adminApi.updateCarousel(carouselForm.value.id, carouselForm.value);
            ElMessage.success('轮播焦点更新成功');
        }
        else {
            await adminApi.createCarousel(carouselForm.value);
            ElMessage.success('新增轮播焦点成功');
        }
        showCarouselDialog.value = false;
        await loadCarousels();
    }
    catch (err) {
        ElMessage.error(err.message || '保存轮播图失败');
    }
}
async function handleToggleCarouselActive(item) {
    try {
        await adminApi.updateCarousel(item.id, { is_active: item.is_active });
        ElMessage.success(`轮播焦点已${item.is_active ? '启用上线' : '暂停下线'}`);
    }
    catch (err) {
        item.is_active = !item.is_active;
        ElMessage.error(err.message || '修改状态失败');
    }
}
async function handleDeleteCarousel(item) {
    try {
        await ElMessageBox.confirm(`确定删除轮播条目《${item.title}》吗？`, '删除提示');
        await adminApi.deleteCarousel(item.id);
        carouselsList.value = carouselsList.value.filter(c => c.id !== item.id);
        ElMessage.success('轮播条目已删除');
    }
    catch (e) { }
}
// =========================================================================
// Users Management & Full CRUD (Feature 22)
// =========================================================================
async function loadUsers() {
    try {
        const params = {
            page: userPage.value,
            per_page: userPageSize.value
        };
        if (userSearchKeyword.value.trim())
            params.search = userSearchKeyword.value.trim();
        if (userFilterRole.value && userFilterRole.value !== 'ALL')
            params.role = userFilterRole.value;
        const res = await adminApi.getUsers(params);
        const data = res?.data || res;
        if (data?.items) {
            let items = data.items;
            if (userFilterStatus.value && userFilterStatus.value !== 'ALL') {
                items = items.filter((u) => u.status === userFilterStatus.value);
            }
            usersList.value = items;
            userTotalCount.value = data.total || items.length;
        }
    }
    catch (e) {
        console.error('Failed to load users:', e);
    }
}
function openAddUserModal() {
    addUserForm.value = {
        username: '',
        password: '',
        nickname: '',
        role: 'USER',
        coins: 50,
        vip_days: 0
    };
    showAddUserDialog.value = true;
}
async function confirmAddUser() {
    if (!addUserForm.value.username.trim() || !addUserForm.value.password.trim()) {
        ElMessage.warning('用户名与密码为必填项');
        return;
    }
    try {
        await adminApi.createUser({
            username: addUserForm.value.username.trim(),
            password: addUserForm.value.password.trim(),
            nickname: addUserForm.value.nickname.trim() || undefined,
            role: addUserForm.value.role,
            coins: addUserForm.value.coins ?? 50,
            vip_days: addUserForm.value.vip_days ?? 0
        });
        ElMessage.success(`用户 @${addUserForm.value.username} 创建成功！`);
        showAddUserDialog.value = false;
        await loadUsers();
    }
    catch (err) {
        ElMessage.error(err.message || '创建用户失败');
    }
}
function openEditUserModal(user) {
    selectedUserForEdit.value = user;
    editUserForm.value = {
        id: user.id,
        username: user.username,
        nickname: user.nickname || '',
        password: '',
        role: user.role,
        status: user.status,
        coins_adjustment: 0,
        vip_days: 0
    };
    showEditUserDialog.value = true;
}
async function confirmEditUser() {
    if (!selectedUserForEdit.value)
        return;
    try {
        const payload = {
            nickname: editUserForm.value.nickname.trim(),
            role: editUserForm.value.role,
            status: editUserForm.value.status
        };
        if (editUserForm.value.password.trim()) {
            payload.password = editUserForm.value.password.trim();
        }
        if (editUserForm.value.coins_adjustment !== 0) {
            payload.coins_adjustment = editUserForm.value.coins_adjustment;
        }
        if (editUserForm.value.vip_days !== 0) {
            payload.vip_days = editUserForm.value.vip_days;
        }
        await adminApi.updateUser(selectedUserForEdit.value.id, payload);
        ElMessage.success(`用户 @${selectedUserForEdit.value.username} 资料更新成功`);
        showEditUserDialog.value = false;
        await loadUsers();
    }
    catch (err) {
        ElMessage.error(err.message || '更新用户失败');
    }
}
async function handleDeleteUser(user) {
    try {
        await ElMessageBox.confirm(`确定要从平台物理删除用户 @${user.username} 吗？此操作将级联清理其所有互动资产，无法撤销。`, '危险删除提示', { confirmButtonText: '确认物理删除', cancelButtonText: '取消', type: 'warning' });
        await adminApi.deleteUser(user.id);
        ElMessage.success(`用户 @${user.username} 已被物理清除`);
        await loadUsers();
    }
    catch (e) {
        // cancelled
    }
}
function openRoleModal(user) {
    selectedUserForRole.value = user;
    selectedRole.value = user.role;
    showRoleDialog.value = true;
}
async function confirmChangeRole() {
    if (!selectedUserForRole.value)
        return;
    try {
        await adminApi.updateUserRole(selectedUserForRole.value.id, selectedRole.value);
        selectedUserForRole.value.role = selectedRole.value;
        showRoleDialog.value = false;
        ElMessage.success(`用户 ${selectedUserForRole.value.username} 角色已调整为 ${getRoleLabel(selectedRole.value)}`);
    }
    catch (err) {
        ElMessage.error(err.message || '调权失败');
    }
}
async function toggleUserStatus(user) {
    const target = user.status === 'ACTIVE' ? 'BANNED' : 'ACTIVE';
    try {
        await adminApi.updateUserStatus(user.id, target);
        user.status = target;
        ElMessage.success(`用户 ${user.username} 账号已${target === 'ACTIVE' ? '解除封禁' : '封禁阻断'}`);
    }
    catch (err) {
        ElMessage.error(err.message || '修改用户状态失败');
    }
}
// =========================================================================
// Applications (Dual Track)
// =========================================================================
async function loadApplications() {
    const res = await adminApi.getApplications();
    const data = res?.data || res;
    if (data) {
        pendingCreators.value = (data.creators || []).filter((c) => c.status === 'PENDING');
        pendingReviewers.value = (data.reviewers || []).filter((r) => r.status === 'PENDING');
    }
}
async function handleApproveApplication(app) {
    try {
        if (applicationSubTab.value === 'creators') {
            await adminApi.reviewCreator(app.user_id, 'APPROVE');
            pendingCreators.value = pendingCreators.value.filter(c => c.user_id !== app.user_id);
            ElMessage.success(`创作者 ${app.username} 入驻申请已批准，创作者空间与发布特权已下发！`);
        }
        else {
            await adminApi.reviewReviewer(app.user_id, 'APPROVE');
            pendingReviewers.value = pendingReviewers.value.filter(r => r.user_id !== app.user_id);
            ElMessage.success(`审核员 ${app.username} 资质已批准，机审中台巡检特权已下发！`);
        }
    }
    catch (err) {
        ElMessage.error(err.message || '审批操作失败');
    }
}
async function handleRejectApplication(app) {
    try {
        if (applicationSubTab.value === 'creators') {
            await adminApi.reviewCreator(app.user_id, 'REJECT');
            pendingCreators.value = pendingCreators.value.filter(c => c.user_id !== app.user_id);
        }
        else {
            await adminApi.reviewReviewer(app.user_id, 'REJECT');
            pendingReviewers.value = pendingReviewers.value.filter(r => r.user_id !== app.user_id);
        }
        ElMessage.info('申请已驳回');
    }
    catch (err) {
        ElMessage.error(err.message || '操作失败');
    }
}
// =========================================================================
// Content Moderation (工单流、敏感词库、弹幕与评论)
// =========================================================================
function switchContentSubTab(tab) {
    contentSubTab.value = tab;
    if (tab === 'queue') {
        loadReviewQueue();
    }
    else if (tab === 'lexicon') {
        loadSensitiveWords();
    }
}
async function loadContents() {
    try {
        const [dmRes, cmRes, qRes, swRes] = await Promise.all([
            adminApi.getDanmakus({ per_page: 50 }),
            adminApi.getComments({ per_page: 50 }),
            adminApi.getReviewQueue('PENDING'),
            adminApi.getSensitiveWords({ per_page: 100 })
        ]);
        danmakusList.value = dmRes?.data?.items || dmRes?.items || [];
        commentsList.value = cmRes?.data?.items || cmRes?.items || [];
        reviewQueueList.value = qRes?.data || qRes || [];
        const swData = swRes?.data || swRes || {};
        sensitiveWordsList.value = swData?.items || [];
        sensitiveWordsTotal.value = swData?.total || 0;
    }
    catch (e) {
        console.error('Error loading content moderation records:', e);
    }
}
async function loadReviewQueue() {
    try {
        const res = await adminApi.getReviewQueue('PENDING');
        reviewQueueList.value = res?.data || res || [];
    }
    catch (e) {
        console.error('Failed to load review queue:', e);
    }
}
async function handleReviewDecision(reviewId, decision) {
    try {
        await adminApi.makeReviewDecision(reviewId, decision);
        reviewQueueList.value = reviewQueueList.value.filter(r => r.id !== reviewId);
        ElMessage.success(`风控裁决已生效：${decision === 'APPROVED' ? '放行通过' : '违规驳回并清理'}`);
    }
    catch (err) {
        ElMessage.error(err.message || '裁决操作失败');
    }
}
async function loadSensitiveWords() {
    try {
        const res = await adminApi.getSensitiveWords({
            query: sensitiveWordSearch.value.trim() || undefined,
            category: sensitiveWordCategory.value !== 'ALL' ? sensitiveWordCategory.value : undefined,
            level: sensitiveWordLevel.value !== 'ALL' ? sensitiveWordLevel.value : undefined,
            per_page: 100
        });
        const data = res?.data || res;
        sensitiveWordsList.value = data?.items || [];
        sensitiveWordsTotal.value = data?.total || 0;
    }
    catch (e) {
        console.error('Failed to load sensitive words:', e);
    }
}
function openAddWordModal() {
    newWordForm.value = { word: '', category: '违禁', level: 'HIGH' };
    showAddWordDialog.value = true;
}
async function confirmAddSensitiveWord() {
    if (!newWordForm.value.word.trim())
        return;
    try {
        await adminApi.addSensitiveWord({
            word: newWordForm.value.word.trim(),
            category: newWordForm.value.category,
            level: newWordForm.value.level
        });
        showAddWordDialog.value = false;
        ElMessage.success(`敏感词 [${newWordForm.value.word.trim()}] 录入成功，DFA 树已即刻热重载！`);
        await loadSensitiveWords();
    }
    catch (err) {
        ElMessage.error(err.message || '录入敏感词失败');
    }
}
async function handleDeleteSensitiveWord(item) {
    try {
        await adminApi.deleteSensitiveWord(item.id);
        sensitiveWordsList.value = sensitiveWordsList.value.filter(w => w.id !== item.id);
        sensitiveWordsTotal.value = Math.max(0, sensitiveWordsTotal.value - 1);
        ElMessage.success(`已删除敏感词 [${item.word}]，DFA 树已更新`);
    }
    catch (err) {
        ElMessage.error(err.message || '删除敏感词失败');
    }
}
async function runDfaTest() {
    if (!dfaTestText.value.trim())
        return;
    dfaTesting.value = true;
    try {
        const res = await adminApi.testSensitiveWords(dfaTestText.value.trim());
        dfaTestResult.value = res?.data || res;
    }
    catch (err) {
        ElMessage.error(err.message || '检测失败');
    }
    finally {
        dfaTesting.value = false;
    }
}
async function fetchDanmakus() {
    try {
        const dmRes = await adminApi.getDanmakus({
            per_page: 50,
            keyword: danmakuSearchQuery.value.trim() || undefined
        });
        danmakusList.value = dmRes?.data?.items || dmRes?.items || [];
    }
    catch (e) {
        ElMessage.error(e.message || '查询弹幕列表失败');
    }
}
function toggleSelectAllDanmakus(e) {
    const target = e.target;
    if (target.checked) {
        selectedDanmakuIds.value = danmakusList.value.map(d => d.id);
    }
    else {
        selectedDanmakuIds.value = [];
    }
}
async function handleBatchDeleteDanmakus() {
    if (selectedDanmakuIds.value.length === 0) {
        ElMessage.warning('请先勾选需要下架的弹幕');
        return;
    }
    try {
        const res = await adminApi.batchDeleteDanmakus(selectedDanmakuIds.value);
        ElMessage.success(res?.message || `已成功批量下架 ${selectedDanmakuIds.value.length} 条违规弹幕`);
        danmakusList.value = danmakusList.value.filter(d => !selectedDanmakuIds.value.includes(d.id));
        selectedDanmakuIds.value = [];
    }
    catch (err) {
        ElMessage.error(err.message || '批量删除失败');
    }
}
async function handleDeleteDanmaku(id) {
    try {
        await adminApi.deleteDanmaku(id);
        danmakusList.value = danmakusList.value.filter(d => d.id !== id);
        selectedDanmakuIds.value = selectedDanmakuIds.value.filter(item => item !== id);
        ElMessage.success('违规弹幕已移除并清退');
    }
    catch (err) {
        ElMessage.error(err.message || '删除失败');
    }
}
async function handleDeleteComment(id) {
    try {
        await adminApi.deleteComment(id);
        commentsList.value = commentsList.value.filter(c => c.id !== id);
        ElMessage.success('违规评论已清理');
    }
    catch (err) {
        ElMessage.error(err.message || '删除失败');
    }
}
// =========================================================================
// Engine Config
// =========================================================================
function saveEngineConfig() {
    if (!engineForm.value.modelName.trim()) {
        ElMessage.warning('请输入有效的模型名称');
        return;
    }
    localStorage.setItem('cinema_active_model', engineForm.value.modelName.trim());
    localStorage.setItem('cinema_temperature', engineForm.value.temperature.toString());
    ElMessage.success(`模型引擎已配置为 [${engineForm.value.modelName.trim()}]，伴读参数已同步！`);
}
function getRoleLabel(role) {
    const map = {
        USER: '普通用户',
        CREATOR: '创作者',
        REVIEWER: '审核员',
        ADMIN: '超级管理员'
    };
    return map[role] || role;
}
function formatNumber(num) {
    if (!num)
        return '0';
    return num >= 10000 ? (num / 10000).toFixed(1) + 'w' : num.toLocaleString();
}
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['admin-sidebar']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-pin-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-tab-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-tab-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-tab-item']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['dot']} */ ;
/** @type {__VLS_StyleScopedClasses['dot']} */ ;
/** @type {__VLS_StyleScopedClasses['dot']} */ ;
/** @type {__VLS_StyleScopedClasses['rank-index']} */ ;
/** @type {__VLS_StyleScopedClasses['rank-index']} */ ;
/** @type {__VLS_StyleScopedClasses['rank-index']} */ ;
/** @type {__VLS_StyleScopedClasses['table-search-input']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table']} */ ;
/** @type {__VLS_StyleScopedClasses['status-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['status-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['status-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-warn']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-danger']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-success']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-radio-box']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-radio-box']} */ ;
/** @type {__VLS_StyleScopedClasses['report-stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['role-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['role-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['role-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['role-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['priv-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['creator']} */ ;
/** @type {__VLS_StyleScopedClasses['priv-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['reviewer']} */ ;
/** @type {__VLS_StyleScopedClasses['priv-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['subtab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['cover-preview-box']} */ ;
/** @type {__VLS_StyleScopedClasses['cover-preview-box']} */ ;
/** @type {__VLS_StyleScopedClasses['placeholder-text']} */ ;
/** @type {__VLS_StyleScopedClasses['placeholder-text']} */ ;
/** @type {__VLS_StyleScopedClasses['cover-preview-box']} */ ;
/** @type {__VLS_StyleScopedClasses['cover-hover-prompt']} */ ;
/** @type {__VLS_StyleScopedClasses['poster-shelf-card']} */ ;
/** @type {__VLS_StyleScopedClasses['shelf-btn-set-main']} */ ;
/** @type {__VLS_StyleScopedClasses['shelf-btn-del']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['sync-dashboard-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-sidebar']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-main-stage']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['lexicon-composite-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['lexicon-filters-row']} */ ;
/** @type {__VLS_StyleScopedClasses['sandbox-result-box']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "admin-page-root" },
    id: "admin-console-page",
});
/** @type {[typeof AdminHeader, ]} */ ;
// @ts-ignore
const __VLS_0 = __VLS_asFunctionalComponent(AdminHeader, new AdminHeader({
    ...{ 'onSelectTab': {} },
    mode: "admin",
    activeTab: (__VLS_ctx.currentTab),
}));
const __VLS_1 = __VLS_0({
    ...{ 'onSelectTab': {} },
    mode: "admin",
    activeTab: (__VLS_ctx.currentTab),
}, ...__VLS_functionalComponentArgsRest(__VLS_0));
let __VLS_3;
let __VLS_4;
let __VLS_5;
const __VLS_6 = {
    onSelectTab: (__VLS_ctx.selectTab)
};
var __VLS_2;
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ onChange: (__VLS_ctx.handleImageFileSelected) },
    type: "file",
    id: "input-upload-image",
    ref: "imageUploadInputRef",
    accept: "image/jpeg,image/png,image/webp",
    ...{ style: {} },
});
/** @type {typeof __VLS_ctx.imageUploadInputRef} */ ;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "admin-layout-wrapper" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "admin-ambient-bg" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "admin-orb orb-1" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "admin-orb orb-2" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.aside, __VLS_intrinsicElements.aside)({
    ...{ onMouseenter: (__VLS_ctx.onSidebarMouseEnter) },
    ...{ onMouseleave: (__VLS_ctx.onSidebarMouseLeave) },
    ...{ class: "admin-sidebar" },
    ...{ class: ({ 'is-collapsed': !__VLS_ctx.isSidebarExpanded, 'is-pinned': __VLS_ctx.isSidebarPinned }) },
    id: "admin-collapsible-sidebar",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "sidebar-header" },
});
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "sidebar-brand" },
    });
    const __VLS_7 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_8 = __VLS_asFunctionalComponent(__VLS_7, new __VLS_7({
        ...{ class: "brand-icon" },
    }));
    const __VLS_9 = __VLS_8({
        ...{ class: "brand-icon" },
    }, ...__VLS_functionalComponentArgsRest(__VLS_8));
    __VLS_10.slots.default;
    const __VLS_11 = {}.TrendCharts;
    /** @type {[typeof __VLS_components.TrendCharts, ]} */ ;
    // @ts-ignore
    const __VLS_12 = __VLS_asFunctionalComponent(__VLS_11, new __VLS_11({}));
    const __VLS_13 = __VLS_12({}, ...__VLS_functionalComponentArgsRest(__VLS_12));
    var __VLS_10;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "brand-text" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "brand-name" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "brand-sub" },
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "sidebar-brand-collapsed" },
    });
    const __VLS_15 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_16 = __VLS_asFunctionalComponent(__VLS_15, new __VLS_15({
        ...{ class: "brand-icon" },
    }));
    const __VLS_17 = __VLS_16({
        ...{ class: "brand-icon" },
    }, ...__VLS_functionalComponentArgsRest(__VLS_16));
    __VLS_18.slots.default;
    const __VLS_19 = {}.TrendCharts;
    /** @type {[typeof __VLS_components.TrendCharts, ]} */ ;
    // @ts-ignore
    const __VLS_20 = __VLS_asFunctionalComponent(__VLS_19, new __VLS_19({}));
    const __VLS_21 = __VLS_20({}, ...__VLS_functionalComponentArgsRest(__VLS_20));
    var __VLS_18;
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.toggleSidebarPin) },
    type: "button",
    ...{ class: "sidebar-pin-btn" },
    title: (__VLS_ctx.isSidebarPinned ? '解除固定 (鼠标悬停展开)' : '锁定固定侧边栏'),
    id: "btn-toggle-sidebar-pin",
});
const __VLS_23 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_24 = __VLS_asFunctionalComponent(__VLS_23, new __VLS_23({
    size: (16),
}));
const __VLS_25 = __VLS_24({
    size: (16),
}, ...__VLS_functionalComponentArgsRest(__VLS_24));
__VLS_26.slots.default;
if (__VLS_ctx.isSidebarPinned) {
    const __VLS_27 = {}.Fold;
    /** @type {[typeof __VLS_components.Fold, ]} */ ;
    // @ts-ignore
    const __VLS_28 = __VLS_asFunctionalComponent(__VLS_27, new __VLS_27({}));
    const __VLS_29 = __VLS_28({}, ...__VLS_functionalComponentArgsRest(__VLS_28));
}
else {
    const __VLS_31 = {}.Expand;
    /** @type {[typeof __VLS_components.Expand, ]} */ ;
    // @ts-ignore
    const __VLS_32 = __VLS_asFunctionalComponent(__VLS_31, new __VLS_31({}));
    const __VLS_33 = __VLS_32({}, ...__VLS_functionalComponentArgsRest(__VLS_32));
}
var __VLS_26;
__VLS_asFunctionalElement(__VLS_intrinsicElements.nav, __VLS_intrinsicElements.nav)({
    ...{ class: "sidebar-nav-scroll" },
});
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "nav-group-title" },
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "nav-divider" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.selectTab('bi');
        } },
    ...{ class: "nav-tab-item" },
    ...{ class: ({ active: __VLS_ctx.currentTab === 'bi' }) },
    id: "admin-tab-bi",
    title: "BI 全景驾驶舱与时序预测",
});
const __VLS_35 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_36 = __VLS_asFunctionalComponent(__VLS_35, new __VLS_35({
    ...{ class: "nav-icon" },
}));
const __VLS_37 = __VLS_36({
    ...{ class: "nav-icon" },
}, ...__VLS_functionalComponentArgsRest(__VLS_36));
__VLS_38.slots.default;
const __VLS_39 = {}.DataLine;
/** @type {[typeof __VLS_components.DataLine, ]} */ ;
// @ts-ignore
const __VLS_40 = __VLS_asFunctionalComponent(__VLS_39, new __VLS_39({}));
const __VLS_41 = __VLS_40({}, ...__VLS_functionalComponentArgsRest(__VLS_40));
var __VLS_38;
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "nav-label" },
    });
}
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "nav-group-title" },
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "nav-divider" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.selectTab('dramas');
        } },
    ...{ class: "nav-tab-item" },
    ...{ class: ({ active: __VLS_ctx.currentTab === 'dramas' }) },
    id: "admin-tab-dramas",
    title: "短剧内容与封面管理",
});
const __VLS_43 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_44 = __VLS_asFunctionalComponent(__VLS_43, new __VLS_43({
    ...{ class: "nav-icon" },
}));
const __VLS_45 = __VLS_44({
    ...{ class: "nav-icon" },
}, ...__VLS_functionalComponentArgsRest(__VLS_44));
__VLS_46.slots.default;
const __VLS_47 = {}.Film;
/** @type {[typeof __VLS_components.Film, ]} */ ;
// @ts-ignore
const __VLS_48 = __VLS_asFunctionalComponent(__VLS_47, new __VLS_47({}));
const __VLS_49 = __VLS_48({}, ...__VLS_functionalComponentArgsRest(__VLS_48));
var __VLS_46;
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "nav-label" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.selectTab('sync');
        } },
    ...{ class: "nav-tab-item" },
    ...{ class: ({ active: __VLS_ctx.currentTab === 'sync' }) },
    id: "admin-tab-sync",
    title: "夸克网盘增量/全量同步",
});
const __VLS_51 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_52 = __VLS_asFunctionalComponent(__VLS_51, new __VLS_51({
    ...{ class: "nav-icon" },
}));
const __VLS_53 = __VLS_52({
    ...{ class: "nav-icon" },
}, ...__VLS_functionalComponentArgsRest(__VLS_52));
__VLS_54.slots.default;
const __VLS_55 = {}.Refresh;
/** @type {[typeof __VLS_components.Refresh, ]} */ ;
// @ts-ignore
const __VLS_56 = __VLS_asFunctionalComponent(__VLS_55, new __VLS_55({}));
const __VLS_57 = __VLS_56({}, ...__VLS_functionalComponentArgsRest(__VLS_56));
var __VLS_54;
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "nav-label" },
    });
}
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "nav-group-title" },
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "nav-divider" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.selectTab('carousels');
        } },
    ...{ class: "nav-tab-item" },
    ...{ class: ({ active: __VLS_ctx.currentTab === 'carousels' }) },
    id: "admin-tab-carousels",
    title: "首页 5 秒焦点轮播管理",
});
const __VLS_59 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_60 = __VLS_asFunctionalComponent(__VLS_59, new __VLS_59({
    ...{ class: "nav-icon" },
}));
const __VLS_61 = __VLS_60({
    ...{ class: "nav-icon" },
}, ...__VLS_functionalComponentArgsRest(__VLS_60));
__VLS_62.slots.default;
const __VLS_63 = {}.Picture;
/** @type {[typeof __VLS_components.Picture, ]} */ ;
// @ts-ignore
const __VLS_64 = __VLS_asFunctionalComponent(__VLS_63, new __VLS_63({}));
const __VLS_65 = __VLS_64({}, ...__VLS_functionalComponentArgsRest(__VLS_64));
var __VLS_62;
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "nav-label" },
    });
}
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "nav-group-title" },
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "nav-divider" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.selectTab('users');
        } },
    ...{ class: "nav-tab-item" },
    ...{ class: ({ active: __VLS_ctx.currentTab === 'users' }) },
    id: "admin-tab-users",
    title: "用户账号与 RBAC 权限",
});
const __VLS_67 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_68 = __VLS_asFunctionalComponent(__VLS_67, new __VLS_67({
    ...{ class: "nav-icon" },
}));
const __VLS_69 = __VLS_68({
    ...{ class: "nav-icon" },
}, ...__VLS_functionalComponentArgsRest(__VLS_68));
__VLS_70.slots.default;
const __VLS_71 = {}.User;
/** @type {[typeof __VLS_components.User, ]} */ ;
// @ts-ignore
const __VLS_72 = __VLS_asFunctionalComponent(__VLS_71, new __VLS_71({}));
const __VLS_73 = __VLS_72({}, ...__VLS_functionalComponentArgsRest(__VLS_72));
var __VLS_70;
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "nav-label" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.selectTab('applications');
        } },
    ...{ class: "nav-tab-item" },
    ...{ class: ({ active: __VLS_ctx.currentTab === 'applications' }) },
    id: "admin-tab-applications",
    title: "创作者/审核员入驻审批",
});
const __VLS_75 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_76 = __VLS_asFunctionalComponent(__VLS_75, new __VLS_75({
    ...{ class: "nav-icon" },
}));
const __VLS_77 = __VLS_76({
    ...{ class: "nav-icon" },
}, ...__VLS_functionalComponentArgsRest(__VLS_76));
__VLS_78.slots.default;
const __VLS_79 = {}.DocumentChecked;
/** @type {[typeof __VLS_components.DocumentChecked, ]} */ ;
// @ts-ignore
const __VLS_80 = __VLS_asFunctionalComponent(__VLS_79, new __VLS_79({}));
const __VLS_81 = __VLS_80({}, ...__VLS_functionalComponentArgsRest(__VLS_80));
var __VLS_78;
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "nav-label" },
    });
}
if (__VLS_ctx.pendingCount > 0 && __VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "nav-badge" },
    });
    (__VLS_ctx.pendingCount);
}
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "nav-group-title" },
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "nav-divider" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.selectTab('contents');
        } },
    ...{ class: "nav-tab-item" },
    ...{ class: ({ active: __VLS_ctx.currentTab === 'contents' }) },
    id: "admin-tab-contents",
    title: "弹幕与评论合规审查",
});
const __VLS_83 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_84 = __VLS_asFunctionalComponent(__VLS_83, new __VLS_83({
    ...{ class: "nav-icon" },
}));
const __VLS_85 = __VLS_84({
    ...{ class: "nav-icon" },
}, ...__VLS_functionalComponentArgsRest(__VLS_84));
__VLS_86.slots.default;
const __VLS_87 = {}.ChatLineSquare;
/** @type {[typeof __VLS_components.ChatLineSquare, ]} */ ;
// @ts-ignore
const __VLS_88 = __VLS_asFunctionalComponent(__VLS_87, new __VLS_87({}));
const __VLS_89 = __VLS_88({}, ...__VLS_functionalComponentArgsRest(__VLS_88));
var __VLS_86;
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "nav-label" },
    });
}
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "nav-group-title" },
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "nav-divider" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.selectTab('engine');
        } },
    ...{ class: "nav-tab-item" },
    ...{ class: ({ active: __VLS_ctx.currentTab === 'engine' }) },
    id: "admin-tab-engine",
    title: "本地/云端模型引擎与 RAG 参数",
});
const __VLS_91 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_92 = __VLS_asFunctionalComponent(__VLS_91, new __VLS_91({
    ...{ class: "nav-icon" },
}));
const __VLS_93 = __VLS_92({
    ...{ class: "nav-icon" },
}, ...__VLS_functionalComponentArgsRest(__VLS_92));
__VLS_94.slots.default;
const __VLS_95 = {}.Setting;
/** @type {[typeof __VLS_components.Setting, ]} */ ;
// @ts-ignore
const __VLS_96 = __VLS_asFunctionalComponent(__VLS_95, new __VLS_95({}));
const __VLS_97 = __VLS_96({}, ...__VLS_functionalComponentArgsRest(__VLS_96));
var __VLS_94;
if (__VLS_ctx.isSidebarExpanded) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "nav-label" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.main, __VLS_intrinsicElements.main)({
    ...{ class: "admin-main-stage" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.header, __VLS_intrinsicElements.header)({
    ...{ class: "stage-top-bar" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "bar-left" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "bar-breadcrumb" },
});
(__VLS_ctx.currentTabTitle);
__VLS_asFunctionalElement(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({
    ...{ class: "bar-headline" },
});
(__VLS_ctx.currentTabTitle);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "bar-right" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.refreshCurrentTab) },
    type: "button",
    ...{ class: "apple-btn-secondary" },
    id: "btn-admin-refresh",
    disabled: (__VLS_ctx.loading),
});
const __VLS_99 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_100 = __VLS_asFunctionalComponent(__VLS_99, new __VLS_99({
    ...{ class: ({ 'is-loading': __VLS_ctx.loading }) },
}));
const __VLS_101 = __VLS_100({
    ...{ class: ({ 'is-loading': __VLS_ctx.loading }) },
}, ...__VLS_functionalComponentArgsRest(__VLS_100));
__VLS_102.slots.default;
const __VLS_103 = {}.Refresh;
/** @type {[typeof __VLS_components.Refresh, ]} */ ;
// @ts-ignore
const __VLS_104 = __VLS_asFunctionalComponent(__VLS_103, new __VLS_103({}));
const __VLS_105 = __VLS_104({}, ...__VLS_functionalComponentArgsRest(__VLS_104));
var __VLS_102;
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.openSyncDialog) },
    type: "button",
    ...{ class: "apple-btn-primary" },
    id: "btn-quick-sync-pan",
});
const __VLS_107 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_108 = __VLS_asFunctionalComponent(__VLS_107, new __VLS_107({}));
const __VLS_109 = __VLS_108({}, ...__VLS_functionalComponentArgsRest(__VLS_108));
__VLS_110.slots.default;
const __VLS_111 = {}.Refresh;
/** @type {[typeof __VLS_components.Refresh, ]} */ ;
// @ts-ignore
const __VLS_112 = __VLS_asFunctionalComponent(__VLS_111, new __VLS_111({}));
const __VLS_113 = __VLS_112({}, ...__VLS_functionalComponentArgsRest(__VLS_112));
var __VLS_110;
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
if (__VLS_ctx.currentTab === 'bi') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "content-section" },
        id: "section-bi",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-grid" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-badge blue" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-number" },
    });
    (__VLS_ctx.formatNumber(__VLS_ctx.biMetrics.total_views));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-sub" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-badge cyan" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-number" },
    });
    (__VLS_ctx.formatNumber(__VLS_ctx.biMetrics.total_danmakus));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-sub" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-badge purple" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-number" },
    });
    (__VLS_ctx.formatNumber(__VLS_ctx.biMetrics.total_comments));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-sub" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-badge pink" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-number" },
    });
    (__VLS_ctx.formatNumber(__VLS_ctx.biMetrics.total_likes));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-sub" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-badge indigo" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-number" },
    });
    (__VLS_ctx.biMetrics.total_users);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-sub" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-badge green" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-number" },
    });
    (__VLS_ctx.biMetrics.active_creators);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-sub" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-badge amber" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-number" },
    });
    (__VLS_ctx.biMetrics.active_reviewers);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-sub" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "kpi-badge red" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-number" },
    });
    (__VLS_ctx.biMetrics.pending_applications);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "kpi-sub" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "chart-block glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "chart-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "chart-title-wrap" },
    });
    const __VLS_115 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_116 = __VLS_asFunctionalComponent(__VLS_115, new __VLS_115({
        ...{ class: "chart-icon" },
    }));
    const __VLS_117 = __VLS_116({
        ...{ class: "chart-icon" },
    }, ...__VLS_functionalComponentArgsRest(__VLS_116));
    __VLS_118.slots.default;
    const __VLS_119 = {}.TrendCharts;
    /** @type {[typeof __VLS_components.TrendCharts, ]} */ ;
    // @ts-ignore
    const __VLS_120 = __VLS_asFunctionalComponent(__VLS_119, new __VLS_119({}));
    const __VLS_121 = __VLS_120({}, ...__VLS_functionalComponentArgsRest(__VLS_120));
    var __VLS_118;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "chart-heading" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "chart-subtext" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "chart-legend-pills" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "legend-pill history" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "dot history" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "legend-pill forecast" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "dot forecast" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "legend-pill bound" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "dot bound" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ref: "biChartRef",
        ...{ class: "echarts-container" },
        id: "bi-trend-echart",
    });
    /** @type {typeof __VLS_ctx.biChartRef} */ ;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "viral-ranking-block glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "block-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "title-wrap" },
    });
    const __VLS_123 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_124 = __VLS_asFunctionalComponent(__VLS_123, new __VLS_123({
        ...{ class: "block-icon" },
    }));
    const __VLS_125 = __VLS_124({
        ...{ class: "block-icon" },
    }, ...__VLS_functionalComponentArgsRest(__VLS_124));
    __VLS_126.slots.default;
    const __VLS_127 = {}.Rank;
    /** @type {[typeof __VLS_components.Rank, ]} */ ;
    // @ts-ignore
    const __VLS_128 = __VLS_asFunctionalComponent(__VLS_127, new __VLS_127({}));
    const __VLS_129 = __VLS_128({}, ...__VLS_functionalComponentArgsRest(__VLS_128));
    var __VLS_126;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "chart-heading" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "chart-subtext" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "viral-table-wrap" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.table, __VLS_intrinsicElements.table)({
        ...{ class: "apple-table" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.thead, __VLS_intrinsicElements.thead)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
        ...{ style: {} },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.tbody, __VLS_intrinsicElements.tbody)({});
    for (const [item, idx] of __VLS_getVForSourceType((__VLS_ctx.viralRankings))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({
            key: (item.video_id),
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "rank-index" },
            ...{ class: ('rank-' + (idx + 1)) },
        });
        (idx + 1);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
            ...{ class: "font-bold" },
        });
        (item.title);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "tag-pill" },
        });
        (item.category);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        (item.total_episodes);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        (__VLS_ctx.formatNumber(item.view_count));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "score-progress-wrap" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "score-val" },
        });
        (item.viral_score);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "score-bar" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "score-fill" },
            ...{ style: ({ width: item.viral_score + '%' }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "status-badge" },
            ...{ class: (item.badge_type) },
        });
        (item.viral_tag);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
            ...{ class: "growth-text" },
        });
        (__VLS_ctx.formatNumber(item.predicted_next_week_views));
    }
}
if (__VLS_ctx.currentTab === 'dramas') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "content-section" },
        id: "section-dramas",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "table-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "table-card-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "search-box" },
    });
    const __VLS_131 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_132 = __VLS_asFunctionalComponent(__VLS_131, new __VLS_131({}));
    const __VLS_133 = __VLS_132({}, ...__VLS_functionalComponentArgsRest(__VLS_132));
    __VLS_134.slots.default;
    const __VLS_135 = {}.Search;
    /** @type {[typeof __VLS_components.Search, ]} */ ;
    // @ts-ignore
    const __VLS_136 = __VLS_asFunctionalComponent(__VLS_135, new __VLS_135({}));
    const __VLS_137 = __VLS_136({}, ...__VLS_functionalComponentArgsRest(__VLS_136));
    var __VLS_134;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        ...{ onInput: (__VLS_ctx.filterDramas) },
        placeholder: "搜索短剧标题、题材分类...",
        ...{ class: "table-search-input" },
    });
    (__VLS_ctx.dramaSearchKeyword);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "table-header-actions" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "stat-counter" },
    });
    (__VLS_ctx.filteredDramas.length);
    if (__VLS_ctx.selectedDramaIds.length > 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.handleBatchDeleteDramas) },
            ...{ class: "apple-btn-secondary" },
            ...{ style: {} },
            id: "btn-admin-batch-delete-dramas",
        });
        const __VLS_139 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_140 = __VLS_asFunctionalComponent(__VLS_139, new __VLS_139({}));
        const __VLS_141 = __VLS_140({}, ...__VLS_functionalComponentArgsRest(__VLS_140));
        __VLS_142.slots.default;
        const __VLS_143 = {}.Delete;
        /** @type {[typeof __VLS_components.Delete, ]} */ ;
        // @ts-ignore
        const __VLS_144 = __VLS_asFunctionalComponent(__VLS_143, new __VLS_143({}));
        const __VLS_145 = __VLS_144({}, ...__VLS_functionalComponentArgsRest(__VLS_144));
        var __VLS_142;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (__VLS_ctx.selectedDramaIds.length);
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.openSyncDialog) },
        ...{ class: "apple-btn-primary" },
    });
    const __VLS_147 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_148 = __VLS_asFunctionalComponent(__VLS_147, new __VLS_147({}));
    const __VLS_149 = __VLS_148({}, ...__VLS_functionalComponentArgsRest(__VLS_148));
    __VLS_150.slots.default;
    const __VLS_151 = {}.Refresh;
    /** @type {[typeof __VLS_components.Refresh, ]} */ ;
    // @ts-ignore
    const __VLS_152 = __VLS_asFunctionalComponent(__VLS_151, new __VLS_151({}));
    const __VLS_153 = __VLS_152({}, ...__VLS_functionalComponentArgsRest(__VLS_152));
    var __VLS_150;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "apple-table-viewport-wrap" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.table, __VLS_intrinsicElements.table)({
        ...{ class: "apple-table" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.thead, __VLS_intrinsicElements.thead)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
        ...{ style: {} },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        ...{ onChange: (__VLS_ctx.toggleSelectAllDramas) },
        type: "checkbox",
        checked: (__VLS_ctx.isAllDramasSelected),
        id: "checkbox-select-all-dramas",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
        ...{ style: {} },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
        ...{ style: {} },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.tbody, __VLS_intrinsicElements.tbody)({});
    for (const [d] of __VLS_getVForSourceType((__VLS_ctx.paginatedDramas))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({
            key: (d.id),
            id: ('drama-row-' + d.id),
            ...{ class: "table-row drama-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
            ...{ style: {} },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            type: "checkbox",
            value: (d.id),
            id: ('chk-drama-' + d.id),
        });
        (__VLS_ctx.selectedDramaIds);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.currentTab === 'dramas'))
                        return;
                    __VLS_ctx.openPosterCarousel(d);
                } },
            ...{ class: "drama-thumb-wrapper" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
            ...{ onError: ((e) => e.target.src = __VLS_ctx.defaultDramaPoster) },
            src: (d.effective_cover || d.cover_url || __VLS_ctx.defaultDramaPoster),
            ...{ class: "drama-thumb-img" },
        });
        if (d.extra_images && d.extra_images.length > 1) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "multi-poster-tag" },
                title: "包含多张剧照海报",
            });
            const __VLS_155 = {}.ElIcon;
            /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
            // @ts-ignore
            const __VLS_156 = __VLS_asFunctionalComponent(__VLS_155, new __VLS_155({
                size: (10),
            }));
            const __VLS_157 = __VLS_156({
                size: (10),
            }, ...__VLS_functionalComponentArgsRest(__VLS_156));
            __VLS_158.slots.default;
            const __VLS_159 = {}.Picture;
            /** @type {[typeof __VLS_components.Picture, ]} */ ;
            // @ts-ignore
            const __VLS_160 = __VLS_asFunctionalComponent(__VLS_159, new __VLS_159({}));
            const __VLS_161 = __VLS_160({}, ...__VLS_functionalComponentArgsRest(__VLS_160));
            var __VLS_158;
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
            (d.extra_images.length);
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "drama-title-main" },
        });
        (d.title);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "drama-synopsis-sub" },
        });
        (d.summary || '暂无梗概');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "tag-pill" },
        });
        (d.category);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        (d.total_episodes);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "stats-mini-line" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (__VLS_ctx.formatNumber(d.view_count));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (__VLS_ctx.formatNumber(d.like_count));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "status-badge" },
            ...{ class: (d.status === 'PUBLISHED' ? 'success' : 'warning') },
            id: ('drama-status-' + d.id),
        });
        (d.status === 'PUBLISHED' ? '已上架' : '已屏蔽下线');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "actions-group" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.currentTab === 'dramas'))
                        return;
                    __VLS_ctx.toggleDramaStatus(d);
                } },
            ...{ class: "btn-text-action" },
            ...{ class: (d.status === 'PUBLISHED' ? 'btn-warn' : 'btn-success') },
            id: ('btn-toggle-status-' + d.id),
        });
        const __VLS_163 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_164 = __VLS_asFunctionalComponent(__VLS_163, new __VLS_163({}));
        const __VLS_165 = __VLS_164({}, ...__VLS_functionalComponentArgsRest(__VLS_164));
        __VLS_166.slots.default;
        if (d.status !== 'PUBLISHED') {
            const __VLS_167 = {}.View;
            /** @type {[typeof __VLS_components.View, ]} */ ;
            // @ts-ignore
            const __VLS_168 = __VLS_asFunctionalComponent(__VLS_167, new __VLS_167({}));
            const __VLS_169 = __VLS_168({}, ...__VLS_functionalComponentArgsRest(__VLS_168));
        }
        else {
            const __VLS_171 = {}.Hide;
            /** @type {[typeof __VLS_components.Hide, ]} */ ;
            // @ts-ignore
            const __VLS_172 = __VLS_asFunctionalComponent(__VLS_171, new __VLS_171({}));
            const __VLS_173 = __VLS_172({}, ...__VLS_functionalComponentArgsRest(__VLS_172));
        }
        var __VLS_166;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (d.status === 'PUBLISHED' ? '屏蔽' : '上架');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.currentTab === 'dramas'))
                        return;
                    __VLS_ctx.openEditCoverModal(d);
                } },
            ...{ class: "btn-text-action" },
            id: ('btn-edit-cover-' + d.id),
            title: "全量编辑短剧元数据与海报",
        });
        const __VLS_175 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_176 = __VLS_asFunctionalComponent(__VLS_175, new __VLS_175({}));
        const __VLS_177 = __VLS_176({}, ...__VLS_functionalComponentArgsRest(__VLS_176));
        __VLS_178.slots.default;
        const __VLS_179 = {}.Edit;
        /** @type {[typeof __VLS_components.Edit, ]} */ ;
        // @ts-ignore
        const __VLS_180 = __VLS_asFunctionalComponent(__VLS_179, new __VLS_179({}));
        const __VLS_181 = __VLS_180({}, ...__VLS_functionalComponentArgsRest(__VLS_180));
        var __VLS_178;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        if (d.extra_images && d.extra_images.length > 1) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!(__VLS_ctx.currentTab === 'dramas'))
                            return;
                        if (!(d.extra_images && d.extra_images.length > 1))
                            return;
                        __VLS_ctx.openPosterCarousel(d);
                    } },
                ...{ class: "btn-text-action" },
            });
            const __VLS_183 = {}.ElIcon;
            /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
            // @ts-ignore
            const __VLS_184 = __VLS_asFunctionalComponent(__VLS_183, new __VLS_183({}));
            const __VLS_185 = __VLS_184({}, ...__VLS_functionalComponentArgsRest(__VLS_184));
            __VLS_186.slots.default;
            const __VLS_187 = {}.Picture;
            /** @type {[typeof __VLS_components.Picture, ]} */ ;
            // @ts-ignore
            const __VLS_188 = __VLS_asFunctionalComponent(__VLS_187, new __VLS_187({}));
            const __VLS_189 = __VLS_188({}, ...__VLS_functionalComponentArgsRest(__VLS_188));
            var __VLS_186;
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.currentTab === 'dramas'))
                        return;
                    __VLS_ctx.handleDeleteDrama(d);
                } },
            ...{ class: "btn-text-action btn-danger" },
            id: ('btn-delete-drama-' + d.id),
        });
        const __VLS_191 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_192 = __VLS_asFunctionalComponent(__VLS_191, new __VLS_191({}));
        const __VLS_193 = __VLS_192({}, ...__VLS_functionalComponentArgsRest(__VLS_192));
        __VLS_194.slots.default;
        const __VLS_195 = {}.Delete;
        /** @type {[typeof __VLS_components.Delete, ]} */ ;
        // @ts-ignore
        const __VLS_196 = __VLS_asFunctionalComponent(__VLS_195, new __VLS_195({}));
        const __VLS_197 = __VLS_196({}, ...__VLS_functionalComponentArgsRest(__VLS_196));
        var __VLS_194;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "table-pagination-row" },
    });
    const __VLS_199 = {}.ElPagination;
    /** @type {[typeof __VLS_components.ElPagination, typeof __VLS_components.elPagination, ]} */ ;
    // @ts-ignore
    const __VLS_200 = __VLS_asFunctionalComponent(__VLS_199, new __VLS_199({
        currentPage: (__VLS_ctx.dramaPage),
        pageSize: (__VLS_ctx.dramaPageSize),
        pageSizes: ([10, 20, 50]),
        total: (__VLS_ctx.filteredDramas.length),
        layout: "total, sizes, prev, pager, next, jumper",
        id: "pagination-dramas",
    }));
    const __VLS_201 = __VLS_200({
        currentPage: (__VLS_ctx.dramaPage),
        pageSize: (__VLS_ctx.dramaPageSize),
        pageSizes: ([10, 20, 50]),
        total: (__VLS_ctx.filteredDramas.length),
        layout: "total, sizes, prev, pager, next, jumper",
        id: "pagination-dramas",
    }, ...__VLS_functionalComponentArgsRest(__VLS_200));
}
if (__VLS_ctx.currentTab === 'sync') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "content-section" },
        id: "section-sync",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "sync-dashboard-grid" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "sync-config-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "card-header-styled" },
    });
    const __VLS_203 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_204 = __VLS_asFunctionalComponent(__VLS_203, new __VLS_203({
        ...{ class: "head-icon" },
    }));
    const __VLS_205 = __VLS_204({
        ...{ class: "head-icon" },
    }, ...__VLS_functionalComponentArgsRest(__VLS_204));
    __VLS_206.slots.default;
    const __VLS_207 = {}.Refresh;
    /** @type {[typeof __VLS_components.Refresh, ]} */ ;
    // @ts-ignore
    const __VLS_208 = __VLS_asFunctionalComponent(__VLS_207, new __VLS_207({}));
    const __VLS_209 = __VLS_208({}, ...__VLS_functionalComponentArgsRest(__VLS_208));
    var __VLS_206;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "chart-heading" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "chart-subtext" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "sync-mode-selector" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "mode-radio-box" },
        ...{ class: ({ selected: __VLS_ctx.syncMode === 'incremental' }) },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        type: "radio",
        value: "incremental",
    });
    (__VLS_ctx.syncMode);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "radio-content" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "radio-title-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "radio-name" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "recommend-pill" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "radio-desc" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "mode-radio-box" },
        ...{ class: ({ selected: __VLS_ctx.syncMode === 'full' }) },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        type: "radio",
        value: "full",
    });
    (__VLS_ctx.syncMode);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "radio-content" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "radio-title-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "radio-name" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "radio-desc" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "sync-action-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.executeSync) },
        type: "button",
        ...{ class: "apple-btn-primary big-btn" },
        id: "btn-start-sync-execute",
        disabled: (__VLS_ctx.isSyncing),
    });
    const __VLS_211 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_212 = __VLS_asFunctionalComponent(__VLS_211, new __VLS_211({
        ...{ class: ({ 'is-loading': __VLS_ctx.isSyncing }) },
    }));
    const __VLS_213 = __VLS_212({
        ...{ class: ({ 'is-loading': __VLS_ctx.isSyncing }) },
    }, ...__VLS_functionalComponentArgsRest(__VLS_212));
    __VLS_214.slots.default;
    const __VLS_215 = {}.Refresh;
    /** @type {[typeof __VLS_components.Refresh, ]} */ ;
    // @ts-ignore
    const __VLS_216 = __VLS_asFunctionalComponent(__VLS_215, new __VLS_215({}));
    const __VLS_217 = __VLS_216({}, ...__VLS_functionalComponentArgsRest(__VLS_216));
    var __VLS_214;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.isSyncing ? '正在与夸克网盘极速同步中...' : '立即启动网盘短剧映射同步');
    if (__VLS_ctx.syncResult) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "sync-report-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "report-header" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "report-status-badge" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "report-mode-tag" },
        });
        (__VLS_ctx.syncResult.mode === 'incremental' ? '增量跳过已有' : '全量重新探测');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "report-stats-grid" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "report-stat-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "num" },
        });
        (__VLS_ctx.syncResult.total_synced_dramas);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "report-stat-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "num" },
        });
        (__VLS_ctx.syncResult.total_episodes);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "report-stat-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "num" },
        });
        (__VLS_ctx.syncResult.new_episodes_added);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "report-stat-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "num" },
        });
        (__VLS_ctx.syncResult.skipped_dramas);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "label" },
        });
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "sync-telemetry-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "chart-heading" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telemetry-list" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telem-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "telem-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "telem-val" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telem-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "telem-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "telem-val font-mono" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telem-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "telem-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "telem-val" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telem-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "telem-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "telem-val font-mono" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "telem-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "telem-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "telem-val font-bold text-success" },
    });
}
if (__VLS_ctx.currentTab === 'carousels') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "content-section" },
        id: "section-carousels",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "carousel-workbench-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "workbench-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "workbench-title-box" },
    });
    const __VLS_219 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_220 = __VLS_asFunctionalComponent(__VLS_219, new __VLS_219({
        ...{ class: "head-icon text-primary" },
    }));
    const __VLS_221 = __VLS_220({
        ...{ class: "head-icon text-primary" },
    }, ...__VLS_functionalComponentArgsRest(__VLS_220));
    __VLS_222.slots.default;
    const __VLS_223 = {}.Picture;
    /** @type {[typeof __VLS_components.Picture, ]} */ ;
    // @ts-ignore
    const __VLS_224 = __VLS_asFunctionalComponent(__VLS_223, new __VLS_223({}));
    const __VLS_225 = __VLS_224({}, ...__VLS_functionalComponentArgsRest(__VLS_224));
    var __VLS_222;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "chart-heading" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "chart-subtext" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "workbench-quick-actions" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "dropdown-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
        ...{ onChange: (__VLS_ctx.handleQuickSelectDrama) },
        id: "select-carousel-drama",
        ...{ class: "apple-select workbench-select" },
        value: (__VLS_ctx.selectedCarouselDramaId),
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "",
    });
    for (const [d] of __VLS_getVForSourceType((__VLS_ctx.dramaOptionsList))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            key: (d.id),
            value: (d.id),
        });
        (d.title);
        (d.category || '短剧');
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.openCreateCarouselModal) },
        ...{ class: "apple-btn-primary" },
        id: "btn-create-carousel",
    });
    const __VLS_227 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_228 = __VLS_asFunctionalComponent(__VLS_227, new __VLS_227({}));
    const __VLS_229 = __VLS_228({}, ...__VLS_functionalComponentArgsRest(__VLS_228));
    __VLS_230.slots.default;
    const __VLS_231 = {}.Plus;
    /** @type {[typeof __VLS_components.Plus, ]} */ ;
    // @ts-ignore
    const __VLS_232 = __VLS_asFunctionalComponent(__VLS_231, new __VLS_231({}));
    const __VLS_233 = __VLS_232({}, ...__VLS_functionalComponentArgsRest(__VLS_232));
    var __VLS_230;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "carousel-live-preview-grid" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "carousel-preview-wrapper" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "carousel-preview-container" },
        id: "carousel-preview-16-9",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "aspect-16-9-box" },
    });
    if (__VLS_ctx.workbenchPreviewCover && !__VLS_ctx.workbenchImgError) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
            ...{ onError: (...[$event]) => {
                    if (!(__VLS_ctx.currentTab === 'carousels'))
                        return;
                    if (!(__VLS_ctx.workbenchPreviewCover && !__VLS_ctx.workbenchImgError))
                        return;
                    __VLS_ctx.workbenchImgError = true;
                } },
            src: (__VLS_ctx.workbenchPreviewCover),
            ...{ class: "preview-bg-img" },
        });
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "preview-empty-placeholder" },
        });
        const __VLS_235 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_236 = __VLS_asFunctionalComponent(__VLS_235, new __VLS_235({
            size: (40),
        }));
        const __VLS_237 = __VLS_236({
            size: (40),
        }, ...__VLS_functionalComponentArgsRest(__VLS_236));
        __VLS_238.slots.default;
        const __VLS_239 = {}.Picture;
        /** @type {[typeof __VLS_components.Picture, ]} */ ;
        // @ts-ignore
        const __VLS_240 = __VLS_asFunctionalComponent(__VLS_239, new __VLS_239({}));
        const __VLS_241 = __VLS_240({}, ...__VLS_functionalComponentArgsRest(__VLS_240));
        var __VLS_238;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "preview-overlay" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "preview-tag-badge" },
    });
    (__VLS_ctx.workbenchPreviewTag);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
        ...{ class: "preview-title" },
    });
    (__VLS_ctx.workbenchPreviewTitle);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "preview-subtitle" },
    });
    (__VLS_ctx.workbenchPreviewSubtitle);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "preview-ratio-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "preview-badge-status" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "workbench-quick-info" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
        ...{ class: "info-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.ul, __VLS_intrinsicElements.ul)({
        ...{ class: "info-list" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({});
    if (__VLS_ctx.selectedCarouselDramaId) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.applyWorkbenchToModal) },
            ...{ class: "apple-btn-secondary" },
        });
        const __VLS_243 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_244 = __VLS_asFunctionalComponent(__VLS_243, new __VLS_243({}));
        const __VLS_245 = __VLS_244({}, ...__VLS_functionalComponentArgsRest(__VLS_244));
        __VLS_246.slots.default;
        const __VLS_247 = {}.Promotion;
        /** @type {[typeof __VLS_components.Promotion, ]} */ ;
        // @ts-ignore
        const __VLS_248 = __VLS_asFunctionalComponent(__VLS_247, new __VLS_247({}));
        const __VLS_249 = __VLS_248({}, ...__VLS_functionalComponentArgsRest(__VLS_248));
        var __VLS_246;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "table-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "table-card-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "chart-heading" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "chart-subtext" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.table, __VLS_intrinsicElements.table)({
        ...{ class: "apple-table" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.thead, __VLS_intrinsicElements.thead)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
        ...{ style: {} },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
        ...{ style: {} },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.tbody, __VLS_intrinsicElements.tbody)({});
    for (const [c] of __VLS_getVForSourceType((__VLS_ctx.carouselsList))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({
            key: (c.id),
            id: ('carousel-row-' + c.id),
            ...{ class: "table-row" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
            src: (c.cover_url),
            ...{ class: "carousel-preview-img" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
            ...{ class: "font-bold" },
        });
        (c.title);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
            ...{ class: "sub-text-col" },
        });
        (c.subtitle);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "tag-pill" },
        });
        (c.tag);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
            ...{ class: "font-mono text-xs" },
        });
        (c.video_id || '未关联');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        (c.sort_order);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        const __VLS_251 = {}.ElSwitch;
        /** @type {[typeof __VLS_components.ElSwitch, typeof __VLS_components.elSwitch, ]} */ ;
        // @ts-ignore
        const __VLS_252 = __VLS_asFunctionalComponent(__VLS_251, new __VLS_251({
            ...{ 'onChange': {} },
            modelValue: (c.is_active),
        }));
        const __VLS_253 = __VLS_252({
            ...{ 'onChange': {} },
            modelValue: (c.is_active),
        }, ...__VLS_functionalComponentArgsRest(__VLS_252));
        let __VLS_255;
        let __VLS_256;
        let __VLS_257;
        const __VLS_258 = {
            onChange: (...[$event]) => {
                if (!(__VLS_ctx.currentTab === 'carousels'))
                    return;
                __VLS_ctx.handleToggleCarouselActive(c);
            }
        };
        var __VLS_254;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "actions-group" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.currentTab === 'carousels'))
                        return;
                    __VLS_ctx.openEditCarouselModal(c);
                } },
            ...{ class: "btn-text-action" },
        });
        const __VLS_259 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_260 = __VLS_asFunctionalComponent(__VLS_259, new __VLS_259({}));
        const __VLS_261 = __VLS_260({}, ...__VLS_functionalComponentArgsRest(__VLS_260));
        __VLS_262.slots.default;
        const __VLS_263 = {}.Edit;
        /** @type {[typeof __VLS_components.Edit, ]} */ ;
        // @ts-ignore
        const __VLS_264 = __VLS_asFunctionalComponent(__VLS_263, new __VLS_263({}));
        const __VLS_265 = __VLS_264({}, ...__VLS_functionalComponentArgsRest(__VLS_264));
        var __VLS_262;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.currentTab === 'carousels'))
                        return;
                    __VLS_ctx.handleDeleteCarousel(c);
                } },
            ...{ class: "btn-text-action btn-danger" },
        });
        const __VLS_267 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_268 = __VLS_asFunctionalComponent(__VLS_267, new __VLS_267({}));
        const __VLS_269 = __VLS_268({}, ...__VLS_functionalComponentArgsRest(__VLS_268));
        __VLS_270.slots.default;
        const __VLS_271 = {}.Delete;
        /** @type {[typeof __VLS_components.Delete, ]} */ ;
        // @ts-ignore
        const __VLS_272 = __VLS_asFunctionalComponent(__VLS_271, new __VLS_271({}));
        const __VLS_273 = __VLS_272({}, ...__VLS_functionalComponentArgsRest(__VLS_272));
        var __VLS_270;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
}
if (__VLS_ctx.currentTab === 'users') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "content-section" },
        id: "section-users",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "table-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "table-card-header user-toolbar-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "user-filters-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "search-box" },
    });
    const __VLS_275 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_276 = __VLS_asFunctionalComponent(__VLS_275, new __VLS_275({}));
    const __VLS_277 = __VLS_276({}, ...__VLS_functionalComponentArgsRest(__VLS_276));
    __VLS_278.slots.default;
    const __VLS_279 = {}.Search;
    /** @type {[typeof __VLS_components.Search, ]} */ ;
    // @ts-ignore
    const __VLS_280 = __VLS_asFunctionalComponent(__VLS_279, new __VLS_279({}));
    const __VLS_281 = __VLS_280({}, ...__VLS_functionalComponentArgsRest(__VLS_280));
    var __VLS_278;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        ...{ onInput: (__VLS_ctx.loadUsers) },
        placeholder: "搜索用户名、昵称...",
        ...{ class: "table-search-input" },
        id: "input-search-users",
    });
    (__VLS_ctx.userSearchKeyword);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
        ...{ onChange: (__VLS_ctx.loadUsers) },
        value: (__VLS_ctx.userFilterRole),
        ...{ class: "apple-select" },
        id: "select-filter-role",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "ALL",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "USER",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "CREATOR",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "REVIEWER",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "ADMIN",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
        ...{ onChange: (__VLS_ctx.loadUsers) },
        value: (__VLS_ctx.userFilterStatus),
        ...{ class: "apple-select" },
        id: "select-filter-status",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "ALL",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "ACTIVE",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "BANNED",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "table-header-actions" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "stat-counter" },
    });
    (__VLS_ctx.userTotalCount);
    if (__VLS_ctx.selectedUserIds.length > 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.handleBatchDeleteUsers) },
            ...{ class: "apple-btn-secondary" },
            ...{ style: {} },
            id: "btn-admin-batch-delete-users",
        });
        const __VLS_283 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_284 = __VLS_asFunctionalComponent(__VLS_283, new __VLS_283({}));
        const __VLS_285 = __VLS_284({}, ...__VLS_functionalComponentArgsRest(__VLS_284));
        __VLS_286.slots.default;
        const __VLS_287 = {}.Delete;
        /** @type {[typeof __VLS_components.Delete, ]} */ ;
        // @ts-ignore
        const __VLS_288 = __VLS_asFunctionalComponent(__VLS_287, new __VLS_287({}));
        const __VLS_289 = __VLS_288({}, ...__VLS_functionalComponentArgsRest(__VLS_288));
        var __VLS_286;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (__VLS_ctx.selectedUserIds.length);
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.openAddUserModal) },
        ...{ class: "apple-btn-primary" },
        id: "btn-admin-add-user",
    });
    const __VLS_291 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_292 = __VLS_asFunctionalComponent(__VLS_291, new __VLS_291({}));
    const __VLS_293 = __VLS_292({}, ...__VLS_functionalComponentArgsRest(__VLS_292));
    __VLS_294.slots.default;
    const __VLS_295 = {}.Plus;
    /** @type {[typeof __VLS_components.Plus, ]} */ ;
    // @ts-ignore
    const __VLS_296 = __VLS_asFunctionalComponent(__VLS_295, new __VLS_295({}));
    const __VLS_297 = __VLS_296({}, ...__VLS_functionalComponentArgsRest(__VLS_296));
    var __VLS_294;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "apple-table-viewport-wrap" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.table, __VLS_intrinsicElements.table)({
        ...{ class: "apple-table" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.thead, __VLS_intrinsicElements.thead)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
        ...{ style: {} },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        ...{ onChange: (__VLS_ctx.toggleSelectAllUsers) },
        type: "checkbox",
        checked: (__VLS_ctx.isAllUsersSelected),
        id: "checkbox-select-all-users",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
        ...{ style: {} },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.tbody, __VLS_intrinsicElements.tbody)({});
    for (const [u] of __VLS_getVForSourceType((__VLS_ctx.usersList))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({
            key: (u.id),
            id: ('user-row-' + u.id),
            ...{ class: "table-row" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
            ...{ style: {} },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            type: "checkbox",
            value: (u.id),
            id: ('chk-user-' + u.id),
        });
        (__VLS_ctx.selectedUserIds);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
            ...{ class: "font-bold" },
        });
        (u.username);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        (u.nickname || '-');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "role-badge" },
            ...{ class: (u.role.toLowerCase()) },
        });
        (__VLS_ctx.getRoleLabel(u.role));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "privilege-tags" },
        });
        if (u.is_creator) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "priv-tag creator" },
            });
        }
        if (u.is_reviewer) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "priv-tag reviewer" },
            });
        }
        if (!u.is_creator && !u.is_reviewer) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "priv-tag guest" },
            });
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "economy-summary-cell" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "coin-tag" },
        });
        (u.coins ?? 50);
        if (u.is_vip) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "vip-tag-active" },
            });
        }
        else {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "vip-tag-none" },
            });
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "status-badge" },
            ...{ class: (u.status === 'ACTIVE' ? 'success' : 'danger') },
        });
        (u.status === 'ACTIVE' ? '正常活跃' : '已封禁');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
            ...{ class: "sub-text-col" },
        });
        (u.created_at?.slice(0, 10));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "actions-group" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.currentTab === 'users'))
                        return;
                    __VLS_ctx.openEditUserModal(u);
                } },
            ...{ class: "btn-text-action" },
            id: ('btn-edit-user-' + u.id),
            title: "编辑资料与资产",
        });
        const __VLS_299 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_300 = __VLS_asFunctionalComponent(__VLS_299, new __VLS_299({}));
        const __VLS_301 = __VLS_300({}, ...__VLS_functionalComponentArgsRest(__VLS_300));
        __VLS_302.slots.default;
        const __VLS_303 = {}.Edit;
        /** @type {[typeof __VLS_components.Edit, ]} */ ;
        // @ts-ignore
        const __VLS_304 = __VLS_asFunctionalComponent(__VLS_303, new __VLS_303({}));
        const __VLS_305 = __VLS_304({}, ...__VLS_functionalComponentArgsRest(__VLS_304));
        var __VLS_302;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.currentTab === 'users'))
                        return;
                    __VLS_ctx.openRoleModal(u);
                } },
            ...{ class: "btn-text-action" },
            id: ('btn-change-role-' + u.id),
            title: "调整系统角色",
        });
        const __VLS_307 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_308 = __VLS_asFunctionalComponent(__VLS_307, new __VLS_307({}));
        const __VLS_309 = __VLS_308({}, ...__VLS_functionalComponentArgsRest(__VLS_308));
        __VLS_310.slots.default;
        const __VLS_311 = {}.Switch;
        /** @type {[typeof __VLS_components.Switch, ]} */ ;
        // @ts-ignore
        const __VLS_312 = __VLS_asFunctionalComponent(__VLS_311, new __VLS_311({}));
        const __VLS_313 = __VLS_312({}, ...__VLS_functionalComponentArgsRest(__VLS_312));
        var __VLS_310;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.currentTab === 'users'))
                        return;
                    __VLS_ctx.toggleUserStatus(u);
                } },
            ...{ class: "btn-text-action" },
            ...{ class: (u.status === 'ACTIVE' ? 'btn-warn' : 'btn-success') },
            id: ('btn-toggle-ban-' + u.id),
        });
        const __VLS_315 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_316 = __VLS_asFunctionalComponent(__VLS_315, new __VLS_315({}));
        const __VLS_317 = __VLS_316({}, ...__VLS_functionalComponentArgsRest(__VLS_316));
        __VLS_318.slots.default;
        if (u.status === 'ACTIVE') {
            const __VLS_319 = {}.Lock;
            /** @type {[typeof __VLS_components.Lock, ]} */ ;
            // @ts-ignore
            const __VLS_320 = __VLS_asFunctionalComponent(__VLS_319, new __VLS_319({}));
            const __VLS_321 = __VLS_320({}, ...__VLS_functionalComponentArgsRest(__VLS_320));
        }
        else {
            const __VLS_323 = {}.Unlock;
            /** @type {[typeof __VLS_components.Unlock, ]} */ ;
            // @ts-ignore
            const __VLS_324 = __VLS_asFunctionalComponent(__VLS_323, new __VLS_323({}));
            const __VLS_325 = __VLS_324({}, ...__VLS_functionalComponentArgsRest(__VLS_324));
        }
        var __VLS_318;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (u.status === 'ACTIVE' ? '封禁' : '解封');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.currentTab === 'users'))
                        return;
                    __VLS_ctx.handleDeleteUser(u);
                } },
            ...{ class: "btn-text-action btn-danger" },
            id: ('btn-delete-user-' + u.id),
            title: "物理级联删除",
        });
        const __VLS_327 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_328 = __VLS_asFunctionalComponent(__VLS_327, new __VLS_327({}));
        const __VLS_329 = __VLS_328({}, ...__VLS_functionalComponentArgsRest(__VLS_328));
        __VLS_330.slots.default;
        const __VLS_331 = {}.Delete;
        /** @type {[typeof __VLS_components.Delete, ]} */ ;
        // @ts-ignore
        const __VLS_332 = __VLS_asFunctionalComponent(__VLS_331, new __VLS_331({}));
        const __VLS_333 = __VLS_332({}, ...__VLS_functionalComponentArgsRest(__VLS_332));
        var __VLS_330;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "table-pagination-row" },
    });
    const __VLS_335 = {}.ElPagination;
    /** @type {[typeof __VLS_components.ElPagination, typeof __VLS_components.elPagination, ]} */ ;
    // @ts-ignore
    const __VLS_336 = __VLS_asFunctionalComponent(__VLS_335, new __VLS_335({
        ...{ 'onSizeChange': {} },
        ...{ 'onCurrentChange': {} },
        currentPage: (__VLS_ctx.userPage),
        pageSize: (__VLS_ctx.userPageSize),
        pageSizes: ([10, 20, 50, 100]),
        total: (__VLS_ctx.userTotalCount),
        layout: "total, sizes, prev, pager, next, jumper",
        id: "pagination-users",
    }));
    const __VLS_337 = __VLS_336({
        ...{ 'onSizeChange': {} },
        ...{ 'onCurrentChange': {} },
        currentPage: (__VLS_ctx.userPage),
        pageSize: (__VLS_ctx.userPageSize),
        pageSizes: ([10, 20, 50, 100]),
        total: (__VLS_ctx.userTotalCount),
        layout: "total, sizes, prev, pager, next, jumper",
        id: "pagination-users",
    }, ...__VLS_functionalComponentArgsRest(__VLS_336));
    let __VLS_339;
    let __VLS_340;
    let __VLS_341;
    const __VLS_342 = {
        onSizeChange: (__VLS_ctx.loadUsers)
    };
    const __VLS_343 = {
        onCurrentChange: (__VLS_ctx.loadUsers)
    };
    var __VLS_338;
}
if (__VLS_ctx.currentTab === 'applications') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "content-section" },
        id: "section-applications",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "dual-subtabs-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.currentTab === 'applications'))
                    return;
                __VLS_ctx.applicationSubTab = 'creators';
            } },
        ...{ class: "subtab-btn" },
        ...{ class: ({ active: __VLS_ctx.applicationSubTab === 'creators' }) },
        id: "subtab-creators",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.pendingCreators.length);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.currentTab === 'applications'))
                    return;
                __VLS_ctx.applicationSubTab = 'reviewers';
            } },
        ...{ class: "subtab-btn" },
        ...{ class: ({ active: __VLS_ctx.applicationSubTab === 'reviewers' }) },
        id: "subtab-reviewers",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.pendingReviewers.length);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "table-card glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.table, __VLS_intrinsicElements.table)({
        ...{ class: "apple-table" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.thead, __VLS_intrinsicElements.thead)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
        ...{ style: {} },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.tbody, __VLS_intrinsicElements.tbody)({});
    for (const [app] of __VLS_getVForSourceType(((__VLS_ctx.applicationSubTab === 'creators' ? __VLS_ctx.pendingCreators : __VLS_ctx.pendingReviewers)))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({
            key: (app.user_id),
            id: ('app-row-' + app.user_id),
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
            ...{ class: "font-bold" },
        });
        (app.username);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        (__VLS_ctx.applicationSubTab === 'creators' ? '短剧创作者' : '持证审核员');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
            ...{ class: "sub-text-col" },
        });
        (app.bio || '无附加陈述');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        (app.applied_at?.slice(0, 16));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "status-badge warning" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "actions-group" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.currentTab === 'applications'))
                        return;
                    __VLS_ctx.handleApproveApplication(app);
                } },
            ...{ class: "apple-btn-primary btn-sm" },
            id: ('btn-approve-' + app.user_id),
        });
        const __VLS_344 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_345 = __VLS_asFunctionalComponent(__VLS_344, new __VLS_344({}));
        const __VLS_346 = __VLS_345({}, ...__VLS_functionalComponentArgsRest(__VLS_345));
        __VLS_347.slots.default;
        const __VLS_348 = {}.Check;
        /** @type {[typeof __VLS_components.Check, ]} */ ;
        // @ts-ignore
        const __VLS_349 = __VLS_asFunctionalComponent(__VLS_348, new __VLS_348({}));
        const __VLS_350 = __VLS_349({}, ...__VLS_functionalComponentArgsRest(__VLS_349));
        var __VLS_347;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.currentTab === 'applications'))
                        return;
                    __VLS_ctx.handleRejectApplication(app);
                } },
            ...{ class: "apple-btn-secondary btn-sm" },
            id: ('btn-reject-' + app.user_id),
        });
        const __VLS_352 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_353 = __VLS_asFunctionalComponent(__VLS_352, new __VLS_352({}));
        const __VLS_354 = __VLS_353({}, ...__VLS_functionalComponentArgsRest(__VLS_353));
        __VLS_355.slots.default;
        const __VLS_356 = {}.Close;
        /** @type {[typeof __VLS_components.Close, ]} */ ;
        // @ts-ignore
        const __VLS_357 = __VLS_asFunctionalComponent(__VLS_356, new __VLS_356({}));
        const __VLS_358 = __VLS_357({}, ...__VLS_functionalComponentArgsRest(__VLS_357));
        var __VLS_355;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    if ((__VLS_ctx.applicationSubTab === 'creators' ? __VLS_ctx.pendingCreators : __VLS_ctx.pendingReviewers).length === 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
            colspan: "6",
            ...{ class: "empty-table-cell" },
        });
    }
}
if (__VLS_ctx.currentTab === 'contents') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "content-section" },
        id: "section-contents",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "dual-subtabs-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.currentTab === 'contents'))
                    return;
                __VLS_ctx.switchContentSubTab('queue');
            } },
        ...{ class: "subtab-btn" },
        ...{ class: ({ active: __VLS_ctx.contentSubTab === 'queue' }) },
        id: "subtab-review-queue",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.reviewQueueList.length);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.currentTab === 'contents'))
                    return;
                __VLS_ctx.switchContentSubTab('lexicon');
            } },
        ...{ class: "subtab-btn" },
        ...{ class: ({ active: __VLS_ctx.contentSubTab === 'lexicon' }) },
        id: "subtab-sensitive-lexicon",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.sensitiveWordsTotal);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.currentTab === 'contents'))
                    return;
                __VLS_ctx.switchContentSubTab('danmakus');
            } },
        ...{ class: "subtab-btn" },
        ...{ class: ({ active: __VLS_ctx.contentSubTab === 'danmakus' }) },
        id: "subtab-danmakus",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.danmakusList.length);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.currentTab === 'contents'))
                    return;
                __VLS_ctx.switchContentSubTab('comments');
            } },
        ...{ class: "subtab-btn" },
        ...{ class: ({ active: __VLS_ctx.contentSubTab === 'comments' }) },
        id: "subtab-comments",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.commentsList.length);
    if (__VLS_ctx.contentSubTab === 'queue') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "table-card glass-card" },
            id: "card-review-queue",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "table-card-header" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
            ...{ class: "chart-heading" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "chart-subtext" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "stat-counter" },
        });
        (__VLS_ctx.reviewQueueList.length);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.table, __VLS_intrinsicElements.table)({
            ...{ class: "apple-table" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.thead, __VLS_intrinsicElements.thead)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
            ...{ style: {} },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tbody, __VLS_intrinsicElements.tbody)({});
        for (const [item] of __VLS_getVForSourceType((__VLS_ctx.reviewQueueList))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({
                key: (item.id),
                id: ('review-row-' + item.id),
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "priv-tag" },
                ...{ class: (item.target_type === 'DANMAKU' ? 'creator' : 'reviewer') },
            });
            (item.target_type === 'DANMAKU' ? '弹幕' : '评论');
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                ...{ class: "font-bold" },
            });
            (item.video_title);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "violation-reason-cell" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "raw-snippet" },
            });
            (item.raw_content || item.violation_reason);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "matched-words-wrap" },
            });
            for (const [w] of __VLS_getVForSourceType((item.matched_words))) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                    key: (w),
                    ...{ class: "risk-pill-mini high" },
                });
                (w);
            }
            if (!item.matched_words?.length) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                    ...{ class: "sub-text-col" },
                });
            }
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "status-badge" },
                ...{ class: (item.risk_level === 'HIGH' ? 'danger' : 'warning') },
            });
            (item.risk_level === 'HIGH' ? '高风险' : '中风险');
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                ...{ class: "sub-text-col" },
            });
            (item.created_at);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "actions-group" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!(__VLS_ctx.currentTab === 'contents'))
                            return;
                        if (!(__VLS_ctx.contentSubTab === 'queue'))
                            return;
                        __VLS_ctx.handleReviewDecision(item.id, 'APPROVED');
                    } },
                ...{ class: "apple-btn-secondary btn-sm" },
                id: ('btn-approve-review-' + item.id),
            });
            const __VLS_360 = {}.ElIcon;
            /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
            // @ts-ignore
            const __VLS_361 = __VLS_asFunctionalComponent(__VLS_360, new __VLS_360({}));
            const __VLS_362 = __VLS_361({}, ...__VLS_functionalComponentArgsRest(__VLS_361));
            __VLS_363.slots.default;
            const __VLS_364 = {}.Check;
            /** @type {[typeof __VLS_components.Check, ]} */ ;
            // @ts-ignore
            const __VLS_365 = __VLS_asFunctionalComponent(__VLS_364, new __VLS_364({}));
            const __VLS_366 = __VLS_365({}, ...__VLS_functionalComponentArgsRest(__VLS_365));
            var __VLS_363;
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!(__VLS_ctx.currentTab === 'contents'))
                            return;
                        if (!(__VLS_ctx.contentSubTab === 'queue'))
                            return;
                        __VLS_ctx.handleReviewDecision(item.id, 'REJECTED');
                    } },
                ...{ class: "apple-btn-primary btn-sm btn-danger" },
                id: ('btn-reject-review-' + item.id),
            });
            const __VLS_368 = {}.ElIcon;
            /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
            // @ts-ignore
            const __VLS_369 = __VLS_asFunctionalComponent(__VLS_368, new __VLS_368({}));
            const __VLS_370 = __VLS_369({}, ...__VLS_functionalComponentArgsRest(__VLS_369));
            __VLS_371.slots.default;
            const __VLS_372 = {}.Delete;
            /** @type {[typeof __VLS_components.Delete, ]} */ ;
            // @ts-ignore
            const __VLS_373 = __VLS_asFunctionalComponent(__VLS_372, new __VLS_372({}));
            const __VLS_374 = __VLS_373({}, ...__VLS_functionalComponentArgsRest(__VLS_373));
            var __VLS_371;
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        }
        if (__VLS_ctx.reviewQueueList.length === 0) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                colspan: "7",
                ...{ class: "empty-table-cell" },
            });
        }
    }
    if (__VLS_ctx.contentSubTab === 'lexicon') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "lexicon-composite-grid" },
            id: "card-sensitive-lexicon",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "table-card glass-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "table-card-header" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
            ...{ class: "chart-heading" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "chart-subtext" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.openAddWordModal) },
            ...{ class: "apple-btn-primary" },
            id: "btn-add-sensitive-word",
        });
        const __VLS_376 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_377 = __VLS_asFunctionalComponent(__VLS_376, new __VLS_376({}));
        const __VLS_378 = __VLS_377({}, ...__VLS_functionalComponentArgsRest(__VLS_377));
        __VLS_379.slots.default;
        const __VLS_380 = {}.Plus;
        /** @type {[typeof __VLS_components.Plus, ]} */ ;
        // @ts-ignore
        const __VLS_381 = __VLS_asFunctionalComponent(__VLS_380, new __VLS_380({}));
        const __VLS_382 = __VLS_381({}, ...__VLS_functionalComponentArgsRest(__VLS_381));
        var __VLS_379;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "lexicon-filters-row" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            ...{ onInput: (__VLS_ctx.loadSensitiveWords) },
            value: (__VLS_ctx.sensitiveWordSearch),
            type: "text",
            ...{ class: "apple-input search-input" },
            placeholder: "搜索敏感词...",
            id: "input-search-word",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
            ...{ onChange: (__VLS_ctx.loadSensitiveWords) },
            value: (__VLS_ctx.sensitiveWordCategory),
            ...{ class: "apple-select" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "ALL",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "涉政",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "暴恐",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "违禁",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "涉黄",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "辱骂",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "广告",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
            ...{ onChange: (__VLS_ctx.loadSensitiveWords) },
            value: (__VLS_ctx.sensitiveWordLevel),
            ...{ class: "apple-select" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "ALL",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "HIGH",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "MEDIUM",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
            value: "LOW",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.table, __VLS_intrinsicElements.table)({
            ...{ class: "apple-table" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.thead, __VLS_intrinsicElements.thead)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
            ...{ style: {} },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tbody, __VLS_intrinsicElements.tbody)({});
        for (const [word] of __VLS_getVForSourceType((__VLS_ctx.sensitiveWordsList))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({
                key: (word.id),
                id: ('word-row-' + word.id),
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                ...{ class: "font-bold font-mono" },
            });
            (word.word);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "priv-tag creator" },
            });
            (word.category);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "status-badge" },
                ...{ class: (word.level === 'HIGH' ? 'danger' : 'warning') },
            });
            (word.level);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                ...{ class: "sub-text-col" },
            });
            (word.created_at);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!(__VLS_ctx.currentTab === 'contents'))
                            return;
                        if (!(__VLS_ctx.contentSubTab === 'lexicon'))
                            return;
                        __VLS_ctx.handleDeleteSensitiveWord(word);
                    } },
                ...{ class: "btn-text-action btn-danger" },
                id: ('btn-del-word-' + word.id),
            });
            const __VLS_384 = {}.ElIcon;
            /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
            // @ts-ignore
            const __VLS_385 = __VLS_asFunctionalComponent(__VLS_384, new __VLS_384({}));
            const __VLS_386 = __VLS_385({}, ...__VLS_functionalComponentArgsRest(__VLS_385));
            __VLS_387.slots.default;
            const __VLS_388 = {}.Delete;
            /** @type {[typeof __VLS_components.Delete, ]} */ ;
            // @ts-ignore
            const __VLS_389 = __VLS_asFunctionalComponent(__VLS_388, new __VLS_388({}));
            const __VLS_390 = __VLS_389({}, ...__VLS_functionalComponentArgsRest(__VLS_389));
            var __VLS_387;
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        }
        if (__VLS_ctx.sensitiveWordsList.length === 0) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                colspan: "5",
                ...{ class: "empty-table-cell" },
            });
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "glass-card dfa-sandbox-card" },
            id: "card-dfa-sandbox",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "card-header-styled" },
        });
        const __VLS_392 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_393 = __VLS_asFunctionalComponent(__VLS_392, new __VLS_392({
            ...{ class: "head-icon" },
        }));
        const __VLS_394 = __VLS_393({
            ...{ class: "head-icon" },
        }, ...__VLS_functionalComponentArgsRest(__VLS_393));
        __VLS_395.slots.default;
        const __VLS_396 = {}.Check;
        /** @type {[typeof __VLS_components.Check, ]} */ ;
        // @ts-ignore
        const __VLS_397 = __VLS_asFunctionalComponent(__VLS_396, new __VLS_396({}));
        const __VLS_398 = __VLS_397({}, ...__VLS_functionalComponentArgsRest(__VLS_397));
        var __VLS_395;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
            ...{ class: "chart-heading" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "chart-subtext" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "sandbox-body" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "form-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.textarea, __VLS_intrinsicElements.textarea)({
            value: (__VLS_ctx.dfaTestText),
            ...{ class: "apple-textarea" },
            rows: "4",
            placeholder: "例如：这部短剧太好看了，但是有些违禁词需要测试，看看能否精准拦截...",
            id: "textarea-dfa-test",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.runDfaTest) },
            ...{ class: "apple-btn-primary full-width" },
            disabled: (!__VLS_ctx.dfaTestText.trim() || __VLS_ctx.dfaTesting),
            id: "btn-run-dfa-test",
        });
        const __VLS_400 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_401 = __VLS_asFunctionalComponent(__VLS_400, new __VLS_400({
            ...{ class: ({ 'is-loading': __VLS_ctx.dfaTesting }) },
        }));
        const __VLS_402 = __VLS_401({
            ...{ class: ({ 'is-loading': __VLS_ctx.dfaTesting }) },
        }, ...__VLS_functionalComponentArgsRest(__VLS_401));
        __VLS_403.slots.default;
        const __VLS_404 = {}.Refresh;
        /** @type {[typeof __VLS_components.Refresh, ]} */ ;
        // @ts-ignore
        const __VLS_405 = __VLS_asFunctionalComponent(__VLS_404, new __VLS_404({}));
        const __VLS_406 = __VLS_405({}, ...__VLS_functionalComponentArgsRest(__VLS_405));
        var __VLS_403;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (__VLS_ctx.dfaTesting ? '检测中...' : '立即运行 DFA 匹配检测');
        if (__VLS_ctx.dfaTestResult) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "sandbox-result-box" },
                ...{ class: ({ 'is-violation': __VLS_ctx.dfaTestResult.has_violation }) },
                id: "dfa-test-result-box",
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "result-status-row" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "status-badge" },
                ...{ class: (__VLS_ctx.dfaTestResult.has_violation ? 'danger' : 'success') },
            });
            (__VLS_ctx.dfaTestResult.has_violation ? '⚠️ 命中违禁词！' : '✅ 检测通过（安全无违规）');
            if (__VLS_ctx.dfaTestResult.has_violation) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                    ...{ class: "risk-tag-text" },
                });
                (__VLS_ctx.dfaTestResult.max_risk_level);
            }
            if (__VLS_ctx.dfaTestResult.has_violation) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "result-detail-line" },
                });
                __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                    ...{ class: "detail-label" },
                });
                for (const [w] of __VLS_getVForSourceType((__VLS_ctx.dfaTestResult.matched_words))) {
                    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                        key: (w),
                        ...{ class: "risk-pill-mini high" },
                    });
                    (w);
                }
            }
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "result-detail-line" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "detail-label" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "sanitized-code" },
            });
            (__VLS_ctx.dfaTestResult.sanitized_text);
        }
    }
    if (__VLS_ctx.contentSubTab === 'danmakus') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "table-card glass-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ style: {} },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ style: {} },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            ...{ onKeyup: (__VLS_ctx.fetchDanmakus) },
            value: (__VLS_ctx.danmakuSearchQuery),
            type: "text",
            placeholder: "搜索弹幕内容/关键词...",
            ...{ class: "apple-input" },
            ...{ style: {} },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.fetchDanmakus) },
            ...{ class: "btn-action" },
        });
        const __VLS_408 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_409 = __VLS_asFunctionalComponent(__VLS_408, new __VLS_408({}));
        const __VLS_410 = __VLS_409({}, ...__VLS_functionalComponentArgsRest(__VLS_409));
        __VLS_411.slots.default;
        const __VLS_412 = {}.Search;
        /** @type {[typeof __VLS_components.Search, ]} */ ;
        // @ts-ignore
        const __VLS_413 = __VLS_asFunctionalComponent(__VLS_412, new __VLS_412({}));
        const __VLS_414 = __VLS_413({}, ...__VLS_functionalComponentArgsRest(__VLS_413));
        var __VLS_411;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.handleBatchDeleteDanmakus) },
            id: "btn-batch-delete-danmakus",
            ...{ class: "btn-action btn-danger" },
            disabled: (__VLS_ctx.selectedDanmakuIds.length === 0),
        });
        const __VLS_416 = {}.ElIcon;
        /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
        // @ts-ignore
        const __VLS_417 = __VLS_asFunctionalComponent(__VLS_416, new __VLS_416({}));
        const __VLS_418 = __VLS_417({}, ...__VLS_functionalComponentArgsRest(__VLS_417));
        __VLS_419.slots.default;
        const __VLS_420 = {}.Delete;
        /** @type {[typeof __VLS_components.Delete, ]} */ ;
        // @ts-ignore
        const __VLS_421 = __VLS_asFunctionalComponent(__VLS_420, new __VLS_420({}));
        const __VLS_422 = __VLS_421({}, ...__VLS_functionalComponentArgsRest(__VLS_421));
        var __VLS_419;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (__VLS_ctx.selectedDanmakuIds.length);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.table, __VLS_intrinsicElements.table)({
            ...{ class: "apple-table" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.thead, __VLS_intrinsicElements.thead)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
            ...{ style: {} },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            ...{ onChange: (__VLS_ctx.toggleSelectAllDanmakus) },
            type: "checkbox",
            checked: (__VLS_ctx.selectedDanmakuIds.length > 0 && __VLS_ctx.selectedDanmakuIds.length === __VLS_ctx.danmakusList.length),
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
            ...{ style: {} },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tbody, __VLS_intrinsicElements.tbody)({});
        for (const [dm] of __VLS_getVForSourceType((__VLS_ctx.danmakusList))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({
                key: (dm.id),
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
                type: "checkbox",
                value: (dm.id),
            });
            (__VLS_ctx.selectedDanmakuIds);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                ...{ class: "font-bold" },
            });
            (dm.content);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            (dm.user_name);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            (dm.video_title);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            (dm.episode_title);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            ((dm.timestamp || 0).toFixed(1));
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                ...{ class: "sub-text-col" },
            });
            (dm.created_at?.slice(0, 16));
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!(__VLS_ctx.currentTab === 'contents'))
                            return;
                        if (!(__VLS_ctx.contentSubTab === 'danmakus'))
                            return;
                        __VLS_ctx.handleDeleteDanmaku(dm.id);
                    } },
                ...{ class: "btn-text-action btn-danger" },
            });
            const __VLS_424 = {}.ElIcon;
            /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
            // @ts-ignore
            const __VLS_425 = __VLS_asFunctionalComponent(__VLS_424, new __VLS_424({}));
            const __VLS_426 = __VLS_425({}, ...__VLS_functionalComponentArgsRest(__VLS_425));
            __VLS_427.slots.default;
            const __VLS_428 = {}.Delete;
            /** @type {[typeof __VLS_components.Delete, ]} */ ;
            // @ts-ignore
            const __VLS_429 = __VLS_asFunctionalComponent(__VLS_428, new __VLS_428({}));
            const __VLS_430 = __VLS_429({}, ...__VLS_functionalComponentArgsRest(__VLS_429));
            var __VLS_427;
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        }
    }
    if (__VLS_ctx.contentSubTab === 'comments') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "table-card glass-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.table, __VLS_intrinsicElements.table)({
            ...{ class: "apple-table" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.thead, __VLS_intrinsicElements.thead)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({
            ...{ style: {} },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.tbody, __VLS_intrinsicElements.tbody)({});
        for (const [cm] of __VLS_getVForSourceType((__VLS_ctx.commentsList))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({
                key: (cm.id),
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                ...{ class: "font-bold" },
            });
            (cm.content);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            (cm.user_name);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            (cm.video_title);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({
                ...{ class: "sub-text-col" },
            });
            (cm.created_at?.slice(0, 16));
            __VLS_asFunctionalElement(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!(__VLS_ctx.currentTab === 'contents'))
                            return;
                        if (!(__VLS_ctx.contentSubTab === 'comments'))
                            return;
                        __VLS_ctx.handleDeleteComment(cm.id);
                    } },
                ...{ class: "btn-text-action btn-danger" },
            });
            const __VLS_432 = {}.ElIcon;
            /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
            // @ts-ignore
            const __VLS_433 = __VLS_asFunctionalComponent(__VLS_432, new __VLS_432({}));
            const __VLS_434 = __VLS_433({}, ...__VLS_functionalComponentArgsRest(__VLS_433));
            __VLS_435.slots.default;
            const __VLS_436 = {}.Delete;
            /** @type {[typeof __VLS_components.Delete, ]} */ ;
            // @ts-ignore
            const __VLS_437 = __VLS_asFunctionalComponent(__VLS_436, new __VLS_436({}));
            const __VLS_438 = __VLS_437({}, ...__VLS_functionalComponentArgsRest(__VLS_437));
            var __VLS_435;
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        }
    }
}
if (__VLS_ctx.currentTab === 'engine') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "content-section" },
        id: "section-engine",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "engine-config-grid" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "glass-card engine-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "card-header-styled" },
    });
    const __VLS_440 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_441 = __VLS_asFunctionalComponent(__VLS_440, new __VLS_440({
        ...{ class: "head-icon" },
    }));
    const __VLS_442 = __VLS_441({
        ...{ class: "head-icon" },
    }, ...__VLS_functionalComponentArgsRest(__VLS_441));
    __VLS_443.slots.default;
    const __VLS_444 = {}.Setting;
    /** @type {[typeof __VLS_components.Setting, ]} */ ;
    // @ts-ignore
    const __VLS_445 = __VLS_asFunctionalComponent(__VLS_444, new __VLS_444({}));
    const __VLS_446 = __VLS_445({}, ...__VLS_functionalComponentArgsRest(__VLS_445));
    var __VLS_443;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "chart-heading" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "chart-subtext" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "engine-form" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        ...{ class: "apple-input" },
        placeholder: "输入大模型名称（如 deepseek-r1:7b）",
    });
    (__VLS_ctx.engineForm.modelName);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    (__VLS_ctx.engineForm.temperature);
    const __VLS_448 = {}.ElSlider;
    /** @type {[typeof __VLS_components.ElSlider, typeof __VLS_components.elSlider, ]} */ ;
    // @ts-ignore
    const __VLS_449 = __VLS_asFunctionalComponent(__VLS_448, new __VLS_448({
        modelValue: (__VLS_ctx.engineForm.temperature),
        min: (0),
        max: (1),
        step: (0.05),
    }));
    const __VLS_450 = __VLS_449({
        modelValue: (__VLS_ctx.engineForm.temperature),
        min: (0),
        max: (1),
        step: (0.05),
    }, ...__VLS_functionalComponentArgsRest(__VLS_449));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.textarea, __VLS_intrinsicElements.textarea)({
        value: (__VLS_ctx.engineForm.prompt),
        ...{ class: "apple-textarea" },
        rows: "4",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.saveEngineConfig) },
        ...{ class: "apple-btn-primary" },
    });
    const __VLS_452 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_453 = __VLS_asFunctionalComponent(__VLS_452, new __VLS_452({}));
    const __VLS_454 = __VLS_453({}, ...__VLS_functionalComponentArgsRest(__VLS_453));
    __VLS_455.slots.default;
    const __VLS_456 = {}.Check;
    /** @type {[typeof __VLS_components.Check, ]} */ ;
    // @ts-ignore
    const __VLS_457 = __VLS_asFunctionalComponent(__VLS_456, new __VLS_456({}));
    const __VLS_458 = __VLS_457({}, ...__VLS_functionalComponentArgsRest(__VLS_457));
    var __VLS_455;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
const __VLS_460 = {}.ElDialog;
/** @type {[typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, ]} */ ;
// @ts-ignore
const __VLS_461 = __VLS_asFunctionalComponent(__VLS_460, new __VLS_460({
    modelValue: (__VLS_ctx.showEditCoverDialog),
    title: "短剧封面资产与多画报海报治理",
    width: "720px",
    id: "modal-edit-cover",
}));
const __VLS_462 = __VLS_461({
    modelValue: (__VLS_ctx.showEditCoverDialog),
    title: "短剧封面资产与多画报海报治理",
    width: "720px",
    id: "modal-edit-cover",
}, ...__VLS_functionalComponentArgsRest(__VLS_461));
__VLS_463.slots.default;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "dialog-form cover-governance-form" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-row-grid" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ class: "apple-input" },
    placeholder: "短剧主标题",
    id: "input-drama-title",
});
(__VLS_ctx.editingDramaMeta.title);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ class: "apple-input" },
    placeholder: "如：现代言情、逆袭爽剧",
    id: "input-drama-category",
});
(__VLS_ctx.editingDramaMeta.category);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-row-grid" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group full-width" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.textarea, __VLS_intrinsicElements.textarea)({
    value: (__VLS_ctx.editingDramaMeta.summary),
    ...{ class: "apple-textarea" },
    rows: "2",
    placeholder: "输入剧情核心冲突亮点...",
    id: "textarea-drama-summary",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group full-width" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ onDragover: (...[$event]) => {
            __VLS_ctx.isCoverDragOver = true;
        } },
    ...{ onDragleave: (...[$event]) => {
            __VLS_ctx.isCoverDragOver = false;
        } },
    ...{ onDrop: (__VLS_ctx.handleCoverDrop) },
    ...{ onClick: (__VLS_ctx.triggerUploadImage) },
    ...{ class: "cover-preview-box" },
    ...{ class: ({ 'is-dragover': __VLS_ctx.isCoverDragOver }) },
    id: "dropzone-cover-upload",
});
if (__VLS_ctx.editingCoverUrl && !__VLS_ctx.coverImgError) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
        ...{ onError: (...[$event]) => {
                if (!(__VLS_ctx.editingCoverUrl && !__VLS_ctx.coverImgError))
                    return;
                __VLS_ctx.coverImgError = true;
            } },
        src: (__VLS_ctx.editingCoverUrl),
        ...{ class: "preview-img" },
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "dashed-micro-glow-placeholder" },
    });
    const __VLS_464 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_465 = __VLS_asFunctionalComponent(__VLS_464, new __VLS_464({
        size: (36),
        ...{ class: "placeholder-icon" },
    }));
    const __VLS_466 = __VLS_465({
        size: (36),
        ...{ class: "placeholder-icon" },
    }, ...__VLS_functionalComponentArgsRest(__VLS_465));
    __VLS_467.slots.default;
    const __VLS_468 = {}.Upload;
    /** @type {[typeof __VLS_components.Upload, ]} */ ;
    // @ts-ignore
    const __VLS_469 = __VLS_asFunctionalComponent(__VLS_468, new __VLS_468({}));
    const __VLS_470 = __VLS_469({}, ...__VLS_functionalComponentArgsRest(__VLS_469));
    var __VLS_467;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "placeholder-text" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "main-tip" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "sub-tip" },
    });
}
if (__VLS_ctx.editingCoverUrl && !__VLS_ctx.coverImgError) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "cover-hover-prompt" },
    });
    const __VLS_472 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_473 = __VLS_asFunctionalComponent(__VLS_472, new __VLS_472({}));
    const __VLS_474 = __VLS_473({}, ...__VLS_functionalComponentArgsRest(__VLS_473));
    __VLS_475.slots.default;
    const __VLS_476 = {}.Upload;
    /** @type {[typeof __VLS_components.Upload, ]} */ ;
    // @ts-ignore
    const __VLS_477 = __VLS_asFunctionalComponent(__VLS_476, new __VLS_476({}));
    const __VLS_478 = __VLS_477({}, ...__VLS_functionalComponentArgsRest(__VLS_477));
    var __VLS_475;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "cover-url-manual-row" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ onInput: (...[$event]) => {
            __VLS_ctx.coverImgError = false;
        } },
    ...{ class: "apple-input text-xs" },
    placeholder: "或输入外部静态图片 URL 直链",
    id: "input-cover-url",
});
(__VLS_ctx.editingCoverUrl);
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.triggerUploadImage) },
    type: "button",
    ...{ class: "apple-btn-secondary btn-sm" },
});
const __VLS_480 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_481 = __VLS_asFunctionalComponent(__VLS_480, new __VLS_480({}));
const __VLS_482 = __VLS_481({}, ...__VLS_functionalComponentArgsRest(__VLS_481));
__VLS_483.slots.default;
const __VLS_484 = {}.Upload;
/** @type {[typeof __VLS_components.Upload, ]} */ ;
// @ts-ignore
const __VLS_485 = __VLS_asFunctionalComponent(__VLS_484, new __VLS_484({}));
const __VLS_486 = __VLS_485({}, ...__VLS_functionalComponentArgsRest(__VLS_485));
var __VLS_483;
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group full-width" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "shelf-header-row" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
(__VLS_ctx.editingDramaPosters.length);
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.triggerUploadImage) },
    type: "button",
    ...{ class: "apple-btn-secondary btn-sm" },
});
const __VLS_488 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_489 = __VLS_asFunctionalComponent(__VLS_488, new __VLS_488({}));
const __VLS_490 = __VLS_489({}, ...__VLS_functionalComponentArgsRest(__VLS_489));
__VLS_491.slots.default;
const __VLS_492 = {}.Plus;
/** @type {[typeof __VLS_components.Plus, ]} */ ;
// @ts-ignore
const __VLS_493 = __VLS_asFunctionalComponent(__VLS_492, new __VLS_492({}));
const __VLS_494 = __VLS_493({}, ...__VLS_functionalComponentArgsRest(__VLS_493));
var __VLS_491;
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "posters-shelf-grid" },
});
for (const [poster, idx] of __VLS_getVForSourceType((__VLS_ctx.editingDramaPosters))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        key: (idx),
        ...{ class: "poster-shelf-card" },
        ...{ class: ({ 'is-main': poster === __VLS_ctx.editingCoverUrl }) },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
        src: (poster),
        ...{ class: "shelf-thumb" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "shelf-card-overlay" },
    });
    if (poster === __VLS_ctx.editingCoverUrl) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "shelf-main-badge" },
        });
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!!(poster === __VLS_ctx.editingCoverUrl))
                        return;
                    __VLS_ctx.setAsMainCover(poster);
                } },
            type: "button",
            ...{ class: "shelf-btn-set-main" },
        });
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                __VLS_ctx.removePoster(idx);
            } },
        type: "button",
        ...{ class: "shelf-btn-del" },
        title: "移除画报",
    });
    const __VLS_496 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_497 = __VLS_asFunctionalComponent(__VLS_496, new __VLS_496({}));
    const __VLS_498 = __VLS_497({}, ...__VLS_functionalComponentArgsRest(__VLS_497));
    __VLS_499.slots.default;
    const __VLS_500 = {}.Delete;
    /** @type {[typeof __VLS_components.Delete, ]} */ ;
    // @ts-ignore
    const __VLS_501 = __VLS_asFunctionalComponent(__VLS_500, new __VLS_500({}));
    const __VLS_502 = __VLS_501({}, ...__VLS_functionalComponentArgsRest(__VLS_501));
    var __VLS_499;
}
if (__VLS_ctx.editingDramaPosters.length === 0) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "shelf-empty-hint" },
    });
}
{
    const { footer: __VLS_thisSlot } = __VLS_463.slots;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                __VLS_ctx.showEditCoverDialog = false;
            } },
        ...{ class: "apple-btn-secondary" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.confirmUpdateCover) },
        ...{ class: "apple-btn-primary" },
        id: "btn-save-drama-cover",
    });
}
var __VLS_463;
const __VLS_504 = {}.ElDialog;
/** @type {[typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, ]} */ ;
// @ts-ignore
const __VLS_505 = __VLS_asFunctionalComponent(__VLS_504, new __VLS_504({
    modelValue: (__VLS_ctx.showPostersCarouselDialog),
    title: (__VLS_ctx.activeDramaForPosters?.title + ' · 多剧照展架'),
    width: "640px",
}));
const __VLS_506 = __VLS_505({
    modelValue: (__VLS_ctx.showPostersCarouselDialog),
    title: (__VLS_ctx.activeDramaForPosters?.title + ' · 多剧照展架'),
    width: "640px",
}, ...__VLS_functionalComponentArgsRest(__VLS_505));
__VLS_507.slots.default;
if (__VLS_ctx.activeDramaForPosters?.extra_images?.length) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "posters-carousel-wrap" },
    });
    const __VLS_508 = {}.ElCarousel;
    /** @type {[typeof __VLS_components.ElCarousel, typeof __VLS_components.elCarousel, typeof __VLS_components.ElCarousel, typeof __VLS_components.elCarousel, ]} */ ;
    // @ts-ignore
    const __VLS_509 = __VLS_asFunctionalComponent(__VLS_508, new __VLS_508({
        trigger: "click",
        height: "360px",
    }));
    const __VLS_510 = __VLS_509({
        trigger: "click",
        height: "360px",
    }, ...__VLS_functionalComponentArgsRest(__VLS_509));
    __VLS_511.slots.default;
    for (const [imgUrl, idx] of __VLS_getVForSourceType((__VLS_ctx.activeDramaForPosters.extra_images))) {
        const __VLS_512 = {}.ElCarouselItem;
        /** @type {[typeof __VLS_components.ElCarouselItem, typeof __VLS_components.elCarouselItem, typeof __VLS_components.ElCarouselItem, typeof __VLS_components.elCarouselItem, ]} */ ;
        // @ts-ignore
        const __VLS_513 = __VLS_asFunctionalComponent(__VLS_512, new __VLS_512({
            key: (idx),
        }));
        const __VLS_514 = __VLS_513({
            key: (idx),
        }, ...__VLS_functionalComponentArgsRest(__VLS_513));
        __VLS_515.slots.default;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "carousel-item-img" },
            ...{ style: ({ backgroundImage: `url(${imgUrl})` }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "img-idx-pill" },
        });
        (idx + 1);
        (__VLS_ctx.activeDramaForPosters.extra_images.length);
        var __VLS_515;
    }
    var __VLS_511;
}
var __VLS_507;
const __VLS_516 = {}.ElDialog;
/** @type {[typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, ]} */ ;
// @ts-ignore
const __VLS_517 = __VLS_asFunctionalComponent(__VLS_516, new __VLS_516({
    modelValue: (__VLS_ctx.showCarouselDialog),
    title: (__VLS_ctx.isEditingCarousel ? '编辑焦点轮播' : '新增焦点轮播 (16:9 所见即所得)'),
    width: "860px",
    id: "modal-carousel",
}));
const __VLS_518 = __VLS_517({
    modelValue: (__VLS_ctx.showCarouselDialog),
    title: (__VLS_ctx.isEditingCarousel ? '编辑焦点轮播' : '新增焦点轮播 (16:9 所见即所得)'),
    width: "860px",
    id: "modal-carousel",
}, ...__VLS_functionalComponentArgsRest(__VLS_517));
__VLS_519.slots.default;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "carousel-dialog-grid" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "dialog-form" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
    ...{ onChange: (__VLS_ctx.handleModalSelectDrama) },
    value: (__VLS_ctx.selectedCarouselDramaModalId),
    ...{ class: "apple-select" },
    id: "select-carousel-drama-modal",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "",
});
for (const [d] of __VLS_getVForSourceType((__VLS_ctx.dramaOptionsList))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        key: (d.id),
        value: (d.id),
    });
    (d.title);
    (d.category || '短剧');
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ class: "apple-input" },
    placeholder: "输入吸引人的轮播焦点标题",
    id: "input-carousel-title",
});
(__VLS_ctx.carouselForm.title);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ class: "apple-input" },
    placeholder: "简短亮点说明",
    id: "input-carousel-subtitle",
});
(__VLS_ctx.carouselForm.subtitle);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ class: "apple-input" },
    placeholder: "本周爆款榜首",
    id: "input-carousel-tag",
});
(__VLS_ctx.carouselForm.tag);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ class: "apple-input" },
    placeholder: "https://...",
    id: "input-carousel-cover",
});
(__VLS_ctx.carouselForm.cover_url);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ class: "apple-input font-mono" },
    placeholder: "短剧 ID",
    id: "input-carousel-videoid",
});
(__VLS_ctx.carouselForm.video_id);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-row-grid" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    type: "number",
    ...{ class: "apple-input" },
});
(__VLS_ctx.carouselForm.sort_order);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    type: "number",
    min: "3",
    max: "20",
    ...{ class: "apple-input" },
    placeholder: "默认 5 秒",
    id: "input-carousel-duration",
});
(__VLS_ctx.carouselForm.duration_seconds);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
const __VLS_520 = {}.ElSwitch;
/** @type {[typeof __VLS_components.ElSwitch, typeof __VLS_components.elSwitch, ]} */ ;
// @ts-ignore
const __VLS_521 = __VLS_asFunctionalComponent(__VLS_520, new __VLS_520({
    modelValue: (__VLS_ctx.carouselForm.is_active),
}));
const __VLS_522 = __VLS_521({
    modelValue: (__VLS_ctx.carouselForm.is_active),
}, ...__VLS_functionalComponentArgsRest(__VLS_521));
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "dialog-preview-col" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "carousel-preview-wrapper" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "carousel-preview-container" },
    id: "carousel-preview-16-9-modal",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "aspect-16-9-box" },
});
if (__VLS_ctx.carouselForm.cover_url) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
        src: (__VLS_ctx.carouselForm.cover_url),
        ...{ class: "preview-bg-img" },
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "preview-empty-placeholder" },
    });
    const __VLS_524 = {}.ElIcon;
    /** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
    // @ts-ignore
    const __VLS_525 = __VLS_asFunctionalComponent(__VLS_524, new __VLS_524({
        size: (40),
    }));
    const __VLS_526 = __VLS_525({
        size: (40),
    }, ...__VLS_functionalComponentArgsRest(__VLS_525));
    __VLS_527.slots.default;
    const __VLS_528 = {}.Picture;
    /** @type {[typeof __VLS_components.Picture, ]} */ ;
    // @ts-ignore
    const __VLS_529 = __VLS_asFunctionalComponent(__VLS_528, new __VLS_528({}));
    const __VLS_530 = __VLS_529({}, ...__VLS_functionalComponentArgsRest(__VLS_529));
    var __VLS_527;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "preview-overlay" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "preview-tag-badge" },
});
(__VLS_ctx.carouselForm.tag || '推荐焦点');
__VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
    ...{ class: "preview-title" },
});
(__VLS_ctx.carouselForm.title || '主标题预览');
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "preview-subtitle" },
});
(__VLS_ctx.carouselForm.subtitle || '副标题亮点预览...');
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "preview-ratio-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "preview-badge-status" },
});
{
    const { footer: __VLS_thisSlot } = __VLS_519.slots;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                __VLS_ctx.showCarouselDialog = false;
            } },
        ...{ class: "apple-btn-secondary" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.saveCarousel) },
        ...{ class: "apple-btn-primary" },
        id: "btn-submit-carousel",
    });
}
var __VLS_519;
const __VLS_532 = {}.ElDialog;
/** @type {[typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, ]} */ ;
// @ts-ignore
const __VLS_533 = __VLS_asFunctionalComponent(__VLS_532, new __VLS_532({
    modelValue: (__VLS_ctx.showAddUserDialog),
    title: "创建新用户账号与特权配置",
    width: "500px",
    id: "modal-add-user",
}));
const __VLS_534 = __VLS_533({
    modelValue: (__VLS_ctx.showAddUserDialog),
    title: "创建新用户账号与特权配置",
    width: "500px",
    id: "modal-add-user",
}, ...__VLS_functionalComponentArgsRest(__VLS_533));
__VLS_535.slots.default;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "dialog-form" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "text-danger" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ class: "apple-input" },
    placeholder: "输入唯一登录账号名",
    id: "input-add-username",
});
(__VLS_ctx.addUserForm.username);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "text-danger" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    type: "password",
    ...{ class: "apple-input" },
    placeholder: "输入初始登录密码",
    id: "input-add-password",
});
(__VLS_ctx.addUserForm.password);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ class: "apple-input" },
    placeholder: "输入个性化展示昵称 (选填)",
    id: "input-add-nickname",
});
(__VLS_ctx.addUserForm.nickname);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
    value: (__VLS_ctx.addUserForm.role),
    ...{ class: "apple-select full-width" },
    id: "select-add-role",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "USER",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "CREATOR",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "REVIEWER",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "ADMIN",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-row-grid" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    type: "number",
    ...{ class: "apple-input" },
    placeholder: "默认 50",
    id: "input-add-coins",
});
(__VLS_ctx.addUserForm.coins);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    type: "number",
    ...{ class: "apple-input" },
    placeholder: "默认 0 天",
    id: "input-add-vip-days",
});
(__VLS_ctx.addUserForm.vip_days);
{
    const { footer: __VLS_thisSlot } = __VLS_535.slots;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                __VLS_ctx.showAddUserDialog = false;
            } },
        ...{ class: "apple-btn-secondary" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.confirmAddUser) },
        ...{ class: "apple-btn-primary" },
        id: "btn-submit-add-user",
    });
}
var __VLS_535;
const __VLS_536 = {}.ElDialog;
/** @type {[typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, ]} */ ;
// @ts-ignore
const __VLS_537 = __VLS_asFunctionalComponent(__VLS_536, new __VLS_536({
    modelValue: (__VLS_ctx.showEditUserDialog),
    title: "编辑用户全量资料与特权资产",
    width: "520px",
    id: "modal-edit-user",
}));
const __VLS_538 = __VLS_537({
    modelValue: (__VLS_ctx.showEditUserDialog),
    title: "编辑用户全量资料与特权资产",
    width: "520px",
    id: "modal-edit-user",
}, ...__VLS_functionalComponentArgsRest(__VLS_537));
__VLS_539.slots.default;
if (__VLS_ctx.selectedUserForEdit) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "dialog-form" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        value: (__VLS_ctx.selectedUserForEdit.username),
        ...{ class: "apple-input" },
        disabled: true,
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        ...{ class: "apple-input" },
        placeholder: "修改用户昵称",
        id: "input-edit-nickname",
    });
    (__VLS_ctx.editUserForm.nickname);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        type: "password",
        ...{ class: "apple-input" },
        placeholder: "输入新密码重置",
        id: "input-edit-password",
    });
    (__VLS_ctx.editUserForm.password);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-row-grid" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
        value: (__VLS_ctx.editUserForm.role),
        ...{ class: "apple-select full-width" },
        id: "select-edit-role",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "USER",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "CREATOR",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "REVIEWER",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "ADMIN",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
        value: (__VLS_ctx.editUserForm.status),
        ...{ class: "apple-select full-width" },
        id: "select-edit-status",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "ACTIVE",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        value: "BANNED",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-row-grid" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        type: "number",
        ...{ class: "apple-input" },
        placeholder: "0",
        id: "input-edit-coins-adj",
    });
    (__VLS_ctx.editUserForm.coins_adjustment);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "form-group" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "form-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        type: "number",
        ...{ class: "apple-input" },
        placeholder: "0",
        id: "input-edit-vip-days",
    });
    (__VLS_ctx.editUserForm.vip_days);
}
{
    const { footer: __VLS_thisSlot } = __VLS_539.slots;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                __VLS_ctx.showEditUserDialog = false;
            } },
        ...{ class: "apple-btn-secondary" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.confirmEditUser) },
        ...{ class: "apple-btn-primary" },
        id: "btn-submit-edit-user",
    });
}
var __VLS_539;
const __VLS_540 = {}.ElDialog;
/** @type {[typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, ]} */ ;
// @ts-ignore
const __VLS_541 = __VLS_asFunctionalComponent(__VLS_540, new __VLS_540({
    modelValue: (__VLS_ctx.showRoleDialog),
    title: "调整用户系统角色与权限",
    width: "400px",
}));
const __VLS_542 = __VLS_541({
    modelValue: (__VLS_ctx.showRoleDialog),
    title: "调整用户系统角色与权限",
    width: "400px",
}, ...__VLS_functionalComponentArgsRest(__VLS_541));
__VLS_543.slots.default;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "role-select-form" },
});
for (const [r] of __VLS_getVForSourceType((['USER', 'CREATOR', 'REVIEWER', 'ADMIN']))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        key: (r),
        ...{ class: "role-radio-item" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        type: "radio",
        value: (r),
    });
    (__VLS_ctx.selectedRole);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.getRoleLabel(r));
}
{
    const { footer: __VLS_thisSlot } = __VLS_543.slots;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                __VLS_ctx.showRoleDialog = false;
            } },
        ...{ class: "apple-btn-secondary" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.confirmChangeRole) },
        ...{ class: "apple-btn-primary" },
    });
}
var __VLS_543;
const __VLS_544 = {}.ElDialog;
/** @type {[typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, ]} */ ;
// @ts-ignore
const __VLS_545 = __VLS_asFunctionalComponent(__VLS_544, new __VLS_544({
    modelValue: (__VLS_ctx.showAddWordDialog),
    title: "录入社区风控敏感词",
    width: "460px",
}));
const __VLS_546 = __VLS_545({
    modelValue: (__VLS_ctx.showAddWordDialog),
    title: "录入社区风控敏感词",
    width: "460px",
}, ...__VLS_functionalComponentArgsRest(__VLS_545));
__VLS_547.slots.default;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "dialog-form" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ class: "apple-input" },
    placeholder: "输入敏感词或违禁短语",
    id: "input-modal-new-word",
});
(__VLS_ctx.newWordForm.word);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
    value: (__VLS_ctx.newWordForm.category),
    ...{ class: "apple-select" },
    id: "select-modal-new-word-category",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "违禁",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "涉政",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "暴恐",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "涉黄",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "辱骂",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "广告",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "form-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "form-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
    value: (__VLS_ctx.newWordForm.level),
    ...{ class: "apple-select" },
    id: "select-modal-new-word-level",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "HIGH",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "MEDIUM",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
    value: "LOW",
});
{
    const { footer: __VLS_thisSlot } = __VLS_547.slots;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                __VLS_ctx.showAddWordDialog = false;
            } },
        ...{ class: "apple-btn-secondary" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.confirmAddSensitiveWord) },
        ...{ class: "apple-btn-primary" },
        disabled: (!__VLS_ctx.newWordForm.word.trim()),
        id: "btn-confirm-add-word",
    });
}
var __VLS_547;
/** @type {__VLS_StyleScopedClasses['admin-page-root']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-layout-wrapper']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-ambient-bg']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-orb']} */ ;
/** @type {__VLS_StyleScopedClasses['orb-1']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-orb']} */ ;
/** @type {__VLS_StyleScopedClasses['orb-2']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-sidebar']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-header']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-brand']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-text']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-name']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-brand-collapsed']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-pin-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-nav-scroll']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-group-title']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-tab-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-label']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-group-title']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-tab-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-label']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-tab-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-label']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-group-title']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-tab-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-label']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-group-title']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-tab-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-label']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-tab-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-label']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-group-title']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-tab-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-label']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-group-title']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-tab-item']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-label']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-main-stage']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-top-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['bar-left']} */ ;
/** @type {__VLS_StyleScopedClasses['bar-breadcrumb']} */ ;
/** @type {__VLS_StyleScopedClasses['bar-headline']} */ ;
/** @type {__VLS_StyleScopedClasses['bar-right']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['content-section']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-header']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-title']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['blue']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-number']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-header']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-title']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['cyan']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-number']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-header']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-title']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['purple']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-number']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-header']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-title']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['pink']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-number']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-header']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-title']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['indigo']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-number']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-header']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-title']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['green']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-number']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-header']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-title']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['amber']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-number']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-header']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-title']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['red']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-number']} */ ;
/** @type {__VLS_StyleScopedClasses['kpi-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-block']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-header']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-title-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-legend-pills']} */ ;
/** @type {__VLS_StyleScopedClasses['legend-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['history']} */ ;
/** @type {__VLS_StyleScopedClasses['dot']} */ ;
/** @type {__VLS_StyleScopedClasses['history']} */ ;
/** @type {__VLS_StyleScopedClasses['legend-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['forecast']} */ ;
/** @type {__VLS_StyleScopedClasses['dot']} */ ;
/** @type {__VLS_StyleScopedClasses['forecast']} */ ;
/** @type {__VLS_StyleScopedClasses['legend-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['bound']} */ ;
/** @type {__VLS_StyleScopedClasses['dot']} */ ;
/** @type {__VLS_StyleScopedClasses['bound']} */ ;
/** @type {__VLS_StyleScopedClasses['echarts-container']} */ ;
/** @type {__VLS_StyleScopedClasses['viral-ranking-block']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['block-header']} */ ;
/** @type {__VLS_StyleScopedClasses['title-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['block-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['viral-table-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table']} */ ;
/** @type {__VLS_StyleScopedClasses['rank-index']} */ ;
/** @type {__VLS_StyleScopedClasses['font-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['tag-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['score-progress-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['score-val']} */ ;
/** @type {__VLS_StyleScopedClasses['score-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['score-fill']} */ ;
/** @type {__VLS_StyleScopedClasses['status-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['growth-text']} */ ;
/** @type {__VLS_StyleScopedClasses['content-section']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['search-box']} */ ;
/** @type {__VLS_StyleScopedClasses['table-search-input']} */ ;
/** @type {__VLS_StyleScopedClasses['table-header-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-counter']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table-viewport-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table']} */ ;
/** @type {__VLS_StyleScopedClasses['table-row']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-card']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-thumb-wrapper']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-thumb-img']} */ ;
/** @type {__VLS_StyleScopedClasses['multi-poster-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-title-main']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-synopsis-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['tag-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['stats-mini-line']} */ ;
/** @type {__VLS_StyleScopedClasses['status-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['actions-group']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-danger']} */ ;
/** @type {__VLS_StyleScopedClasses['table-pagination-row']} */ ;
/** @type {__VLS_StyleScopedClasses['content-section']} */ ;
/** @type {__VLS_StyleScopedClasses['sync-dashboard-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['sync-config-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-header-styled']} */ ;
/** @type {__VLS_StyleScopedClasses['head-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['sync-mode-selector']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-radio-box']} */ ;
/** @type {__VLS_StyleScopedClasses['radio-content']} */ ;
/** @type {__VLS_StyleScopedClasses['radio-title-row']} */ ;
/** @type {__VLS_StyleScopedClasses['radio-name']} */ ;
/** @type {__VLS_StyleScopedClasses['recommend-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['radio-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-radio-box']} */ ;
/** @type {__VLS_StyleScopedClasses['radio-content']} */ ;
/** @type {__VLS_StyleScopedClasses['radio-title-row']} */ ;
/** @type {__VLS_StyleScopedClasses['radio-name']} */ ;
/** @type {__VLS_StyleScopedClasses['radio-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['sync-action-row']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['big-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['sync-report-card']} */ ;
/** @type {__VLS_StyleScopedClasses['report-header']} */ ;
/** @type {__VLS_StyleScopedClasses['report-status-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['report-mode-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['report-stats-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['report-stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['num']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['report-stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['num']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['report-stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['num']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['report-stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['num']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['sync-telemetry-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['telemetry-list']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-row']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-label']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-val']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-row']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-label']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-val']} */ ;
/** @type {__VLS_StyleScopedClasses['font-mono']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-row']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-label']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-val']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-row']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-label']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-val']} */ ;
/** @type {__VLS_StyleScopedClasses['font-mono']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-row']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-label']} */ ;
/** @type {__VLS_StyleScopedClasses['telem-val']} */ ;
/** @type {__VLS_StyleScopedClasses['font-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['text-success']} */ ;
/** @type {__VLS_StyleScopedClasses['content-section']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-workbench-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['workbench-header']} */ ;
/** @type {__VLS_StyleScopedClasses['workbench-title-box']} */ ;
/** @type {__VLS_StyleScopedClasses['head-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['text-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['workbench-quick-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-select']} */ ;
/** @type {__VLS_StyleScopedClasses['workbench-select']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-live-preview-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-preview-wrapper']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-preview-container']} */ ;
/** @type {__VLS_StyleScopedClasses['aspect-16-9-box']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-bg-img']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-empty-placeholder']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-tag-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-title']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-subtitle']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-ratio-label']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-badge-status']} */ ;
/** @type {__VLS_StyleScopedClasses['workbench-quick-info']} */ ;
/** @type {__VLS_StyleScopedClasses['info-title']} */ ;
/** @type {__VLS_StyleScopedClasses['info-list']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table']} */ ;
/** @type {__VLS_StyleScopedClasses['table-row']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-preview-img']} */ ;
/** @type {__VLS_StyleScopedClasses['font-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-text-col']} */ ;
/** @type {__VLS_StyleScopedClasses['tag-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['font-mono']} */ ;
/** @type {__VLS_StyleScopedClasses['text-xs']} */ ;
/** @type {__VLS_StyleScopedClasses['actions-group']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-danger']} */ ;
/** @type {__VLS_StyleScopedClasses['content-section']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['user-toolbar-header']} */ ;
/** @type {__VLS_StyleScopedClasses['user-filters-group']} */ ;
/** @type {__VLS_StyleScopedClasses['search-box']} */ ;
/** @type {__VLS_StyleScopedClasses['table-search-input']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-select']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-select']} */ ;
/** @type {__VLS_StyleScopedClasses['table-header-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-counter']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table-viewport-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table']} */ ;
/** @type {__VLS_StyleScopedClasses['table-row']} */ ;
/** @type {__VLS_StyleScopedClasses['font-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['role-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['privilege-tags']} */ ;
/** @type {__VLS_StyleScopedClasses['priv-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['creator']} */ ;
/** @type {__VLS_StyleScopedClasses['priv-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['reviewer']} */ ;
/** @type {__VLS_StyleScopedClasses['priv-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['guest']} */ ;
/** @type {__VLS_StyleScopedClasses['economy-summary-cell']} */ ;
/** @type {__VLS_StyleScopedClasses['coin-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['vip-tag-active']} */ ;
/** @type {__VLS_StyleScopedClasses['vip-tag-none']} */ ;
/** @type {__VLS_StyleScopedClasses['status-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-text-col']} */ ;
/** @type {__VLS_StyleScopedClasses['actions-group']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-danger']} */ ;
/** @type {__VLS_StyleScopedClasses['table-pagination-row']} */ ;
/** @type {__VLS_StyleScopedClasses['content-section']} */ ;
/** @type {__VLS_StyleScopedClasses['dual-subtabs-row']} */ ;
/** @type {__VLS_StyleScopedClasses['subtab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['subtab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table']} */ ;
/** @type {__VLS_StyleScopedClasses['font-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-text-col']} */ ;
/** @type {__VLS_StyleScopedClasses['status-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['warning']} */ ;
/** @type {__VLS_StyleScopedClasses['actions-group']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-table-cell']} */ ;
/** @type {__VLS_StyleScopedClasses['content-section']} */ ;
/** @type {__VLS_StyleScopedClasses['dual-subtabs-row']} */ ;
/** @type {__VLS_StyleScopedClasses['subtab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['subtab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['subtab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['subtab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-counter']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table']} */ ;
/** @type {__VLS_StyleScopedClasses['priv-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['font-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['violation-reason-cell']} */ ;
/** @type {__VLS_StyleScopedClasses['raw-snippet']} */ ;
/** @type {__VLS_StyleScopedClasses['matched-words-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['risk-pill-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['high']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-text-col']} */ ;
/** @type {__VLS_StyleScopedClasses['status-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-text-col']} */ ;
/** @type {__VLS_StyleScopedClasses['actions-group']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-danger']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-table-cell']} */ ;
/** @type {__VLS_StyleScopedClasses['lexicon-composite-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['lexicon-filters-row']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['search-input']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-select']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-select']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table']} */ ;
/** @type {__VLS_StyleScopedClasses['font-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['font-mono']} */ ;
/** @type {__VLS_StyleScopedClasses['priv-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['creator']} */ ;
/** @type {__VLS_StyleScopedClasses['status-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-text-col']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-danger']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-table-cell']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['dfa-sandbox-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-header-styled']} */ ;
/** @type {__VLS_StyleScopedClasses['head-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['sandbox-body']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-textarea']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['full-width']} */ ;
/** @type {__VLS_StyleScopedClasses['sandbox-result-box']} */ ;
/** @type {__VLS_StyleScopedClasses['result-status-row']} */ ;
/** @type {__VLS_StyleScopedClasses['status-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['risk-tag-text']} */ ;
/** @type {__VLS_StyleScopedClasses['result-detail-line']} */ ;
/** @type {__VLS_StyleScopedClasses['detail-label']} */ ;
/** @type {__VLS_StyleScopedClasses['risk-pill-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['high']} */ ;
/** @type {__VLS_StyleScopedClasses['result-detail-line']} */ ;
/** @type {__VLS_StyleScopedClasses['detail-label']} */ ;
/** @type {__VLS_StyleScopedClasses['sanitized-code']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-danger']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table']} */ ;
/** @type {__VLS_StyleScopedClasses['font-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-text-col']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-danger']} */ ;
/** @type {__VLS_StyleScopedClasses['table-card']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-table']} */ ;
/** @type {__VLS_StyleScopedClasses['font-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-text-col']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-danger']} */ ;
/** @type {__VLS_StyleScopedClasses['content-section']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-config-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-header-styled']} */ ;
/** @type {__VLS_StyleScopedClasses['head-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['chart-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['engine-form']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-textarea']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['dialog-form']} */ ;
/** @type {__VLS_StyleScopedClasses['cover-governance-form']} */ ;
/** @type {__VLS_StyleScopedClasses['form-row-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-row-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['full-width']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-textarea']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['full-width']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['cover-preview-box']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-img']} */ ;
/** @type {__VLS_StyleScopedClasses['dashed-micro-glow-placeholder']} */ ;
/** @type {__VLS_StyleScopedClasses['placeholder-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['placeholder-text']} */ ;
/** @type {__VLS_StyleScopedClasses['main-tip']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-tip']} */ ;
/** @type {__VLS_StyleScopedClasses['cover-hover-prompt']} */ ;
/** @type {__VLS_StyleScopedClasses['cover-url-manual-row']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['text-xs']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['full-width']} */ ;
/** @type {__VLS_StyleScopedClasses['shelf-header-row']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['posters-shelf-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['poster-shelf-card']} */ ;
/** @type {__VLS_StyleScopedClasses['shelf-thumb']} */ ;
/** @type {__VLS_StyleScopedClasses['shelf-card-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['shelf-main-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['shelf-btn-set-main']} */ ;
/** @type {__VLS_StyleScopedClasses['shelf-btn-del']} */ ;
/** @type {__VLS_StyleScopedClasses['shelf-empty-hint']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['posters-carousel-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-item-img']} */ ;
/** @type {__VLS_StyleScopedClasses['img-idx-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-dialog-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['dialog-form']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-select']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['font-mono']} */ ;
/** @type {__VLS_StyleScopedClasses['form-row-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['dialog-preview-col']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-preview-wrapper']} */ ;
/** @type {__VLS_StyleScopedClasses['carousel-preview-container']} */ ;
/** @type {__VLS_StyleScopedClasses['aspect-16-9-box']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-bg-img']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-empty-placeholder']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-tag-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-title']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-subtitle']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-ratio-label']} */ ;
/** @type {__VLS_StyleScopedClasses['preview-badge-status']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['dialog-form']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['text-danger']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['text-danger']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-select']} */ ;
/** @type {__VLS_StyleScopedClasses['full-width']} */ ;
/** @type {__VLS_StyleScopedClasses['form-row-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['dialog-form']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-row-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-select']} */ ;
/** @type {__VLS_StyleScopedClasses['full-width']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-select']} */ ;
/** @type {__VLS_StyleScopedClasses['full-width']} */ ;
/** @type {__VLS_StyleScopedClasses['form-row-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['role-select-form']} */ ;
/** @type {__VLS_StyleScopedClasses['role-radio-item']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['dialog-form']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-select']} */ ;
/** @type {__VLS_StyleScopedClasses['form-group']} */ ;
/** @type {__VLS_StyleScopedClasses['form-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-select']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-primary']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            AdminHeader: AdminHeader,
            DataLine: DataLine,
            TrendCharts: TrendCharts,
            Film: Film,
            Refresh: Refresh,
            Picture: Picture,
            User: User,
            Check: Check,
            Close: Close,
            Setting: Setting,
            Search: Search,
            Delete: Delete,
            Edit: Edit,
            Plus: Plus,
            Switch: Switch,
            Lock: Lock,
            Unlock: Unlock,
            View: View,
            Hide: Hide,
            Fold: Fold,
            Expand: Expand,
            DocumentChecked: DocumentChecked,
            ChatLineSquare: ChatLineSquare,
            Rank: Rank,
            Upload: Upload,
            Promotion: Promotion,
            isSidebarPinned: isSidebarPinned,
            isSidebarExpanded: isSidebarExpanded,
            onSidebarMouseEnter: onSidebarMouseEnter,
            onSidebarMouseLeave: onSidebarMouseLeave,
            toggleSidebarPin: toggleSidebarPin,
            currentTab: currentTab,
            currentTabTitle: currentTabTitle,
            selectTab: selectTab,
            loading: loading,
            biMetrics: biMetrics,
            biChartRef: biChartRef,
            viralRankings: viralRankings,
            dramaSearchKeyword: dramaSearchKeyword,
            dramaPage: dramaPage,
            dramaPageSize: dramaPageSize,
            selectedDramaIds: selectedDramaIds,
            defaultDramaPoster: defaultDramaPoster,
            filteredDramas: filteredDramas,
            paginatedDramas: paginatedDramas,
            isAllDramasSelected: isAllDramasSelected,
            toggleSelectAllDramas: toggleSelectAllDramas,
            handleBatchDeleteDramas: handleBatchDeleteDramas,
            showEditCoverDialog: showEditCoverDialog,
            editingCoverUrl: editingCoverUrl,
            editingDramaPosters: editingDramaPosters,
            editingDramaMeta: editingDramaMeta,
            imageUploadInputRef: imageUploadInputRef,
            isCoverDragOver: isCoverDragOver,
            coverImgError: coverImgError,
            showPostersCarouselDialog: showPostersCarouselDialog,
            activeDramaForPosters: activeDramaForPosters,
            syncMode: syncMode,
            isSyncing: isSyncing,
            syncResult: syncResult,
            carouselsList: carouselsList,
            showCarouselDialog: showCarouselDialog,
            isEditingCarousel: isEditingCarousel,
            dramaOptionsList: dramaOptionsList,
            selectedCarouselDramaId: selectedCarouselDramaId,
            selectedCarouselDramaModalId: selectedCarouselDramaModalId,
            workbenchImgError: workbenchImgError,
            carouselForm: carouselForm,
            workbenchPreviewCover: workbenchPreviewCover,
            workbenchPreviewTitle: workbenchPreviewTitle,
            workbenchPreviewSubtitle: workbenchPreviewSubtitle,
            workbenchPreviewTag: workbenchPreviewTag,
            usersList: usersList,
            userSearchKeyword: userSearchKeyword,
            userFilterRole: userFilterRole,
            userFilterStatus: userFilterStatus,
            userTotalCount: userTotalCount,
            userPage: userPage,
            userPageSize: userPageSize,
            selectedUserIds: selectedUserIds,
            isAllUsersSelected: isAllUsersSelected,
            toggleSelectAllUsers: toggleSelectAllUsers,
            handleBatchDeleteUsers: handleBatchDeleteUsers,
            showRoleDialog: showRoleDialog,
            selectedRole: selectedRole,
            showAddUserDialog: showAddUserDialog,
            addUserForm: addUserForm,
            showEditUserDialog: showEditUserDialog,
            selectedUserForEdit: selectedUserForEdit,
            editUserForm: editUserForm,
            applicationSubTab: applicationSubTab,
            pendingCreators: pendingCreators,
            pendingReviewers: pendingReviewers,
            pendingCount: pendingCount,
            contentSubTab: contentSubTab,
            reviewQueueList: reviewQueueList,
            sensitiveWordsList: sensitiveWordsList,
            sensitiveWordsTotal: sensitiveWordsTotal,
            sensitiveWordSearch: sensitiveWordSearch,
            sensitiveWordCategory: sensitiveWordCategory,
            sensitiveWordLevel: sensitiveWordLevel,
            showAddWordDialog: showAddWordDialog,
            newWordForm: newWordForm,
            dfaTestText: dfaTestText,
            dfaTestResult: dfaTestResult,
            dfaTesting: dfaTesting,
            danmakusList: danmakusList,
            selectedDanmakuIds: selectedDanmakuIds,
            danmakuSearchQuery: danmakuSearchQuery,
            commentsList: commentsList,
            engineForm: engineForm,
            refreshCurrentTab: refreshCurrentTab,
            filterDramas: filterDramas,
            toggleDramaStatus: toggleDramaStatus,
            openEditCoverModal: openEditCoverModal,
            triggerUploadImage: triggerUploadImage,
            handleImageFileSelected: handleImageFileSelected,
            handleCoverDrop: handleCoverDrop,
            setAsMainCover: setAsMainCover,
            removePoster: removePoster,
            confirmUpdateCover: confirmUpdateCover,
            openPosterCarousel: openPosterCarousel,
            handleDeleteDrama: handleDeleteDrama,
            openSyncDialog: openSyncDialog,
            executeSync: executeSync,
            handleQuickSelectDrama: handleQuickSelectDrama,
            applyWorkbenchToModal: applyWorkbenchToModal,
            handleModalSelectDrama: handleModalSelectDrama,
            openCreateCarouselModal: openCreateCarouselModal,
            openEditCarouselModal: openEditCarouselModal,
            saveCarousel: saveCarousel,
            handleToggleCarouselActive: handleToggleCarouselActive,
            handleDeleteCarousel: handleDeleteCarousel,
            loadUsers: loadUsers,
            openAddUserModal: openAddUserModal,
            confirmAddUser: confirmAddUser,
            openEditUserModal: openEditUserModal,
            confirmEditUser: confirmEditUser,
            handleDeleteUser: handleDeleteUser,
            openRoleModal: openRoleModal,
            confirmChangeRole: confirmChangeRole,
            toggleUserStatus: toggleUserStatus,
            handleApproveApplication: handleApproveApplication,
            handleRejectApplication: handleRejectApplication,
            switchContentSubTab: switchContentSubTab,
            handleReviewDecision: handleReviewDecision,
            loadSensitiveWords: loadSensitiveWords,
            openAddWordModal: openAddWordModal,
            confirmAddSensitiveWord: confirmAddSensitiveWord,
            handleDeleteSensitiveWord: handleDeleteSensitiveWord,
            runDfaTest: runDfaTest,
            fetchDanmakus: fetchDanmakus,
            toggleSelectAllDanmakus: toggleSelectAllDanmakus,
            handleBatchDeleteDanmakus: handleBatchDeleteDanmakus,
            handleDeleteDanmaku: handleDeleteDanmaku,
            handleDeleteComment: handleDeleteComment,
            saveEngineConfig: saveEngineConfig,
            getRoleLabel: getRoleLabel,
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
//# sourceMappingURL=AdminView.vue.js.map