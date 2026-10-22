import { api } from './client';
export const adminApi = {
    getOverview: () => {
        return api.get('/admin/overview');
    },
    getBiMetrics: () => {
        return api.get('/admin/bi-metrics');
    },
    getBiTrends: () => {
        return api.get('/admin/bi-trends');
    },
    getUsers: (params) => {
        return api.get('/admin/users', {
            params
        });
    },
    createUser: (data) => {
        return api.post('/admin/users', data);
    },
    updateUser: (userId, data) => {
        return api.put(`/admin/users/${userId}`, data);
    },
    deleteUser: (userId) => {
        return api.delete(`/admin/users/${userId}`);
    },
    batchDeleteUsers: (userIds) => {
        return api.post('/admin/users/batch-delete', { user_ids: userIds });
    },
    adjustUserCoins: (userId, amount, reason, vip_days) => {
        return api.post(`/admin/users/${userId}/adjust-coins`, { amount, reason, vip_days });
    },
    updateUserStatus: (user_id, status) => {
        return api.post(`/admin/users/${user_id}/status`, { status });
    },
    updateUserRole: (user_id, role) => {
        return api.post(`/admin/users/${user_id}/role`, { role });
    },
    getApplications: () => {
        return api.get('/admin/applications');
    },
    reviewCreator: (user_id, action, remarks) => {
        return api.post('/admin/creators/review', {
            user_id,
            action,
            remarks
        });
    },
    reviewReviewer: (user_id, action, remarks) => {
        return api.post('/admin/reviewers/review', {
            user_id,
            action,
            remarks
        });
    },
    getDanmakus: (params) => {
        return api.get('/admin/contents/danmakus', { params });
    },
    deleteDanmaku: (id) => {
        return api.delete(`/admin/contents/danmakus/${id}`);
    },
    batchDeleteDanmakus: (ids) => {
        return api.post('/admin/contents/danmakus/batch-delete', { ids });
    },
    getComments: (params) => {
        return api.get('/admin/contents/comments', { params });
    },
    deleteComment: (id) => {
        return api.delete(`/admin/contents/comments/${id}`);
    },
    getDramas: (params) => {
        return api.get('/admin/dramas', { params });
    },
    updateDrama: (id, data) => {
        return api.put(`/admin/dramas/${id}`, data);
    },
    toggleDramaStatus: (id, status) => {
        return api.post(`/admin/dramas/${id}/status`, { status });
    },
    updateDramaCover: (id, cover_url) => {
        return api.put(`/admin/dramas/${id}/cover`, { cover_url });
    },
    updateDramaPosters: (id, extra_images) => {
        return api.put(`/admin/dramas/${id}/posters`, { extra_images });
    },
    deleteDrama: (id) => {
        return api.delete(`/admin/dramas/${id}`);
    },
    batchDeleteDramas: (dramaIds) => {
        return api.post('/admin/dramas/batch-delete', { drama_ids: dramaIds });
    },
    getDramaOptions: () => {
        return api.get('/admin/dramas/options');
    },
    uploadImage: (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/upload/image', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },
    syncPanAll: (mode = 'incremental') => {
        return api.post('/admin/pan/sync-all', {}, { params: { mode } });
    },
    getCarousels: () => {
        return api.get('/admin/carousels');
    },
    createCarousel: (data) => {
        return api.post('/admin/carousels', data);
    },
    updateCarousel: (id, data) => {
        return api.put(`/admin/carousels/${id}`, data);
    },
    deleteCarousel: (id) => {
        return api.delete(`/admin/carousels/${id}`);
    },
    getReviewQueue: (status = 'PENDING') => {
        return api.get('/review/queue', { params: { status } });
    },
    makeReviewDecision: (review_id, decision, notes) => {
        return api.post('/review/decision', { review_id, decision, notes });
    },
    getSensitiveWords: (params) => {
        return api.get('/review/sensitive-words', { params });
    },
    addSensitiveWord: (data) => {
        return api.post('/review/sensitive-words', data);
    },
    deleteSensitiveWord: (word_id) => {
        return api.delete(`/review/sensitive-words/${word_id}`);
    },
    testSensitiveWords: (text) => {
        return api.post('/review/sensitive-words/test', { text });
    },
    getDualModelSettings: () => {
        return api.get('/models/dual-settings');
    },
    updateDualModelSettings: (data) => {
        return api.put('/models/dual-settings', data);
    },
    testChatConnection: (data) => {
        return api.post('/models/test-connection', data);
    },
    testEmbeddingConnection: (data) => {
        return api.post('/models/test-embedding', data);
    }
};
//# sourceMappingURL=admin.js.map