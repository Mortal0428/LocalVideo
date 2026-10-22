import { api } from './client';
export const authApi = {
    register: (data) => {
        return api.post('/auth/register', data);
    },
    login: (data) => {
        return api.post('/auth/login', data);
    },
    getMe: () => {
        return api.get('/auth/me');
    },
    quickSwitch: (role) => {
        return api.post(`/auth/quick-switch/${role}`);
    }
};
//# sourceMappingURL=auth.js.map