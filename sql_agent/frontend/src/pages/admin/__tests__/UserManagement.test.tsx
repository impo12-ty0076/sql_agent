import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import configureStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import UserManagement from '../UserManagement';

// Mock the UserTable component
jest.mock('../../../components/admin/UserTable', () => {
  return function MockUserTable({ users, loading, filter, onFilterChange }) {
    return (
      <div data-testid="user-table">
        <div>Users: {users.length}</div>
        <div>Loading: {loading.toString()}</div>
        <div>Filter: {JSON.stringify(filter)}</div>
        <button onClick={() => onFilterChange({ searchTerm: 'test' })}>Change Filter</button>
      </div>
    );
  };
});

const middlewares = [thunk];
const mockStore = configureStore(middlewares);

describe('UserManagement Component', () => {
  let store;

  beforeEach(() => {
    store = mockStore({
      admin: {
        users: {
          data: [
            {
              id: '1',
              username: 'testuser',
              email: 'test@example.com',
              role: 'user',
              status: 'active',
            },
            {
              id: '2',
              username: 'adminuser',
              email: 'admin@example.com',
              role: 'admin',
              status: 'active',
            },
          ],
          loading: false,
          error: null,
          filter: {},
        },
      },
    });

    // Mock dispatch function
    store.dispatch = jest.fn();
  });

  test('renders user management page', () => {
    render(
      <Provider store={store}>
        <BrowserRouter>
          <UserManagement />
        </BrowserRouter>
      </Provider>
    );

    expect(screen.getByText('User Management')).toBeInTheDocument();
    expect(screen.getByText('Manage users, roles, and permissions')).toBeInTheDocument();
    expect(screen.getByTestId('user-table')).toBeInTheDocument();
  });

  test('dispatches fetchUsers on mount', () => {
    render(
      <Provider store={store}>
        <BrowserRouter>
          <UserManagement />
        </BrowserRouter>
      </Provider>
    );

    expect(store.dispatch).toHaveBeenCalled();
  });
});