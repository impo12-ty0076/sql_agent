import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import NaturalLanguageQueryInput from '../NaturalLanguageQueryInput';
import { queryService } from '../../services/queryService';

// Mock the queryService
jest.mock('../../services/queryService', () => ({
  queryService: {
    processNaturalLanguage: jest.fn(),
    executeQuery: jest.fn()
  }
}));

// Create a simple mock store without middleware for testing
const mockStore = configureStore([]);

describe('NaturalLanguageQueryInput Component', () => {
  let store: any;
  const onQueryCompleteMock = jest.fn();
  
  beforeEach(() => {
    store = mockStore({
      query: {
        loading: false,
        error: null
      },
      db: {
        selectedDatabase: {
          id: 'db1',
          name: 'Test DB',
          connected: true
        }
      }
    });
    
    // Reset mocks
    jest.clearAllMocks();
  });
  
  it('renders the input form correctly', () => {
    render(
      <Provider store={store}>
        <NaturalLanguageQueryInput onQueryComplete={onQueryCompleteMock} />
      </Provider>
    );
    
    expect(screen.getByLabelText(/자연어 질의 입력/i)).toBeInTheDocument();
    expect(screen.getByText(/RAG 시스템 사용/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /질의하기/i })).toBeInTheDocument();
  });
  
  it('handles query submission and shows SQL review', async () => {
    const mockSqlResult = {
      queryId: 'query123',
      generatedSql: 'SELECT * FROM users',
      status: 'completed'
    };
    
    (queryService.processNaturalLanguage as jest.Mock).mockResolvedValue(mockSqlResult);
    
    render(
      <Provider store={store}>
        <NaturalLanguageQueryInput onQueryComplete={onQueryCompleteMock} />
      </Provider>
    );
    
    // Enter query text
    fireEvent.change(screen.getByLabelText(/자연어 질의 입력/i), {
      target: { value: '모든 사용자 정보를 보여줘' }
    });
    
    // Submit the query
    fireEvent.click(screen.getByRole('button', { name: /질의하기/i }));
    
    // Wait for SQL review to appear
    await waitFor(() => {
      expect(screen.getByText(/생성된 SQL:/i)).toBeInTheDocument();
      expect(screen.getByText('SELECT * FROM users')).toBeInTheDocument();
    });
    
    // Verify the service was called correctly
    expect(queryService.processNaturalLanguage).toHaveBeenCalledWith(
      'db1', 
      '모든 사용자 정보를 보여줘', 
      false
    );
  });
  
  it('allows SQL editing and execution', async () => {
    const mockSqlResult = {
      queryId: 'query123',
      generatedSql: 'SELECT * FROM users',
      status: 'completed'
    };
    
    const mockExecutionResult = {
      columns: [{ name: 'id', type: 'int' }, { name: 'name', type: 'varchar' }],
      rows: [[1, 'User 1'], [2, 'User 2']],
      rowCount: 2,
      executionTime: 0.1,
      truncated: false
    };
    
    (queryService.processNaturalLanguage as jest.Mock).mockResolvedValue(mockSqlResult);
    (queryService.executeQuery as jest.Mock).mockResolvedValue(mockExecutionResult);
    
    render(
      <Provider store={store}>
        <NaturalLanguageQueryInput onQueryComplete={onQueryCompleteMock} />
      </Provider>
    );
    
    // Enter query text and submit
    fireEvent.change(screen.getByLabelText(/자연어 질의 입력/i), {
      target: { value: '모든 사용자 정보를 보여줘' }
    });
    fireEvent.click(screen.getByRole('button', { name: /질의하기/i }));
    
    // Wait for SQL review to appear
    await waitFor(() => {
      expect(screen.getByText(/생성된 SQL:/i)).toBeInTheDocument();
    });
    
    // Click edit button
    fireEvent.click(screen.getByTitle(/SQL 편집/i));
    
    // Modify SQL
    const sqlEditor = screen.getByDisplayValue('SELECT * FROM users');
    fireEvent.change(sqlEditor, {
      target: { value: 'SELECT id, name FROM users WHERE active = 1' }
    });
    
    // Execute SQL
    fireEvent.click(screen.getByRole('button', { name: /SQL 실행/i }));
    
    // Verify execution
    await waitFor(() => {
      expect(queryService.executeQuery).toHaveBeenCalledWith(
        'db1', 
        'SELECT id, name FROM users WHERE active = 1'
      );
      expect(onQueryCompleteMock).toHaveBeenCalledWith(mockExecutionResult);
    });
  });
  
  it('toggles RAG system option', () => {
    render(
      <Provider store={store}>
        <NaturalLanguageQueryInput onQueryComplete={onQueryCompleteMock} />
      </Provider>
    );
    
    // Find and click the RAG toggle
    const ragToggle = screen.getByRole('checkbox', { name: /RAG 시스템 사용/i });
    expect(ragToggle).not.toBeChecked();
    
    fireEvent.click(ragToggle);
    expect(ragToggle).toBeChecked();
  });
  
  it('handles errors during query processing', async () => {
    (queryService.processNaturalLanguage as jest.Mock).mockRejectedValue(
      new Error('자연어 처리 중 오류가 발생했습니다.')
    );
    
    render(
      <Provider store={store}>
        <NaturalLanguageQueryInput onQueryComplete={onQueryCompleteMock} />
      </Provider>
    );
    
    // Enter query text and submit
    fireEvent.change(screen.getByLabelText(/자연어 질의 입력/i), {
      target: { value: '모든 사용자 정보를 보여줘' }
    });
    fireEvent.click(screen.getByRole('button', { name: /질의하기/i }));
    
    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/자연어 처리 중 오류가 발생했습니다./i)).toBeInTheDocument();
    });
  });
});