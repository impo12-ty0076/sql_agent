import React, { useState } from 'react';
import { Box, Typography, Paper, Button } from '@mui/material';
import EnhancedResultTable from '../EnhancedResultTable';

// Sample data
const sampleColumns = [
  { name: 'ID', type: 'number' },
  { name: '이름', type: 'string' },
  { name: '이메일', type: 'string' },
  { name: '부서', type: 'string' },
  { name: '직급', type: 'string' },
  { name: '입사일', type: 'date' },
  { name: '급여', type: 'number' },
  { name: '설명', type: 'text' },
];

const generateSampleData = (count: number) => {
  const departments = ['개발팀', '마케팅팀', '영업팀', '인사팀', '재무팀'];
  const positions = ['사원', '대리', '과장', '차장', '부장'];

  return Array(count)
    .fill(null)
    .map((_, i) => [
      i + 1,
      `사용자 ${i + 1}`,
      `user${i + 1}@example.com`,
      departments[i % departments.length],
      positions[i % positions.length],
      `${2020 - (i % 10)}-${String((i % 12) + 1).padStart(2, '0')}-${String((i % 28) + 1).padStart(
        2,
        '0'
      )}`,
      50000000 + i * 1000000,
      `이 사용자는 ${departments[i % departments.length]}의 ${
        positions[i % positions.length]
      }이며, 다양한 프로젝트에 참여하고 있습니다. 이 설명은 긴 텍스트 처리 기능을 테스트하기 위한 예시입니다.`,
    ]);
};

const ResultTableExample: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);
  const [rows, setRows] = useState(() => generateSampleData(20));
  const [rowCount, setRowCount] = useState(20);

  // 데이터 새로고침 핸들러
  const handleRefresh = () => {
    setLoading(true);
    setError(undefined);

    // 실제 애플리케이션에서는 API 호출 등을 수행
    setTimeout(() => {
      try {
        const newData = generateSampleData(20);
        setRows(newData);
        setRowCount(newData.length);
        setLoading(false);
      } catch (err) {
        setError('데이터 로드 중 오류가 발생했습니다.');
        setLoading(false);
      }
    }, 1000);
  };

  // 대용량 데이터 로드 핸들러
  const handleLoadLargeData = () => {
    setLoading(true);
    setError(undefined);

    setTimeout(() => {
      try {
        const newData = generateSampleData(100);
        setRows(newData);
        setRowCount(newData.length);
        setLoading(false);
      } catch (err) {
        setError('대용량 데이터 로드 중 오류가 발생했습니다.');
        setLoading(false);
      }
    }, 1500);
  };

  // 오류 시뮬레이션 핸들러
  const handleSimulateError = () => {
    setError('테스트 오류 메시지입니다.');
  };

  // 행 클릭 핸들러
  const handleRowClick = (row: any[], rowIndex: number) => {
    console.log(`Row ${rowIndex} clicked:`, row);
    alert(`${rowIndex + 1}번 행 클릭: ${row[1]} (${row[2]})`);
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        쿼리 결과 표시 컴포넌트 예제
      </Typography>

      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <Button variant="contained" onClick={handleRefresh}>
          데이터 새로고침
        </Button>
        <Button variant="outlined" onClick={handleLoadLargeData}>
          대용량 데이터 로드 (100행)
        </Button>
        <Button variant="outlined" color="error" onClick={handleSimulateError}>
          오류 시뮬레이션
        </Button>
      </Box>

      <EnhancedResultTable
        columns={sampleColumns}
        rows={rows}
        rowCount={rowCount}
        loading={loading}
        error={error}
        onRefresh={handleRefresh}
        showRowNumbers={true}
        onRowClick={handleRowClick}
        executionTime={123.45}
      />
    </Paper>
  );
};

export default ResultTableExample;
