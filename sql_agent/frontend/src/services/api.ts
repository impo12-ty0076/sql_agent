import axios from 'axios';
import { store } from '../store';

// API 기본 설정
// 1) 환경변수에 `/api` 가 포함되거나 끝에 슬래시가 남아 있어도 중복되지 않도록 정리한다.
const RAW_BASE_URL = (process.env.REACT_APP_API_URL || 'http://localhost:8000').trim();
// 마지막에 `/` 또는 `/api` 가 붙어 있다면 제거한다
const API_BASE_URL = RAW_BASE_URL
  // 끝에 `/api` 가 있을 경우 제거
  .replace(/\/api\/?$/i, '')
  // 남은 끝 슬래시 제거
  .replace(/\/+$/, '');

// 모든 엔드포인트에서 사용할 공통 접두사
const API_PREFIX = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 - 토큰 추가
api.interceptors.request.use(
  config => {
    // Redux store에서 토큰을 가져옴
    const state = store.getState();
    const token = state.auth.token;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 - 오류 처리
api.interceptors.response.use(
  response => {
    return response;
  },
  error => {
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
  // Login must use form-urlencoded body because the backend expects
  // OAuth2PasswordRequestForm (application/x-www-form-urlencoded)
  login: (username: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    return api.post(`${API_PREFIX}/auth/login`, params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  logout: () => api.post(`${API_PREFIX}/auth/logout`),
  getCurrentUser: () => api.get(`${API_PREFIX}/auth/me`),
};

export const databaseAPI = {
  listDatabases: () => api.get('/api/db/list'),
  connectDatabase: (dbId: string) => api.post('/api/db/connect', { db_id: dbId }),
  getDatabaseSchema: (dbId: string) => api.get('/api/db/schema', { params: { db_id: dbId } }),
};

export const queryAPI = {
  processNaturalLanguage: (dbId: string, query: string, useRag = false) =>
    api.post(`${API_PREFIX}/query/natural`, { db_id: dbId, query, use_rag: useRag }),
  executeQuery: (dbId: string, sql: string) =>
    api.post(`${API_PREFIX}/query/execute`, { db_id: dbId, sql }),
  getQueryStatus: (queryId: string) => api.get(`${API_PREFIX}/query/status/${queryId}`),
  cancelQuery: (queryId: string) => api.post(`${API_PREFIX}/query/cancel/${queryId}`),
};

export const resultAPI = {
  getQueryResult: (resultId: string, page = 1, pageSize = 50) =>
    api.get(`${API_PREFIX}/result/${resultId}`, { params: { page, page_size: pageSize } }),
  getResultSummary: (resultId: string) => api.get(`${API_PREFIX}/result/${resultId}/summary`),
  generateReport: (resultId: string, visualizationTypes: string[] = [], includeInsights = true) =>
    api.post(`${API_PREFIX}/result/report`, {
      result_id: resultId,
      visualization_types: visualizationTypes,
      include_insights: includeInsights,
    }),
  getReport: (reportId: string) => api.get(`${API_PREFIX}/result/report/${reportId}`),
};

export default api;
