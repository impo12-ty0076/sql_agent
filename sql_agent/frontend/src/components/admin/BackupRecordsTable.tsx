import React, { useState } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  IconButton,
  Chip,
  Tooltip,
  TextField,
  InputAdornment,
  Button,
  Typography,
  LinearProgress,
} from '@mui/material';
import { Download, Restore, Search, CheckCircle, Error, HourglassTop } from '@mui/icons-material';
import { BackupRecord, BackupFilter } from '../../types/systemSettings';

interface BackupRecordsTableProps {
  backupRecords: BackupRecord[];
  loading: boolean;
  onRestore: (record: BackupRecord) => void;
  onDownload: (record: BackupRecord) => void;
  onFilterChange: (filter: BackupFilter) => void;
  filter: BackupFilter;
  totalCount: number;
  page: number;
  rowsPerPage: number;
  onPageChange: (event: unknown, newPage: number) => void;
  onRowsPerPageChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

const BackupRecordsTable: React.FC<BackupRecordsTableProps> = ({
  backupRecords,
  loading,
  onRestore,
  onDownload,
  onFilterChange,
  filter,
  totalCount,
  page,
  rowsPerPage,
  onPageChange,
  onRowsPerPageChange,
}) => {
  const [startDate, setStartDate] = useState<string>(
    filter.startDate ? new Date(filter.startDate).toISOString().split('T')[0] : ''
  );
  const [endDate, setEndDate] = useState<string>(
    filter.endDate ? new Date(filter.endDate).toISOString().split('T')[0] : ''
  );

  const handleStartDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setStartDate(event.target.value);
  };

  const handleEndDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEndDate(event.target.value);
  };

  const handleFilterApply = () => {
    onFilterChange({
      ...filter,
      startDate: startDate ? new Date(startDate) : undefined,
      endDate: endDate ? new Date(endDate) : undefined,
    });
  };

  const handleStatusChange = (status: 'completed' | 'failed' | 'in_progress' | undefined) => {
    onFilterChange({
      ...filter,
      status,
    });
  };

  const getStatusIcon = (status: string): React.ReactElement => {
    switch (status) {
      case 'completed':
        return <CheckCircle fontSize="small" />;
      case 'failed':
        return <Error fontSize="small" />;
      case 'in_progress':
        return <HourglassTop fontSize="small" />;
      default:
        return <CheckCircle fontSize="small" />; // Default icon to ensure we always return a ReactElement
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'in_progress':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', mb: 2, gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          label="Start Date"
          type="date"
          value={startDate}
          onChange={handleStartDateChange}
          InputLabelProps={{ shrink: true }}
          size="small"
          sx={{ width: 170 }}
        />
        <TextField
          label="End Date"
          type="date"
          value={endDate}
          onChange={handleEndDateChange}
          InputLabelProps={{ shrink: true }}
          size="small"
          sx={{ width: 170 }}
        />
        <Button variant="outlined" size="small" onClick={handleFilterApply} startIcon={<Search />}>
          Apply Filter
        </Button>
        <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
          <Chip
            label="All"
            color={!filter.status ? 'primary' : 'default'}
            onClick={() => handleStatusChange(undefined)}
            clickable
          />
          <Chip
            label="Completed"
            color={filter.status === 'completed' ? 'success' : 'default'}
            onClick={() => handleStatusChange('completed')}
            clickable
            icon={<CheckCircle fontSize="small" />}
          />
          <Chip
            label="Failed"
            color={filter.status === 'failed' ? 'error' : 'default'}
            onClick={() => handleStatusChange('failed')}
            clickable
            icon={<Error fontSize="small" />}
          />
          <Chip
            label="In Progress"
            color={filter.status === 'in_progress' ? 'warning' : 'default'}
            onClick={() => handleStatusChange('in_progress')}
            clickable
            icon={<HourglassTop fontSize="small" />}
          />
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }} aria-label="backup records table">
          <TableHead>
            <TableRow>
              <TableCell>Timestamp</TableCell>
              <TableCell>Configuration</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Location</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {backupRecords.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No backup records found
                </TableCell>
              </TableRow>
            ) : (
              backupRecords.map(record => (
                <TableRow key={record.id} hover>
                  <TableCell>{new Date(record.timestamp).toLocaleString()}</TableCell>
                  <TableCell>{record.configId}</TableCell>
                  <TableCell>{formatFileSize(record.size)}</TableCell>
                  <TableCell>
                    <Chip
                      label={record.status}
                      color={getStatusColor(record.status)}
                      size="small"
                      icon={getStatusIcon(record.status)}
                    />
                    {record.error && (
                      <Typography variant="caption" color="error" display="block">
                        {record.error}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography
                      variant="body2"
                      sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}
                    >
                      {record.location}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Download">
                      <IconButton
                        onClick={() => onDownload(record)}
                        color="primary"
                        disabled={record.status !== 'completed'}
                      >
                        <Download />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Restore">
                      <IconButton
                        onClick={() => onRestore(record)}
                        color="warning"
                        disabled={record.status !== 'completed'}
                      >
                        <Restore />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[5, 10, 25]}
        component="div"
        count={totalCount}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={onPageChange}
        onRowsPerPageChange={onRowsPerPageChange}
      />
    </Box>
  );
};

export default BackupRecordsTable;
