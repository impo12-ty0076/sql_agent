import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Divider,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Snackbar,
} from '@mui/material';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import api from '../../services/api';
import { QueryDetailsResponse } from '../../types/api';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DownloadIcon from '@mui/icons-material/Download';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../store';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`shared-query-tabpanel-${index}`}
      aria-labelledby={`shared-query-tab-${index}`}
      {...other}
      style={{ height: 'calc(100% - 48px)', overflow: 'auto' }}
    >
      {value === index && <Box sx={{ p: 2, height: '100%' }}>{children}</Box>}
    </div>
  );
}

interface SharedQueryViewProps {
  shareId: string;
  token: string;
}

interface QueryResult {
  columns: { name: string; type: string }[];
  rows: any[][];
  rowCount: number;
  totalRowCount?: number;
  summary?: string;
}

const SharedQueryView: React.FC<SharedQueryViewProps> = ({ shareId, token }) => {
  const dispatch = useDispatch<AppDispatch>();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [queryDetails, setQueryDetails] = useState<QueryDetailsResponse | null>(null);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [shareDetails, setShareDetails] = useState<{
    created_by: string;
    created_at: string;
    expires_at?: string;
  } | null>(null);

  useEffect(() => {
    const fetchSharedQuery = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get<{
          query_details: QueryDetailsResponse;
          share_details: {
            created_by: string;
            created_at: string;
            expires_at?: string;
          };
        }>(`/api/query-history/shared/${shareId}?token=${token}`);

        setQueryDetails(response.data.query_details);
        setShareDetails(response.data.share_details);

        // Fetch query result if available
        if (response.data.query_details.result) {
          try {
            const resultResponse = await api.get<QueryResult>(
              `/api/query-history/shared/${shareId}/result?token=${token}&page=${
                page + 1
              }&page_size=${rowsPerPage}`
            );
            setQueryResult(resultResponse.data);
          } catch (resultErr) {
            console.error('Failed to fetch result data:', resultErr);
          }
        }
      } catch (err: any) {
        setError(err.response?.data?.message || '공유된 쿼리를 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchSharedQuery();
  }, [shareId, token, page, rowsPerPage]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleCopySQL = () => {
    if (queryDetails?.generated_sql) {
      navigator.clipboard.writeText(queryDetails.generated_sql);
      showSnackbar('SQL이 클립보드에 복사되었습니다.');
    }
  };

  const handleCloneQuery = async () => {
    if (!queryDetails) return;

    try {
      await api.post('/api/query-history/clone', {
        query_id: queryDetails.id,
      });
      showSnackbar('쿼리가 내 이력에 복제되었습니다.');
    } catch (err) {
      console.error('Failed to clone query:', err);
      showSnackbar('쿼리 복제에 실패했습니다.');
    }
  };

  const handleDownloadResults = () => {
    if (!queryResult) return;

    try {
      // Create CSV content
      const headers = queryResult.columns.map(col => col.name).join(',');
      const rows = queryResult.rows.map(row => row.join(',')).join('\n');
      const csvContent = `${headers}\n${rows}`;

      // Create download link
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.setAttribute('hidden', '');
      a.setAttribute('href', url);
      a.setAttribute('download', `query-result-${new Date().getTime()}.csv`);
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      showSnackbar('결과가 CSV 파일로 다운로드되었습니다.');
    } catch (err) {
      console.error('Failed to download results:', err);
      showSnackbar('결과 다운로드에 실패했습니다.');
    }
  };

  const showSnackbar = (message: string) => {
    setSnackbarMessage(message);
    setSnackbarOpen(true);
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

  if (loading) {
    return (
      <Box
        sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          p: 3,
        }}
      >
        <Alert severity="error" sx={{ width: '100%', maxWidth: 600 }}>
          {error}
        </Alert>
      </Box>
    );
  }

  if (!queryDetails || !shareDetails) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          p: 3,
        }}
      >
        <Alert severity="warning" sx={{ width: '100%', maxWidth: 600 }}>
          공유된 쿼리 정보를 찾을 수 없습니다.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          공유된 쿼리
        </Typography>

        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary">
            공유자: {shareDetails.created_by}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            공유일:{' '}
            {format(new Date(shareDetails.created_at), 'yyyy년 MM월 dd일 HH:mm:ss', { locale: ko })}
          </Typography>
          {shareDetails.expires_at && (
            <Typography variant="body2" color="text.secondary">
              만료일:{' '}
              {format(new Date(shareDetails.expires_at), 'yyyy년 MM월 dd일 HH:mm:ss', {
                locale: ko,
              })}
            </Typography>
          )}
        </Box>

        <Divider sx={{ mb: 3 }} />

        <Box sx={{ height: 'calc(100vh - 300px)', display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="shared query tabs">
              <Tab
                label="자연어 질의"
                id="shared-query-tab-0"
                aria-controls="shared-query-tabpanel-0"
              />
              <Tab label="SQL" id="shared-query-tab-1" aria-controls="shared-query-tabpanel-1" />
              <Tab label="결과" id="shared-query-tab-2" aria-controls="shared-query-tabpanel-2" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            {queryDetails.natural_language ? (
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {queryDetails.natural_language}
              </Typography>
            ) : (
              <Typography variant="body2" color="text.secondary">
                자연어 질의 정보가 없습니다
              </Typography>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            {queryDetails.generated_sql ? (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
                  <Button startIcon={<ContentCopyIcon />} size="small" onClick={handleCopySQL}>
                    SQL 복사
                  </Button>
                </Box>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    bgcolor: 'grey.100',
                    fontFamily: 'monospace',
                    whiteSpace: 'pre-wrap',
                    overflowX: 'auto',
                  }}
                >
                  {queryDetails.generated_sql}
                </Paper>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                SQL 정보가 없습니다
              </Typography>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            {queryResult ? (
              <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  {queryResult.summary && (
                    <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                      {queryResult.summary}
                    </Typography>
                  )}
                  <Button startIcon={<DownloadIcon />} size="small" onClick={handleDownloadResults}>
                    CSV 다운로드
                  </Button>
                </Box>

                <TableContainer
                  component={Paper}
                  variant="outlined"
                  sx={{ flexGrow: 1, overflow: 'auto' }}
                >
                  <Table stickyHeader size="small">
                    <TableHead>
                      <TableRow>
                        {queryResult.columns.map((column, index) => (
                          <TableCell key={index}>
                            <Typography variant="subtitle2">{column.name}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {column.type}
                            </Typography>
                          </TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {queryResult.rows.map((row, rowIndex) => (
                        <TableRow key={rowIndex} hover>
                          {row.map((cell, cellIndex) => (
                            <TableCell key={cellIndex}>
                              {cell !== null ? String(cell) : <em>null</em>}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                <TablePagination
                  rowsPerPageOptions={[10, 25, 50, 100]}
                  component="div"
                  count={queryResult.totalRowCount || queryResult.rowCount}
                  rowsPerPage={rowsPerPage}
                  page={page}
                  onPageChange={handleChangePage}
                  onRowsPerPageChange={handleChangeRowsPerPage}
                  labelRowsPerPage="행 수:"
                />
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                결과 정보가 없습니다
              </Typography>
            )}
          </TabPanel>
        </Box>

        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
          <Button variant="outlined" onClick={() => window.history.back()}>
            뒤로 가기
          </Button>

          <Button variant="contained" color="primary" onClick={handleCloneQuery}>
            내 쿼리로 복제
          </Button>
        </Box>
      </Paper>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        message={snackbarMessage}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      />
    </Box>
  );
};

export default SharedQueryView;
