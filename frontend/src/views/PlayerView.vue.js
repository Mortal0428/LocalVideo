/// <reference types="../../node_modules/.vue-global-types/vue_3.5_0_0_0.d.ts" />
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { videoApi } from '../api/video';
import { authApi } from '../api/auth';
import { favoritesApi } from '../api/favorites';
import { userApi, notificationApi } from '../api/user';
import { useUserStore } from '../stores/user';
import { Bell } from '@element-plus/icons-vue';
import NotificationSkylight from '../components/NotificationSkylight.vue';
const route = useRoute();
const props = defineProps();
const userStore = useUserStore();
const defaultAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=apple';
const defaultCover = 'https://images.unsplash.com/photo-1518173946687-a4c8a383392e?w=800&q=80';
// State
const videoRef = ref(null);
const chatScrollRef = ref(null);
const displayMode = ref('landscape');
const activeTab = ref('episodes');
const isWebFullscreen = ref(false);
const isSidebarCollapsed = ref(false);
function toggleWebFullscreen() {
    isWebFullscreen.value = !isWebFullscreen.value;
}
function toggleNativeFullscreen() {
    const container = document.getElementById('widescreen-player-box') || videoRef.value;
    if (!container)
        return;
    if (!document.fullscreenElement) {
        if (container.requestFullscreen) {
            container.requestFullscreen();
        }
        else if (container.webkitRequestFullscreen) {
            container.webkitRequestFullscreen();
        }
    }
    else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}
// Continuous Autoplay State (persisted to localStorage)
const isAutoplayEnabled = ref(true);
const showCountdownHud = ref(false);
const countdownSeconds = ref(5);
let countdownTimer = null;
function initAutoplaySetting() {
    const p1 = localStorage.getItem('cinema_player_autoplay');
    const p2 = localStorage.getItem('cinema_autoplay_enabled');
    if (p1 !== null) {
        isAutoplayEnabled.value = p1 !== 'false';
    }
    else if (p2 !== null) {
        isAutoplayEnabled.value = p2 !== 'false';
    }
    else {
        isAutoplayEnabled.value = true;
    }
    localStorage.setItem('cinema_player_autoplay', String(isAutoplayEnabled.value));
    localStorage.setItem('cinema_autoplay_enabled', String(isAutoplayEnabled.value));
}
function toggleAutoplay() {
    isAutoplayEnabled.value = !isAutoplayEnabled.value;
    localStorage.setItem('cinema_player_autoplay', String(isAutoplayEnabled.value));
    localStorage.setItem('cinema_autoplay_enabled', String(isAutoplayEnabled.value));
}
// Multi-level Favorites State
const isFavorited = ref(false);
const favoriteCount = ref(980);
const showFavoriteModal = ref(false);
const userFolders = ref([]);
const selectedFolderIds = ref([]);
const showNewFolderInput = ref(false);
const newFolderName = ref('');
const newFolderIsPublic = ref(false);
const isSavingFavorite = ref(false);
// Coin Economy & Tipping State (Feature 20)
const showCoinModal = ref(false);
const videoCoinCount = ref(2140);
const userWalletBalance = ref(50);
const userTippedCount = ref(0);
const isTipping = ref(false);
const tipSuccessTip = ref('');
// Playback Rate & Resolution Controls
const currentRate = ref(1.0);
const showSpeedMenu = ref(false);
const currentResolution = ref('1080P 超清');
const showResMenu = ref(false);
let speedMenuTimer = null;
let resMenuTimer = null;
function openSpeedMenu() {
    if (speedMenuTimer)
        clearTimeout(speedMenuTimer);
    showSpeedMenu.value = true;
}
function closeSpeedMenuDebounced() {
    if (speedMenuTimer)
        clearTimeout(speedMenuTimer);
    speedMenuTimer = setTimeout(() => {
        showSpeedMenu.value = false;
    }, 250);
}
function openResMenu() {
    if (resMenuTimer)
        clearTimeout(resMenuTimer);
    showResMenu.value = true;
}
function closeResMenuDebounced() {
    if (resMenuTimer)
        clearTimeout(resMenuTimer);
    resMenuTimer = setTimeout(() => {
        showResMenu.value = false;
    }, 250);
}
function setPlaybackRate(rate) {
    currentRate.value = rate;
    if (videoRef.value) {
        videoRef.value.playbackRate = rate;
    }
    showSpeedMenu.value = false;
}
function setResolution(res) {
    currentResolution.value = res;
    showResMenu.value = false;
}
const highlights = ref([]);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const progressPercent = ref(0);
const album = ref(null);
const episodes = ref([]);
const currentEpisode = ref(null);
const currentStreamUrl = ref('');
// Episode Chunking Logic (1-50, 51-100, 全部)
const selectedChunk = ref('1-50');
const episodeChunks = computed(() => {
    const total = episodes.value.length;
    if (total <= 50)
        return [];
    const chunks = [];
    const step = 50;
    for (let i = 1; i <= total; i += step) {
        const end = Math.min(i + step - 1, total);
        chunks.push({
            label: `${i}-${end}`,
            start: i,
            end: end
        });
    }
    chunks.push({ label: '全部', start: 1, end: total });
    return chunks;
});
const visibleEpisodes = computed(() => {
    if (episodeChunks.value.length === 0 || selectedChunk.value === '全部') {
        return episodes.value;
    }
    const chunk = episodeChunks.value.find(c => c.label === selectedChunk.value);
    if (!chunk)
        return episodes.value;
    return episodes.value.filter(ep => ep.episode_num >= chunk.start && ep.episode_num <= chunk.end);
});
const isLiked = ref(false);
const likeCount = ref(0);
const resumeToast = ref('');
// Notification Skylight State
const showSkylightDrawer = ref(false);
const unreadCounts = ref({ total: 0, announcements: 0, replies: 0, likes: 0 });
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
// Two-Tier Comments State
const comments = ref([]);
const commentsTotal = ref(0);
const commentText = ref('');
const isSubmittingComment = ref(false);
const activeReplyRootId = ref('');
const activeReplyTargetUserId = ref('');
const replyTargetName = ref('');
const replyText = ref('');
const isSubmittingReply = ref(false);
const highlightedCommentId = ref('');
function formatNumber(val) {
    if (!val)
        return '0';
    if (val >= 10000) {
        return (val / 10000).toFixed(1) + '万';
    }
    return val.toLocaleString();
}
// Danmaku
const danmakuInputText = ref('');
const activeDanmakus = ref([]);
let danmakuWs = null;
// Companion Agent State
const agentInputText = ref('');
const isStreamingAgent = ref(false);
const quickPrompts = ref([
    '本集的核心矛盾反转是什么？',
    '为什么主角会在此时出手？',
    '跳到本集最精彩的高能名场面'
]);
const agentMessages = ref([
    {
        sender: 'agent',
        text: '您好！我是您的智能短剧伴读 Agent。在观影过程中，您可以随时提问剧情矛盾、人物动机、台词细节或画面感知，我会为您智能解构并提供秒级精准跳转！',
        targetTime: 25,
        timeTag: '00:25',
        scene: '主角登场高能瞬间'
    }
]);
// Review Queue
const reviewQueue = ref([]);
// Auth state
const currentUser = userStore.currentUser;
const showAuthModal = ref(false);
const authMode = ref('login');
const authForm = ref({ username: '', password: '' });
onMounted(async () => {
    initAutoplaySetting();
    await restoreUserSession();
    await fetchUnreadCount();
    const videoId = route.params.id || route.query.videoId || 'latest';
    await loadVideoData(videoId);
});
watch(() => [route.params.id, route.query.videoId, route.query.episodeId], async ([newId, newQId, newEpId]) => {
    const targetId = newId || newQId;
    if (targetId && targetId !== album.value?.id) {
        await loadVideoData(targetId);
    }
    else if (newEpId && episodes.value.length > 0) {
        const matched = episodes.value.find(e => e.id === newEpId);
        if (matched && matched.id !== currentEpisode.value?.id) {
            selectEpisode(matched);
        }
    }
});
onUnmounted(() => {
    reportHeartbeat(true);
    closeDanmakuWs();
    if (countdownTimer) {
        clearInterval(countdownTimer);
        countdownTimer = null;
    }
});
async function restoreUserSession() {
    await userStore.refreshProfile();
    await fetchUnreadCount();
}
async function loadVideoData(videoId) {
    try {
        const res = await videoApi.getAlbum(videoId);
        if (res?.data) {
            album.value = res.data;
            episodes.value = res.data.episodes || [];
            if (episodes.value.length > 0) {
                const targetEpId = route.query.episodeId;
                let chosenEp = episodes.value[0];
                if (targetEpId) {
                    const matched = episodes.value.find(e => e.id === targetEpId);
                    if (matched)
                        chosenEp = matched;
                }
                selectEpisode(chosenEp);
            }
            await checkFavoriteStatus(res.data.id);
        }
        else {
            setupMockAlbum(videoId);
        }
    }
    catch (err) {
        console.warn('Failed to load remote album, using local fallback:', err);
        setupMockAlbum(videoId);
    }
}
function setupMockAlbum(videoId) {
    album.value = {
        id: videoId,
        title: '【乘风2026】绝美舞台合唱瞬间',
        summary: '中国联通沃盘超清原画直连，视听大厅精选高能剧目。',
        category: '都市逆袭',
        cover_url: 'https://images.unsplash.com/photo-1518173946687-a4c8a383392e?w=800&q=80',
        episodes: [
            { id: 'ef96c393-0bab-43b5-9cf8-b0c8d065b0ba', episode_num: 1, title: '雨爱初相遇', stream_url: `/api/v1/videos/stream/ef96c393-0bab-43b5-9cf8-b0c8d065b0ba`, duration_seconds: 165, transcode_status: 'READY' },
            { id: '25320389-d52b-4696-be3f-6f064df91eb0', episode_num: 2, title: '风暴中的抉择', stream_url: `/api/v1/videos/stream/25320389-d52b-4696-be3f-6f064df91eb0`, duration_seconds: 180, transcode_status: 'READY' },
            { id: '7c819230-1123-4819-bf39-2a90184e9123', episode_num: 3, title: '荣耀与新生', stream_url: `/api/v1/videos/stream/7c819230-1123-4819-bf39-2a90184e9123`, duration_seconds: 195, transcode_status: 'READY' }
        ]
    };
    episodes.value = album.value.episodes || [];
    if (episodes.value.length > 0) {
        const targetEpId = route.query.episodeId;
        let chosenEp = episodes.value[0];
        if (targetEpId) {
            const matched = episodes.value.find(e => e.id === targetEpId);
            if (matched)
                chosenEp = matched;
        }
        selectEpisode(chosenEp);
    }
}
async function selectEpisode(ep) {
    // Save heartbeat for previous episode before switching
    if (currentEpisode.value && currentEpisode.value.id !== ep.id) {
        reportHeartbeat(true);
    }
    currentEpisode.value = ep;
    currentStreamUrl.value = ep.stream_url || `/api/v1/videos/stream/${ep.id}`;
    initDanmakuWs(ep.id);
    loadEpisodeHighlightsAndPrompts(ep.id);
    // Real watch history auto-resume from URL query or database
    let seekSec = 0;
    if (route.query.time && Number(route.query.time) > 0) {
        seekSec = Number(route.query.time);
    }
    else {
        try {
            const hRes = await videoApi.getHistory(ep.id);
            if (hRes?.data?.progress_seconds && hRes.data.progress_seconds > 0) {
                seekSec = Math.floor(hRes.data.progress_seconds);
            }
        }
        catch (err) { }
    }
    if (seekSec > 0) {
        nextTick(() => {
            if (videoRef.value) {
                videoRef.value.currentTime = seekSec;
            }
        });
        resumeToast.value = `已为您自动续播至上次观看进度 ${formatSeconds(seekSec)}`;
        setTimeout(() => {
            resumeToast.value = '';
        }, 4000);
    }
    // Fetch real persistent like status & real two-tier comments from backend
    await loadEpisodeLikeStatus(ep.id);
    await loadEpisodeComments(ep.id);
    await loadEpisodeTipStatus(ep.id);
    // Immediate initial heartbeat report for watch history persistence
    setTimeout(() => {
        reportHeartbeat(true);
    }, 800);
}
async function loadEpisodeHighlightsAndPrompts(episodeId) {
    try {
        const res = await videoApi.getHighlights(episodeId);
        if (res?.data && res.data.length > 0) {
            highlights.value = res.data.map((h) => ({
                time: h.time,
                timeTag: h.timeTag,
                title: h.title,
                desc: h.desc,
                tag: h.tag || '高能时刻'
            }));
        }
    }
    catch (e) {
        console.warn('Load highlights failed:', e);
    }
    try {
        const pRes = await videoApi.getQuickPrompts(episodeId);
        if (pRes?.data && pRes.data.length > 0) {
            quickPrompts.value = pRes.data;
        }
    }
    catch (e) {
        console.warn('Load quick prompts failed:', e);
    }
}
const nextEpisode = computed(() => {
    if (!currentEpisode.value || episodes.value.length === 0)
        return null;
    const currentIdx = episodes.value.findIndex(e => e.id === currentEpisode.value?.id);
    if (currentIdx >= 0 && currentIdx < episodes.value.length - 1) {
        return episodes.value[currentIdx + 1];
    }
    return null;
});
function startCountdownAutoplay() {
    if (!nextEpisode.value)
        return;
    showCountdownHud.value = true;
    countdownSeconds.value = 5;
    if (countdownTimer)
        clearInterval(countdownTimer);
    countdownTimer = setInterval(() => {
        countdownSeconds.value -= 1;
        if (countdownSeconds.value <= 0) {
            clearInterval(countdownTimer);
            countdownTimer = null;
            executeNextEpisodeImmediately();
        }
    }, 1000);
}
function executeNextEpisodeImmediately() {
    if (countdownTimer) {
        clearInterval(countdownTimer);
        countdownTimer = null;
    }
    showCountdownHud.value = false;
    if (nextEpisode.value) {
        switchEpisodeSeamlessly(nextEpisode.value);
    }
}
function cancelCountdownAutoplay() {
    if (countdownTimer) {
        clearInterval(countdownTimer);
        countdownTimer = null;
    }
    showCountdownHud.value = false;
    isPlaying.value = false;
    if (videoRef.value) {
        videoRef.value.pause();
    }
}
function switchEpisodeSeamlessly(ep) {
    const savedRate = currentRate.value;
    const savedVolume = videoRef.value ? videoRef.value.volume : 1.0;
    const savedMuted = videoRef.value ? videoRef.value.muted : false;
    selectEpisode(ep);
    nextTick(() => {
        if (videoRef.value) {
            videoRef.value.playbackRate = savedRate;
            videoRef.value.volume = savedVolume;
            videoRef.value.muted = savedMuted;
            videoRef.value.currentTime = 0;
            videoRef.value.play().then(() => {
                isPlaying.value = true;
                if (videoRef.value) {
                    videoRef.value.playbackRate = savedRate;
                }
            }).catch(err => {
                console.warn('Playback resume error:', err);
            });
        }
    });
}
function switchEpisode(ep) {
    switchEpisodeSeamlessly(ep);
}
function togglePlay() {
    if (!videoRef.value)
        return;
    if (videoRef.value.paused) {
        videoRef.value.play().then(() => {
            isPlaying.value = true;
            reportHeartbeat(true);
        }).catch(err => {
            console.warn('Autoplay prevented:', err);
        });
    }
    else {
        videoRef.value.pause();
        isPlaying.value = false;
        reportHeartbeat(true);
    }
}
let lastHeartbeatTime = 0;
async function reportHeartbeat(force = false) {
    if (!currentEpisode.value?.id)
        return;
    const cur = Math.floor(currentTime.value);
    if (!force && Math.abs(cur - lastHeartbeatTime) < 5)
        return;
    lastHeartbeatTime = cur;
    try {
        await videoApi.sendHeartbeat(currentEpisode.value.id, cur);
    }
    catch (err) {
        // Guest or offline
    }
}
function onTimeUpdate() {
    if (!videoRef.value)
        return;
    currentTime.value = videoRef.value.currentTime;
    if (duration.value > 0) {
        progressPercent.value = (currentTime.value / duration.value) * 100;
    }
    reportHeartbeat(false);
}
function onLoadedMetadata() {
    if (!videoRef.value)
        return;
    duration.value = videoRef.value.duration || 165;
    // Crucial: preserve playbackRate across source switch
    if (currentRate.value) {
        videoRef.value.playbackRate = currentRate.value;
    }
}
function onVideoEnded() {
    isPlaying.value = false;
    reportHeartbeat(true);
    if (isAutoplayEnabled.value && nextEpisode.value) {
        startCountdownAutoplay();
    }
}
function handleSeekClick(e) {
    const track = e.currentTarget;
    const rect = track.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, clickX / rect.width));
    if (videoRef.value && duration.value > 0) {
        videoRef.value.currentTime = ratio * duration.value;
    }
}
function jumpToTimestamp(seconds, sceneName) {
    if (videoRef.value) {
        videoRef.value.currentTime = seconds;
        videoRef.value.play().then(() => {
            isPlaying.value = true;
        }).catch(() => { });
        resumeToast.value = `已为您秒级跳转至：${sceneName || formatSeconds(seconds)}`;
        setTimeout(() => {
            resumeToast.value = '';
        }, 3000);
    }
}
function formatSeconds(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}
// WebSocket Danmaku
function initDanmakuWs(episodeId) {
    closeDanmakuWs();
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/danmaku/ws/${episodeId}`;
    try {
        danmakuWs = new WebSocket(wsUrl);
        danmakuWs.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (msg.type === 'danmaku') {
                    pushFlyingDanmaku(msg.content, msg.color || '#FFFFFF');
                }
            }
            catch (e) { }
        };
    }
    catch (err) {
        console.warn('WebSocket connection not supported in current mode, simulated locally.');
    }
}
function closeDanmakuWs() {
    if (danmakuWs) {
        danmakuWs.close();
        danmakuWs = null;
    }
}
function sendDanmaku() {
    const text = danmakuInputText.value.trim();
    if (!text)
        return;
    // DFA check simulation for sensitive words
    if (text.includes('微信') || text.includes('代理') || text.includes('刷单')) {
        reviewQueue.value.push({
            id: String(Date.now()),
            target_id: text,
            violation_reason: '敏感广告营销词命中'
        });
        alert('【内容风控提醒】您发送的内容包含敏感广告词，已被机审系统拦截。');
        danmakuInputText.value = '';
        return;
    }
    if (danmakuWs && danmakuWs.readyState === WebSocket.OPEN) {
        danmakuWs.send(JSON.stringify({ content: text, color: '#FFFFFF', time_offset: currentTime.value }));
    }
    else {
        pushFlyingDanmaku(text, '#FFFFFF');
    }
    danmakuInputText.value = '';
}
function pushFlyingDanmaku(content, color) {
    const bullet = {
        id: String(Math.random()),
        content,
        color,
        track: Math.floor(Math.random() * 4),
        speed: 6 + Math.random() * 3
    };
    activeDanmakus.value.push(bullet);
    setTimeout(() => {
        activeDanmakus.value = activeDanmakus.value.filter(b => b.id !== bullet.id);
    }, bullet.speed * 1000);
}
// Real Persistent Likes
async function loadEpisodeLikeStatus(episodeId) {
    try {
        const res = await videoApi.getLikeStatus(episodeId);
        if (res?.data) {
            isLiked.value = !!res.data.is_liked;
            likeCount.value = res.data.like_count ?? 0;
        }
    }
    catch (err) {
        console.warn('Failed to load like status:', err);
    }
}
async function handleToggleLike() {
    if (!currentUser.value) {
        openAuthModal('点赞需要先登录用户账号');
        return;
    }
    if (!currentEpisode.value?.id)
        return;
    try {
        const res = await videoApi.toggleLike(currentEpisode.value.id);
        if (res?.data) {
            isLiked.value = !!res.data.is_liked;
            likeCount.value = res.data.like_count ?? (isLiked.value ? likeCount.value + 1 : Math.max(0, likeCount.value - 1));
        }
    }
    catch (err) {
        console.warn('Failed to toggle like:', err);
        alert(err?.response?.data?.detail || '点赞操作失败');
    }
}
async function loadEpisodeTipStatus(episodeId) {
    try {
        const res = await videoApi.getTipStatus(episodeId);
        if (res?.data) {
            userTippedCount.value = res.data.tipped_count ?? 0;
            videoCoinCount.value = res.data.video_coin_count ?? 2140;
        }
    }
    catch (err) {
        console.warn('Failed to load tip status:', err);
    }
}
async function handleCoin() {
    if (!currentUser.value) {
        openAuthModal('投币支持需要先登录用户账号');
        return;
    }
    showCoinModal.value = true;
    tipSuccessTip.value = '';
    try {
        const wRes = await userApi.getCoinWallet();
        if (wRes?.data) {
            userWalletBalance.value = wRes.data.balance ?? 50;
        }
    }
    catch (err) {
        console.warn('Failed to load wallet balance:', err);
    }
    if (currentEpisode.value?.id) {
        await loadEpisodeTipStatus(currentEpisode.value.id);
    }
}
async function executeTip(amount) {
    if (!currentEpisode.value?.id)
        return;
    if (userTippedCount.value + amount > 2) {
        alert(`每部短剧每人最多打赏 2 枚金币，您已打赏 ${userTippedCount.value} 枚`);
        return;
    }
    if (userWalletBalance.value < amount) {
        alert(`金币余额不足，需要 ${amount} 金币，当前余额为 ${userWalletBalance.value}`);
        return;
    }
    isTipping.value = true;
    try {
        const res = await videoApi.tipVideo(currentEpisode.value.id, { coin_amount: amount });
        if (res?.data) {
            userWalletBalance.value = res.data.wallet_balance;
            videoCoinCount.value = res.data.video_coin_count;
            userTippedCount.value = res.data.tipped_count;
            tipSuccessTip.value = `🪙 感谢支持！成功打赏 ${amount} 枚金币！全站热度值 +${amount * 10}`;
            setTimeout(() => {
                showCoinModal.value = false;
            }, 1500);
        }
    }
    catch (err) {
        alert(err?.response?.data?.detail || err?.message || '投币失败');
    }
    finally {
        isTipping.value = false;
    }
}
async function checkFavoriteStatus(videoId) {
    if (!currentUser.value) {
        isFavorited.value = false;
        return;
    }
    try {
        const res = await favoritesApi.getStatus(videoId);
        const data = res?.data || res;
        isFavorited.value = !!data?.is_favorited;
        selectedFolderIds.value = data?.folder_ids || [];
    }
    catch (e) {
        console.warn('Check favorite status error:', e);
    }
}
async function handleFavoriteClick() {
    if (!currentUser.value) {
        openAuthModal('收藏短剧需要先登录用户账号');
        return;
    }
    showFavoriteModal.value = true;
    await loadUserFolders();
    if (album.value?.id) {
        await checkFavoriteStatus(album.value.id);
    }
}
function handleFavorite() {
    handleFavoriteClick();
}
async function loadUserFolders() {
    try {
        const res = await favoritesApi.getFolders();
        const data = res?.data || res;
        userFolders.value = Array.isArray(data) ? data : [];
    }
    catch (e) {
        console.warn('Load user folders error:', e);
    }
}
function toggleFolderSelection(folderId) {
    const idx = selectedFolderIds.value.indexOf(folderId);
    if (idx >= 0) {
        selectedFolderIds.value.splice(idx, 1);
    }
    else {
        selectedFolderIds.value.push(folderId);
    }
}
async function handleCreateFolderInModal() {
    const name = newFolderName.value.trim();
    if (!name)
        return;
    try {
        const res = await favoritesApi.createFolder({
            name,
            is_public: newFolderIsPublic.value
        });
        const created = res?.data || res;
        if (created && created.id) {
            userFolders.value.push(created);
            selectedFolderIds.value.push(created.id);
            newFolderName.value = '';
            showNewFolderInput.value = false;
        }
    }
    catch (err) {
        alert(err?.response?.data?.detail || '创建收藏夹失败，请重试');
    }
}
async function handleQuickDefaultSave() {
    if (!album.value?.id)
        return;
    try {
        const res = await favoritesApi.quickDefaultToggle(album.value.id);
        const data = res?.data || res;
        isFavorited.value = !!data?.is_favorited;
        favoriteCount.value += isFavorited.value ? 1 : -1;
        resumeToast.value = data?.message || (isFavorited.value ? '已存入默认收藏夹' : '已从默认收藏夹移出');
        setTimeout(() => { resumeToast.value = ''; }, 3000);
        showFavoriteModal.value = false;
    }
    catch (e) {
        alert(e?.response?.data?.detail || '快捷收藏失败');
    }
}
async function handleSaveToSelectedFolders() {
    if (!album.value?.id)
        return;
    isSavingFavorite.value = true;
    try {
        if (selectedFolderIds.value.length === 0) {
            await favoritesApi.removeItem(album.value.id);
            isFavorited.value = false;
            favoriteCount.value = Math.max(0, favoriteCount.value - 1);
            resumeToast.value = '已从所有收藏夹移出';
        }
        else {
            await favoritesApi.addItem({
                video_id: album.value.id,
                folder_ids: selectedFolderIds.value
            });
            isFavorited.value = true;
            favoriteCount.value += 1;
            resumeToast.value = `已成功保存至 ${selectedFolderIds.value.length} 个收藏夹`;
        }
        setTimeout(() => { resumeToast.value = ''; }, 3000);
        showFavoriteModal.value = false;
    }
    catch (e) {
        alert(e?.response?.data?.detail || '保存收藏失败');
    }
    finally {
        isSavingFavorite.value = false;
    }
}
function handleShare() {
    navigator.clipboard?.writeText(window.location.href);
    alert('↗️ 播放链接已复制到剪贴板，快分享给好友一起追剧吧！');
}
// Real Two-Tier Comments Operations
async function loadEpisodeComments(episodeId) {
    try {
        const res = await videoApi.getComments(episodeId);
        if (res?.data) {
            comments.value = res.data.items || [];
            commentsTotal.value = res.data.total ?? comments.value.length;
        }
    }
    catch (err) {
        console.warn('Failed to load comments:', err);
    }
    // Handle route.query.commentId highlighting
    const targetCommentId = route.query.commentId;
    if (targetCommentId) {
        highlightedCommentId.value = targetCommentId;
        nextTick(() => {
            const el = document.getElementById('comment-' + targetCommentId);
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
        setTimeout(() => {
            highlightedCommentId.value = '';
        }, 4000);
    }
}
async function submitComment() {
    if (!currentUser.value) {
        openAuthModal('发表评论需要先登录账号');
        return;
    }
    const text = commentText.value.trim();
    if (!text)
        return;
    if (!currentEpisode.value?.id)
        return;
    isSubmittingComment.value = true;
    try {
        const res = await videoApi.postComment(currentEpisode.value.id, { content: text });
        if (res?.data) {
            commentText.value = '';
            await loadEpisodeComments(currentEpisode.value.id);
        }
    }
    catch (err) {
        console.warn('Failed to submit comment:', err);
        alert(err?.response?.data?.detail || '发表评论失败，请重试');
    }
    finally {
        isSubmittingComment.value = false;
    }
}
function toggleReplyInput(rootId, targetUserId, targetName) {
    if (!currentUser.value) {
        openAuthModal('回复评论需要先登录账号');
        return;
    }
    if (activeReplyRootId.value === rootId && activeReplyTargetUserId.value === targetUserId) {
        cancelReply();
        return;
    }
    activeReplyRootId.value = rootId;
    activeReplyTargetUserId.value = targetUserId || '';
    replyTargetName.value = targetName || '用户';
    replyText.value = '';
}
function cancelReply() {
    activeReplyRootId.value = '';
    activeReplyTargetUserId.value = '';
    replyTargetName.value = '';
    replyText.value = '';
}
async function submitReply(rootId) {
    if (!currentUser.value) {
        openAuthModal('回复评论需要先登录账号');
        return;
    }
    const text = replyText.value.trim();
    if (!text)
        return;
    if (!currentEpisode.value?.id)
        return;
    isSubmittingReply.value = true;
    try {
        await videoApi.postComment(currentEpisode.value.id, {
            content: text,
            root_id: rootId,
            parent_id: rootId,
            reply_to_user_id: activeReplyTargetUserId.value || undefined
        });
        cancelReply();
        await loadEpisodeComments(currentEpisode.value.id);
    }
    catch (err) {
        console.warn('Failed to submit reply:', err);
        alert(err?.response?.data?.detail || '回复发表失败，请重试');
    }
    finally {
        isSubmittingReply.value = false;
    }
}
async function handleToggleCommentLike(comment) {
    if (!currentUser.value) {
        openAuthModal('点赞评论需要先登录账号');
        return;
    }
    try {
        const res = await videoApi.toggleCommentLike(comment.id);
        if (res?.data) {
            comment.is_liked = !!res.data.is_liked;
            comment.like_count = res.data.like_count;
        }
    }
    catch (err) {
        console.warn('Failed to toggle comment like:', err);
    }
}
// Companion interaction with SSE Streaming & Timeline RAG
async function sendAgentQuestion() {
    if (isStreamingAgent.value)
        return;
    const q = agentInputText.value.trim();
    if (!q)
        return;
    agentMessages.value.push({ sender: 'user', text: q });
    agentInputText.value = '';
    scrollToBottom();
    // Add agent placeholder message
    const agentMsgIndex = agentMessages.value.length;
    agentMessages.value.push({
        sender: 'agent',
        text: '',
        thought: '',
        targetTime: undefined,
        timeTag: undefined,
        scene: undefined,
        isTyping: true
    });
    scrollToBottom();
    isStreamingAgent.value = true;
    const currentSec = videoRef.value ? videoRef.value.currentTime : 0;
    const episodeId = currentEpisode.value?.id || 'ef96c393-0bab-43b5-9cf8-b0c8d065b0ba';
    try {
        await videoApi.streamAgentChat({
            episodeId,
            question: q,
            currentVideoTime: currentSec,
            onThought: (th) => {
                agentMessages.value[agentMsgIndex].thought = (agentMessages.value[agentMsgIndex].thought || '') + th;
                scrollToBottom();
            },
            onToken: (token) => {
                agentMessages.value[agentMsgIndex].text += token;
                scrollToBottom();
            },
            onActionCard: (card) => {
                agentMessages.value[agentMsgIndex].targetTime = card.timestamp;
                agentMessages.value[agentMsgIndex].timeTag = card.time_tag;
                agentMessages.value[agentMsgIndex].scene = card.title;
            },
            onDone: (data) => {
                agentMessages.value[agentMsgIndex].isTyping = false;
                if (agentMessages.value[agentMsgIndex].targetTime === undefined) {
                    agentMessages.value[agentMsgIndex].targetTime = data.target_time;
                    agentMessages.value[agentMsgIndex].timeTag = data.time_tag;
                }
                isStreamingAgent.value = false;
                scrollToBottom();
            },
            onError: (err) => {
                console.warn('Stream chat error:', err);
                agentMessages.value[agentMsgIndex].isTyping = false;
                isStreamingAgent.value = false;
                if (!agentMessages.value[agentMsgIndex].text) {
                    agentMessages.value[agentMsgIndex].text = `【系统异常】` + (err?.message || '伴读服务调用失败，请检查模型服务状态。');
                }
            }
        });
    }
    catch (err) {
        agentMessages.value[agentMsgIndex].isTyping = false;
        isStreamingAgent.value = false;
        if (!agentMessages.value[agentMsgIndex].text) {
            agentMessages.value[agentMsgIndex].text = `【网络中断】无法连接至伴读服务，请稍后重试。`;
        }
    }
    finally {
        agentMessages.value[agentMsgIndex].isTyping = false;
        isStreamingAgent.value = false;
    }
}
function askQuickPrompt(p) {
    agentInputText.value = p;
    sendAgentQuestion();
}
function scrollToBottom() {
    nextTick(() => {
        if (chatScrollRef.value) {
            chatScrollRef.value.scrollTop = chatScrollRef.value.scrollHeight;
        }
    });
}
// Review moderation
function handleReviewDecision(id, decision) {
    reviewQueue.value = reviewQueue.value.filter(r => r.id !== id);
    alert(`审核裁决完成：该记录已标记为【${decision === 'APPROVED' ? '放行通过' : '确认违规下架'}】`);
}
// Role switch
async function switchRole(roleName) {
    const accounts = {
        USER: { u: 'user', p: 'user123' },
        CREATOR: { u: 'creator', p: 'creator123' },
        REVIEWER: { u: 'reviewer', p: 'reviewer123' },
        ADMIN: { u: 'admin', p: 'admin123' }
    };
    const acc = accounts[roleName];
    if (!acc)
        return;
    try {
        const res = await authApi.login({ username: acc.u, password: acc.p });
        const token = res?.access_token || res?.data?.access_token;
        const userObj = res?.user || res?.data?.user;
        if (token && userObj) {
            userStore.setUser(userObj, token);
        }
    }
    catch (e) { }
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
function openAuthModal(hint = '') {
    showAuthModal.value = true;
}
function handleLogout() {
    userStore.clearUser();
    window.location.href = '/';
}
async function handleAuthSubmit() {
    try {
        const res = await authApi.login({
            username: authForm.value.username.trim(),
            password: authForm.value.password.trim()
        });
        const token = res?.access_token || res?.data?.access_token;
        const userObj = res?.user || res?.data?.user;
        if (token && userObj) {
            userStore.setUser(userObj, token);
            showAuthModal.value = false;
        }
        else {
            alert('登录失败，请检查账号密码');
        }
    }
    catch (e) {
        alert('登录失败，请检查账号密码');
    }
}
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['apple-back-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-switch-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-switch-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['role-mini-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['user-chip-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['user-name-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['user-role-badge-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['user-role-badge-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['user-role-badge-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['user-role-badge-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['logout-link-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-landscape']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-portrait']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-portrait']} */ ;
/** @type {__VLS_StyleScopedClasses['video-viewport-box']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-portrait']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-portrait']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-portrait']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-portrait']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-portrait']} */ ;
/** @type {__VLS_StyleScopedClasses['core-video-element']} */ ;
/** @type {__VLS_StyleScopedClasses['progress-track-wrapper']} */ ;
/** @type {__VLS_StyleScopedClasses['progress-bar-bg']} */ ;
/** @type {__VLS_StyleScopedClasses['danmaku-pill-input']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-danmaku-send']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-ctrl-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-popover-glass']} */ ;
/** @type {__VLS_StyleScopedClasses['popover-item']} */ ;
/** @type {__VLS_StyleScopedClasses['popover-item']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['video-meta-card']} */ ;
/** @type {__VLS_StyleScopedClasses['action-pills-row']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-action-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-action-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-action-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['comments-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-textarea']} */ ;
/** @type {__VLS_StyleScopedClasses['side-tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['episode-chunk-tabs-row']} */ ;
/** @type {__VLS_StyleScopedClasses['episode-chunk-tabs-row']} */ ;
/** @type {__VLS_StyleScopedClasses['episode-chunk-tabs-row']} */ ;
/** @type {__VLS_StyleScopedClasses['chunk-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['chunk-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['episodes-scroll-window']} */ ;
/** @type {__VLS_StyleScopedClasses['episodes-scroll-window']} */ ;
/** @type {__VLS_StyleScopedClasses['episodes-scroll-window']} */ ;
/** @type {__VLS_StyleScopedClasses['episodes-scroll-window']} */ ;
/** @type {__VLS_StyleScopedClasses['episode-tile-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['episode-tile-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['highlight-card-item']} */ ;
/** @type {__VLS_StyleScopedClasses['highlight-time-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['highlight-time-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['highlight-card-item']} */ ;
/** @type {__VLS_StyleScopedClasses['jump-hint']} */ ;
/** @type {__VLS_StyleScopedClasses['quick-prompt-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['jump-timestamp-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-pill-input']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-stage-container']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-portrait']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-player-column']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-portrait']} */ ;
/** @type {__VLS_StyleScopedClasses['video-viewport-box']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-portrait']} */ ;
/** @type {__VLS_StyleScopedClasses['video-meta-card']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-portrait']} */ ;
/** @type {__VLS_StyleScopedClasses['comments-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['autoplay-toggle-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['autoplay-toggle-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['autoplay-indicator-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['favorites-modal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-title']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-select-item']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-thread-card']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-bubble-item']} */ ;
/** @type {__VLS_StyleScopedClasses['commenter-avatar']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-author-line']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-name']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-time']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-content-text']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['inline-reply-box']} */ ;
/** @type {__VLS_StyleScopedClasses['reply-textarea']} */ ;
/** @type {__VLS_StyleScopedClasses['reply-cancel-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-bell-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tip-option-card']} */ ;
/** @type {__VLS_StyleScopedClasses['tip-option-card']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-collapse-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['floating-expand-sidebar-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-stage-container']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-stage-container']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-collapsed']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-player-column']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-stage-container']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-collapsed']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-landscape']} */ ;
/** @type {__VLS_StyleScopedClasses['video-viewport-box']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-stage-container']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-collapsed']} */ ;
/** @type {__VLS_StyleScopedClasses['stage-landscape']} */ ;
/** @type {__VLS_StyleScopedClasses['video-viewport-box']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-stage-container']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-collapsed']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-sidebar-column']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-stage-container']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-stage-container']} */ ;
/** @type {__VLS_StyleScopedClasses['is-web-fullscreen']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-player-column']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-stage-container']} */ ;
/** @type {__VLS_StyleScopedClasses['is-web-fullscreen']} */ ;
/** @type {__VLS_StyleScopedClasses['video-viewport-box']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-stage-container']} */ ;
/** @type {__VLS_StyleScopedClasses['is-web-fullscreen']} */ ;
/** @type {__VLS_StyleScopedClasses['video-meta-card']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-stage-container']} */ ;
/** @type {__VLS_StyleScopedClasses['is-web-fullscreen']} */ ;
/** @type {__VLS_StyleScopedClasses['comments-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-stage-container']} */ ;
/** @type {__VLS_StyleScopedClasses['is-web-fullscreen']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-sidebar-column']} */ ;
/** @type {__VLS_StyleScopedClasses['comments-flow-list']} */ ;
/** @type {__VLS_StyleScopedClasses['comments-flow-list']} */ ;
/** @type {__VLS_StyleScopedClasses['comments-flow-list']} */ ;
/** @type {__VLS_StyleScopedClasses['comments-flow-list']} */ ;
/** @type {__VLS_StyleScopedClasses['comments-flow-list']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "apple-player-page" },
    ...{ class: ({ 'mode-landscape': __VLS_ctx.displayMode === 'landscape', 'mode-portrait': __VLS_ctx.displayMode === 'portrait' }) },
    id: "cinema-backdrop",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.header, __VLS_intrinsicElements.header)({
    ...{ class: "player-global-header" },
    id: "player-top-header",
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
    ...{ class: "apple-back-btn" },
    id: "btn-back-home",
    title: "返回视听大厅",
}));
const __VLS_2 = __VLS_1({
    to: "/",
    ...{ class: "apple-back-btn" },
    id: "btn-back-home",
    title: "返回视听大厅",
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
__VLS_3.slots.default;
__VLS_asFunctionalElement(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({
    viewBox: "0 0 24 24",
    ...{ class: "back-svg" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.path)({
    fill: "currentColor",
    d: "M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
var __VLS_3;
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "header-divider" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "drama-headline-chip" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "drama-tag" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "drama-title-text" },
});
(__VLS_ctx.album?.title || '精彩短剧');
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "episode-pill" },
});
(__VLS_ctx.currentEpisode?.episode_num || 1);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "header-center" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "apple-mode-switcher-capsule" },
    id: "mode-switcher-container",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.displayMode = 'landscape';
        } },
    ...{ class: "mode-switch-btn" },
    ...{ class: ({ active: __VLS_ctx.displayMode === 'landscape' }) },
    id: "btn-mode-landscape",
    title: "切换为 16:9 极简宽屏影院模式",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({
    viewBox: "0 0 24 24",
    ...{ class: "mode-icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.path)({
    fill: "currentColor",
    d: "M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H4V6h16v12z",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.displayMode = 'portrait';
        } },
    ...{ class: "mode-switch-btn" },
    ...{ class: ({ active: __VLS_ctx.displayMode === 'portrait' }) },
    id: "btn-mode-portrait",
    title: "切换为 9:16 沉浸短剧胶囊模式",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({
    viewBox: "0 0 24 24",
    ...{ class: "mode-icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.path)({
    fill: "currentColor",
    d: "M17 1.01L7 1c-1.1 0-2 .9-2 2v18c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V3c0-1.1-.9-1.99-2-1.99zM17 19H7V5h10v14z",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "header-right" },
});
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
const __VLS_4 = {}.ElIcon;
/** @type {[typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, typeof __VLS_components.ElIcon, typeof __VLS_components.elIcon, ]} */ ;
// @ts-ignore
const __VLS_5 = __VLS_asFunctionalComponent(__VLS_4, new __VLS_4({
    size: (16),
}));
const __VLS_6 = __VLS_5({
    size: (16),
}, ...__VLS_functionalComponentArgsRest(__VLS_5));
__VLS_7.slots.default;
const __VLS_8 = {}.Bell;
/** @type {[typeof __VLS_components.Bell, ]} */ ;
// @ts-ignore
const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({}));
const __VLS_10 = __VLS_9({}, ...__VLS_functionalComponentArgsRest(__VLS_9));
var __VLS_7;
if (__VLS_ctx.unreadCounts.total > 0) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "skylight-unread-badge" },
        id: "skylight-unread-badge",
    });
    (__VLS_ctx.unreadCounts.total > 99 ? '99+' : __VLS_ctx.unreadCounts.total);
}
if (__VLS_ctx.currentUser) {
    const __VLS_12 = {}.RouterLink;
    /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
    // @ts-ignore
    const __VLS_13 = __VLS_asFunctionalComponent(__VLS_12, new __VLS_12({
        to: "/user/space",
        ...{ class: "user-chip-mini" },
        id: "user-profile-badge",
        title: "前往个人中心",
    }));
    const __VLS_14 = __VLS_13({
        to: "/user/space",
        ...{ class: "user-chip-mini" },
        id: "user-profile-badge",
        title: "前往个人中心",
    }, ...__VLS_functionalComponentArgsRest(__VLS_13));
    __VLS_15.slots.default;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
        src: (__VLS_ctx.currentUser.avatar_url || __VLS_ctx.defaultAvatar),
        ...{ class: "avatar-mini" },
        id: "user-avatar-img",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "user-info-text" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "user-name-mini" },
        id: "user-display-name",
    });
    (__VLS_ctx.currentUser.nickname || __VLS_ctx.currentUser.username);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "user-role-badge-mini" },
        ...{ class: (__VLS_ctx.currentUser.role?.toLowerCase()) },
    });
    (__VLS_ctx.getRoleLabel(__VLS_ctx.currentUser.role));
    var __VLS_15;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.handleLogout) },
        ...{ class: "logout-link-mini" },
        id: "btn-logout",
    });
}
else {
    const __VLS_16 = {}.RouterLink;
    /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
    // @ts-ignore
    const __VLS_17 = __VLS_asFunctionalComponent(__VLS_16, new __VLS_16({
        to: "/login",
        ...{ class: "apple-primary-btn mini-btn" },
        id: "btn-open-login",
    }));
    const __VLS_18 = __VLS_17({
        to: "/login",
        ...{ class: "apple-primary-btn mini-btn" },
        id: "btn-open-login",
    }, ...__VLS_functionalComponentArgsRest(__VLS_17));
    __VLS_19.slots.default;
    var __VLS_19;
}
const __VLS_20 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_21 = __VLS_asFunctionalComponent(__VLS_20, new __VLS_20({
    name: "apple-toast-slide",
}));
const __VLS_22 = __VLS_21({
    name: "apple-toast-slide",
}, ...__VLS_functionalComponentArgsRest(__VLS_21));
__VLS_23.slots.default;
if (__VLS_ctx.resumeToast) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "resume-toast-capsule" },
        id: "resume-toast-pill",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "toast-sparkle" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "toast-msg" },
    });
    (__VLS_ctx.resumeToast);
}
var __VLS_23;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "theater-stage-container" },
    ...{ class: (['stage-' + __VLS_ctx.displayMode, { 'sidebar-collapsed': __VLS_ctx.isSidebarCollapsed, 'is-web-fullscreen': __VLS_ctx.isWebFullscreen }]) },
    id: (__VLS_ctx.displayMode === 'landscape' ? 'landscape-player-layout' : 'portrait-player-layout'),
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "theater-player-column" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "video-viewport-box" },
    id: "widescreen-player-box",
});
if (__VLS_ctx.displayMode === 'portrait') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "mobile-notch-bar" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "notch-speaker" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "notch-title" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ onClick: (__VLS_ctx.togglePlay) },
    ...{ class: "video-media-wrapper" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.video, __VLS_intrinsicElements.video)({
    ...{ onTimeupdate: (__VLS_ctx.onTimeUpdate) },
    ...{ onLoadedmetadata: (__VLS_ctx.onLoadedMetadata) },
    ...{ onEnded: (__VLS_ctx.onVideoEnded) },
    ref: "videoRef",
    id: "player-video",
    ...{ class: "core-video-element" },
    playsinline: true,
    preload: "auto",
    src: (__VLS_ctx.currentStreamUrl),
});
/** @type {typeof __VLS_ctx.videoRef} */ ;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "danmaku-screen-layer" },
    'pointer-events': "none",
});
for (const [d] of __VLS_getVForSourceType((__VLS_ctx.activeDanmakus))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        key: (d.id),
        ...{ class: "danmaku-flying-bullet" },
        ...{ style: ({
                top: (d.track * 26 + 12) + 'px',
                color: d.color,
                animationDuration: d.speed + 's'
            }) },
    });
    (d.content);
}
const __VLS_24 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_25 = __VLS_asFunctionalComponent(__VLS_24, new __VLS_24({
    name: "fade",
}));
const __VLS_26 = __VLS_25({
    name: "fade",
}, ...__VLS_functionalComponentArgsRest(__VLS_25));
__VLS_27.slots.default;
if (!__VLS_ctx.isPlaying) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "play-splash-circle" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({
        viewBox: "0 0 24 24",
        ...{ class: "splash-svg" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.path)({
        fill: "currentColor",
        d: "M8 5v14l11-7z",
    });
}
var __VLS_27;
const __VLS_28 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_29 = __VLS_asFunctionalComponent(__VLS_28, new __VLS_28({
    name: "apple-hud-pop",
}));
const __VLS_30 = __VLS_29({
    name: "apple-hud-pop",
}, ...__VLS_functionalComponentArgsRest(__VLS_29));
__VLS_31.slots.default;
if (__VLS_ctx.showCountdownHud) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "autoplay-countdown-hud autoplay-countdown-hud-overlay" },
        id: "autoplay-countdown-hud",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "hud-glass-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "hud-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "hud-sparkle-icon" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "hud-badge" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "hud-body" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "hud-timer-circle" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "hud-timer-num" },
        id: "hud-countdown-seconds",
    });
    (__VLS_ctx.countdownSeconds);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "hud-timer-unit" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "hud-next-info" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "hud-next-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "hud-next-title" },
        id: "hud-next-ep-title",
    });
    (__VLS_ctx.nextEpisode?.episode_num || (__VLS_ctx.currentEpisode ? __VLS_ctx.currentEpisode.episode_num + 1 : 1));
    (__VLS_ctx.nextEpisode?.title || '精彩下一集');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "hud-actions-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.executeNextEpisodeImmediately) },
        ...{ class: "hud-btn-primary" },
        id: "btn-hud-skip-next",
        title: "立即播放下一集",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        id: "btn-skip-countdown",
    });
    (__VLS_ctx.countdownSeconds);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.cancelCountdownAutoplay) },
        ...{ class: "hud-btn-secondary" },
        id: "btn-hud-cancel-autoplay",
        title: "取消自动连播",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        id: "btn-cancel-countdown",
    });
}
var __VLS_31;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "player-controls-bar" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ onClick: (__VLS_ctx.handleSeekClick) },
    ...{ class: "progress-track-wrapper" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "progress-bar-bg" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "progress-bar-fill" },
    ...{ style: ({ width: __VLS_ctx.progressPercent + '%' }) },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "progress-handle" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "controls-action-line" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "ctrl-left" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.togglePlay) },
    ...{ class: "icon-ctrl-btn" },
    title: "播放/暂停",
});
if (__VLS_ctx.isPlaying) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({
        viewBox: "0 0 24 24",
        ...{ class: "ctrl-svg" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.path)({
        fill: "currentColor",
        d: "M6 19h4V5H6v14zm8-14v14h4V5h-4z",
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({
        viewBox: "0 0 24 24",
        ...{ class: "ctrl-svg" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.path)({
        fill: "currentColor",
        d: "M8 5v14l11-7z",
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "timestamp-display" },
});
(__VLS_ctx.formatSeconds(__VLS_ctx.currentTime));
(__VLS_ctx.formatSeconds(__VLS_ctx.duration));
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "danmaku-send-box" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ onKeyup: (__VLS_ctx.sendDanmaku) },
    id: "input-danmaku",
    ...{ class: "danmaku-pill-input" },
    placeholder: "发一条友善弹幕，与全网剧迷实时互动...",
    maxlength: "50",
});
(__VLS_ctx.danmakuInputText);
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.sendDanmaku) },
    ...{ class: "btn-danmaku-send" },
    id: "btn-send-danmaku",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "ctrl-right" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.toggleAutoplay) },
    ...{ class: "pill-ctrl-btn autoplay-toggle-btn" },
    ...{ class: ({ active: __VLS_ctx.isAutoplayEnabled }) },
    id: "btn-toggle-autoplay",
    title: (__VLS_ctx.isAutoplayEnabled ? '点击关闭自动连播' : '点击开启自动连播'),
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "autoplay-indicator-dot" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(__VLS_ctx.isAutoplayEnabled ? '开' : '关');
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ onMouseenter: (__VLS_ctx.openSpeedMenu) },
    ...{ onMouseleave: (__VLS_ctx.closeSpeedMenuDebounced) },
    ...{ class: "speed-menu-wrap" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.showSpeedMenu = !__VLS_ctx.showSpeedMenu;
        } },
    ...{ class: "pill-ctrl-btn" },
    id: "btn-playback-rate",
    title: "调节播放倍速",
});
(__VLS_ctx.currentRate === 1.0 ? '倍速' : __VLS_ctx.currentRate + 'x');
if (__VLS_ctx.showSpeedMenu) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ onMouseenter: (__VLS_ctx.openSpeedMenu) },
        ...{ onMouseleave: (__VLS_ctx.closeSpeedMenuDebounced) },
        ...{ class: "dropdown-popover-glass" },
        id: "menu-playback-speed",
    });
    for (const [r] of __VLS_getVForSourceType(([2.0, 1.5, 1.25, 1.0, 0.75, 0.5]))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.showSpeedMenu))
                        return;
                    __VLS_ctx.setPlaybackRate(r);
                } },
            key: (r),
            ...{ class: "popover-item" },
            ...{ class: ({ active: __VLS_ctx.currentRate === r }) },
            id: ('speed-opt-' + r),
        });
        (r);
    }
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ onMouseenter: (__VLS_ctx.openResMenu) },
    ...{ onMouseleave: (__VLS_ctx.closeResMenuDebounced) },
    ...{ class: "resolution-menu-wrap" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.showResMenu = !__VLS_ctx.showResMenu;
        } },
    ...{ class: "pill-ctrl-btn" },
    id: "btn-resolution",
    title: "清晰度画质选择",
});
(__VLS_ctx.currentResolution);
if (__VLS_ctx.showResMenu) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ onMouseenter: (__VLS_ctx.openResMenu) },
        ...{ onMouseleave: (__VLS_ctx.closeResMenuDebounced) },
        ...{ class: "dropdown-popover-glass" },
        id: "menu-resolution",
    });
    for (const [res] of __VLS_getVForSourceType((['4K 原画', '1080P 超清', '720P 高清']))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.showResMenu))
                        return;
                    __VLS_ctx.setResolution(res);
                } },
            key: (res),
            ...{ class: "popover-item" },
            ...{ class: ({ active: __VLS_ctx.currentResolution === res }) },
        });
        (res);
    }
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.displayMode = (__VLS_ctx.displayMode === 'landscape' ? 'portrait' : 'landscape');
        } },
    ...{ class: "mode-quick-toggle" },
    title: (__VLS_ctx.displayMode === 'landscape' ? '切换为 9:16 沉浸短剧竖屏' : '切换为 16:9 极简宽屏'),
});
(__VLS_ctx.displayMode === 'landscape' ? '竖屏' : '横屏');
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.toggleWebFullscreen) },
    ...{ class: "mode-quick-toggle" },
    ...{ class: ({ active: __VLS_ctx.isWebFullscreen }) },
    id: "btn-web-fullscreen",
    title: (__VLS_ctx.isWebFullscreen ? '退出网页沉浸全屏' : '网页沉浸全屏'),
});
(__VLS_ctx.isWebFullscreen ? '还原' : '网页全屏');
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.toggleNativeFullscreen) },
    ...{ class: "mode-quick-toggle" },
    id: "btn-native-fullscreen",
    title: "物理全屏",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.isSidebarCollapsed = !__VLS_ctx.isSidebarCollapsed;
        } },
    ...{ class: "mode-quick-toggle" },
    ...{ class: ({ active: __VLS_ctx.isSidebarCollapsed }) },
    id: "btn-toggle-sidebar",
    title: (__VLS_ctx.isSidebarCollapsed ? '展开右侧功能面板 (选集/看点/伴读)' : '收起右侧功能面板，全幅巨幕自适应'),
});
(__VLS_ctx.isSidebarCollapsed ? '展开侧栏 ❮' : '收起侧栏 ❯');
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "video-meta-card" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "meta-titles-row" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({
    ...{ class: "video-main-heading" },
});
(__VLS_ctx.album?.title);
(__VLS_ctx.currentEpisode?.episode_num);
(__VLS_ctx.currentEpisode?.title);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "video-stats-labels" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(__VLS_ctx.formatNumber(__VLS_ctx.album?.view_count || 1280));
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(__VLS_ctx.formatNumber(__VLS_ctx.activeDanmakus.length || 0));
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "action-pills-row" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.handleToggleLike) },
    ...{ class: "apple-action-pill btn-like" },
    ...{ class: ({ active: __VLS_ctx.isLiked }) },
    id: "btn-video-like",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "pill-emoji" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(__VLS_ctx.isLiked ? '已点赞' : '点赞');
(__VLS_ctx.likeCount);
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.handleCoin) },
    ...{ class: "apple-action-pill" },
    id: "btn-coin-tip",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "pill-emoji" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(__VLS_ctx.videoCoinCount);
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.handleFavoriteClick) },
    ...{ class: "apple-action-pill" },
    ...{ class: ({ active: __VLS_ctx.isFavorited }) },
    id: "btn-favorite",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "pill-emoji" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(__VLS_ctx.isFavorited ? '已收藏' : '收藏');
(__VLS_ctx.favoriteCount);
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.handleShare) },
    ...{ class: "apple-action-pill" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "pill-emoji" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "comments-bento-card" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "comments-card-header" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
(__VLS_ctx.commentsTotal || __VLS_ctx.comments.length);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "comment-compose-box" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
    src: (__VLS_ctx.currentUser?.avatar_url || __VLS_ctx.defaultAvatar),
    ...{ class: "compose-avatar" },
    alt: "头像",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "compose-input-area" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.textarea, __VLS_intrinsicElements.textarea)({
    ...{ onKeyup: (__VLS_ctx.submitComment) },
    value: (__VLS_ctx.commentText),
    id: "input-comment",
    ...{ class: "comment-textarea" },
    placeholder: "发一条走心评论，与剧迷深度探讨高能剧情...",
    rows: "2",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.submitComment) },
    ...{ class: "apple-primary-btn" },
    id: "btn-submit-comment",
    disabled: (__VLS_ctx.isSubmittingComment || !__VLS_ctx.commentText.trim()),
});
(__VLS_ctx.isSubmittingComment ? '发送中...' : '发表评论');
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "comments-flow-list" },
    id: "comments-flow-list",
});
if (__VLS_ctx.comments.length === 0) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "comments-empty-state" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "empty-emoji" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
for (const [c] of __VLS_getVForSourceType((__VLS_ctx.comments))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        key: (c.id),
        id: ('comment-' + c.id),
        ...{ class: "comment-thread-card" },
        ...{ class: ({ 'comment-highlight': __VLS_ctx.highlightedCommentId === c.id }) },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "comment-bubble-item root-bubble" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
        src: (c.avatar_url || __VLS_ctx.defaultAvatar),
        ...{ class: "commenter-avatar" },
        alt: "头像",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "comment-body" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "comment-author-line" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "comment-name" },
    });
    (c.nickname || c.username);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "comment-time" },
    });
    (c.created_at || '刚刚');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "comment-content-text" },
    });
    (c.content);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "comment-actions-bar" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                __VLS_ctx.handleToggleCommentLike(c);
            } },
        type: "button",
        ...{ class: "comment-action-btn like-btn" },
        ...{ class: ({ liked: c.is_liked }) },
        id: ('btn-like-comment-' + c.id),
        title: "点赞",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "action-icon" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "action-count" },
    });
    (c.like_count || 0);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                __VLS_ctx.toggleReplyInput(c.id, c.user_id, c.nickname || c.username);
            } },
        type: "button",
        ...{ class: "comment-action-btn reply-btn" },
        id: ('btn-reply-comment-' + c.id),
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "action-icon" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    if (c.replies && c.replies.length > 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "sub-thread-container" },
        });
        for (const [r] of __VLS_getVForSourceType((c.replies))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                key: (r.id),
                id: ('comment-' + r.id),
                ...{ class: "comment-bubble-item sub-bubble" },
                ...{ class: ({ 'comment-highlight': __VLS_ctx.highlightedCommentId === r.id }) },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
                src: (r.avatar_url || __VLS_ctx.defaultAvatar),
                ...{ class: "commenter-avatar sub-avatar" },
                alt: "头像",
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "comment-body" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "comment-author-line" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "comment-name" },
            });
            (r.nickname || r.username);
            if (r.reply_to_nickname || r.reply_to_username) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                    ...{ class: "mention-target-tag" },
                });
                (r.reply_to_nickname || r.reply_to_username);
            }
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "comment-time" },
            });
            (r.created_at || '刚刚');
            __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
                ...{ class: "comment-content-text" },
            });
            (r.content);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "comment-actions-bar" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!(c.replies && c.replies.length > 0))
                            return;
                        __VLS_ctx.handleToggleCommentLike(r);
                    } },
                type: "button",
                ...{ class: "comment-action-btn like-btn" },
                ...{ class: ({ liked: r.is_liked }) },
                id: ('btn-like-comment-' + r.id),
                title: "点赞",
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "action-icon" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "action-count" },
            });
            (r.like_count || 0);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!(c.replies && c.replies.length > 0))
                            return;
                        __VLS_ctx.toggleReplyInput(c.id, r.user_id, r.nickname || r.username);
                    } },
                type: "button",
                ...{ class: "comment-action-btn reply-btn" },
                id: ('btn-reply-comment-' + r.id),
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "action-icon" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        }
    }
    const __VLS_32 = {}.transition;
    /** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
    // @ts-ignore
    const __VLS_33 = __VLS_asFunctionalComponent(__VLS_32, new __VLS_32({
        name: "apple-fade",
    }));
    const __VLS_34 = __VLS_33({
        name: "apple-fade",
    }, ...__VLS_functionalComponentArgsRest(__VLS_33));
    __VLS_35.slots.default;
    if (__VLS_ctx.activeReplyRootId === c.id) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "inline-reply-box" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "reply-input-wrap" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "replying-to-badge" },
        });
        (__VLS_ctx.replyTargetName);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.textarea, __VLS_intrinsicElements.textarea)({
            value: (__VLS_ctx.replyText),
            id: ('input-reply-comment-' + c.id),
            ...{ class: "reply-textarea" },
            placeholder: "写下您的理性探讨或精彩补充...",
            rows: "2",
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "reply-box-footer" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.cancelReply) },
            type: "button",
            ...{ class: "reply-cancel-btn" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.activeReplyRootId === c.id))
                        return;
                    __VLS_ctx.submitReply(c.id);
                } },
            type: "button",
            ...{ class: "apple-primary-btn reply-submit-btn" },
            id: ('btn-submit-reply-' + c.id),
            disabled: (__VLS_ctx.isSubmittingReply || !__VLS_ctx.replyText.trim()),
        });
        (__VLS_ctx.isSubmittingReply ? '回复中...' : '提交回复');
    }
    var __VLS_35;
}
if (__VLS_ctx.isSidebarCollapsed) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.isSidebarCollapsed))
                    return;
                __VLS_ctx.isSidebarCollapsed = false;
            } },
        ...{ class: "floating-expand-sidebar-btn" },
        id: "btn-expand-sidebar-float",
        title: "展开右侧功能栏 (选集/看点/伴读)",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.aside, __VLS_intrinsicElements.aside)({
    ...{ class: "theater-sidebar-column" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "sidebar-top-control-bar" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "sidebar-top-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.isSidebarCollapsed = true;
        } },
    type: "button",
    ...{ class: "sidebar-collapse-btn" },
    id: "btn-collapse-sidebar",
    title: "收起右侧面板，独占主屏幕视窗",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "sidebar-tab-segment" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.activeTab = 'episodes';
        } },
    ...{ class: "side-tab-btn" },
    ...{ class: ({ active: __VLS_ctx.activeTab === 'episodes' }) },
    id: "tab-btn-episodes",
});
(__VLS_ctx.episodes.length);
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.activeTab = 'highlights';
        } },
    ...{ class: "side-tab-btn" },
    ...{ class: ({ active: __VLS_ctx.activeTab === 'highlights' }) },
    id: "tab-btn-highlights",
});
(__VLS_ctx.highlights.length);
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.activeTab = 'agent';
        } },
    ...{ class: "side-tab-btn" },
    ...{ class: ({ active: __VLS_ctx.activeTab === 'agent' }) },
    id: "tab-btn-agent",
});
if (__VLS_ctx.currentUser?.role === 'REVIEWER' || __VLS_ctx.currentUser?.role === 'ADMIN') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.currentUser?.role === 'REVIEWER' || __VLS_ctx.currentUser?.role === 'ADMIN'))
                    return;
                __VLS_ctx.activeTab = 'review';
            } },
        ...{ class: "side-tab-btn" },
        ...{ class: ({ active: __VLS_ctx.activeTab === 'review' }) },
        id: "tab-btn-review",
    });
}
if (__VLS_ctx.activeTab === 'episodes') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "panel-episodes-wrap" },
    });
    if (__VLS_ctx.episodeChunks.length > 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "episode-chunk-tabs-row" },
            id: "episode-chunk-tabs",
        });
        for (const [chunk] of __VLS_getVForSourceType((__VLS_ctx.episodeChunks))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!(__VLS_ctx.activeTab === 'episodes'))
                            return;
                        if (!(__VLS_ctx.episodeChunks.length > 0))
                            return;
                        __VLS_ctx.selectedChunk = chunk.label;
                    } },
                key: (chunk.label),
                ...{ class: "chunk-pill-btn" },
                ...{ class: ({ active: __VLS_ctx.selectedChunk === chunk.label }) },
                id: ('btn-chunk-' + chunk.label),
            });
            (chunk.label);
        }
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "episodes-scroll-window" },
        id: "episodes-scroll-viewport",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "episodes-bento-grid" },
    });
    for (const [ep] of __VLS_getVForSourceType((__VLS_ctx.visibleEpisodes))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.activeTab === 'episodes'))
                        return;
                    __VLS_ctx.switchEpisode(ep);
                } },
            key: (ep.id),
            ...{ class: "episode-tile-btn" },
            ...{ class: ({ active: __VLS_ctx.currentEpisode?.id === ep.id }) },
            id: ('ep-btn-' + ep.episode_num),
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "ep-num-line" },
        });
        (ep.episode_num);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "ep-title-sub" },
        });
        (ep.title);
    }
}
if (__VLS_ctx.activeTab === 'highlights') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "panel-highlights-wrap" },
        id: "panel-highlights",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "highlights-flow-list" },
    });
    for (const [h, idx] of __VLS_getVForSourceType((__VLS_ctx.highlights))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.activeTab === 'highlights'))
                        return;
                    __VLS_ctx.jumpToTimestamp(h.time, h.title);
                } },
            key: (idx),
            ...{ class: "highlight-card-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "highlight-time-badge" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "time-text" },
        });
        (__VLS_ctx.formatSeconds(h.time));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "jump-hint" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "highlight-info-box" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "highlight-title-line" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "highlight-title" },
        });
        (h.title);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "highlight-tag-pill" },
        });
        (h.tag);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "highlight-desc" },
        });
        (h.desc);
    }
}
if (__VLS_ctx.activeTab === 'agent') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "panel-agent-dock" },
        id: "panel-agent",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "agent-quick-prompts-row" },
    });
    for (const [p, idx] of __VLS_getVForSourceType((__VLS_ctx.quickPrompts))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.activeTab === 'agent'))
                        return;
                    __VLS_ctx.askQuickPrompt(p);
                } },
            key: (idx),
            ...{ class: "quick-prompt-pill" },
        });
        (p);
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "agent-chat-messages-scroll" },
        ref: "chatScrollRef",
    });
    /** @type {typeof __VLS_ctx.chatScrollRef} */ ;
    for (const [msg, idx] of __VLS_getVForSourceType((__VLS_ctx.agentMessages))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            key: (idx),
            ...{ class: "chat-bubble-row" },
            ...{ class: (msg.sender) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "bubble-avatar-squircle" },
        });
        (msg.sender === 'agent' ? '💬' : '👤');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "bubble-content-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "bubble-sender-name" },
        });
        (msg.sender === 'agent' ? '剧情伴读 (DeepSeek-R1)' : '我');
        if (msg.thought && msg.text) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "thought-collapsible-box" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.details, __VLS_intrinsicElements.details)({});
            __VLS_asFunctionalElement(__VLS_intrinsicElements.summary, __VLS_intrinsicElements.summary)({
                ...{ class: "thought-summary-badge" },
            });
            (msg.thought.length);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "thought-inner-text" },
            });
            (msg.thought);
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "bubble-body-text" },
        });
        (msg.text || msg.thought);
        if (msg.isTyping) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "stream-cursor" },
            });
        }
        if (msg.targetTime !== undefined) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "timestamp-jump-box" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!(__VLS_ctx.activeTab === 'agent'))
                            return;
                        if (!(msg.targetTime !== undefined))
                            return;
                        __VLS_ctx.jumpToTimestamp(msg.targetTime, msg.scene);
                    } },
                ...{ class: "jump-timestamp-btn" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "sparkle-icon" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
            (msg.timeTag);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "scene-label" },
            });
            (msg.scene);
        }
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "agent-input-dock" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        ...{ onKeyup: (__VLS_ctx.sendAgentQuestion) },
        id: "input-agent",
        ...{ class: "agent-pill-input" },
        placeholder: "提问本集核心反转、台词或画面细节...",
        disabled: (__VLS_ctx.isStreamingAgent),
    });
    (__VLS_ctx.agentInputText);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.sendAgentQuestion) },
        ...{ class: "apple-primary-btn" },
        id: "btn-send-agent",
        disabled: (__VLS_ctx.isStreamingAgent),
    });
    (__VLS_ctx.isStreamingAgent ? '思考中...' : '提问');
}
if (__VLS_ctx.activeTab === 'review') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "panel-review-wrap" },
        id: "panel-review",
    });
    if (__VLS_ctx.reviewQueue.length === 0) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty-review-state" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    for (const [item] of __VLS_getVForSourceType((__VLS_ctx.reviewQueue))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            key: (item.id),
            ...{ class: "review-record-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "record-meta-line" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "review-badge-red" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "violation-reason-tag" },
        });
        (item.violation_reason);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "violating-text-quote" },
        });
        (item.target_id);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "review-actions-row" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.activeTab === 'review'))
                        return;
                    __VLS_ctx.handleReviewDecision(item.id, 'APPROVED');
                } },
            ...{ class: "review-btn approve-btn" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.activeTab === 'review'))
                        return;
                    __VLS_ctx.handleReviewDecision(item.id, 'REJECTED');
                } },
            ...{ class: "review-btn reject-btn" },
        });
    }
}
const __VLS_36 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_37 = __VLS_asFunctionalComponent(__VLS_36, new __VLS_36({
    name: "apple-modal-fade",
}));
const __VLS_38 = __VLS_37({
    name: "apple-modal-fade",
}, ...__VLS_functionalComponentArgsRest(__VLS_37));
__VLS_39.slots.default;
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
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "modal-title" },
    });
    (__VLS_ctx.authMode === 'login' ? '账号登录' : '注册新账号');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showAuthModal))
                    return;
                __VLS_ctx.showAuthModal = false;
            } },
        ...{ class: "modal-close-icon-btn" },
        id: "btn-close-auth-modal",
    });
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
        required: true,
    });
    (__VLS_ctx.authForm.password);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        type: "submit",
        ...{ class: "apple-primary-btn modal-submit-btn" },
        id: "btn-submit-auth",
    });
    (__VLS_ctx.authMode === 'login' ? '立即登录' : '注册账号');
}
var __VLS_39;
const __VLS_40 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_41 = __VLS_asFunctionalComponent(__VLS_40, new __VLS_40({
    name: "apple-modal-fade",
}));
const __VLS_42 = __VLS_41({
    name: "apple-modal-fade",
}, ...__VLS_functionalComponentArgsRest(__VLS_41));
__VLS_43.slots.default;
if (__VLS_ctx.showFavoriteModal) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showFavoriteModal))
                    return;
                __VLS_ctx.showFavoriteModal = false;
            } },
        ...{ class: "apple-modal-backdrop" },
        id: "modal-player-favorites",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "apple-modal-card favorites-modal-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-card-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-header-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "modal-header-icon" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "modal-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showFavoriteModal))
                    return;
                __VLS_ctx.showFavoriteModal = false;
            } },
        ...{ class: "modal-close-icon-btn" },
        id: "btn-close-favorite-modal",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-body favorites-modal-body" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "drama-mini-preview" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.img)({
        src: (__VLS_ctx.album?.cover_url || __VLS_ctx.defaultCover),
        ...{ class: "mini-cover" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "mini-meta" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({
        ...{ class: "mini-title" },
    });
    (__VLS_ctx.album?.title || '当前短剧');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "mini-sub" },
    });
    (__VLS_ctx.album?.category || '短剧');
    (__VLS_ctx.episodes.length);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "folders-selection-list" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "section-label-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showFavoriteModal))
                    return;
                __VLS_ctx.showNewFolderInput = !__VLS_ctx.showNewFolderInput;
            } },
        ...{ class: "btn-text-action" },
        id: "btn-show-create-folder",
    });
    (__VLS_ctx.showNewFolderInput ? '收起' : '+ 新建收藏夹');
    if (__VLS_ctx.showNewFolderInput) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "inline-new-folder-box" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            ...{ onKeyup: (__VLS_ctx.handleCreateFolderInModal) },
            id: "input-new-folder-name",
            ...{ class: "apple-form-input mini" },
            placeholder: "输入收藏夹名称...",
            maxlength: "30",
        });
        (__VLS_ctx.newFolderName);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            ...{ class: "privacy-switch-label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            type: "checkbox",
            id: "checkbox-folder-public",
        });
        (__VLS_ctx.newFolderIsPublic);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (__VLS_ctx.handleCreateFolderInModal) },
            ...{ class: "apple-primary-btn mini-btn" },
            id: "btn-confirm-create-folder",
            disabled: (!__VLS_ctx.newFolderName.trim()),
        });
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "folder-items-scroll" },
    });
    for (const [folder] of __VLS_getVForSourceType((__VLS_ctx.userFolders))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.showFavoriteModal))
                        return;
                    __VLS_ctx.toggleFolderSelection(folder.id);
                } },
            key: (folder.id),
            ...{ class: "folder-select-item" },
            ...{ class: ({ selected: __VLS_ctx.selectedFolderIds.includes(folder.id) }) },
            id: ('folder-item-' + folder.id),
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "folder-select-left" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.showFavoriteModal))
                        return;
                    __VLS_ctx.toggleFolderSelection(folder.id);
                } },
            type: "checkbox",
            ...{ class: "apple-checkbox" },
            checked: (__VLS_ctx.selectedFolderIds.includes(folder.id)),
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "folder-name-text" },
        });
        (folder.name);
        if (folder.is_default) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "badge-default-tag" },
            });
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "badge-privacy-tag" },
        });
        (folder.is_public ? '公开' : '私密');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "folder-count-badge" },
        });
        (folder.item_count);
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-footer favorites-modal-footer" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.handleQuickDefaultSave) },
        ...{ class: "apple-btn-secondary" },
        id: "btn-quick-default-fav",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.handleSaveToSelectedFolders) },
        ...{ class: "apple-primary-btn" },
        id: "btn-save-favorites",
        disabled: (__VLS_ctx.isSavingFavorite),
    });
    (__VLS_ctx.isSavingFavorite ? '保存中...' : `确认保存 (${__VLS_ctx.selectedFolderIds.length})`);
}
var __VLS_43;
const __VLS_44 = {}.transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.transition, typeof __VLS_components.Transition, typeof __VLS_components.transition, ]} */ ;
// @ts-ignore
const __VLS_45 = __VLS_asFunctionalComponent(__VLS_44, new __VLS_44({
    name: "apple-modal-fade",
}));
const __VLS_46 = __VLS_45({
    name: "apple-modal-fade",
}, ...__VLS_functionalComponentArgsRest(__VLS_45));
__VLS_47.slots.default;
if (__VLS_ctx.showCoinModal) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showCoinModal))
                    return;
                __VLS_ctx.showCoinModal = false;
            } },
        ...{ class: "apple-modal-backdrop modal-overlay" },
        id: "coin-tip-modal",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "apple-glass-dialog modal-card coin-tip-dialog" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-title-wrap" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "modal-emoji" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({
        ...{ class: "modal-title" },
    });
    (__VLS_ctx.album?.title);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showCoinModal))
                    return;
                __VLS_ctx.showCoinModal = false;
            } },
        ...{ class: "modal-close-btn" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-body" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "wallet-balance-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "wallet-label" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "wallet-val" },
    });
    (__VLS_ctx.userWalletBalance);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "tipping-status-box" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "tip-status-text" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({});
    (__VLS_ctx.userTippedCount);
    if (__VLS_ctx.userTippedCount >= 2) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "max-tip-badge" },
        });
    }
    if (__VLS_ctx.tipSuccessTip) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "tip-success-banner" },
        });
        (__VLS_ctx.tipSuccessTip);
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "tipping-options-grid" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showCoinModal))
                    return;
                __VLS_ctx.executeTip(1);
            } },
        ...{ class: "tip-option-card" },
        id: "btn-tip-1-coin",
        disabled: (__VLS_ctx.isTipping || __VLS_ctx.userTippedCount >= 2 || (__VLS_ctx.userTippedCount + 1 > 2) || __VLS_ctx.userWalletBalance < 1),
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "option-coin-icon" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "option-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "option-sub" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showCoinModal))
                    return;
                __VLS_ctx.executeTip(2);
            } },
        ...{ class: "tip-option-card" },
        id: "btn-tip-2-coins",
        disabled: (__VLS_ctx.isTipping || __VLS_ctx.userTippedCount >= 1 || (__VLS_ctx.userTippedCount + 2 > 2) || __VLS_ctx.userWalletBalance < 2),
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "option-coin-icon" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "option-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "option-sub" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "modal-footer" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.showCoinModal))
                    return;
                __VLS_ctx.showCoinModal = false;
            } },
        ...{ class: "apple-btn-secondary" },
    });
}
var __VLS_47;
/** @type {[typeof NotificationSkylight, ]} */ ;
// @ts-ignore
const __VLS_48 = __VLS_asFunctionalComponent(NotificationSkylight, new NotificationSkylight({
    ...{ 'onUnreadCountChanged': {} },
    modelValue: (__VLS_ctx.showSkylightDrawer),
    unreadCounts: (__VLS_ctx.unreadCounts),
}));
const __VLS_49 = __VLS_48({
    ...{ 'onUnreadCountChanged': {} },
    modelValue: (__VLS_ctx.showSkylightDrawer),
    unreadCounts: (__VLS_ctx.unreadCounts),
}, ...__VLS_functionalComponentArgsRest(__VLS_48));
let __VLS_51;
let __VLS_52;
let __VLS_53;
const __VLS_54 = {
    onUnreadCountChanged: (__VLS_ctx.fetchUnreadCount)
};
var __VLS_50;
/** @type {__VLS_StyleScopedClasses['apple-player-page']} */ ;
/** @type {__VLS_StyleScopedClasses['player-global-header']} */ ;
/** @type {__VLS_StyleScopedClasses['header-inner']} */ ;
/** @type {__VLS_StyleScopedClasses['header-left']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-back-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['back-svg']} */ ;
/** @type {__VLS_StyleScopedClasses['header-divider']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-headline-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-title-text']} */ ;
/** @type {__VLS_StyleScopedClasses['episode-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['header-center']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-mode-switcher-capsule']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-switch-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-switch-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['header-right']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-trigger-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-bell-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['skylight-unread-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['user-chip-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['avatar-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['user-info-text']} */ ;
/** @type {__VLS_StyleScopedClasses['user-name-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['user-role-badge-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['logout-link-mini']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['mini-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['resume-toast-capsule']} */ ;
/** @type {__VLS_StyleScopedClasses['toast-sparkle']} */ ;
/** @type {__VLS_StyleScopedClasses['toast-msg']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-stage-container']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-player-column']} */ ;
/** @type {__VLS_StyleScopedClasses['video-viewport-box']} */ ;
/** @type {__VLS_StyleScopedClasses['mobile-notch-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['notch-speaker']} */ ;
/** @type {__VLS_StyleScopedClasses['notch-title']} */ ;
/** @type {__VLS_StyleScopedClasses['video-media-wrapper']} */ ;
/** @type {__VLS_StyleScopedClasses['core-video-element']} */ ;
/** @type {__VLS_StyleScopedClasses['danmaku-screen-layer']} */ ;
/** @type {__VLS_StyleScopedClasses['danmaku-flying-bullet']} */ ;
/** @type {__VLS_StyleScopedClasses['play-splash-circle']} */ ;
/** @type {__VLS_StyleScopedClasses['splash-svg']} */ ;
/** @type {__VLS_StyleScopedClasses['autoplay-countdown-hud']} */ ;
/** @type {__VLS_StyleScopedClasses['autoplay-countdown-hud-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-header']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-sparkle-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-body']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-timer-circle']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-timer-num']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-timer-unit']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-next-info']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-next-label']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-next-title']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-actions-row']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-btn-primary']} */ ;
/** @type {__VLS_StyleScopedClasses['hud-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['player-controls-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['progress-track-wrapper']} */ ;
/** @type {__VLS_StyleScopedClasses['progress-bar-bg']} */ ;
/** @type {__VLS_StyleScopedClasses['progress-bar-fill']} */ ;
/** @type {__VLS_StyleScopedClasses['progress-handle']} */ ;
/** @type {__VLS_StyleScopedClasses['controls-action-line']} */ ;
/** @type {__VLS_StyleScopedClasses['ctrl-left']} */ ;
/** @type {__VLS_StyleScopedClasses['icon-ctrl-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['ctrl-svg']} */ ;
/** @type {__VLS_StyleScopedClasses['ctrl-svg']} */ ;
/** @type {__VLS_StyleScopedClasses['timestamp-display']} */ ;
/** @type {__VLS_StyleScopedClasses['danmaku-send-box']} */ ;
/** @type {__VLS_StyleScopedClasses['danmaku-pill-input']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-danmaku-send']} */ ;
/** @type {__VLS_StyleScopedClasses['ctrl-right']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-ctrl-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['autoplay-toggle-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['autoplay-indicator-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['speed-menu-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-ctrl-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-popover-glass']} */ ;
/** @type {__VLS_StyleScopedClasses['popover-item']} */ ;
/** @type {__VLS_StyleScopedClasses['resolution-menu-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-ctrl-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['dropdown-popover-glass']} */ ;
/** @type {__VLS_StyleScopedClasses['popover-item']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-quick-toggle']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-quick-toggle']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-quick-toggle']} */ ;
/** @type {__VLS_StyleScopedClasses['mode-quick-toggle']} */ ;
/** @type {__VLS_StyleScopedClasses['video-meta-card']} */ ;
/** @type {__VLS_StyleScopedClasses['meta-titles-row']} */ ;
/** @type {__VLS_StyleScopedClasses['video-main-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['video-stats-labels']} */ ;
/** @type {__VLS_StyleScopedClasses['action-pills-row']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-action-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-like']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-emoji']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-action-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-emoji']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-action-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-emoji']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-action-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['pill-emoji']} */ ;
/** @type {__VLS_StyleScopedClasses['comments-bento-card']} */ ;
/** @type {__VLS_StyleScopedClasses['comments-card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-compose-box']} */ ;
/** @type {__VLS_StyleScopedClasses['compose-avatar']} */ ;
/** @type {__VLS_StyleScopedClasses['compose-input-area']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-textarea']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['comments-flow-list']} */ ;
/** @type {__VLS_StyleScopedClasses['comments-empty-state']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-emoji']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-thread-card']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-bubble-item']} */ ;
/** @type {__VLS_StyleScopedClasses['root-bubble']} */ ;
/** @type {__VLS_StyleScopedClasses['commenter-avatar']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-body']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-author-line']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-name']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-time']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-content-text']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-actions-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['like-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['action-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['action-count']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['reply-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['action-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-thread-container']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-bubble-item']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-bubble']} */ ;
/** @type {__VLS_StyleScopedClasses['commenter-avatar']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-avatar']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-body']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-author-line']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-name']} */ ;
/** @type {__VLS_StyleScopedClasses['mention-target-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-time']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-content-text']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-actions-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['like-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['action-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['action-count']} */ ;
/** @type {__VLS_StyleScopedClasses['comment-action-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['reply-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['action-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['inline-reply-box']} */ ;
/** @type {__VLS_StyleScopedClasses['reply-input-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['replying-to-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['reply-textarea']} */ ;
/** @type {__VLS_StyleScopedClasses['reply-box-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['reply-cancel-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['reply-submit-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['floating-expand-sidebar-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['theater-sidebar-column']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-top-control-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-top-title']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-collapse-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-tab-segment']} */ ;
/** @type {__VLS_StyleScopedClasses['side-tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['side-tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['side-tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['side-tab-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['panel-episodes-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['episode-chunk-tabs-row']} */ ;
/** @type {__VLS_StyleScopedClasses['chunk-pill-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['episodes-scroll-window']} */ ;
/** @type {__VLS_StyleScopedClasses['episodes-bento-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['episode-tile-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['ep-num-line']} */ ;
/** @type {__VLS_StyleScopedClasses['ep-title-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['panel-highlights-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['highlights-flow-list']} */ ;
/** @type {__VLS_StyleScopedClasses['highlight-card-item']} */ ;
/** @type {__VLS_StyleScopedClasses['highlight-time-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['time-text']} */ ;
/** @type {__VLS_StyleScopedClasses['jump-hint']} */ ;
/** @type {__VLS_StyleScopedClasses['highlight-info-box']} */ ;
/** @type {__VLS_StyleScopedClasses['highlight-title-line']} */ ;
/** @type {__VLS_StyleScopedClasses['highlight-title']} */ ;
/** @type {__VLS_StyleScopedClasses['highlight-tag-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['highlight-desc']} */ ;
/** @type {__VLS_StyleScopedClasses['panel-agent-dock']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-quick-prompts-row']} */ ;
/** @type {__VLS_StyleScopedClasses['quick-prompt-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-chat-messages-scroll']} */ ;
/** @type {__VLS_StyleScopedClasses['chat-bubble-row']} */ ;
/** @type {__VLS_StyleScopedClasses['bubble-avatar-squircle']} */ ;
/** @type {__VLS_StyleScopedClasses['bubble-content-card']} */ ;
/** @type {__VLS_StyleScopedClasses['bubble-sender-name']} */ ;
/** @type {__VLS_StyleScopedClasses['thought-collapsible-box']} */ ;
/** @type {__VLS_StyleScopedClasses['thought-summary-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['thought-inner-text']} */ ;
/** @type {__VLS_StyleScopedClasses['bubble-body-text']} */ ;
/** @type {__VLS_StyleScopedClasses['stream-cursor']} */ ;
/** @type {__VLS_StyleScopedClasses['timestamp-jump-box']} */ ;
/** @type {__VLS_StyleScopedClasses['jump-timestamp-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['sparkle-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['scene-label']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-input-dock']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-pill-input']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['panel-review-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-review-state']} */ ;
/** @type {__VLS_StyleScopedClasses['review-record-card']} */ ;
/** @type {__VLS_StyleScopedClasses['record-meta-line']} */ ;
/** @type {__VLS_StyleScopedClasses['review-badge-red']} */ ;
/** @type {__VLS_StyleScopedClasses['violation-reason-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['violating-text-quote']} */ ;
/** @type {__VLS_StyleScopedClasses['review-actions-row']} */ ;
/** @type {__VLS_StyleScopedClasses['review-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['approve-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['review-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['reject-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-modal-backdrop']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-modal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-title']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-close-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-form']} */ ;
/** @type {__VLS_StyleScopedClasses['form-field-group']} */ ;
/** @type {__VLS_StyleScopedClasses['field-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['form-field-group']} */ ;
/** @type {__VLS_StyleScopedClasses['field-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-submit-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-modal-backdrop']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-modal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['favorites-modal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-header-title']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-header-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-title']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-close-icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-body']} */ ;
/** @type {__VLS_StyleScopedClasses['favorites-modal-body']} */ ;
/** @type {__VLS_StyleScopedClasses['drama-mini-preview']} */ ;
/** @type {__VLS_StyleScopedClasses['mini-cover']} */ ;
/** @type {__VLS_StyleScopedClasses['mini-meta']} */ ;
/** @type {__VLS_StyleScopedClasses['mini-title']} */ ;
/** @type {__VLS_StyleScopedClasses['mini-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['folders-selection-list']} */ ;
/** @type {__VLS_StyleScopedClasses['section-label-row']} */ ;
/** @type {__VLS_StyleScopedClasses['btn-text-action']} */ ;
/** @type {__VLS_StyleScopedClasses['inline-new-folder-box']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-form-input']} */ ;
/** @type {__VLS_StyleScopedClasses['mini']} */ ;
/** @type {__VLS_StyleScopedClasses['privacy-switch-label']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['mini-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-items-scroll']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-select-item']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-select-left']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-checkbox']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-name-text']} */ ;
/** @type {__VLS_StyleScopedClasses['badge-default-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['badge-privacy-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['folder-count-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['favorites-modal-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-primary-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-modal-backdrop']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-glass-dialog']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-card']} */ ;
/** @type {__VLS_StyleScopedClasses['coin-tip-dialog']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-header']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-title-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-emoji']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-title']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-close-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-body']} */ ;
/** @type {__VLS_StyleScopedClasses['wallet-balance-row']} */ ;
/** @type {__VLS_StyleScopedClasses['wallet-label']} */ ;
/** @type {__VLS_StyleScopedClasses['wallet-val']} */ ;
/** @type {__VLS_StyleScopedClasses['tipping-status-box']} */ ;
/** @type {__VLS_StyleScopedClasses['tip-status-text']} */ ;
/** @type {__VLS_StyleScopedClasses['max-tip-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['tip-success-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['tipping-options-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['tip-option-card']} */ ;
/** @type {__VLS_StyleScopedClasses['option-coin-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['option-title']} */ ;
/** @type {__VLS_StyleScopedClasses['option-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['tip-option-card']} */ ;
/** @type {__VLS_StyleScopedClasses['option-coin-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['option-title']} */ ;
/** @type {__VLS_StyleScopedClasses['option-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['modal-footer']} */ ;
/** @type {__VLS_StyleScopedClasses['apple-btn-secondary']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            Bell: Bell,
            NotificationSkylight: NotificationSkylight,
            defaultAvatar: defaultAvatar,
            defaultCover: defaultCover,
            videoRef: videoRef,
            chatScrollRef: chatScrollRef,
            displayMode: displayMode,
            activeTab: activeTab,
            isWebFullscreen: isWebFullscreen,
            isSidebarCollapsed: isSidebarCollapsed,
            toggleWebFullscreen: toggleWebFullscreen,
            toggleNativeFullscreen: toggleNativeFullscreen,
            isAutoplayEnabled: isAutoplayEnabled,
            showCountdownHud: showCountdownHud,
            countdownSeconds: countdownSeconds,
            toggleAutoplay: toggleAutoplay,
            isFavorited: isFavorited,
            favoriteCount: favoriteCount,
            showFavoriteModal: showFavoriteModal,
            userFolders: userFolders,
            selectedFolderIds: selectedFolderIds,
            showNewFolderInput: showNewFolderInput,
            newFolderName: newFolderName,
            newFolderIsPublic: newFolderIsPublic,
            isSavingFavorite: isSavingFavorite,
            showCoinModal: showCoinModal,
            videoCoinCount: videoCoinCount,
            userWalletBalance: userWalletBalance,
            userTippedCount: userTippedCount,
            isTipping: isTipping,
            tipSuccessTip: tipSuccessTip,
            currentRate: currentRate,
            showSpeedMenu: showSpeedMenu,
            currentResolution: currentResolution,
            showResMenu: showResMenu,
            openSpeedMenu: openSpeedMenu,
            closeSpeedMenuDebounced: closeSpeedMenuDebounced,
            openResMenu: openResMenu,
            closeResMenuDebounced: closeResMenuDebounced,
            setPlaybackRate: setPlaybackRate,
            setResolution: setResolution,
            highlights: highlights,
            isPlaying: isPlaying,
            currentTime: currentTime,
            duration: duration,
            progressPercent: progressPercent,
            album: album,
            episodes: episodes,
            currentEpisode: currentEpisode,
            currentStreamUrl: currentStreamUrl,
            selectedChunk: selectedChunk,
            episodeChunks: episodeChunks,
            visibleEpisodes: visibleEpisodes,
            isLiked: isLiked,
            likeCount: likeCount,
            resumeToast: resumeToast,
            showSkylightDrawer: showSkylightDrawer,
            unreadCounts: unreadCounts,
            fetchUnreadCount: fetchUnreadCount,
            comments: comments,
            commentsTotal: commentsTotal,
            commentText: commentText,
            isSubmittingComment: isSubmittingComment,
            activeReplyRootId: activeReplyRootId,
            replyTargetName: replyTargetName,
            replyText: replyText,
            isSubmittingReply: isSubmittingReply,
            highlightedCommentId: highlightedCommentId,
            formatNumber: formatNumber,
            danmakuInputText: danmakuInputText,
            activeDanmakus: activeDanmakus,
            agentInputText: agentInputText,
            isStreamingAgent: isStreamingAgent,
            quickPrompts: quickPrompts,
            agentMessages: agentMessages,
            reviewQueue: reviewQueue,
            currentUser: currentUser,
            showAuthModal: showAuthModal,
            authMode: authMode,
            authForm: authForm,
            nextEpisode: nextEpisode,
            executeNextEpisodeImmediately: executeNextEpisodeImmediately,
            cancelCountdownAutoplay: cancelCountdownAutoplay,
            switchEpisode: switchEpisode,
            togglePlay: togglePlay,
            onTimeUpdate: onTimeUpdate,
            onLoadedMetadata: onLoadedMetadata,
            onVideoEnded: onVideoEnded,
            handleSeekClick: handleSeekClick,
            jumpToTimestamp: jumpToTimestamp,
            formatSeconds: formatSeconds,
            sendDanmaku: sendDanmaku,
            handleToggleLike: handleToggleLike,
            handleCoin: handleCoin,
            executeTip: executeTip,
            handleFavoriteClick: handleFavoriteClick,
            toggleFolderSelection: toggleFolderSelection,
            handleCreateFolderInModal: handleCreateFolderInModal,
            handleQuickDefaultSave: handleQuickDefaultSave,
            handleSaveToSelectedFolders: handleSaveToSelectedFolders,
            handleShare: handleShare,
            submitComment: submitComment,
            toggleReplyInput: toggleReplyInput,
            cancelReply: cancelReply,
            submitReply: submitReply,
            handleToggleCommentLike: handleToggleCommentLike,
            sendAgentQuestion: sendAgentQuestion,
            askQuickPrompt: askQuickPrompt,
            handleReviewDecision: handleReviewDecision,
            getRoleLabel: getRoleLabel,
            handleLogout: handleLogout,
            handleAuthSubmit: handleAuthSubmit,
        };
    },
    __typeProps: {},
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
    __typeProps: {},
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=PlayerView.vue.js.map