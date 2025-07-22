import React, { useState } from 'react';
import { Container, Typography, Box, Paper, Tabs, Tab } from '@mui/material';
import QueryInput from '../components/QueryInput';
import ResultTable from '../components/ResultTable';

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
  const [isLoading, setIsLoading] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [queryResult, setQueryResult] = useState<any>(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const handleQuerySubmit = (query: string) => {
    setIsLoading(true);
    
    // 실제 구현에서는 API 호출
    setTimeout(() => {
      setQueryResult({
        columns: [
          { name: 'id', type: 'int' },
          { name: 'username', type: 'varchar' },
          { name: 'email', type: 'varchar' },
        ],
        rows: [
          [1, 'user1', 'user1@example.com'],
          [2, 'user2', 'user2@example.com'],
        ],
        rowCount: 2,
        page: 0,
        pageSize: 10,
      });
      setIsLoading(false);
    }, 1000);
  };

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        SQL DB LLM Agent
      </Typography>
      
      <QueryInput onSubmit={handleQuerySubmit} isLoading={isLoading} />
      
      {queryResult && (
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
              총 2명의 사용자가 조회되었습니다. 사용자 ID, 사용자명, 이메일 정보가 포함되어 있습니다.
            </Typography>
          </TabPanel>
          
          <TabPanel value={tabValue} index={2}>
            <Typography variant="body1">
              리포트 생성 기능은 아직 구현되지 않았습니다.
            </Typography>
          </TabPanel>
        </Paper>
      )}
    </Container>
  );
};

export default Dashboard;