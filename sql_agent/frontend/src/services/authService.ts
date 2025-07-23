import { Dispatch } from 'redux';
import { authAPI } from './api';
import { loginStart, loginSuccess, loginFailure, logout, User } from '../store/slices/authSlice';

export const authService = {
  /**
   * Login with username and password
   */
  login: (username: string, password: string) => async (dispatch: Dispatch) => {
    dispatch(loginStart());

    try {
      const response = await authAPI.login(username, password);
      const data = response.data as { user: User; token: string };
      const { user, token } = data;

      // Store token in localStorage
      localStorage.setItem('token', token);

      dispatch(loginSuccess({ user, token }));
      return { success: true };
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || '�α��� �� ������ �߻��߽��ϴ�';
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
      const response = await authAPI.getCurrentUser();
      const user = response.data as User;

      dispatch(loginSuccess({ user, token }));
      return { authenticated: true };
    } catch (err) {
      localStorage.removeItem('token');
      dispatch(logout());
      return { authenticated: false };
    }
  },

  /**
   * Update user profile
   */
  updateProfile: (userData: any) => async (dispatch: Dispatch) => {
    try {
      // This would be a real API call in a production app
      // const response = await api.put('/api/auth/profile', userData);
      // const updatedUser = response.data;

      // For now, we'll simulate a successful update
      const token = localStorage.getItem('token') || '';

      dispatch(loginSuccess({ user: userData, token }));
      return { success: true };
    } catch (err: any) {
      return {
        success: false,
        error: err.response?.data?.message || '������ ������Ʈ �� ������ �߻��߽��ϴ�',
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

      // For now, we'll simulate a successful update
      await new Promise(resolve => setTimeout(resolve, 1000));

      return { success: true };
    } catch (err: any) {
      return {
        success: false,
        error: err.response?.data?.message || '��й�ȣ ���� �� ������ �߻��߽��ϴ�',
      };
    }
  },
};

export default authService;
