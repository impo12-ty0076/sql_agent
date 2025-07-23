"""
Base database connector interface for SQL DB LLM Agent System.
This module defines the abstract base class for all database connectors.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple
from contextlib import contextmanager
import logging
from datetime import datetime

from ...models.database import Database, DatabaseSchema, Schema, Table, Column
from ...models.query import QueryResult, ResultColumn
from .sql_converter import SQLConverter

logger = logging.getLogger(__name__)

class ConnectionPoolManager(ABC):
    """
    Abstract base class for managing database connection pools.
    """
    
    @abstractmethod
    def get_connection(self, db_config: Database) -> Any:
        """
        Get a connection from the pool or create a new one if needed.
        
        Args:
            db_config: Database configuration
            
        Returns:
            Database connection object
        """
        pass
    
    @abstractmethod
    def release_connection(self, connection: Any, db_id: str) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            connection: Database connection object
            db_id: Database identifier
        """
        pass
    
    @abstractmethod
    def close_all_connections(self, db_id: Optional[str] = None) -> None:
        """
        Close all connections in the pool for a specific database or all databases.
        
        Args:
            db_id: Optional database identifier. If None, close all connections.
        """
        pass
    
    @abstractmethod
    def get_pool_stats(self, db_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about the connection pool.
        
        Args:
            db_id: Optional database identifier. If None, get stats for all pools.
            
        Returns:
            Dictionary with pool statistics
        """
        pass

class DBConnector(ABC):
    """
    Abstract base class for database connectors.
    Defines the interface that all database connectors must implement.
    """
    
    def __init__(self, connection_pool_manager: ConnectionPoolManager):
        """
        Initialize the database connector with a connection pool manager.
        
        Args:
            connection_pool_manager: Connection pool manager instance
        """
        self.connection_pool_manager = connection_pool_manager
    
    @abstractmethod
    def test_connection(self, db_config: Database) -> Tuple[bool, Optional[str]]:
        """
        Test the connection to the database.
        
        Args:
            db_config: Database configuration
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        pass
    
    @contextmanager
    def get_connection(self, db_config: Database):
        """
        Context manager for getting a database connection.
        
        Args:
            db_config: Database configuration
            
        Yields:
            Database connection object
        """
        connection = None
        try:
            connection = self.connection_pool_manager.get_connection(db_config)
            yield connection
        except Exception as e:
            logger.error(f"Error getting connection for database {db_config.id}: {str(e)}")
            raise
        finally:
            if connection:
                self.connection_pool_manager.release_connection(connection, db_config.id)
    
    def execute_query(self, db_config: Database, query: str, params: Optional[Dict[str, Any]] = None, 
                     timeout: Optional[int] = None, max_rows: Optional[int] = None, 
                     auto_convert: bool = True) -> QueryResult:
        """
        Execute a SQL query and return the results.
        
        Args:
            db_config: Database configuration
            query: SQL query string
            params: Optional query parameters
            timeout: Optional query timeout in seconds
            max_rows: Optional maximum number of rows to return
            auto_convert: Whether to automatically convert the query to the target dialect
            
        Returns:
            QueryResult object containing the query results
        """
        # Automatically convert the query if enabled
        if auto_convert:
            converted_query, warnings = SQLConverter.auto_convert(query, db_config)
            if converted_query != query:
                logger.info(f"Query automatically converted for {db_config.type}. Warnings: {warnings}")
                query = converted_query
        
        # Execute the query using the concrete implementation
        return self._execute_query_impl(db_config, query, params, timeout, max_rows)
    
    @abstractmethod
    def _execute_query_impl(self, db_config: Database, query: str, params: Optional[Dict[str, Any]] = None, 
                          timeout: Optional[int] = None, max_rows: Optional[int] = None) -> QueryResult:
        """
        Implementation of query execution for specific database types.
        
        Args:
            db_config: Database configuration
            query: SQL query string
            params: Optional query parameters
            timeout: Optional query timeout in seconds
            max_rows: Optional maximum number of rows to return
            
        Returns:
            QueryResult object containing the query results
        """
        pass
    
    @abstractmethod
    def cancel_query(self, query_id: str) -> bool:
        """
        Cancel a running query.
        
        Args:
            query_id: Query identifier
            
        Returns:
            True if the query was successfully cancelled, False otherwise
        """
        pass
    
    @abstractmethod
    def get_schema(self, db_config: Database) -> DatabaseSchema:
        """
        Get the database schema.
        
        Args:
            db_config: Database configuration
            
        Returns:
            DatabaseSchema object containing the database schema
        """
        pass
    
    @abstractmethod
    def validate_query(self, db_config: Database, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a SQL query without executing it.
        
        Args:
            db_config: Database configuration
            query: SQL query string
            
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        pass
    
    @abstractmethod
    def is_read_only_query(self, query: str) -> bool:
        """
        Check if a query is read-only (SELECT, SHOW, DESCRIBE, etc.).
        
        Args:
            query: SQL query string
            
        Returns:
            True if the query is read-only, False otherwise
        """
        pass
    
    def format_error(self, error: Exception) -> str:
        """
        Format an exception into a user-friendly error message.
        
        Args:
            error: Exception object
            
        Returns:
            Formatted error message
        """
        return f"{type(error).__name__}: {str(error)}"