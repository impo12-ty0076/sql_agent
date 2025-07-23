import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Container, Typography, Box, Divider } from '@mui/material';
import { RootState } from '../../store';
import { fetchUsers, setUserFilter } from '../../store/slices/adminSlice';
import UserTable from '../../components/admin/UserTable';
import { UserFilter } from '../../types/admin';

const UserManagement: React.FC = () => {
  const dispatch = useDispatch();
  const { data: users, loading, filter } = useSelector((state: RootState) => state.admin.users);

  useEffect(() => {
    dispatch(fetchUsers(filter) as any);
  }, [dispatch, filter]);

  const handleFilterChange = (newFilter: UserFilter) => {
    dispatch(setUserFilter(newFilter));
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        User Management
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" paragraph>
        Manage users, roles, and permissions
      </Typography>

      <Divider sx={{ my: 3 }} />

      <Box mb={4}>
        <UserTable
          users={users}
          loading={loading}
          filter={filter}
          onFilterChange={handleFilterChange}
        />
      </Box>
    </Container>
  );
};

export default UserManagement;