import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ApiKeyTable from '../ApiKeyTable';
import { ApiKey } from '../../../types/systemSettings';

const mockApiKeys: ApiKey[] = [
  {
    id: '1',
    name: 'OpenAI Key',
    service: 'openai',
    lastFourDigits: '1234',
    createdAt: new Date('2023-01-01'),
    status: 'active',
  },
  {
    id: '2',
    name: 'Azure OpenAI Key',
    service: 'azure_openai',
    lastFourDigits: '5678',
    createdAt: new Date('2023-01-01'),
    expiresAt: new Date('2024-01-01'),
    status: 'expired',
  },
];

const mockProps = {
  apiKeys: mockApiKeys,
  loading: false,
  onEdit: jest.fn(),
  onDelete: jest.fn(),
  onRevoke: jest.fn(),
  onFilterChange: jest.fn(),
  filter: {},
  totalCount: 2,
  page: 0,
  rowsPerPage: 10,
  onPageChange: jest.fn(),
  onRowsPerPageChange: jest.fn(),
};

describe('ApiKeyTable', () => {
  it('renders API key table with data', () => {
    render(<ApiKeyTable {...mockProps} />);

    // Check if table headers are rendered
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Service')).toBeInTheDocument();
    expect(screen.getByText('Key')).toBeInTheDocument();
    expect(screen.getByText('Created')).toBeInTheDocument();

    // Check if API key data is rendered
    expect(screen.getByText('OpenAI Key')).toBeInTheDocument();
    expect(screen.getByText('OpenAI')).toBeInTheDocument();
    expect(screen.getByText('Azure OpenAI Key')).toBeInTheDocument();
    expect(screen.getByText('Azure OpenAI')).toBeInTheDocument();

    // Check if masked keys are displayed
    const maskedKeys = screen.getAllByText(/•••• •••• •••• \d{4}/);
    expect(maskedKeys.length).toBe(2);
  });

  it('shows loading state', () => {
    render(<ApiKeyTable {...mockProps} loading={true} />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('shows empty state', () => {
    render(<ApiKeyTable {...mockProps} apiKeys={[]} />);
    expect(screen.getByText('No API keys found')).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    render(<ApiKeyTable {...mockProps} />);
    const editButtons = screen.getAllByLabelText('Edit');
    fireEvent.click(editButtons[0]);
    expect(mockProps.onEdit).toHaveBeenCalledWith(mockApiKeys[0]);
  });

  it('calls onDelete when delete button is clicked', () => {
    render(<ApiKeyTable {...mockProps} />);
    const deleteButtons = screen.getAllByLabelText('Delete');
    fireEvent.click(deleteButtons[0]);
    expect(mockProps.onDelete).toHaveBeenCalledWith(mockApiKeys[0]);
  });

  it('calls onRevoke when revoke button is clicked', () => {
    render(<ApiKeyTable {...mockProps} />);
    const revokeButtons = screen.getAllByLabelText('Revoke');
    fireEvent.click(revokeButtons[0]);
    expect(mockProps.onRevoke).toHaveBeenCalledWith(mockApiKeys[0]);
  });

  it('calls onFilterChange when search is submitted', () => {
    render(<ApiKeyTable {...mockProps} />);
    const searchInput = screen.getByLabelText('Search');
    fireEvent.change(searchInput, { target: { value: 'openai' } });

    const searchButton = screen.getByLabelText('Search');
    fireEvent.click(searchButton);

    expect(mockProps.onFilterChange).toHaveBeenCalledWith({ searchTerm: 'openai' });
  });

  it('calls onFilterChange when service filter is changed', () => {
    render(<ApiKeyTable {...mockProps} />);
    const serviceSelect = screen.getByLabelText('Service');
    fireEvent.mouseDown(serviceSelect);

    const openaiOption = screen.getByText('OpenAI');
    fireEvent.click(openaiOption);

    expect(mockProps.onFilterChange).toHaveBeenCalledWith({ service: 'openai' });
  });
});
