"""
Enhanced error handling middleware for FastAPI
"""
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import Dict, Any, Callable, Union, Type

from ..models.error import ErrorCode, ErrorCategory, ErrorSeverity
from ..models.database_exceptions import DatabaseError
from ..services.error_service import ErrorService

logger = logging.getLogger(__name__)


class EnhancedErrorHandler:
    """Enhanced error handlers for various exceptions using structured error handling"""
    
    @staticmethod
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle validation errors
        
        Args:
            request: FastAPI request
            exc: Validation error
            
        Returns:
            JSON response with structured error details
        """
        # Extract validation error details
        error_details = []
        for error in exc.errors():
            error_details.append({
                "loc": error.get("loc", []),
                "msg": error.get("msg", ""),
                "type": error.get("type", "")
            })
        
        # Create error response
        error_response = ErrorService.create_error_response(
            code=ErrorCode.VAL_INVALID_INPUT,
            details={"validation_errors": error_details}
        )
        
        # Log the error
        ErrorService.log_error(
            code=ErrorCode.VAL_INVALID_INPUT,
            details={"validation_errors": error_details},
            exception=exc
        )
        
        # Return JSON response
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.dict()
        )
    
    @staticmethod
    async def db_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """
        Handle database errors
        
        Args:
            request: FastAPI request
            exc: Database error
            
        Returns:
            JSON response with structured error details
        """
        # Map SQLAlchemy error to appropriate error code
        if "connection" in str(exc).lower():
            error_code = ErrorCode.DB_CONNECTION_FAILED
        elif "timeout" in str(exc).lower():
            error_code = ErrorCode.DB_TIMEOUT
        elif "permission" in str(exc).lower():
            error_code = ErrorCode.AUTHZ_DB_ACCESS_DENIED
        else:
            error_code = ErrorCode.DB_QUERY_FAILED
        
        # Create error response
        error_response = ErrorService.create_error_response(
            code=error_code,
            details={"sqlalchemy_error": str(exc)}
        )
        
        # Log the error
        ErrorService.log_error(
            code=error_code,
            details={"sqlalchemy_error": str(exc)},
            exception=exc
        )
        
        # Get appropriate HTTP status code
        http_status = ErrorService.get_http_status_code(error_code)
        
        # Return JSON response
        return JSONResponse(
            status_code=http_status,
            content=error_response.dict()
        )
    
    @staticmethod
    async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
        """
        Handle custom database errors
        
        Args:
            request: FastAPI request
            exc: Custom database error
            
        Returns:
            JSON response with structured error details
        """
        # Map custom database error to appropriate error code
        error_code = ErrorService.map_exception_to_error_code(exc)
        
        # Create error response
        error_response = ErrorService.create_error_response(
            code=error_code,
            details={"database_error": str(exc)}
        )
        
        # Log the error
        ErrorService.log_error(
            code=error_code,
            details={"database_error": str(exc)},
            exception=exc
        )
        
        # Get appropriate HTTP status code
        http_status = ErrorService.get_http_status_code(error_code)
        
        # Return JSON response
        return JSONResponse(
            status_code=http_status,
            content=error_response.dict()
        )
    
    @staticmethod
    async def http_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle general errors
        
        Args:
            request: FastAPI request
            exc: General error
            
        Returns:
            JSON response with structured error details
        """
        # Handle exception using error service
        error_response = ErrorService.handle_exception(exc)
        
        # Get appropriate HTTP status code
        http_status = ErrorService.get_http_status_code(error_response.error.code)
        
        # Return JSON response
        return JSONResponse(
            status_code=http_status,
            content=error_response.dict()
        )