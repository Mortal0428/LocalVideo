import { api } from './client';
export const videoApi = {
    // Fetch home feed (carousels, categories, videos)
    async getHomeFeed(category, keyword) {
        return api.get('/videos/home-feed', { params: { category, keyword } });
    },
    // Fetch cloud files list for portal
    async getCloudFiles() {
        return api.get('/videos/cloud-files');
    },
    // Fetch album details and episode list
    async getAlbum(videoId = 'latest') {
        return api.get(`/interactions/album/${videoId}`);
    },
    // Get last watch progress for auto-resume
    async getHistory(episodeId) {
        return api.get(`/interactions/episodes/${episodeId}/history`);
    },
    // Report watch progress heartbeat
    async sendHeartbeat(episodeId, progressSeconds) {
        return api.post(`/interactions/episodes/${episodeId}/heartbeat`, {
            progress_seconds: progressSeconds
        });
    },
    // Query like status
    async getLikeStatus(episodeId) {
        return api.get(`/interactions/episodes/${episodeId}/like-status`);
    },
    // Toggle video like
    async toggleLike(episodeId) {
        return api.post(`/interactions/episodes/${episodeId}/like`, {});
    },
    // Toggle comment like
    async toggleCommentLike(commentId) {
        return api.post(`/interactions/comments/${commentId}/like`, {});
    },
    // Query coin tip status
    async getTipStatus(episodeId) {
        return api.get(`/interactions/episodes/${episodeId}/tip-status`);
    },
    // Tip video with coins
    async tipVideo(episodeId, data) {
        return api.post(`/interactions/episodes/${episodeId}/tip`, data);
    },
    // Fetch comments (two-tier nested tree)
    async getComments(episodeId) {
        return api.get(`/interactions/episodes/${episodeId}/comments`);
    },
    // Post new comment or reply
    async postComment(episodeId, payload) {
        const body = typeof payload === 'string' ? { content: payload } : payload;
        return api.post(`/interactions/episodes/${episodeId}/comments`, body);
    },
    // Companion chat query (Legacy sync)
    async chatWithAgent(query, episodeId) {
        return api.post('/agent/chat', { question: query, episode_id: episodeId });
    },
    // Fetch official timeline highlights extracted by Timeline Skill
    async getHighlights(episodeId) {
        return api.get(`/agent/episodes/${episodeId}/highlights`);
    },
    // Fetch starter quick prompts
    async getQuickPrompts(episodeId) {
        return api.get(`/agent/quick-prompts/${episodeId}`);
    },
    // Streaming SSE Chat with Timeline Subtitle RAG & Multimodal Skills
    async streamAgentChat(params) {
        try {
            const token = localStorage.getItem('cinema_access_token') || localStorage.getItem('token');
            const headers = {
                'Content-Type': 'application/json'
            };
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
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
            });
            if (!response.ok || !response.body) {
                throw new Error(`HTTP error ${response.status}`);
            }
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';
            while (true) {
                const { done, value } = await reader.read();
                if (done)
                    break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || '';
                for (const line of lines) {
                    const trimmed = line.trim();
                    if (trimmed.startsWith('data:')) {
                        const jsonStr = trimmed.slice(5).trim();
                        if (!jsonStr)
                            continue;
                        try {
                            const data = JSON.parse(jsonStr);
                            if (data.type === 'token' && params.onToken) {
                                params.onToken(data.content);
                            }
                            else if (data.type === 'thought' && params.onThought) {
                                params.onThought(data.content);
                            }
                            else if (data.type === 'action_card' && params.onActionCard) {
                                params.onActionCard(data);
                            }
                            else if (data.type === 'done' && params.onDone) {
                                params.onDone(data);
                            }
                        }
                        catch (e) {
                            console.error('Failed to parse SSE line:', jsonStr, e);
                        }
                    }
                }
            }
        }
        catch (err) {
            if (params.onError) {
                params.onError(err);
            }
            else {
                throw err;
            }
        }
    }
};
//# sourceMappingURL=video.js.map