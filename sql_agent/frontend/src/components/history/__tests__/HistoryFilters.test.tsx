import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import HistoryFilters from '../HistoryFilters';
import { setFilters, resetFilters } from '../../../store/slices/historySlice';

// Mock Redux store
const mockStore = configureStore([]);

describe('HistoryFilters', () => {
  let store: any;

  beforeEach(() => {
    store = mockStore({
      history: {
        filters: {
          limit: 100,
          offset: 0,
          favorite_only: false,
          tags: [],
        }
      }
    });
    
    store.dispatch = jest.fn();
  });

  const renderComponent = () => {
    return render(
      <Provider store={store}>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <HistoryFilters />
        </LocalizationProvider>
      </Provider>
    );
  };

  test('renders filter components correctly', () => {
    renderComponent();
    
    expect(screen.getByText('필터')).toBeInTheDocument();
    expect(screen.getByLabelText('시작일')).toBeInTheDocument();
    expect(screen.getByLabelText('종료일')).toBeInTheDocument();
    expect(screen.getByLabelText('즐겨찾기만 보기')).toBeInTheDocument();
    expect(screen.getByLabelText('태그')).toBeInTheDocument();
    expect(screen.getByText('초기화')).toBeInTheDocument();
    expect(screen.getByText('적용')).toBeInTheDocument();
  });

  test('applies filters when Apply button is clicked', () => {
    renderComponent();
    
    // Check favorite only
    fireEvent.click(screen.getByLabelText('즐겨찾기만 보기'));
    
    // Add search text
    fireEvent.change(screen.getByPlaceholderText('쿼리 내용, 메모 검색'), {
      target: { value: '매출 데이터' }
    });
    
    // Click apply button
    fireEvent.click(screen.getByText('적용'));
    
    // Check if setFilters action was dispatched with correct parameters
    expect(store.dispatch).toHaveBeenCalledWith(
      setFilters({
        favorite_only: true,
        tags: [],
        start_date: undefined,
        end_date: undefined,
        search_text: '매출 데이터',
      })
    );
  });

  test('resets filters when Reset button is clicked', () => {
    renderComponent();
    
    // Click reset button
    fireEvent.click(screen.getByText('초기화'));
    
    // Check if resetFilters action was dispatched
    expect(store.dispatch).toHaveBeenCalledWith(resetFilters());
  });
});