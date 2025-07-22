"""
결과 요약 서비스

이 모듈은 쿼리 결과 데이터 분석, 자연어 요약 생성, 인사이트 추출 기능을 제공합니다.
"""
from typing import Dict, Any, List, Optional, Tuple, Union
import logging
import statistics
import json
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
import numpy as np

from ..llm.base import LLMService

logger = logging.getLogger(__name__)

class ResultSummaryService:
    """
    쿼리 결과 요약 서비스
    
    이 서비스는 SQL 쿼리 결과를 분석하고, 자연어 요약을 생성하며, 주요 인사이트를 추출합니다.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        ResultSummaryService 초기화
        
        Args:
            llm_service (Optional[LLMService]): LLM 서비스 인스턴스
        """
        self.llm_service = llm_service
    
    async def generate_summary(self, 
                              query_result: Dict[str, Any], 
                              natural_language: str, 
                              sql_query: str) -> Dict[str, Any]:
        """
        쿼리 결과에 대한 요약 생성
        
        Args:
            query_result (Dict[str, Any]): 쿼리 실행 결과
            natural_language (str): 원본 자연어 질의
            sql_query (str): 실행된 SQL 쿼리
            
        Returns:
            Dict[str, Any]: 요약 및 인사이트
        """
        try:
            # 기본 통계 분석 수행
            stats = self._analyze_data(query_result)
            
            # LLM 서비스가 있으면 자연어 요약 생성
            if self.llm_service:
                summary_result = await self.llm_service.summarize_results(
                    query_result=query_result,
                    natural_language=natural_language,
                    sql_query=sql_query
                )
                
                # LLM 생성 요약과 통계 분석 결과 병합
                summary_result["statistics"] = stats
                return summary_result
            else:
                # LLM 서비스가 없는 경우 기본 요약만 반환
                return {
                    "summary": "쿼리 결과에 대한 기본 통계 분석입니다.",
                    "insights": self._generate_basic_insights(query_result, stats),
                    "statistics": stats
                }
        except Exception as e:
            logger.error(f"결과 요약 생성 중 오류 발생: {str(e)}")
            return {
                "summary": "결과 요약을 생성하는 중 오류가 발생했습니다.",
                "error": str(e),
                "statistics": {}
            }
    
    def _analyze_data(self, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        쿼리 결과 데이터 분석
        
        Args:
            query_result (Dict[str, Any]): 쿼리 실행 결과
            
        Returns:
            Dict[str, Any]: 데이터 분석 결과
        """
        if not query_result or "columns" not in query_result or "rows" not in query_result:
            return {"error": "유효하지 않은 쿼리 결과 형식"}
        
        columns = query_result["columns"]
        rows = query_result["rows"]
        row_count = len(rows)
        
        if row_count == 0:
            return {"row_count": 0, "message": "결과 데이터가 없습니다."}
        
        # 데이터프레임으로 변환하여 분석
        try:
            df = self._convert_to_dataframe(columns, rows)
            
            # 기본 통계 계산
            stats = {
                "row_count": row_count,
                "column_count": len(columns),
                "column_stats": self._calculate_column_stats(df)
            }
            
            # 시계열 데이터 감지 및 분석
            time_series_columns = self._detect_time_series(df)
            if time_series_columns:
                stats["time_series"] = self._analyze_time_series(df, time_series_columns)
            
            # 상관관계 분석 (수치형 컬럼이 2개 이상인 경우)
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_columns) >= 2:
                stats["correlations"] = self._calculate_correlations(df, numeric_columns)
            
            return stats
        except Exception as e:
            logger.error(f"데이터 분석 중 오류 발생: {str(e)}")
            return {
                "row_count": row_count,
                "error": f"데이터 분석 중 오류 발생: {str(e)}"
            }
    
    def _convert_to_dataframe(self, columns: List[Dict[str, str]], rows: List[List[Any]]) -> pd.DataFrame:
        """
        쿼리 결과를 pandas DataFrame으로 변환
        
        Args:
            columns (List[Dict[str, str]]): 컬럼 정보
            rows (List[List[Any]]): 행 데이터
            
        Returns:
            pd.DataFrame: 변환된 데이터프레임
        """
        column_names = [col["name"] for col in columns]
        
        # JSON 직렬화 가능한 형태로 데이터 변환
        processed_rows = []
        for row in rows:
            processed_row = []
            for value in row:
                if isinstance(value, (datetime, date)):
                    processed_row.append(value.isoformat())
                elif isinstance(value, Decimal):
                    processed_row.append(float(value))
                else:
                    processed_row.append(value)
            processed_rows.append(processed_row)
        
        df = pd.DataFrame(processed_rows, columns=column_names)
        
        # 날짜/시간 컬럼 변환
        for col in columns:
            col_name = col["name"]
            col_type = col["type"].lower()
            if "date" in col_type or "time" in col_type:
                try:
                    df[col_name] = pd.to_datetime(df[col_name])
                except:
                    pass  # 변환 실패 시 원래 형식 유지
        
        return df
    
    def _calculate_column_stats(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        각 컬럼에 대한 통계 계산
        
        Args:
            df (pd.DataFrame): 데이터프레임
            
        Returns:
            Dict[str, Dict[str, Any]]: 컬럼별 통계 정보
        """
        stats = {}
        
        for column in df.columns:
            col_stats = {}
            series = df[column]
            
            # 결측값 통계
            null_count = series.isna().sum()
            col_stats["null_count"] = int(null_count)
            col_stats["null_percentage"] = round(100 * null_count / len(df), 2)
            
            # 데이터 타입에 따른 통계
            if pd.api.types.is_numeric_dtype(series):
                # 수치형 데이터
                non_null = series.dropna()
                if len(non_null) > 0:
                    col_stats["min"] = float(non_null.min())
                    col_stats["max"] = float(non_null.max())
                    col_stats["mean"] = float(non_null.mean())
                    col_stats["median"] = float(non_null.median())
                    col_stats["std"] = float(non_null.std()) if len(non_null) > 1 else 0
                    
                    # 이상치 감지 (IQR 방법)
                    q1 = float(non_null.quantile(0.25))
                    q3 = float(non_null.quantile(0.75))
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    outliers = non_null[(non_null < lower_bound) | (non_null > upper_bound)]
                    col_stats["outlier_count"] = len(outliers)
                    col_stats["outlier_percentage"] = round(100 * len(outliers) / len(non_null), 2)
            
            elif pd.api.types.is_datetime64_dtype(series):
                # 날짜/시간 데이터
                non_null = series.dropna()
                if len(non_null) > 0:
                    col_stats["min"] = non_null.min().isoformat()
                    col_stats["max"] = non_null.max().isoformat()
                    col_stats["range_days"] = (non_null.max() - non_null.min()).days
            
            else:
                # 문자열/범주형 데이터
                non_null = series.dropna()
                if len(non_null) > 0:
                    value_counts = non_null.value_counts()
                    col_stats["unique_count"] = len(value_counts)
                    col_stats["unique_percentage"] = round(100 * len(value_counts) / len(non_null), 2)
                    
                    # 상위 5개 값
                    top_values = value_counts.head(5).to_dict()
                    col_stats["top_values"] = {str(k): int(v) for k, v in top_values.items()}
            
            stats[column] = col_stats
        
        return stats
    
    def _detect_time_series(self, df: pd.DataFrame) -> List[str]:
        """
        시계열 데이터 컬럼 감지
        
        Args:
            df (pd.DataFrame): 데이터프레임
            
        Returns:
            List[str]: 시계열 데이터로 판단되는 컬럼 목록
        """
        time_series_columns = []
        
        for column in df.columns:
            if pd.api.types.is_datetime64_dtype(df[column]):
                # 날짜/시간 컬럼이 정렬되어 있고 고유값이 많으면 시계열로 간주
                unique_ratio = df[column].nunique() / len(df)
                if unique_ratio > 0.1:  # 최소 10% 이상의 값이 고유해야 함
                    time_series_columns.append(column)
        
        return time_series_columns
    
    def _analyze_time_series(self, df: pd.DataFrame, time_columns: List[str]) -> Dict[str, Any]:
        """
        시계열 데이터 분석
        
        Args:
            df (pd.DataFrame): 데이터프레임
            time_columns (List[str]): 시계열 컬럼 목록
            
        Returns:
            Dict[str, Any]: 시계열 분석 결과
        """
        results = {}
        
        for time_col in time_columns:
            # 수치형 컬럼 찾기
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            
            col_results = {
                "frequency": self._detect_time_frequency(df[time_col]),
                "trends": {}
            }
            
            # 각 수치형 컬럼에 대해 시계열 분석
            for num_col in numeric_columns:
                # 결측값 제거 후 시간순 정렬
                temp_df = df[[time_col, num_col]].dropna().sort_values(by=time_col)
                
                if len(temp_df) >= 3:  # 최소 3개 이상의 데이터 포인트 필요
                    # 추세 감지
                    try:
                        # 간단한 선형 추세 계산
                        x = np.arange(len(temp_df))
                        y = temp_df[num_col].values
                        coeffs = np.polyfit(x, y, 1)
                        slope = coeffs[0]
                        
                        # 추세 방향 결정
                        if abs(slope) < 0.001:
                            trend = "stable"
                        elif slope > 0:
                            trend = "increasing"
                        else:
                            trend = "decreasing"
                        
                        col_results["trends"][num_col] = {
                            "direction": trend,
                            "slope": float(slope)
                        }
                    except:
                        pass
            
            results[time_col] = col_results
        
        return results
    
    def _detect_time_frequency(self, time_series: pd.Series) -> str:
        """
        시계열 데이터의 빈도 감지
        
        Args:
            time_series (pd.Series): 시계열 데이터
            
        Returns:
            str: 감지된 빈도 (daily, weekly, monthly, yearly, irregular)
        """
        # 결측값 제거 및 정렬
        clean_series = time_series.dropna().sort_values()
        
        if len(clean_series) <= 1:
            return "unknown"
        
        # 시간 간격 계산
        diff = clean_series.diff().dropna()
        
        if len(diff) == 0:
            return "unknown"
        
        # 가장 흔한 간격 찾기
        try:
            most_common_diff = diff.value_counts().idxmax()
            days = most_common_diff.total_seconds() / (24 * 3600)
            
            # 빈도 결정
            if days < 0.1:  # 몇 시간 이내
                return "hourly"
            elif 0.9 <= days <= 1.1:  # 약 1일
                return "daily"
            elif 6.5 <= days <= 7.5:  # 약 1주
                return "weekly"
            elif 28 <= days <= 31:  # 약 1달
                return "monthly"
            elif 365 <= days <= 366:  # 약 1년
                return "yearly"
            else:
                return "irregular"
        except:
            return "irregular"
    
    def _calculate_correlations(self, df: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """
        수치형 컬럼 간 상관관계 계산
        
        Args:
            df (pd.DataFrame): 데이터프레임
            numeric_columns (List[str]): 수치형 컬럼 목록
            
        Returns:
            Dict[str, Any]: 상관관계 분석 결과
        """
        if len(numeric_columns) < 2:
            return {}
        
        try:
            # 상관관계 행렬 계산
            corr_matrix = df[numeric_columns].corr().fillna(0).round(3)
            
            # 상위 상관관계 추출
            strong_correlations = []
            
            for i in range(len(numeric_columns)):
                for j in range(i+1, len(numeric_columns)):
                    col1 = numeric_columns[i]
                    col2 = numeric_columns[j]
                    corr_value = corr_matrix.loc[col1, col2]
                    
                    if abs(corr_value) >= 0.5:  # 중간 이상의 상관관계만 포함
                        strong_correlations.append({
                            "column1": col1,
                            "column2": col2,
                            "correlation": float(corr_value),
                            "strength": self._interpret_correlation(corr_value)
                        })
            
            # 상관관계 강도에 따라 정렬
            strong_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            
            return {
                "matrix": corr_matrix.to_dict(),
                "strong_correlations": strong_correlations[:5]  # 상위 5개만 반환
            }
        except Exception as e:
            logger.error(f"상관관계 계산 중 오류 발생: {str(e)}")
            return {}
    
    def _interpret_correlation(self, corr_value: float) -> str:
        """
        상관계수 해석
        
        Args:
            corr_value (float): 상관계수
            
        Returns:
            str: 상관관계 강도 설명
        """
        abs_corr = abs(corr_value)
        
        if abs_corr >= 0.9:
            strength = "very strong"
        elif abs_corr >= 0.7:
            strength = "strong"
        elif abs_corr >= 0.5:
            strength = "moderate"
        elif abs_corr >= 0.3:
            strength = "weak"
        else:
            strength = "very weak"
        
        direction = "positive" if corr_value >= 0 else "negative"
        
        return f"{strength} {direction}"
    
    def _generate_basic_insights(self, query_result: Dict[str, Any], stats: Dict[str, Any]) -> List[str]:
        """
        기본 인사이트 생성
        
        Args:
            query_result (Dict[str, Any]): 쿼리 실행 결과
            stats (Dict[str, Any]): 통계 분석 결과
            
        Returns:
            List[str]: 기본 인사이트 목록
        """
        insights = []
        
        # 행 수 관련 인사이트
        row_count = stats.get("row_count", 0)
        if row_count == 0:
            insights.append("쿼리 결과에 데이터가 없습니다.")
        else:
            insights.append(f"총 {row_count}개의 행이 반환되었습니다.")
        
        # 컬럼 통계 관련 인사이트
        column_stats = stats.get("column_stats", {})
        for column, col_stats in column_stats.items():
            # 결측값 관련 인사이트
            null_percentage = col_stats.get("null_percentage", 0)
            if null_percentage > 20:
                insights.append(f"'{column}' 컬럼은 {null_percentage}%의 결측값을 포함하고 있습니다.")
            
            # 수치형 컬럼 인사이트
            if "mean" in col_stats:
                outlier_percentage = col_stats.get("outlier_percentage", 0)
                if outlier_percentage > 5:
                    insights.append(f"'{column}' 컬럼은 {outlier_percentage}%의 이상치를 포함하고 있습니다.")
            
            # 범주형 컬럼 인사이트
            if "unique_count" in col_stats:
                unique_count = col_stats.get("unique_count", 0)
                unique_percentage = col_stats.get("unique_percentage", 0)
                if unique_count == 1:
                    insights.append(f"'{column}' 컬럼은 단일 값만 포함하고 있습니다.")
                elif unique_percentage < 1:
                    insights.append(f"'{column}' 컬럼은 매우 낮은 카디널리티({unique_count}개 고유값)를 가집니다.")
                elif unique_percentage > 95:
                    insights.append(f"'{column}' 컬럼은 거의 모든 행이 고유한 값을 가집니다.")
        
        # 시계열 관련 인사이트
        time_series = stats.get("time_series", {})
        for time_col, ts_stats in time_series.items():
            frequency = ts_stats.get("frequency", "")
            if frequency != "irregular" and frequency != "unknown":
                insights.append(f"'{time_col}' 컬럼은 {frequency} 빈도의 시계열 데이터입니다.")
            
            # 추세 관련 인사이트
            for num_col, trend_info in ts_stats.get("trends", {}).items():
                direction = trend_info.get("direction", "")
                if direction == "increasing":
                    insights.append(f"'{num_col}'은(는) '{time_col}'에 따라 증가하는 추세를 보입니다.")
                elif direction == "decreasing":
                    insights.append(f"'{num_col}'은(는) '{time_col}'에 따라 감소하는 추세를 보입니다.")
        
        # 상관관계 관련 인사이트
        correlations = stats.get("correlations", {})
        strong_correlations = correlations.get("strong_correlations", [])
        for corr in strong_correlations:
            col1 = corr.get("column1", "")
            col2 = corr.get("column2", "")
            strength = corr.get("strength", "")
            if col1 and col2 and strength:
                insights.append(f"'{col1}'과(와) '{col2}' 사이에 {strength} 상관관계가 있습니다.")
        
        return insights