"""
SQL query execution service for handling query execution, monitoring, and cancellation.
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from ..models.query import QueryStatus, QueryUpdate, QueryResult, QueryResultCreate
from ..models.database import Database
from ..db.crud.query import update_query, get_query_by_id
from ..db.crud.query_result import create_query_result, get_query_result_by_id
from ..db.connectors.factory import connector_factory
from ..utils.logging import log_event, log_error
from ..services.query_history_service import QueryHistoryService

logger = logging.getLogger(__name__)

class QueryExecutionService:
    """
    Service for executing SQL queries, monitoring their status, and handling cancellation.
    """
    
    def __init__(self):
        """
        Initialize the query execution service.
        """
        self._running_tasks = {}  # Dictionary to track running asyncio tasks
        self._history_service = QueryHistoryService()
    
    async def execute_query(
        self, 
        user_id: str, 
        db_id: str, 
        sql: str, 
        query_id: Optional[str] = None,
        timeout: Optional[int] = 300,  # Default timeout of 5 minutes
        max_rows: Optional[int] = 10000,  # Default max rows
        auto_save_to_history: bool = True  # Automatically save to history
    ) -> Dict[str, Any]:
        """
        Execute a SQL query asynchronously.
        
        Args:
            user_id: User ID
            db_id: Database ID
            sql: SQL query to execute
            query_id: Optional query ID (if updating an existing query)
            timeout: Optional query timeout in seconds
            max_rows: Optional maximum number of rows to return
            auto_save_to_history: Whether to automatically save the query to history
            
        Returns:
            Dictionary with query execution information
        """
        try:
            # Generate query ID if not provided
            if not query_id:
                query_id = str(uuid.uuid4())
            
            # Log the query execution request
            log_event("execute_query_request", {
                "user_id": user_id,
                "db_id": db_id,
                "query_id": query_id,
                "sql": sql,
                "timeout": timeout,
                "max_rows": max_rows
            })
            
            # Update query status to EXECUTING if it exists
            query = await get_query_by_id(query_id)
            if query:
                await update_query(query_id, QueryUpdate(
                    status=QueryStatus.EXECUTING,
                    executed_sql=sql,
                    start_time=datetime.utcnow()
                ))
            
            # Start the query execution as a background task
            task = asyncio.create_task(
                self._execute_query_task(
                    user_id=user_id,
                    db_id=db_id,
                    sql=sql,
                    query_id=query_id,
                    timeout=timeout,
                    max_rows=max_rows,
                    auto_save_to_history=auto_save_to_history
                )
            )
            
            # Store the task for potential cancellation
            self._running_tasks[query_id] = task
            
            # Return immediately with the query ID
            return {
                "query_id": query_id,
                "status": QueryStatus.EXECUTING.value,
                "start_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            log_error("execute_query_error", str(e), {
                "user_id": user_id,
                "db_id": db_id,
                "query_id": query_id,
                "sql": sql
            })
            
            # Update query status to FAILED if it exists
            if query_id:
                try:
                    await update_query(query_id, QueryUpdate(
                        status=QueryStatus.FAILED,
                        error=str(e),
                        end_time=datetime.utcnow()
                    ))
                except Exception as update_error:
                    logger.error(f"Failed to update query status: {str(update_error)}")
            
            raise
    
    async def _execute_query_task(
        self, 
        user_id: str, 
        db_id: str, 
        sql: str, 
        query_id: str,
        timeout: Optional[int],
        max_rows: Optional[int],
        auto_save_to_history: bool
    ) -> None:
        """
        Background task for executing a SQL query.
        
        Args:
            user_id: User ID
            db_id: Database ID
            sql: SQL query to execute
            query_id: Query ID
            timeout: Query timeout in seconds
            max_rows: Maximum number of rows to return
            auto_save_to_history: Whether to automatically save the query to history
        """
        result_id = None
        try:
            # Get database configuration
            # In a real implementation, this would fetch the actual database config
            # For now, we'll create a dummy config
            db_config = Database(
                id=db_id,
                name=f"Database {db_id}",
                type="mssql" if db_id == "db1" else "hana",
                host="localhost",
                port=1433 if db_id == "db1" else 30015,
                default_schema="dbo" if db_id == "db1" else "SYSTEM"
            )
            
            # Get the appropriate connector for this database type
            connector = connector_factory.create_connector(db_config)
            
            # Check if the query is read-only
            if not connector.is_read_only_query(sql):
                raise ValueError("Only read-only queries are allowed")
            
            # Execute the query with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    connector.execute_query,
                    db_config=db_config,
                    query=sql,
                    timeout=timeout,
                    max_rows=max_rows
                ),
                timeout=timeout if timeout else None
            )
            
            # Create query result record
            result_create = QueryResultCreate(
                query_id=query_id,
                columns=result.columns,
                rows=result.rows,
                row_count=result.row_count,
                truncated=result.truncated,
                total_row_count=result.total_row_count
            )
            
            created_result = await create_query_result(result_create)
            result_id = created_result.id
            
            # Update query status to COMPLETED
            await update_query(query_id, QueryUpdate(
                status=QueryStatus.COMPLETED,
                end_time=datetime.utcnow(),
                result_id=result_id
            ))
            
            log_event("execute_query_completed", {
                "user_id": user_id,
                "db_id": db_id,
                "query_id": query_id,
                "result_id": result_id,
                "row_count": result.row_count,
                "truncated": result.truncated
            })
            
            # Automatically save to history if enabled
            if auto_save_to_history:
                try:
                    await self._history_service.save_query_to_history(
                        user_id=user_id,
                        query_id=query_id
                    )
                    log_event("query_auto_saved_to_history", {
                        "user_id": user_id,
                        "query_id": query_id
                    })
                except Exception as e:
                    log_error("auto_save_to_history_error", str(e), {
                        "user_id": user_id,
                        "query_id": query_id
                    })
            
        except asyncio.CancelledError:
            # Query was cancelled
            await update_query(query_id, QueryUpdate(
                status=QueryStatus.CANCELLED,
                end_time=datetime.utcnow()
            ))
            
            log_event("execute_query_cancelled", {
                "user_id": user_id,
                "db_id": db_id,
                "query_id": query_id
            })
            
        except Exception as e:
            # Query execution failed
            error_message = str(e)
            
            await update_query(query_id, QueryUpdate(
                status=QueryStatus.FAILED,
                error=error_message,
                end_time=datetime.utcnow()
            ))
            
            log_error("execute_query_failed", error_message, {
                "user_id": user_id,
                "db_id": db_id,
                "query_id": query_id,
                "sql": sql
            })
            
        finally:
            # Remove the task from running tasks
            if query_id in self._running_tasks:
                del self._running_tasks[query_id]
    
    async def get_query_status(self, query_id: str) -> Dict[str, Any]:
        """
        Get the status of a query.
        
        Args:
            query_id: Query ID
            
        Returns:
            Dictionary with query status information
            
        Raises:
            ValueError: If the query is not found
        """
        # Get query from database
        query = await get_query_by_id(query_id)
        if not query:
            raise ValueError(f"Query with ID {query_id} not found")
        
        # Check if the query has a result
        result = None
        if query.result_id:
            result = await get_query_result_by_id(query.result_id)
        
        # Build response
        response = {
            "query_id": query.id,
            "status": query.status,
            "start_time": query.start_time.isoformat() if query.start_time else None,
            "end_time": query.end_time.isoformat() if query.end_time else None,
            "error": query.error,
            "result_id": query.result_id,
            "is_running": query.id in self._running_tasks,
            "natural_language": query.natural_language,
            "generated_sql": query.generated_sql,
            "executed_sql": query.executed_sql,
        }
        
        # Add result information if available
        if result:
            response["result"] = {
                "row_count": result.row_count,
                "truncated": result.truncated,
                "total_row_count": result.total_row_count,
                "column_count": len(result.columns),
                "created_at": result.created_at.isoformat()
            }
        
        return response
    
    async def cancel_query(self, query_id: str) -> Dict[str, Any]:
        """
        Cancel a running query.
        
        Args:
            query_id: Query ID
            
        Returns:
            Dictionary with cancellation status
            
        Raises:
            ValueError: If the query is not found or not running
        """
        # Check if the query is running
        if query_id not in self._running_tasks:
            # Check if the query exists
            query = await get_query_by_id(query_id)
            if not query:
                raise ValueError(f"Query with ID {query_id} not found")
            
            # Query exists but is not running
            return {
                "query_id": query_id,
                "status": query.status,
                "cancelled": False,
                "message": f"Query is not running (status: {query.status})"
            }
        
        # Cancel the running task
        task = self._running_tasks[query_id]
        task.cancel()
        
        # Try to cancel the query in the database connector
        try:
            query_tracker = connector_factory.get_query_tracker()
            db_cancel_result = query_tracker.cancel_query(query_id)
        except Exception as e:
            logger.error(f"Error cancelling query in database: {str(e)}")
            db_cancel_result = False
        
        # Update query status
        await update_query(query_id, QueryUpdate(
            status=QueryStatus.CANCELLED,
            end_time=datetime.utcnow()
        ))
        
        # Log the cancellation
        log_event("cancel_query", {
            "query_id": query_id,
            "db_cancel_result": db_cancel_result
        })
        
        return {
            "query_id": query_id,
            "status": QueryStatus.CANCELLED.value,
            "cancelled": True,
            "message": "Query cancelled successfully"
        }
    
    async def get_running_queries(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of running queries.
        
        Args:
            user_id: Optional user ID to filter queries
            
        Returns:
            List of running query information
        """
        running_queries = []
        
        for query_id in self._running_tasks:
            try:
                query = await get_query_by_id(query_id)
                if query and (user_id is None or query.user_id == user_id):
                    running_queries.append({
                        "query_id": query.id,
                        "user_id": query.user_id,
                        "db_id": query.db_id,
                        "status": query.status,
                        "start_time": query.start_time.isoformat() if query.start_time else None,
                        "natural_language": query.natural_language,
                        "executed_sql": query.executed_sql
                    })
            except Exception as e:
                logger.error(f"Error getting query {query_id}: {str(e)}")
        
        return running_queries