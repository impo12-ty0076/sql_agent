import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Box, 
  Typography, 
  Paper, 
  Divider, 
  CircularProgress,
  Alert,
  Snackbar
} from '@mui/material';
import { AppDispatch, RootState } from '../store';
import { fetchQueryHistory } from '../services/historyService';
import { clearError } from '../store/slices/historySlice';
import HistoryFilters from '../components/history/HistoryFilters';
import HistoryList from '../components/history/HistoryList';
import HistoryDetail from '../components/history/HistoryDetail';

const QueryHistory: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { items, loading, error, filters, selectedItem } = useSelector((state: RootState) => state.history);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Fetch history on component mount and when filters change
  useEffect(() => {
    dispatch(fetchQueryHistory(filters));
  }, [dispatch, filters]);

  // Show error in snackbar if there is one
  useEffect(() => {
    if (error) {
      setSnackbarMessage(error);
      setSnackbarOpen(true);
    }
  }, [error]);

  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
    dispatch(clearError());
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        쿼리 이력 관리
      </Typography>
      
      <Box sx={{ mb: 2 }}>
        <HistoryFilters />
      </Box>
      
      <Divider sx={{ mb: 2 }} />
      
      <Box sx={{ display: 'flex', flexGrow: 1, gap: 2, height: 'calc(100% - 120px)' }}>
        <Paper 
          elevation={3} 
          sx={{ 
            width: '40%', 
            p: 2, 
            overflow: 'auto',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
              <CircularProgress />
            </Box>
          ) : (
            <HistoryList items={items} />
          )}
        </Paper>
        
        <Paper 
          elevation={3} 
          sx={{ 
            width: '60%', 
            p: 2, 
            overflow: 'auto' 
          }}
        >
          {selectedItem ? (
            <HistoryDetail item={selectedItem} />
          ) : (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
              <Typography variant="body1" color="text.secondary">
                이력 항목을 선택하여 상세 정보를 확인하세요
              </Typography>
            </Box>
          )}
        </Paper>
      </Box>
      
      <Snackbar 
        open={snackbarOpen} 
        autoHideDuration={6000} 
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleSnackbarClose} severity="error" sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default QueryHistory;