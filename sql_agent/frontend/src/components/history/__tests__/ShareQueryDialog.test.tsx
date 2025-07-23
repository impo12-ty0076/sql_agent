import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import ShareQueryDialog from '../ShareQueryDialog';

// Mock the historyService functions
jest.mock('../../../services/historyService', () => ({
  createShareLink: jest.fn(() => ({ type: 'mocked-action' })),
  updateShareLink: jest.fn(() => ({ type: 'mocked-action' })),
  deleteShareLink: jest.fn(() => ({ type: 'mocked-action' }))
}));

// Import after mocking
import { createShareLink, updateShareLink, deleteShareLink } from '../../../services/historyService';

const mockStore = configureStore();

describe('ShareQueryDialog', () => {
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
    jest.mocked(createShareLink).mockClear();
    jest.mocked(updateShareLink).mockClear();
    jest.mocked(deleteShareLink).mockClear();
  });
  
  it('renders correctly for creating a new share link', () => {
    render(
      <Provider store={store}>
        <ShareQueryDialog
          open={true}
          onClose={() => {}}
          historyId="123"
        />
      </Provider>
    );
    
    expect(screen.getByText('쿼리 공유')).toBeInTheDocument();
    expect(screen.getByText('링크 생성')).toBeInTheDocument();
    expect(screen.queryByText('링크 삭제')).not.toBeInTheDocument();
  });
  
  it('renders correctly for editing an existing share link', () => {
    render(
      <Provider store={store}>
        <ShareQueryDialog
          open={true}
          onClose={() => {}}
          historyId="123"
          existingShareLink={{
            id: "456",
            link: "https://example.com/share/456",
            expiresAt: "2023-12-31T23:59:59Z",
            allowedUsers: ["user1@example.com", "user2@example.com"]
          }}
        />
      </Provider>
    );
    
    expect(screen.getByText('쿼리 공유')).toBeInTheDocument();
    expect(screen.getByText('링크 업데이트')).toBeInTheDocument();
    expect(screen.getByText('링크 삭제')).toBeInTheDocument();
    expect(screen.getByDisplayValue('https://example.com/share/456')).toBeInTheDocument();
  });
  
  it('calls createShareLink when creating a new link', async () => {
    jest.mocked(createShareLink).mockReturnValue({
      type: 'history/createShareLink/fulfilled',
      payload: {
        id: "789",
        share_link: "https://example.com/share/789"
      }
    } as any);
    
    render(
      <Provider store={store}>
        <ShareQueryDialog
          open={true}
          onClose={() => {}}
          historyId="123"
        />
      </Provider>
    );
    
    fireEvent.click(screen.getByText('링크 생성'));
    
    await waitFor(() => {
      expect(createShareLink).toHaveBeenCalledWith({
        historyId: "123",
        expiresInDays: 7,
        allowedUsers: undefined
      });
    });
  });
  
  it('calls updateShareLink when updating an existing link', async () => {
    jest.mocked(updateShareLink).mockReturnValue({
      type: 'history/updateShareLink/fulfilled',
      payload: {
        id: "456",
        share_link: "https://example.com/share/456"
      }
    } as any);
    
    render(
      <Provider store={store}>
        <ShareQueryDialog
          open={true}
          onClose={() => {}}
          historyId="123"
          existingShareLink={{
            id: "456",
            link: "https://example.com/share/456",
            expiresAt: "2023-12-31T23:59:59Z",
            allowedUsers: []
          }}
        />
      </Provider>
    );
    
    fireEvent.click(screen.getByText('링크 업데이트'));
    
    await waitFor(() => {
      expect(updateShareLink).toHaveBeenCalledWith({
        shareId: "456",
        expiresInDays: 7,
        allowedUsers: []
      });
    });
  });
  
  it('calls deleteShareLink when deleting a link', async () => {
    jest.mocked(deleteShareLink).mockReturnValue({
      type: 'history/deleteShareLink/fulfilled',
      payload: "456"
    } as any);
    
    render(
      <Provider store={store}>
        <ShareQueryDialog
          open={true}
          onClose={() => {}}
          historyId="123"
          existingShareLink={{
            id: "456",
            link: "https://example.com/share/456",
            expiresAt: "2023-12-31T23:59:59Z",
            allowedUsers: []
          }}
        />
      </Provider>
    );
    
    fireEvent.click(screen.getByText('링크 삭제'));
    
    await waitFor(() => {
      expect(deleteShareLink).toHaveBeenCalledWith("456");
    });
  });
});