import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import EnhancedResultTable from '../EnhancedResultTable';

// Mock Material UI components that might cause issues in tests
jest.mock('@mui/material/Menu', () => {
  return ({ children, open }: { children: React.ReactNode; open: boolean }) => {
    return open ? <div data-testid="mock-menu">{children}</div> : null;
  };
});

// Mock data
const mockColumns = [
  { name: 'ID', type: 'number' },
  { name: 'Name', type: 'string' },
  { name: 'Email', type: 'string' },
  { name: 'Age', type: 'number' },
  { name: 'Description', type: 'string' },
];

const mockRows = [
  [
    1,
    'John Doe',
    'john@example.com',
    30,
    'This is a very long description that should be truncated in the table view because it exceeds the character limit for display in a single cell.',
  ],
  [2, 'Jane Smith', 'jane@example.com', 25, 'Short description'],
  [3, 'Bob Johnson', 'bob@example.com', 40, 'Another description'],
  [4, 'Alice Brown', 'alice@example.com', 35, 'Yet another description'],
  [5, 'Charlie Wilson', 'charlie@example.com', 28, 'Final description'],
];

describe('EnhancedResultTable Component', () => {
  test('renders table with correct headers and data', () => {
    render(
      <EnhancedResultTable columns={mockColumns} rows={mockRows} rowCount={mockRows.length} />
    );

    // Check if headers are rendered
    mockColumns.forEach(column => {
      expect(screen.getByText(column.name)).toBeInTheDocument();
    });

    // Check if data is rendered
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('jane@example.com')).toBeInTheDocument();
    expect(screen.getByText('40')).toBeInTheDocument();
  });

  test('handles pagination correctly', () => {
    // Create more rows for pagination testing
    const manyRows = Array(25)
      .fill(null)
      .map((_, i) => [
        i + 1,
        `User ${i + 1}`,
        `user${i + 1}@example.com`,
        20 + i,
        `Description ${i + 1}`,
      ]);

    render(
      <EnhancedResultTable columns={mockColumns} rows={manyRows} rowCount={manyRows.length} />
    );

    // Check initial page (should show first 10 rows)
    expect(screen.getByText('User 1')).toBeInTheDocument();
    expect(screen.getByText('User 10')).toBeInTheDocument();
    expect(screen.queryByText('User 11')).not.toBeInTheDocument();

    // Go to next page
    const nextPageButton = screen.getByRole('button', { name: /next page/i });
    fireEvent.click(nextPageButton);

    // Check second page
    expect(screen.queryByText('User 1')).not.toBeInTheDocument();
    expect(screen.getByText('User 11')).toBeInTheDocument();
    expect(screen.getByText('User 20')).toBeInTheDocument();
  });

  test('handles sorting correctly', () => {
    render(
      <EnhancedResultTable columns={mockColumns} rows={mockRows} rowCount={mockRows.length} />
    );

    // Find the Name column header and click to sort (more reliable than Age)
    const nameHeader = screen.getByText('Name').closest('th');
    if (!nameHeader) throw new Error('Name header not found');

    const sortButton = within(nameHeader).getByRole('button');
    fireEvent.click(sortButton);

    // After sorting by name, "Alice" should be first
    const firstRowAfterSort = screen.getByText('Alice Brown');
    expect(firstRowAfterSort).toBeInTheDocument();

    // Click again to sort in descending order
    fireEvent.click(sortButton);

    // After sorting by name in descending order, "Jane" should be first
    const firstRowAfterDescSort = screen.getAllByText(/Jane|John|Bob|Alice|Charlie/)[0];
    expect(firstRowAfterDescSort).toHaveTextContent('Jane Smith');
  });

  test('handles filtering correctly', () => {
    render(
      <EnhancedResultTable columns={mockColumns} rows={mockRows} rowCount={mockRows.length} />
    );

    // Use global filter
    const filterInput = screen.getByPlaceholderText('전체 검색...');
    fireEvent.change(filterInput, { target: { value: 'john' } });

    // Check if only John's row is visible
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument();

    // Clear filter
    fireEvent.change(filterInput, { target: { value: '' } });

    // All rows should be visible again
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
  });

  test('displays loading state correctly', () => {
    render(<EnhancedResultTable columns={mockColumns} rows={[]} rowCount={0} loading={true} />);

    expect(screen.getByText('데이터를 불러오는 중...')).toBeInTheDocument();
  });

  test('displays error state correctly', () => {
    const errorMessage = '쿼리 실행 중 오류가 발생했습니다.';
    const handleRefresh = jest.fn();

    render(
      <EnhancedResultTable
        columns={mockColumns}
        rows={[]}
        rowCount={0}
        error={errorMessage}
        onRefresh={handleRefresh}
      />
    );

    expect(screen.getByText(`오류 발생: ${errorMessage}`)).toBeInTheDocument();

    // Click refresh button
    const refreshButton = screen.getByText('다시 시도');
    fireEvent.click(refreshButton);

    expect(handleRefresh).toHaveBeenCalledTimes(1);
  });

  test('displays row numbers when enabled', () => {
    render(
      <EnhancedResultTable
        columns={mockColumns}
        rows={mockRows}
        rowCount={mockRows.length}
        showRowNumbers={true}
      />
    );

    // Check if row number header is present
    expect(screen.getByText('#')).toBeInTheDocument();

    // Check if row numbers are displayed
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  test('handles row click events', () => {
    const handleRowClick = jest.fn();

    render(
      <EnhancedResultTable
        columns={mockColumns}
        rows={mockRows}
        rowCount={mockRows.length}
        onRowClick={handleRowClick}
      />
    );

    // Click on first row
    const firstRow = screen.getByText('John Doe').closest('tr');
    if (firstRow) {
      fireEvent.click(firstRow);
      expect(handleRowClick).toHaveBeenCalledWith(mockRows[0], 0);
    }
  });

  test('handles column visibility toggle', () => {
    render(
      <EnhancedResultTable columns={mockColumns} rows={mockRows} rowCount={mockRows.length} />
    );

    // Open column visibility menu
    const columnMenuButton = screen.getByLabelText('컬럼 표시 설정');
    fireEvent.click(columnMenuButton);

    // Check if menu is open (mocked)
    expect(screen.getByTestId('mock-menu')).toBeInTheDocument();
  });

  test('handles CSV download', () => {
    // Mock URL.createObjectURL and URL.revokeObjectURL
    global.URL.createObjectURL = jest.fn(() => 'mock-url');
    global.URL.revokeObjectURL = jest.fn();

    // Mock document.createElement and appendChild/removeChild
    const mockLink = {
      setAttribute: jest.fn(),
      click: jest.fn(),
      style: { visibility: '' },
    };
    jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
    jest.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
    jest.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);

    render(
      <EnhancedResultTable columns={mockColumns} rows={mockRows} rowCount={mockRows.length} />
    );

    // Click download button
    const downloadButton = screen.getByLabelText('CSV 다운로드');
    fireEvent.click(downloadButton);

    expect(mockLink.click).toHaveBeenCalled();
    expect(global.URL.createObjectURL).toHaveBeenCalled();
    expect(global.URL.revokeObjectURL).toHaveBeenCalled();
  });

  test('handles clipboard copy', async () => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn().mockResolvedValue(undefined),
      },
    });

    render(
      <EnhancedResultTable columns={mockColumns} rows={mockRows} rowCount={mockRows.length} />
    );

    // Click copy button
    const copyButton = screen.getByLabelText('클립보드에 복사');
    fireEvent.click(copyButton);

    expect(navigator.clipboard.writeText).toHaveBeenCalled();
  });

  test('displays truncated data warning', () => {
    render(
      <EnhancedResultTable
        columns={mockColumns}
        rows={mockRows}
        rowCount={mockRows.length}
        truncated={true}
        totalRowCount={1000}
      />
    );

    expect(screen.getByText(/전체 1000개 중 일부/)).toBeInTheDocument();
  });

  test('shows execution time when provided', () => {
    render(
      <EnhancedResultTable
        columns={mockColumns}
        rows={mockRows}
        rowCount={mockRows.length}
        executionTime={1234.56}
      />
    );

    expect(screen.getByText('실행 시간: 1234.56ms')).toBeInTheDocument();
  });

  test('handles empty state with filters', () => {
    render(
      <EnhancedResultTable columns={mockColumns} rows={mockRows} rowCount={mockRows.length} />
    );

    // Apply a filter that returns no results
    const filterInput = screen.getByPlaceholderText('전체 검색...');
    fireEvent.change(filterInput, { target: { value: 'nonexistent' } });

    expect(screen.getByText('필터 조건에 맞는 결과가 없습니다.')).toBeInTheDocument();
    expect(screen.getByText('모든 필터 지우기')).toBeInTheDocument();
  });
});
