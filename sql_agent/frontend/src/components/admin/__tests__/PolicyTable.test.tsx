import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import PolicyTable from '../PolicyTable';
import { Policy } from '../../../types/admin';

// Mock navigate function
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}));

describe('PolicyTable Component', () => {
  const mockPolicies: Policy[] = [
    {
      id: '1',
      name: 'Default Policy',
      description: 'Default query limits for regular users',
      settings: {
        maxQueriesPerDay: 100,
        maxQueryExecutionTime: 60,
        maxResultSize: 10000,
        allowedQueryTypes: ['SELECT'],
        blockedKeywords: ['DROP', 'DELETE'],
      },
      createdAt: new Date('2022-01-01'),
      updatedAt: new Date('2022-01-01'),
      appliedToUsers: 10,
    },
    {
      id: '2',
      name: 'Admin Policy',
      description: 'Extended limits for administrators',
      settings: {
        maxQueriesPerDay: 500,
        maxQueryExecutionTime: 300,
        maxResultSize: 50000,
        allowedQueryTypes: ['SELECT', 'SHOW'],
        blockedKeywords: [],
      },
      createdAt: new Date('2022-01-02'),
      updatedAt: new Date('2022-01-02'),
      appliedToUsers: 2,
    },
  ];

  const mockFilterChange = jest.fn();
  const mockDeletePolicy = jest.fn();

  test('renders policy table with data', () => {
    render(
      <BrowserRouter>
        <PolicyTable
          policies={mockPolicies}
          loading={false}
          filter={{}}
          onFilterChange={mockFilterChange}
          onDeletePolicy={mockDeletePolicy}
        />
      </BrowserRouter>
    );

    // Check if policies are displayed
    expect(screen.getByText('Default Policy')).toBeInTheDocument();
    expect(screen.getByText('Admin Policy')).toBeInTheDocument();
    expect(screen.getByText('Default query limits for regular users')).toBeInTheDocument();
    expect(screen.getByText('Extended limits for administrators')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('500')).toBeInTheDocument();
  });

  test('renders loading state', () => {
    render(
      <BrowserRouter>
        <PolicyTable
          policies={[]}
          loading={true}
          filter={{}}
          onFilterChange={mockFilterChange}
          onDeletePolicy={mockDeletePolicy}
        />
      </BrowserRouter>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('renders empty state', () => {
    render(
      <BrowserRouter>
        <PolicyTable
          policies={[]}
          loading={false}
          filter={{}}
          onFilterChange={mockFilterChange}
          onDeletePolicy={mockDeletePolicy}
        />
      </BrowserRouter>
    );

    expect(screen.getByText('No policies found')).toBeInTheDocument();
  });

  test('handles search filter change', () => {
    render(
      <BrowserRouter>
        <PolicyTable
          policies={mockPolicies}
          loading={false}
          filter={{}}
          onFilterChange={mockFilterChange}
          onDeletePolicy={mockDeletePolicy}
        />
      </BrowserRouter>
    );

    const searchInput = screen.getByLabelText('Search Policies');
    fireEvent.change(searchInput, { target: { value: 'admin' } });

    expect(mockFilterChange).toHaveBeenCalledWith({ searchTerm: 'admin' });
  });

  test('calls delete function when delete button is clicked', () => {
    render(
      <BrowserRouter>
        <PolicyTable
          policies={mockPolicies}
          loading={false}
          filter={{}}
          onFilterChange={mockFilterChange}
          onDeletePolicy={mockDeletePolicy}
        />
      </BrowserRouter>
    );

    // Find all delete buttons and click the first one
    const deleteButtons = screen.getAllByTitle('Delete Policy');
    fireEvent.click(deleteButtons[0]);

    expect(mockDeletePolicy).toHaveBeenCalledWith('1');
  });
});
