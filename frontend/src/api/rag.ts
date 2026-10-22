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

export const ragApi = {
  async getOverviewStats(): Promise<{ code: number; data: RAGOverviewStats }> {
    return api.get('/rag-admin/stats')
  },

  async listCorpora(dramaId?: string): Promise<{ code: number; data: RAGCorpusItem[] }> {
    return api.get('/rag-admin/corpora', { params: { drama_id: dramaId } })
  },

  async initSampleAssets(force: boolean = false): Promise<{ code: number; data: any }> {
    return api.post('/rag-admin/corpora/init-sample', null, { params: { force } })
  },

  async createCorpus(payload: {
    title: string
    doc_type: string
    content: string
    drama_id?: string
    strategy?: string
  }): Promise<{ code: number; data: any }> {
    return api.post('/rag-admin/corpora/create', payload)
  },

  async deleteCorpus(corpusId: string): Promise<{ code: number; message: string }> {
    return api.delete(`/rag-admin/corpora/${corpusId}`)
  },

  async listChunks(params?: { corpus_id?: string; drama_id?: string; limit?: number }): Promise<{ code: number; data: RAGChunkItem[] }> {
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

  async getGraphSubgraph(entityName?: string, dramaId?: string): Promise<{ code: number; data: any }> {
    return api.get('/rag-admin/graph/subgraph', { params: { entity_name: entityName, drama_id: dramaId } })
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

  async runBenchmark(payload: { name?: string; max_samples?: number }): Promise<{ code: number; data: RAGEvalRunItem }> {
    return api.post('/rag-admin/eval/run', payload)
  },

  async listEvalRuns(limit: number = 20): Promise<{ code: number; data: RAGEvalRunItem[] }> {
    return api.get('/rag-admin/eval/history', { params: { limit } })
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
  }
}
