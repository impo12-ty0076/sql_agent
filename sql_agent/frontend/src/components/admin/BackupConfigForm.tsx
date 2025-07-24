import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Typography,
  Switch,
  FormControlLabel,
  CircularProgress,
  Paper,
  FormHelperText,
} from '@mui/material';
import { SelectChangeEvent } from '@mui/material/Select';
import { BackupConfig } from '../../types/systemSettings';

interface BackupConfigFormProps {
  initialValues?: Partial<BackupConfig>;
  onSubmit: (values: Partial<BackupConfig>) => Promise<void>;
  onCancel: () => void;
  loading: boolean;
}

const BackupConfigForm: React.FC<BackupConfigFormProps> = ({
  initialValues,
  onSubmit,
  onCancel,
  loading,
}) => {
  const [values, setValues] = useState<Partial<BackupConfig>>(
    initialValues || {
      name: '',
      schedule: 'daily',
      retention: 7,
      includeSettings: true,
      includeUserData: true,
      includeQueryHistory: true,
      destination: 'local',
      status: 'active',
    }
  );

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange =
    (field: keyof BackupConfig) =>
    (event: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
      const value = event.target.value;
      setValues({
        ...values,
        [field]: field === 'retention' ? Number(value) : value,
      });

      // Clear error when field is changed
      if (errors[field]) {
        setErrors({
          ...errors,
          [field]: '',
        });
      }
    };

  const handleSelectChange = (field: keyof BackupConfig) => (event: SelectChangeEvent) => {
    const value = event.target.value;
    setValues({
      ...values,
      [field]: value,
    });

    // Clear error when field is changed
    if (errors[field]) {
      setErrors({
        ...errors,
        [field]: '',
      });
    }
  };

  const handleSwitchChange =
    (field: keyof BackupConfig) => (event: React.ChangeEvent<HTMLInputElement>) => {
      setValues({
        ...values,
        [field]: event.target.checked,
      });
    };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!values.name) newErrors.name = 'Name is required';
    if (!values.schedule) newErrors.schedule = 'Schedule is required';
    if (!values.retention) newErrors.retention = 'Retention is required';
    if (values.retention && (values.retention < 1 || values.retention > 365)) {
      newErrors.retention = 'Retention must be between 1 and 365';
    }
    if (!values.destination) newErrors.destination = 'Destination is required';

    // Ensure at least one data type is included
    if (!values.includeSettings && !values.includeUserData && !values.includeQueryHistory) {
      newErrors.includeData = 'At least one data type must be included';
    }

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

  return (
    <Paper sx={{ p: 3 }}>
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <Typography variant="h6" gutterBottom>
          {initialValues?.id ? 'Edit Backup Configuration' : 'New Backup Configuration'}
        </Typography>

        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              required
              fullWidth
              label="Backup Name"
              value={values.name || ''}
              onChange={handleChange('name')}
              error={!!errors.name}
              helperText={errors.name}
              disabled={loading}
              margin="normal"
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControl fullWidth margin="normal" error={!!errors.schedule}>
              <InputLabel>Schedule</InputLabel>
              <Select
                value={values.schedule || 'daily'}
                onChange={handleSelectChange('schedule')}
                label="Schedule"
                disabled={loading}
              >
                <MenuItem value="daily">Daily</MenuItem>
                <MenuItem value="weekly">Weekly</MenuItem>
                <MenuItem value="monthly">Monthly</MenuItem>
                <MenuItem value="manual">Manual Only</MenuItem>
              </Select>
              {errors.schedule && <FormHelperText>{errors.schedule}</FormHelperText>}
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              required
              fullWidth
              label="Retention (number of backups)"
              type="number"
              value={values.retention || ''}
              onChange={handleChange('retention')}
              error={!!errors.retention}
              helperText={errors.retention}
              disabled={loading}
              margin="normal"
              InputProps={{ inputProps: { min: 1, max: 365 } }}
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
              Data to Include
            </Typography>
            {errors.includeData && <FormHelperText error>{errors.includeData}</FormHelperText>}
            <Grid container>
              <Grid item xs={12} sm={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={values.includeSettings || false}
                      onChange={handleSwitchChange('includeSettings')}
                      color="primary"
                      disabled={loading}
                    />
                  }
                  label="System Settings"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={values.includeUserData || false}
                      onChange={handleSwitchChange('includeUserData')}
                      color="primary"
                      disabled={loading}
                    />
                  }
                  label="User Data"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={values.includeQueryHistory || false}
                      onChange={handleSwitchChange('includeQueryHistory')}
                      color="primary"
                      disabled={loading}
                    />
                  }
                  label="Query History"
                />
              </Grid>
            </Grid>
          </Grid>

          <Grid item xs={12}>
            <TextField
              required
              fullWidth
              label="Destination Path"
              value={values.destination || ''}
              onChange={handleChange('destination')}
              error={!!errors.destination}
              helperText={errors.destination || 'Path where backups will be stored'}
              disabled={loading}
              margin="normal"
            />
          </Grid>

          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={values.status === 'active'}
                  onChange={e =>
                    setValues({
                      ...values,
                      status: e.target.checked ? 'active' : 'inactive',
                    })
                  }
                  color="primary"
                  disabled={loading}
                />
              }
              label="Active"
            />
          </Grid>

          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2, gap: 1 }}>
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

export default BackupConfigForm;
