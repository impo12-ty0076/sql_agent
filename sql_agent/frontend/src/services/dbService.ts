import { AppDispatch } from '../store';
import { databaseAPI } from './api';
import {
  fetchDatabasesStart,
  fetchDatabasesSuccess,
  fetchDatabasesFailure,
  selectDatabase,
  fetchTablesStart,
  fetchTablesSuccess,
  fetchTablesFailure,
  Database,
  Table,
} from '../store/slices/dbSlice';

export const dbService = {
  // 사용자가 접근 가능한 데이터베이스 목록 조회
  fetchDatabases: () => async (dispatch: AppDispatch) => {
    try {
      dispatch(fetchDatabasesStart());
      const response = await databaseAPI.listDatabases();
      dispatch(fetchDatabasesSuccess(response.data));
      return response.data;
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || '데이터베이스 목록을 불러오는데 실패했습니다.';
      dispatch(fetchDatabasesFailure(errorMessage));
      throw error;
    }
  },

  // 데이터베이스 연결
  connectToDatabase: (dbId: string) => async (dispatch: AppDispatch) => {
    try {
      dispatch(fetchDatabasesStart());
      const response = await databaseAPI.connectDatabase(dbId);
      
      // 연결 성공 시 해당 DB를 선택 상태로 변경
      const connectedDb: Database = {
        ...response.data,
        connected: true
      };
      
      dispatch(selectDatabase(connectedDb));
      return connectedDb;
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || '데이터베이스 연결에 실패했습니다.';
      dispatch(fetchDatabasesFailure(errorMessage));
      throw error;
    }
  },

  // 데이터베이스 스키마 정보 조회
  fetchDatabaseSchema: (dbId: string) => async (dispatch: AppDispatch) => {
    try {
      dispatch(fetchTablesStart());
      const response = await databaseAPI.getDatabaseSchema(dbId);
      dispatch(fetchTablesSuccess(response.data));
      return response.data;
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || '데이터베이스 스키마를 불러오는데 실패했습니다.';
      dispatch(fetchTablesFailure(errorMessage));
      throw error;
    }
  },

  // 데이터베이스 선택 (이미 연결된 경우)
  selectExistingDatabase: (database: Database) => (dispatch: AppDispatch) => {
    dispatch(selectDatabase(database));
  },
};

export default dbService;