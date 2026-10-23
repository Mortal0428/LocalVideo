import { api } from './client'
import type { ApiResponse } from './auth'

export interface AdminBiCards {
  total_views: number
  total_danmakus: number
  total_comments: number
  total_likes: number
  total_users: number
  active_creators: number
  active_reviewers: number
  banned_users: number
  pending_applications: number
  total_dramas: number
  total_episodes: number
}

export interface AdminBiMetricsData {
  bi_cards: AdminBiCards
  categories_distribution: Array<{ name: string; count: number }>
  cloud_storage: {
    status: string
    mount_path: string
    items_count: number
  }
  ai_engine: {
    active_model: string
    rag_status: string
    temperature: number
  }
}

export interface AdminUserItem {
  id: string
  username: string
  nickname?: string
  role: string
  is_creator: boolean
  is_reviewer: boolean
  status: 'ACTIVE' | 'BANNED'
  coins?: number
  vip_expire_at?: string
  is_vip?: boolean
  creator_application_status?: string
  creator_bio?: string
  reviewer_application_status?: string
  reviewer_bio?: string
  created_at: string
}

export interface AdminOverviewData {
  total_users: number
  active_creators: number
  banned_users: number
  pending_creators: number
  pending_reviewers: number
  total_dramas: number
  total_episodes: number
  cloud_disk_status: string
  active_mount: string
}

export interface ApplicationItem {
  user_id: string
  username: string
  nickname?: string
  bio?: string
  status: string
  applied_at: string
}

export interface ApplicationsData {
  creators: ApplicationItem[]
  reviewers: ApplicationItem[]
}

export interface AdminDanmakuItem {
  id: string
  content: string
  color: string
  track: number
  speed: number
  timestamp: number
  user_id: string
  user_name: string
  video_title: string
  episode_title: string
  created_at: string
}

export interface AdminCommentItem {
  id: string
  content: string
  user_id: string
  user_name: string
  video_title: string
  created_at: string
}

export interface AdminDramaItem {
  id: string
  title: string
  category: string
  summary: string
  cover_url: string
  custom_cover_url?: string
  effective_cover?: string
  extra_images?: string[]
  status: string
  total_episodes: number
  view_count: number
  like_count: number
  storage_path: string
  created_at: string
}

export interface BiTrendsData {
  history: {
    dates: string[]
    views: number[]
    danmakus: number[]
    comments: number[]
    likes: number[]
  }
  prediction: {
    algorithm: string
    dates: string[]
    forecast_views: number[]
    upper_bound: number[]
    lower_bound: number[]
  }
  viral_rankings: Array<{
    video_id: string
    title: string
    category: string
    total_episodes: number
    view_count: number
    viral_score: number
    viral_tag: string
    badge_type: string
    predicted_next_week_views: number
  }>
  category_distribution: Array<{ name: string; value: number }>
}

export interface SystemCarouselItem {
  id: string
  title: string
  subtitle?: string
  tag: string
  cover_url: string
  video_id?: string
  drama_title?: string
  sort_order: number
  duration_seconds?: number
  is_active: boolean
  created_at: string
}

export const adminApi = {
  getOverview: () => {
    return api.get<any, ApiResponse<AdminOverviewData>>('/admin/overview')
  },

  getBiMetrics: () => {
    return api.get<any, ApiResponse<AdminBiMetricsData>>('/admin/bi-metrics')
  },

  getBiTrends: () => {
    return api.get<any, ApiResponse<BiTrendsData>>('/admin/bi-trends')
  },

  getUsers: (params?: { page?: number; per_page?: number; search?: string; role?: string }) => {
    return api.get<any, ApiResponse<{ total: number; page: number; per_page: number; items: AdminUserItem[] }>>('/admin/users', {
      params
    })
  },

  createUser: (data: { username: string; password: string; nickname?: string; role?: string; coins?: number; vip_days?: number }) => {
    return api.post<any, ApiResponse<any>>('/admin/users', data)
  },

  updateUser: (userId: string, data: { nickname?: string; password?: string; role?: string; status?: string; coins?: number; coins_adjustment?: number; vip_days?: number; vip_expire_at?: string }) => {
    return api.put<any, ApiResponse<any>>(`/admin/users/${userId}`, data)
  },

  deleteUser: (userId: string) => {
    return api.delete<any, ApiResponse<any>>(`/admin/users/${userId}`)
  },

  batchDeleteUsers: (userIds: string[]) => {
    return api.post<any, ApiResponse<{ deleted_count: number; deleted_users: string[] }>>('/admin/users/batch-delete', { user_ids: userIds })
  },

  adjustUserCoins: (userId: string, amount: number, reason?: string, vip_days?: number) => {
    return api.post<any, ApiResponse<any>>(`/admin/users/${userId}/adjust-coins`, { amount, reason, vip_days })
  },

  updateUserStatus: (user_id: string, status: 'ACTIVE' | 'BANNED') => {
    return api.post<any, ApiResponse<any>>(`/admin/users/${user_id}/status`, { status })
  },

  updateUserRole: (user_id: string, role: string) => {
    return api.post<any, ApiResponse<any>>(`/admin/users/${user_id}/role`, { role })
  },

  getApplications: () => {
    return api.get<any, ApiResponse<ApplicationsData>>('/admin/applications')
  },

  reviewCreator: (user_id: string, action: 'APPROVE' | 'REJECT', remarks?: string) => {
    return api.post<any, ApiResponse<any>>('/admin/creators/review', {
      user_id,
      action,
      remarks
    })
  },

  reviewReviewer: (user_id: string, action: 'APPROVE' | 'REJECT', remarks?: string) => {
    return api.post<any, ApiResponse<any>>('/admin/reviewers/review', {
      user_id,
      action,
      remarks
    })
  },

  getDanmakus: (params?: { page?: number; per_page?: number; search?: string; keyword?: string; time_min?: number; time_max?: number; video_id?: string; episode_id?: string }) => {
    return api.get<any, ApiResponse<{ total: number; page: number; per_page: number; items: AdminDanmakuItem[] }>>('/admin/contents/danmakus', { params })
  },

  deleteDanmaku: (id: string) => {
    return api.delete<any, ApiResponse<any>>(`/admin/contents/danmakus/${id}`)
  },

  batchDeleteDanmakus: (ids: string[]) => {
    return api.post<any, ApiResponse<{ deleted_count: number; success: boolean }>>('/admin/contents/danmakus/batch-delete', { ids })
  },

  getComments: (params?: { page?: number; per_page?: number; search?: string }) => {
    return api.get<any, ApiResponse<{ total: number; page: number; per_page: number; items: AdminCommentItem[] }>>('/admin/contents/comments', { params })
  },

  deleteComment: (id: string) => {
    return api.delete<any, ApiResponse<any>>(`/admin/contents/comments/${id}`)
  },

  getDramas: (params?: { page?: number; per_page?: number; search?: string }) => {
    return api.get<any, ApiResponse<{ total: number; page: number; per_page: number; items: AdminDramaItem[] }>>('/admin/dramas', { params })
  },

  updateDrama: (id: string, data: { title?: string; category?: string; summary?: string; cover_url?: string; status?: string }) => {
    return api.put<any, ApiResponse<any>>(`/admin/dramas/${id}`, data)
  },

  toggleDramaStatus: (id: string, status: string) => {
    return api.post<any, ApiResponse<any>>(`/admin/dramas/${id}/status`, { status })
  },

  updateDramaCover: (id: string, cover_url: string) => {
    return api.put<any, ApiResponse<any>>(`/admin/dramas/${id}/cover`, { cover_url })
  },

  updateDramaPosters: (id: string, extra_images: string[]) => {
    return api.put<any, ApiResponse<any>>(`/admin/dramas/${id}/posters`, { extra_images })
  },

  deleteDrama: (id: string) => {
    return api.delete<any, ApiResponse<any>>(`/admin/dramas/${id}`)
  },

  batchDeleteDramas: (dramaIds: string[]) => {
    return api.post<any, ApiResponse<{ deleted_count: number }>>('/admin/dramas/batch-delete', { drama_ids: dramaIds })
  },

  getDramaOptions: () => {
    return api.get<any, ApiResponse<Array<{ id: string; title: string; category: string; cover_url: string; extra_images: string }>>>('/admin/dramas/options')
  },

  uploadImage: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<any, ApiResponse<{ url: string; filename: string; size: number }>>('/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  syncPanAll: (mode: string = 'incremental') => {
    return api.post<any, ApiResponse<{ success: boolean; mode: string; dramas_found: number; total_synced_dramas: number; total_episodes: number; new_episodes_added: number; skipped_dramas: number; dramas: any[] }>>('/admin/pan/sync-all', {}, { params: { mode } })
  },

  getCarousels: () => {
    return api.get<any, ApiResponse<SystemCarouselItem[]>>('/admin/carousels')
  },

  createCarousel: (data: Partial<SystemCarouselItem>) => {
    return api.post<any, ApiResponse<any>>('/admin/carousels', data)
  },

  updateCarousel: (id: string, data: Partial<SystemCarouselItem>) => {
    return api.put<any, ApiResponse<any>>(`/admin/carousels/${id}`, data)
  },

  deleteCarousel: (id: string) => {
    return api.delete<any, ApiResponse<any>>(`/admin/carousels/${id}`)
  },

  getReviewQueue: (status: string = 'PENDING') => {
    return api.get<any, ApiResponse<ReviewQueueItem[]>>('/review/queue', { params: { status } })
  },

  makeReviewDecision: (review_id: string, decision: 'APPROVED' | 'REJECTED', notes?: string) => {
    return api.post<any, ApiResponse<any>>('/review/decision', { review_id, decision, notes })
  },

  getSensitiveWords: (params?: { query?: string; category?: string; level?: string; page?: number; per_page?: number }) => {
    return api.get<any, ApiResponse<{ total: number; page: number; per_page: number; items: SensitiveWordItem[] }>>('/review/sensitive-words', { params })
  },

  addSensitiveWord: (data: { word: string; level?: string; category?: string }) => {
    return api.post<any, ApiResponse<SensitiveWordItem>>('/review/sensitive-words', data)
  },

  deleteSensitiveWord: (word_id: string) => {
    return api.delete<any, ApiResponse<any>>(`/review/sensitive-words/${word_id}`)
  },

  testSensitiveWords: (text: string) => {
    return api.post<any, ApiResponse<SensitiveWordTestResult>>('/review/sensitive-words/test', { text })
  },

  getDualModelSettings: () => {
    return api.get<any, ApiResponse<any>>('/models/dual-settings')
  },

  updateDualModelSettings: (data: any) => {
    return api.put<any, ApiResponse<any>>('/models/dual-settings', data)
  },

  testChatConnection: (data: { provider: string; model?: string; api_key?: string; base_url?: string }) => {
    return api.post<any, ApiResponse<any>>('/models/test-connection', data)
  },

  testEmbeddingConnection: (data: { provider: string; model?: string; api_key?: string; base_url?: string }) => {
    return api.post<any, ApiResponse<any>>('/models/test-embedding', data)
  },

  getAnnouncements: (page: number = 1, per_page: number = 50) => {
    return api.get<any, ApiResponse<AdminAnnouncementListResponse>>('/admin/announcements', { params: { page, per_page } })
  },

  createAnnouncement: (data: { title: string; content: string; tag?: string }) => {
    return api.post<any, ApiResponse<AdminAnnouncementItem>>('/admin/announcements', data)
  },

  updateAnnouncement: (id: string, data: { title?: string; content?: string; tag?: string; is_published?: boolean }) => {
    return api.put<any, ApiResponse<AdminAnnouncementItem>>(`/admin/announcements/${id}`, data)
  },

  retractAnnouncement: (id: string) => {
    return api.post<any, ApiResponse<any>>(`/admin/announcements/${id}/retract`)
  },

  deleteAnnouncement: (id: string) => {
    return api.delete<any, ApiResponse<any>>(`/admin/announcements/${id}`)
  },

  batchDeleteAnnouncements: (announcement_ids: string[]) => {
    return api.post<any, ApiResponse<any>>('/admin/announcements/batch-delete', { announcement_ids })
  },

  getRedemptionCodes: (params?: { page?: number; per_page?: number; code_type?: string; status?: string; keyword?: string }) => {
    return api.get<any, ApiResponse<AdminRedemptionCodeListResponse>>('/admin/redemption-codes', { params })
  },

  generateRedemptionCodes: (data: { code_type: 'COIN' | 'VIP'; reward_amount: number; count: number; expires_days?: number | null; remark?: string }) => {
    return api.post<any, ApiResponse<{ count: number; codes: AdminRedemptionCodeItem[] }>>('/admin/redemption-codes/generate', data)
  },

  batchRedemptionCodesAction: (data: { code_ids: string[]; action: 'revoke' | 'delete' }) => {
    return api.post<any, ApiResponse<{ affected_count: number }>>('/admin/redemption-codes/batch-action', data)
  },

  deleteRedemptionCode: (codeId: string) => {
    return api.delete<any, ApiResponse<any>>(`/admin/redemption-codes/${codeId}`)
  }
}

export interface AdminRedemptionCodeItem {
  id: string
  code: string
  code_type: 'COIN' | 'VIP'
  reward_amount: number
  status: 'ACTIVE' | 'USED' | 'EXPIRED' | 'REVOKED'
  remark: string
  created_by?: string
  used_by?: string
  used_by_username?: string
  used_at?: string
  expires_at: string
  created_at: string
}

export interface AdminRedemptionCodeListResponse {
  total: number
  page: number
  per_page: number
  summary: {
    total_active: number
    total_used: number
    total_coins_redeemed: number
    total_vip_days_redeemed: number
  }
  items: AdminRedemptionCodeItem[]
}

export interface AdminAnnouncementItem {
  id: string
  title: string
  content: string
  tag: string
  is_published: boolean
  creator_id: string
  created_at: string
  updated_at: string
}

export interface AdminAnnouncementListResponse {
  total: number
  page: number
  per_page: number
  items: AdminAnnouncementItem[]
}

export interface ReviewQueueItem {
  id: string
  video_id: string
  video_title: string
  target_type: string
  target_id: string
  raw_content: string
  matched_words: string[]
  risk_level: string
  violation_reason: string
  status: string
  created_at: string
}

export interface SensitiveWordItem {
  id: string
  word: string
  level: string
  category: string
  created_at: string
}

export interface SensitiveWordTestResult {
  original_text: string
  has_violation: boolean
  sanitized_text: string
  matched_words: string[]
  max_risk_level: string
}


export { ragApi } from './rag'
