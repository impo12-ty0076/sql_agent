import { Dispatch } from 'redux';
import axios from 'axios';
import api, { authAPI } from './api';
import { loginStart, loginSuccess, loginFailure, logout, User } from '../store/slices/authSlice';

// Helper to extract error message from AxiosError
const getErrorMessage = (error: unknown, fallback: string): string => {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { message?: string; detail?: string } | undefined;
    return data?.message || data?.detail || fallback;
  }
  return fallback;
};

export const authService = {
  /**
   * Login with username and password
   */
  login: (username: string, password: string) => async (dispatch: Dispatch) => {
    dispatch(loginStart());

    try {
      // First, request token using credentials
      const response = await authAPI.login(username, password);
      const { access_token: token } = response.data as { access_token: string };

      // Store token in localStorage
      localStorage.setItem('token', token);

      try {
        // Fetch user info using the newly acquired token.
        // At this point the Redux store does not yet know about the token,
        // so the Axios request interceptor will NOT add the Authorization header automatically.
        // We therefore explicitly pass the token in the headers for this single request.

        const meResponse = await api.get('/api/auth/me', {
          headers: { Authorization: `Bearer ${token}` },
        });

        const user = meResponse.data as User;

        // Now that we have both user and token, update the Redux store.
        dispatch(loginSuccess({ user, token }));
        return { success: true };
      } catch (meError: unknown) {
        // If fetching user info fails, still consider login failed
        const errorMessage = getErrorMessage(meError, '사용자 정보를 불러오지 못했습니다');
        dispatch(loginFailure(errorMessage));
        return { success: false, error: errorMessage };
      }
    } catch (err: unknown) {
      const errorMessage = getErrorMessage(err, '로그인 중 오류가 발생했습니다');
      dispatch(loginFailure(errorMessage));
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Logout user
   */
  logout: () => async (dispatch: Dispatch) => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout API error:', error);
    }

    // Clear token from localStorage
    localStorage.removeItem('token');

    // Update Redux state
    dispatch(logout());
  },

  /**
   * Check if user is authenticated and load user data
   */
  checkAuth: () => async (dispatch: Dispatch) => {
    const token = localStorage.getItem('token');

    if (!token) {
      return { authenticated: false };
    }

    try {
      const response = await api.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const user = response.data as User;

      dispatch(loginSuccess({ user, token }));
      return { authenticated: true };
    } catch (err: unknown) {
      localStorage.removeItem('token');
      dispatch(logout());
      return { authenticated: false };
    }
  },

  /**
   * Update user profile
   */
  updateProfile: (userData: User) => async (dispatch: Dispatch) => {
    try {
      // This would be a real API call in a production app
      // const response = await api.put('/api/auth/profile', userData);
      // const updatedUser = response.data;

      // For now, we'll simulate a successful update
      const token = localStorage.getItem('token') || '';

      dispatch(loginSuccess({ user: userData, token }));
      return { success: true };
    } catch (err: unknown) {
      return {
        success: false,
        error: getErrorMessage(err, '프로필 업데이트 중 오류가 발생했습니다'),
      };
    }
  },

  /**
   * Change password
   */
  changePassword: (currentPassword: string, newPassword: string) => async () => {
    try {
      // This would be a real API call in a production app
      // await api.put('/api/auth/password', { currentPassword, newPassword });

      // Prevent unused variable lint errors until implemented
      void currentPassword;
      void newPassword;

      return { success: true };
    } catch (err: unknown) {
      return {
        success: false,
        error: getErrorMessage(err, '비밀번호 변경 중 오류가 발생했습니다'),
      };
    }
  },
};

export default authService;
