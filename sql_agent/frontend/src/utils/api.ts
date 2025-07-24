import axios from 'axios';
import { store } from '../store';
import { logout } from '../store/slices/authSlice';
import { addNotification } from '../store/slices/uiSlice';

// Create axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  config => {
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

// Response interceptor
api.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    if (error.response) {
      // Handle 401 Unauthorized errors
      if (error.response.status === 401) {
        store.dispatch(logout());
        store.dispatch(
          addNotification({
            type: 'error',
            message: 'Your session has expired. Please log in again.',
          })
        );
      }

      // Handle 403 Forbidden errors
      if (error.response.status === 403) {
        store.dispatch(
          addNotification({
            type: 'error',
            message: 'You do not have permission to perform this action.',
          })
        );
      }

      // Handle 500 Server errors
      if (error.response.status >= 500) {
        store.dispatch(
          addNotification({
            type: 'error',
            message: 'A server error occurred. Please try again later.',
          })
        );
      }
    } else if (error.request) {
      // The request was made but no response was received
      store.dispatch(
        addNotification({
          type: 'error',
          message: 'Network error. Please check your connection.',
        })
      );
    }

    return Promise.reject(error);
  }
);

export default api;
