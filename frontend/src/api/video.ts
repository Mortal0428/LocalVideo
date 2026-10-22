import { api } from './client'

export interface Episode {
  id: string
  episode_num: number
  title: string
  duration_seconds: number
  transcode_status: string
  stream_url: string
  created_at?: string
}

export type VideoEpisode = Episode

export interface VideoAlbum {
  id: string
  title: string
  summary?: string
  description?: string
  cover_url: string
  category: string
  like_count?: number
  view_count?: number
  total_episodes?: number
  episodes: Episode[]
}

export interface VideoItem {
  id: string
  title: string
  description?: string
  category?: string
  cover_url?: string
  custom_cover_url?: string
  extra_images?: string[]
  episodes_count?: number
  duration_str?: string
  play_count_str?: string
  danmaku_count_str?: string
  creator_name?: string
  creator_avatar?: string
}

export interface CommentItem {
  id: string
  user_id?: string
  username: string
  user_name?: string
  avatar_url?: string
  user_avatar?: string
  content: string
  like_count?: number
  created_at?: string
  created_at_str?: string
}

export interface CommentReplyItem {
  id: string
  root_id: string
  parent_id?: string
  user_id: string
  username: string
  nickname?: string
  avatar_url?: string
  reply_to_user_id?: string
  reply_to_username?: string
  reply_to_nickname?: string
  content: string
  like_count: number
  is_liked?: boolean
  created_at: string
}

export interface TwoTierCommentItem {
  id: string
  user_id: string
  username: string
  nickname?: string
  avatar_url?: string
  content: string
  like_count: number
  is_liked?: boolean
  created_at: string
  replies: CommentReplyItem[]
  reply_count: number
}

export interface DanmakuItem {
  id: string
  episode_id?: string
  user_id?: string
  content: string
  color?: string
  time_offset?: number
}

export interface HighlightItem {
  time: number
  timeTag: string
  title: string
  desc: string
  tag: string
}

export interface ActionCardData {
  action: string
  timestamp: number
  time_tag: string
  title: string
  desc?: string
}

export const videoApi = {
  // Fetch direct cloud stream URL with lease and proxy fallback
  async getDirectStreamUrl(episodeId: string): Promise<{ code: number; data: { episode_id: string; direct_url: string; expires_in: number; fallback_proxy_url: string } }> {
    return api.get(`/videos/stream/direct-url/${episodeId}`)
  },

  // Fetch home feed (carousels, categories, videos)
  async getHomeFeed(category?: string, keyword?: string): Promise<{ code: number; data: { categories: any[]; carousels: any[]; videos: any[] } }> {
    return api.get('/videos/home-feed', { params: { category, keyword } })
  },

  // Fetch cloud files list for portal
  async getCloudFiles(): Promise<{ code: number; data: VideoItem[] }> {
    return api.get('/videos/cloud-files')
  },

  // Fetch album details and episode list
  async getAlbum(videoId: string = 'latest'): Promise<{ code: number; data: VideoAlbum }> {
    return api.get(`/interactions/album/${videoId}`)
  },

  // Get last watch progress for auto-resume
  async getHistory(episodeId: string): Promise<{ code: number; data: { progress_seconds: number; last_episode_id: string } }> {
    return api.get(`/interactions/episodes/${episodeId}/history`)
  },

  // Report watch progress heartbeat
  async sendHeartbeat(episodeId: string, progressSeconds: number): Promise<any> {
    return api.post(`/interactions/episodes/${episodeId}/heartbeat`, {
      progress_seconds: progressSeconds
    })
  },

  // Query like status
  async getLikeStatus(episodeId: string): Promise<{ code: number; data: { is_liked: boolean; like_count: number; heat_score?: number } }> {
    return api.get(`/interactions/episodes/${episodeId}/like-status`)
  },

  // Toggle video like
  async toggleLike(episodeId: string): Promise<{ code: number; data: { is_liked: boolean; like_count: number; heat_score?: number } }> {
    return api.post(`/interactions/episodes/${episodeId}/like`, {})
  },

  // Toggle comment like
  async toggleCommentLike(commentId: string): Promise<{ code: number; data: { is_liked: boolean; like_count: number } }> {
    return api.post(`/interactions/comments/${commentId}/like`, {})
  },

  // Query coin tip status
  async getTipStatus(episodeId: string): Promise<{ code: number; message: string; data: { tipped_count: number; max_allowed: number; video_coin_count: number; heat_score: number } }> {
    return api.get(`/interactions/episodes/${episodeId}/tip-status`)
  },

  // Tip video with coins
  async tipVideo(episodeId: string, data: { coin_amount: number }): Promise<{ code: number; message: string; data: { tipped_count: number; max_allowed: number; video_coin_count: number; heat_score: number; wallet_balance: number } }> {
    return api.post(`/interactions/episodes/${episodeId}/tip`, data)
  },

  // Fetch comments (two-tier nested tree)
  async getComments(episodeId: string): Promise<{ code: number; data: { items: TwoTierCommentItem[]; total: number } }> {
    return api.get(`/interactions/episodes/${episodeId}/comments`)
  },

  // Post new comment or reply
  async postComment(
    episodeId: string,
    payload: string | { content: string; root_id?: string; parent_id?: string; reply_to_user_id?: string }
  ): Promise<{ code: number; data: TwoTierCommentItem | CommentReplyItem }> {
    const body = typeof payload === 'string' ? { content: payload } : payload
    return api.post(`/interactions/episodes/${episodeId}/comments`, body)
  },

  // Companion chat query (Legacy sync)
  async chatWithAgent(query: string, episodeId?: string): Promise<{ code: number; data: { response: string; relevant_timestamps?: Array<{ timestamp: number; title: string }> } }> {
    return api.post('/agent/chat', { question: query, episode_id: episodeId })
  },

  // Fetch official timeline highlights extracted by Timeline Skill
  async getHighlights(episodeId: string): Promise<{ code: number; data: HighlightItem[] }> {
    return api.get(`/agent/episodes/${episodeId}/highlights`)
  },

  // Fetch starter quick prompts
  async getQuickPrompts(episodeId: string): Promise<{ code: number; data: string[] }> {
    return api.get(`/agent/quick-prompts/${episodeId}`)
  },

  // Streaming SSE Chat with Timeline Subtitle RAG & Multimodal Skills
  async streamAgentChat(params: {
    episodeId: string
    question: string
    currentVideoTime?: number
    modelName?: string
    onThought?: (thought: string) => void
    onToken?: (token: string) => void
    onActionCard?: (card: ActionCardData) => void
    onDone?: (data: { target_time: number; time_tag: string; model_used?: string }) => void
    onError?: (err: any) => void
  }): Promise<void> {
    try {
      const token = localStorage.getItem('cinema_access_token') || localStorage.getItem('token')
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('/api/v1/agent/chat/stream', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          episode_id: params.episodeId,
          question: params.question,
          current_video_time: params.currentVideoTime || 0,
          model_name: params.modelName || undefined
        })
      })

      if (!response.ok || !response.body) {
        throw new Error(`HTTP error ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith('data:')) {
            const jsonStr = trimmed.slice(5).trim()
            if (!jsonStr) continue
            try {
              const data = JSON.parse(jsonStr)
              if (data.type === 'token' && params.onToken) {
                params.onToken(data.content)
              } else if (data.type === 'thought' && params.onThought) {
                params.onThought(data.content)
              } else if (data.type === 'action_card' && params.onActionCard) {
                params.onActionCard(data)
              } else if (data.type === 'done' && params.onDone) {
                params.onDone(data)
              }
            } catch (e) {
              console.error('Failed to parse SSE line:', jsonStr, e)
            }
          }
        }
      }
    } catch (err) {
      if (params.onError) {
        params.onError(err)
      } else {
        throw err
      }
    }
  }
}

