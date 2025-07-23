"""
Logging utilities
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def log_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    Log an event
    
    Args:
        event_type: Type of event
        data: Event data
    """
    logger.info(f"Event: {event_type} - Data: {data}")

def log_error(error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an error
    
    Args:
        error_type: Type of error
        error_message: Error message
        context: Error context
    """
    logger.error(f"Error: {error_type} - Message: {error_message} - Context: {context or {}}")

def log_warning(warning_type: str, warning_message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a warning
    
    Args:
        warning_type: Type of warning
        warning_message: Warning message
        context: Warning context
    """
    logger.warning(f"Warning: {warning_type} - Message: {warning_message} - Context: {context or {}}")

def log_debug(debug_type: str, debug_message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a debug message
    
    Args:
        debug_type: Type of debug message
        debug_message: Debug message
        context: Debug context
    """
    logger.debug(f"Debug: {debug_type} - Message: {debug_message} - Context: {context or {}}")

def log_info(info_type: str, info_message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an info message
    
    Args:
        info_type: Type of info message
        info_message: Info message
        context: Info context
    """
    logger.info(f"Info: {info_type} - Message: {info_message} - Context: {context or {}}")

def log_critical(critical_type: str, critical_message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a critical message
    
    Args:
        critical_type: Type of critical message
        critical_message: Critical message
        context: Critical context
    """
    logger.critical(f"Critical: {critical_type} - Message: {critical_message} - Context: {context or {}}")

def log_exception(exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an exception
    
    Args:
        exception: Exception
        context: Exception context
    """
    logger.exception(f"Exception: {str(exception)} - Context: {context or {}}")

def log_query(user_id: str, db_id: str, query_id: str, query_text: str, query_type: str) -> None:
    """
    Log a query
    
    Args:
        user_id: User ID
        db_id: Database ID
        query_id: Query ID
        query_text: Query text
        query_type: Query type (natural, sql, rag)
    """
    logger.info(
        f"Query: {query_type} - User: {user_id} - DB: {db_id} - ID: {query_id} - Text: {query_text[:100]}..."
    )