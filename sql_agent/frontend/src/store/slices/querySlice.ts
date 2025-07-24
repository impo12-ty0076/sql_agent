import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface QueryResult {
  columns: string[];
  rows: any[][];
  rowCount: number;
  executionTime: number;
  resultId?: string;
}

export interface SavedQuery {
  id: string;
  name: string;
  query: string;
  databaseId: string;
  createdAt: string;
  updatedAt: string;
}

export interface QueryState {
  currentQuery: string;
  generatedSql: string;
  useRag: boolean;
  queryHistory: {
    query: string;
    timestamp: string;
    databaseId: string;
    sql?: string;
    useRag?: boolean;
  }[];
  savedQueries: SavedQuery[];
  results: QueryResult | null;
  loading: boolean;
  error: string | null;
}

const initialState: QueryState = {
  currentQuery: '',
  generatedSql: '',
  useRag: false,
  queryHistory: [],
  savedQueries: [],
  results: null,
  loading: false,
  error: null,
};

const querySlice = createSlice({
  name: 'query',
  initialState,
  reducers: {
    setCurrentQuery: (state, action: PayloadAction<string>) => {
      state.currentQuery = action.payload;
    },
    setGeneratedSql: (state, action: PayloadAction<string>) => {
      state.generatedSql = action.payload;
    },
    setUseRag: (state, action: PayloadAction<boolean>) => {
      state.useRag = action.payload;
    },
    executeQueryStart: state => {
      state.loading = true;
      state.error = null;
    },
    executeQuerySuccess: (state, action: PayloadAction<QueryResult>) => {
      state.results = action.payload;
      state.loading = false;
      // Add to history
      state.queryHistory.unshift({
        query: state.currentQuery,
        timestamp: new Date().toISOString(),
        databaseId: '', // This should be set from the selected database
        sql: state.generatedSql,
        useRag: state.useRag,
      });
      // Limit history to 50 items
      if (state.queryHistory.length > 50) {
        state.queryHistory = state.queryHistory.slice(0, 50);
      }
    },
    executeQueryFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
    clearQueryResults: state => {
      state.results = null;
    },
    fetchSavedQueriesStart: state => {
      state.loading = true;
    },
    fetchSavedQueriesSuccess: (state, action: PayloadAction<SavedQuery[]>) => {
      state.savedQueries = action.payload;
      state.loading = false;
    },
    fetchSavedQueriesFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
    saveQuerySuccess: (state, action: PayloadAction<SavedQuery>) => {
      state.savedQueries.push(action.payload);
    },
    deleteQuerySuccess: (state, action: PayloadAction<string>) => {
      state.savedQueries = state.savedQueries.filter(query => query.id !== action.payload);
    },
    clearQueryError: state => {
      state.error = null;
    },
  },
});

export const {
  setCurrentQuery,
  setGeneratedSql,
  setUseRag,
  executeQueryStart,
  executeQuerySuccess,
  executeQueryFailure,
  clearQueryResults,
  fetchSavedQueriesStart,
  fetchSavedQueriesSuccess,
  fetchSavedQueriesFailure,
  saveQuerySuccess,
  deleteQuerySuccess,
  clearQueryError,
} = querySlice.actions;

export default querySlice.reducer;
