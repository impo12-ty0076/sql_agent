import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import AdminDashboard from '../AdminDashboard';

// Mock the components
jest.mock('../../../components/admin/StatisticsCard', () => ({
    __esModule: true,
    default: ({ title }: { title: string }) => <div data-testid={`statistics-card-${title}`}>{title}</div>,
}));

jest.mock('../../../components/admin/ChartCard', () => ({
    __esModule: true,
    default: ({ title }: { title: string }) => <div data-testid={`chart-card-${title}`}>{title}</div>,
}));

jest.mock('../../../components/admin/SystemStatusCard', () => ({
    __esModule: true,
    default: () => <div data-testid="system-status-card">System Status Card</div>,
}));

jest.mock('../../../components/admin/LogsTable', () => ({
    __esModule: true,
    default: () => <div data-testid="logs-table">Logs Table</div>,
}));

// Create mock store without middleware for testing
const mockStore = configureStore([]);

describe('AdminDashboard', () => {
    let store: any;

    beforeEach(() => {
        store = mockStore({
            admin: {
                stats: {
                    data: {
                        totalUsers: 100,
                        activeUsers: 50,
                        totalQueries: 1000,
                        queriesLastDay: 200,
                        averageResponseTime: 150,
                        errorRate: 2.5,
                    },
                    loading: false,
                    error: null,
                },
                status: {
                    data: {
                        status: 'healthy',
                        components: {
                            database: 'healthy',
                            api: 'healthy',
                            llm: 'healthy',
                            storage: 'healthy',
                        },
                        uptime: 86400,
                        lastChecked: '2025-07-23T12:00:00Z',
                    },
                    loading: false,
                    error: null,
                },
                logs: {
                    data: [],
                    loading: false,
                    error: null,
                    filter: {},
                },
                usageStats: {
                    data: null,
                    loading: false,
                    error: null,
                    period: 'day',
                },
                errorStats: {
                    data: null,
                    loading: false,
                    error: null,
                    period: 'day',
                },
                performanceMetrics: {
                    data: null,
                    loading: false,
                    error: null,
                    period: 'day',
                },
            },
        });

        // Mock dispatch
        store.dispatch = jest.fn();
    });

    test('renders dashboard title and sections', () => {
        render(
            <Provider store={store}>
                <AdminDashboard />
            </Provider>
        );

        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
        expect(screen.getByText('System Overview')).toBeInTheDocument();
        expect(screen.getByText('Usage Analytics')).toBeInTheDocument();
        expect(screen.getByText('System Logs')).toBeInTheDocument();
    });

    test('renders statistics cards', () => {
        render(
            <Provider store={store}>
                <AdminDashboard />
            </Provider>
        );

        expect(screen.getByTestId('statistics-card-Total Users')).toBeInTheDocument();
        expect(screen.getByTestId('statistics-card-Active Users')).toBeInTheDocument();
        expect(screen.getByTestId('statistics-card-Total Queries')).toBeInTheDocument();
        expect(screen.getByTestId('statistics-card-Queries (Last 24h)')).toBeInTheDocument();
        expect(screen.getByTestId('statistics-card-Avg Response Time')).toBeInTheDocument();
        expect(screen.getByTestId('statistics-card-Error Rate')).toBeInTheDocument();
    });

    test('renders system status card', () => {
        render(
            <Provider store={store}>
                <AdminDashboard />
            </Provider>
        );

        expect(screen.getByTestId('system-status-card')).toBeInTheDocument();
    });

    test('renders chart cards', () => {
        render(
            <Provider store={store}>
                <AdminDashboard />
            </Provider>
        );

        expect(screen.getByTestId('chart-card-Query Usage')).toBeInTheDocument();
        expect(screen.getByTestId('chart-card-Error Distribution')).toBeInTheDocument();
        expect(screen.getByTestId('chart-card-System Performance')).toBeInTheDocument();
    });

    test('renders logs table', () => {
        render(
            <Provider store={store}>
                <AdminDashboard />
            </Provider>
        );

        expect(screen.getByTestId('logs-table')).toBeInTheDocument();
    });

    test('dispatches initial data fetch actions', () => {
        render(
            <Provider store={store}>
                <AdminDashboard />
            </Provider>
        );

        // Should dispatch 6 actions on mount
        expect(store.dispatch).toHaveBeenCalledTimes(6);
    });
});