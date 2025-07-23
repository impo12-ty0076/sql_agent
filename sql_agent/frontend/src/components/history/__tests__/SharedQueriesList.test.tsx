import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import SharedQueriesList from '../SharedQueriesList';

// Mock the historyService functions
jest.mock('../../../services/historyService', () => ({
  deleteShareLink: jest.fn(() => ({ type: 'mocked-action' })),
  getShareLinks: jest.fn(() => ({ type: 'mocked-action' }))
}));

// Import after mocking
import { deleteShareLink, getShareLinks } from '../../../services/historyService';

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn()
  }
});

const mockStore = configureStore();

describe('SharedQueriesList', () => {
  let store: any;
  
  beforeEach(() => {
    store = mockStore({
      history: {
        shareLinks: {},
        shareLinksLoading: false,
        shareLinksError: null
      }
    });
    
    // Reset mocks
    jest.mocked(deleteShareLink).mockClear();
    jest.mocked(getShareLinks).mockClear();
    jest.mocked(navigator.clipboard.writeText).mockClear();
  });
  
  it('renders loading state correctly', () => {
    render(
      <Provider store={store}>
        <SharedQueriesList
          historyId="123"
          shareLinks={[]}
          loading={true}
          error={null}
        />
      </Provider>
    );
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
  
  it('renders error state correctly', () => {
    render(
      <Provider store={store}>
        <SharedQueriesList
          historyId="123"
          shareLinks={[]}
          loading={false}
          error="Failed to load share links"
        />
      </Provider>
    );
    
    expect(screen.getByText('Failed to load share links')).toBeInTheDocument();
  });
  
  it('renders empty state correctly', () => {
    render(
      <Provider store={store}>
        <SharedQueriesList
          historyId="123"
          shareLinks={[]}
          loading={false}
          error={null}
        />
      </Provider>
    );
    
    expect(screen.getByText('이 쿼리에 대한 공유 링크가 없습니다.')).toBeInTheDocument();
  });
  
  it('renders share links correctly', () => {
    const shareLinks = [
      {
        id: "456",
        history_id: "123",
        share_link: "https://example.com/share/456",
        created_by: "user@example.com",
        created_at: "2023-01-01T12:00:00Z",
        expires_at: "2023-12-31T23:59:59Z",
        allowed_users: ["user1@example.com", "user2@example.com"]
      }
    ];
    
    render(
      <Provider store={store}>
        <SharedQueriesList
          historyId="123"
          shareLinks={shareLinks}
          loading={false}
          error={null}
        />
      </Provider>
    );
    
    expect(screen.getByText("https://example.com/share/456")).toBeInTheDocument();
    expect(screen.getByText(/생성일: 2023년 01월 01일/)).toBeInTheDocument();
    expect(screen.getByText(/만료일: 2023년 12월 31일/)).toBeInTheDocument();
    expect(screen.getByText(/허용된 사용자: user1@example.com, user2@example.com/)).toBeInTheDocument();
  });
  
  it('copies link to clipboard when copy button is clicked', async () => {
    const shareLinks = [
      {
        id: "456",
        history_id: "123",
        share_link: "https://example.com/share/456",
        created_by: "user@example.com",
        created_at: "2023-01-01T12:00:00Z",
        expires_at: "2023-12-31T23:59:59Z",
        allowed_users: []
      }
    ];
    
    render(
      <Provider store={store}>
        <SharedQueriesList
          historyId="123"
          shareLinks={shareLinks}
          loading={false}
          error={null}
        />
      </Provider>
    );
    
    // Find and click the copy button
    const copyButton = screen.getByLabelText('링크 복사');
    fireEvent.click(copyButton);
    
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith("https://example.com/share/456");
    
    // Check for success message
    await waitFor(() => {
      expect(screen.getByText('링크가 클립보드에 복사되었습니다.')).toBeInTheDocument();
    });
  });
  
  it('shows delete confirmation dialog when delete button is clicked', () => {
    const shareLinks = [
      {
        id: "456",
        history_id: "123",
        share_link: "https://example.com/share/456",
        created_by: "user@example.com",
        created_at: "2023-01-01T12:00:00Z",
        expires_at: "2023-12-31T23:59:59Z",
        allowed_users: []
      }
    ];
    
    render(
      <Provider store={store}>
        <SharedQueriesList
          historyId="123"
          shareLinks={shareLinks}
          loading={false}
          error={null}
        />
      </Provider>
    );
    
    // Find and click the delete button
    const deleteButton = screen.getByLabelText('삭제');
    fireEvent.click(deleteButton);
    
    // Check for confirmation dialog
    expect(screen.getByText('공유 링크 삭제')).toBeInTheDocument();
    expect(screen.getByText('이 공유 링크를 삭제하시겠습니까? 이 작업은 취소할 수 없습니다.')).toBeInTheDocument();
  });
  
  it('calls deleteShareLink when delete is confirmed', async () => {
    jest.mocked(deleteShareLink).mockReturnValue({
      type: 'history/deleteShareLink/fulfilled',
      payload: "456"
    } as any);
    
    const shareLinks = [
      {
        id: "456",
        history_id: "123",
        share_link: "https://example.com/share/456",
        created_by: "user@example.com",
        created_at: "2023-01-01T12:00:00Z",
        expires_at: "2023-12-31T23:59:59Z",
        allowed_users: []
      }
    ];
    
    render(
      <Provider store={store}>
        <SharedQueriesList
          historyId="123"
          shareLinks={shareLinks}
          loading={false}
          error={null}
        />
      </Provider>
    );
    
    // Find and click the delete button
    const deleteButton = screen.getByLabelText('삭제');
    fireEvent.click(deleteButton);
    
    // Confirm deletion
    const confirmButton = screen.getByText('삭제', { selector: 'button' });
    fireEvent.click(confirmButton);
    
    await waitFor(() => {
      expect(deleteShareLink).toHaveBeenCalledWith("456");
    });
  });
});