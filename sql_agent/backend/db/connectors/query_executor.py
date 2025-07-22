"""
Query execution and result processing utilities for database connectors.
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime

from sql_agent.backend.models.query import QueryResult, ResultColumn
from sql_agent.backend.models.database import Database

logger = logging.getLogger(__name__)

class QueryExecutionTracker:
    """
    Tracks running queries and provides methods to cancel them.
    """
    
    def __init__(self):
        """
        Initialize the query execution tracker.
        """
        self._running_queries: Dict[str, Dict[str, Any]] = {}
    
    def register_query(self, query_id: str, db_id: str, cancel_func: callable) -> None:
        """
        Register a running query.
        
        Args:
            query_id: Query identifier
            db_id: Database identifier
            cancel_func: Function to call to cancel the query
        """
        self._running_queries[query_id] = {
            "db_id": db_id,
            "start_time": datetime.now(),
            "cancel_func": cancel_func
        }
    
    def unregister_query(self, query_id: str) -> None:
        """
        Unregister a query that has completed or been cancelled.
        
        Args:
            query_id: Query identifier
        """
        if query_id in self._running_queries:
            del self._running_queries[query_id]
    
    def cancel_query(self, query_id: str) -> bool:
        """
        Cancel a running query.
        
        Args:
            query_id: Query identifier
            
        Returns:
            True if the query was successfully cancelled, False otherwise
        """
        if query_id in self._running_queries:
            try:
                cancel_func = self._running_queries[query_id]["cancel_func"]
                result = cancel_func()
                self.unregister_query(query_id)
                return result
            except Exception as e:
                logger.error(f"Error cancelling query {query_id}: {str(e)}")
                return False
        else:
            logger.warning(f"Attempted to cancel unknown query: {query_id}")
            return False
    
    def get_running_queries(self, db_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get information about running queries.
        
        Args:
            db_id: Optional database identifier to filter queries
            
        Returns:
            Dictionary of query_id -> query information
        """
        if db_id is None:
            return self._running_queries.copy()
        else:
            return {
                query_id: info
                for query_id, info in self._running_queries.items()
                if info["db_id"] == db_id
            }
    
    def get_query_count(self, db_id: Optional[str] = None) -> int:
        """
        Get the number of running queries.
        
        Args:
            db_id: Optional database identifier to filter queries
            
        Returns:
            Number of running queries
        """
        if db_id is None:
            return len(self._running_queries)
        else:
            return sum(1 for info in self._running_queries.values() if info["db_id"] == db_id)

class QueryResultProcessor:
    """
    Processes query results into a standardized format.
    """
    
    @staticmethod
    def process_result(cursor: Any, query: str, max_rows: Optional[int] = None) -> QueryResult:
        """
        Process a database cursor into a QueryResult object.
        
        Args:
            cursor: Database cursor with query results
            query: SQL query string
            max_rows: Optional maximum number of rows to return
            
        Returns:
            QueryResult object containing the query results
        """
        start_time = time.time()
        
        # Extract column information
        columns = []
        if cursor.description:
            for col in cursor.description:
                # Column description format varies by database driver
                # Typically: (name, type_code, display_size, internal_size, precision, scale, null_ok)
                col_name = col[0]
                col_type = str(col[1]) if len(col) > 1 else "unknown"
                columns.append(ResultColumn(name=col_name, type=col_type))
        
        # Extract row data with optional limit
        truncated = False
        total_row_count = None
        
        if max_rows is not None:
            # Fetch limited number of rows
            rows = []
            for i, row in enumerate(cursor):
                if i < max_rows:
                    rows.append(list(row))
                else:
                    truncated = True
                    # Try to get total count if possible
                    try:
                        # This might not work for all database drivers
                        cursor.fetchall()  # Consume remaining rows
                        total_row_count = i + cursor.rowcount
                    except:
                        pass
                    break
        else:
            # Fetch all rows
            rows = [list(row) for row in cursor]
        
        row_count = len(rows)
        
        # Create query result
        result = QueryResult(
            id=str(uuid.uuid4()),
            query_id="",  # Will be set by the caller
            columns=columns,
            rows=rows,
            row_count=row_count,
            truncated=truncated,
            total_row_count=total_row_count,
            created_at=datetime.now()
        )
        
        logger.debug(f"Processed query result with {row_count} rows in {time.time() - start_time:.2f}s")
        return result