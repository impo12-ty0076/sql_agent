import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import SharedQuery from '../SharedQuery';

// Mock the SharedQueryView component
jest.mock('../../components/history/SharedQueryView', () => {
  return {
    __esModule: true,
    default: ({ shareId, token }: { shareId: string; token: string }) => (
      <div data-testid="shared-query-view">
        Shared Query View (ID: {shareId}, Token: {token})
      </div>
    )
  };
});

const mockStore = configureStore();

describe('SharedQuery', () => {
  let store: any;
  
  beforeEach(() => {
    store = mockStore({
      auth: {
        isAuthenticated: false,
        user: null
      }
    });
  });
  
  it('renders error message when id or token is missing', () => {
    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/shared']}>
          <Routes>
            <Route path="/shared" element={<SharedQuery />} />
          </Routes>
        </MemoryRouter>
      </Provider>
    );
    
    expect(screen.getByText('잘못된 공유 링크')).toBeInTheDocument();
    expect(screen.getByText('유효한 공유 ID와 토큰이 필요합니다.')).toBeInTheDocument();
  });
  
  it('renders SharedQueryView with correct props when id and token are provided', () => {
    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/shared?id=123&token=abc']}>
          <Routes>
            <Route path="/shared" element={<SharedQuery />} />
          </Routes>
        </MemoryRouter>
      </Provider>
    );
    
    expect(screen.getByTestId('shared-query-view')).toBeInTheDocument();
    expect(screen.getByText('Shared Query View (ID: 123, Token: abc)')).toBeInTheDocument();
  });
});