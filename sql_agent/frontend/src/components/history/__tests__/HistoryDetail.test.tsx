import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import HistoryDetail from '../HistoryDetail';
import { toggleFavorite, updateTags, updateHistoryItem } from '../../../services/historyService';
import api from '../../../services/api';

// Mock API
jest.mock('../../../services/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

// Mock Redux store
const mockStore = configureStore([]);

describe('HistoryDetail', () => {
  let store: any;
  const mockItem = {
    id: '1',
    user_id: 'user1',
    query_id: 'query123456789',
    favorite: true,
    tags: ['중요', '매출'],
    notes: '중요한 매출 쿼리',
    created_at: '2025-07-01T10:00:00Z',
    updated_at: '2025-07-01T10:00:00Z',
  };

  const mockQueryDetails = {
    natural_language: '지난 달 매출은 얼마인가요?',
    generated_sql:
      "SELECT SUM(amount) FROM sales WHERE date >= '2025-06-01' AND date <= '2025-06-30'",
    result: {
      columns: ['total_sales'],
      rows: [[1500000]],
    },
  };

  beforeEach(() => {
    store = mockStore({});
    store.dispatch = jest.fn();

    // Mock API responses
    (api.get as jest.Mock).mockImplementation(url => {
      if (url.includes('/api/query/')) {
        return Promise.resolve({ data: mockQueryDetails });
      }
      if (url.includes('/api/query-history/tags')) {
        return Promise.resolve({ data: { tags: ['중요', '매출', '고객', '제품', '분석'] } });
      }
      return Promise.reject(new Error('Not found'));
    });

    (api.post as jest.Mock).mockImplementation(url => {
      if (url.includes('/api/query-history/share')) {
        return Promise.resolve({
          data: {
            share_link: 'https://example.com/share/abc123',
          },
        });
      }
      return Promise.reject(new Error('Not found'));
    });
  });

  const renderComponent = () => {
    return render(
      <Provider store={store}>
        <HistoryDetail item={mockItem} />
      </Provider>
    );
  };

  test('renders history detail correctly', async () => {
    renderComponent();

    // Check basic information
    expect(screen.getByText('쿼리 상세 정보')).toBeInTheDocument();
    expect(screen.getByText(/생성일:/)).toBeInTheDocument();
    expect(screen.getByText(/마지막 수정일:/)).toBeInTheDocument();

    // Check tags
    expect(screen.getByText('중요')).toBeInTheDocument();
    expect(screen.getByText('매출')).toBeInTheDocument();

    // Check notes
    expect(screen.getByText('중요한 매출 쿼리')).toBeInTheDocument();

    // Check tabs
    expect(screen.getByRole('tab', { name: '자연어 질의' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'SQL' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '결과' })).toBeInTheDocument();

    // Wait for query details to load
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith(`/api/query/${mockItem.query_id}`);
    });
  });

  test('toggles favorite status', () => {
    renderComponent();

    // Find and click the star icon
    const favoriteButton = screen.getByRole('button', { name: '즐겨찾기 해제' });
    fireEvent.click(favoriteButton);

    expect(store.dispatch).toHaveBeenCalledWith(
      toggleFavorite({ historyId: '1', favorite: false })
    );
  });

  test('edits and saves notes', () => {
    renderComponent();

    // Find and click the edit button for notes
    const editButtons = screen.getAllByRole('button', { name: '' });
    const editNotesButton = editButtons.find(
      button => button.parentElement?.previousElementSibling?.textContent === '메모'
    );

    fireEvent.click(editNotesButton!);

    // Find textarea and change value
    const textarea = screen.getByPlaceholderText('메모를 입력하세요');
    fireEvent.change(textarea, { target: { value: '수정된 메모' } });

    // Find and click save button
    const saveButton = screen.getAllByRole('button')[3]; // This might be fragile
    fireEvent.click(saveButton);

    expect(store.dispatch).toHaveBeenCalledWith(
      updateHistoryItem({
        historyId: '1',
        data: { notes: '수정된 메모' },
      })
    );
  });

  test('opens share dialog and creates share link', async () => {
    renderComponent();

    // Find and click share button
    const shareButton = screen.getByRole('button', { name: '공유' });
    fireEvent.click(shareButton);

    // Check if dialog is open
    expect(screen.getByText('쿼리 공유')).toBeInTheDocument();

    // Select expiry and click create link
    const expirySelect = screen.getByLabelText('만료 기간');
    fireEvent.change(expirySelect, { target: { value: '30' } });

    const createLinkButton = screen.getByRole('button', { name: '링크 생성' });
    fireEvent.click(createLinkButton);

    // Wait for API call
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/query-history/share', {
        history_id: '1',
        expires_in_days: 30,
      });
    });

    // Check if link is displayed
    await waitFor(() => {
      expect(screen.getByLabelText('공유 링크')).toHaveValue('https://example.com/share/abc123');
    });
  });

  test('switches between tabs', async () => {
    renderComponent();

    // Wait for query details to load
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith(`/api/query/${mockItem.query_id}`);
    });

    // Click SQL tab
    const sqlTab = screen.getByRole('tab', { name: 'SQL' });
    fireEvent.click(sqlTab);

    // Check if SQL content is displayed
    await waitFor(() => {
      expect(screen.getByText(/SELECT SUM/)).toBeInTheDocument();
    });

    // Click Results tab
    const resultsTab = screen.getByRole('tab', { name: '결과' });
    fireEvent.click(resultsTab);

    // Check if results content is displayed
    await waitFor(() => {
      expect(screen.getByText(/결과 데이터가 있습니다/)).toBeInTheDocument();
    });
  });
});
