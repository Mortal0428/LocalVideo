import { api } from './client'

export interface FavoriteFolder {
  id: string
  user_id: string
  name: string
  is_default: boolean
  is_public: boolean
  description: string
  item_count: number
  created_at: string | null
  updated_at: string | null
}

export interface FavoriteVideoDetail {
  id: string
  title: string
  cover_url: string | null
  category: string
  summary: string
  total_episodes: number
  author: string
  duration: number
  first_episode_id: string | null
}

export interface FavoriteItem {
  id: string
  folder_id: string
  video_id: string
  created_at: string | null
  video: FavoriteVideoDetail
}

export interface FavoriteStatus {
  is_favorited: boolean
  folder_ids: string[]
  item_ids: string[]
}

export interface CreateFolderParams {
  name: string
  is_public?: boolean
  description?: string
}

export interface UpdateFolderParams {
  name?: string
  is_public?: boolean
  description?: string
}

export interface AddItemParams {
  video_id: string
  folder_id?: string
  folder_ids?: string[]
}

export const favoritesApi = {
  getFolders: () => {
    return api.get<FavoriteFolder[]>('/favorites/folders')
  },

  createFolder: (data: CreateFolderParams) => {
    return api.post<FavoriteFolder>('/favorites/folders', data)
  },

  updateFolder: (folderId: string, data: UpdateFolderParams) => {
    return api.put<FavoriteFolder>(`/favorites/folders/${folderId}`, data)
  },

  deleteFolder: (folderId: string) => {
    return api.delete<{ success: boolean; message: string }>(`/favorites/folders/${folderId}`)
  },

  getFolderItems: (folderId: string) => {
    return api.get<FavoriteItem[]>(`/favorites/folders/${folderId}/items`)
  },

  addItem: (data: AddItemParams) => {
    return api.post<{ success: boolean; message: string; video_id: string; folder_ids: string[] }>('/favorites/items', data)
  },

  removeItem: (itemOrVideoId: string) => {
    return api.delete<{ success: boolean; message: string }>(`/favorites/items/${itemOrVideoId}`)
  },

  removeFolderItem: (folderId: string, videoId: string) => {
    return api.delete<{ success: boolean; message: string }>(`/favorites/folders/${folderId}/items/${videoId}`)
  },

  getStatus: (videoId: string) => {
    return api.get<FavoriteStatus>(`/favorites/status/${videoId}`)
  },

  quickDefaultToggle: (videoId: string) => {
    return api.post<{ success: boolean; is_favorited: boolean; message: string }>('/favorites/quick-default', { video_id: videoId })
  }
}
