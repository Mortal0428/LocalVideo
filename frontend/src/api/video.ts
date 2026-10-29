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

export interface MentionCandidateItem {
  id: string
  username: string
  nickname: string
  avatar_url: string
  role: string
  is_creator: boolean
  is_vip: boolean
  is_following: boolean
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
  /**
   * ==============================================================================
   * 【全链路前端 API】：getDirectStreamUrl (获取短剧分集直链播放地址)
   * 【调用来源】：PlayerView.vue 播放器初始化加载视频源或切换分集时
   * 【对应后端路由】：GET /api/v1/videos/stream/direct-url/{episode_id}
   * 【对应后端文件】：backend/app/api/v1/endpoints/stream.py -> get_direct_stream_url()
   * 【核心执行】：读取视频直链租约，支持云盘直链与本地反向代理双重兜底
   * ==============================================================================
   */
  async getDirectStreamUrl(episodeId: string): Promise<{ code: number; data: { episode_id: string; direct_url: string; expires_in: number; fallback_proxy_url: string } }> {
    return api.get(`/videos/stream/direct-url/${episodeId}`)
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：getHomeFeed (获取首页推荐短剧瀑布流与焦点轮播)
   * 【调用来源】：HomeView.vue 沉浸式大厅挂载时自动拉取
   * 【对应后端路由】：GET /api/v1/videos/home-feed
   * 【对应后端文件】：backend/app/api/v1/endpoints/stream.py -> get_home_feed()
   * 【核心执行】：聚合查询 system_carousels 焦点海报、题材分类与已发布短剧列表
   * ==============================================================================
   */
  async getHomeFeed(category?: string, keyword?: string): Promise<{ code: number; data: { categories: any[]; carousels: any[]; videos: any[] } }> {
    return api.get('/videos/home-feed', { params: { category, keyword } })
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：getCloudFiles (获取云盘已同步的媒体文件清单)
   * 【调用来源】：HomeView.vue 首页网盘资源展示或选集面板
   * 【对应后端路由】：GET /api/v1/videos/cloud-files
   * 【对应后端文件】：backend/app/api/v1/endpoints/stream.py -> list_cloud_files()
   * 【核心执行】：遍历云盘挂载目录返回已就绪的媒体文件元数据列表
   * ==============================================================================
   */
  async getCloudFiles(): Promise<{ code: number; data: VideoItem[] }> {
    return api.get('/videos/cloud-files')
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：getAlbum (获取短剧专辑详情与全量分集切片列表)
   * 【调用来源】：PlayerView.vue 播放器进入时拉取短剧元数据和集数列表
   * 【对应后端路由】：GET /api/v1/interactions/album/{video_id}
   * 【对应后端文件】：backend/app/api/v1/endpoints/interactions.py -> get_video_album()
   * 【核心执行】：关联查询 videos 档案与 video_episodes 分集列表，按集数升序排列
   * ==============================================================================
   */
  async getAlbum(videoId: string = 'latest'): Promise<{ code: number; data: VideoAlbum }> {
    return api.get(`/interactions/album/${videoId}`)
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：getHistory (查询历史观看断点秒数)
   * 【调用来源】：PlayerView.vue 视频播放器载入时查询观众上次看到第几秒，自动跳秒续播
   * 【对应后端路由】：GET /api/v1/interactions/episodes/{episode_id}/history
   * 【对应后端文件】：backend/app/api/v1/endpoints/interactions.py -> get_watch_history()
   * 【核心执行】：查询 user_watch_histories 表提取 progress_seconds 浮点秒数
   * ==============================================================================
   */
  async getHistory(episodeId: string): Promise<{ code: number; data: { progress_seconds: number; last_episode_id: string } }> {
    return api.get(`/interactions/episodes/${episodeId}/history`)
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：sendHeartbeat (播放器定时心跳上报播放进度)
   * 【调用来源】：PlayerView.vue 播放器内部每隔 5~10 秒定时自动发送心跳
   * 【对应后端路由】：POST /api/v1/interactions/episodes/{episode_id}/heartbeat
   * 【对应后端文件】：backend/app/api/v1/endpoints/interactions.py -> record_watch_heartbeat()
   * 【核心执行】：更新 user_watch_histories 播放秒数，并累加短剧 view_count 播放总次数
   * ==============================================================================
   */
  async sendHeartbeat(episodeId: string, progressSeconds: number): Promise<any> {
    return api.post(`/interactions/episodes/${episodeId}/heartbeat`, {
      progress_seconds: progressSeconds
    })
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：getLikeStatus (查询当前用户是否已给该视频点赞)
   * 【调用来源】：PlayerView.vue 播放器右下角点赞爱心图标初始化点亮状态
   * 【对应后端路由】：GET /api/v1/interactions/episodes/{episode_id}/like-status
   * 【对应后端文件】：backend/app/api/v1/endpoints/interactions.py -> get_like_status()
   * 【核心执行】：查询 user_likes 唯一去重表判断是否存在点赞记录并返回总获赞数
   * ==============================================================================
   */
  async getLikeStatus(episodeId: string): Promise<{ code: number; data: { is_liked: boolean; like_count: number; heat_score?: number } }> {
    return api.get(`/interactions/episodes/${episodeId}/like-status`)
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：toggleLike (切换视频点赞状态：点赞或取消点赞)
   * 【调用来源】：PlayerView.vue 点击点赞爱心图标触发
   * 【对应后端路由】：POST /api/v1/interactions/episodes/{episode_id}/like
   * 【对应后端文件】：backend/app/api/v1/endpoints/interactions.py -> toggle_like()
   * 【核心执行】：增删 user_likes 记录，自增/自减 videos.like_count，并重算全网热度分
   * ==============================================================================
   */
  async toggleLike(episodeId: string): Promise<{ code: number; data: { is_liked: boolean; like_count: number; heat_score?: number } }> {
    return api.post(`/interactions/episodes/${episodeId}/like`, {})
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：toggleCommentLike (对单条评论点赞或取消点赞)
   * 【调用来源】：PlayerView.vue 评论楼层右侧点赞小手图标点击触发
   * 【对应后端路由】：POST /api/v1/interactions/comments/{comment_id}/like
   * 【对应后端文件】：backend/app/api/v1/endpoints/interactions.py -> toggle_comment_like()
   * 【核心执行】：增删 comment_likes 记录，同步更新 user_comments.like_count 获赞数字
   * ==============================================================================
   */
  async toggleCommentLike(commentId: string): Promise<{ code: number; data: { is_liked: boolean; like_count: number } }> {
    return api.post(`/interactions/comments/${commentId}/like`, {})
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：getTipStatus (查询当前用户对该短剧的累计打赏枚数)
   * 【调用来源】：PlayerView.vue 展开投币打赏弹窗时查询打赏额度
   * 【对应后端路由】：GET /api/v1/interactions/episodes/{episode_id}/tip-status
   * 【对应后端文件】：backend/app/api/v1/endpoints/interactions.py -> get_tip_status()
   * 【核心执行】：查询 video_coin_tips 获取已打赏枚数 (上限 2 枚)
   * ==============================================================================
   */
  async getTipStatus(episodeId: string): Promise<{ code: number; message: string; data: { tipped_count: number; max_allowed: number; video_coin_count: number; heat_score: number } }> {
    return api.get(`/interactions/episodes/${episodeId}/tip-status`)
  },

  // Tip video with coins
  /**
   * ==============================================================================
   * 【全链路前端 API】：tipVideo (观众对短剧分集打赏投币)
   * 【调用来源】：PlayerView.vue 播放器控制栏右侧投币按钮
   * 【对应后端路由】：POST /api/v1/interactions/episodes/{episode_id}/tip
   * 【对应后端文件】：backend/app/api/v1/endpoints/interactions.py -> tip_video()
   * 【后续流向】：interactions.py 悲观锁扣减钱包 -> 记录账单流水 -> 短剧投币数+1与热度值重算
   * ==============================================================================
   */
  async tipVideo(episodeId: string, data: { coin_amount: number }): Promise<{ code: number; message: string; data: { tipped_count: number; max_allowed: number; video_coin_count: number; heat_score: number; wallet_balance: number } }> {
    return api.post(`/interactions/episodes/${episodeId}/tip`, data)
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：getComments (拉取短剧两级楼中楼评论树列表)
   * 【调用来源】：PlayerView.vue 底部评论区展开加载
   * 【对应后端路由】：GET /api/v1/interactions/episodes/{episode_id}/comments
   * 【对应后端文件】：backend/app/api/v1/endpoints/interactions.py -> get_comments()
   * 【核心执行】：查询 user_comments 主楼评论并联查嵌套 replies 二级楼中楼回复
   * ==============================================================================
   */
  async getComments(episodeId: string): Promise<{ code: number; data: { items: TwoTierCommentItem[]; total: number } }> {
    return api.get(`/interactions/episodes/${episodeId}/comments`)
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：postComment (发表一条新评论或回复某人的二级评论)
   * 【调用来源】：PlayerView.vue 评论输入框点击发送或在某个楼层点击回复
   * 【对应后端路由】：POST /api/v1/interactions/episodes/{episode_id}/comments
   * 【对应后端文件】：backend/app/api/v1/endpoints/interactions.py -> create_comment()
   * 【核心执行】：经过 DFA 敏感词机审，记录 parent_id / root_id / reply_to_user_id 入库
   * ==============================================================================
   */
  async postComment(
    episodeId: string,
    payload: string | { content: string; root_id?: string; parent_id?: string; reply_to_user_id?: string }
  ): Promise<{ code: number; data: TwoTierCommentItem | CommentReplyItem }> {
    const body = typeof payload === 'string' ? { content: payload } : payload
    return api.post(`/interactions/episodes/${episodeId}/comments`, body)
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：getMentionCandidates (输入 @ 字符时的候选提及用户联想)
   * 【调用来源】：PlayerView.vue 评论框输入 @ 字符时弹出快捷联想悬浮层
   * 【对应后端路由】：GET /api/v1/interactions/mention-candidates
   * 【对应后端文件】：backend/app/api/v1/endpoints/interactions.py -> get_mention_candidates()
   * 【核心执行】：模糊搜索 users 表匹配昵称、用户名以及同剧互动观众
   * ==============================================================================
   */
  async getMentionCandidates(params: {
    keyword?: string
    episodeId?: string
    limit?: number
  }): Promise<{ code: number; data: { items: MentionCandidateItem[]; total: number } }> {
    return api.get('/interactions/mention-candidates', {
      params: {
        keyword: params.keyword,
        episode_id: params.episodeId,
        limit: params.limit || 8
      }
    })
  },

  // Companion chat query (Legacy sync)
  /**
   * ==============================================================================
   * 【全链路前端 API】：chatWithAgent (播放器 AI 剧情伴聊问答请求)
   * 【调用来源】：PlayerView.vue 伴聊气泡窗口点击发送
   * 【对应后端路由】：POST /api/v1/agent/chat
   * 【对应后端文件】：backend/app/api/v1/endpoints/agent.py -> chat_with_agent()
   * 【后续流向】：agent.py -> ModularRAGPipeline.query() -> SelfRAG 防剧透 -> 大模型底座
   * ==============================================================================
   */
  async chatWithAgent(query: string, episodeId?: string): Promise<{ code: number; data: { response: string; relevant_timestamps?: Array<{ timestamp: number; title: string }> } }> {
    return api.post('/agent/chat', { question: query, episode_id: episodeId })
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：getHighlights (获取本集剧本高能反转打点清单)
   * 【调用来源】：PlayerView.vue 播放器进度条上方高能打点小图标与 AI 抽屉推荐
   * 【对应后端路由】：GET /api/v1/agent/episodes/{episode_id}/highlights
   * 【对应后端文件】：backend/app/api/v1/endpoints/agent.py -> get_episode_highlights()
   * 【核心执行】：通过 Timeline Skill 提取 video_subtitle_timelines 中 is_climax=True 的高能节点
   * ==============================================================================
   */
  async getHighlights(episodeId: string): Promise<{ code: number; data: HighlightItem[] }> {
    return api.get(`/agent/episodes/${episodeId}/highlights`)
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：getQuickPrompts (获取 AI 伴聊开场快捷追问气泡卡片)
   * 【调用来源】：PlayerView.vue AI 剧情伴侣聊天视窗初次展开时
   * 【对应后端路由】：GET /api/v1/agent/quick-prompts/{episode_id}
   * 【对应后端文件】：backend/app/api/v1/endpoints/agent.py -> get_quick_prompts()
   * 【核心执行】：根据本集剧情自动生成 3 条趣味追问（如“男主隐藏身份是什么？”）
   * ==============================================================================
   */
  async getQuickPrompts(episodeId: string): Promise<{ code: number; data: string[] }> {
    return api.get(`/agent/quick-prompts/${episodeId}`)
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：streamAgentChat (SSE 毫秒级打字机流式伴聊会话)
   * 【调用来源】：PlayerView.vue AI 剧情伴聊抽屉发送追问
   * 【对应后端路由】：POST /api/v1/agent/chat/stream
   * 【对应后端文件】：backend/app/api/v1/endpoints/agent.py -> chat_with_video_agent_stream()
   * 【核心执行】：建立 SSE 长连接，流式推送 thought 思考过程、token 文本与 action_card 跳秒卡片
   * ==============================================================================
   */
  async streamAgentChat(params: {
    episodeId: string
    question: string
    currentVideoTime?: number
    dramaId?: string
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
          drama_id: params.dramaId || undefined,
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

