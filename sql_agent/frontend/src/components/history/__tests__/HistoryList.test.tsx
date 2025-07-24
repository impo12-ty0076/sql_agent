import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import HistoryList from '../HistoryList';
import { setSelectedItem } from '../../../store/slices/historySlice';
import { toggleFavorite, deleteHistoryItem } from '../../../services/historyService';

// Mock Redux store
const mockStore = configureStore([]);

// Mock window.confirm
window.confirm = jest.fn();

describe('HistoryList', () => {
  let store: any;
  const mockItems = [
    {
      id: '1',
      user_id: 'user1',
      query_id: 'query123456789',
      favorite: true,
      tags: ['중요', '매출'],
      notes: '중요한 매출 쿼리',
      created_at: '2025-07-01T10:00:00Z',
      updated_at: '2025-07-01T10:00:00Z',
    },
    {
      id: '2',
      user_id: 'user1',
      query_id: 'query987654321',
      favorite: false,
      tags: ['고객'],
      notes: '',
      created_at: '2025-07-02T11:00:00Z',
      updated_at: '2025-07-02T11:00:00Z',
    },
  ];

  beforeEach(() => {
    store = mockStore({
      history: {
        selectedItem: null,
      },
    });

    store.dispatch = jest.fn();
    (window.confirm as jest.Mock).mockImplementation(() => true);
  });

  const renderComponent = () => {
    return render(
      <Provider store={store}>
        <HistoryList items={mockItems} />
      </Provider>
    );
  };

  test('renders history items correctly', () => {
    renderComponent();

    expect(screen.getByText('쿼리 #query123')).toBeInTheDocument();
    expect(screen.getByText('쿼리 #query987')).toBeInTheDocument();
  });

  test('displays empty message when no items', () => {
    render(
      <Provider store={store}>
        <HistoryList items={[]} />
      </Provider>
    );

    expect(screen.getByText('쿼리 이력이 없습니다')).toBeInTheDocument();
  });

  test('selects an item when clicked', () => {
    renderComponent();

    fireEvent.click(screen.getByText('쿼리 #query123'));

    expect(store.dispatch).toHaveBeenCalledWith(setSelectedItem(mockItems[0]));
  });

  test('toggles favorite status', () => {
    renderComponent();

    // Find and click the star icon for the first item
    const starButtons = screen.getAllByRole('button', { name: '' });
    fireEvent.click(starButtons[0]); // First star button

    expect(store.dispatch).toHaveBeenCalledWith(
      toggleFavorite({ historyId: '1', favorite: false })
    );
  });

  test('opens context menu and deletes an item after confirmation', () => {
    renderComponent();

    // Find and click the more options button for the first item
    const moreButtons = screen.getAllByRole('button', { name: 'more options' });
    fireEvent.click(moreButtons[0]);

    // Click delete option in the menu
    const deleteMenuItem = screen.getByText('삭제');
    fireEvent.click(deleteMenuItem);

    // Confirm deletion in the dialog
    const confirmButton = screen.getByRole('button', { name: '삭제' });
    fireEvent.click(confirmButton);

    expect(store.dispatch).toHaveBeenCalledWith(deleteHistoryItem('1'));
  });
});
