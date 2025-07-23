"""
Middleware for request logging and error handling
"""
from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging
import time
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)

class LoggingMiddleware:
    """Middleware for request logging"""
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response
        
        Args:
            request: FastAPI request
            call_next: Next middleware or endpoint
            
        Returns:
            Response
        """
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Time: {process_time:.4f}s"
            )
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} "
                f"- Error: {str(e)} - Time: {process_time:.4f}s"
            )
            
            # Re-raise exception for error handler
            raise

class ErrorHandler:
    """Error handlers for various exceptions"""
    
    @staticmethod
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle validation errors
        
        Args:
            request: FastAPI request
            exc: Validation error
            
        Returns:
            JSON response with error details
        """
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "code": "validation_error",
                "message": "Validation error",
                "details": exc.errors()
            }
        )
    
    @staticmethod
    async def db_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """
        Handle database errors
        
        Args:
            request: FastAPI request
            exc: Database error
            
        Returns:
            JSON response with error details
        """
        logger.error(f"Database error: {str(exc)}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "code": "database_error",
                "message": "Database error",
                "details": str(exc)
            }
        )
    
    @staticmethod
    async def http_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle general errors
        
        Args:
            request: FastAPI request
            exc: General error
            
        Returns:
            JSON response with error details
        """
        logger.error(f"Unhandled error: {str(exc)}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "code": "internal_server_error",
                "message": "Internal server error",
                "details": str(exc)
            }
        )