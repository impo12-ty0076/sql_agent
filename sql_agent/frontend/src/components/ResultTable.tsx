import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  TablePagination,
} from '@mui/material';

interface Column {
  name: string;
  type: string;
}

interface ResultTableProps {
  columns: Column[];
  rows: any[][];
  rowCount: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}

const ResultTable: React.FC<ResultTableProps> = ({
  columns,
  rows,
  rowCount,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
}) => {
  if (!columns.length || !rows.length) {
    return (
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="body1">결과가 없습니다.</Typography>
      </Paper>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        쿼리 결과
      </Typography>
      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          총 {rowCount}개의 행이 조회되었습니다.
        </Typography>
      </Box>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              {columns.map((column, index) => (
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
            {rows.map((row, rowIndex) => (
              <TableRow key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <TableCell key={cellIndex}>{String(cell)}</TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        component="div"
        count={rowCount}
        page={page}
        onPageChange={(_, newPage) => onPageChange(newPage)}
        rowsPerPage={pageSize}
        onRowsPerPageChange={(e) => onPageSizeChange(parseInt(e.target.value, 10))}
        rowsPerPageOptions={[10, 25, 50, 100]}
      />
    </Paper>
  );
};

export default ResultTable;