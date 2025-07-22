import React, { useState } from 'react';
import { TextField, Button, Box, Typography, Paper } from '@mui/material';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

const QueryInput: React.FC<QueryInputProps> = ({ onSubmit, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSubmit(query);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        자연어로 질의하기
      </Typography>
      <form onSubmit={handleSubmit}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            label="질의 입력"
            multiline
            rows={3}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="예: 지난 달 매출이 가장 높은 상품 5개를 보여줘"
            fullWidth
            variant="outlined"
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={isLoading || !query.trim()}
          >
            {isLoading ? '처리 중...' : '질의하기'}
          </Button>
        </Box>
      </form>
    </Paper>
  );
};

export default QueryInput;