import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import Dashboard from '../Dashboard';
import { dbService } from '../../services/dbService';

// Mock the dbService
jest.mock('../../services/dbService', () => ({
  dbService: {
    connectToDatabase: jest.fn(),
  },
}));

describe('Dashboard Component', () => {
  let store: any;
  
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Setup mock store with initial state
    store = configureStore({
      reducer: () => ({
        db: {
          selectedDatabase: null,
          loading: false,
          error: null,
        }
      }),
      middleware: (getDefaultMiddleware) => 
        getDefaultMiddleware({
          thunk: {
            extraArgument: {},
          },
          serializableCheck: false,
        })
    });
  });

  test('renders dashboard title', () => {
    render(
      <Provider store={store}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByText('SQL DB LLM Agent')).toBeInTheDocument();
    expect(screen.getByText('대시보드')).toBeInTheDocument();
  });

  test('attempts to connect to last used database on mount', () => {
    // Setup localStorage with a last connected database ID
    localStorage.setItem('lastConnectedDbId', 'db123');
    
    render(
      <Provider store={store}>
        <Dashboard />
      </Provider>
    );
    
    expect(dbService.connectToDatabase).toHaveBeenCalledWith('db123');
  });

  test('shows error message when trying to submit query without database connection', () => {
    render(
      <Provider store={store}>
        <Dashboard />
      </Provider>
    );
    
    // Find the query input and enter some text
    const queryInput = screen.getByLabelText('질의 입력');
    fireEvent.change(queryInput, { target: { value: 'test query' } });
    
    // Find and click the submit button
    const submitButton = screen.getByRole('button', { name: '질의하기' });
    fireEvent.click(submitButton);
    
    // Check for error message
    expect(screen.getByText('데이터베이스에 연결되어 있지 않습니다. 먼저 데이터베이스를 선택하고 연결해주세요.')).toBeInTheDocument();
  });

  test('displays query results when database is connected', async () => {
    // Setup mock store with a connected database
    store = configureStore({
      reducer: () => ({
        db: {
          selectedDatabase: {
            id: 'db123',
            name: 'Test DB',
            connected: true,
          },
          loading: false,
          error: null,
        }
      }),
      middleware: (getDefaultMiddleware) => 
        getDefaultMiddleware({
          thunk: {
            extraArgument: {},
          },
          serializableCheck: false,
        })
    });
    
    render(
      <Provider store={store}>
        <Dashboard />
      </Provider>
    );
    
    // Find the query input and enter some text
    const queryInput = screen.getByLabelText('질의 입력');
    fireEvent.change(queryInput, { target: { value: 'test query' } });
    
    // Find and click the submit button
    const submitButton = screen.getByRole('button', { name: '질의하기' });
    fireEvent.click(submitButton);
    
    // Wait for the results to appear (after the setTimeout in handleQuerySubmit)
    await waitFor(() => {
      expect(screen.getByText('테이블')).toBeInTheDocument();
      expect(screen.getByText('요약')).toBeInTheDocument();
      expect(screen.getByText('리포트')).toBeInTheDocument();
    }, { timeout: 1500 });
  });

  test('changes tab when tab is clicked', async () => {
    // Setup mock store with a connected database and query results
    store = configureStore({
      reducer: () => ({
        db: {
          selectedDatabase: {
            id: 'db123',
            name: 'Test DB',
            connected: true,
          },
          loading: false,
          error: null,
        }
      }),
      middleware: (getDefaultMiddleware) => 
        getDefaultMiddleware({
          thunk: {
            extraArgument: {},
          },
          serializableCheck: false,
        })
    });
    
    render(
      <Provider store={store}>
        <Dashboard />
      </Provider>
    );
    
    // Find the query input and enter some text
    const queryInput = screen.getByLabelText('질의 입력');
    fireEvent.change(queryInput, { target: { value: 'test query' } });
    
    // Submit a query to get results
    const submitButton = screen.getByRole('button', { name: '질의하기' });
    fireEvent.click(submitButton);
    
    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText('테이블')).toBeInTheDocument();
    }, { timeout: 1500 });
    
    // Click on the summary tab
    const summaryTab = screen.getByText('요약');
    fireEvent.click(summaryTab);
    
    // Check that summary content is displayed
    expect(screen.getByText('총 2명의 사용자가 조회되었습니다. 사용자 ID, 사용자명, 이메일 정보가 포함되어 있습니다.')).toBeInTheDocument();
  });
});