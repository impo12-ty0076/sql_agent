import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Collapse,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Grid,
  Button,
  SelectChangeEvent,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import FilterListIcon from '@mui/icons-material/FilterList';
import { LogEntry, LogFilter } from '../../services/adminService';

interface LogsTableProps {
  logs: LogEntry[];
  loading: boolean;
  error: string | null;
  filter: LogFilter;
  onFilterChange: (filter: LogFilter) => void;
}

const LogsTable: React.FC<LogsTableProps> = ({ logs, loading, error, filter, onFilterChange }) => {
  const [showFilters, setShowFilters] = useState(false);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [localFilter, setLocalFilter] = useState<LogFilter>(filter);

  const handleExpandRow = (logId: string) => {
    setExpandedRow(expandedRow === logId ? null : logId);
  };

  const handleFilterChange = (field: keyof LogFilter, value: unknown) => {
    setLocalFilter(prev => ({ ...prev, [field]: value }));
  };

  const applyFilters = () => {
    onFilterChange(localFilter);
  };

  const resetFilters = () => {
    const resetFilter = {};
    setLocalFilter(resetFilter);
    onFilterChange(resetFilter);
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'info':
        return 'info';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'auth':
        return 'primary';
      case 'query':
        return 'secondary';
      case 'system':
        return 'info';
      case 'security':
        return 'error';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" height={200}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6">System Logs</Typography>
          <Box display="flex" justifyContent="center" alignItems="center" height={200}>
            <Typography color="error">{error}</Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">System Logs</Typography>
          <Button
            startIcon={<FilterListIcon />}
            onClick={() => setShowFilters(!showFilters)}
            color="primary"
            size="small"
          >
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </Button>
        </Box>

        <Collapse in={showFilters}>
          <Paper sx={{ p: 2, mb: 2 }}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel id="log-level-label">Log Level</InputLabel>
                    <Select
                      labelId="log-level-label"
                      id="log-level"
                      value={localFilter.level || ''}
                      label="Log Level"
                      onChange={(e: SelectChangeEvent) =>
                        handleFilterChange('level', e.target.value || undefined)
                      }
                    >
                      <MenuItem value="">All Levels</MenuItem>
                      <MenuItem value="info">Info</MenuItem>
                      <MenuItem value="warning">Warning</MenuItem>
                      <MenuItem value="error">Error</MenuItem>
                      <MenuItem value="critical">Critical</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel id="category-label">Category</InputLabel>
                    <Select
                      labelId="category-label"
                      id="category"
                      value={localFilter.category || ''}
                      label="Category"
                      onChange={(e: SelectChangeEvent) =>
                        handleFilterChange('category', e.target.value || undefined)
                      }
                    >
                      <MenuItem value="">All Categories</MenuItem>
                      <MenuItem value="auth">Authentication</MenuItem>
                      <MenuItem value="query">Query</MenuItem>
                      <MenuItem value="system">System</MenuItem>
                      <MenuItem value="security">Security</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <DatePicker
                    label="Start Date"
                    value={localFilter.startDate ? new Date(localFilter.startDate) : null}
                    onChange={date =>
                      handleFilterChange(
                        'startDate',
                        date && date instanceof Date ? date.toISOString() : undefined
                      )
                    }
                    renderInput={params => <TextField {...params} size="small" fullWidth />}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <DatePicker
                    label="End Date"
                    value={localFilter.endDate ? new Date(localFilter.endDate) : null}
                    onChange={date =>
                      handleFilterChange(
                        'endDate',
                        date && date instanceof Date ? date.toISOString() : undefined
                      )
                    }
                    renderInput={params => <TextField {...params} size="small" fullWidth />}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField
                    fullWidth
                    size="small"
                    label="User ID"
                    value={localFilter.userId || ''}
                    onChange={e => handleFilterChange('userId', e.target.value || undefined)}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Search Term"
                    value={localFilter.searchTerm || ''}
                    onChange={e => handleFilterChange('searchTerm', e.target.value || undefined)}
                  />
                </Grid>
                <Grid item xs={12} sm={12} md={6}>
                  <Box display="flex" justifyContent="flex-end" gap={1}>
                    <Button variant="outlined" onClick={resetFilters}>
                      Reset
                    </Button>
                    <Button variant="contained" onClick={applyFilters}>
                      Apply Filters
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </LocalizationProvider>
          </Paper>
        </Collapse>

        <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
          <Table stickyHeader aria-label="logs table">
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox" />
                <TableCell>Timestamp</TableCell>
                <TableCell>Level</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Message</TableCell>
                <TableCell>User ID</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {!Array.isArray(logs) || logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    No logs found
                  </TableCell>
                </TableRow>
              ) : (
                (Array.isArray(logs) ? logs : []).map(log => (
                  <React.Fragment key={log.id}>
                    <TableRow hover>
                      <TableCell padding="checkbox">
                        <IconButton
                          aria-label="expand row"
                          size="small"
                          onClick={() => handleExpandRow(log.id)}
                        >
                          {expandedRow === log.id ? (
                            <KeyboardArrowUpIcon />
                          ) : (
                            <KeyboardArrowDownIcon />
                          )}
                        </IconButton>
                      </TableCell>
                      <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                      <TableCell>
                        <Chip
                          label={log.level.toUpperCase()}
                          color={
                            getLevelColor(log.level) as
                              | 'default'
                              | 'primary'
                              | 'secondary'
                              | 'error'
                              | 'info'
                              | 'success'
                              | 'warning'
                              | undefined
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={log.category}
                          color={
                            getCategoryColor(log.category) as
                              | 'default'
                              | 'primary'
                              | 'secondary'
                              | 'error'
                              | 'info'
                              | 'success'
                              | 'warning'
                              | undefined
                          }
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>{log.message}</TableCell>
                      <TableCell>{log.userId || '-'}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
                        <Collapse in={expandedRow === log.id} timeout="auto" unmountOnExit>
                          <Box sx={{ margin: 1 }}>
                            <Typography variant="h6" gutterBottom component="div">
                              Details
                            </Typography>
                            <pre
                              style={{
                                backgroundColor: '#f5f5f5',
                                padding: '10px',
                                borderRadius: '4px',
                                overflowX: 'auto',
                              }}
                            >
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          </Box>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </React.Fragment>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
};

export default LogsTable;
