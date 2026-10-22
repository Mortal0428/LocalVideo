import { api } from './client';
export const creatorApi = {
    apply: (data) => {
        return api.post('/creator/apply', data);
    },
    getPanTree: (path) => {
        return api.get('/creator/pan/tree', {
            params: { path: path || '/kuake/红果项目资源目录' }
        });
    },
    mkdir: (folder_name, parent_path) => {
        return api.post('/creator/pan/mkdir', {
            folder_name,
            parent_path: parent_path || '/kuake/红果项目资源目录'
        });
    },
    uploadVideo: (formData) => {
        return api.post('/creator/pan/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },
    uploadChunk: (formData) => {
        return api.post('/creator/pan/upload-chunk', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },
    mergeChunks: (formData) => {
        return api.post('/creator/pan/merge-chunk', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },
    getMyDramas: () => {
        return api.get('/creator/dramas');
    },
    getDramaEpisodes: (dramaId) => {
        return api.get(`/creator/dramas/${dramaId}/episodes`);
    },
    updateDrama: (dramaId, data) => {
        return api.put(`/creator/dramas/${dramaId}`, data);
    },
    updateEpisode: (episodeId, data) => {
        return api.put(`/creator/episodes/${episodeId}`, data);
    },
    deleteDrama: (dramaId) => {
        return api.delete(`/creator/dramas/${dramaId}`);
    },
    syncDramas: () => {
        return api.post('/creator/pan/sync-dramas');
    }
};
//# sourceMappingURL=creator.js.map