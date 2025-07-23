import React, { useState, useEffect, useMemo, useCallback } from 'react';
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
  TableSortLabel,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Tooltip,
  LinearProgress,
  Menu,
  MenuItem,
  Divider,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  useTheme,
  useMediaQuery,
  Alert,
  Snackbar,
  Skeleton,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Download as DownloadIcon,
  ContentCopy as CopyIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  ViewColumn as ViewColumnIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

interface Column {
  name: string;
  type: string;
  width?: number | string;
}

interface EnhancedResultTableProps {
  columns: Column[];
  rows: any[][];
  rowCount: number;
  loading?: boolean;
  truncated?: boolean;
  totalRowCount?: number;
  executionTime?: number;
  onRefresh?: () => void;
  error?: string;
  maxHeight?: number | string;
  stickyHeader?: boolean;
  showRowNumbers?: boolean;
  onRowClick?: (row: any[], rowIndex: number) => void;
  highlightSearchTerms?: boolean;
}

interface FilterState {
  columnIndex: number;
  value: string;
  operator?: FilterOperator;
}

type FilterOperator = 'contains' | 'equals' | 'startsWith' | 'endsWith' | 'greaterThan' | 'lessThan';

interface ColumnVisibility {
  columnIndex: number;
  visible: boolean;
}

const EnhancedResultTable: React.FC<EnhancedResultTableProps> = ({
  columns,
  rows,
  rowCount,
  loading = false,
  truncated = false,
  totalRowCount,
  executionTime,
  onRefresh,
  error,
  maxHeight = 600,
  stickyHeader = true,
  showRowNumbers = false,
  onRowClick,
  highlightSearchTerms = true,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // State for pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // State for sorting
  const [orderBy, setOrderBy] = useState<number | null>(null);
  const [order, setOrder] = useState<'asc' | 'desc'>('asc');
  
  // State for filtering
  const [filters, setFilters] = useState<FilterState[]>([]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [filterMenuAnchorEl, setFilterMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [filterColumnIndex, setFilterColumnIndex] = useState<number | null>(null);
  const [filterOperator, setFilterOperator] = useState<FilterOperator>('contains');
  
  // State for column visibility
  const [columnVisibility, setColumnVisibility] = useState<ColumnVisibility[]>([]);
  const [columnMenuAnchorEl, setColumnMenuAnchorEl] = useState<null | HTMLElement>(null);
  
  // State for cell detail view
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [detailContent, setDetailContent] = useState<string>('');
  const [detailTitle, setDetailTitle] = useState<string>('');
  
  // State for notifications
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'warning' | 'info'>('success');
  
  // Initialize column visibility when columns change
  useEffect(() => {
    if (columns.length) {
      setColumnVisibility(columns.map((_, index) => ({
        columnIndex: index,
        visible: true
      })));
    }
  }, [columns]);

  // Reset pagination when data changes
  useEffect(() => {
    setPage(0);
  }, [rows, filters, globalFilter]);

  // Handle sort request
  const handleRequestSort = (columnIndex: number) => {
    const isAsc = orderBy === columnIndex && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(columnIndex);
  };

  // Handle filter menu open
  const handleFilterMenuOpen = (event: React.MouseEvent<HTMLElement>, columnIndex: number) => {
    setFilterMenuAnchorEl(event.currentTarget);
    setFilterColumnIndex(columnIndex);
  };

  // Handle filter menu close
  const handleFilterMenuClose = () => {
    setFilterMenuAnchorEl(null);
    setFilterColumnIndex(null);
  };

  // Handle filter apply
  const handleFilterApply = (value: string) => {
    if (filterColumnIndex !== null) {
      // Remove existing filter for this column if it exists
      const newFilters = filters.filter(f => f.columnIndex !== filterColumnIndex);
      
      // Add new filter if value is not empty
      if (value.trim()) {
        newFilters.push({
          columnIndex: filterColumnIndex,
          value: value.trim(),
          operator: filterOperator
        });
      }
      
      setFilters(newFilters);
      handleFilterMenuClose();
    }
  };
  
  // Handle filter operator change
  const handleFilterOperatorChange = (event: SelectChangeEvent<FilterOperator>) => {
    setFilterOperator(event.target.value as FilterOperator);
  };
  
  // Handle column visibility toggle
  const handleColumnVisibilityToggle = (columnIndex: number) => {
    setColumnVisibility(prev => 
      prev.map(col => 
        col.columnIndex === columnIndex 
          ? { ...col, visible: !col.visible } 
          : col
      )
    );
  };
  
  // Handle column menu open
  const handleColumnMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setColumnMenuAnchorEl(event.currentTarget);
  };
  
  // Handle column menu close
  const handleColumnMenuClose = () => {
    setColumnMenuAnchorEl(null);
  };
  
  // Handle cell detail view
  const handleCellDetail = (content: any, columnName: string) => {
    if (content !== null && content !== undefined) {
      setDetailContent(String(content));
      setDetailTitle(columnName);
      setDetailDialogOpen(true);
    }
  };
  
  // Handle detail dialog close
  const handleDetailDialogClose = () => {
    setDetailDialogOpen(false);
  };

  // Handle filter remove
  const handleFilterRemove = (columnIndex: number) => {
    setFilters(filters.filter(f => f.columnIndex !== columnIndex));
  };

  // Handle clear all filters
  const handleClearAllFilters = () => {
    setFilters([]);
    setGlobalFilter('');
  };

  // Handle global filter change
  const handleGlobalFilterChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setGlobalFilter(event.target.value);
  };

  // Handle page change
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  // Handle rows per page change
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Show notification
  const showNotification = (message: string, severity: 'success' | 'error' | 'warning' | 'info' = 'success') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };

  // Copy to clipboard
  const handleCopyToClipboard = async () => {
    try {
      // Create a string representation of the data
      const visibleColumnNames = columns
        .filter((_, index) => columnVisibility.find(col => col.columnIndex === index)?.visible ?? true)
        .map(col => col.name);
      
      const headers = visibleColumnNames.join('\t');
      const data = filteredAndSortedRows.map(row => 
        row.filter((_, index) => columnVisibility.find(col => col.columnIndex === index)?.visible ?? true)
          .join('\t')
      ).join('\n');
      const text = `${headers}\n${data}`;
      
      await navigator.clipboard.writeText(text);
      showNotification(`${filteredAndSortedRows.length}개 행이 클립보드에 복사되었습니다.`);
    } catch (err) {
      console.error('Could not copy data: ', err);
      showNotification('클립보드 복사에 실패했습니다.', 'error');
    }
  };

  // Download as CSV
  const handleDownloadCsv = () => {
    try {
      // Create CSV content with only visible columns
      const visibleColumnNames = columns
        .filter((_, index) => columnVisibility.find(col => col.columnIndex === index)?.visible ?? true)
        .map(col => col.name);
      
      const headers = visibleColumnNames.map(name => `"${name}"`).join(',');
      const data = filteredAndSortedRows.map(row => 
        row.filter((_, index) => columnVisibility.find(col => col.columnIndex === index)?.visible ?? true)
          .map(cell => `"${String(cell || '').replace(/"/g, '""')}"`)
          .join(',')
      ).join('\n');
      const csv = `${headers}\n${data}`;
      
      // Create download link
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `query_result_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      showNotification(`${filteredAndSortedRows.length}개 행이 CSV 파일로 다운로드되었습니다.`);
    } catch (err) {
      console.error('Could not download CSV: ', err);
      showNotification('CSV 다운로드에 실패했습니다.', 'error');
    }
  };

  // Apply filter based on operator
  const applyFilter = useCallback((cellValue: any, filter: FilterState): boolean => {
    const strValue = String(cellValue || '').toLowerCase();
    const filterValue = filter.value.toLowerCase();
    
    switch (filter.operator) {
      case 'equals':
        return strValue === filterValue;
      case 'startsWith':
        return strValue.startsWith(filterValue);
      case 'endsWith':
        return strValue.endsWith(filterValue);
      case 'greaterThan':
        // Try to compare as numbers if possible
        const numCell = Number(cellValue);
        const numFilter = Number(filterValue);
        if (!isNaN(numCell) && !isNaN(numFilter)) {
          return numCell > numFilter;
        }
        return strValue > filterValue;
      case 'lessThan':
        // Try to compare as numbers if possible
        const numCellLt = Number(cellValue);
        const numFilterLt = Number(filterValue);
        if (!isNaN(numCellLt) && !isNaN(numFilterLt)) {
          return numCellLt < numFilterLt;
        }
        return strValue < filterValue;
      case 'contains':
      default:
        return strValue.includes(filterValue);
    }
  }, []);

  // Apply filters to rows
  const filteredRows = useMemo(() => {
    if (!rows.length) return [];
    
    return rows.filter(row => {
      // Apply column-specific filters
      const passesColumnFilters = filters.every(filter => {
        const cellValue = row[filter.columnIndex];
        return applyFilter(cellValue, filter);
      });
      
      // Apply global filter
      const passesGlobalFilter = !globalFilter || row.some(cell => 
        String(cell).toLowerCase().includes(globalFilter.toLowerCase())
      );
      
      return passesColumnFilters && passesGlobalFilter;
    });
  }, [rows, filters, globalFilter, applyFilter]);

  // Apply sorting to filtered rows
  const filteredAndSortedRows = useMemo(() => {
    if (!filteredRows.length) return [];
    
    if (orderBy === null) return filteredRows;
    
    return [...filteredRows].sort((a, b) => {
      const aValue = a[orderBy];
      const bValue = b[orderBy];
      
      // Handle different types of values
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return order === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      // Default string comparison
      const aString = String(aValue || '').toLowerCase();
      const bString = String(bValue || '').toLowerCase();
      
      return order === 'asc' 
        ? aString.localeCompare(bString)
        : bString.localeCompare(aString);
    });
  }, [filteredRows, orderBy, order]);

  // Get current page rows
  const currentPageRows = useMemo(() => {
    const startIndex = page * rowsPerPage;
    return filteredAndSortedRows.slice(startIndex, startIndex + rowsPerPage);
  }, [filteredAndSortedRows, page, rowsPerPage]);

  // Get visible columns
  const visibleColumns = useMemo(() => {
    if (!columnVisibility.length) return columns;
    return columns.filter((_, index) => 
      columnVisibility.find(col => col.columnIndex === index)?.visible ?? true
    );
  }, [columns, columnVisibility]);
  
  // Get visible column indices
  const visibleColumnIndices = useMemo(() => {
    return columnVisibility
      .filter(col => col.visible)
      .map(col => col.columnIndex);
  }, [columnVisibility]);
  
  // Get visible column count for colSpan
  const visibleColumnCount = useMemo(() => {
    const baseCount = columnVisibility.length ? columnVisibility.filter(col => col.visible).length : columns.length;
    return showRowNumbers ? baseCount + 1 : baseCount;
  }, [columnVisibility, columns.length, showRowNumbers]);

  // Highlight search terms in text
  const highlightText = useCallback((text: string, searchTerm: string) => {
    if (!highlightSearchTerms || !searchTerm.trim()) return text;
    
    const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} style={{ backgroundColor: '#ffeb3b', padding: '0 2px' }}>
          {part}
        </mark>
      ) : part
    );
  }, [highlightSearchTerms]);

  // If no data
  if (!columns.length) {
    return (
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="body1">결과가 없습니다.</Typography>
      </Paper>
    );
  }
  
  // If error
  if (error) {
    return (
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="body1" color="error">오류 발생: {error}</Typography>
        {onRefresh && (
          <Button 
            startIcon={<RefreshIcon />} 
            onClick={onRefresh}
            variant="outlined"
            sx={{ mt: 2 }}
          >
            다시 시도
          </Button>
        )}
      </Paper>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          쿼리 결과
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="컬럼 표시 설정">
            <IconButton onClick={handleColumnMenuOpen} size="small">
              <ViewColumnIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="클립보드에 복사">
            <IconButton onClick={handleCopyToClipboard} size="small">
              <CopyIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="CSV 다운로드">
            <IconButton onClick={handleDownloadCsv} size="small">
              <DownloadIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="body2" color="text.secondary">
            {filteredRows.length === rowCount 
              ? `총 ${rowCount}개의 행이 조회되었습니다.` 
              : `${filteredRows.length} / ${rowCount}개의 행이 표시되고 있습니다.`}
            {truncated && totalRowCount && ` (전체 ${totalRowCount}개 중 일부)`}
          </Typography>
          {executionTime && (
            <Typography variant="caption" color="text.secondary" display="block">
              실행 시간: {executionTime.toFixed(2)}ms
            </Typography>
          )}
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TextField
            variant="outlined"
            size="small"
            placeholder="전체 검색..."
            value={globalFilter}
            onChange={handleGlobalFilterChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
              endAdornment: globalFilter && (
                <InputAdornment position="end">
                  <IconButton
                    size="small"
                    onClick={() => setGlobalFilter('')}
                    edge="end"
                  >
                    <ClearIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{ width: 200 }}
          />
          
          {filters.length > 0 && (
            <Tooltip title="모든 필터 지우기">
              <IconButton size="small" onClick={handleClearAllFilters} sx={{ ml: 1 }}>
                <ClearIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>
      
      {/* Active filters display */}
      {filters.length > 0 && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
          {filters.map((filter, index) => (
            <Chip
              key={index}
              label={`${columns[filter.columnIndex].name}: ${filter.value}`}
              onDelete={() => handleFilterRemove(filter.columnIndex)}
              size="small"
              color="primary"
              variant="outlined"
            />
          ))}
        </Box>
      )}
      
      {loading && <LinearProgress sx={{ mb: 2 }} />}
      
      <TableContainer sx={{ maxHeight }}>
        <Table stickyHeader={stickyHeader} size="small">
          <TableHead>
            <TableRow>
              {showRowNumbers && (
                <TableCell sx={{ width: 60, fontWeight: 'bold' }}>
                  <Typography variant="subtitle2">#</Typography>
                </TableCell>
              )}
              {columns.map((column, index) => {
                // Check if column is visible
                const isVisible = columnVisibility.find(col => col.columnIndex === index)?.visible ?? true;
                if (!isVisible) return null;
                
                return (
                  <TableCell 
                    key={index}
                    sortDirection={orderBy === index ? order : false}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <TableSortLabel
                        active={orderBy === index}
                        direction={orderBy === index ? order : 'asc'}
                        onClick={() => handleRequestSort(index)}
                      >
                        <Typography variant="subtitle2">{column.name}</Typography>
                      </TableSortLabel>
                      
                      <Tooltip title="필터">
                        <IconButton
                          size="small"
                          onClick={(e) => handleFilterMenuOpen(e, index)}
                          sx={{ ml: 0.5 }}
                        >
                          <FilterIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      {column.type}
                    </Typography>
                  </TableCell>
                );
              })}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && currentPageRows.length === 0 ? (
              // Show skeleton loading rows
              Array(rowsPerPage).fill(null).map((_, skeletonIndex) => (
                <TableRow key={`skeleton-${skeletonIndex}`}>
                  {showRowNumbers && (
                    <TableCell>
                      <Skeleton variant="text" width={30} />
                    </TableCell>
                  )}
                  {columns.map((_, colIndex) => {
                    const isVisible = columnVisibility.find(col => col.columnIndex === colIndex)?.visible ?? true;
                    if (!isVisible) return null;
                    
                    return (
                      <TableCell key={colIndex}>
                        <Skeleton variant="text" width="80%" />
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))
            ) : (
              currentPageRows.map((row, rowIndex) => (
                <TableRow 
                  key={rowIndex} 
                  hover 
                  onClick={() => onRowClick?.(row, page * rowsPerPage + rowIndex)}
                  sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
                >
                  {showRowNumbers && (
                    <TableCell sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
                      {page * rowsPerPage + rowIndex + 1}
                    </TableCell>
                  )}
                  {row.map((cell, cellIndex) => {
                  // Check if column is visible
                  const isVisible = columnVisibility.find(col => col.columnIndex === cellIndex)?.visible ?? true;
                  if (!isVisible) return null;
                  
                  const columnName = columns[cellIndex]?.name || '';
                  const cellContent = cell !== null && cell !== undefined ? cell : '';
                  const cellStr = String(cellContent);
                  const isTruncated = cellStr.length > 100;
                  
                  return (
                    <TableCell 
                      key={cellIndex}
                      onClick={() => isTruncated && handleCellDetail(cellContent, columnName)}
                      sx={{ 
                        cursor: isTruncated ? 'pointer' : 'default',
                        maxWidth: '200px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      <Tooltip title={isTruncated ? "클릭하여 전체 내용 보기" : ""}>
                        <span>
                          {isTruncated 
                            ? highlightText(`${cellStr.substring(0, 100)}...`, globalFilter)
                            : highlightText(cellStr, globalFilter)
                          }
                        </span>
                      </Tooltip>
                    </TableCell>
                  );
                  })}
                </TableRow>
              ))
            )}
            {!loading && currentPageRows.length === 0 && (
              <TableRow>
                <TableCell colSpan={visibleColumnCount} align="center">
                  <Box sx={{ py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                      {filteredRows.length === 0 && (filters.length > 0 || globalFilter) 
                        ? '필터 조건에 맞는 결과가 없습니다.' 
                        : '결과가 없습니다.'
                      }
                    </Typography>
                    {filteredRows.length === 0 && (filters.length > 0 || globalFilter) && (
                      <Button 
                        size="small" 
                        onClick={handleClearAllFilters}
                        sx={{ mt: 1 }}
                      >
                        모든 필터 지우기
                      </Button>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      <TablePagination
        component="div"
        count={filteredAndSortedRows.length}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        rowsPerPageOptions={[10, 25, 50, 100]}
        labelRowsPerPage="행 수:"
        labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
      />
      
      {/* Filter menu */}
      <Menu
        anchorEl={filterMenuAnchorEl}
        open={Boolean(filterMenuAnchorEl)}
        onClose={handleFilterMenuClose}
      >
        <Box sx={{ p: 2, width: 250 }}>
          <Typography variant="subtitle2" gutterBottom>
            {filterColumnIndex !== null && columns[filterColumnIndex]?.name} 필터
          </Typography>
          
          <FormControl fullWidth size="small" sx={{ mb: 2 }}>
            <InputLabel>연산자</InputLabel>
            <Select
              value={filterOperator}
              onChange={handleFilterOperatorChange}
              label="연산자"
            >
              <MenuItem value="contains">포함</MenuItem>
              <MenuItem value="equals">일치</MenuItem>
              <MenuItem value="startsWith">시작</MenuItem>
              <MenuItem value="endsWith">끝</MenuItem>
              <MenuItem value="greaterThan">초과</MenuItem>
              <MenuItem value="lessThan">미만</MenuItem>
            </Select>
          </FormControl>
          
          <TextField
            autoFocus
            fullWidth
            size="small"
            placeholder="필터 값 입력..."
            defaultValue={filterColumnIndex !== null 
              ? filters.find(f => f.columnIndex === filterColumnIndex)?.value || '' 
              : ''}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleFilterApply((e.target as HTMLInputElement).value);
              }
            }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      const input = (e.currentTarget.parentNode as HTMLElement)
                        .querySelector('input') as HTMLInputElement;
                      handleFilterApply(input.value);
                    }}
                  >
                    <SearchIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          
          <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="caption" color="text.secondary">
              Enter 키를 눌러 적용
            </Typography>
            {filterColumnIndex !== null && 
              filters.some(f => f.columnIndex === filterColumnIndex) && (
              <Typography 
                variant="caption" 
                color="primary" 
                sx={{ cursor: 'pointer' }}
                onClick={() => handleFilterRemove(filterColumnIndex)}
              >
                필터 제거
              </Typography>
            )}
          </Box>
        </Box>
      </Menu>
      
      {/* Column visibility menu */}
      <Menu
        anchorEl={columnMenuAnchorEl}
        open={Boolean(columnMenuAnchorEl)}
        onClose={handleColumnMenuClose}
      >
        <Box sx={{ p: 2, width: 250 }}>
          <Typography variant="subtitle2" gutterBottom>
            컬럼 표시 설정
          </Typography>
          <Divider sx={{ my: 1 }} />
          {columnVisibility.map((col) => (
            <MenuItem key={col.columnIndex} onClick={() => handleColumnVisibilityToggle(col.columnIndex)}>
              <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between' }}>
                <Typography variant="body2">
                  {columns[col.columnIndex]?.name}
                </Typography>
                {col.visible ? <VisibilityIcon fontSize="small" color="primary" /> : <VisibilityOffIcon fontSize="small" />}
              </Box>
            </MenuItem>
          ))}
        </Box>
      </Menu>
      
      {/* Cell detail dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={handleDetailDialogClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{detailTitle}</DialogTitle>
        <DialogContent dividers>
          <Box sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {detailContent}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => navigator.clipboard.writeText(detailContent)}>
            복사
          </Button>
          <Button onClick={handleDetailDialogClose}>
            닫기
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Notification snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setSnackbarOpen(false)} 
          severity={snackbarSeverity}
          variant="filled"
          icon={snackbarSeverity === 'success' ? <CheckCircleIcon /> : undefined}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Paper>
  );
};

export default EnhancedResultTable;