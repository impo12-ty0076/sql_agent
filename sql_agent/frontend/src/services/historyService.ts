import { createAsyncThunk } from '@reduxjs/toolkit';
import api from './api';

// Types
export interface QueryHistoryItem {
  id: string;
  user_id: string;
  query_id: string;
  favorite: boolean;
  tags: string[];
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface QueryHistoryListResponse {
  items: QueryHistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface QueryHistoryFilters {
  limit?: number;
  offset?: number;
  favorite_only?: boolean;
  tags?: string[];
  start_date?: string;
  end_date?: string;
  search_text?: string;
}

export interface QueryHistoryUpdate {
  favorite?: boolean;
  tags?: string[];
  notes?: string;
}

export interface ShareLink {
  id: string;
  history_id: string;
  share_link: string;
  created_by: string;
  created_at: string;
  expires_at?: string;
  allowed_users?: string[];
}

export interface ShareLinkRequest {
  historyId: string;
  expiresInDays?: number;
  allowedUsers?: string[];
}

export interface UpdateShareLinkRequest {
  shareId: string;
  expiresInDays?: number;
  allowedUsers?: string[];
}

export interface ShareLinkResponse {
  id: string;
  share_link: string;
  expires_at?: string;
  allowed_users?: string[];
}

// Async thunks
export const fetchQueryHistory = createAsyncThunk(
  'history/fetchQueryHistory',
  async (filters: QueryHistoryFilters, { rejectWithValue }) => {
    try {
      const params = new URLSearchParams();
      
      if (filters.limit) params.append('limit', filters.limit.toString());
      if (filters.offset) params.append('offset', filters.offset.toString());
      if (filters.favorite_only) params.append('favorite_only', filters.favorite_only.toString());
      if (filters.tags && filters.tags.length > 0) {
        filters.tags.forEach(tag => params.append('tags', tag));
      }
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.search_text) params.append('search_text', filters.search_text);
      
      const response = await api.get<QueryHistoryListResponse>(`/api/query-history/?${params.toString()}`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

export const updateHistoryItem = createAsyncThunk(
  'history/updateHistoryItem',
  async ({ historyId, data }: { historyId: string; data: QueryHistoryUpdate }, { rejectWithValue }) => {
    try {
      const response = await api.put<QueryHistoryItem>(`/api/query-history/${historyId}`, data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

export const toggleFavorite = createAsyncThunk(
  'history/toggleFavorite',
  async ({ historyId, favorite }: { historyId: string; favorite: boolean }, { rejectWithValue }) => {
    try {
      const response = await api.post<QueryHistoryItem>(`/api/query-history/favorite/${historyId}`, { favorite });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

export const updateTags = createAsyncThunk(
  'history/updateTags',
  async ({ historyId, tags }: { historyId: string; tags: string[] }, { rejectWithValue }) => {
    try {
      const response = await api.post<QueryHistoryItem>(`/api/query-history/tags/${historyId}`, { tags });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

export const deleteHistoryItem = createAsyncThunk(
  'history/deleteHistoryItem',
  async (historyId: string, { rejectWithValue }) => {
    try {
      await api.delete(`/api/query-history/${historyId}`);
      return historyId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

// Share link thunks
export const createShareLink = createAsyncThunk(
  'history/createShareLink',
  async (request: ShareLinkRequest, { rejectWithValue }) => {
    try {
      const response = await api.post<ShareLinkResponse>('/api/query-history/share', {
        history_id: request.historyId,
        expires_in_days: request.expiresInDays,
        allowed_users: request.allowedUsers
      });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

export const updateShareLink = createAsyncThunk(
  'history/updateShareLink',
  async (request: UpdateShareLinkRequest, { rejectWithValue }) => {
    try {
      const response = await api.put<ShareLinkResponse>(`/api/query-history/share/${request.shareId}`, {
        expires_in_days: request.expiresInDays,
        allowed_users: request.allowedUsers
      });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

export const deleteShareLink = createAsyncThunk(
  'history/deleteShareLink',
  async (shareId: string, { rejectWithValue }) => {
    try {
      await api.delete(`/api/query-history/share/${shareId}`);
      return shareId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

export const getShareLinks = createAsyncThunk(
  'history/getShareLinks',
  async (historyId: string, { rejectWithValue }) => {
    try {
      const response = await api.get<{ items: ShareLink[] }>(`/api/query-history/${historyId}/shares`);
      return response.data.items;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

// Service object
const historyService = {
  fetchQueryHistory,
  updateHistoryItem,
  toggleFavorite,
  updateTags,
  deleteHistoryItem,
  createShareLink,
  updateShareLink,
  deleteShareLink,
  getShareLinks
};

export default historyService;