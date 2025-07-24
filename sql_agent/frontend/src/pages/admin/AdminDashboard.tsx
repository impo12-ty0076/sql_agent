import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Grid,
  Container,
  Typography,
  Box,
  Divider,
  Button,
  Card,
  CardContent,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import PeopleIcon from '@mui/icons-material/People';
import QueryStatsIcon from '@mui/icons-material/QueryStats';
import SpeedIcon from '@mui/icons-material/Speed';
import ErrorIcon from '@mui/icons-material/Error';
import SecurityIcon from '@mui/icons-material/Security';
import ManageAccountsIcon from '@mui/icons-material/ManageAccounts';
import { RootState } from '../../store';
import {
  fetchSystemStats,
  fetchSystemStatus,
  fetchLogs,
  fetchUsageStats,
  fetchErrorStats,
  fetchPerformanceMetrics,
  setLogFilter,
  setUsageStatsPeriod,
  setErrorStatsPeriod,
  setPerformanceMetricsPeriod,
} from '../../store/slices/adminSlice';
import StatisticsCard from '../../components/admin/StatisticsCard';
import ChartCard from '../../components/admin/ChartCard';
import SystemStatusCard from '../../components/admin/SystemStatusCard';
import LogsTable from '../../components/admin/LogsTable';
import { LogFilter } from '../../services/adminService';

const AdminDashboard: React.FC = () => {
  const dispatch = useDispatch();
  const { stats, status, logs, usageStats, errorStats, performanceMetrics } = useSelector(
    (state: RootState) => state.admin
  );

  useEffect(() => {
    // Fetch initial data
    dispatch(fetchSystemStats() as any);
    dispatch(fetchSystemStatus() as any);
    dispatch(fetchLogs() as any);
    dispatch(fetchUsageStats(usageStats.period) as any);
    dispatch(fetchErrorStats(errorStats.period) as any);
    dispatch(fetchPerformanceMetrics(performanceMetrics.period) as any);

    // Set up refresh interval
    const refreshInterval = setInterval(() => {
      dispatch(fetchSystemStats() as any);
      dispatch(fetchSystemStatus() as any);
    }, 60000); // Refresh stats and status every minute

    return () => clearInterval(refreshInterval);
  }, [dispatch, usageStats.period, errorStats.period, performanceMetrics.period]);

  const handleLogFilterChange = (filter: LogFilter) => {
    dispatch(setLogFilter(filter));
    dispatch(fetchLogs(filter) as any);
  };

  const handleUsageStatsPeriodChange = (period: 'day' | 'week' | 'month') => {
    dispatch(setUsageStatsPeriod(period));
    dispatch(fetchUsageStats(period) as any);
  };

  const handleErrorStatsPeriodChange = (period: 'day' | 'week' | 'month') => {
    dispatch(setErrorStatsPeriod(period));
    dispatch(fetchErrorStats(period) as any);
  };

  const handlePerformanceMetricsPeriodChange = (period: 'day' | 'week' | 'month') => {
    dispatch(setPerformanceMetricsPeriod(period));
    dispatch(fetchPerformanceMetrics(period) as any);
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Admin Dashboard
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" paragraph>
        Monitor system performance, usage statistics, and logs
      </Typography>

      <Box mb={4}>
        <Typography variant="h5" gutterBottom>
          System Overview
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <StatisticsCard
              title="Total Users"
              value={stats.data?.totalUsers || 0}
              icon={<PeopleIcon />}
              loading={stats.loading}
              color="primary.main"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatisticsCard
              title="Active Users"
              value={stats.data?.activeUsers || 0}
              icon={<PeopleIcon />}
              loading={stats.loading}
              color="success.main"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatisticsCard
              title="Total Queries"
              value={stats.data?.totalQueries || 0}
              icon={<QueryStatsIcon />}
              loading={stats.loading}
              color="info.main"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatisticsCard
              title="Queries (Last 24h)"
              value={stats.data?.queriesLastDay || 0}
              icon={<QueryStatsIcon />}
              loading={stats.loading}
              color="secondary.main"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatisticsCard
              title="Avg Response Time"
              value={`${stats.data?.averageResponseTime || 0} ms`}
              icon={<SpeedIcon />}
              loading={stats.loading}
              color="warning.main"
              description="Average query response time in milliseconds"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatisticsCard
              title="Error Rate"
              value={`${stats.data?.errorRate || 0}%`}
              icon={<ErrorIcon />}
              loading={stats.loading}
              color="error.main"
              description="Percentage of queries that resulted in errors"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={6}>
            <SystemStatusCard status={status.data} loading={status.loading} error={status.error} />
          </Grid>
        </Grid>
      </Box>

      <Divider sx={{ my: 4 }} />

      <Box mb={4}>
        <Typography variant="h5" gutterBottom>
          Usage Analytics
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <ChartCard
              title="Query Usage"
              chartData={usageStats.data}
              loading={usageStats.loading}
              error={usageStats.error}
              chartType="line"
              period={usageStats.period}
              onPeriodChange={handleUsageStatsPeriodChange}
              height={300}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <ChartCard
              title="Error Distribution"
              chartData={errorStats.data}
              loading={errorStats.loading}
              error={errorStats.error}
              chartType="bar"
              period={errorStats.period}
              onPeriodChange={handleErrorStatsPeriodChange}
              height={300}
            />
          </Grid>
          <Grid item xs={12}>
            <ChartCard
              title="System Performance"
              chartData={performanceMetrics.data}
              loading={performanceMetrics.loading}
              error={performanceMetrics.error}
              chartType="line"
              period={performanceMetrics.period}
              onPeriodChange={handlePerformanceMetricsPeriodChange}
              height={300}
            />
          </Grid>
        </Grid>
      </Box>

      <Divider sx={{ my: 4 }} />

      <Box mb={4}>
        <Typography variant="h5" gutterBottom>
          Administration
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <ManageAccountsIcon fontSize="large" color="primary" sx={{ mr: 2 }} />
                  <Typography variant="h6">User Management</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Manage users, roles, and database access permissions. Control who can access the
                  system and what they can do.
                </Typography>
                <Button
                  variant="contained"
                  color="primary"
                  component={RouterLink}
                  to="/admin/users"
                  startIcon={<PeopleIcon />}
                >
                  Manage Users
                </Button>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <SecurityIcon fontSize="large" color="primary" sx={{ mr: 2 }} />
                  <Typography variant="h6">Policy Management</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Create and manage query limit policies. Set restrictions on query execution time,
                  result size, and allowed query types.
                </Typography>
                <Button
                  variant="contained"
                  color="primary"
                  component={RouterLink}
                  to="/admin/policies"
                  startIcon={<SecurityIcon />}
                >
                  Manage Policies
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      <Divider sx={{ my: 4 }} />

      <Box mb={4}>
        <Typography variant="h5" gutterBottom>
          System Logs
        </Typography>
        <LogsTable
          logs={logs.data}
          loading={logs.loading}
          error={logs.error}
          filter={logs.filter}
          onFilterChange={handleLogFilterChange}
        />
      </Box>
    </Container>
  );
};

export default AdminDashboard;
