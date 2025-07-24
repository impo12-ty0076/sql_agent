import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import {
  fetchQueryHistory,
  updateHistoryItem,
  toggleFavorite,
  updateTags,
  deleteHistoryItem,
  createShareLink,
  updateShareLink,
  deleteShareLink,
  getShareLinks,
  QueryHistoryItem,
  QueryHistoryListResponse,
  QueryHistoryFilters,
  ShareLink,
  ShareLinkResponse,
} from '../../services/historyService';

interface HistoryState {
  items: QueryHistoryItem[];
  total: number;
  loading: boolean;
  error: string | null;
  filters: QueryHistoryFilters;
  selectedItem: QueryHistoryItem | null;
  shareLinks: Record<string, ShareLink[]>;
  shareLinksLoading: boolean;
  shareLinksError: string | null;
}

const initialState: HistoryState = {
  items: [],
  total: 0,
  loading: false,
  error: null,
  filters: {
    limit: 100,
    offset: 0,
    favorite_only: false,
    tags: [],
    search_text: '',
  },
  selectedItem: null,
  shareLinks: {},
  shareLinksLoading: false,
  shareLinksError: null,
};

const historySlice = createSlice({
  name: 'history',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<QueryHistoryFilters>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    resetFilters: state => {
      state.filters = initialState.filters;
    },
    setSelectedItem: (state, action: PayloadAction<QueryHistoryItem | null>) => {
      state.selectedItem = action.payload;
    },
    clearError: state => {
      state.error = null;
    },
  },
  extraReducers: builder => {
    // Fetch query history
    builder.addCase(fetchQueryHistory.pending, state => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(
      fetchQueryHistory.fulfilled,
      (state, action: PayloadAction<QueryHistoryListResponse>) => {
        state.loading = false;
        state.items = action.payload.items;
        state.total = action.payload.total;
      }
    );
    builder.addCase(fetchQueryHistory.rejected, (state, action) => {
      state.loading = false;
      state.error = (action.payload as string) || 'Failed to fetch query history';
    });

    // Update history item
    builder.addCase(
      updateHistoryItem.fulfilled,
      (state, action: PayloadAction<QueryHistoryItem>) => {
        const index = state.items.findIndex(item => item.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
        if (state.selectedItem?.id === action.payload.id) {
          state.selectedItem = action.payload;
        }
      }
    );

    // Toggle favorite
    builder.addCase(toggleFavorite.fulfilled, (state, action: PayloadAction<QueryHistoryItem>) => {
      const index = state.items.findIndex(item => item.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = action.payload;
      }
      if (state.selectedItem?.id === action.payload.id) {
        state.selectedItem = action.payload;
      }
    });

    // Update tags
    builder.addCase(updateTags.fulfilled, (state, action: PayloadAction<QueryHistoryItem>) => {
      const index = state.items.findIndex(item => item.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = action.payload;
      }
      if (state.selectedItem?.id === action.payload.id) {
        state.selectedItem = action.payload;
      }
    });

    // Delete history item
    builder.addCase(deleteHistoryItem.fulfilled, (state, action: PayloadAction<string>) => {
      state.items = state.items.filter(item => item.id !== action.payload);
      if (state.selectedItem?.id === action.payload) {
        state.selectedItem = null;
      }
      state.total = Math.max(0, state.total - 1);
    });

    // Get share links
    builder.addCase(getShareLinks.pending, state => {
      state.shareLinksLoading = true;
      state.shareLinksError = null;
    });
    builder.addCase(getShareLinks.fulfilled, (state, action: PayloadAction<ShareLink[]>) => {
      state.shareLinksLoading = false;
      if (action.payload.length > 0) {
        const historyId = action.payload[0].history_id;
        state.shareLinks[historyId] = action.payload;
      }
    });
    builder.addCase(getShareLinks.rejected, (state, action) => {
      state.shareLinksLoading = false;
      state.shareLinksError = (action.payload as string) || 'Failed to fetch share links';
    });

    // Create share link
    builder.addCase(
      createShareLink.fulfilled,
      (state, action: PayloadAction<ShareLinkResponse>) => {
        // This would be updated when we fetch the share links again
      }
    );

    // Update share link
    builder.addCase(
      updateShareLink.fulfilled,
      (state, action: PayloadAction<ShareLinkResponse>) => {
        // This would be updated when we fetch the share links again
      }
    );

    // Delete share link
    builder.addCase(deleteShareLink.fulfilled, (state, action: PayloadAction<string>) => {
      // Remove the deleted share link from all history items
      Object.keys(state.shareLinks).forEach(historyId => {
        state.shareLinks[historyId] = state.shareLinks[historyId].filter(
          link => link.id !== action.payload
        );
      });
    });
  },
});

export const { setFilters, resetFilters, setSelectedItem, clearError } = historySlice.actions;

export default historySlice.reducer;
