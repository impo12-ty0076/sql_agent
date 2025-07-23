import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from './store';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import UserProfile from './pages/UserProfile';
import SharedQuery from './pages/SharedQuery';
import Layout from './components/layout/Layout';
import { authService } from './services/authService';

// Create pages for routes
const QueryPage = () => <Layout title="SQL Query">Query Page Content</Layout>;
const HistoryPage = () => <Layout title="Query History">History Page Content</Layout>;
const SavedQueriesPage = () => <Layout title="Saved Queries">Saved Queries Content</Layout>;
const DatabasesPage = () => <Layout title="Databases">Databases Content</Layout>;
const FeedbackPage = () => <Layout title="Feedback">Feedback Content</Layout>;
const SettingsPage = () => <Layout title="Settings">Settings Content</Layout>;
import AdminDashboard from './pages/admin/AdminDashboard';
const SystemSettingsPage = () => (
  <React.Suspense fallback={<div>Loading...</div>}>
    {React.createElement(React.lazy(() => import('./pages/admin/SystemSettings')))}
  </React.Suspense>
);
const NotFoundPage = () => <Layout title="Not Found">Page not found</Layout>;

// Protected route component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Admin route component
const AdminRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role !== 'admin') {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

function App() {
  const dispatch = useDispatch();
  const { theme: themeMode } = useSelector((state: RootState) => state.ui);

  // Check authentication status on app load
  useEffect(() => {
    dispatch(authService.checkAuth() as any);
  }, [dispatch]);

  // Create theme based on the theme mode from Redux store
  const theme = createTheme({
    palette: {
      mode: themeMode as 'light' | 'dark',
      primary: {
        main: '#1976d2',
      },
      secondary: {
        main: '#dc004e',
      },
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    },
  });

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/shared" element={<SharedQuery />} />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout title="Dashboard">
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/query"
            element={
              <ProtectedRoute>
                <QueryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <HistoryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/saved"
            element={
              <ProtectedRoute>
                <SavedQueriesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/databases"
            element={
              <ProtectedRoute>
                <DatabasesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/feedback"
            element={
              <ProtectedRoute>
                <FeedbackPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <UserProfile />
              </ProtectedRoute>
            }
          />

          {/* Admin routes */}
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <Layout title="Admin Dashboard">
                  <AdminDashboard />
                </Layout>
              </AdminRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <AdminRoute>
                <Layout title="User Management">
                  <React.Suspense fallback={<div>Loading...</div>}>
                    {React.createElement(React.lazy(() => import('./pages/admin/UserManagement')))}
                  </React.Suspense>
                </Layout>
              </AdminRoute>
            }
          />
          <Route
            path="/admin/users/:userId"
            element={
              <AdminRoute>
                <Layout title="User Details">
                  <React.Suspense fallback={<div>Loading...</div>}>
                    {React.createElement(React.lazy(() => import('./pages/admin/UserDetail')))}
                  </React.Suspense>
                </Layout>
              </AdminRoute>
            }
          />
          <Route
            path="/admin/policies"
            element={
              <AdminRoute>
                <Layout title="Policy Management">
                  <React.Suspense fallback={<div>Loading...</div>}>
                    {React.createElement(
                      React.lazy(() => import('./pages/admin/PolicyManagement'))
                    )}
                  </React.Suspense>
                </Layout>
              </AdminRoute>
            }
          />
          <Route
            path="/admin/policies/:policyId"
            element={
              <AdminRoute>
                <Layout title="Policy Details">
                  <React.Suspense fallback={<div>Loading...</div>}>
                    {React.createElement(React.lazy(() => import('./pages/admin/PolicyDetail')))}
                  </React.Suspense>
                </Layout>
              </AdminRoute>
            }
          />
          <Route
            path="/admin/settings"
            element={
              <AdminRoute>
                <Layout title="System Settings">
                  <SystemSettingsPage />
                </Layout>
              </AdminRoute>
            }
          />

          {/* Not found route */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
