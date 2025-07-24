import { reportService } from '../reportService';
import { resultAPI } from '../api';
import {
  startReportGeneration,
  updateReportProgress,
  reportGenerationSuccess,
  reportGenerationFailure,
} from '../../store/slices/reportSlice';

// Mock the API
jest.mock('../api', () => ({
  resultAPI: {
    generateReport: jest.fn(),
    getReport: jest.fn(),
  },
}));

describe('reportService', () => {
  let dispatch: jest.Mock;

  beforeEach(() => {
    dispatch = jest.fn();
    jest.clearAllMocks();
  });

  describe('generateReport', () => {
    it('should handle successful report generation', async () => {
      // Mock API responses
      (resultAPI.generateReport as jest.Mock).mockResolvedValue({
        data: { reportId: 'report-123' },
      });

      // First call returns in-progress status
      (resultAPI.getReport as jest.Mock).mockResolvedValueOnce({
        data: {
          status: 'in_progress',
          progress: 50,
          statusMessage: '데이터 분석 중...',
        },
      });

      // Second call returns completed status with report
      const mockReport = {
        id: 'report-123',
        resultId: 'result-456',
        visualizations: [],
        insights: [],
        createdAt: new Date().toISOString(),
      };

      (resultAPI.getReport as jest.Mock).mockResolvedValueOnce({
        data: {
          status: 'completed',
          report: mockReport,
        },
      });

      // Mock setTimeout to resolve immediately
      jest.spyOn(global, 'setTimeout').mockImplementation((cb: any) => {
        cb();
        return {} as any;
      });

      // Call the service
      await reportService.generateReport('result-456', ['bar', 'line'], true)(dispatch);

      // Verify dispatch calls
      expect(dispatch).toHaveBeenCalledWith(startReportGeneration());
      expect(dispatch).toHaveBeenCalledWith(
        updateReportProgress({
          progress: 50,
          statusMessage: '데이터 분석 중...',
        })
      );
      expect(dispatch).toHaveBeenCalledWith(reportGenerationSuccess(mockReport));

      // Verify API calls
      expect(resultAPI.generateReport).toHaveBeenCalledWith('result-456', ['bar', 'line'], true);
      expect(resultAPI.getReport).toHaveBeenCalledWith('report-123');
    });

    it('should handle failed report generation', async () => {
      // Mock API responses
      (resultAPI.generateReport as jest.Mock).mockResolvedValue({
        data: { reportId: 'report-123' },
      });

      // Report generation failed
      (resultAPI.getReport as jest.Mock).mockResolvedValueOnce({
        data: {
          status: 'failed',
          error: '데이터 분석 중 오류가 발생했습니다.',
        },
      });

      // Mock setTimeout to resolve immediately
      jest.spyOn(global, 'setTimeout').mockImplementation((cb: any) => {
        cb();
        return {} as any;
      });

      // Call the service and expect it to throw
      try {
        await reportService.generateReport('result-456', ['bar', 'line'], true)(dispatch);
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).toBe('데이터 분석 중 오류가 발생했습니다.');
      }

      // Verify dispatch calls
      expect(dispatch).toHaveBeenCalledWith(startReportGeneration());
      expect(dispatch).toHaveBeenCalledWith(
        reportGenerationFailure('데이터 분석 중 오류가 발생했습니다.')
      );
    });
  });

  describe('getReport', () => {
    it('should fetch an existing report', async () => {
      const mockReport = {
        id: 'report-123',
        resultId: 'result-456',
        visualizations: [],
        insights: [],
        createdAt: new Date().toISOString(),
      };

      (resultAPI.getReport as jest.Mock).mockResolvedValue({
        data: {
          report: mockReport,
        },
      });

      await reportService.getReport('report-123')(dispatch);

      expect(dispatch).toHaveBeenCalledWith(reportGenerationSuccess(mockReport));
      expect(resultAPI.getReport).toHaveBeenCalledWith('report-123');
    });

    it('should handle errors when fetching a report', async () => {
      (resultAPI.getReport as jest.Mock).mockRejectedValue({
        message: '리포트를 찾을 수 없습니다.',
      });

      try {
        await reportService.getReport('report-123')(dispatch);
        fail('Should have thrown an error');
      } catch (error) {
        expect(dispatch).toHaveBeenCalledWith(
          reportGenerationFailure('리포트를 찾을 수 없습니다.')
        );
      }
    });
  });
});
