import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
  OutlinedInput,
  Chip,
  Button,
  Paper,
  Divider,
  FormHelperText,
  SelectChangeEvent,
  Grid,
  CircularProgress,
} from '@mui/material';
import { Database, UserPermissions, DatabasePermission } from '../../types/admin';

interface UserPermissionsFormProps {
  permissions: UserPermissions;
  databases: Database[];
  loading: boolean;
  onSave: (permissions: UserPermissions) => void;
}

const UserPermissionsForm: React.FC<UserPermissionsFormProps> = ({
  permissions,
  databases,
  loading,
  onSave,
}) => {
  const [formPermissions, setFormPermissions] = useState<UserPermissions>({
    allowedDatabases: [],
  });
  const [selectedDbId, setSelectedDbId] = useState<string>('');
  const [selectedSchemas, setSelectedSchemas] = useState<string[]>([]);
  const [selectedTables, setSelectedTables] = useState<string[]>([]);
  const [availableTables, setAvailableTables] = useState<string[]>([]);

  // Initialize form with current permissions
  useEffect(() => {
    setFormPermissions(permissions);
  }, [permissions]);

  // Update available tables when selected schemas change
  useEffect(() => {
    if (!selectedDbId) return;

    const selectedDb = databases.find(db => db.id === selectedDbId);
    if (!selectedDb) return;

    const tables: string[] = [];
    selectedDb.schemas
      .filter(schema => selectedSchemas.includes(schema.name))
      .forEach(schema => {
        schema.tables.forEach(table => {
          tables.push(table.name);
        });
      });

    setAvailableTables(tables);
    // Reset selected tables when schemas change
    setSelectedTables([]);
  }, [selectedDbId, selectedSchemas, databases]);

  const handleDatabaseChange = (event: SelectChangeEvent<string>) => {
    const dbId = event.target.value;
    setSelectedDbId(dbId);
    setSelectedSchemas([]);
    setSelectedTables([]);
  };

  const handleSchemaChange = (event: SelectChangeEvent<string[]>) => {
    const schemas = event.target.value as string[];
    setSelectedSchemas(schemas);
  };

  const handleTableChange = (event: SelectChangeEvent<string[]>) => {
    const tables = event.target.value as string[];
    setSelectedTables(tables);
  };

  const handleAddPermission = () => {
    if (!selectedDbId) return;

    const selectedDb = databases.find(db => db.id === selectedDbId);
    if (!selectedDb) return;

    const newPermission: DatabasePermission = {
      dbId: selectedDbId,
      dbType: selectedDb.type,
      allowedSchemas: selectedSchemas,
      allowedTables: selectedTables,
    };

    // Remove any existing permission for this database
    const updatedPermissions = formPermissions.allowedDatabases.filter(
      p => p.dbId !== selectedDbId
    );

    // Add the new permission
    setFormPermissions({
      allowedDatabases: [...updatedPermissions, newPermission],
    });

    // Reset selection
    setSelectedDbId('');
    setSelectedSchemas([]);
    setSelectedTables([]);
  };

  const handleRemovePermission = (dbId: string) => {
    setFormPermissions({
      allowedDatabases: formPermissions.allowedDatabases.filter(p => p.dbId !== dbId),
    });
  };

  const handleSave = () => {
    onSave(formPermissions);
  };

  const getDbNameById = (dbId: string) => {
    const db = databases.find(db => db.id === dbId);
    return db ? db.name : dbId;
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Database Permissions
      </Typography>

      {loading ? (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Add Database Permission
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small">
                  <InputLabel>Database</InputLabel>
                  <Select value={selectedDbId} onChange={handleDatabaseChange} label="Database">
                    {databases.map(db => (
                      <MenuItem key={db.id} value={db.id}>
                        {db.name} ({db.type})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small" disabled={!selectedDbId}>
                  <InputLabel>Schemas</InputLabel>
                  <Select
                    multiple
                    value={selectedSchemas}
                    onChange={handleSchemaChange}
                    input={<OutlinedInput label="Schemas" />}
                    renderValue={selected => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map(value => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {selectedDbId &&
                      databases
                        .find(db => db.id === selectedDbId)
                        ?.schemas.map(schema => (
                          <MenuItem key={schema.name} value={schema.name}>
                            <Checkbox checked={selectedSchemas.indexOf(schema.name) > -1} />
                            <ListItemText primary={schema.name} />
                          </MenuItem>
                        ))}
                  </Select>
                  <FormHelperText>Select schemas to grant access</FormHelperText>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small" disabled={selectedSchemas.length === 0}>
                  <InputLabel>Tables</InputLabel>
                  <Select
                    multiple
                    value={selectedTables}
                    onChange={handleTableChange}
                    input={<OutlinedInput label="Tables" />}
                    renderValue={selected => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map(value => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {availableTables.map(table => (
                      <MenuItem key={table} value={table}>
                        <Checkbox checked={selectedTables.indexOf(table) > -1} />
                        <ListItemText primary={table} />
                      </MenuItem>
                    ))}
                  </Select>
                  <FormHelperText>
                    {selectedTables.length === 0 && selectedSchemas.length > 0
                      ? 'Empty selection grants access to all tables'
                      : 'Select tables to grant access'}
                  </FormHelperText>
                </FormControl>
              </Grid>
            </Grid>

            <Box mt={2} display="flex" justifyContent="flex-end">
              <Button
                variant="contained"
                color="primary"
                onClick={handleAddPermission}
                disabled={!selectedDbId || selectedSchemas.length === 0}
              >
                Add Permission
              </Button>
            </Box>
          </Paper>

          <Typography variant="subtitle1" gutterBottom>
            Current Permissions
          </Typography>

          {formPermissions.allowedDatabases.length === 0 ? (
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography color="text.secondary">No database permissions set</Typography>
            </Paper>
          ) : (
            formPermissions.allowedDatabases.map((permission, index) => (
              <Paper key={permission.dbId} sx={{ p: 2, mb: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="subtitle2">
                    {getDbNameById(permission.dbId)} ({permission.dbType})
                  </Typography>
                  <Button
                    size="small"
                    color="error"
                    onClick={() => handleRemovePermission(permission.dbId)}
                  >
                    Remove
                  </Button>
                </Box>
                <Divider sx={{ my: 1 }} />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Schemas:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {permission.allowedSchemas.map(schema => (
                      <Chip key={schema} label={schema} size="small" />
                    ))}
                  </Box>
                </Box>
                {permission.allowedTables.length > 0 && (
                  <Box mt={1}>
                    <Typography variant="body2" color="text.secondary">
                      Tables:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                      {permission.allowedTables.map(table => (
                        <Chip key={table} label={table} size="small" />
                      ))}
                    </Box>
                  </Box>
                )}
                {permission.allowedTables.length === 0 && (
                  <Typography variant="body2" color="text.secondary" mt={1}>
                    Access to all tables in selected schemas
                  </Typography>
                )}
              </Paper>
            ))
          )}

          <Box mt={3} display="flex" justifyContent="flex-end">
            <Button variant="contained" color="primary" onClick={handleSave}>
              Save Permissions
            </Button>
          </Box>
        </>
      )}
    </Box>
  );
};

export default UserPermissionsForm;
