import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import SystemSettings from '../SystemSettings';
import { systemSettingsService } from '../../../services/systemSettingsService';

// Mock the systemSettingsService
jest.mock('../../../services/systemSettingsService', () => ({
  systemSettingsService: {
    getConnectionConfigs: jest.fn().mockResolvedValue([
      {
        id: '1',
        name: 'Test DB',
        type: 'mssql',
        host: 'localhost',
        port: 1433,
        username: 'sa',
        passwordLastUpdated: new Date('2023-01-01'),
        defaultSchema: 'dbo',
        options: {},
        createdAt: new Date('2023-01-01'),
        updatedAt: new Date('2023-01-01'),
        status: 'active'
      }
    ]),
    getApiKeys: jest.fn().mockResolvedValue([
      {
        id: '1',
        name: 'Test API Key',
        service: 'openai',
        lastFourDigits: '1234',
        createdAt: new Date('2023-01-01'),
        status: 'active'
      }
    ]),
    getBackupConfigs: jest.fn().mockResolvedValue([
      {
        id: '1',
        name: 'Daily Backup',
        schedule: 'daily',
        retention: 7,
        includeSettings: true,
        includeUserData: true,
        includeQueryHistory: true,
        destination: '/backups/daily',
        status: 'active'
      }
    ]),
    getBackupRecords: jest.fn().mockResolvedValue([
      {
        id: '1',
        configId: '1',
        timestamp: new Date('2023-01-01'),
        size: 1024 * 1024, // 1MB
        status: 'completed',
        location: '/backups/daily/backup-2023-01-01.zip'
      }
    ]),
    testConnection: jest.fn().mockResolvedValue({ success: true, message: 'Connection successful' }),
    createConnectionConfig: jest.fn().mockResolvedValue({}),
    updateConnectionConfig: jest.fn().mockResolvedValue({}),
    deleteConnectionConfig: jest.fn().mockResolvedValue({}),
    createApiKey: jest.fn().mockResolvedValue({ fullKey: 'test-api-key-12345' }),
    updateApiKey: jest.fn().mockResolvedValue({}),
    deleteApiKey: jest.fn().mockResolvedValue({}),
    revokeApiKey: jest.fn().mockResolvedValue({}),
    createBackupConfig: jest.fn().mockResolvedValue({}),
    updateBackupConfig: jest.fn().mockResolvedValue({}),
    deleteBackupConfig: jest.fn().mockResolvedValue({}),
    createBackupNow: jest.fn().mockResolvedValue({}),
    restoreFromBackup: jest.fn().mockResolvedValue({ success: true, message: 'Restore successful' }),
    downloadBackup: jest.fn().mockResolvedValue(new Blob(['test']))
  }
}));

// Mock store
const mockStore = configureStore([]);
const store = mockStore({
  auth: {
    isAuthenticated: true,
    user: { role: 'admin' }
  },
  ui: {
    theme: 'light'
  }
});

// Mock window.URL.createObjectURL
global.URL.createObjectURL = jest.fn();
global.URL.revokeObjectURL = jest.fn();

describe('SystemSettings', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the system settings page with tabs', async () => {
    render(
      <Provider store={store}>
        <SystemSettings />
      </Provider>
    );
    
    // Check if the page title is rendered
    expect(screen.getByText('System Settings')).toBeInTheDocument();
    
    // Check if tabs are rendered
    expect(screen.getByText('Database Connections')).toBeInTheDocument();
    expect(screen.getByText('API Keys')).toBeInTheDocument();
    expect(screen.getByText('Backup & Restore')).toBeInTheDocument();
    
    // Wait for data to load
    await waitFor(() => {
      expect(systemSettingsService.getConnectionConfigs).toHaveBeenCalled();
    });
    
    // Check if connection data is loaded
    expect(screen.getByText('Test DB')).toBeInTheDocument();
  });

  it('switches between tabs', async () => {
    render(
      <Provider store={store}>
        <SystemSettings />
      </Provider>
    );
    
    // Wait for initial data to load
    await waitFor(() => {
      expect(systemSettingsService.getConnectionConfigs).toHaveBeenCalled();
    });
    
    // Switch to API Keys tab
    fireEvent.click(screen.getByText('API Keys'));
    
    // Wait for API keys data to load
    await waitFor(() => {
      expect(systemSettingsService.getApiKeys).toHaveBeenCalled();
    });
    
    // Check if API key data is loaded
    expect(screen.getByText('Test API Key')).toBeInTheDocument();
    
    // Switch to Backup & Restore tab
    fireEvent.click(screen.getByText('Backup & Restore'));
    
    // Wait for backup data to load
    await waitFor(() => {
      expect(systemSettingsService.getBackupConfigs).toHaveBeenCalled();
      expect(systemSettingsService.getBackupRecords).toHaveBeenCalled();
    });
    
    // Check if backup data is loaded
    expect(screen.getByText('Daily Backup')).toBeInTheDocument();
  });

  it('opens connection form when add button is clicked', async () => {
    render(
      <Provider store={store}>
        <SystemSettings />
      </Provider>
    );
    
    // Wait for data to load
    await waitFor(() => {
      expect(systemSettingsService.getConnectionConfigs).toHaveBeenCalled();
    });
    
    // Click add connection button
    fireEvent.click(screen.getByText('Add Connection'));
    
    // Check if form is displayed
    expect(screen.getByText('New Connection Configuration')).toBeInTheDocument();
  });

  it('opens API key form when add button is clicked', async () => {
    render(
      <Provider store={store}>
        <SystemSettings />
      </Provider>
    );
    
    // Switch to API Keys tab
    fireEvent.click(screen.getByText('API Keys'));
    
    // Wait for data to load
    await waitFor(() => {
      expect(systemSettingsService.getApiKeys).toHaveBeenCalled();
    });
    
    // Click add API key button
    fireEvent.click(screen.getByText('Add API Key'));
    
    // Check if form is displayed
    expect(screen.getByText('New API Key')).toBeInTheDocument();
  });

  it('opens backup config form when add button is clicked', async () => {
    render(
      <Provider store={store}>
        <SystemSettings />
      </Provider>
    );
    
    // Switch to Backup & Restore tab
    fireEvent.click(screen.getByText('Backup & Restore'));
    
    // Wait for data to load
    await waitFor(() => {
      expect(systemSettingsService.getBackupConfigs).toHaveBeenCalled();
    });
    
    // Click add backup config button
    fireEvent.click(screen.getByText('Add Backup Configuration'));
    
    // Check if form is displayed
    expect(screen.getByText('New Backup Configuration')).toBeInTheDocument();
  });
});