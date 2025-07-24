import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  IconButton,
  Tooltip,
  TextField,
  InputAdornment,
  Button,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import { Policy, PolicyFilter } from '../../types/admin';

interface PolicyTableProps {
  policies: Policy[];
  loading: boolean;
  filter: PolicyFilter;
  onFilterChange: (filter: PolicyFilter) => void;
  onDeletePolicy: (policyId: string) => void;
}

const PolicyTable: React.FC<PolicyTableProps> = ({
  policies,
  loading,
  filter,
  onFilterChange,
  onDeletePolicy,
}) => {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ ...filter, searchTerm: event.target.value });
  };

  const handleEditPolicy = (policyId: string) => {
    navigate(`/admin/policies/${policyId}`);
  };

  const handleCreatePolicy = () => {
    navigate('/admin/policies/new');
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', mb: 2, justifyContent: 'space-between' }}>
        <TextField
          label="Search Policies"
          variant="outlined"
          size="small"
          value={filter.searchTerm || ''}
          onChange={handleSearchChange}
          sx={{ width: '300px' }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleCreatePolicy}
        >
          Create Policy
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }} aria-label="policies table">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Max Queries/Day</TableCell>
              <TableCell>Max Execution Time (s)</TableCell>
              <TableCell>Max Result Size</TableCell>
              <TableCell>Applied To</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : policies.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No policies found
                </TableCell>
              </TableRow>
            ) : (
              policies.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map(policy => (
                <TableRow key={policy.id} hover>
                  <TableCell>{policy.name}</TableCell>
                  <TableCell>{policy.description}</TableCell>
                  <TableCell>{policy.settings.maxQueriesPerDay}</TableCell>
                  <TableCell>{policy.settings.maxQueryExecutionTime}</TableCell>
                  <TableCell>{policy.settings.maxResultSize} rows</TableCell>
                  <TableCell>{policy.appliedToUsers} users</TableCell>
                  <TableCell>
                    <Tooltip title="Edit Policy">
                      <IconButton size="small" onClick={() => handleEditPolicy(policy.id)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Policy">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => onDeletePolicy(policy.id)}
                      >
                        <DeleteIcon fontSize="small" />
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
        count={policies.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Box>
  );
};

export default PolicyTable;
