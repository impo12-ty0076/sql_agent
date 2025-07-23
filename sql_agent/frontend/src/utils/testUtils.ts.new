import { configureStore } from '@reduxjs/toolkit';
import { AnyAction, UnknownAction } from 'redux';
import { ThunkDispatch } from '@reduxjs/toolkit';

/**
 * Creates a mock store for testing purposes
 * @param initialState The initial state for the store
 * @returns A configured mock store
 */
export const createMockStore = (initialState: any) => {
  const actions: AnyAction[] = [];
  
  const store = configureStore({
    reducer: () => initialState,
    middleware: (getDefaultMiddleware) => 
      getDefaultMiddleware({
        thunk: {
          extraArgument: {},
        },
        serializableCheck: false,
      }),
  });

  // Add a way to track dispatched actions for assertions
  const originalDispatch = store.dispatch;
  // Cast the mock function to unknown first, then to the expected dispatch type
  store.dispatch = jest.fn((action: any) => {
    actions.push(action);
    return originalDispatch(action);
  }) as unknown as typeof store.dispatch;

  return {
    ...store,
    getActions: () => actions,
    clearActions: () => actions.splice(0, actions.length),
  };
};
