import React, { useState } from 'react';
import {
  TextField,
  Button,
  Box,
  Typography,
  Paper,
  CircularProgress,
  FormControlLabel,
  Switch,
  Collapse,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { queryService, NaturalLanguageQueryResult } from '../services/queryService';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import EditIcon from '@mui/icons-material/Edit';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';

interface NaturalLanguageQueryInputProps {
  onQueryComplete: (result: any) => void;
  disabled?: boolean;
  placeholder?: string;
}

const NaturalLanguageQueryInput: React.FC<NaturalLanguageQueryInputProps> = ({
  onQueryComplete,
  disabled = false,
  placeholder = '예: 지난 달 매출이 가장 높은 상품 5개를 보여줘',
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const { loading } = useSelector((state: RootState) => state.query);
  const { selectedDatabase } = useSelector((state: RootState) => state.db);

  const [query, setQuery] = useState('');
  const [useRag, setUseRag] = useState(false);
  const [sqlResult, setSqlResult] = useState<NaturalLanguageQueryResult | null>(null);
  const [editingSql, setEditingSql] = useState(false);
  const [modifiedSql, setModifiedSql] = useState('');
  const [processingStep, setProcessingStep] = useState<'input' | 'review' | 'executing'>('input');
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !selectedDatabase?.id) return;

    setError(null);
    setProcessingStep('review');

    try {
      const result = await dispatch(
        queryService.processNaturalLanguage(selectedDatabase.id, query, useRag)
      );
      setSqlResult(result);
      setModifiedSql(result.generatedSql);
    } catch (err: any) {
      setError(err.message || '자연어 처리 중 오류가 발생했습니다.');
      setProcessingStep('input');
    }
  };

  const handleExecuteSql = async () => {
    if (!selectedDatabase?.id || !modifiedSql.trim()) return;

    setError(null);
    setProcessingStep('executing');

    try {
      const result = await dispatch(queryService.executeQuery(selectedDatabase.id, modifiedSql));
      onQueryComplete(result);
      // Reset to initial state for next query
      setProcessingStep('input');
    } catch (err: any) {
      setError(err.message || 'SQL 실행 중 오류가 발생했습니다.');
      setProcessingStep('review'); // Go back to review step on error
    }
  };

  const handleCopySql = () => {
    navigator.clipboard.writeText(modifiedSql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRagToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    setUseRag(event.target.checked);
  };

  const renderInputStep = () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <TextField
        label="자연어 질의 입력"
        multiline
        rows={3}
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder={placeholder}
        fullWidth
        variant="outlined"
        disabled={disabled || loading}
        helperText={disabled ? '데이터베이스에 연결한 후 질의할 수 있습니다.' : ''}
      />

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <FormControlLabel
          control={
            <Switch checked={useRag} onChange={handleRagToggle} name="ragToggle" color="primary" />
          }
          label={
            <Tooltip title="RAG 시스템은 키워드 기반 검색을 통해 관련 데이터를 검색하고 결과를 제공합니다.">
              <Typography variant="body2">RAG 시스템 사용</Typography>
            </Tooltip>
          }
        />

        <Button
          type="submit"
          variant="contained"
          color="primary"
          disabled={loading || !query.trim() || disabled}
          onClick={handleSubmit}
          startIcon={loading ? <CircularProgress size={20} /> : undefined}
        >
          {loading ? '처리 중...' : '질의하기'}
        </Button>
      </Box>
    </Box>
  );

  const renderReviewStep = () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Typography variant="subtitle1" gutterBottom>
        자연어 질의:
      </Typography>
      <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
        <Typography variant="body1">{query}</Typography>
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
        <Typography variant="subtitle1">생성된 SQL:</Typography>
        <Box>
          <Tooltip title="SQL 편집">
            <IconButton
              size="small"
              onClick={() => setEditingSql(!editingSql)}
              color={editingSql ? 'primary' : 'default'}
            >
              <EditIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title={copied ? '복사됨!' : 'SQL 복사'}>
            <IconButton size="small" onClick={handleCopySql}>
              {copied ? <CheckCircleOutlineIcon color="success" /> : <ContentCopyIcon />}
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {editingSql ? (
        <TextField
          multiline
          rows={5}
          value={modifiedSql}
          onChange={e => setModifiedSql(e.target.value)}
          fullWidth
          variant="outlined"
          sx={{ fontFamily: 'monospace' }}
        />
      ) : (
        <Paper
          variant="outlined"
          sx={{ p: 2, bgcolor: 'background.default', fontFamily: 'monospace', overflowX: 'auto' }}
        >
          <pre style={{ margin: 0 }}>{modifiedSql}</pre>
        </Paper>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
        <Button
          variant="outlined"
          onClick={() => {
            setProcessingStep('input');
            setSqlResult(null);
          }}
        >
          뒤로
        </Button>

        <Button
          variant="contained"
          color="primary"
          onClick={handleExecuteSql}
          startIcon={<PlayArrowIcon />}
          disabled={!modifiedSql.trim()}
        >
          SQL 실행
        </Button>
      </Box>
    </Box>
  );

  return (
    <form onSubmit={handleSubmit}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {processingStep === 'input' && renderInputStep()}
      {processingStep === 'review' && renderReviewStep()}
      {processingStep === 'executing' && (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
          <CircularProgress />
          <Typography variant="body1" sx={{ mt: 2 }}>
            SQL 쿼리 실행 중...
          </Typography>
        </Box>
      )}
    </form>
  );
};

export default NaturalLanguageQueryInput;
