import React, { useEffect, useState } from 'react';
import { 
  Box, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Button, 
  Typography, 
  CircularProgress,
  SelectChangeEvent,
  Alert,
  Snackbar
} from '@mui/material';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../store';
import { Database } from '../store/slices/dbSlice';
import { dbService } from '../services/dbService';

const DatabaseSelector: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { databases, selectedDatabase, loading, error } = useSelector((state: RootState) => state.db);
  const [selectedDbId, setSelectedDbId] = useState<string>('');
  const [connecting, setConnecting] = useState<boolean>(false);
  const [openSnackbar, setOpenSnackbar] = useState<boolean>(false);
  const [snackbarMessage, setSnackbarMessage] = useState<string>('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');

  // 컴포넌트 마운트 시 데이터베이스 목록 조회
  useEffect(() => {
    if (databases.length === 0 && !loading) {
      dispatch(dbService.fetchDatabases());
    }
  }, [dispatch, databases.length, loading]);

  // 선택된 데이터베이스가 있으면 선택 상태 업데이트
  useEffect(() => {
    if (selectedDatabase) {
      setSelectedDbId(selectedDatabase.id);
    }
  }, [selectedDatabase]);

  const handleDatabaseChange = (event: SelectChangeEvent<string>) => {
    setSelectedDbId(event.target.value);
  };

  const handleConnect = async () => {
    if (!selectedDbId) return;

    try {
      setConnecting(true);
      await dispatch(dbService.connectToDatabase(selectedDbId));
      setSnackbarMessage('데이터베이스에 성공적으로 연결되었습니다.');
      setSnackbarSeverity('success');
      setOpenSnackbar(true);
    } catch (error: any) {
      setSnackbarMessage(error.message || '데이터베이스 연결에 실패했습니다.');
      setSnackbarSeverity('error');
      setOpenSnackbar(true);
    } finally {
      setConnecting(false);
    }
  };

  const handleCloseSnackbar = () => {
    setOpenSnackbar(false);
  };

  // 이미 연결된 데이터베이스 선택
  const handleSelectExisting = (database: Database) => {
    dispatch(dbService.selectExistingDatabase(database));
  };

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h6" gutterBottom>
        데이터베이스 선택
      </Typography>
      
      {loading && !connecting && (
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <CircularProgress size={24} sx={{ mr: 2 }} />
          <Typography>데이터베이스 목록을 불러오는 중...</Typography>
        </Box>
      )}
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 2 }}>
        <FormControl fullWidth>
          <InputLabel id="database-select-label">데이터베이스</InputLabel>
          <Select
            labelId="database-select-label"
            id="database-select"
            value={selectedDbId}
            label="데이터베이스"
            onChange={handleDatabaseChange}
            disabled={loading || connecting}
          >
            {databases.map((db) => (
              <MenuItem 
                key={db.id} 
                value={db.id}
                onClick={() => db.connected && handleSelectExisting(db)}
              >
                {db.name} ({db.type}) {db.connected && '- 연결됨'}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        
        <Button 
          variant="contained" 
          onClick={handleConnect}
          disabled={!selectedDbId || loading || connecting || (selectedDatabase?.id === selectedDbId && selectedDatabase?.connected)}
        >
          {connecting ? <CircularProgress size={24} /> : '연결'}
        </Button>
      </Box>
      
      <Snackbar
        open={openSnackbar}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default DatabaseSelector;