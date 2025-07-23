import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Visualization {
  id: string;
  type: 'bar' | 'line' | 'pie' | 'scatter' | 'heatmap' | 'custom';
  title: string;
  description?: string;
  imageData: string; // Base64 encoded image
}

export interface Report {
  id: string;
  resultId: string;
  visualizations: Visualization[];
  insights: string[];
  createdAt: string;
}

export interface ReportState {
  currentReport: Report | null;
  reportGenerationEnabled: boolean;
  reportGenerationOptions: {
    visualizationTypes: string[];
    includeInsights: boolean;
  };
  reportGenerationStatus: {
    isGenerating: boolean;
    progress: number; // 0-100
    statusMessage: string;
  };
  error: string | null;
}

const initialState: ReportState = {
  currentReport: null,
  reportGenerationEnabled: false,
  reportGenerationOptions: {
    visualizationTypes: ['bar', 'line', 'pie'],
    includeInsights: true,
  },
  reportGenerationStatus: {
    isGenerating: false,
    progress: 0,
    statusMessage: '',
  },
  error: null,
};

const reportSlice = createSlice({
  name: 'report',
  initialState,
  reducers: {
    toggleReportGeneration: (state, action: PayloadAction<boolean>) => {
      state.reportGenerationEnabled = action.payload;
    },
    updateReportOptions: (state, action: PayloadAction<{
      visualizationTypes?: string[];
      includeInsights?: boolean;
    }>) => {
      if (action.payload.visualizationTypes !== undefined) {
        state.reportGenerationOptions.visualizationTypes = action.payload.visualizationTypes;
      }
      if (action.payload.includeInsights !== undefined) {
        state.reportGenerationOptions.includeInsights = action.payload.includeInsights;
      }
    },
    startReportGeneration: (state) => {
      state.reportGenerationStatus.isGenerating = true;
      state.reportGenerationStatus.progress = 0;
      state.reportGenerationStatus.statusMessage = '리포트 생성 준비 중...';
      state.error = null;
    },
    updateReportProgress: (state, action: PayloadAction<{
      progress: number;
      statusMessage: string;
    }>) => {
      state.reportGenerationStatus.progress = action.payload.progress;
      state.reportGenerationStatus.statusMessage = action.payload.statusMessage;
    },
    reportGenerationSuccess: (state, action: PayloadAction<Report>) => {
      state.currentReport = action.payload;
      state.reportGenerationStatus.isGenerating = false;
      state.reportGenerationStatus.progress = 100;
      state.reportGenerationStatus.statusMessage = '리포트 생성 완료';
    },
    reportGenerationFailure: (state, action: PayloadAction<string>) => {
      state.reportGenerationStatus.isGenerating = false;
      state.error = action.payload;
    },
    clearReport: (state) => {
      state.currentReport = null;
      state.reportGenerationStatus.progress = 0;
      state.reportGenerationStatus.statusMessage = '';
    },
  },
});

export const {
  toggleReportGeneration,
  updateReportOptions,
  startReportGeneration,
  updateReportProgress,
  reportGenerationSuccess,
  reportGenerationFailure,
  clearReport,
} = reportSlice.actions;

export default reportSlice.reducer;