import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
  Container,
  Typography,
  Box,
  Divider,
  Paper,
  Grid,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { RootState } from '../../store';
import {
  fetchUserById,
  updateUserStatus,
  updateUserRole,
  updateUserPermissions,
  fetchDatabases,
  clearSelectedUser,
} from '../../store/slices/adminSlice';
import UserPermissionsForm from '../../components/admin/UserPermissionsForm';
import { UserPermissions } from '../../types/admin';

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
      id={`user-tabpanel-${index}`}
      aria-labelledby={`user-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const UserDetail: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { selectedUser, loading: userLoading } = useSelector((state: RootState) => state.admin.users);
  const { data: databases, loading: dbLoading } = useSelector((state: RootState) => state.admin.databases);
  const [tabValue, setTabValue] = useState(0);
  const [statusUpdating, setStatusUpdating] = useState(false);
  const [roleUpdating, setRoleUpdating] = useState(false);
  const [permissionsUpdating, setPermissionsUpdating] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (userId) {
      dispatch(fetchUserById(userId) as any);
      dispatch(fetchDatabases() as any);
    }

    return () => {
      dispatch(clearSelectedUser());
    };
  }, [dispatch, userId]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleStatusChange = async (event: React.ChangeEvent<{ value: unknown }>) => {
    if (!selectedUser) return;
    
    const newStatus = event.target.value as 'active' | 'inactive' | 'suspended';
    setStatusUpdating(true);
    try {
      await dispatch(updateUserStatus({ userId: selectedUser.id, status: newStatus }) as any);
      setSuccessMessage('User status updated successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
    } finally {
      setStatusUpdating(false);
    }
  };

  const handleRoleChange = async (event: React.ChangeEvent<{ value: unknown }>) => {
    if (!selectedUser) return;
    
    const newRole = event.target.value as 'user' | 'admin';
    setRoleUpdating(true);
    try {
      await dispatch(updateUserRole({ userId: selectedUser.id, role: newRole }) as any);
      setSuccessMessage('User role updated successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
    } finally {
      setRoleUpdating(false);
    }
  };

  const handlePermissionsUpdate = async (permissions: UserPermissions) => {
    if (!selectedUser) return;
    
    setPermissionsUpdating(true);
    try {
      await dispatch(updateUserPermissions({ userId: selectedUser.id, permissions }) as any);
      setSuccessMessage('User permissions updated successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
    } finally {
      setPermissionsUpdating(false);
    }
  };

  const handleBack = () => {
    navigate('/admin/users');
  };

  if (userLoading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (!selectedUser) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">User not found</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mt: 2 }}>
          Back to Users
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" alignItems="center" mb={2}>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack}>
          Back to Users
        </Button>
      </Box>

      <Typography variant="h4" gutterBottom>
        User Details
      </Typography>

      {successMessage && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {successMessage}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="text.secondary">
              Username
            </Typography>
            <Typography variant="body1">{selectedUser.username}</Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="text.secondary">
              Email
            </Typography>
            <Typography variant="body1">{selectedUser.email}</Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="subtitle2" color="text.secondary">
              Created At
            </Typography>
            <Typography variant="body1">
              {new Date(selectedUser.createdAt).toLocaleString()}
            </Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="subtitle2" color="text.secondary">
              Last Login
            </Typography>
            <Typography variant="body1">
              {new Date(selectedUser.lastLogin).toLocaleString()}
            </Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={selectedUser.status}
                label="Status"
                onChange={handleStatusChange as any}
                disabled={statusUpdating}
              >
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
                <MenuItem value="suspended">Suspended</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Role</InputLabel>
              <Select
                value={selectedUser.role}
                label="Role"
                onChange={handleRoleChange as any}
                disabled={roleUpdating}
              >
                <MenuItem value="user">User</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="user management tabs">
          <Tab label="Permissions" />
          <Tab label="Activity" />
          <Tab label="Policies" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <UserPermissionsForm
          permissions={selectedUser.permissions}
          databases={databases}
          loading={dbLoading}
          onSave={handlePermissionsUpdate}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            User Activity
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Activity tracking will be implemented in a future update.
          </Typography>
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Applied Policies
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Policy assignment will be implemented in a future update.
          </Typography>
        </Paper>
      </TabPanel>
    </Container>
  );
};

export default UserDetail;