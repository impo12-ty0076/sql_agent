import { AppDispatch } from '../store';
import { 
  executeQueryStart, 
  executeQuerySuccess, 
  executeQueryFailure,
  setCurrentQuery,
  setGeneratedSql,
  setUseRag
} from '../store/slices/querySlice';
import { queryAPI } from './api';

export interface NaturalLanguageQueryResult {
  queryId: string;
  generatedSql: string;
  status: 'pending' | 'executing' | 'completed' | 'failed';
  error?: string;
}

export interface SqlExecutionResult {
  columns: { name: string; type: string }[];
  rows: any[][];
  rowCount: number;
  executionTime: number;
  truncated: boolean;
  totalRowCount?: number;
  resultId?: string;
}

export const queryService = {
  processNaturalLanguage: (dbId: string, query: string, useRag: boolean = false) => 
    async (dispatch: AppDispatch) => {
      dispatch(executeQueryStart());
      dispatch(setCurrentQuery(query));
      dispatch(setUseRag(useRag));
      
      try {
        const response = await queryAPI.processNaturalLanguage(dbId, query, useRag);
        const result = response.data as NaturalLanguageQueryResult;
        dispatch(setGeneratedSql(result.generatedSql));
        return result;
      } catch (error: any) {
        dispatch(executeQueryFailure(error.response?.data?.message || '자연어 처리 중 오류가 발생했습니다.'));
        throw error;
      }
    },
    
  executeQuery: (dbId: string, sql: string) => 
    async (dispatch: AppDispatch) => {
      dispatch(executeQueryStart());
      
      try {
        const response = await queryAPI.executeQuery(dbId, sql);
        const result = response.data as SqlExecutionResult;
        dispatch(executeQuerySuccess({
          columns: result.columns.map(col => col.name),
          rows: result.rows,
          rowCount: result.rowCount,
          executionTime: result.executionTime,
          resultId: result.resultId
        }));
        return result;
      } catch (error: any) {
        dispatch(executeQueryFailure(error.response?.data?.message || 'SQL 실행 중 오류가 발생했습니다.'));
        throw error;
      }
    },
    
  getQueryStatus: async (queryId: string) => {
    try {
      const response = await queryAPI.getQueryStatus(queryId);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  cancelQuery: async (queryId: string) => {
    try {
      const response = await queryAPI.cancelQuery(queryId);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
};