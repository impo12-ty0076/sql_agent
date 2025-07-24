import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ResultTableExample from '../examples/ResultTableExample';

// Mock EnhancedResultTable component to simplify testing
jest.mock('../EnhancedResultTable', () => {
  return ({ columns, rows, rowCount, loading, error, onRefresh, onRowClick }: any) => (
    <div data-testid="enhanced-result-table">
      <div data-testid="columns">{JSON.stringify(columns)}</div>
      <div data-testid="row-count">{rowCount}</div>
      <div data-testid="loading">{loading ? 'true' : 'false'}</div>
      {error && <div data-testid="error">{error}</div>}
      {onRefresh && (
        <button data-testid="refresh-button" onClick={onRefresh}>
          Refresh
        </button>
      )}
      {rows.length > 0 && (
        <div data-testid="first-row" onClick={() => onRowClick && onRowClick(rows[0], 0)}>
          {rows[0][1]} - {rows[0][2]}
        </div>
      )}
    </div>
  );
});

describe('ResultTableExample Component', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('renders with initial data', () => {
    render(<ResultTableExample />);

    expect(screen.getByText('쿼리 결과 표시 컴포넌트 예제')).toBeInTheDocument();
    expect(screen.getByTestId('enhanced-result-table')).toBeInTheDocument();
    expect(screen.getByTestId('row-count').textContent).toBe('20');
    expect(screen.getByTestId('loading').textContent).toBe('false');
  });

  test('handles refresh button click', async () => {
    render(<ResultTableExample />);

    const refreshButton = screen.getByText('데이터 새로고침');
    fireEvent.click(refreshButton);

    expect(screen.getByTestId('loading').textContent).toBe('true');

    jest.advanceTimersByTime(1000);

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });
  });

  test('handles large data load button click', async () => {
    render(<ResultTableExample />);

    const largeDataButton = screen.getByText('대용량 데이터 로드 (100행)');
    fireEvent.click(largeDataButton);

    expect(screen.getByTestId('loading').textContent).toBe('true');

    jest.advanceTimersByTime(1500);

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
      expect(screen.getByTestId('row-count').textContent).toBe('100');
    });
  });

  test('handles error simulation button click', () => {
    render(<ResultTableExample />);

    const errorButton = screen.getByText('오류 시뮬레이션');
    fireEvent.click(errorButton);

    expect(screen.getByTestId('error').textContent).toBe('테스트 오류 메시지입니다.');
  });

  test('passes correct props to EnhancedResultTable', () => {
    render(<ResultTableExample />);

    const columnsElement = screen.getByTestId('columns');
    const columnsData = JSON.parse(columnsElement.textContent || '[]');

    expect(columnsData).toHaveLength(8);
    expect(columnsData[0].name).toBe('ID');
    expect(columnsData[1].name).toBe('이름');
  });

  test('handles row click', () => {
    // Mock window.alert
    const alertMock = jest.spyOn(window, 'alert').mockImplementation(() => {});

    render(<ResultTableExample />);

    const firstRow = screen.getByTestId('first-row');
    fireEvent.click(firstRow);

    expect(alertMock).toHaveBeenCalled();

    alertMock.mockRestore();
  });
});
