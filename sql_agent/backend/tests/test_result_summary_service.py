"""
Unit tests for the Result Summary Service.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from ..llm.result_summary_service import ResultSummaryService

# Mock data
mock_columns = [
    {"name": "id", "type": "int"},
    {"name": "username", "type": "varchar"},
    {"name": "email", "type": "varchar"},
    {"name": "age", "type": "int"}
]

mock_rows = [
    [1, "user1", "user1@example.com", 25],
    [2, "user2", "user2@example.com", 30],
    [3, "user3", "user3@example.com", 35],
    [4, "user4", "user4@example.com", 40],
    [5, "user5", "user5@example.com", 45]
]

class TestResultSummaryService:
    """Test cases for the Result Summary Service."""
    
    def test_calculate_basic_statistics(self):
        """Test calculating basic statistics from query results."""
        # Create service with mock LLM
        llm_service = MagicMock()
        service = ResultSummaryService(llm_service)
        
        # Calculate statistics
        stats = service._calculate_basic_statistics(mock_columns, mock_rows)
        
        # Verify statistics
        assert stats["row_count"] == 5
        assert stats["column_count"] == 4
        
        # Check column statistics
        assert "id" in stats["columns"]
        assert "username" in stats["columns"]
        assert "email" in stats["columns"]
        assert "age" in stats["columns"]
        
        # Check numeric column statistics
        age_stats = stats["columns"]["age"]
        assert age_stats["type"] == "int"
        assert age_stats["null_count"] == 0
        assert age_stats["min"] == 25
        assert age_stats["max"] == 45
        assert age_stats["avg"] == 35.0
        
        # Check string column statistics
        username_stats = stats["columns"]["username"]
        assert username_stats["type"] == "varchar"
        assert username_stats["null_count"] == 0
        assert username_stats["min_length"] == 5  # "user1" length
        assert username_stats["max_length"] == 5  # "user5" length
    
    def test_is_numeric(self):
        """Test the _is_numeric helper function."""
        service = ResultSummaryService(MagicMock())
        
        # Test numeric values
        assert service._is_numeric(42) is True
        assert service._is_numeric(3.14) is True
        assert service._is_numeric("123") is True
        assert service._is_numeric("-456.78") is True
        
        # Test non-numeric values
        assert service._is_numeric("abc") is False
        assert service._is_numeric(None) is False
        assert service._is_numeric("") is False
        assert service._is_numeric("12a") is False
    
    def test_create_basic_summary_prompt(self):
        """Test creating a basic summary prompt."""
        service = ResultSummaryService(MagicMock())
        
        # Calculate statistics for prompt
        stats = service._calculate_basic_statistics(mock_columns, mock_rows)
        
        # Create prompt
        prompt = service._create_basic_summary_prompt(mock_columns, mock_rows, stats, True)
        
        # Verify prompt content
        assert "You are a data analyst" in prompt
        assert "Total rows: 5" in prompt
        assert "Total columns: 4" in prompt
        assert "Sample Data" in prompt
        assert "Potential insights" in prompt
    
    def test_create_detailed_summary_prompt(self):
        """Test creating a detailed summary prompt."""
        service = ResultSummaryService(MagicMock())
        
        # Calculate statistics for prompt
        stats = service._calculate_basic_statistics(mock_columns, mock_rows)
        
        # Create prompt
        prompt = service._create_detailed_summary_prompt(mock_columns, mock_rows, stats, True)
        
        # Verify prompt content
        assert "You are a data analyst" in prompt
        assert "Total rows: 5" in prompt
        assert "Total columns: 4" in prompt
        assert "Sample Data" in prompt
        assert "Key insights" in prompt
        assert "Recommendations" in prompt
    
    @pytest.mark.asyncio
    async def test_generate_summary(self):
        """Test generating a summary from query results."""
        # Create mock LLM service
        llm_service = MagicMock()
        llm_service.generate_text = AsyncMock(return_value="This is a test summary with insights.")
        
        # Create service
        service = ResultSummaryService(llm_service)
        
        # Generate summary
        summary = await service.generate_summary(
            columns=mock_columns,
            rows=mock_rows,
            summary_type="basic",
            include_insights=True
        )
        
        # Verify summary
        assert summary == "This is a test summary with insights."
        llm_service.generate_text.assert_called_once()
        
        # The prompt should include statistics and sample data
        prompt = llm_service.generate_text.call_args[0][0]
        assert "Total rows: 5" in prompt
        assert "Total columns: 4" in prompt