import React from 'react';
import { Box, Typography, LinearProgress, Paper, CircularProgress } from '@mui/material';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

const ReportProgress: React.FC = () => {
  const { reportGenerationStatus } = useSelector((state: RootState) => state.report);
  const { isGenerating, progress, statusMessage } = reportGenerationStatus;

  if (!isGenerating) {
    return null;
  }

  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <CircularProgress size={24} sx={{ mr: 2 }} />
        <Typography variant="h6">리포트 생성 중</Typography>
      </Box>

      <Typography variant="body2" color="text.secondary" gutterBottom>
        {statusMessage}
      </Typography>

      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{ height: 8, borderRadius: 4 }}
        />
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {progress}%
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
};

export default ReportProgress;
