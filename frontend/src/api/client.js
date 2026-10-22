import axios from 'axios';
export const api = axios.create({
    baseURL: '/api/v1',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
});
api.interceptors.request.use(config => {
    const token = localStorage.getItem('cinema_access_token') || localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, error => Promise.reject(error));
api.interceptors.response.use(response => {
    return response.data;
}, error => {
    console.error('API Error:', error);
    return Promise.reject(error);
});
//# sourceMappingURL=client.js.map