import React, { useState } from 'react';
import { TextField, Button, Box, Typography, Paper } from '@mui/material';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  placeholder?: string;
}

const QueryInput: React.FC<QueryInputProps> = ({
  onSubmit,
  isLoading,
  disabled = false,
  placeholder = '예: 지난 달 매출이 가장 높은 상품 5개를 보여줘',
}) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSubmit(query);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField
          label="질의 입력"
          multiline
          rows={3}
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder={placeholder}
          fullWidth
          variant="outlined"
          disabled={disabled}
          helperText={disabled ? '데이터베이스에 연결한 후 질의할 수 있습니다.' : ''}
        />
        <Button
          type="submit"
          variant="contained"
          color="primary"
          disabled={isLoading || !query.trim() || disabled}
        >
          {isLoading ? '처리 중...' : '질의하기'}
        </Button>
      </Box>
    </form>
  );
};

export default QueryInput;
