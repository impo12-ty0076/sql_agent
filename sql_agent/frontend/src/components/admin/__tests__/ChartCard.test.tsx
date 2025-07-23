import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ChartCard from '../ChartCard';
import { ChartData } from '../../../services/adminService';

// Mock Chart.js
jest.mock('chart.js');
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="mock-line-chart">Line Chart</div>,
  Bar: () => <div data-testid="mock-bar-chart">Bar Chart</div>,
  Pie: () => <div data-testid="mock-pie-chart">Pie Chart</div>,
}));

describe('ChartCard', () => {
  const mockChartData: ChartData = {
    labels: ['Jan', 'Feb', 'Mar'],
    datasets: [
      {
        label: 'Dataset 1',
        data: [10, 20, 30],
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgba(75, 192, 192, 1)',
      },
    ],
  };

  const mockOnPeriodChange = jest.fn();

  test('renders loading state', () => {
    render(
      <ChartCard
        title="Test Chart"
        chartData={null}
        loading={true}
        error={null}
        period="day"
        onPeriodChange={mockOnPeriodChange}
      />
    );
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('renders error state', () => {
    render(
      <ChartCard
        title="Test Chart"
        chartData={null}
        loading={false}
        error="Test error"
        period="day"
        onPeriodChange={mockOnPeriodChange}
      />
    );
    
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  test('renders empty state', () => {
    render(
      <ChartCard
        title="Test Chart"
        chartData={null}
        loading={false}
        error={null}
        period="day"
        onPeriodChange={mockOnPeriodChange}
      />
    );
    
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  test('renders line chart correctly', () => {
    render(
      <ChartCard
        title="Test Chart"
        chartData={mockChartData}
        loading={false}
        error={null}
        chartType="line"
        period="day"
        onPeriodChange={mockOnPeriodChange}
      />
    );
    
    expect(screen.getByText('Test Chart')).toBeInTheDocument();
    expect(screen.getByTestId('mock-line-chart')).toBeInTheDocument();
  });

  test('renders bar chart correctly', () => {
    render(
      <ChartCard
        title="Test Chart"
        chartData={mockChartData}
        loading={false}
        error={null}
        chartType="bar"
        period="day"
        onPeriodChange={mockOnPeriodChange}
      />
    );
    
    expect(screen.getByTestId('mock-bar-chart')).toBeInTheDocument();
  });

  test('renders pie chart correctly', () => {
    render(
      <ChartCard
        title="Test Chart"
        chartData={mockChartData}
        loading={false}
        error={null}
        chartType="pie"
        period="day"
        onPeriodChange={mockOnPeriodChange}
      />
    );
    
    expect(screen.getByTestId('mock-pie-chart')).toBeInTheDocument();
  });

  test('handles period change', () => {
    render(
      <ChartCard
        title="Test Chart"
        chartData={mockChartData}
        loading={false}
        error={null}
        period="day"
        onPeriodChange={mockOnPeriodChange}
      />
    );
    
    // Click on week button
    fireEvent.click(screen.getByRole('button', { name: 'week' }));
    
    expect(mockOnPeriodChange).toHaveBeenCalledWith('week');
  });
});