"""
Result Summary Service

This module provides functionality for generating natural language summaries of query results
using LLM services.
"""

import logging
from typing import List, Dict, Any, Optional
import json

from .base import LLMService

logger = logging.getLogger(__name__)

class ResultSummaryService:
    """
    Service for generating natural language summaries of query results using LLM.
    """
    
    def __init__(self, llm_service: LLMService):
        """
        Initialize the result summary service.
        
        Args:
            llm_service: LLM service for generating summaries
        """
        self.llm_service = llm_service
    
    async def generate_summary(
        self,
        columns: List[Dict[str, Any]],
        rows: List[List[Any]],
        summary_type: str = "basic",
        include_insights: bool = True,
        max_rows_for_summary: int = 1000
    ) -> str:
        """
        Generate a natural language summary of query results.
        
        Args:
            columns: List of column definitions (name, type)
            rows: List of data rows
            summary_type: Type of summary to generate ('basic' or 'detailed')
            include_insights: Whether to include insights in the summary
            max_rows_for_summary: Maximum number of rows to include in the summary
            
        Returns:
            Natural language summary of the query results
        """
        try:
            # Limit the number of rows to avoid overwhelming the LLM
            limited_rows = rows[:max_rows_for_summary]
            
            # Prepare column information
            column_info = []
            for col in columns:
                column_info.append({
                    "name": col["name"],
                    "type": col["type"]
                })
            
            # Calculate basic statistics
            stats = self._calculate_basic_statistics(columns, limited_rows)
            
            # Prepare prompt based on summary type
            if summary_type == "detailed":
                prompt = self._create_detailed_summary_prompt(column_info, limited_rows, stats, include_insights)
            else:
                prompt = self._create_basic_summary_prompt(column_info, limited_rows, stats, include_insights)
            
            # Generate summary using LLM
            response = await self.llm_service.generate_text(prompt)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating result summary: {str(e)}")
            return f"Failed to generate summary: {str(e)}"
    
    def _calculate_basic_statistics(
        self,
        columns: List[Dict[str, Any]],
        rows: List[List[Any]]
    ) -> Dict[str, Any]:
        """
        Calculate basic statistics for the query results.
        
        Args:
            columns: List of column definitions
            rows: List of data rows
            
        Returns:
            Dictionary of basic statistics
        """
        stats = {
            "row_count": len(rows),
            "column_count": len(columns),
            "columns": {}
        }
        
        # Skip if no rows
        if not rows:
            return stats
        
        # Calculate statistics for each column
        for i, col in enumerate(columns):
            col_name = col["name"]
            col_type = col["type"].lower()
            
            # Initialize column statistics
            col_stats = {
                "type": col_type,
                "null_count": 0,
                "distinct_count": 0
            }
            
            # Extract column values
            values = [row[i] for row in rows]
            
            # Count nulls
            null_count = sum(1 for v in values if v is None)
            col_stats["null_count"] = null_count
            col_stats["null_percent"] = (null_count / len(rows)) * 100 if rows else 0
            
            # Count distinct values
            try:
                distinct_values = set(str(v) if v is not None else None for v in values)
                col_stats["distinct_count"] = len(distinct_values)
                col_stats["distinct_percent"] = (len(distinct_values) / len(rows)) * 100 if rows else 0
            except:
                # If we can't calculate distinct values, skip it
                pass
            
            # Add numeric statistics if applicable
            if col_type in ["int", "integer", "float", "double", "decimal", "numeric"]:
                numeric_values = [float(v) for v in values if v is not None and str(v).strip() and self._is_numeric(v)]
                if numeric_values:
                    col_stats["min"] = min(numeric_values)
                    col_stats["max"] = max(numeric_values)
                    col_stats["avg"] = sum(numeric_values) / len(numeric_values)
            
            # Add string statistics if applicable
            if col_type in ["varchar", "char", "text", "string"]:
                string_values = [str(v) for v in values if v is not None]
                if string_values:
                    col_stats["min_length"] = min(len(v) for v in string_values)
                    col_stats["max_length"] = max(len(v) for v in string_values)
                    col_stats["avg_length"] = sum(len(v) for v in string_values) / len(string_values)
            
            # Add date statistics if applicable
            if col_type in ["date", "datetime", "timestamp"]:
                # In a real implementation, we would parse dates and calculate min/max/etc.
                # For now, we'll skip this
                pass
            
            # Add to column statistics
            stats["columns"][col_name] = col_stats
        
        return stats
    
    def _is_numeric(self, value: Any) -> bool:
        """
        Check if a value is numeric.
        
        Args:
            value: Value to check
            
        Returns:
            True if the value is numeric, False otherwise
        """
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _create_basic_summary_prompt(
        self,
        columns: List[Dict[str, Any]],
        rows: List[List[Any]],
        stats: Dict[str, Any],
        include_insights: bool
    ) -> str:
        """
        Create a prompt for generating a basic summary of query results.
        
        Args:
            columns: List of column definitions
            rows: List of data rows
            stats: Basic statistics
            include_insights: Whether to include insights
            
        Returns:
            Prompt for generating a basic summary
        """
        # Convert rows to a more readable format for the prompt
        formatted_rows = []
        for row in rows[:10]:  # Only include first 10 rows in the prompt
            formatted_row = {}
            for i, col in enumerate(columns):
                formatted_row[col["name"]] = row[i]
            formatted_rows.append(formatted_row)
        
        prompt = f"""
        You are a data analyst tasked with summarizing SQL query results. Please provide a concise summary of the following query results.
        
        Query Result Information:
        - Total rows: {stats["row_count"]}
        - Total columns: {stats["column_count"]}
        
        Column Information:
        {json.dumps(columns, indent=2)}
        
        Basic Statistics:
        {json.dumps(stats, indent=2)}
        
        Sample Data (first {len(formatted_rows)} rows):
        {json.dumps(formatted_rows, indent=2)}
        
        Please provide a concise summary of the query results in a few sentences. Focus on:
        1. The overall structure of the data (number of rows, columns, types)
        2. Key statistics for important columns
        3. Any notable patterns or distributions in the data
        """
        
        if include_insights:
            prompt += """
            4. Potential insights or findings from the data
            5. Any data quality issues (missing values, outliers)
            
            Format your response as a well-structured paragraph that a business user could understand.
            """
        
        return prompt
    
    def _create_detailed_summary_prompt(
        self,
        columns: List[Dict[str, Any]],
        rows: List[List[Any]],
        stats: Dict[str, Any],
        include_insights: bool
    ) -> str:
        """
        Create a prompt for generating a detailed summary of query results.
        
        Args:
            columns: List of column definitions
            rows: List of data rows
            stats: Basic statistics
            include_insights: Whether to include insights
            
        Returns:
            Prompt for generating a detailed summary
        """
        # Convert rows to a more readable format for the prompt
        formatted_rows = []
        for row in rows[:20]:  # Include more rows for detailed summary
            formatted_row = {}
            for i, col in enumerate(columns):
                formatted_row[col["name"]] = row[i]
            formatted_rows.append(formatted_row)
        
        prompt = f"""
        You are a data analyst tasked with providing a detailed summary of SQL query results. Please analyze the following query results and provide a comprehensive summary.
        
        Query Result Information:
        - Total rows: {stats["row_count"]}
        - Total columns: {stats["column_count"]}
        
        Column Information:
        {json.dumps(columns, indent=2)}
        
        Detailed Statistics:
        {json.dumps(stats, indent=2)}
        
        Sample Data (first {len(formatted_rows)} rows):
        {json.dumps(formatted_rows, indent=2)}
        
        Please provide a detailed summary of the query results. Include:
        1. An overview of the dataset structure and content
        2. Detailed analysis of each important column (data type, range, distribution, missing values)
        3. Relationships between columns if apparent
        """
        
        if include_insights:
            prompt += """
            4. Key insights and findings from the data
            5. Data quality assessment (completeness, consistency, accuracy)
            6. Potential business implications of the findings
            7. Recommendations for further analysis or actions
            
            Format your response as a well-structured report with clear sections and bullet points where appropriate.
            Make sure your analysis is data-driven and objective, highlighting the most important aspects of the results.
            """
        
        return prompt