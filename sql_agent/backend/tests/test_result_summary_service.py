"""
Unit tests for the Result Summary Service.
"""

import unittest
import sys
import os
import pytest
import json
from datetime import datetime, timedelta
import pandas as pd
from unittest.mock import AsyncMock, patch, MagicMock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.services.result_summary_service import ResultSummaryService
from backend.llm.base import LLMService, LLMConfig, LLMProvider

class TestResultSummaryService(unittest.TestCase):
    """
    Tests for the Result Summary Service.
    """
    
    def setUp(self):
        """
        Set up test environment before each test.
        """
        # Create a mock LLM service
        self.mock_llm_service = MagicMock(spec=LLMService)
        self.mock_llm_service.summarize_results = AsyncMock(return_value={
            "summary": "This is a mock summary of the query results.",
            "insights": ["Insight 1", "Insight 2", "Insight 3"]
        })
        
        # Create a result summary service instance
        self.summary_service = ResultSummaryService(llm_service=self.mock_llm_service)
        
        # Sample query result for testing
        self.sample_query_result = {
            "columns": [
                {"name": "employee_id", "type": "INT"},
                {"name": "first_name", "type": "VARCHAR"},
                {"name": "salary", "type": "DECIMAL"},
                {"name": "hire_date", "type": "DATE"},
                {"name": "department_id", "type": "INT"}
            ],
            "rows": [
                [1, "John", 5000.0, "2020-01-15", 10],
                [2, "Jane", 6000.0, "2019-05-20", 20],
                [3, "Bob", 4500.0, "2021-03-10", 10],
                [4, "Alice", 7000.0, "2018-11-05", 30],
                [5, "Charlie", 5500.0, "2020-07-22", 20]
            ],
            "rowCount": 5,
            "truncated": False
        }
    
    def test_convert_to_dataframe(self):
        """
        Test conversion of query result to pandas DataFrame.
        """
        df = self.summary_service._convert_to_dataframe(
            self.sample_query_result["columns"],
            self.sample_query_result["rows"]
        )
        
        # Check DataFrame shape
        self.assertEqual(df.shape, (5, 5))
        
        # Check column names
        self.assertEqual(list(df.columns), ["employee_id", "first_name", "salary", "hire_date", "department_id"])
        
        # Check data types
        self.assertTrue(pd.api.types.is_numeric_dtype(df["employee_id"]))
        self.assertTrue(pd.api.types.is_object_dtype(df["first_name"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(df["salary"]))
        self.assertTrue(pd.api.types.is_datetime64_dtype(df["hire_date"]) or pd.api.types.is_object_dtype(df["hire_date"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(df["department_id"]))
    
    def test_calculate_column_stats(self):
        """
        Test calculation of column statistics.
        """
        df = self.summary_service._convert_to_dataframe(
            self.sample_query_result["columns"],
            self.sample_query_result["rows"]
        )
        
        stats = self.summary_service._calculate_column_stats(df)
        
        # Check if stats were calculated for all columns
        self.assertEqual(len(stats), 5)
        
        # Check numeric column stats
        self.assertIn("mean", stats["salary"])
        self.assertIn("median", stats["salary"])
        self.assertIn("min", stats["salary"])
        self.assertIn("max", stats["salary"])
        
        # Check categorical column stats
        self.assertIn("unique_count", stats["first_name"])
        self.assertEqual(stats["first_name"]["unique_count"], 5)
        
        # Check date column stats
        if "min" in stats["hire_date"]:
            self.assertIn("max", stats["hire_date"])
            self.assertIn("range_days", stats["hire_date"])
    
    def test_detect_time_series(self):
        """
        Test detection of time series columns.
        """
        # Create a DataFrame with a clear time series
        dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(30)]
        values = list(range(30))
        df = pd.DataFrame({"date": dates, "value": values})
        
        time_series_columns = self.summary_service._detect_time_series(df)
        
        # Check if the date column was detected as a time series
        self.assertIn("date", time_series_columns)
    
    def test_analyze_time_series(self):
        """
        Test time series analysis.
        """
        # Create a DataFrame with a clear time series
        dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(30)]
        values = list(range(30))  # Increasing trend
        df = pd.DataFrame({"date": dates, "value": values})
        df["date"] = pd.to_datetime(df["date"])
        
        time_columns = ["date"]
        results = self.summary_service._analyze_time_series(df, time_columns)
        
        # Check if analysis was performed
        self.assertIn("date", results)
        self.assertIn("frequency", results["date"])
        self.assertIn("trends", results["date"])
        
        # Check if trend was detected correctly
        self.assertIn("value", results["date"]["trends"])
        self.assertEqual(results["date"]["trends"]["value"]["direction"], "increasing")
    
    def test_calculate_correlations(self):
        """
        Test correlation calculation.
        """
        # Create a DataFrame with correlated columns
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 6, 8, 10],  # Perfect positive correlation with x
            "z": [5, 4, 3, 2, 1]    # Perfect negative correlation with x
        })
        
        numeric_columns = ["x", "y", "z"]
        correlations = self.summary_service._calculate_correlations(df, numeric_columns)
        
        # Check if correlations were calculated
        self.assertIn("matrix", correlations)
        self.assertIn("strong_correlations", correlations)
        
        # Check if strong correlations were detected
        self.assertEqual(len(correlations["strong_correlations"]), 3)
        
        # Check correlation strengths
        for corr in correlations["strong_correlations"]:
            if corr["column1"] == "x" and corr["column2"] == "y":
                self.assertAlmostEqual(corr["correlation"], 1.0, places=1)
                self.assertIn("strong positive", corr["strength"])
            elif corr["column1"] == "x" and corr["column2"] == "z":
                self.assertAlmostEqual(corr["correlation"], -1.0, places=1)
                self.assertIn("strong negative", corr["strength"])
    
    def test_generate_basic_insights(self):
        """
        Test generation of basic insights.
        """
        stats = {
            "row_count": 5,
            "column_stats": {
                "salary": {
                    "mean": 5600.0,
                    "outlier_percentage": 10.0
                },
                "department_id": {
                    "unique_count": 3,
                    "unique_percentage": 60.0
                }
            }
        }
        
        insights = self.summary_service._generate_basic_insights(self.sample_query_result, stats)
        
        # Check if insights were generated
        self.assertTrue(len(insights) > 0)
        
        # Check if row count insight is present
        self.assertTrue(any("5개의 행" in insight for insight in insights))
        
        # Check if outlier insight is present
        self.assertTrue(any("salary" in insight and "이상치" in insight for insight in insights))
    
    @pytest.mark.asyncio
    async def test_generate_summary_with_llm(self):
        """
        Test summary generation with LLM service.
        """
        summary_result = await self.summary_service.generate_summary(
            self.sample_query_result,
            "직원들의 급여 정보를 보여줘",
            "SELECT employee_id, first_name, salary, hire_date, department_id FROM employees"
        )
        
        # Check if LLM service was called
        self.mock_llm_service.summarize_results.assert_called_once()
        
        # Check if summary contains LLM-generated content
        self.assertIn("summary", summary_result)
        self.assertEqual(summary_result["summary"], "This is a mock summary of the query results.")
        
        # Check if insights were included
        self.assertIn("insights", summary_result)
        self.assertEqual(summary_result["insights"], ["Insight 1", "Insight 2", "Insight 3"])
        
        # Check if statistics were included
        self.assertIn("statistics", summary_result)
    
    @pytest.mark.asyncio
    async def test_generate_summary_without_llm(self):
        """
        Test summary generation without LLM service.
        """
        # Create service without LLM
        summary_service_no_llm = ResultSummaryService()
        
        summary_result = await summary_service_no_llm.generate_summary(
            self.sample_query_result,
            "직원들의 급여 정보를 보여줘",
            "SELECT employee_id, first_name, salary, hire_date, department_id FROM employees"
        )
        
        # Check if basic summary was generated
        self.assertIn("summary", summary_result)
        self.assertIn("기본 통계 분석", summary_result["summary"])
        
        # Check if insights were generated
        self.assertIn("insights", summary_result)
        self.assertTrue(len(summary_result["insights"]) > 0)
        
        # Check if statistics were included
        self.assertIn("statistics", summary_result)
    
    @pytest.mark.asyncio
    async def test_generate_summary_with_empty_result(self):
        """
        Test summary generation with empty query result.
        """
        empty_result = {
            "columns": self.sample_query_result["columns"],
            "rows": [],
            "rowCount": 0,
            "truncated": False
        }
        
        summary_result = await self.summary_service.generate_summary(
            empty_result,
            "직원들의 급여 정보를 보여줘",
            "SELECT employee_id, first_name, salary, hire_date, department_id FROM employees"
        )
        
        # Check if statistics reflect empty result
        self.assertIn("statistics", summary_result)
        self.assertEqual(summary_result["statistics"].get("row_count", None), 0)
    
    @pytest.mark.asyncio
    async def test_generate_summary_with_error_handling(self):
        """
        Test error handling in summary generation.
        """
        # Set up LLM service to raise an exception
        self.mock_llm_service.summarize_results.side_effect = Exception("API Error")
        
        summary_result = await self.summary_service.generate_summary(
            self.sample_query_result,
            "직원들의 급여 정보를 보여줘",
            "SELECT employee_id, first_name, salary, hire_date, department_id FROM employees"
        )
        
        # Check if error was handled
        self.assertIn("error", summary_result)
        self.assertEqual(summary_result["summary"], "결과 요약을 생성하는 중 오류가 발생했습니다.")

if __name__ == "__main__":
    unittest.main()