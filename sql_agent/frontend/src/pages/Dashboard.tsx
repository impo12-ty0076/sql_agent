import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Tabs,
  Tab,
  Alert,
  Divider,
  Grid,
  Card,
  CardContent,
  Skeleton,
} from '@mui/material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../store';
import NaturalLanguageQueryInput from '../components/NaturalLanguageQueryInput';
import ResultTable from '../components/ResultTable';
import DatabaseSelector from '../components/DatabaseSelector';
import ConnectionStatus from '../components/ConnectionStatus';
import ReportToggle from '../components/ReportToggle';
import ReportProgress from '../components/ReportProgress';
import ReportVisualization from '../components/ReportVisualization';
import { dbService } from '../services/dbService';
import { reportService } from '../services/reportService';
import { SqlExecutionResult } from '../services/queryService';

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
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Dashboard: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const {
    selectedDatabase,
    loading: dbLoading,
    error: dbError,
  } = useSelector((state: RootState) => state.db);
  const { reportGenerationStatus } = useSelector((state: RootState) => state.report);
  const [tabValue, setTabValue] = useState(0);
  const [queryResult, setQueryResult] = useState<any>(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [queryError, setQueryError] = useState<string | null>(null);

  // Component mount - try to connect to last used database
  useEffect(() => {
    const lastConnectedDbId = localStorage.getItem('lastConnectedDbId');
    if (lastConnectedDbId && !selectedDatabase) {
      dispatch(dbService.connectToDatabase(lastConnectedDbId)).catch(() => {
        // Silently ignore connection failures on auto-connect
      });
    }
  }, [dispatch, selectedDatabase]);

  // Save last connected database to localStorage
  useEffect(() => {
    if (selectedDatabase?.connected) {
      localStorage.setItem('lastConnectedDbId', selectedDatabase.id);
    }
  }, [selectedDatabase]);

  const { reportGenerationEnabled, reportGenerationOptions } = useSelector(
    (state: RootState) => state.report
  );

  const handleQueryComplete = (result: SqlExecutionResult) => {
    if (!result) return;

    setQueryError(null);
    setQueryResult({
      columns: result.columns,
      rows: result.rows,
      rowCount: result.rowCount,
      page: 0,
      pageSize: 10,
      executionTime: result.executionTime,
      truncated: result.truncated,
      totalRowCount: result.totalRowCount,
    });

    // If report generation is enabled, generate a report
    if (reportGenerationEnabled && result.rowCount > 0) {
      dispatch(
        reportService.generateReport(
          result.resultId || 'temp-result-id', // In a real app, we'd have a proper resultId
          reportGenerationOptions.visualizationTypes,
          reportGenerationOptions.includeInsights
        )
      ).catch(error => {
        setQueryError(`리포트 생성 오류: ${error.message}`);
      });
    }
  };

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        SQL DB LLM Agent
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              대시보드
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              자연어로 데이터베이스에 질의하고 결과를 분석하세요. 시작하려면 먼저 데이터베이스를
              선택하고 연결하세요.
            </Typography>

            <Divider sx={{ my: 2 }} />

            <DatabaseSelector />
            <ConnectionStatus />
          </Paper>
        </Grid>

        <Grid item xs={12}>
          {dbError && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {dbError}
            </Alert>
          )}

          {queryError && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {queryError}
            </Alert>
          )}

          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              자연어 질의
            </Typography>
            <NaturalLanguageQueryInput
              onQueryComplete={handleQueryComplete}
              disabled={!selectedDatabase?.connected}
              placeholder={
                selectedDatabase?.connected
                  ? "자연어로 질문하세요 (예: '모든 사용자의 이름과 이메일을 보여줘')"
                  : '질의하려면 먼저 데이터베이스에 연결하세요'
              }
            />
          </Paper>
        </Grid>

        {dbLoading && !queryResult && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Skeleton variant="rectangular" height={40} sx={{ mb: 2 }} />
                <Skeleton variant="rectangular" height={200} />
              </CardContent>
            </Card>
          </Grid>
        )}

        {queryResult && (
          <Grid item xs={12}>
            <Paper sx={{ mb: 3 }}>
              <Tabs value={tabValue} onChange={handleTabChange} aria-label="result tabs">
                <Tab label="테이블" />
                <Tab label="요약" />
                <Tab label="리포트" />
              </Tabs>

              <TabPanel value={tabValue} index={0}>
                <ResultTable
                  columns={queryResult.columns}
                  rows={queryResult.rows}
                  rowCount={queryResult.rowCount}
                  page={page}
                  pageSize={pageSize}
                  onPageChange={setPage}
                  onPageSizeChange={setPageSize}
                />
              </TabPanel>

              <TabPanel value={tabValue} index={1}>
                <Typography variant="body1">
                  총 2명의 사용자가 조회되었습니다. 사용자 ID, 사용자명, 이메일 정보가 포함되어
                  있습니다.
                </Typography>
              </TabPanel>

              <TabPanel value={tabValue} index={2}>
                <ReportToggle />
                <ReportProgress />
                <ReportVisualization />
              </TabPanel>
            </Paper>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default Dashboard;
