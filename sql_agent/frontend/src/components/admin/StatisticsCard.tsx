import React from 'react';
import { Card, CardContent, Typography, Box, CircularProgress, Tooltip } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';

interface StatisticsCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  loading?: boolean;
  color?: string;
}

const StatisticsCard: React.FC<StatisticsCardProps> = ({
  title,
  value,
  description,
  icon,
  loading = false,
  color = 'primary.main',
}) => {
  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography variant="subtitle2" color="text.secondary">
            {title}
            {description && (
              <Tooltip title={description} arrow placement="top">
                <InfoIcon
                  fontSize="small"
                  sx={{ ml: 0.5, fontSize: '1rem', verticalAlign: 'middle' }}
                />
              </Tooltip>
            )}
          </Typography>
          {icon && <Box color={color}>{icon}</Box>}
        </Box>
        <Box display="flex" alignItems="center" height={60}>
          {loading ? (
            <CircularProgress size={24} />
          ) : (
            <Typography variant="h4" component="div" color={color} fontWeight="bold">
              {value}
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default StatisticsCard;
