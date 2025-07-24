import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import LogsTable from '../LogsTable';
import { LogEntry, LogFilter } from '../../../services/adminService';

// Mock the DatePicker component to avoid test issues
jest.mock('@mui/x-date-pickers/DatePicker', () => ({
  DatePicker: ({ label, onChange }: any) => (
    <input
      type="text"
      placeholder={label}
      onChange={e => onChange(new Date(e.target.value))}
      data-testid={`mock-date-picker-${label.replace(/\s+/g, '-').toLowerCase()}`}
    />
  ),
}));

describe('LogsTable', () => {
  const mockLogs: LogEntry[] = [
    {
      id: '1',
      timestamp: '2025-07-23T10:00:00Z',
      level: 'info',
      category: 'auth',
      message: 'User logged in',
      userId: 'user123',
      details: { ip: '192.168.1.1', browser: 'Chrome' },
    },
    {
      id: '2',
      timestamp: '2025-07-23T10:05:00Z',
      level: 'error',
      category: 'query',
      message: 'Query execution failed',
      userId: 'user456',
      details: { error: 'Syntax error', query: 'SELECT * FROM' },
    },
  ];

  const mockFilter: LogFilter = {};
  const mockOnFilterChange = jest.fn();

  test('renders loading state', () => {
    render(
      <LogsTable
        logs={[]}
        loading={true}
        error={null}
        filter={mockFilter}
        onFilterChange={mockOnFilterChange}
      />
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('renders error state', () => {
    render(
      <LogsTable
        logs={[]}
        loading={false}
        error="Test error"
        filter={mockFilter}
        onFilterChange={mockOnFilterChange}
      />
    );

    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  test('renders empty state', () => {
    render(
      <LogsTable
        logs={[]}
        loading={false}
        error={null}
        filter={mockFilter}
        onFilterChange={mockOnFilterChange}
      />
    );

    expect(screen.getByText('No logs found')).toBeInTheDocument();
  });

  test('renders logs correctly', () => {
    render(
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <LogsTable
          logs={mockLogs}
          loading={false}
          error={null}
          filter={mockFilter}
          onFilterChange={mockOnFilterChange}
        />
      </LocalizationProvider>
    );

    // Check table headers
    expect(screen.getByText('Timestamp')).toBeInTheDocument();
    expect(screen.getByText('Level')).toBeInTheDocument();
    expect(screen.getByText('Category')).toBeInTheDocument();
    expect(screen.getByText('Message')).toBeInTheDocument();
    expect(screen.getByText('User ID')).toBeInTheDocument();

    // Check log entries
    expect(screen.getByText('User logged in')).toBeInTheDocument();
    expect(screen.getByText('Query execution failed')).toBeInTheDocument();
    expect(screen.getByText('INFO')).toBeInTheDocument();
    expect(screen.getByText('ERROR')).toBeInTheDocument();
    expect(screen.getByText('auth')).toBeInTheDocument();
    expect(screen.getByText('query')).toBeInTheDocument();
    expect(screen.getByText('user123')).toBeInTheDocument();
    expect(screen.getByText('user456')).toBeInTheDocument();
  });

  test('toggles filter visibility', () => {
    render(
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <LogsTable
          logs={mockLogs}
          loading={false}
          error={null}
          filter={mockFilter}
          onFilterChange={mockOnFilterChange}
        />
      </LocalizationProvider>
    );

    // Initially filters should be hidden
    expect(screen.getByText('Show Filters')).toBeInTheDocument();

    // Click to show filters
    fireEvent.click(screen.getByText('Show Filters'));

    // Now filters should be visible and button text changed
    expect(screen.getByText('Hide Filters')).toBeInTheDocument();
    expect(screen.getByText('Log Level')).toBeInTheDocument();
    expect(screen.getByText('Category')).toBeInTheDocument();

    // Click to hide filters
    fireEvent.click(screen.getByText('Hide Filters'));

    // Filters should be hidden again
    expect(screen.getByText('Show Filters')).toBeInTheDocument();
  });

  test('expands log details', () => {
    render(
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <LogsTable
          logs={mockLogs}
          loading={false}
          error={null}
          filter={mockFilter}
          onFilterChange={mockOnFilterChange}
        />
      </LocalizationProvider>
    );

    // Initially details should be hidden
    expect(screen.queryByText('Details')).not.toBeInTheDocument();

    // Click to expand first log
    const expandButtons = screen.getAllByRole('button', { name: 'expand row' });
    fireEvent.click(expandButtons[0]);

    // Now details should be visible
    expect(screen.getByText('Details')).toBeInTheDocument();
    expect(screen.getByText(/"ip": "192.168.1.1"/)).toBeInTheDocument();
    expect(screen.getByText(/"browser": "Chrome"/)).toBeInTheDocument();
  });
});
