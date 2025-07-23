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
  CircularProgress,
  Paper,
  FormHelperText,
  Alert,
  IconButton,
  InputAdornment,
  SelectChangeEvent,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ContentCopy, Visibility, VisibilityOff } from '@mui/icons-material';
import { ApiKey } from '../../types/systemSettings';

// Extended ApiKey interface to include the key property for form handling
interface ApiKeyFormData extends Partial<ApiKey> {
  key?: string;
}

interface ApiKeyFormProps {
  initialValues?: Partial<ApiKey>;
  onSubmit: (values: Partial<ApiKey>) => Promise<{ fullKey?: string }>;
  onCancel: () => void;
  loading: boolean;
}

const ApiKeyForm: React.FC<ApiKeyFormProps> = ({ initialValues, onSubmit, onCancel, loading }) => {
  const [values, setValues] = useState<ApiKeyFormData>(
    initialValues || {
      name: '',
      service: 'openai',
      status: 'active',
    }
  );

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [expiryDate, setExpiryDate] = useState<Date | undefined>(
    initialValues?.expiresAt ? new Date(initialValues.expiresAt) : undefined
  );
  const [showKey, setShowKey] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [keyCopied, setKeyCopied] = useState(false);

  const handleChange =
    (field: keyof ApiKeyFormData) =>
    (event: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
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

  const handleServiceChange = (event: SelectChangeEvent) => {
    setValues({
      ...values,
      service: event.target.value as ApiKey['service'],
    });

    // Clear error when field is changed
    if (errors.service) {
      setErrors({
        ...errors,
        service: '',
      });
    }
  };

  const handleExpiryDateChange = (date: Date | null) => {
    setExpiryDate(date || undefined);
    setValues({
      ...values,
      expiresAt: date || undefined,
    });
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!values.name) newErrors.name = 'Name is required';
    if (!values.service) newErrors.service = 'Service is required';
    if (!initialValues?.id && !values.key) newErrors.key = 'API Key is required';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!validate()) return;

    try {
      const result = await onSubmit({
        ...values,
        expiresAt: expiryDate,
      });

      if (result.fullKey) {
        setNewKey(result.fullKey);
      }
    } catch (error) {
      console.error('Error submitting form:', error);
    }
  };

  const handleCopyKey = () => {
    if (newKey) {
      navigator.clipboard.writeText(newKey);
      setKeyCopied(true);
      setTimeout(() => setKeyCopied(false), 2000);
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <Typography variant="h6" gutterBottom>
          {initialValues?.id ? 'Edit API Key' : 'New API Key'}
        </Typography>

        {newKey && (
          <Alert
            severity="success"
            sx={{ mb: 3 }}
            action={
              <IconButton aria-label="copy" color="inherit" size="small" onClick={handleCopyKey}>
                <ContentCopy fontSize="inherit" />
              </IconButton>
            }
          >
            <Typography variant="subtitle2">
              API Key created successfully. Please copy this key now as it won't be shown again:
            </Typography>
            <Box
              sx={{
                mt: 1,
                p: 1,
                bgcolor: 'background.paper',
                borderRadius: 1,
                fontFamily: 'monospace',
                wordBreak: 'break-all',
              }}
            >
              {newKey}
            </Box>
            {keyCopied && (
              <Typography variant="caption" color="success.main">
                Copied to clipboard!
              </Typography>
            )}
          </Alert>
        )}

        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              required
              fullWidth
              label="API Key Name"
              value={values.name || ''}
              onChange={handleChange('name')}
              error={!!errors.name}
              helperText={errors.name}
              disabled={loading || !!newKey}
              margin="normal"
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControl fullWidth margin="normal" error={!!errors.service}>
              <InputLabel>Service</InputLabel>
              <Select
                value={values.service || 'openai'}
                onChange={handleServiceChange}
                label="Service"
                disabled={loading || !!newKey}
              >
                <MenuItem value="openai">OpenAI</MenuItem>
                <MenuItem value="azure_openai">Azure OpenAI</MenuItem>
                <MenuItem value="huggingface">Hugging Face</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
              {errors.service && <FormHelperText>{errors.service}</FormHelperText>}
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label="Expiry Date (Optional)"
                value={expiryDate || null}
                onChange={handleExpiryDateChange}
                disabled={loading || !!newKey}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    margin: 'normal',
                  },
                }}
              />
            </LocalizationProvider>
          </Grid>

          {!initialValues?.id && (
            <Grid item xs={12}>
              <TextField
                fullWidth
                required
                label="API Key"
                type={showKey ? 'text' : 'password'}
                value={values.key || ''}
                onChange={handleChange('key')}
                error={!!errors.key}
                helperText={errors.key}
                disabled={loading || !!newKey}
                margin="normal"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle key visibility"
                        onClick={() => setShowKey(!showKey)}
                        edge="end"
                      >
                        {showKey ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
          )}

          {!newKey && (
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
          )}

          {newKey && (
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2, gap: 1 }}>
                <Button onClick={onCancel} variant="contained" color="primary">
                  Done
                </Button>
              </Box>
            </Grid>
          )}
        </Grid>
      </Box>
    </Paper>
  );
};

export default ApiKeyForm;
