import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import UserTable from '../UserTable';
import { User } from '../../../types/admin';

// Mock navigate function
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}));

describe('UserTable Component', () => {
  const mockUsers: User[] = [
    {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      role: 'user',
      status: 'active',
      lastLogin: new Date('2023-01-01'),
      createdAt: new Date('2022-01-01'),
      updatedAt: new Date('2022-01-01'),
      permissions: {
        allowedDatabases: [],
      },
    },
    {
      id: '2',
      username: 'adminuser',
      email: 'admin@example.com',
      role: 'admin',
      status: 'active',
      lastLogin: new Date('2023-01-02'),
      createdAt: new Date('2022-01-02'),
      updatedAt: new Date('2022-01-02'),
      permissions: {
        allowedDatabases: [],
      },
    },
  ];

  const mockFilterChange = jest.fn();

  test('renders user table with data', () => {
    render(
      <BrowserRouter>
        <UserTable
          users={mockUsers}
          loading={false}
          filter={{}}
          onFilterChange={mockFilterChange}
        />
      </BrowserRouter>
    );

    // Check if users are displayed
    expect(screen.getByText('testuser')).toBeInTheDocument();
    expect(screen.getByText('adminuser')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByText('admin@example.com')).toBeInTheDocument();
  });

  test('renders loading state', () => {
    render(
      <BrowserRouter>
        <UserTable
          users={[]}
          loading={true}
          filter={{}}
          onFilterChange={mockFilterChange}
        />
      </BrowserRouter>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('renders empty state', () => {
    render(
      <BrowserRouter>
        <UserTable
          users={[]}
          loading={false}
          filter={{}}
          onFilterChange={mockFilterChange}
        />
      </BrowserRouter>
    );

    expect(screen.getByText('No users found')).toBeInTheDocument();
  });

  test('handles search filter change', () => {
    render(
      <BrowserRouter>
        <UserTable
          users={mockUsers}
          loading={false}
          filter={{}}
          onFilterChange={mockFilterChange}
        />
      </BrowserRouter>
    );

    const searchInput = screen.getByLabelText('Search Users');
    fireEvent.change(searchInput, { target: { value: 'admin' } });
    
    expect(mockFilterChange).toHaveBeenCalledWith({ searchTerm: 'admin' });
  });
});