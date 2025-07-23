import { useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../store';
import { authService } from '../services/authService';
import { User } from '../store/slices/authSlice';

export const useAuth = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isAuthenticated, user, loading, error } = useSelector((state: RootState) => state.auth);

  const login = useCallback(
    async (username: string, password: string) => {
      const result = await dispatch(authService.login(username, password) as any);
      if (result.success) {
        navigate('/');
      }
      return result;
    },
    [dispatch, navigate]
  );

  const logout = useCallback(async () => {
    await dispatch(authService.logout() as any);
    navigate('/login');
  }, [dispatch, navigate]);

  const checkAuth = useCallback(async () => {
    return await dispatch(authService.checkAuth() as any);
  }, [dispatch]);

  const updateProfile = useCallback(
    async (userData: Partial<User>) => {
      if (!user) return { success: false, error: 'User not authenticated' };
      
      const updatedUser = {
        ...user,
        ...userData,
      };
      
      return await dispatch(authService.updateProfile(updatedUser) as any);
    },
    [dispatch, user]
  );

  const changePassword = useCallback(
    async (currentPassword: string, newPassword: string) => {
      return await dispatch(authService.changePassword(currentPassword, newPassword) as any);
    },
    [dispatch]
  );

  const isAdmin = user?.role === 'admin';

  return {
    isAuthenticated,
    user,
    loading,
    error,
    isAdmin,
    login,
    logout,
    checkAuth,
    updateProfile,
    changePassword,
  };
};

export default useAuth;