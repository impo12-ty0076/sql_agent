import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import {
  adminService,
  SystemStats,
  SystemStatus,
  LogEntry,
  LogFilter,
  ChartData,
} from '../../services/adminService';
import {
  User,
  UserFilter,
  Policy,
  PolicyFilter,
  UserPermissions,
  PolicySettings,
  Database,
} from '../../types/admin';

// Define the state interface
interface AdminState {
  stats: {
    data: SystemStats | null;
    loading: boolean;
    error: string | null;
  };
  status: {
    data: SystemStatus | null;
    loading: boolean;
    error: string | null;
  };
  logs: {
    data: LogEntry[];
    loading: boolean;
    error: string | null;
    filter: LogFilter;
  };
  usageStats: {
    data: ChartData | null;
    loading: boolean;
    error: string | null;
    period: 'day' | 'week' | 'month';
  };
  errorStats: {
    data: ChartData | null;
    loading: boolean;
    error: string | null;
    period: 'day' | 'week' | 'month';
  };
  performanceMetrics: {
    data: ChartData | null;
    loading: boolean;
    error: string | null;
    period: 'day' | 'week' | 'month';
  };
  users: {
    data: User[];
    selectedUser: User | null;
    loading: boolean;
    error: string | null;
    filter: UserFilter;
  };
  policies: {
    data: Policy[];
    selectedPolicy: Policy | null;
    loading: boolean;
    error: string | null;
    filter: PolicyFilter;
  };
  databases: {
    data: Database[];
    loading: boolean;
    error: string | null;
  };
}

// Initial state
const initialState: AdminState = {
  stats: {
    data: null,
    loading: false,
    error: null,
  },
  status: {
    data: null,
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
  users: {
    data: [],
    selectedUser: null,
    loading: false,
    error: null,
    filter: {},
  },
  policies: {
    data: [],
    selectedPolicy: null,
    loading: false,
    error: null,
    filter: {},
  },
  databases: {
    data: [],
    loading: false,
    error: null,
  },
};

// Async thunks
export const fetchSystemStats = createAsyncThunk(
  'admin/fetchSystemStats',
  async (_, { rejectWithValue }) => {
    try {
      return await adminService.getSystemStats();
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch system stats');
    }
  }
);

export const fetchSystemStatus = createAsyncThunk(
  'admin/fetchSystemStatus',
  async (_, { rejectWithValue }) => {
    try {
      return await adminService.getSystemStatus();
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch system status');
    }
  }
);

export const fetchLogs = createAsyncThunk(
  'admin/fetchLogs',
  async (filter: LogFilter | undefined, { rejectWithValue }) => {
    try {
      return await adminService.getLogs(filter);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch logs');
    }
  }
);

export const fetchUsageStats = createAsyncThunk(
  'admin/fetchUsageStats',
  async (period: 'day' | 'week' | 'month', { rejectWithValue }) => {
    try {
      return await adminService.getUsageStats(period);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch usage stats');
    }
  }
);

export const fetchErrorStats = createAsyncThunk(
  'admin/fetchErrorStats',
  async (period: 'day' | 'week' | 'month', { rejectWithValue }) => {
    try {
      return await adminService.getErrorStats(period);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch error stats');
    }
  }
);

export const fetchPerformanceMetrics = createAsyncThunk(
  'admin/fetchPerformanceMetrics',
  async (period: 'day' | 'week' | 'month', { rejectWithValue }) => {
    try {
      return await adminService.getPerformanceMetrics(period);
    } catch (error: any) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch performance metrics'
      );
    }
  }
);

// User management thunks
export const fetchUsers = createAsyncThunk(
  'admin/fetchUsers',
  async (filter: UserFilter | undefined, { rejectWithValue }) => {
    try {
      return await adminService.getUsers(filter);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch users');
    }
  }
);

export const fetchUserById = createAsyncThunk(
  'admin/fetchUserById',
  async (userId: string, { rejectWithValue }) => {
    try {
      return await adminService.getUserById(userId);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch user');
    }
  }
);

export const updateUserStatus = createAsyncThunk(
  'admin/updateUserStatus',
  async (
    { userId, status }: { userId: string; status: 'active' | 'inactive' | 'suspended' },
    { rejectWithValue }
  ) => {
    try {
      return await adminService.updateUserStatus(userId, status);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to update user status');
    }
  }
);

export const updateUserRole = createAsyncThunk(
  'admin/updateUserRole',
  async ({ userId, role }: { userId: string; role: 'user' | 'admin' }, { rejectWithValue }) => {
    try {
      return await adminService.updateUserRole(userId, role);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to update user role');
    }
  }
);

export const updateUserPermissions = createAsyncThunk(
  'admin/updateUserPermissions',
  async (
    { userId, permissions }: { userId: string; permissions: UserPermissions },
    { rejectWithValue }
  ) => {
    try {
      return await adminService.updateUserPermissions(userId, permissions);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to update user permissions');
    }
  }
);

// Policy management thunks
export const fetchPolicies = createAsyncThunk(
  'admin/fetchPolicies',
  async (filter: PolicyFilter | undefined, { rejectWithValue }) => {
    try {
      return await adminService.getPolicies(filter);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch policies');
    }
  }
);

export const fetchPolicyById = createAsyncThunk(
  'admin/fetchPolicyById',
  async (policyId: string, { rejectWithValue }) => {
    try {
      return await adminService.getPolicyById(policyId);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch policy');
    }
  }
);

export const createPolicy = createAsyncThunk(
  'admin/createPolicy',
  async (
    policy: Omit<Policy, 'id' | 'createdAt' | 'updatedAt' | 'appliedToUsers'>,
    { rejectWithValue }
  ) => {
    try {
      return await adminService.createPolicy(policy);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to create policy');
    }
  }
);

export const updatePolicy = createAsyncThunk(
  'admin/updatePolicy',
  async (
    { policyId, policy }: { policyId: string; policy: Partial<Policy> },
    { rejectWithValue }
  ) => {
    try {
      return await adminService.updatePolicy(policyId, policy);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to update policy');
    }
  }
);

export const deletePolicy = createAsyncThunk(
  'admin/deletePolicy',
  async (policyId: string, { rejectWithValue }) => {
    try {
      await adminService.deletePolicy(policyId);
      return policyId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to delete policy');
    }
  }
);

export const applyPolicyToUser = createAsyncThunk(
  'admin/applyPolicyToUser',
  async ({ policyId, userId }: { policyId: string; userId: string }, { rejectWithValue }) => {
    try {
      await adminService.applyPolicyToUser(policyId, userId);
      return { policyId, userId };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to apply policy to user');
    }
  }
);

export const removePolicyFromUser = createAsyncThunk(
  'admin/removePolicyFromUser',
  async ({ policyId, userId }: { policyId: string; userId: string }, { rejectWithValue }) => {
    try {
      await adminService.removePolicyFromUser(policyId, userId);
      return { policyId, userId };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to remove policy from user');
    }
  }
);

export const fetchDatabases = createAsyncThunk(
  'admin/fetchDatabases',
  async (_, { rejectWithValue }) => {
    try {
      return await adminService.getDatabases();
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch databases');
    }
  }
);

// Create the slice
const adminSlice = createSlice({
  name: 'admin',
  initialState,
  reducers: {
    setLogFilter: (state, action: PayloadAction<LogFilter>) => {
      state.logs.filter = action.payload;
    },
    setUsageStatsPeriod: (state, action: PayloadAction<'day' | 'week' | 'month'>) => {
      state.usageStats.period = action.payload;
    },
    setErrorStatsPeriod: (state, action: PayloadAction<'day' | 'week' | 'month'>) => {
      state.errorStats.period = action.payload;
    },
    setPerformanceMetricsPeriod: (state, action: PayloadAction<'day' | 'week' | 'month'>) => {
      state.performanceMetrics.period = action.payload;
    },
    setUserFilter: (state, action: PayloadAction<UserFilter>) => {
      state.users.filter = action.payload;
    },
    setPolicyFilter: (state, action: PayloadAction<PolicyFilter>) => {
      state.policies.filter = action.payload;
    },
    clearSelectedUser: state => {
      state.users.selectedUser = null;
    },
    clearSelectedPolicy: state => {
      state.policies.selectedPolicy = null;
    },
  },
  extraReducers: builder => {
    // System Stats
    builder.addCase(fetchSystemStats.pending, state => {
      state.stats.loading = true;
      state.stats.error = null;
    });
    builder.addCase(fetchSystemStats.fulfilled, (state, action) => {
      state.stats.loading = false;
      state.stats.data = action.payload;
    });
    builder.addCase(fetchSystemStats.rejected, (state, action) => {
      state.stats.loading = false;
      state.stats.error = action.payload as string;
    });

    // System Status
    builder.addCase(fetchSystemStatus.pending, state => {
      state.status.loading = true;
      state.status.error = null;
    });
    builder.addCase(fetchSystemStatus.fulfilled, (state, action) => {
      state.status.loading = false;
      state.status.data = action.payload;
    });
    builder.addCase(fetchSystemStatus.rejected, (state, action) => {
      state.status.loading = false;
      state.status.error = action.payload as string;
    });

    // Logs
    builder.addCase(fetchLogs.pending, state => {
      state.logs.loading = true;
      state.logs.error = null;
    });
    builder.addCase(fetchLogs.fulfilled, (state, action) => {
      state.logs.loading = false;
      state.logs.data = action.payload;
    });
    builder.addCase(fetchLogs.rejected, (state, action) => {
      state.logs.loading = false;
      state.logs.error = action.payload as string;
    });

    // Usage Stats
    builder.addCase(fetchUsageStats.pending, state => {
      state.usageStats.loading = true;
      state.usageStats.error = null;
    });
    builder.addCase(fetchUsageStats.fulfilled, (state, action) => {
      state.usageStats.loading = false;
      state.usageStats.data = action.payload;
    });
    builder.addCase(fetchUsageStats.rejected, (state, action) => {
      state.usageStats.loading = false;
      state.usageStats.error = action.payload as string;
    });

    // Error Stats
    builder.addCase(fetchErrorStats.pending, state => {
      state.errorStats.loading = true;
      state.errorStats.error = null;
    });
    builder.addCase(fetchErrorStats.fulfilled, (state, action) => {
      state.errorStats.loading = false;
      state.errorStats.data = action.payload;
    });
    builder.addCase(fetchErrorStats.rejected, (state, action) => {
      state.errorStats.loading = false;
      state.errorStats.error = action.payload as string;
    });

    // Performance Metrics
    builder.addCase(fetchPerformanceMetrics.pending, state => {
      state.performanceMetrics.loading = true;
      state.performanceMetrics.error = null;
    });
    builder.addCase(fetchPerformanceMetrics.fulfilled, (state, action) => {
      state.performanceMetrics.loading = false;
      state.performanceMetrics.data = action.payload;
    });
    builder.addCase(fetchPerformanceMetrics.rejected, (state, action) => {
      state.performanceMetrics.loading = false;
      state.performanceMetrics.error = action.payload as string;
    });

    // Users
    builder.addCase(fetchUsers.pending, state => {
      state.users.loading = true;
      state.users.error = null;
    });
    builder.addCase(fetchUsers.fulfilled, (state, action) => {
      state.users.loading = false;
      state.users.data = action.payload;
    });
    builder.addCase(fetchUsers.rejected, (state, action) => {
      state.users.loading = false;
      state.users.error = action.payload as string;
    });

    builder.addCase(fetchUserById.pending, state => {
      state.users.loading = true;
      state.users.error = null;
    });
    builder.addCase(fetchUserById.fulfilled, (state, action) => {
      state.users.loading = false;
      state.users.selectedUser = action.payload;
    });
    builder.addCase(fetchUserById.rejected, (state, action) => {
      state.users.loading = false;
      state.users.error = action.payload as string;
    });

    builder.addCase(updateUserStatus.fulfilled, (state, action) => {
      const updatedUser = action.payload;
      state.users.data = state.users.data.map(user =>
        user.id === updatedUser.id ? updatedUser : user
      );
      if (state.users.selectedUser?.id === updatedUser.id) {
        state.users.selectedUser = updatedUser;
      }
    });

    builder.addCase(updateUserRole.fulfilled, (state, action) => {
      const updatedUser = action.payload;
      state.users.data = state.users.data.map(user =>
        user.id === updatedUser.id ? updatedUser : user
      );
      if (state.users.selectedUser?.id === updatedUser.id) {
        state.users.selectedUser = updatedUser;
      }
    });

    builder.addCase(updateUserPermissions.fulfilled, (state, action) => {
      const updatedUser = action.payload;
      state.users.data = state.users.data.map(user =>
        user.id === updatedUser.id ? updatedUser : user
      );
      if (state.users.selectedUser?.id === updatedUser.id) {
        state.users.selectedUser = updatedUser;
      }
    });

    // Policies
    builder.addCase(fetchPolicies.pending, state => {
      state.policies.loading = true;
      state.policies.error = null;
    });
    builder.addCase(fetchPolicies.fulfilled, (state, action) => {
      state.policies.loading = false;
      state.policies.data = action.payload;
    });
    builder.addCase(fetchPolicies.rejected, (state, action) => {
      state.policies.loading = false;
      state.policies.error = action.payload as string;
    });

    builder.addCase(fetchPolicyById.pending, state => {
      state.policies.loading = true;
      state.policies.error = null;
    });
    builder.addCase(fetchPolicyById.fulfilled, (state, action) => {
      state.policies.loading = false;
      state.policies.selectedPolicy = action.payload;
    });
    builder.addCase(fetchPolicyById.rejected, (state, action) => {
      state.policies.loading = false;
      state.policies.error = action.payload as string;
    });

    builder.addCase(createPolicy.fulfilled, (state, action) => {
      state.policies.data = [...state.policies.data, action.payload];
    });

    builder.addCase(updatePolicy.fulfilled, (state, action) => {
      const updatedPolicy = action.payload;
      state.policies.data = state.policies.data.map(policy =>
        policy.id === updatedPolicy.id ? updatedPolicy : policy
      );
      if (state.policies.selectedPolicy?.id === updatedPolicy.id) {
        state.policies.selectedPolicy = updatedPolicy;
      }
    });

    builder.addCase(deletePolicy.fulfilled, (state, action) => {
      const policyId = action.payload;
      state.policies.data = state.policies.data.filter(policy => policy.id !== policyId);
      if (state.policies.selectedPolicy?.id === policyId) {
        state.policies.selectedPolicy = null;
      }
    });

    // Databases
    builder.addCase(fetchDatabases.pending, state => {
      state.databases.loading = true;
      state.databases.error = null;
    });
    builder.addCase(fetchDatabases.fulfilled, (state, action) => {
      state.databases.loading = false;
      state.databases.data = action.payload;
    });
    builder.addCase(fetchDatabases.rejected, (state, action) => {
      state.databases.loading = false;
      state.databases.error = action.payload as string;
    });
  },
});

// Export actions and reducer
export const {
  setLogFilter,
  setUsageStatsPeriod,
  setErrorStatsPeriod,
  setPerformanceMetricsPeriod,
  setUserFilter,
  setPolicyFilter,
  clearSelectedUser,
  clearSelectedPolicy,
} = adminSlice.actions;

export default adminSlice.reducer;
