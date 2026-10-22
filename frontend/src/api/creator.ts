import { api } from './client'
import type { ApiResponse } from './auth'

export interface CloudDiskItem {
  name: string
  size: number
  is_dir: boolean
  modified?: string
  thumb?: string
  path: string
}

export interface CloudDiskTreeData {
  current_path: string
  parent_path: string
  total_count: number
  folders: CloudDiskItem[]
  files: CloudDiskItem[]
}

export interface CreatorDramaItem {
  id: string
  title: string
  description?: string
  category?: string
  cover_url?: string
  episodes_count?: number
  total_episodes?: number
  play_count?: number
  view_count?: number
  like_count?: number
  coin_count?: number
  viral_score?: number
  status: string
  created_at: string
}

export interface CreatorEpisodeItem {
  id: string
  episode_num: number
  title: string
  duration_seconds: number
  status: string
  raw_file_path: string
  climax_seconds?: number | null
  created_at: string
}

export const creatorApi = {
  apply: (data: { creator_name: string; bio?: string }) => {
    return api.post<any, ApiResponse<any>>('/creator/apply', data)
  },

  getPanTree: (path?: string) => {
    return api.get<any, ApiResponse<CloudDiskTreeData>>('/creator/pan/tree', {
      params: { path: path || '/kuake/红果项目资源目录' }
    })
  },

  mkdir: (folder_name: string, parent_path?: string) => {
    return api.post<any, ApiResponse<{ path: string; folder_name: string }>>('/creator/pan/mkdir', {
      folder_name,
      parent_path: parent_path || '/kuake/红果项目资源目录'
    })
  },

  uploadVideo: (formData: FormData) => {
    return api.post<any, ApiResponse<any>>('/creator/pan/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  getMyDramas: () => {
    return api.get<any, ApiResponse<CreatorDramaItem[]>>('/creator/dramas')
  },

  getDramaEpisodes: (dramaId: string) => {
    return api.get<any, ApiResponse<{ drama_id: string; drama_title: string; total_count: number; episodes: CreatorEpisodeItem[] }>>(`/creator/dramas/${dramaId}/episodes`)
  },

  updateDrama: (dramaId: string, data: { title?: string; category?: string; description?: string; cover_url?: string; status?: string }) => {
    return api.put<any, ApiResponse<CreatorDramaItem>>(`/creator/dramas/${dramaId}`, data)
  },

  updateEpisode: (episodeId: string, data: { title?: string; episode_num?: number; climax_seconds?: number }) => {
    return api.put<any, ApiResponse<CreatorEpisodeItem>>(`/creator/episodes/${episodeId}`, data)
  },

  deleteDrama: (dramaId: string) => {
    return api.delete<any, ApiResponse<any>>(`/creator/dramas/${dramaId}`)
  },

  syncDramas: () => {
    return api.post<any, ApiResponse<any>>('/creator/pan/sync-dramas')
  }
}
