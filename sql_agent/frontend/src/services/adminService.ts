import api from './api';
import { User, UserFilter, Policy, PolicyFilter, UserPermissions, PolicySettings, Database } from '../types/admin';

// Types for admin service
export interface SystemStats {
  totalUsers: number;
  activeUsers: number;
  totalQueries: number;
  queriesLastDay: number;
  averageResponseTime: number;
  errorRate: number;
}

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'down';
  components: {
    database: 'healthy' | 'degraded' | 'down';
    api: 'healthy' | 'degraded' | 'down';
    llm: 'healthy' | 'degraded' | 'down';
    storage: 'healthy' | 'degraded' | 'down';
  };
  uptime: number; // in seconds
  lastChecked: string;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  category: 'auth' | 'query' | 'system' | 'security';
  message: string;
  userId?: string;
  details: Record<string, any>;
}

export interface LogFilter {
  level?: 'info' | 'warning' | 'error' | 'critical';
  category?: 'auth' | 'query' | 'system' | 'security';
  startDate?: string;
  endDate?: string;
  userId?: string;
  searchTerm?: string;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    fill?: boolean;
  }[];
}

// Admin service functions
export const adminService = {
  // Get system statistics
  getSystemStats: async (): Promise<SystemStats> => {
    const response = await api.get('/admin/stats');
    return response.data;
  },

  // Get system status
  getSystemStatus: async (): Promise<SystemStatus> => {
    const response = await api.get('/admin/status');
    return response.data;
  },

  // Get logs with optional filtering
  getLogs: async (filter?: LogFilter): Promise<LogEntry[]> => {
    const response = await api.get('/admin/logs', { params: filter });
    return response.data;
  },

  // Get usage statistics for charts
  getUsageStats: async (period: 'day' | 'week' | 'month'): Promise<ChartData> => {
    const response = await api.get(`/admin/usage-stats/${period}`);
    return response.data;
  },

  // Get error statistics for charts
  getErrorStats: async (period: 'day' | 'week' | 'month'): Promise<ChartData> => {
    const response = await api.get(`/admin/error-stats/${period}`);
    return response.data;
  },

  // Get performance metrics for charts
  getPerformanceMetrics: async (period: 'day' | 'week' | 'month'): Promise<ChartData> => {
    const response = await api.get(`/admin/performance/${period}`);
    return response.data;
  },

  // User management functions
  getUsers: async (filter?: UserFilter): Promise<User[]> => {
    const response = await api.get('/admin/users', { params: filter });
    return response.data;
  },

  getUserById: async (userId: string): Promise<User> => {
    const response = await api.get(`/admin/users/${userId}`);
    return response.data;
  },

  updateUserStatus: async (userId: string, status: 'active' | 'inactive' | 'suspended'): Promise<User> => {
    const response = await api.patch(`/admin/users/${userId}/status`, { status });
    return response.data;
  },

  updateUserRole: async (userId: string, role: 'user' | 'admin'): Promise<User> => {
    const response = await api.patch(`/admin/users/${userId}/role`, { role });
    return response.data;
  },

  updateUserPermissions: async (userId: string, permissions: UserPermissions): Promise<User> => {
    const response = await api.put(`/admin/users/${userId}/permissions`, permissions);
    return response.data;
  },

  // Policy management functions
  getPolicies: async (filter?: PolicyFilter): Promise<Policy[]> => {
    const response = await api.get('/admin/policies', { params: filter });
    return response.data;
  },

  getPolicyById: async (policyId: string): Promise<Policy> => {
    const response = await api.get(`/admin/policies/${policyId}`);
    return response.data;
  },

  createPolicy: async (policy: Omit<Policy, 'id' | 'createdAt' | 'updatedAt' | 'appliedToUsers'>): Promise<Policy> => {
    const response = await api.post('/admin/policies', policy);
    return response.data;
  },

  updatePolicy: async (policyId: string, policy: Partial<Policy>): Promise<Policy> => {
    const response = await api.put(`/admin/policies/${policyId}`, policy);
    return response.data;
  },

  deletePolicy: async (policyId: string): Promise<void> => {
    await api.delete(`/admin/policies/${policyId}`);
  },

  applyPolicyToUser: async (policyId: string, userId: string): Promise<void> => {
    await api.post(`/admin/policies/${policyId}/apply`, { userId });
  },

  removePolicyFromUser: async (policyId: string, userId: string): Promise<void> => {
    await api.post(`/admin/policies/${policyId}/remove`, { userId });
  },

  // Database information for permissions
  getDatabases: async (): Promise<Database[]> => {
    const response = await api.get('/admin/databases');
    return response.data;
  }
};