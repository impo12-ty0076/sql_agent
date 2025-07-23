"""
Error handling service for structured error handling
"""
import logging
import traceback
from typing import Dict, List, Optional, Any, Type, Union
from fastapi import status
from pydantic import ValidationError

from ..models.error import (
    ErrorCode, 
    ErrorCategory, 
    ErrorSeverity, 
    ErrorDetail, 
    ErrorResponse,
    ERROR_MESSAGES,
    ERROR_CATEGORIES,
    ERROR_SEVERITIES,
    ERROR_RETRYABLE,
    ERROR_SUGGESTIONS
)
from ..utils.logging import log_error, log_exception

logger = logging.getLogger(__name__)


class ErrorService:
    """Service for handling errors in a structured way"""
    
    @staticmethod
    def create_error_detail(
        code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        override_message: Optional[str] = None,
        additional_suggestions: Optional[List[str]] = None
    ) -> ErrorDetail:
        """
        Create a structured error detail object
        
        Args:
            code: Error code
            details: Additional error details
            override_message: Custom error message (overrides default message)
            additional_suggestions: Additional suggestions to append to default suggestions
            
        Returns:
            ErrorDetail object
        """
        # Get default values from mappings
        message = override_message or ERROR_MESSAGES.get(code, "Unknown error")
        category = ERROR_CATEGORIES.get(code, ErrorCategory.UNKNOWN)
        severity = ERROR_SEVERITIES.get(code, ErrorSeverity.ERROR)
        retryable = ERROR_RETRYABLE.get(code, False)
        
        # Get suggestions and append additional ones if provided
        suggestions = ERROR_SUGGESTIONS.get(code, [])
        if additional_suggestions:
            suggestions.extend(additional_suggestions)
        
        # Create error detail
        return ErrorDetail(
            code=code,
            message=message,
            category=category,
            severity=severity,
            details=details,
            suggestions=suggestions if suggestions else None,
            retryable=retryable
        )
    
    @staticmethod
    def create_error_response(
        code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        override_message: Optional[str] = None,
        additional_suggestions: Optional[List[str]] = None
    ) -> ErrorResponse:
        """
        Create a structured error response
        
        Args:
            code: Error code
            details: Additional error details
            override_message: Custom error message (overrides default message)
            additional_suggestions: Additional suggestions to append to default suggestions
            
        Returns:
            ErrorResponse object
        """
        error_detail = ErrorService.create_error_detail(
            code=code,
            details=details,
            override_message=override_message,
            additional_suggestions=additional_suggestions
        )
        
        return ErrorResponse(error=error_detail)
    
    @staticmethod
    def log_error(
        code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        override_message: Optional[str] = None,
        exception: Optional[Exception] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Log an error with structured information
        
        Args:
            code: Error code
            details: Additional error details
            override_message: Custom error message (overrides default message)
            exception: Exception object if available
            user_id: User ID if available
        """
        # Get default values from mappings
        message = override_message or ERROR_MESSAGES.get(code, "Unknown error")
        category = ERROR_CATEGORIES.get(code, ErrorCategory.UNKNOWN)
        severity = ERROR_SEVERITIES.get(code, ErrorSeverity.ERROR)
        
        # Create context for logging
        context = {
            "error_code": code,
            "error_category": category,
            "error_severity": severity
        }
        
        if details:
            context.update({"details": details})
        
        if user_id:
            context.update({"user_id": user_id})
        
        if exception:
            context.update({
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "traceback": traceback.format_exc()
            })
            log_exception(exception, context)
        else:
            log_error(str(code), message, context)
    
    @staticmethod
    def get_http_status_code(code: ErrorCode) -> int:
        """
        Get the appropriate HTTP status code for an error code
        
        Args:
            code: Error code
            
        Returns:
            HTTP status code
        """
        # Authentication errors
        if code.startswith("AUTH_"):
            if code == ErrorCode.AUTH_INVALID_CREDENTIALS:
                return status.HTTP_401_UNAUTHORIZED
            if code == ErrorCode.AUTH_EXPIRED_TOKEN:
                return status.HTTP_401_UNAUTHORIZED
            if code == ErrorCode.AUTH_INVALID_TOKEN:
                return status.HTTP_401_UNAUTHORIZED
            if code == ErrorCode.AUTH_MISSING_TOKEN:
                return status.HTTP_401_UNAUTHORIZED
            if code == ErrorCode.AUTH_SESSION_EXPIRED:
                return status.HTTP_401_UNAUTHORIZED
            if code == ErrorCode.AUTH_ACCOUNT_LOCKED:
                return status.HTTP_403_FORBIDDEN
        
        # Authorization errors
        if code.startswith("AUTHZ_"):
            return status.HTTP_403_FORBIDDEN
        
        # Database errors
        if code.startswith("DB_"):
            if code == ErrorCode.DB_CONNECTION_FAILED:
                return status.HTTP_503_SERVICE_UNAVAILABLE
            if code == ErrorCode.DB_TIMEOUT:
                return status.HTTP_504_GATEWAY_TIMEOUT
            if code == ErrorCode.DB_RESOURCE_LIMIT:
                return status.HTTP_429_TOO_MANY_REQUESTS
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Validation errors
        if code.startswith("VAL_"):
            return status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Business logic errors
        if code.startswith("BIZ_"):
            if code == ErrorCode.BIZ_RESOURCE_NOT_FOUND:
                return status.HTTP_404_NOT_FOUND
            if code == ErrorCode.BIZ_DUPLICATE_RESOURCE:
                return status.HTTP_409_CONFLICT
            if code == ErrorCode.BIZ_RESOURCE_CONFLICT:
                return status.HTTP_409_CONFLICT
            if code == ErrorCode.BIZ_OPERATION_TIMEOUT:
                return status.HTTP_504_GATEWAY_TIMEOUT
            if code == ErrorCode.BIZ_QUOTA_EXCEEDED:
                return status.HTTP_429_TOO_MANY_REQUESTS
            return status.HTTP_400_BAD_REQUEST
        
        # External service errors
        if code.startswith("EXT_"):
            if code == ErrorCode.EXT_SERVICE_UNAVAILABLE:
                return status.HTTP_503_SERVICE_UNAVAILABLE
            if code == ErrorCode.EXT_SERVICE_TIMEOUT:
                return status.HTTP_504_GATEWAY_TIMEOUT
            return status.HTTP_502_BAD_GATEWAY
        
        # LLM service errors
        if code.startswith("LLM_"):
            if code == ErrorCode.LLM_QUOTA_EXCEEDED:
                return status.HTTP_429_TOO_MANY_REQUESTS
            if code == ErrorCode.LLM_TIMEOUT:
                return status.HTTP_504_GATEWAY_TIMEOUT
            return status.HTTP_502_BAD_GATEWAY
        
        # System errors
        if code.startswith("SYS_"):
            if code == ErrorCode.SYS_MAINTENANCE:
                return status.HTTP_503_SERVICE_UNAVAILABLE
            if code == ErrorCode.SYS_RESOURCE_EXHAUSTED:
                return status.HTTP_503_SERVICE_UNAVAILABLE
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Network errors
        if code.startswith("NET_"):
            if code == ErrorCode.NET_TIMEOUT:
                return status.HTTP_504_GATEWAY_TIMEOUT
            return status.HTTP_502_BAD_GATEWAY
        
        # Default for unknown errors
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @staticmethod
    def map_exception_to_error_code(exception: Exception) -> ErrorCode:
        """
        Map an exception to an error code
        
        Args:
            exception: Exception object
            
        Returns:
            Appropriate error code for the exception
        """
        # Map common exceptions to error codes
        exception_type = type(exception).__name__
        
        # Database exceptions
        if exception_type == "ConnectionError" or "ConnectionError" in exception_type:
            return ErrorCode.DB_CONNECTION_FAILED
        
        if exception_type == "TimeoutError" or "Timeout" in exception_type:
            return ErrorCode.DB_TIMEOUT
        
        if exception_type == "QueryError" or "SQLAlchemyError" in exception_type:
            return ErrorCode.DB_QUERY_FAILED
        
        if exception_type == "SchemaError":
            return ErrorCode.DB_SCHEMA_ERROR
        
        if exception_type == "UnsupportedDatabaseTypeError":
            return ErrorCode.DB_UNSUPPORTED_TYPE
        
        if exception_type == "DatabasePermissionError":
            return ErrorCode.AUTHZ_DB_ACCESS_DENIED
        
        # Validation exceptions
        if exception_type == "ValidationError" or isinstance(exception, ValidationError):
            return ErrorCode.VAL_INVALID_INPUT
        
        if exception_type == "ValueError":
            return ErrorCode.VAL_INVALID_INPUT
        
        if exception_type == "TypeError":
            return ErrorCode.VAL_TYPE_MISMATCH
        
        # Authentication exceptions
        if "Unauthorized" in exception_type or "AuthenticationError" in exception_type:
            return ErrorCode.AUTH_INVALID_CREDENTIALS
        
        if "TokenExpired" in exception_type:
            return ErrorCode.AUTH_EXPIRED_TOKEN
        
        if "InvalidToken" in exception_type:
            return ErrorCode.AUTH_INVALID_TOKEN
        
        # LLM exceptions
        if "OpenAIError" in exception_type or "LLMError" in exception_type:
            return ErrorCode.LLM_API_ERROR
        
        # Network exceptions
        if "ConnectionError" in exception_type or "NetworkError" in exception_type:
            return ErrorCode.NET_CONNECTION_ERROR
        
        # Default for unknown exceptions
        return ErrorCode.UNKNOWN_ERROR
    
    @staticmethod
    def handle_exception(
        exception: Exception,
        user_id: Optional[str] = None,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> ErrorResponse:
        """
        Handle an exception and create a structured error response
        
        Args:
            exception: Exception object
            user_id: User ID if available
            additional_details: Additional details to include in the error
            
        Returns:
            ErrorResponse object
        """
        # Map exception to error code
        error_code = ErrorService.map_exception_to_error_code(exception)
        
        # Create details
        details = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception)
        }
        
        if additional_details:
            details.update(additional_details)
        
        # Log the error
        ErrorService.log_error(
            code=error_code,
            details=details,
            exception=exception,
            user_id=user_id
        )
        
        # Create and return error response
        return ErrorService.create_error_response(
            code=error_code,
            details=details
        )