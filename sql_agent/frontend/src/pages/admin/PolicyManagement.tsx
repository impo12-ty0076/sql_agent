import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Container,
  Typography,
  Box,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
} from '@mui/material';
import { RootState } from '../../store';
import { fetchPolicies, setPolicyFilter, deletePolicy } from '../../store/slices/adminSlice';
import PolicyTable from '../../components/admin/PolicyTable';
import { PolicyFilter } from '../../types/admin';

const PolicyManagement: React.FC = () => {
  const dispatch = useDispatch();
  const {
    data: policies,
    loading,
    filter,
  } = useSelector((state: RootState) => state.admin.policies);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [policyToDelete, setPolicyToDelete] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    dispatch(fetchPolicies(filter) as any);
  }, [dispatch, filter]);

  const handleFilterChange = (newFilter: PolicyFilter) => {
    dispatch(setPolicyFilter(newFilter));
  };

  const handleDeleteClick = (policyId: string) => {
    setPolicyToDelete(policyId);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (policyToDelete) {
      await dispatch(deletePolicy(policyToDelete) as any);
      setSuccessMessage('Policy deleted successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
    }
    setDeleteDialogOpen(false);
    setPolicyToDelete(null);
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setPolicyToDelete(null);
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Policy Management
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" paragraph>
        Manage query limit policies and restrictions
      </Typography>

      {successMessage && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {successMessage}
        </Alert>
      )}

      <Divider sx={{ my: 3 }} />

      <Box mb={4}>
        <PolicyTable
          policies={policies}
          loading={loading}
          filter={filter}
          onFilterChange={handleFilterChange}
          onDeletePolicy={handleDeleteClick}
        />
      </Box>

      <Dialog open={deleteDialogOpen} onClose={handleDeleteCancel}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          Are you sure you want to delete this policy? This action cannot be undone.
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default PolicyManagement;
