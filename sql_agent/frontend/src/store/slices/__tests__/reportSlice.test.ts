import reportReducer, {
  toggleReportGeneration,
  updateReportOptions,
  startReportGeneration,
  updateReportProgress,
  reportGenerationSuccess,
  reportGenerationFailure,
  clearReport,
} from '../reportSlice';

describe('reportSlice', () => {
  const initialState = {
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

  it('should handle initial state', () => {
    expect(reportReducer(undefined, { type: 'unknown' })).toEqual(initialState);
  });

  it('should handle toggleReportGeneration', () => {
    const actual = reportReducer(initialState, toggleReportGeneration(true));
    expect(actual.reportGenerationEnabled).toEqual(true);
  });

  it('should handle updateReportOptions', () => {
    const actual = reportReducer(
      initialState,
      updateReportOptions({
        visualizationTypes: ['bar', 'scatter'],
        includeInsights: false,
      })
    );
    expect(actual.reportGenerationOptions).toEqual({
      visualizationTypes: ['bar', 'scatter'],
      includeInsights: false,
    });
  });

  it('should handle startReportGeneration', () => {
    const actual = reportReducer(initialState, startReportGeneration());
    expect(actual.reportGenerationStatus).toEqual({
      isGenerating: true,
      progress: 0,
      statusMessage: '리포트 생성 준비 중...',
    });
    expect(actual.error).toBeNull();
  });

  it('should handle updateReportProgress', () => {
    const actual = reportReducer(
      initialState,
      updateReportProgress({
        progress: 50,
        statusMessage: '데이터 분석 중...',
      })
    );
    expect(actual.reportGenerationStatus.progress).toEqual(50);
    expect(actual.reportGenerationStatus.statusMessage).toEqual('데이터 분석 중...');
  });

  it('should handle reportGenerationSuccess', () => {
    const mockReport = {
      id: 'report-1',
      resultId: 'result-1',
      visualizations: [],
      insights: [],
      createdAt: '2023-09-15T10:30:00Z',
    };

    const actual = reportReducer(initialState, reportGenerationSuccess(mockReport));
    expect(actual.currentReport).toEqual(mockReport);
    expect(actual.reportGenerationStatus.isGenerating).toEqual(false);
    expect(actual.reportGenerationStatus.progress).toEqual(100);
  });

  it('should handle reportGenerationFailure', () => {
    const actual = reportReducer(initialState, reportGenerationFailure('오류 발생'));
    expect(actual.error).toEqual('오류 발생');
    expect(actual.reportGenerationStatus.isGenerating).toEqual(false);
  });

  it('should handle clearReport', () => {
    const stateWithReport = {
      ...initialState,
      currentReport: {
        id: 'report-1',
        resultId: 'result-1',
        visualizations: [],
        insights: [],
        createdAt: '2023-09-15T10:30:00Z',
      },
      reportGenerationStatus: {
        isGenerating: false,
        progress: 100,
        statusMessage: '리포트 생성 완료',
      },
    };

    const actual = reportReducer(stateWithReport, clearReport());
    expect(actual.currentReport).toBeNull();
    expect(actual.reportGenerationStatus.progress).toEqual(0);
    expect(actual.reportGenerationStatus.statusMessage).toEqual('');
  });
});
