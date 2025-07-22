import { useState, useCallback } from 'react';
import { queryAPI, resultAPI } from '../services/api';

interface UseQueryResult {
  isLoading: boolean;
  error: string | null;
  queryResult: any | null;
  processQuery: (dbId: string, naturalLanguage: string) => Promise<void>;
  getQueryResult: (resultId: string) => Promise<void>;
}

export const useQuery = (): UseQueryResult => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [queryResult, setQueryResult] = useState<any | null>(null);

  const processQuery = useCallback(async (dbId: string, naturalLanguage: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // 자연어 질의 처리
      const nlResponse = await queryAPI.processNaturalLanguage(dbId, naturalLanguage);
      const data = nlResponse.data as { query_id: string; generated_sql: string };
      const { generated_sql } = data;
      
      // SQL 쿼리 실행
      const executeResponse = await queryAPI.executeQuery(dbId, generated_sql);
      const executeData = executeResponse.data as { result_id: string };
      const { result_id } = executeData;
      
      // 쿼리 결과 조회
      await getQueryResult(result_id);
    } catch (err: any) {
      setError(err.response?.data?.message || '쿼리 처리 중 오류가 발생했습니다.');
      setQueryResult(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getQueryResult = useCallback(async (resultId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await resultAPI.getQueryResult(resultId);
      setQueryResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || '결과 조회 중 오류가 발생했습니다.');
      setQueryResult(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    isLoading,
    error,
    queryResult,
    processQuery,
    getQueryResult,
  };
};

export default useQuery;