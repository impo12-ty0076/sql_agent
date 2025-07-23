import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import dbReducer from './slices/dbSlice';
import queryReducer from './slices/querySlice';
import uiReducer from './slices/uiSlice';
import reportReducer from './slices/reportSlice';
import historyReducer from './slices/historySlice';
import adminReducer from './slices/adminSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    db: dbReducer,
    query: queryReducer,
    ui: uiReducer,
    report: reportReducer,
    history: historyReducer,
    admin: adminReducer,
  },
  middleware: (getDefaultMiddleware) => getDefaultMiddleware(),
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;