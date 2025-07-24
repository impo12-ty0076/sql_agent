import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  Grid,
  Divider,
  Chip,
  InputAdornment,
  IconButton,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import { Policy, PolicySettings } from '../../types/admin';

interface PolicyFormProps {
  policy?: Policy;
  onSave: (policy: Omit<Policy, 'id' | 'createdAt' | 'updatedAt' | 'appliedToUsers'>) => void;
  onCancel: () => void;
}

const defaultPolicySettings: PolicySettings = {
  maxQueriesPerDay: 100,
  maxQueryExecutionTime: 60,
  maxResultSize: 10000,
  allowedQueryTypes: ['SELECT'],
  blockedKeywords: [],
};

const PolicyForm: React.FC<PolicyFormProps> = ({ policy, onSave, onCancel }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [settings, setSettings] = useState<PolicySettings>(defaultPolicySettings);
  const [newKeyword, setNewKeyword] = useState('');
  const [newQueryType, setNewQueryType] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (policy) {
      setName(policy.name);
      setDescription(policy.description);
      setSettings(policy.settings);
    }
  }, [policy]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (settings.maxQueriesPerDay <= 0) {
      newErrors.maxQueriesPerDay = 'Must be greater than 0';
    }

    if (settings.maxQueryExecutionTime <= 0) {
      newErrors.maxQueryExecutionTime = 'Must be greater than 0';
    }

    if (settings.maxResultSize <= 0) {
      newErrors.maxResultSize = 'Must be greater than 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (!validate()) return;

    onSave({
      name,
      description,
      settings,
    });
  };

  const handleAddBlockedKeyword = () => {
    if (!newKeyword.trim()) return;
    setSettings({
      ...settings,
      blockedKeywords: [...settings.blockedKeywords, newKeyword.trim()],
    });
    setNewKeyword('');
  };

  const handleRemoveBlockedKeyword = (keyword: string) => {
    setSettings({
      ...settings,
      blockedKeywords: settings.blockedKeywords.filter(k => k !== keyword),
    });
  };

  const handleAddQueryType = () => {
    if (!newQueryType.trim()) return;
    setSettings({
      ...settings,
      allowedQueryTypes: [...settings.allowedQueryTypes, newQueryType.trim().toUpperCase()],
    });
    setNewQueryType('');
  };

  const handleRemoveQueryType = (queryType: string) => {
    setSettings({
      ...settings,
      allowedQueryTypes: settings.allowedQueryTypes.filter(t => t !== queryType),
    });
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {policy ? 'Edit Policy' : 'Create New Policy'}
      </Typography>
      <Divider sx={{ mb: 3 }} />

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Policy Name"
            value={name}
            onChange={e => setName(e.target.value)}
            error={!!errors.name}
            helperText={errors.name}
            required
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Description"
            value={description}
            onChange={e => setDescription(e.target.value)}
            error={!!errors.description}
            helperText={errors.description}
            multiline
            rows={2}
            required
          />
        </Grid>

        <Grid item xs={12}>
          <Typography variant="subtitle1" gutterBottom>
            Query Limits
          </Typography>
        </Grid>

        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            label="Max Queries Per Day"
            type="number"
            value={settings.maxQueriesPerDay}
            onChange={e =>
              setSettings({
                ...settings,
                maxQueriesPerDay: parseInt(e.target.value) || 0,
              })
            }
            error={!!errors.maxQueriesPerDay}
            helperText={errors.maxQueriesPerDay}
            InputProps={{
              inputProps: { min: 1 },
            }}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            label="Max Query Execution Time (seconds)"
            type="number"
            value={settings.maxQueryExecutionTime}
            onChange={e =>
              setSettings({
                ...settings,
                maxQueryExecutionTime: parseInt(e.target.value) || 0,
              })
            }
            error={!!errors.maxQueryExecutionTime}
            helperText={errors.maxQueryExecutionTime}
            InputProps={{
              inputProps: { min: 1 },
            }}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            label="Max Result Size (rows)"
            type="number"
            value={settings.maxResultSize}
            onChange={e =>
              setSettings({
                ...settings,
                maxResultSize: parseInt(e.target.value) || 0,
              })
            }
            error={!!errors.maxResultSize}
            helperText={errors.maxResultSize}
            InputProps={{
              inputProps: { min: 1 },
            }}
          />
        </Grid>

        <Grid item xs={12}>
          <Typography variant="subtitle1" gutterBottom>
            Allowed Query Types
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <TextField
              fullWidth
              label="Add Query Type"
              value={newQueryType}
              onChange={e => setNewQueryType(e.target.value)}
              placeholder="e.g., SELECT, SHOW"
              size="small"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={handleAddQueryType} edge="end">
                      <AddIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {settings.allowedQueryTypes.map(queryType => (
              <Chip
                key={queryType}
                label={queryType}
                onDelete={() => handleRemoveQueryType(queryType)}
                color="primary"
              />
            ))}
            {settings.allowedQueryTypes.length === 0 && (
              <Typography variant="body2" color="text.secondary">
                No query types allowed
              </Typography>
            )}
          </Box>
        </Grid>

        <Grid item xs={12}>
          <Typography variant="subtitle1" gutterBottom>
            Blocked Keywords
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <TextField
              fullWidth
              label="Add Blocked Keyword"
              value={newKeyword}
              onChange={e => setNewKeyword(e.target.value)}
              placeholder="e.g., DROP, DELETE"
              size="small"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={handleAddBlockedKeyword} edge="end">
                      <AddIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {settings.blockedKeywords.map(keyword => (
              <Chip
                key={keyword}
                label={keyword}
                onDelete={() => handleRemoveBlockedKeyword(keyword)}
                color="error"
              />
            ))}
            {settings.blockedKeywords.length === 0 && (
              <Typography variant="body2" color="text.secondary">
                No blocked keywords
              </Typography>
            )}
          </Box>
        </Grid>
      </Grid>

      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
        <Button variant="outlined" onClick={onCancel}>
          Cancel
        </Button>
        <Button variant="contained" color="primary" onClick={handleSave}>
          {policy ? 'Update Policy' : 'Create Policy'}
        </Button>
      </Box>
    </Paper>
  );
};

export default PolicyForm;
