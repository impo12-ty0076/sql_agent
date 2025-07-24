import React from 'react';
import {
  Box,
  Typography,
  Chip,
  Paper,
  Tooltip,
  IconButton,
  Collapse,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

const ConnectionStatus: React.FC = () => {
  const { selectedDatabase, tables, error } = useSelector((state: RootState) => state.db);
  const [expanded, setExpanded] = React.useState(false);

  const handleToggleExpand = () => {
    setExpanded(!expanded);
  };

  if (!selectedDatabase) {
    return (
      <Paper sx={{ p: 2, mb: 3, bgcolor: 'background.default' }}>
        <Typography variant="body2" color="text.secondary">
          데이터베이스를 선택하고 연결해주세요.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="subtitle1" sx={{ mr: 2 }}>
            연결 상태:
          </Typography>

          {selectedDatabase.connected ? (
            <Chip icon={<CheckCircleIcon />} label="연결됨" color="success" size="small" />
          ) : (
            <Chip icon={<ErrorIcon />} label="연결 안됨" color="error" size="small" />
          )}
        </Box>

        <Tooltip title="연결 정보">
          <IconButton size="small" onClick={handleToggleExpand}>
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Tooltip>
      </Box>

      <Collapse in={expanded}>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>데이터베이스:</strong> {selectedDatabase.name}
          </Typography>
          <Typography variant="body2">
            <strong>유형:</strong> {selectedDatabase.type}
          </Typography>
          {selectedDatabase.host && (
            <Typography variant="body2">
              <strong>호스트:</strong> {selectedDatabase.host}
              {selectedDatabase.port && `:${selectedDatabase.port}`}
            </Typography>
          )}

          {error && (
            <Box sx={{ mt: 1, p: 1, bgcolor: 'error.light', borderRadius: 1 }}>
              <Typography variant="body2" color="error.contrastText">
                <ErrorIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                {error}
              </Typography>
            </Box>
          )}

          {selectedDatabase.connected && tables.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                <InfoIcon fontSize="small" sx={{ mr: 1 }} />
                사용 가능한 테이블: {tables.length}개
              </Typography>

              {tables.length > 0 && (
                <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
                  {tables.slice(0, 5).map((table, index) => (
                    <ListItem key={index} sx={{ py: 0 }}>
                      <ListItemText
                        primary={table.name}
                        secondary={`${table.columns.length}개 컬럼`}
                        primaryTypographyProps={{ variant: 'body2' }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItem>
                  ))}
                  {tables.length > 5 && (
                    <ListItem sx={{ py: 0 }}>
                      <ListItemText
                        primary={`...외 ${tables.length - 5}개 테이블`}
                        primaryTypographyProps={{ variant: 'caption', color: 'text.secondary' }}
                      />
                    </ListItem>
                  )}
                </List>
              )}
            </Box>
          )}
        </Box>
      </Collapse>
    </Paper>
  );
};

export default ConnectionStatus;
