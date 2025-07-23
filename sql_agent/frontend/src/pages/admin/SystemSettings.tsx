import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  Snackbar,
  Alert,
  Paper,
  Divider
} from '@mui/material';
import { Add } from '@mui/icons-material';
import ConnectionConfigTable from '../../components/admin/ConnectionConfigTable';
import ConnectionConfigForm from '../../components/admin/ConnectionConfigForm';
import ApiKeyTable from '../../components/admin/ApiKeyTable';
import ApiKeyForm from '../../components/admin/ApiKeyForm';
import BackupConfigTable from '../../components/admin/BackupConfigTable';
import BackupConfigForm from '../../components/admin/BackupConfigForm';
import BackupRecordsTable from '../../components/admin/BackupRecordsTable';
import { systemSettingsService } from '../../services/systemSettingsService';
import { 
  ConnectionConfig, 
  ApiKey, 
  BackupConfig, 
  BackupRecord,
  ConnectionConfigFilter,
  ApiKeyFilter,
  BackupFilter
} from '../../types/systemSettings';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

const a11yProps = (index: number) => {
  return {
    id: `settings-tab-${index}`,
    'aria-controls': `settings-tabpanel-${index}`,
  };
};

const SystemSettings: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  
  // Connection configs state
  const [connections, setConnections] = useState<ConnectionConfig[]>([]);
  const [connectionFilter, setConnectionFilter] = useState<ConnectionConfigFilter>({});
  const [connectionPage, setConnectionPage] = useState(0);
  const [connectionRowsPerPage, setConnectionRowsPerPage] = useState(10);
  const [connectionTotalCount, setConnectionTotalCount] = useState(0);
  const [selectedConnection, setSelectedConnection] = useState<ConnectionConfig | null>(null);
  const [showConnectionForm, setShowConnectionForm] = useState(false);
  const [deleteConnectionDialog, setDeleteConnectionDialog] = useState(false);
  
  // API keys state
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [apiKeyFilter, setApiKeyFilter] = useState<ApiKeyFilter>({});
  const [apiKeyPage, setApiKeyPage] = useState(0);
  const [apiKeyRowsPerPage, setApiKeyRowsPerPage] = useState(10);
  const [apiKeyTotalCount, setApiKeyTotalCount] = useState(0);
  const [selectedApiKey, setSelectedApiKey] = useState<ApiKey | null>(null);
  const [showApiKeyForm, setShowApiKeyForm] = useState(false);
  const [deleteApiKeyDialog, setDeleteApiKeyDialog] = useState(false);
  const [revokeApiKeyDialog, setRevokeApiKeyDialog] = useState(false);
  
  // Backup configs state
  const [backupConfigs, setBackupConfigs] = useState<BackupConfig[]>([]);
  const [selectedBackupConfig, setSelectedBackupConfig] = useState<BackupConfig | null>(null);
  const [showBackupConfigForm, setShowBackupConfigForm] = useState(false);
  const [deleteBackupConfigDialog, setDeleteBackupConfigDialog] = useState(false);
  
  // Backup records state
  const [backupRecords, setBackupRecords] = useState<BackupRecord[]>([]);
  const [backupFilter, setBackupFilter] = useState<BackupFilter>({});
  const [backupPage, setBackupPage] = useState(0);
  const [backupRowsPerPage, setBackupRowsPerPage] = useState(10);
  const [backupTotalCount, setBackupTotalCount] = useState(0);
  const [selectedBackupRecord, setSelectedBackupRecord] = useState<BackupRecord | null>(null);
  const [restoreBackupDialog, setRestoreBackupDialog] = useState(false);
  
  // Common state
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({
    open: false,
    message: '',
    severity: 'info'
  });

  // Tab handling
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Snackbar handling
  const handleSnackbarClose = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info' | 'warning') => {
    setSnackbar({
      open: true,
      message,
      severity
    });
  };

  // Connection configs handlers
  const loadConnections = async () => {
    setLoading(true);
    try {
      const data = await systemSettingsService.getConnectionConfigs(connectionFilter);
      setConnections(data);
      setConnectionTotalCount(data.length); // In a real app, this would come from the API
    } catch (error) {
      console.error('Error loading connections:', error);
      showSnackbar('Failed to load database connections', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectionFilterChange = (filter: ConnectionConfigFilter) => {
    setConnectionFilter(filter);
    setConnectionPage(0);
  };

  const handleConnectionPageChange = (event: unknown, newPage: number) => {
    setConnectionPage(newPage);
  };

  const handleConnectionRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setConnectionRowsPerPage(parseInt(event.target.value, 10));
    setConnectionPage(0);
  };

  const handleAddConnection = () => {
    setSelectedConnection(null);
    setShowConnectionForm(true);
  };

  const handleEditConnection = (connection: ConnectionConfig) => {
    setSelectedConnection(connection);
    setShowConnectionForm(true);
  };

  const handleDeleteConnection = (connection: ConnectionConfig) => {
    setSelectedConnection(connection);
    setDeleteConnectionDialog(true);
  };

  const handleTestConnection = async (connection: ConnectionConfig) => {
    setLoading(true);
    try {
      const result = await systemSettingsService.testConnection(connection);
      showSnackbar(
        result.success 
          ? `Connection to ${connection.name} successful` 
          : `Connection to ${connection.name} failed: ${result.message}`,
        result.success ? 'success' : 'error'
      );
    } catch (error) {
      console.error('Error testing connection:', error);
      showSnackbar(`Connection test failed: ${(error as Error).message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectionFormSubmit = async (values: Partial<ConnectionConfig>) => {
    setLoading(true);
    try {
      if (selectedConnection) {
        await systemSettingsService.updateConnectionConfig(selectedConnection.id, values);
        showSnackbar('Connection updated successfully', 'success');
      } else {
        await systemSettingsService.createConnectionConfig(values as any);
        showSnackbar('Connection created successfully', 'success');
      }
      setShowConnectionForm(false);
      loadConnections();
    } catch (error) {
      console.error('Error saving connection:', error);
      showSnackbar(`Failed to save connection: ${(error as Error).message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectionFormCancel = () => {
    setShowConnectionForm(false);
  };

  const confirmDeleteConnection = async () => {
    if (!selectedConnection) return;
    
    setLoading(true);
    try {
      await systemSettingsService.deleteConnectionConfig(selectedConnection.id);
      showSnackbar('Connection deleted successfully', 'success');
      setDeleteConnectionDialog(false);
      loadConnections();
    } catch (error) {
      console.error('Error deleting connection:', error);
      showSnackbar(`Failed to delete connection: ${(error as Error).message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // API keys handlers
  const loadApiKeys = async () => {
    setLoading(true);
    try {
      const data = await systemSettingsService.getApiKeys(apiKeyFilter);
      setApiKeys(data);
      setApiKeyTotalCount(data.length); // In a real app, this would come from the API
    } catch (error) {
      console.error('Error loading API keys:', error);
      showSnackbar('Failed to load API keys', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleApiKeyFilterChange = (filter: ApiKeyFilter) => {
    setApiKeyFilter(filter);
    setApiKeyPage(0);
  };

  const handleApiKeyPageChange = (event: unknown, newPage: number) => {
    setApiKeyPage(newPage);
  };

  const handleApiKeyRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setApiKeyRowsPerPage(parseInt(event.target.value, 10));
    setApiKeyPage(0);
  };

  const handleAddApiKey = () => {
    setSelectedApiKey(null);
    setShowApiKeyForm(true);
  };

  const handleEditApiKey = (apiKey: ApiKey) => {
    setSelectedApiKey(apiKey);
    setShowApiKeyForm(true);
  };

  const handleDeleteApiKey = (apiKey: ApiKey) => {
    setSelectedApiKey(apiKey);
    setDeleteApiKeyDialog(true);
  };

  const handleRevokeApiKey = (apiKey: ApiKey) => {
    setSelectedApiKey(apiKey);
    setRevokeApiKeyDialog(true);
  };

  const handleApiKeyFormSubmit = async (values: Partial<ApiKey>) => {
    setLoading(true);
    try {
      if (selectedApiKey) {
        await systemSettingsService.updateApiKey(selectedApiKey.id, values);
        showSnackbar('API key updated successfully', 'success');
      } else {
        const result = await systemSettingsService.createApiKey(values as any);
        // The full key is returned only once when created
        if (result.fullKey) {
          // The form component will display the full key to the user
          return { fullKey: result.fullKey };
        }
        showSnackbar('API key created successfully', 'success');
      }
      setShowApiKeyForm(false);
      loadApiKeys();
      return {};
    } catch (error) {
      console.error('Error saving API key:', error);
      showSnackbar(`Failed to save API key: ${(error as Error).message}`, 'error');
      return {};
    } finally {
      setLoading(false);
    }
  };

  const handleApiKeyFormCancel = () => {
    setShowApiKeyForm(false);
  };

  const confirmDeleteApiKey = async () => {
    if (!selectedApiKey) return;
    
    setLoading(true);
    try {
      await systemSettingsService.deleteApiKey(selectedApiKey.id);
      showSnackbar('API key deleted successfully', 'success');
      setDeleteApiKeyDialog(false);
      loadApiKeys();
    } catch (error) {
      console.error('Error deleting API key:', error);
      showSnackbar(`Failed to delete API key: ${(error as Error).message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const confirmRevokeApiKey = async () => {
    if (!selectedApiKey) return;
    
    setLoading(true);
    try {
      await systemSettingsService.revokeApiKey(selectedApiKey.id);
      showSnackbar('API key revoked successfully', 'success');
      setRevokeApiKeyDialog(false);
      loadApiKeys();
    } catch (error) {
      console.error('Error revoking API key:', error);
      showSnackbar(`Failed to revoke API key: ${(error as Error).message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Backup configs handlers
  const loadBackupConfigs = async () => {
    setLoading(true);
    try {
      const data = await systemSettingsService.getBackupConfigs();
      setBackupConfigs(data);
    } catch (error) {
      console.error('Error loading backup configs:', error);
      showSnackbar('Failed to load backup configurations', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAddBackupConfig = () => {
    setSelectedBackupConfig(null);
    setShowBackupConfigForm(true);
  };

  const handleEditBackupConfig = (config: BackupConfig) => {
    setSelectedBackupConfig(config);
    setShowBackupConfigForm(true);
  };

  const handleDeleteBackupConfig = (config: BackupConfig) => {
    setSelectedBackupConfig(config);
    setDeleteBackupConfigDialog(true);
  };

  const handleBackupNow = async (config: BackupConfig) => {
    setLoading(true);
    try {
      await systemSettingsService.createBackupNow(config.id);
      showSnackbar('Backup started successfully', 'success');
      loadBackupRecords();
    } catch (error) {
      console.error('Error starting backup:', error);
      showSnackbar(`Failed to start backup: ${(error as Error).message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleBackupConfigFormSubmit = async (values: Partial<BackupConfig>) => {
    setLoading(true);
    try {
      if (selectedBackupConfig) {
        await systemSettingsService.updateBackupConfig(selectedBackupConfig.id, values);
        showSnackbar('Backup configuration updated successfully', 'success');
      } else {
        await systemSettingsService.createBackupConfig(values as any);
        showSnackbar('Backup configuration created successfully', 'success');
      }
      setShowBackupConfigForm(false);
      loadBackupConfigs();
    } catch (error) {
      console.error('Error saving backup config:', error);
      showSnackbar(`Failed to save backup configuration: ${(error as Error).message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleBackupConfigFormCancel = () => {
    setShowBackupConfigForm(false);
  };

  const confirmDeleteBackupConfig = async () => {
    if (!selectedBackupConfig) return;
    
    setLoading(true);
    try {
      await systemSettingsService.deleteBackupConfig(selectedBackupConfig.id);
      showSnackbar('Backup configuration deleted successfully', 'success');
      setDeleteBackupConfigDialog(false);
      loadBackupConfigs();
    } catch (error) {
      console.error('Error deleting backup config:', error);
      showSnackbar(`Failed to delete backup configuration: ${(error as Error).message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Backup records handlers
  const loadBackupRecords = async () => {
    setLoading(true);
    try {
      const data = await systemSettingsService.getBackupRecords(backupFilter);
      setBackupRecords(data);
      setBackupTotalCount(data.length); // In a real app, this would come from the API
    } catch (error) {
      console.error('Error loading backup records:', error);
      showSnackbar('Failed to load backup records', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleBackupFilterChange = (filter: BackupFilter) => {
    setBackupFilter(filter);
    setBackupPage(0);
  };

  const handleBackupPageChange = (event: unknown, newPage: number) => {
    setBackupPage(newPage);
  };

  const handleBackupRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setBackupRowsPerPage(parseInt(event.target.value, 10));
    setBackupPage(0);
  };

  const handleRestoreBackup = (record: BackupRecord) => {
    setSelectedBackupRecord(record);
    setRestoreBackupDialog(true);
  };

  const handleDownloadBackup = async (record: BackupRecord) => {
    setLoading(true);
    try {
      const blob = await systemSettingsService.downloadBackup(record.id);
      
      // Create a download link and trigger it
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `backup-${record.id}-${new Date(record.timestamp).toISOString().split('T')[0]}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      showSnackbar('Backup download started', 'success');
    } catch (error) {
      console.error('Error downloading backup:', error);
      showSnackbar(`Failed to download backup: ${(error as Error).message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const confirmRestoreBackup = async () => {
    if (!selectedBackupRecord) return;
    
    setLoading(true);
    try {
      const result = await systemSettingsService.restoreFromBackup(selectedBackupRecord.id);
      showSnackbar(
        result.success 
          ? 'System restored successfully' 
          : `Restore failed: ${result.message}`,
        result.success ? 'success' : 'error'
      );
      setRestoreBackupDialog(false);
      
      // Reload all data after restore
      loadConnections();
      loadApiKeys();
      loadBackupConfigs();
      loadBackupRecords();
    } catch (error) {
      console.error('Error restoring backup:', error);
      showSnackbar(`Failed to restore system: ${(error as Error).message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Load data on component mount and tab change
  useEffect(() => {
    switch (tabValue) {
      case 0:
        loadConnections();
        break;
      case 1:
        loadApiKeys();
        break;
      case 2:
        loadBackupConfigs();
        loadBackupRecords();
        break;
    }
  }, [tabValue, connectionFilter, apiKeyFilter, backupFilter]);

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        System Settings
      </Typography>
      
      <Paper sx={{ width: '100%', mb: 2 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="system settings tabs"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Database Connections" {...a11yProps(0)} />
          <Tab label="API Keys" {...a11yProps(1)} />
          <Tab label="Backup & Restore" {...a11yProps(2)} />
        </Tabs>
        
        {/* Database Connections Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<Add />}
              onClick={handleAddConnection}
            >
              Add Connection
            </Button>
          </Box>
          
          <ConnectionConfigTable
            connections={connections}
            loading={loading}
            onEdit={handleEditConnection}
            onDelete={handleDeleteConnection}
            onTest={handleTestConnection}
            onFilterChange={handleConnectionFilterChange}
            filter={connectionFilter}
            totalCount={connectionTotalCount}
            page={connectionPage}
            rowsPerPage={connectionRowsPerPage}
            onPageChange={handleConnectionPageChange}
            onRowsPerPageChange={handleConnectionRowsPerPageChange}
          />
        </TabPanel>
        
        {/* API Keys Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<Add />}
              onClick={handleAddApiKey}
            >
              Add API Key
            </Button>
          </Box>
          
          <ApiKeyTable
            apiKeys={apiKeys}
            loading={loading}
            onEdit={handleEditApiKey}
            onDelete={handleDeleteApiKey}
            onRevoke={handleRevokeApiKey}
            onFilterChange={handleApiKeyFilterChange}
            filter={apiKeyFilter}
            totalCount={apiKeyTotalCount}
            page={apiKeyPage}
            rowsPerPage={apiKeyRowsPerPage}
            onPageChange={handleApiKeyPageChange}
            onRowsPerPageChange={handleApiKeyRowsPerPageChange}
          />
        </TabPanel>
        
        {/* Backup & Restore Tab */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Backup Configurations
          </Typography>
          
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<Add />}
              onClick={handleAddBackupConfig}
            >
              Add Backup Configuration
            </Button>
          </Box>
          
          <BackupConfigTable
            backupConfigs={backupConfigs}
            loading={loading}
            onEdit={handleEditBackupConfig}
            onDelete={handleDeleteBackupConfig}
            onBackupNow={handleBackupNow}
          />
          
          <Divider sx={{ my: 4 }} />
          
          <Typography variant="h6" gutterBottom>
            Backup History
          </Typography>
          
          <BackupRecordsTable
            backupRecords={backupRecords}
            loading={loading}
            onRestore={handleRestoreBackup}
            onDownload={handleDownloadBackup}
            onFilterChange={handleBackupFilterChange}
            filter={backupFilter}
            totalCount={backupTotalCount}
            page={backupPage}
            rowsPerPage={backupRowsPerPage}
            onPageChange={handleBackupPageChange}
            onRowsPerPageChange={handleBackupRowsPerPageChange}
          />
        </TabPanel>
      </Paper>
      
      {/* Connection Form Dialog */}
      <Dialog
        open={showConnectionForm}
        onClose={handleConnectionFormCancel}
        maxWidth="md"
        fullWidth
      >
        <DialogContent>
          <ConnectionConfigForm
            initialValues={selectedConnection || undefined}
            onSubmit={handleConnectionFormSubmit}
            onTest={systemSettingsService.testConnection}
            onCancel={handleConnectionFormCancel}
            loading={loading}
          />
        </DialogContent>
      </Dialog>
      
      {/* API Key Form Dialog */}
      <Dialog
        open={showApiKeyForm}
        onClose={handleApiKeyFormCancel}
        maxWidth="md"
        fullWidth
      >
        <DialogContent>
          <ApiKeyForm
            initialValues={selectedApiKey || undefined}
            onSubmit={handleApiKeyFormSubmit}
            onCancel={handleApiKeyFormCancel}
            loading={loading}
          />
        </DialogContent>
      </Dialog>
      
      {/* Backup Config Form Dialog */}
      <Dialog
        open={showBackupConfigForm}
        onClose={handleBackupConfigFormCancel}
        maxWidth="md"
        fullWidth
      >
        <DialogContent>
          <BackupConfigForm
            initialValues={selectedBackupConfig || undefined}
            onSubmit={handleBackupConfigFormSubmit}
            onCancel={handleBackupConfigFormCancel}
            loading={loading}
          />
        </DialogContent>
      </Dialog>
      
      {/* Delete Connection Confirmation Dialog */}
      <Dialog
        open={deleteConnectionDialog}
        onClose={() => setDeleteConnectionDialog(false)}
      >
        <DialogTitle>Delete Connection</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the connection "{selectedConnection?.name}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConnectionDialog(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={confirmDeleteConnection} color="error" disabled={loading}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Delete API Key Confirmation Dialog */}
      <Dialog
        open={deleteApiKeyDialog}
        onClose={() => setDeleteApiKeyDialog(false)}
      >
        <DialogTitle>Delete API Key</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the API key "{selectedApiKey?.name}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteApiKeyDialog(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={confirmDeleteApiKey} color="error" disabled={loading}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Revoke API Key Confirmation Dialog */}
      <Dialog
        open={revokeApiKeyDialog}
        onClose={() => setRevokeApiKeyDialog(false)}
      >
        <DialogTitle>Revoke API Key</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to revoke the API key "{selectedApiKey?.name}"? This will immediately invalidate the key and it can no longer be used.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRevokeApiKeyDialog(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={confirmRevokeApiKey} color="warning" disabled={loading}>
            Revoke
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Delete Backup Config Confirmation Dialog */}
      <Dialog
        open={deleteBackupConfigDialog}
        onClose={() => setDeleteBackupConfigDialog(false)}
      >
        <DialogTitle>Delete Backup Configuration</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the backup configuration "{selectedBackupConfig?.name}"? This will not delete existing backup files, but scheduled backups will no longer run.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteBackupConfigDialog(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={confirmDeleteBackupConfig} color="error" disabled={loading}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Restore Backup Confirmation Dialog */}
      <Dialog
        open={restoreBackupDialog}
        onClose={() => setRestoreBackupDialog(false)}
      >
        <DialogTitle>Restore System</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to restore the system from the backup created on {selectedBackupRecord ? new Date(selectedBackupRecord.timestamp).toLocaleString() : ''}? This will overwrite current system settings and data.
          </DialogContentText>
          <Alert severity="warning" sx={{ mt: 2 }}>
            Warning: This operation cannot be undone. All users will be disconnected during the restore process.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRestoreBackupDialog(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={confirmRestoreBackup} color="warning" disabled={loading}>
            Restore
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleSnackbarClose} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SystemSettings;