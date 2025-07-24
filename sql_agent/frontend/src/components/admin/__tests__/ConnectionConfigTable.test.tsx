import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ConnectionConfigTable from '../ConnectionConfigTable';
import { ConnectionConfig } from '../../../types/systemSettings';

const mockConnections: ConnectionConfig[] = [
  {
    id: '1',
    name: 'Test DB 1',
    type: 'mssql',
    host: 'localhost',
    port: 1433,
    username: 'sa',
    passwordLastUpdated: new Date('2023-01-01'),
    defaultSchema: 'dbo',
    options: {},
    createdAt: new Date('2023-01-01'),
    updatedAt: new Date('2023-01-01'),
    status: 'active',
  },
  {
    id: '2',
    name: 'Test DB 2',
    type: 'hana',
    host: 'hanaserver',
    port: 30015,
    username: 'SYSTEM',
    passwordLastUpdated: new Date('2023-01-01'),
    defaultSchema: 'SYSTEM',
    options: {},
    createdAt: new Date('2023-01-01'),
    updatedAt: new Date('2023-01-01'),
    status: 'inactive',
  },
];

const mockProps = {
  connections: mockConnections,
  loading: false,
  onEdit: jest.fn(),
  onDelete: jest.fn(),
  onTest: jest.fn(),
  onFilterChange: jest.fn(),
  filter: {},
  totalCount: 2,
  page: 0,
  rowsPerPage: 10,
  onPageChange: jest.fn(),
  onRowsPerPageChange: jest.fn(),
};

describe('ConnectionConfigTable', () => {
  it('renders connection table with data', () => {
    render(<ConnectionConfigTable {...mockProps} />);

    // Check if table headers are rendered
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Type')).toBeInTheDocument();
    expect(screen.getByText('Host')).toBeInTheDocument();
    expect(screen.getByText('Port')).toBeInTheDocument();

    // Check if connection data is rendered
    expect(screen.getByText('Test DB 1')).toBeInTheDocument();
    expect(screen.getByText('localhost')).toBeInTheDocument();
    expect(screen.getByText('1433')).toBeInTheDocument();
    expect(screen.getByText('Test DB 2')).toBeInTheDocument();
    expect(screen.getByText('hanaserver')).toBeInTheDocument();
    expect(screen.getByText('30015')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<ConnectionConfigTable {...mockProps} loading={true} />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('shows empty state', () => {
    render(<ConnectionConfigTable {...mockProps} connections={[]} />);
    expect(screen.getByText('No connection configurations found')).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    render(<ConnectionConfigTable {...mockProps} />);
    const editButtons = screen.getAllByLabelText('Edit');
    fireEvent.click(editButtons[0]);
    expect(mockProps.onEdit).toHaveBeenCalledWith(mockConnections[0]);
  });

  it('calls onDelete when delete button is clicked', () => {
    render(<ConnectionConfigTable {...mockProps} />);
    const deleteButtons = screen.getAllByLabelText('Delete');
    fireEvent.click(deleteButtons[0]);
    expect(mockProps.onDelete).toHaveBeenCalledWith(mockConnections[0]);
  });

  it('calls onTest when test button is clicked', () => {
    render(<ConnectionConfigTable {...mockProps} />);
    const testButtons = screen.getAllByLabelText('Test Connection');
    fireEvent.click(testButtons[0]);
    expect(mockProps.onTest).toHaveBeenCalledWith(mockConnections[0]);
  });

  it('calls onFilterChange when search is submitted', () => {
    render(<ConnectionConfigTable {...mockProps} />);
    const searchInput = screen.getByLabelText('Search');
    fireEvent.change(searchInput, { target: { value: 'test' } });

    const searchButton = screen.getByLabelText('Search');
    fireEvent.click(searchButton);

    expect(mockProps.onFilterChange).toHaveBeenCalledWith({ searchTerm: 'test' });
  });

  it('calls onFilterChange when type filter is changed', () => {
    render(<ConnectionConfigTable {...mockProps} />);
    const typeSelect = screen.getByLabelText('Database Type');
    fireEvent.mouseDown(typeSelect);

    const mssqlOption = screen.getByText('MS-SQL');
    fireEvent.click(mssqlOption);

    expect(mockProps.onFilterChange).toHaveBeenCalledWith({ type: 'mssql' });
  });
});
