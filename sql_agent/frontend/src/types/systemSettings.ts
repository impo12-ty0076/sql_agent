// Types for system settings management

export interface ConnectionConfig {
  id: string;
  name: string;
  type: 'mssql' | 'hana';
  host: string;
  port: number;
  username: string;
  passwordLastUpdated: Date;
  defaultSchema: string;
  options: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
  status: 'active' | 'inactive';
}

export interface ApiKey {
  id: string;
  name: string;
  service: 'openai' | 'azure_openai' | 'huggingface' | 'other';
  lastFourDigits: string;
  createdAt: Date;
  expiresAt?: Date;
  status: 'active' | 'expired' | 'revoked';
}

export interface BackupConfig {
  id: string;
  name: string;
  schedule: 'daily' | 'weekly' | 'monthly' | 'manual';
  retention: number; // Number of backups to retain
  includeSettings: boolean;
  includeUserData: boolean;
  includeQueryHistory: boolean;
  destination: string;
  lastBackupAt?: Date;
  nextBackupAt?: Date;
  status: 'active' | 'inactive';
}

export interface BackupRecord {
  id: string;
  configId: string;
  timestamp: Date;
  size: number; // In bytes
  status: 'completed' | 'failed' | 'in_progress';
  location: string;
  error?: string;
}

export interface ConnectionConfigFilter {
  type?: 'mssql' | 'hana';
  status?: 'active' | 'inactive';
  searchTerm?: string;
}

export interface ApiKeyFilter {
  service?: 'openai' | 'azure_openai' | 'huggingface' | 'other';
  status?: 'active' | 'expired' | 'revoked';
  searchTerm?: string;
}

export interface BackupFilter {
  status?: 'completed' | 'failed' | 'in_progress';
  startDate?: Date;
  endDate?: Date;
}
