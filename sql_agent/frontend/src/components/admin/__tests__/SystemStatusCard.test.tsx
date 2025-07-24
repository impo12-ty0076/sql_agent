import React from 'react';
import { render, screen } from '@testing-library/react';
import SystemStatusCard from '../SystemStatusCard';
import { SystemStatus } from '../../../services/adminService';

describe('SystemStatusCard', () => {
  const mockStatus: SystemStatus = {
    status: 'healthy',
    components: {
      database: 'healthy',
      api: 'healthy',
      llm: 'degraded',
      storage: 'healthy',
    },
    uptime: 86400, // 1 day in seconds
    lastChecked: '2025-07-23T12:00:00Z',
  };

  test('renders loading state', () => {
    render(<SystemStatusCard status={null} loading={true} error={null} />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('renders error state', () => {
    render(<SystemStatusCard status={null} loading={false} error="Test error" />);

    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  test('renders empty state', () => {
    render(<SystemStatusCard status={null} loading={false} error={null} />);

    expect(screen.getByText('No status data available')).toBeInTheDocument();
  });

  test('renders system status correctly', () => {
    render(<SystemStatusCard status={mockStatus} loading={false} error={null} />);

    // Check title and status
    expect(screen.getByText('System Status')).toBeInTheDocument();
    expect(screen.getByText('HEALTHY')).toBeInTheDocument();

    // Check uptime
    expect(screen.getByText('Uptime')).toBeInTheDocument();
    expect(screen.getByText('1d 0h 0m')).toBeInTheDocument();

    // Check last checked
    expect(screen.getByText('Last Checked')).toBeInTheDocument();

    // Check component statuses
    expect(screen.getByText('Component Status')).toBeInTheDocument();
    expect(screen.getByText('Database')).toBeInTheDocument();
    expect(screen.getByText('Api')).toBeInTheDocument();
    expect(screen.getByText('Llm')).toBeInTheDocument();
    expect(screen.getByText('Storage')).toBeInTheDocument();
  });

  test('renders different status colors', () => {
    const degradedStatus: SystemStatus = {
      ...mockStatus,
      status: 'degraded',
    };

    render(<SystemStatusCard status={degradedStatus} loading={false} error={null} />);

    expect(screen.getByText('DEGRADED')).toBeInTheDocument();
  });
});
