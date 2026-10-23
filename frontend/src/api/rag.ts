import { api } from './client'

export interface RAGOverviewStats {
  total_corpora: number
  total_chunks: number
  total_evals: number
  latest_eval_score: number
  latest_eval?: {
    id: string
    name: string
    judge_model: string
    faithfulness: number
    answer_relevance: number
    context_precision: number
    context_recall: number
    f1_score: number
    created_at: string
  }
  graph_status: {
    is_connected: boolean
    backend: 'neo4j' | 'embedded_fallback'
    uri: string
    user: string
    total_nodes: number
    total_edges: number
    message: string
  }
  judge_config: {
    mode: 'local' | 'cloud'
    local: {
      provider: string
      model_name: string
      base_url: string
    }
    cloud: {
      provider: string
      model_name: string
      base_url: string
      api_key?: string
      masked_api_key?: string
    }
    temperature: number
    timeout_seconds: number
  }
  tools_config?: Record<string, any>
}

export interface RAGCorpusItem {
  id: string
  drama_id?: string
  title: string
  doc_type: string
  chunk_count: number
  content_preview: string
  created_at: string
  updated_at: string
}

export interface RAGChunkItem {
  id: string
  corpus_id: string
  drama_id?: string
  episode_num: number
  start_sec: number
  end_sec: number
  time_tag: string
  chunk_strategy: string
  content: string
  parent_content?: string
  token_count: number
}

export interface RAGEvalRunItem {
  id: string
  name: string
  judge_model: string
  faithfulness: number
  answer_relevance: number
  context_precision: number
  context_recall: number
  f1_score: number
  sample_count: number
  latency_ms: number
  created_at: string
}

export interface PipelineTraceStep {
  name: string
  stage: string
  enabled: boolean
  latency_ms: number
  count: number
  details: string
}

export interface PipelineTraceResult {
  trace_id: string
  query: string
  episode_num: number
  current_sec: number
  total_latency_ms: number
  trace_steps: PipelineTraceStep[]
  retrieved_documents: Array<{
    id: string
    text: string
    score: number
    chunk_strategy: string
    episode_num: number
    start_sec: number
    end_sec: number
    time_tag: string
    source: string
  }>
  graph_entities: any[]
  crag_status: string
  crag_confidence: number
  crag_reason: string
  best_anchor?: any
}

export interface ChunkPreviewResult {
  strategy: string
  total_chunks: number
  stats: {
    total_chunks: number
    total_chars: number
    avg_chunk_size: number
    max_chunk_size: number
    min_chunk_size: number
  }
  chunks: Array<{
    id: string
    chunk_index: number
    content: string
    char_count: number
    start_sec: number
    end_sec: number
    time_tag: string
    strategy: string
    parent_content?: string
  }>
}

export const ragApi = {
  async getOverviewStats(): Promise<{ code: number; data: RAGOverviewStats }> {
    return api.get('/rag-admin/stats')
  },

  async listDramas(): Promise<{ code: number; data: any[] }> {
    return api.get('/rag-admin/dramas')
  },

  async listCategories(dramaId?: string): Promise<{ code: number; data: any[] }> {
    return api.get('/rag-admin/categories', { params: { drama_id: dramaId } })
  },

  async createCategory(payload: { name: string; drama_id: string; parent_id?: string }): Promise<{ code: number; data: any; message: string }> {
    return api.post('/rag-admin/categories', payload)
  },

  async deleteCategory(catId: string): Promise<{ code: number; message: string }> {
    return api.delete(`/rag-admin/categories/${catId}`)
  },

  async uploadCorpusFile(formData: FormData): Promise<{ code: number; data: any; message: string }> {
    return api.post('/rag-admin/corpora/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  async listCorpora(params?: { drama_id?: string; category_id?: string; page?: number; page_size?: number }): Promise<{ code: number; data: any }> {
    return api.get('/rag-admin/corpora', { params })
  },

  async initSampleAssets(force: boolean = false): Promise<{ code: number; data: any }> {
    return api.post('/rag-admin/corpora/init-sample', null, { params: { force } })
  },

  async createCorpus(payload: {
    title: string
    doc_type: string
    content: string
    drama_id?: string
    category_id?: string
    strategy?: string
  }): Promise<{ code: number; data: any }> {
    return api.post('/rag-admin/corpora/create', payload)
  },

  async getCorpus(corpusId: string): Promise<{ code: number; data: any }> {
    return api.get(`/rag-admin/corpora/${corpusId}`)
  },

  async embedCorpus(corpusId: string, payload?: {
    chunk_size?: number
    chunk_overlap?: number
    strategy?: string
    re_extract_graph?: boolean
  }): Promise<{ code: number; message: string; data: any }> {
    return api.post(`/rag-admin/corpora/${corpusId}/embed`, payload || {})
  },

  async deleteCorpus(corpusId: string): Promise<{ code: number; message: string }> {
    return api.delete(`/rag-admin/corpora/${corpusId}`)
  },

  async listChunks(params?: any): Promise<{ code: number; data: any }> {
    return api.get('/rag-admin/chunks', { params })
  },

  async debugChunkStrategy(payload: {
    text: string
    strategy: string
    chunk_size?: number
    chunk_overlap?: number
    episode_num?: number
  }): Promise<{ code: number; data: any }> {
    return api.post('/rag-admin/chunks/debug', payload)
  },

  async getGraphStatus(): Promise<{ code: number; data: any }> {
    return api.get('/rag-admin/graph/status')
  },

  async getGraphSubgraph(entityName?: string, dramaId?: string, limit: number = 200): Promise<{ code: number; data: any }> {
    return api.get('/rag-admin/graph/subgraph', { params: { entity_name: entityName, drama_id: dramaId, limit } })
  },

  async reconnectNeo4j(): Promise<{ code: number; data: any }> {
    return api.post('/rag-admin/graph/reconnect')
  },

  async getJudgeConfig(): Promise<{ code: number; data: any }> {
    return api.get('/rag-admin/eval/judge-config')
  },

  async saveJudgeConfig(configData: any): Promise<{ code: number; data: any; message: string }> {
    return api.post('/rag-admin/eval/judge-config', configData)
  },

  async runBenchmark(payload: { name?: string; max_samples?: number; drama_id?: string; drama_title?: string }): Promise<{ code: number; data: any }> {
    return api.post('/rag-admin/eval/run', payload)
  },

  async getEvalTaskStatus(runId: string): Promise<{ code: number; data: any }> {
    return api.get(`/rag-admin/eval/task/${runId}`)
  },

  async previewChunkLab(payload: {
    strategy: string
    chunk_size: number
    overlap: number
    window_step: number
    parent_child_ratio: number
    text: string
  }): Promise<{ code: number; data: any }> {
    return api.post('/rag-admin/chunklab/preview', payload)
  },

  async saveGlobalChunkDefault(payload: {
    strategy: string
    chunk_size: number
    overlap: number
    window_step: number
    parent_child_ratio: number
  }): Promise<{ code: number; data: any; message: string }> {
    return api.post('/rag-admin/chunklab/save-global-default', payload)
  },

  async getGlobalChunkDefault(): Promise<{ code: number; data: any }> {
    return api.get('/rag-admin/chunklab/global-default')
  },

  async listEvalRuns(params?: any): Promise<{ code: number; data: any }> {
    const p = typeof params === 'number' ? { limit: params } : (params || {})
    return api.get('/rag-admin/eval/history', { params: p })
  },

  async getActiveEvalRun(): Promise<{ code: number; data: any }> {
    return api.get('/rag-admin/eval/active')
  },

  async getToolsConfig(): Promise<{ code: number; data: any }> {
    return api.get('/rag-admin/tools-config')
  },

  async saveToolsConfig(configData: any): Promise<{ code: number; data: any; message: string }> {
    return api.post('/rag-admin/tools-config', configData)
  },

  async probeNeo4j(timeoutSec: number = 2.5): Promise<{ code: number; data: any }> {
    return api.post('/rag-admin/probe/neo4j', null, { params: { timeout_sec: timeoutSec } })
  },

  async probeLlm(payload: any): Promise<{ code: number; data: any }> {
    return api.post('/rag-admin/probe/llm', payload)
  },

  async importAllPresetAssets(force: boolean = true): Promise<{ code: number; data: any; message: string }> {
    return api.post('/rag-admin/preset/import-all', null, { params: { force } })
  },

  async debugPipelineTrace(payload: {
    query: string
    drama_id?: string
    episode_num?: number
    current_sec?: number
  }): Promise<{ code: number; data: PipelineTraceResult }> {
    return api.post('/rag-admin/trace/debug', payload)
  },

  async previewChunking(payload: {
    content: string
    strategy: string
    chunk_size?: number
    chunk_overlap?: number
    drama_id?: string
    episode_num?: number
  }): Promise<{ code: number; data: ChunkPreviewResult }> {
    return api.post('/rag-admin/chunk/preview', payload)
  }
}
