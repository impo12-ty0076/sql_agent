import React from 'react';
import { Card, CardContent, Typography, Box, CircularProgress, ToggleButtonGroup, ToggleButton } from '@mui/material';
import { Line, Bar, Pie } from 'react-chartjs-2';
import { ChartData } from '../../services/adminService';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface ChartCardProps {
  title: string;
  chartData: ChartData | null;
  loading: boolean;
  error: string | null;
  chartType?: 'line' | 'bar' | 'pie';
  period: 'day' | 'week' | 'month';
  onPeriodChange: (period: 'day' | 'week' | 'month') => void;
  height?: number;
}

const ChartCard: React.FC<ChartCardProps> = ({
  title,
  chartData,
  loading,
  error,
  chartType = 'line',
  period,
  onPeriodChange,
  height = 300,
}) => {
  const handlePeriodChange = (
    event: React.MouseEvent<HTMLElement>,
    newPeriod: 'day' | 'week' | 'month' | null
  ) => {
    if (newPeriod !== null) {
      onPeriodChange(newPeriod);
    }
  };

  const renderChart = () => {
    if (loading) {
      return (
        <Box display="flex" justifyContent="center" alignItems="center" height={height}>
          <CircularProgress />
        </Box>
      );
    }

    if (error) {
      return (
        <Box display="flex" justifyContent="center" alignItems="center" height={height}>
          <Typography color="error">{error}</Typography>
        </Box>
      );
    }

    if (!chartData) {
      return (
        <Box display="flex" justifyContent="center" alignItems="center" height={height}>
          <Typography color="text.secondary">No data available</Typography>
        </Box>
      );
    }

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
        },
      },
    };

    switch (chartType) {
      case 'line':
        return <Line data={chartData} options={options} height={height} />;
      case 'bar':
        return <Bar data={chartData} options={options} height={height} />;
      case 'pie':
        return <Pie data={chartData} options={options} height={height} />;
      default:
        return <Line data={chartData} options={options} height={height} />;
    }
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1, pb: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">{title}</Typography>
          <ToggleButtonGroup
            size="small"
            value={period}
            exclusive
            onChange={handlePeriodChange}
            aria-label="time period"
          >
            <ToggleButton value="day" aria-label="day">
              Day
            </ToggleButton>
            <ToggleButton value="week" aria-label="week">
              Week
            </ToggleButton>
            <ToggleButton value="month" aria-label="month">
              Month
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
        <Box height={height}>{renderChart()}</Box>
      </CardContent>
    </Card>
  );
};

export default ChartCard;