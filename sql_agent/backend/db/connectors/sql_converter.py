"""
SQL query conversion utility for SQL DB LLM Agent System.
This module provides functionality to automatically convert SQL queries between different database dialects.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Union, Callable

from sql_agent.backend.models.database import Database, DBType
from sql_agent.backend.db.connectors.dialect_handler import SQLDialectHandler

logger = logging.getLogger(__name__)

class SQLConverter:
    """
    Converts SQL queries between different database dialects.
    
    This class provides functionality to:
    - Automatically detect source dialect
    - Convert queries between MS-SQL and SAP HANA
    - Validate compatibility
    - Suggest optimizations
    """
    
    @classmethod
    def auto_convert(cls, query: str, target_db_config: Database) -> Tuple[str, List[str]]:
        """
        Automatically detect the source dialect and convert to the target dialect.
        
        Args:
            query: SQL query string
            target_db_config: Target database configuration
            
        Returns:
            Tuple of (converted_query: str, warnings: List[str])
        """
        warnings = []
        
        # Determine target dialect
        if target_db_config.type == DBType.MSSQL:
            target_dialect = SQLDialectHandler.DB_TYPE_MSSQL
        elif target_db_config.type == DBType.HANA:
            target_dialect = SQLDialectHandler.DB_TYPE_HANA
        else:
            warnings.append(f"Unsupported database type: {target_db_config.type}. Query will not be converted.")
            return query, warnings
        
        # Detect dialect features in the query
        features = SQLDialectHandler.detect_dialect_features(query)
        
        # Determine the most likely source dialect
        mssql_feature_count = len(features[SQLDialectHandler.DB_TYPE_MSSQL])
        hana_feature_count = len(features[SQLDialectHandler.DB_TYPE_HANA])
        
        # If no dialect-specific features are detected, return the original query
        if mssql_feature_count == 0 and hana_feature_count == 0:
            return query, warnings
        
        # Determine source dialect based on feature count
        if mssql_feature_count > hana_feature_count:
            source_dialect = SQLDialectHandler.DB_TYPE_MSSQL
        else:
            source_dialect = SQLDialectHandler.DB_TYPE_HANA
        
        # If source and target dialects are the same, return the original query
        if source_dialect == target_dialect:
            return query, warnings
        
        # Check compatibility
        is_compatible, reason = SQLDialectHandler.is_compatible(query, target_dialect)
        if not is_compatible:
            warnings.append(f"Query may not be fully compatible with {target_dialect}: {reason}")
        
        # Convert the query
        try:
            converted_query = SQLDialectHandler.convert_sql(query, source_dialect, target_dialect)
            
            # If the query was changed, add a warning
            if converted_query != query:
                warnings.append(f"Query was automatically converted from {source_dialect} to {target_dialect}.")
                
                # Get optimization suggestions
                suggestions = SQLDialectHandler.suggest_optimizations(converted_query, target_dialect)
                if suggestions:
                    warnings.extend(suggestions)
            
            return converted_query, warnings
            
        except Exception as e:
            logger.error(f"Error converting query: {str(e)}")
            warnings.append(f"Failed to convert query: {str(e)}. Using original query.")
            return query, warnings
    
    @classmethod
    def convert_with_dialect(cls, query: str, source_dialect: str, target_dialect: str) -> Tuple[str, List[str]]:
        """
        Convert a SQL query from a specified source dialect to a target dialect.
        
        Args:
            query: SQL query string
            source_dialect: Source dialect (e.g., 'mssql', 'hana')
            target_dialect: Target dialect (e.g., 'mssql', 'hana')
            
        Returns:
            Tuple of (converted_query: str, warnings: List[str])
        """
        warnings = []
        
        # Check if source and target dialects are the same
        if source_dialect == target_dialect:
            return query, warnings
        
        # Check compatibility
        is_compatible, reason = SQLDialectHandler.is_compatible(query, target_dialect)
        if not is_compatible:
            warnings.append(f"Query may not be fully compatible with {target_dialect}: {reason}")
        
        # Convert the query
        try:
            converted_query = SQLDialectHandler.convert_sql(query, source_dialect, target_dialect)
            
            # If the query was changed, add a warning
            if converted_query != query:
                warnings.append(f"Query was converted from {source_dialect} to {target_dialect}.")
                
                # Get optimization suggestions
                suggestions = SQLDialectHandler.suggest_optimizations(converted_query, target_dialect)
                if suggestions:
                    warnings.extend(suggestions)
            
            return converted_query, warnings
            
        except Exception as e:
            logger.error(f"Error converting query: {str(e)}")
            warnings.append(f"Failed to convert query: {str(e)}. Using original query.")
            return query, warnings