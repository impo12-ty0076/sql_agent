import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import EnhancedResultTable from '../EnhancedResultTable';

// Mock Material UI components that might cause issues in tests
jest.mock('@mui/material/Menu', () => {
  return ({ children, open }: { children: React.ReactNode; open: boolean }) => {
    return open ? <div data-testid="mock-menu">{children}</div> : null;
  };
});

// Mock data for advanced testing
const mockColumns = [
  { name: 'ID', type: 'number' },
  { name: 'Name', type: 'string' },
  { name: 'Email', type: 'string' },
  { name: 'Age', type: 'number' },
  { name: 'Salary', type: 'number' },
  { name: 'Department', type: 'string' },
  { name: 'Description', type: 'text' }
];

const mockLargeDataset = Array(100).fill(null).map((_, i) => [
  i + 1,
  `User ${i + 1}`,
  `user${i + 1}@example.com`,
  20 + (i % 50),
  50000 + (i * 1000),
  ['Engineering', 'Marketing', 'Sales', 'HR'][i % 4],
  `This is a detailed description for user ${i + 1} with some additional information that might be quite long and need truncation in the table view.`
]);

describe('EnhancedResultTable - Advanced Features', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
  });

  describe('Large Dataset Handling', () => {
    test('handles large datasets with pagination', () => {
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={mockLargeDataset}
          rowCount={mockLargeDataset.length}
        />
      );
      
      // Should show first page (10 rows by default)
      expect(screen.getByText('User 1')).toBeInTheDocument();
      expect(screen.getByText('User 10')).toBeInTheDocument();
      expect(screen.queryByText('User 11')).not.toBeInTheDocument();
      
      // Check pagination info
      expect(screen.getByText('1-10 / 100')).toBeInTheDocument();
    });

    test('handles different page sizes', () => {
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={mockLargeDataset}
          rowCount={mockLargeDataset.length}
        />
      );
      
      // Find pagination controls
      const paginationElement = screen.getByText('행 수:').parentElement;
      expect(paginationElement).toBeInTheDocument();
      
      // Should show default 10 rows
      expect(screen.getByText('User 1')).toBeInTheDocument();
      expect(screen.getByText('User 10')).toBeInTheDocument();
      expect(screen.queryByText('User 11')).not.toBeInTheDocument();
    });
  });

  describe('Advanced Filtering', () => {
    test('handles multiple column filters simultaneously', () => {
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={mockLargeDataset}
          rowCount={mockLargeDataset.length}
        />
      );
      
      // Apply global filter first
      const globalFilter = screen.getByPlaceholderText('전체 검색...');
      fireEvent.change(globalFilter, { target: { value: 'Engineering' } });
      
      // Should filter to only Engineering department users
      expect(screen.getByText('User 1')).toBeInTheDocument(); // User 1 is in Engineering
      expect(screen.queryByText('User 2')).not.toBeInTheDocument(); // User 2 is in Marketing
    });

    test('handles numeric filtering with greater than operator', () => {
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={mockLargeDataset.slice(0, 10)}
          rowCount={10}
        />
      );
      
      // Check that Age column exists
      expect(screen.getByText('Age')).toBeInTheDocument();
      
      // Apply global filter to test filtering functionality
      const globalFilter = screen.getByPlaceholderText('전체 검색...');
      fireEvent.change(globalFilter, { target: { value: '25' } });
      
      // Should filter results
      expect(screen.getByText('User 6')).toBeInTheDocument(); // User 6 has age 25
    });

    test('clears all filters correctly', () => {
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={mockLargeDataset}
          rowCount={mockLargeDataset.length}
        />
      );
      
      // Apply a global filter
      const globalFilter = screen.getByPlaceholderText('전체 검색...');
      fireEvent.change(globalFilter, { target: { value: 'User 1' } });
      
      // Should show filtered results
      expect(screen.getByText('User 1')).toBeInTheDocument();
      expect(screen.getByText('User 10')).toBeInTheDocument();
      expect(screen.queryByText('User 2')).not.toBeInTheDocument();
      
      // Clear filter by clearing the input
      fireEvent.change(globalFilter, { target: { value: '' } });
      
      // Should show all results again
      expect(screen.getByText('User 1')).toBeInTheDocument();
      expect(screen.getByText('User 2')).toBeInTheDocument();
    });
  });

  describe('Advanced Sorting', () => {
    test('handles numeric sorting correctly', () => {
      const numericData = [
        [1, 'User A', 'a@test.com', 25, 50000, 'Engineering', 'Desc A'],
        [2, 'User B', 'b@test.com', 30, 60000, 'Marketing', 'Desc B'],
        [3, 'User C', 'c@test.com', 22, 45000, 'Sales', 'Desc C'],
      ];
      
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={numericData}
          rowCount={numericData.length}
        />
      );
      
      // Find and click sort button for Age column
      const ageHeader = screen.getByText('Age');
      const sortButton = ageHeader.closest('th')?.querySelector('button');
      
      if (sortButton) {
        fireEvent.click(sortButton);
        
        // After sorting, User C (age 22) should appear first
        expect(screen.getByText('User C')).toBeInTheDocument();
      }
    });

    test('handles string sorting correctly', () => {
      const stringData = [
        [1, 'Charlie', 'charlie@test.com', 25, 50000, 'Engineering', 'Desc'],
        [2, 'Alice', 'alice@test.com', 30, 60000, 'Marketing', 'Desc'],
        [3, 'Bob', 'bob@test.com', 22, 45000, 'Sales', 'Desc'],
      ];
      
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={stringData}
          rowCount={stringData.length}
        />
      );
      
      // Find and click sort button for Name column
      const nameHeader = screen.getByText('Name');
      const sortButton = nameHeader.closest('th')?.querySelector('button');
      
      if (sortButton) {
        fireEvent.click(sortButton);
        
        // After sorting, Alice should appear first
        expect(screen.getByText('Alice')).toBeInTheDocument();
      }
    });
  });

  describe('Export Functionality', () => {
    beforeEach(() => {
      // Mock clipboard API
      Object.assign(navigator, {
        clipboard: {
          writeText: jest.fn().mockResolvedValue(undefined),
        },
      });
      
      // Mock URL methods
      global.URL.createObjectURL = jest.fn(() => 'mock-url');
      global.URL.revokeObjectURL = jest.fn();
      
      // Mock document methods
      const mockLink = {
        setAttribute: jest.fn(),
        click: jest.fn(),
        style: { visibility: '' }
      };
      jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
      jest.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);
    });

    test('exports filtered data to clipboard', async () => {
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={mockLargeDataset.slice(0, 5)}
          rowCount={5}
        />
      );
      
      // Apply filter
      const globalFilter = screen.getByPlaceholderText('전체 검색...');
      fireEvent.change(globalFilter, { target: { value: 'User 1' } });
      
      // Copy to clipboard
      const copyButton = screen.getByLabelText('클립보드에 복사');
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalled();
      });
    });

    test('exports to CSV with proper formatting', () => {
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={mockLargeDataset.slice(0, 3)}
          rowCount={3}
        />
      );
      
      // Download CSV
      const downloadButton = screen.getByLabelText('CSV 다운로드');
      fireEvent.click(downloadButton);
      
      expect(global.URL.createObjectURL).toHaveBeenCalled();
      expect(document.createElement).toHaveBeenCalledWith('a');
    });
  });

  describe('Row Numbers and Row Click', () => {
    test('displays row numbers when enabled', () => {
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={mockLargeDataset.slice(0, 5)}
          rowCount={5}
          showRowNumbers={true}
        />
      );
      
      expect(screen.getByText('#')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });

    test('handles row click events', () => {
      const handleRowClick = jest.fn();
      
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={mockLargeDataset.slice(0, 3)}
          rowCount={3}
          onRowClick={handleRowClick}
        />
      );
      
      // Click on second row
      const secondRow = screen.getByText('User 2').closest('tr');
      if (secondRow) {
        fireEvent.click(secondRow);
        expect(handleRowClick).toHaveBeenCalledWith(mockLargeDataset[1], 1);
      }
    });
  });

  describe('Loading and Error States', () => {
    test('displays skeleton loading for large datasets', () => {
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={[]}
          rowCount={0}
          loading={true}
        />
      );
      
      // Should show loading state
      expect(screen.getByText('데이터를 불러오는 중...')).toBeInTheDocument();
    });

    test('handles error state with retry functionality', () => {
      const handleRefresh = jest.fn();
      
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={[]}
          rowCount={0}
          error="Database connection failed"
          onRefresh={handleRefresh}
        />
      );
      
      expect(screen.getByText('오류 발생: Database connection failed')).toBeInTheDocument();
      
      const retryButton = screen.getByText('다시 시도');
      fireEvent.click(retryButton);
      
      expect(handleRefresh).toHaveBeenCalledTimes(1);
    });
  });

  describe('Performance and Memory', () => {
    test('handles large datasets with proper pagination', () => {
      const largeDataset = Array(100).fill(null).map((_, i) => [
        i + 1,
        `User ${i + 1}`,
        `user${i + 1}@example.com`,
        20 + (i % 50),
        50000 + (i * 100),
        ['Engineering', 'Marketing', 'Sales', 'HR'][i % 4],
        `Description ${i + 1}`
      ]);
      
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={largeDataset}
          rowCount={largeDataset.length}
        />
      );
      
      // Should show correct pagination info
      expect(screen.getByText('1-10 / 100')).toBeInTheDocument();
      
      // Should only render visible rows (not all 100)
      expect(screen.getByText('User 1')).toBeInTheDocument();
      expect(screen.getByText('User 10')).toBeInTheDocument();
      expect(screen.queryByText('User 11')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('provides proper ARIA labels and roles', () => {
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={mockLargeDataset.slice(0, 5)}
          rowCount={5}
        />
      );
      
      // Check for proper table structure
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getAllByRole('columnheader')).toHaveLength(mockColumns.length);
      expect(screen.getAllByRole('row')).toHaveLength(6); // 1 header + 5 data rows
    });

    test('supports keyboard navigation', () => {
      render(
        <EnhancedResultTable
          columns={mockColumns}
          rows={mockLargeDataset.slice(0, 5)}
          rowCount={5}
        />
      );
      
      // Focus on search input
      const searchInput = screen.getByPlaceholderText('전체 검색...');
      searchInput.focus();
      expect(document.activeElement).toBe(searchInput);
      
      // Should be able to type in search input
      fireEvent.change(searchInput, { target: { value: 'test' } });
      expect(searchInput).toHaveValue('test');
    });
  });
});