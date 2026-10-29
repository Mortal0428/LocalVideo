import { api } from './client'

export interface UserInfo {
  id: string
  username: string
  nickname?: string
  role: 'GUEST' | 'USER' | 'CREATOR' | 'REVIEWER' | 'ADMIN'
  is_creator?: boolean
  is_reviewer?: boolean
  status?: string
  creator_application_status?: string
  creator_bio?: string
  reviewer_application_status?: string
  reviewer_bio?: string
  avatar_url?: string
  is_vip?: boolean
  vip_expire_at?: string
  coins?: number
  created_at?: string
}

export type UserProfile = UserInfo

export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserInfo
}

export interface ApiResponse<T> {
  code: number
  data: T
  message?: string
}

export const authApi = {
  register: (data: { username: string; password: string; nickname?: string; role?: string }) => {
    return api.post<any, ApiResponse<TokenResponse>>('/auth/register', data)
  },

  login: (data: { username: string; password: string }) => {
    return api.post<any, ApiResponse<TokenResponse>>('/auth/login', data)
  },

  getMe: () => {
    return api.get<any, ApiResponse<UserInfo>>('/auth/me')
  },

  quickSwitch: (role: string) => {
    return api.post<any, ApiResponse<TokenResponse>>(`/auth/quick-switch/${role}`)
  },

  getWallpaperConfig: () => {
    return api.get<any, ApiResponse<{
      mode: string
      custom_url?: string
      dark_opacity?: number
      light_opacity?: number
      blur_px?: number
      title?: string
    }>>('/auth/wallpaper-config')
  }
}
