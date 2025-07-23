import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import configureStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import PolicyManagement from '../PolicyManagement';

// Mock the PolicyTable component
jest.mock('../../../components/admin/PolicyTable', () => {
  return function MockPolicyTable({ policies, loading, filter, onFilterChange, onDeletePolicy }) {
    return (
      <div data-testid="policy-table">
        <div>Policies: {policies.length}</div>
        <div>Loading: {loading.toString()}</div>
        <div>Filter: {JSON.stringify(filter)}</div>
        <button onClick={() => onFilterChange({ searchTerm: 'test' })}>Change Filter</button>
        <button onClick={() => onDeletePolicy('1')}>Delete Policy</button>
      </div>
    );
  };
});

const middlewares = [thunk];
const mockStore = configureStore(middlewares);

describe('PolicyManagement Component', () => {
  let store;

  beforeEach(() => {
    store = mockStore({
      admin: {
        policies: {
          data: [
            {
              id: '1',
              name: 'Default Policy',
              description: 'Default query limits',
              settings: {
                maxQueriesPerDay: 100,
                maxQueryExecutionTime: 60,
                maxResultSize: 10000,
                allowedQueryTypes: ['SELECT'],
                blockedKeywords: [],
              },
              appliedToUsers: 5,
            },
            {
              id: '2',
              name: 'Admin Policy',
              description: 'Admin query limits',
              settings: {
                maxQueriesPerDay: 500,
                maxQueryExecutionTime: 300,
                maxResultSize: 50000,
                allowedQueryTypes: ['SELECT', 'SHOW'],
                blockedKeywords: [],
              },
              appliedToUsers: 2,
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

  test('renders policy management page', () => {
    render(
      <Provider store={store}>
        <BrowserRouter>
          <PolicyManagement />
        </BrowserRouter>
      </Provider>
    );

    expect(screen.getByText('Policy Management')).toBeInTheDocument();
    expect(screen.getByText('Manage query limit policies and restrictions')).toBeInTheDocument();
    expect(screen.getByTestId('policy-table')).toBeInTheDocument();
  });

  test('dispatches fetchPolicies on mount', () => {
    render(
      <Provider store={store}>
        <BrowserRouter>
          <PolicyManagement />
        </BrowserRouter>
      </Provider>
    );

    expect(store.dispatch).toHaveBeenCalled();
  });

  test('opens delete confirmation dialog when delete is clicked', () => {
    render(
      <Provider store={store}>
        <BrowserRouter>
          <PolicyManagement />
        </BrowserRouter>
      </Provider>
    );

    // Click the delete button in the mocked PolicyTable
    fireEvent.click(screen.getByText('Delete Policy'));
    
    // Check if the confirmation dialog is shown
    expect(screen.getByText('Confirm Delete')).toBeInTheDocument();
    expect(screen.getByText('Are you sure you want to delete this policy? This action cannot be undone.')).toBeInTheDocument();
  });

  test('dispatches deletePolicy when confirmation is confirmed', () => {
    render(
      <Provider store={store}>
        <BrowserRouter>
          <PolicyManagement />
        </BrowserRouter>
      </Provider>
    );

    // Click the delete button in the mocked PolicyTable
    fireEvent.click(screen.getByText('Delete Policy'));
    
    // Click the confirm button in the dialog
    fireEvent.click(screen.getByText('Delete'));
    
    // Check if deletePolicy was dispatched
    expect(store.dispatch).toHaveBeenCalledTimes(2); // Once for fetchPolicies on mount, once for deletePolicy
  });
});