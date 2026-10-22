import { api } from './client';
export const ragApi = {
    async getOverviewStats() {
        return api.get('/rag-admin/stats');
    },
    async listCorpora(dramaId) {
        return api.get('/rag-admin/corpora', { params: { drama_id: dramaId } });
    },
    async initSampleAssets(force = false) {
        return api.post('/rag-admin/corpora/init-sample', null, { params: { force } });
    },
    async createCorpus(payload) {
        return api.post('/rag-admin/corpora/create', payload);
    },
    async deleteCorpus(corpusId) {
        return api.delete(`/rag-admin/corpora/${corpusId}`);
    },
    async listChunks(params) {
        return api.get('/rag-admin/chunks', { params });
    },
    async debugChunkStrategy(payload) {
        return api.post('/rag-admin/chunks/debug', payload);
    },
    async getGraphStatus() {
        return api.get('/rag-admin/graph/status');
    },
    async getGraphSubgraph(entityName, dramaId) {
        return api.get('/rag-admin/graph/subgraph', { params: { entity_name: entityName, drama_id: dramaId } });
    },
    async reconnectNeo4j() {
        return api.post('/rag-admin/graph/reconnect');
    },
    async getJudgeConfig() {
        return api.get('/rag-admin/eval/judge-config');
    },
    async saveJudgeConfig(configData) {
        return api.post('/rag-admin/eval/judge-config', configData);
    },
    async runBenchmark(payload) {
        return api.post('/rag-admin/eval/run', payload);
    },
    async listEvalRuns(limit = 20) {
        return api.get('/rag-admin/eval/history', { params: { limit } });
    },
    async getToolsConfig() {
        return api.get('/rag-admin/tools-config');
    },
    async saveToolsConfig(configData) {
        return api.post('/rag-admin/tools-config', configData);
    },
    async probeNeo4j(timeoutSec = 2.5) {
        return api.post('/rag-admin/probe/neo4j', null, { params: { timeout_sec: timeoutSec } });
    },
    async probeLlm(payload) {
        return api.post('/rag-admin/probe/llm', payload);
    },
    async importAllPresetAssets(force = true) {
        return api.post('/rag-admin/preset/import-all', null, { params: { force } });
    },
    async debugPipelineTrace(payload) {
        return api.post('/rag-admin/trace/debug', payload);
    },
    async previewChunking(payload) {
        return api.post('/rag-admin/chunk/preview', payload);
    }
};
//# sourceMappingURL=rag.js.map