import { api } from './client';
export const favoritesApi = {
    getFolders: () => {
        return api.get('/favorites/folders');
    },
    createFolder: (data) => {
        return api.post('/favorites/folders', data);
    },
    updateFolder: (folderId, data) => {
        return api.put(`/favorites/folders/${folderId}`, data);
    },
    deleteFolder: (folderId) => {
        return api.delete(`/favorites/folders/${folderId}`);
    },
    getFolderItems: (folderId) => {
        return api.get(`/favorites/folders/${folderId}/items`);
    },
    addItem: (data) => {
        return api.post('/favorites/items', data);
    },
    removeItem: (itemOrVideoId) => {
        return api.delete(`/favorites/items/${itemOrVideoId}`);
    },
    removeFolderItem: (folderId, videoId) => {
        return api.delete(`/favorites/folders/${folderId}/items/${videoId}`);
    },
    getStatus: (videoId) => {
        return api.get(`/favorites/status/${videoId}`);
    },
    quickDefaultToggle: (videoId) => {
        return api.post('/favorites/quick-default', { video_id: videoId });
    }
};
//# sourceMappingURL=favorites.js.map