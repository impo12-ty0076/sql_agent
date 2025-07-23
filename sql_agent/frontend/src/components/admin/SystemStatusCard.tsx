import React from 'react';
import { Card, CardContent, Typography, Box, CircularProgress, Chip, Grid } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import { SystemStatus } from '../../services/adminService';

interface SystemStatusCardProps {
  status: SystemStatus | null;
  loading: boolean;
  error: string | null;
}

const SystemStatusCard: React.FC<SystemStatusCardProps> = ({ status, loading, error }) => {
  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / (3600 * 24));
    const hours = Math.floor((seconds % (3600 * 24)) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    return `${days}d ${hours}h ${minutes}m`;
  };

  const getStatusIcon = (status: 'healthy' | 'degraded' | 'down'): React.ReactElement => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon sx={{ color: 'success.main' }} />;
      case 'degraded':
        return <WarningIcon sx={{ color: 'warning.main' }} />;
      case 'down':
        return <ErrorIcon sx={{ color: 'error.main' }} />;
      default:
        return <InfoIcon sx={{ color: 'info.main' }} />; // Default icon to ensure we always return a ReactElement
    }
  };

  const getStatusColor = (status: 'healthy' | 'degraded' | 'down') => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'down':
        return 'error';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" height={150}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Typography variant="h6">System Status</Typography>
          <Box display="flex" justifyContent="center" alignItems="center" height={150}>
            <Typography color="error">{error}</Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!status) {
    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Typography variant="h6">System Status</Typography>
          <Box display="flex" justifyContent="center" alignItems="center" height={150}>
            <Typography color="text.secondary">No status data available</Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">System Status</Typography>
          <Chip
            icon={getStatusIcon(status.status)}
            label={status.status.toUpperCase()}
            color={getStatusColor(status.status) as any}
            size="small"
          />
        </Box>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" color="text.secondary">
              Uptime
            </Typography>
            <Typography variant="body1">{formatUptime(status.uptime)}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" color="text.secondary">
              Last Checked
            </Typography>
            <Typography variant="body1">
              {new Date(status.lastChecked).toLocaleString()}
            </Typography>
          </Grid>
        </Grid>
        
        <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2, mb: 1 }}>
          Component Status
        </Typography>
        
        <Grid container spacing={1}>
          {Object.entries(status.components).map(([component, componentStatus]) => (
            <Grid item xs={6} sm={3} key={component}>
              <Box display="flex" alignItems="center">
                {getStatusIcon(componentStatus)}
                <Typography variant="body2" sx={{ ml: 1 }}>
                  {component.charAt(0).toUpperCase() + component.slice(1)}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default SystemStatusCard;