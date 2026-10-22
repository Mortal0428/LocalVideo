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
    }
};
//# sourceMappingURL=rag.js.map