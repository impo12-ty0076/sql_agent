import React from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Tooltip,
  Button
} from '@mui/material';
import { Edit, Delete, Backup, Schedule } from '@mui/icons-material';
import { BackupConfig } from '../../types/systemSettings';

interface BackupConfigTableProps {
  backupConfigs: BackupConfig[];
  loading: boolean;
  onEdit: (config: BackupConfig) => void;
  onDelete: (config: BackupConfig) => void;
  onBackupNow: (config: BackupConfig) => void;
}

const BackupConfigTable: React.FC<BackupConfigTableProps> = ({
  backupConfigs,
  loading,
  onEdit,
  onDelete,
  onBackupNow
}) => {
  const formatSchedule = (schedule: string) => {
    return schedule.charAt(0).toUpperCase() + schedule.slice(1);
  };

  const getStatusColor = (status: string) => {
    return status === 'active' ? 'success' : 'error';
  };

  return (
    <Box sx={{ width: '100%' }}>
      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }} aria-label="backup configurations table">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Schedule</TableCell>
              <TableCell>Retention</TableCell>
              <TableCell>Included Data</TableCell>
              <TableCell>Last Backup</TableCell>
              <TableCell>Next Backup</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center">Loading...</TableCell>
              </TableRow>
            ) : backupConfigs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">No backup configurations found</TableCell>
              </TableRow>
            ) : (
              backupConfigs.map((config) => (
                <TableRow key={config.id} hover>
                  <TableCell>{config.name}</TableCell>
                  <TableCell>
                    <Chip 
                      label={formatSchedule(config.schedule)} 
                      color="primary"
                      size="small"
                      variant="outlined"
                      icon={<Schedule fontSize="small" />}
                    />
                  </TableCell>
                  <TableCell>{config.retention} backups</TableCell>
                  <TableCell>
                    {[
                      config.includeSettings && 'Settings',
                      config.includeUserData && 'User Data',
                      config.includeQueryHistory && 'Query History'
                    ].filter(Boolean).join(', ')}
                  </TableCell>
                  <TableCell>
                    {config.lastBackupAt 
                      ? new Date(config.lastBackupAt).toLocaleString() 
                      : 'Never'}
                  </TableCell>
                  <TableCell>
                    {config.nextBackupAt && config.status === 'active'
                      ? new Date(config.nextBackupAt).toLocaleString()
                      : 'N/A'}
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={config.status} 
                      color={getStatusColor(config.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Backup Now">
                      <IconButton 
                        onClick={() => onBackupNow(config)} 
                        color="primary"
                        disabled={config.status !== 'active'}
                      >
                        <Backup />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton onClick={() => onEdit(config)} color="primary">
                        <Edit />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton onClick={() => onDelete(config)} color="error">
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
    </Box>
  );
};

export default BackupConfigTable;