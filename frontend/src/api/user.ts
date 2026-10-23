import { api } from './client'
import type { UserInfo } from './auth'

export interface UserStats {
  history_count: number
  likes_count: number
  creator_videos_count: number
  following_count?: number
  followers_count?: number
}

export interface UserFullProfile extends UserInfo {
  is_reviewer?: boolean
  reviewer_application_status?: string
  reviewer_bio?: string
  is_vip?: boolean
  vip_expire_at?: string
  coins?: number
  stats: UserStats
}

export interface WatchHistoryItem {
  history_id: string
  episode_id?: string
  last_episode_id?: string
  video_id: string
  drama_title: string
  cover_url: string
  episode_num: number
  episode_title: string
  progress_seconds: number
  duration_seconds: number
  progress_pct: number
  updated_at: string
}

export interface UserLikeItem {
  like_id: string
  episode_id?: string
  video_id: string
  drama_title: string
  cover_url: string
  episode_num?: number
  episode_title?: string
  created_at: string
}

export interface UserNotificationItem {
  id: string
  category: 'ANNOUNCEMENT' | 'REPLY' | 'LIKE' | 'MENTION'
  title: string
  content: string
  sender_id?: string
  sender_name?: string
  sender_avatar?: string
  video_id?: string
  episode_id?: string
  comment_id?: string
  announcement_id?: string
  is_read: boolean
  created_at: string
}

export interface UnreadCountData {
  total: number
  announcements: number
  replies: number
  likes: number
  mentions?: number
}

export const userApi = {
  getProfile: () => {
    return api.get<any, { code: number; data: UserFullProfile }>('/user/profile')
  },

  updateProfile: (data: { nickname?: string; avatar_url?: string; bio?: string }) => {
    return api.put<any, { code: number; data: UserInfo }>('/user/profile', data)
  },

  applyCreator: (data: { creator_name?: string; bio?: string }) => {
    return api.post<any, { code: number; data: UserInfo; message: string }>('/user/apply-creator', data)
  },

  applyReviewer: (data: { reviewer_name?: string; bio?: string }) => {
    return api.post<any, { code: number; data: UserInfo; message: string }>('/user/apply-reviewer', data)
  },

  getHistory: () => {
    return api.get<any, { code: number; data: WatchHistoryItem[] }>('/user/history')
  },

  getLikes: () => {
    return api.get<any, { code: number; data: UserLikeItem[] }>('/user/likes')
  },

  getCoinWallet: () => {
    return api.get<any, { code: number; data: UserCoinWalletData }>('/user/coins/wallet')
  },

  dailySignIn: () => {
    return api.post<any, { code: number; message: string; data: { balance: number; reward: number; has_signed_today: boolean } }>('/user/coins/sign-in')
  },

  watchAdReward: () => {
    return api.post<any, { code: number; message: string; data: { balance: number; reward: number } }>('/user/coins/watch-ad')
  },

  exchangeVip: (data: { days: number; cost?: number }) => {
    return api.post<any, { code: number; message: string; data: { balance: number; vip_expire_at: string; days_added: number } }>('/user/coins/exchange-vip', data)
  },

  redeemCode: (code: string) => {
    return api.post<any, { code: number; message: string; data: { code: string; code_type: 'COIN' | 'VIP'; reward_amount: number; balance: number; total_earned: number; vip_expire_at: string } }>('/user/coins/redeem', { code })
  },

  getComments: (page = 1, size = 30) => {
    return api.get<any, { code: number; data: { total: number; page: number; size: number; items: any[] } }>(`/user/comments?page=${page}&size=${size}`)
  },

  deleteComment: (commentId: string) => {
    return api.delete<any, { code: number; message: string }>(`/user/comments/${commentId}`)
  },

  toggleFollow: (targetUserId: string) => {
    return api.post<any, { code: number; message: string; data: { is_following: boolean; followers_count: number } }>(`/user/follow/${targetUserId}`)
  },

  getFollowStatus: (targetUserId: string) => {
    return api.get<any, { code: number; data: { is_following: boolean; followers_count: number; following_count: number } }>(`/user/follow-status/${targetUserId}`)
  },

  getFollowings: () => {
    return api.get<any, { code: number; data: { total: number; items: any[] } }>('/user/followings')
  },

  getFollowers: () => {
    return api.get<any, { code: number; data: { total: number; items: any[] } }>('/user/followers')
  },

  getPublicCard: (targetUserId: string | number) => {
    return api.get<any, { code: number; data: any }>(`/user/public-card/${targetUserId}`)
  },

  uploadImage: (formData: FormData) => {
    return api.post<any, { code: number; url: string; message: string }>('/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

export interface UserCoinWalletData {
  balance: number
  total_earned: number
  total_spent: number
  has_signed_today: boolean
  ad_watch_count_today?: number
}

export const notificationApi = {
  async getNotifications(category?: string, page = 1, perPage = 20): Promise<{ code: number; data: { total: number; page: number; per_page: number; items: UserNotificationItem[] } }> {
    return api.get('/notifications', { params: { category, page, per_page: perPage } })
  },

  async getUnreadCount(): Promise<{ code: number; data: UnreadCountData }> {
    return api.get('/notifications/unread-count')
  },

  async markRead(notificationId: string): Promise<{ code: number; data: { id: string; is_read: boolean } }> {
    return api.post(`/notifications/${notificationId}/read`)
  },

  async markAllRead(category?: string): Promise<{ code: number; data: { updated_count: number } }> {
    return api.post('/notifications/read-all', {}, { params: { category } })
  }
}
