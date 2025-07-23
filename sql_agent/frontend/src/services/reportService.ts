import { AppDispatch } from '../store';
import { 
  startReportGeneration, 
  updateReportProgress, 
  reportGenerationSuccess, 
  reportGenerationFailure,
  Report
} from '../store/slices/reportSlice';
import { resultAPI } from './api';

export const reportService = {
  generateReport: (resultId: string, visualizationTypes: string[] = [], includeInsights: boolean = true) => 
    async (dispatch: AppDispatch) => {
      dispatch(startReportGeneration());
      
      try {
        // Start report generation
        const response = await resultAPI.generateReport(resultId, visualizationTypes, includeInsights);
        const reportId = response.data.reportId;
        
        // Poll for report status
        let isComplete = false;
        let progress = 0;
        
        while (!isComplete) {
          await new Promise(resolve => setTimeout(resolve, 1000)); // Poll every second
          
          const statusResponse = await resultAPI.getReport(reportId);
          const status = statusResponse.data;
          
          if (status.status === 'completed') {
            isComplete = true;
            dispatch(reportGenerationSuccess(status.report as Report));
          } else if (status.status === 'failed') {
            throw new Error(status.error || '리포트 생성에 실패했습니다.');
          } else {
            // Update progress
            progress = status.progress || progress;
            dispatch(updateReportProgress({
              progress,
              statusMessage: status.statusMessage || `리포트 생성 중... (${progress}%)`
            }));
          }
        }
        
        return reportId;
      } catch (error: any) {
        dispatch(reportGenerationFailure(error.message || '리포트 생성 중 오류가 발생했습니다.'));
        throw error;
      }
    },
    
  getReport: (reportId: string) => 
    async (dispatch: AppDispatch) => {
      try {
        const response = await resultAPI.getReport(reportId);
        const report = response.data.report as Report;
        dispatch(reportGenerationSuccess(report));
        return report;
      } catch (error: any) {
        dispatch(reportGenerationFailure(error.message || '리포트 조회 중 오류가 발생했습니다.'));
        throw error;
      }
    }
};