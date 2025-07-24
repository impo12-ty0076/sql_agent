import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Container, Typography, Box, Button, Alert, CircularProgress } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { RootState } from '../../store';
import {
  fetchPolicyById,
  createPolicy,
  updatePolicy,
  clearSelectedPolicy,
} from '../../store/slices/adminSlice';
import PolicyForm from '../../components/admin/PolicyForm';
import { Policy } from '../../types/admin';

const PolicyDetail: React.FC = () => {
  const { policyId } = useParams<{ policyId: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { selectedPolicy, loading } = useSelector((state: RootState) => state.admin.policies);
  const [successMessage, setSuccessMessage] = useState('');
  const isNewPolicy = policyId === 'new';

  useEffect(() => {
    if (!isNewPolicy && policyId) {
      dispatch(fetchPolicyById(policyId) as any);
    }

    return () => {
      dispatch(clearSelectedPolicy());
    };
  }, [dispatch, policyId, isNewPolicy]);

  const handleSave = async (
    policy: Omit<Policy, 'id' | 'createdAt' | 'updatedAt' | 'appliedToUsers'>
  ) => {
    try {
      if (isNewPolicy) {
        await dispatch(createPolicy(policy) as any);
        setSuccessMessage('Policy created successfully');
      } else if (selectedPolicy) {
        await dispatch(updatePolicy({ policyId: selectedPolicy.id, policy }) as any);
        setSuccessMessage('Policy updated successfully');
      }

      // Navigate back after a short delay to show the success message
      setTimeout(() => {
        navigate('/admin/policies');
      }, 1500);
    } catch (error) {
      console.error('Error saving policy:', error);
    }
  };

  const handleCancel = () => {
    navigate('/admin/policies');
  };

  const handleBack = () => {
    navigate('/admin/policies');
  };

  if (!isNewPolicy && loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (!isNewPolicy && !selectedPolicy) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">Policy not found</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mt: 2 }}>
          Back to Policies
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" alignItems="center" mb={2}>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack}>
          Back to Policies
        </Button>
      </Box>

      <Typography variant="h4" gutterBottom>
        {isNewPolicy ? 'Create New Policy' : 'Edit Policy'}
      </Typography>

      {successMessage && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {successMessage}
        </Alert>
      )}

      <PolicyForm
        policy={isNewPolicy ? undefined : selectedPolicy || undefined}
        onSave={handleSave}
        onCancel={handleCancel}
      />
    </Container>
  );
};

export default PolicyDetail;
