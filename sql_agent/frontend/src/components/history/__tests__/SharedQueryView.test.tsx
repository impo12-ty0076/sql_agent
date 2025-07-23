import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import SharedQueryView from '../SharedQueryView';
import api from '../../../services/api';

// Mock the API
jest.mock('../../../services/api', () => ({
  get: jest.fn(),
  post: jest.fn()
}));

const mockStore = configureStore();

describe('SharedQueryView', () => {
  let store: any;
  
  beforeEach(() => {
    store = mockStore({});
    
    // Reset mocks
    jest.mocked(api.get).mockReset();
    jest.mocked(api.post).mockReset();
  });
  
  it('renders loading state correctly', () => {
    jest.mocked(api.get).mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(
      <Provider store={store}>
        <SharedQueryView shareId="123" token="abc123" />
      </Provider>
    );
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
  
  it('renders error state correctly', async () => {
    jest.mocked(api.get).mockRejectedValue({
      response: { data: { message: 'Invalid share link' } }
    });
    
    render(
      <Provider store={store}>
        <SharedQueryView shareId="123" token="abc123" />
      </Provider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Invalid share link')).toBeInTheDocument();
    });
  });
  
  it('renders query details correctly', async () => {
    const mockQueryDetails = {
      id: "456",
      natural_language: "Show me sales data for last month",
      generated_sql: "SELECT * FROM sales WHERE date >= '2023-01-01' AND date <= '2023-01-31'",
      created_at: "2023-01-01T12:00:00Z",
      updated_at: "2023-01-01T12:00:00Z"
    };
    
    const mockShareDetails = {
      created_by: "user@example.com",
      created_at: "2023-01-01T12:00:00Z",
      expires_at: "2023-12-31T23:59:59Z"
    };
    
    jest.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes('/api/query-history/shared/')) {
        return Promise.resolve({
          data: {
            query_details: mockQueryDetails,
            share_details: mockShareDetails
          }
        });
      }
      return Promise.reject(new Error('Unexpected URL'));
    });
    
    render(
      <Provider store={store}>
        <SharedQueryView shareId="123" token="abc123" />
      </Provider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('공유된 쿼리')).toBeInTheDocument();
      expect(screen.getByText('공유자: user@example.com')).toBeInTheDocument();
      expect(screen.getByText(/공유일: 2023년 01월 01일/)).toBeInTheDocument();
      expect(screen.getByText(/만료일: 2023년 12월 31일/)).toBeInTheDocument();
      expect(screen.getByText('Show me sales data for last month')).toBeInTheDocument();
      expect(screen.getByText("SELECT * FROM sales WHERE date >= '2023-01-01' AND date <= '2023-01-31'")).toBeInTheDocument();
    });
  });
  
  it('renders query results correctly', async () => {
    const mockQueryDetails = {
      id: "456",
      natural_language: "Show me sales data",
      generated_sql: "SELECT * FROM sales LIMIT 10",
      result: "result-id-789",
      created_at: "2023-01-01T12:00:00Z",
      updated_at: "2023-01-01T12:00:00Z"
    };
    
    const mockShareDetails = {
      created_by: "user@example.com",
      created_at: "2023-01-01T12:00:00Z"
    };
    
    const mockQueryResult = {
      columns: [
        { name: "id", type: "INTEGER" },
        { name: "product", type: "VARCHAR" },
        { name: "amount", type: "DECIMAL" }
      ],
      rows: [
        [1, "Product A", 100.50],
        [2, "Product B", 200.75]
      ],
      rowCount: 2,
      totalRowCount: 2,
      summary: "2 sales records found"
    };
    
    jest.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes('/api/query-history/shared/') && !url.includes('/result')) {
        return Promise.resolve({
          data: {
            query_details: mockQueryDetails,
            share_details: mockShareDetails
          }
        });
      } else if (url.includes('/api/query-history/shared/') && url.includes('/result')) {
        return Promise.resolve({
          data: mockQueryResult
        });
      }
      return Promise.reject(new Error('Unexpected URL'));
    });
    
    render(
      <Provider store={store}>
        <SharedQueryView shareId="123" token="abc123" />
      </Provider>
    );
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('공유된 쿼리')).toBeInTheDocument();
    });
    
    // Click on the Results tab
    fireEvent.click(screen.getByText('결과'));
    
    await waitFor(() => {
      expect(screen.getByText('2 sales records found')).toBeInTheDocument();
      expect(screen.getByText('id')).toBeInTheDocument();
      expect(screen.getByText('product')).toBeInTheDocument();
      expect(screen.getByText('amount')).toBeInTheDocument();
      expect(screen.getByText('Product A')).toBeInTheDocument();
      expect(screen.getByText('100.5')).toBeInTheDocument();
      expect(screen.getByText('Product B')).toBeInTheDocument();
      expect(screen.getByText('200.75')).toBeInTheDocument();
    });
  });
  
  it('copies SQL to clipboard when copy button is clicked', async () => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn()
      }
    });
    
    const mockQueryDetails = {
      id: "456",
      natural_language: "Show me sales data",
      generated_sql: "SELECT * FROM sales LIMIT 10",
      created_at: "2023-01-01T12:00:00Z",
      updated_at: "2023-01-01T12:00:00Z"
    };
    
    const mockShareDetails = {
      created_by: "user@example.com",
      created_at: "2023-01-01T12:00:00Z"
    };
    
    jest.mocked(api.get).mockResolvedValue({
      data: {
        query_details: mockQueryDetails,
        share_details: mockShareDetails
      }
    });
    
    render(
      <Provider store={store}>
        <SharedQueryView shareId="123" token="abc123" />
      </Provider>
    );
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('공유된 쿼리')).toBeInTheDocument();
    });
    
    // Click on the SQL tab
    fireEvent.click(screen.getByText('SQL'));
    
    // Click the copy button
    fireEvent.click(screen.getByText('SQL 복사'));
    
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith("SELECT * FROM sales LIMIT 10");
  });
  
  it('calls clone API when clone button is clicked', async () => {
    jest.mocked(api.post).mockResolvedValue({ data: { success: true } });
    
    const mockQueryDetails = {
      id: "456",
      natural_language: "Show me sales data",
      generated_sql: "SELECT * FROM sales LIMIT 10",
      created_at: "2023-01-01T12:00:00Z",
      updated_at: "2023-01-01T12:00:00Z"
    };
    
    const mockShareDetails = {
      created_by: "user@example.com",
      created_at: "2023-01-01T12:00:00Z"
    };
    
    jest.mocked(api.get).mockResolvedValue({
      data: {
        query_details: mockQueryDetails,
        share_details: mockShareDetails
      }
    });
    
    render(
      <Provider store={store}>
        <SharedQueryView shareId="123" token="abc123" />
      </Provider>
    );
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('공유된 쿼리')).toBeInTheDocument();
    });
    
    // Click the clone button
    fireEvent.click(screen.getByText('내 쿼리로 복제'));
    
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/query-history/clone', {
        query_id: "456"
      });
    });
  });
});