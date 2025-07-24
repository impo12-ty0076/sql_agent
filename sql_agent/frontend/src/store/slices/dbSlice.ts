import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Database {
  id: string;
  name: string;
  type: 'mysql' | 'postgresql' | 'sqlite' | 'mssql' | 'oracle';
  host?: string;
  port?: number;
  username?: string;
  connected: boolean;
}

export interface Table {
  name: string;
  schema?: string;
  columns: Column[];
}

export interface Column {
  name: string;
  type: string;
  nullable: boolean;
  isPrimaryKey: boolean;
  isForeignKey: boolean;
}

export interface DbState {
  databases: Database[];
  selectedDatabase: Database | null;
  tables: Table[];
  loading: boolean;
  error: string | null;
}

const initialState: DbState = {
  databases: [],
  selectedDatabase: null,
  tables: [],
  loading: false,
  error: null,
};

const dbSlice = createSlice({
  name: 'db',
  initialState,
  reducers: {
    fetchDatabasesStart: state => {
      state.loading = true;
      state.error = null;
    },
    fetchDatabasesSuccess: (state, action: PayloadAction<Database[]>) => {
      state.databases = action.payload;
      state.loading = false;
    },
    fetchDatabasesFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
    selectDatabase: (state, action: PayloadAction<Database>) => {
      state.selectedDatabase = action.payload;
    },
    fetchTablesStart: state => {
      state.loading = true;
      state.error = null;
    },
    fetchTablesSuccess: (state, action: PayloadAction<Table[]>) => {
      state.tables = action.payload;
      state.loading = false;
    },
    fetchTablesFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
    clearDbError: state => {
      state.error = null;
    },
  },
});

export const {
  fetchDatabasesStart,
  fetchDatabasesSuccess,
  fetchDatabasesFailure,
  selectDatabase,
  fetchTablesStart,
  fetchTablesSuccess,
  fetchTablesFailure,
  clearDbError,
} = dbSlice.actions;

export default dbSlice.reducer;
