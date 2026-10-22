import { api } from './client';
export const userApi = {
    getProfile: () => {
        return api.get('/user/profile');
    },
    updateProfile: (data) => {
        return api.put('/user/profile', data);
    },
    applyCreator: (data) => {
        return api.post('/user/apply-creator', data);
    },
    applyReviewer: (data) => {
        return api.post('/user/apply-reviewer', data);
    },
    getHistory: () => {
        return api.get('/user/history');
    },
    getLikes: () => {
        return api.get('/user/likes');
    },
    getCoinWallet: () => {
        return api.get('/user/coins/wallet');
    },
    dailySignIn: () => {
        return api.post('/user/coins/sign-in');
    },
    watchAdReward: () => {
        return api.post('/user/coins/watch-ad');
    },
    exchangeVip: (data) => {
        return api.post('/user/coins/exchange-vip', data);
    }
};
export const notificationApi = {
    async getNotifications(category, page = 1, perPage = 20) {
        return api.get('/notifications', { params: { category, page, per_page: perPage } });
    },
    async getUnreadCount() {
        return api.get('/notifications/unread-count');
    },
    async markRead(notificationId) {
        return api.post(`/notifications/${notificationId}/read`);
    },
    async markAllRead(category) {
        return api.post('/notifications/read-all', {}, { params: { category } });
    }
};
//# sourceMappingURL=user.js.map