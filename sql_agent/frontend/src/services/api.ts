import axios from 'axios';

// API 기본 설정
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 요청 인터셉터 - 토큰 추가
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// 응답 인터셉터 - 오류 처리
api.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        // 인증 오류 처리
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// API 함수
export const authAPI = {
    login: (username: string, password: string) =>
        api.post('/api/auth/login', { username, password }),
    logout: () =>
        api.post('/api/auth/logout'),
    getCurrentUser: () =>
        api.get('/api/auth/me'),
};

export const databaseAPI = {
    listDatabases: () =>
        api.get('/api/db/list'),
    connectDatabase: (dbId: string) =>
        api.post('/api/db/connect', { db_id: dbId }),
    getDatabaseSchema: (dbId: string) =>
        api.get('/api/db/schema', { params: { db_id: dbId } }),
};

export const queryAPI = {
    processNaturalLanguage: (dbId: string, query: string, useRag: boolean = false) =>
        api.post('/api/query/natural', { db_id: dbId, query, use_rag: useRag }),
    executeQuery: (dbId: string, sql: string) =>
        api.post('/api/query/execute', { db_id: dbId, sql }),
    getQueryStatus: (queryId: string) =>
        api.get(`/api/query/status/${queryId}`),
    cancelQuery: (queryId: string) =>
        api.post(`/api/query/cancel/${queryId}`),
};

export const resultAPI = {
    getQueryResult: (resultId: string, page: number = 1, pageSize: number = 50) =>
        api.get(`/api/result/${resultId}`, { params: { page, page_size: pageSize } }),
    getResultSummary: (resultId: string) =>
        api.get(`/api/result/${resultId}/summary`),
    generateReport: (resultId: string, visualizationTypes: string[] = [], includeInsights: boolean = true) =>
        api.post('/api/result/report', { result_id: resultId, visualization_types: visualizationTypes, include_insights: includeInsights }),
    getReport: (reportId: string) =>
        api.get(`/api/result/report/${reportId}`),
};

export default api;