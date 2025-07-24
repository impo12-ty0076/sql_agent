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
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material';
import { SelectChangeEvent } from '@mui/material/Select';
import { Edit, Delete, Refresh, Search, Check, Clear } from '@mui/icons-material';
import { ConnectionConfig, ConnectionConfigFilter } from '../../types/systemSettings';

interface ConnectionConfigTableProps {
  connections: ConnectionConfig[];
  loading: boolean;
  onEdit: (connection: ConnectionConfig) => void;
  onDelete: (connection: ConnectionConfig) => void;
  onTest: (connection: ConnectionConfig) => void;
  onFilterChange: (filter: ConnectionConfigFilter) => void;
  filter: ConnectionConfigFilter;
  totalCount: number;
  page: number;
  rowsPerPage: number;
  onPageChange: (event: unknown, newPage: number) => void;
  onRowsPerPageChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

const ConnectionConfigTable: React.FC<ConnectionConfigTableProps> = ({
  connections,
  loading,
  onEdit,
  onDelete,
  onTest,
  onFilterChange,
  filter,
  totalCount,
  page,
  rowsPerPage,
  onPageChange,
  onRowsPerPageChange,
}) => {
  const [searchTerm, setSearchTerm] = useState(filter.searchTerm || '');

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const handleSearchSubmit = () => {
    onFilterChange({ ...filter, searchTerm });
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSearchSubmit();
    }
  };

  const handleTypeChange = (event: SelectChangeEvent) => {
    onFilterChange({ ...filter, type: event.target.value as 'mssql' | 'hana' | undefined });
  };

  const handleStatusChange = (event: SelectChangeEvent) => {
    onFilterChange({ ...filter, status: event.target.value as 'active' | 'inactive' | undefined });
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', mb: 2, gap: 2, flexWrap: 'wrap' }}>
        <TextField
          label="Search"
          variant="outlined"
          size="small"
          value={searchTerm}
          onChange={handleSearchChange}
          onKeyPress={handleKeyPress}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={handleSearchSubmit} edge="end">
                  <Search />
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{ flexGrow: 1, minWidth: '200px' }}
        />
        <FormControl size="small" sx={{ minWidth: '150px' }}>
          <InputLabel>Database Type</InputLabel>
          <Select
            value={filter.type || ''}
            onChange={handleTypeChange}
            label="Database Type"
            displayEmpty
          >
            <MenuItem value="">All Types</MenuItem>
            <MenuItem value="mssql">MS-SQL</MenuItem>
            <MenuItem value="hana">SAP HANA</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: '150px' }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={filter.status || ''}
            onChange={handleStatusChange}
            label="Status"
            displayEmpty
          >
            <MenuItem value="">All Status</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="inactive">Inactive</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }} aria-label="connection configurations table">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Host</TableCell>
              <TableCell>Port</TableCell>
              <TableCell>Default Schema</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Updated</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : connections.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  No connection configurations found
                </TableCell>
              </TableRow>
            ) : (
              connections.map(connection => (
                <TableRow key={connection.id} hover>
                  <TableCell>{connection.name}</TableCell>
                  <TableCell>
                    <Chip
                      label={connection.type === 'mssql' ? 'MS-SQL' : 'SAP HANA'}
                      color={connection.type === 'mssql' ? 'primary' : 'secondary'}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>{connection.host}</TableCell>
                  <TableCell>{connection.port}</TableCell>
                  <TableCell>{connection.defaultSchema}</TableCell>
                  <TableCell>
                    <Chip
                      label={connection.status}
                      color={connection.status === 'active' ? 'success' : 'error'}
                      icon={connection.status === 'active' ? <Check /> : <Clear />}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{new Date(connection.updatedAt).toLocaleDateString()}</TableCell>
                  <TableCell align="right">
                    <Tooltip title="Test Connection">
                      <IconButton onClick={() => onTest(connection)} color="info">
                        <Refresh />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton onClick={() => onEdit(connection)} color="primary">
                        <Edit />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton onClick={() => onDelete(connection)} color="error">
                        <Delete />
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

export default ConnectionConfigTable;
