import api from './api';
import {
  ConnectionConfig,
  ApiKey,
  BackupConfig,
  BackupRecord,
  ConnectionConfigFilter,
  ApiKeyFilter,
  BackupFilter,
} from '../types/systemSettings';

// System settings service functions
export const systemSettingsService = {
  // DB Connection management
  getConnectionConfigs: async (filter?: ConnectionConfigFilter): Promise<ConnectionConfig[]> => {
    const response = await api.get('/api/admin/connections', { params: filter });
    return response.data;
  },

  getConnectionConfigById: async (id: string): Promise<ConnectionConfig> => {
    const response = await api.get(`/api/admin/connections/${id}`);
    return response.data;
  },

  createConnectionConfig: async (
    config: Omit<ConnectionConfig, 'id' | 'createdAt' | 'updatedAt' | 'passwordLastUpdated'>
  ): Promise<ConnectionConfig> => {
    const response = await api.post('/api/admin/connections', config);
    return response.data;
  },

  updateConnectionConfig: async (
    id: string,
    config: Partial<ConnectionConfig>
  ): Promise<ConnectionConfig> => {
    const response = await api.put(`/api/admin/connections/${id}`, config);
    return response.data;
  },

  deleteConnectionConfig: async (id: string): Promise<void> => {
    await api.delete(`/api/admin/connections/${id}`);
  },

  testConnection: async (
    config: Partial<ConnectionConfig>
  ): Promise<{ success: boolean; message: string }> => {
    const response = await api.post('/api/admin/connections/test', config);
    return response.data;
  },

  // API Key management
  getApiKeys: async (filter?: ApiKeyFilter): Promise<ApiKey[]> => {
    const response = await api.get('/api/admin/api-keys', { params: filter });
    return response.data;
  },

  getApiKeyById: async (id: string): Promise<ApiKey> => {
    const response = await api.get(`/api/admin/api-keys/${id}`);
    return response.data;
  },

  createApiKey: async (
    apiKey: Omit<ApiKey, 'id' | 'createdAt' | 'lastFourDigits'>
  ): Promise<ApiKey & { fullKey: string }> => {
    const response = await api.post('/admin/api-keys', apiKey);
    return response.data;
  },

  updateApiKey: async (id: string, apiKey: Partial<ApiKey>): Promise<ApiKey> => {
    const response = await api.put(`/admin/api-keys/${id}`, apiKey);
    return response.data;
  },

  deleteApiKey: async (id: string): Promise<void> => {
    await api.delete(`/admin/api-keys/${id}`);
  },

  revokeApiKey: async (id: string): Promise<ApiKey> => {
    const response = await api.post(`/admin/api-keys/${id}/revoke`);
    return response.data;
  },

  // Backup and restore
  getBackupConfigs: async (): Promise<BackupConfig[]> => {
    const response = await api.get('/admin/backups/configs');
    return response.data;
  },

  getBackupConfigById: async (id: string): Promise<BackupConfig> => {
    const response = await api.get(`/admin/backups/configs/${id}`);
    return response.data;
  },

  createBackupConfig: async (
    config: Omit<BackupConfig, 'id' | 'createdAt' | 'updatedAt' | 'lastBackupAt' | 'nextBackupAt'>
  ): Promise<BackupConfig> => {
    const response = await api.post('/admin/backups/configs', config);
    return response.data;
  },

  updateBackupConfig: async (id: string, config: Partial<BackupConfig>): Promise<BackupConfig> => {
    const response = await api.put(`/admin/backups/configs/${id}`, config);
    return response.data;
  },

  deleteBackupConfig: async (id: string): Promise<void> => {
    await api.delete(`/admin/backups/configs/${id}`);
  },

  getBackupRecords: async (filter?: BackupFilter): Promise<BackupRecord[]> => {
    const response = await api.get('/admin/backups/records', { params: filter });
    return response.data;
  },

  createBackupNow: async (configId: string): Promise<BackupRecord> => {
    const response = await api.post(`/admin/backups/configs/${configId}/backup`);
    return response.data;
  },

  restoreFromBackup: async (backupId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post(`/admin/backups/records/${backupId}/restore`);
    return response.data;
  },

  downloadBackup: async (backupId: string): Promise<Blob> => {
    const response = await api.get(`/admin/backups/records/${backupId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },
};
