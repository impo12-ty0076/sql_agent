import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Grid,
  Typography,
  Switch,
  FormControlLabel,
  CircularProgress,
  Alert,
  Paper
} from '@mui/material';
import { SelectChangeEvent } from '@mui/material/Select';
import { ConnectionConfig } from '../../types/systemSettings';

// Extended ConnectionConfig type to include password
interface ExtendedConnectionConfig extends ConnectionConfig {
  password?: string;
}

interface ConnectionConfigFormProps {
  initialValues?: Partial<ExtendedConnectionConfig>;
  onSubmit: (values: Partial<ExtendedConnectionConfig>) => Promise<void>;
  onTest?: (values: Partial<ExtendedConnectionConfig>) => Promise<{ success: boolean; message: string }>;
  onCancel: () => void;
  loading: boolean;
}

const ConnectionConfigForm: React.FC<ConnectionConfigFormProps> = ({
  initialValues,
  onSubmit,
  onTest,
  onCancel,
  loading
}) => {
  const [values, setValues] = useState<Partial<ExtendedConnectionConfig>>(
    initialValues || {
      name: '',
      type: 'mssql',
      host: '',
      port: 1433,
      username: '',
      password: '',
      defaultSchema: '',
      options: {},
      status: 'active'
    }
  );
  
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (field: keyof ExtendedConnectionConfig) => (
    event: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>
  ) => {
    const value = event.target.value;
    setValues({
      ...values,
      [field]: field === 'port' ? Number(value) : value
    });
    
    // Clear error when field is changed
    if (errors[field]) {
      setErrors({
        ...errors,
        [field]: ''
      });
    }
    
    // Clear test result when form is changed
    setTestResult(null);
  };

  const handleSelectChange = (field: keyof ExtendedConnectionConfig) => (
    event: SelectChangeEvent
  ) => {
    const value = event.target.value;
    setValues({
      ...values,
      [field]: value
    });
    
    // Clear error when field is changed
    if (errors[field]) {
      setErrors({
        ...errors,
        [field]: ''
      });
    }
    
    // Clear test result when form is changed
    setTestResult(null);
  };

  const handleStatusChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setValues({
      ...values,
      status: event.target.checked ? 'active' : 'inactive'
    });
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!values.name) newErrors.name = 'Name is required';
    if (!values.host) newErrors.host = 'Host is required';
    if (!values.port) newErrors.port = 'Port is required';
    if (values.port && (values.port < 0 || values.port > 65535)) {
      newErrors.port = 'Port must be between 0 and 65535';
    }
    if (!values.username) newErrors.username = 'Username is required';
    if (!initialValues?.id && !values.password) newErrors.password = 'Password is required';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validate()) return;
    
    try {
      await onSubmit(values);
    } catch (error) {
      console.error('Error submitting form:', error);
    }
  };

  const handleTest = async () => {
    if (!validate() || !onTest) return;
    
    setTestLoading(true);
    setTestResult(null);
    
    try {
      const result = await onTest(values);
      setTestResult(result);
    } catch (error) {
      console.error('Error testing connection:', error);
      setTestResult({ success: false, message: 'An error occurred while testing the connection' });
    } finally {
      setTestLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <Typography variant="h6" gutterBottom>
          {initialValues?.id ? 'Edit Connection Configuration' : 'New Connection Configuration'}
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              required
              fullWidth
              label="Connection Name"
              value={values.name || ''}
              onChange={handleChange('name')}
              error={!!errors.name}
              helperText={errors.name}
              disabled={loading}
              margin="normal"
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Database Type</InputLabel>
              <Select
                value={values.type || 'mssql'}
                onChange={handleSelectChange('type')}
                label="Database Type"
                disabled={loading}
              >
                <MenuItem value="mssql">MS-SQL Server</MenuItem>
                <MenuItem value="hana">SAP HANA</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={8}>
            <TextField
              required
              fullWidth
              label="Host"
              value={values.host || ''}
              onChange={handleChange('host')}
              error={!!errors.host}
              helperText={errors.host}
              disabled={loading}
              margin="normal"
            />
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <TextField
              required
              fullWidth
              label="Port"
              type="number"
              value={values.port || ''}
              onChange={handleChange('port')}
              error={!!errors.port}
              helperText={errors.port}
              disabled={loading}
              margin="normal"
              InputProps={{ inputProps: { min: 0, max: 65535 } }}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              required
              fullWidth
              label="Username"
              value={values.username || ''}
              onChange={handleChange('username')}
              error={!!errors.username}
              helperText={errors.username}
              disabled={loading}
              margin="normal"
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label={initialValues?.id ? 'New Password (leave blank to keep current)' : 'Password'}
              type={showPassword ? 'text' : 'password'}
              value={values.password || ''}
              onChange={handleChange('password')}
              error={!!errors.password}
              helperText={errors.password || (initialValues?.id ? 'Leave blank to keep current password' : '')}
              disabled={loading}
              margin="normal"
            />
          </Grid>
          
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={showPassword}
                  onChange={() => setShowPassword(!showPassword)}
                  color="primary"
                />
              }
              label="Show password"
            />
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Default Schema"
              value={values.defaultSchema || ''}
              onChange={handleChange('defaultSchema')}
              disabled={loading}
              margin="normal"
            />
          </Grid>
          
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={values.status === 'active'}
                  onChange={handleStatusChange}
                  color="primary"
                  disabled={loading}
                />
              }
              label="Active"
            />
          </Grid>
          
          {testResult && (
            <Grid item xs={12}>
              <Alert severity={testResult.success ? 'success' : 'error'}>
                {testResult.message}
              </Alert>
            </Grid>
          )}
          
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2, gap: 1 }}>
              {onTest && (
                <Button
                  variant="outlined"
                  onClick={handleTest}
                  disabled={loading || testLoading}
                  startIcon={testLoading && <CircularProgress size={20} />}
                >
                  Test Connection
                </Button>
              )}
              <Button onClick={onCancel} disabled={loading}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={loading}
                startIcon={loading && <CircularProgress size={20} />}
              >
                {initialValues?.id ? 'Update' : 'Create'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Paper>
  );
};

export default ConnectionConfigForm;