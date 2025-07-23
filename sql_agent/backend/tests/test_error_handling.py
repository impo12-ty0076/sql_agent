"""
Unit tests for error handling system
"""
import unittest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError, BaseModel

from ..models.error import (
    ErrorCode,
    ErrorCategory,
    ErrorSeverity,
    ErrorDetail,
    ErrorResponse
)
from ..models.database_exceptions import (
    ConnectionError,
    QueryError,
    SchemaError,
    UnsupportedDatabaseTypeError,
    DatabasePermissionError
)
from ..services.error_service import ErrorService
from ..utils.error_message_generator import ErrorMessageGenerator


class TestErrorModel(unittest.TestCase):
    """Test error models"""
    
    def test_error_detail_creation(self):
        """Test creating an error detail object"""
        error_detail = ErrorDetail(
            code=ErrorCode.DB_CONNECTION_FAILED,
            message="Failed to connect to database",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.ERROR,
            details={"db_id": "test_db"},
            suggestions=["Check connection settings"],
            retryable=True
        )
        
        self.assertEqual(error_detail.code, ErrorCode.DB_CONNECTION_FAILED)
        self.assertEqual(error_detail.message, "Failed to connect to database")
        self.assertEqual(error_detail.category, ErrorCategory.DATABASE)
        self.assertEqual(error_detail.severity, ErrorSeverity.ERROR)
        self.assertEqual(error_detail.details, {"db_id": "test_db"})
        self.assertEqual(error_detail.suggestions, ["Check connection settings"])
        self.assertTrue(error_detail.retryable)
    
    def test_error_response_creation(self):
        """Test creating an error response object"""
        error_detail = ErrorDetail(
            code=ErrorCode.DB_CONNECTION_FAILED,
            message="Failed to connect to database",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.ERROR,
            details={"db_id": "test_db"},
            suggestions=["Check connection settings"],
            retryable=True
        )
        
        error_response = ErrorResponse(error=error_detail)
        
        self.assertEqual(error_response.status, "error")
        self.assertEqual(error_response.error, error_detail)


class TestErrorService(unittest.TestCase):
    """Test error service"""
    
    def test_create_error_detail(self):
        """Test creating an error detail using the service"""
        error_detail = ErrorService.create_error_detail(
            code=ErrorCode.DB_CONNECTION_FAILED,
            details={"db_id": "test_db"},
            override_message="Custom error message",
            additional_suggestions=["Custom suggestion"]
        )
        
        self.assertEqual(error_detail.code, ErrorCode.DB_CONNECTION_FAILED)
        self.assertEqual(error_detail.message, "Custom error message")
        self.assertEqual(error_detail.category, ErrorCategory.DATABASE)
        self.assertEqual(error_detail.details, {"db_id": "test_db"})
        self.assertIn("Custom suggestion", error_detail.suggestions)
    
    def test_create_error_response(self):
        """Test creating an error response using the service"""
        error_response = ErrorService.create_error_response(
            code=ErrorCode.DB_CONNECTION_FAILED,
            details={"db_id": "test_db"}
        )
        
        self.assertEqual(error_response.status, "error")
        self.assertEqual(error_response.error.code, ErrorCode.DB_CONNECTION_FAILED)
        self.assertEqual(error_response.error.category, ErrorCategory.DATABASE)
        self.assertEqual(error_response.error.details, {"db_id": "test_db"})
    
    def test_get_http_status_code(self):
        """Test getting HTTP status code for error codes"""
        from fastapi import status
        
        # Authentication errors
        self.assertEqual(
            ErrorService.get_http_status_code(ErrorCode.AUTH_INVALID_CREDENTIALS),
            status.HTTP_401_UNAUTHORIZED
        )
        
        # Authorization errors
        self.assertEqual(
            ErrorService.get_http_status_code(ErrorCode.AUTHZ_INSUFFICIENT_PERMISSIONS),
            status.HTTP_403_FORBIDDEN
        )
        
        # Database errors
        self.assertEqual(
            ErrorService.get_http_status_code(ErrorCode.DB_CONNECTION_FAILED),
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
        # Validation errors
        self.assertEqual(
            ErrorService.get_http_status_code(ErrorCode.VAL_INVALID_INPUT),
            status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        
        # Business logic errors
        self.assertEqual(
            ErrorService.get_http_status_code(ErrorCode.BIZ_RESOURCE_NOT_FOUND),
            status.HTTP_404_NOT_FOUND
        )
    
    def test_map_exception_to_error_code(self):
        """Test mapping exceptions to error codes"""
        # Database exceptions
        self.assertEqual(
            ErrorService.map_exception_to_error_code(ConnectionError("test_db", "Failed to connect")),
            ErrorCode.DB_CONNECTION_FAILED
        )
        
        self.assertEqual(
            ErrorService.map_exception_to_error_code(QueryError("SELECT * FROM users", "Syntax error")),
            ErrorCode.DB_QUERY_FAILED
        )
        
        self.assertEqual(
            ErrorService.map_exception_to_error_code(SchemaError("Table not found")),
            ErrorCode.DB_SCHEMA_ERROR
        )
        
        self.assertEqual(
            ErrorService.map_exception_to_error_code(UnsupportedDatabaseTypeError("mongodb")),
            ErrorCode.DB_UNSUPPORTED_TYPE
        )
        
        self.assertEqual(
            ErrorService.map_exception_to_error_code(DatabasePermissionError("user1", "table1", "select")),
            ErrorCode.AUTHZ_DB_ACCESS_DENIED
        )
        
        # Standard exceptions
        self.assertEqual(
            ErrorService.map_exception_to_error_code(ValueError("Invalid value")),
            ErrorCode.VAL_INVALID_INPUT
        )
        
        self.assertEqual(
            ErrorService.map_exception_to_error_code(TypeError("Invalid type")),
            ErrorCode.VAL_TYPE_MISMATCH
        )
        
        # Unknown exception
        self.assertEqual(
            ErrorService.map_exception_to_error_code(Exception("Unknown error")),
            ErrorCode.UNKNOWN_ERROR
        )
    
    def test_handle_exception(self):
        """Test handling exceptions"""
        # Create a test exception
        exception = ConnectionError("test_db", "Failed to connect")
        
        # Handle the exception
        error_response = ErrorService.handle_exception(
            exception=exception,
            user_id="user1",
            additional_details={"test": "value"}
        )
        
        # Check the response
        self.assertEqual(error_response.status, "error")
        self.assertEqual(error_response.error.code, ErrorCode.DB_CONNECTION_FAILED)
        self.assertEqual(error_response.error.category, ErrorCategory.DATABASE)
        self.assertEqual(error_response.error.details["exception_type"], "ConnectionError")
        self.assertEqual(error_response.error.details["test"], "value")


class TestErrorMessageGenerator(unittest.TestCase):
    """Test error message generator"""
    
    def test_generate_db_connection_error_message(self):
        """Test generating user-friendly message for DB connection errors"""
        # Timeout error
        message = ErrorMessageGenerator.generate_db_connection_error_message({
            "exception_message": "Connection timeout after 30 seconds",
            "db_id": "test_db"
        })
        self.assertIn("시간이 초과되었습니다", message)
        
        # Authentication error
        message = ErrorMessageGenerator.generate_db_connection_error_message({
            "exception_message": "Authentication failed for user 'admin'",
            "db_id": "test_db"
        })
        self.assertIn("인증 정보가 올바르지 않습니다", message)
        
        # Host error
        message = ErrorMessageGenerator.generate_db_connection_error_message({
            "exception_message": "Could not resolve host: db.example.com",
            "db_id": "test_db"
        })
        self.assertIn("서버를 찾을 수 없습니다", message)
    
    def test_generate_db_query_error_message(self):
        """Test generating user-friendly message for DB query errors"""
        # Syntax error
        message = ErrorMessageGenerator.generate_db_query_error_message({
            "exception_message": "Syntax error in SQL statement",
            "query": "SELECT * FORM users"
        })
        self.assertIn("문법 오류", message)
        
        # Column not found
        message = ErrorMessageGenerator.generate_db_query_error_message({
            "exception_message": "column 'user_name' not found",
            "query": "SELECT user_name FROM users"
        })
        self.assertIn("'user_name' 컬럼을 찾을 수 없습니다", message)
        
        # Table not found
        message = ErrorMessageGenerator.generate_db_query_error_message({
            "exception_message": "table 'users' not found",
            "query": "SELECT * FROM users"
        })
        self.assertIn("'users' 테이블을 찾을 수 없습니다", message)
    
    def test_generate_llm_error_message(self):
        """Test generating user-friendly message for LLM service errors"""
        # Quota exceeded
        message = ErrorMessageGenerator.generate_llm_error_message({
            "exception_message": "API rate limit exceeded"
        })
        self.assertIn("할당량을 초과했습니다", message)
        
        # Timeout
        message = ErrorMessageGenerator.generate_llm_error_message({
            "exception_message": "Request timeout after 60 seconds"
        })
        self.assertIn("시간이 초과되었습니다", message)
        
        # Content filter
        message = ErrorMessageGenerator.generate_llm_error_message({
            "exception_message": "Content filtered due to policy violation"
        })
        self.assertIn("콘텐츠 필터에 의해 요청이 차단되었습니다", message)
    
    def test_generate_validation_error_message(self):
        """Test generating user-friendly message for validation errors"""
        # Field validation error
        message = ErrorMessageGenerator.generate_validation_error_message({
            "validation_errors": [
                {
                    "loc": ["body", "username"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        })
        self.assertIn("'body.username': field required", message)
    
    def test_generate_user_friendly_message(self):
        """Test generating user-friendly message based on error details"""
        # DB connection error
        error_detail = ErrorDetail(
            code=ErrorCode.DB_CONNECTION_FAILED,
            message="",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.ERROR,
            details={
                "exception_message": "Connection timeout after 30 seconds",
                "db_id": "test_db"
            }
        )
        message = ErrorMessageGenerator.generate_user_friendly_message(error_detail)
        self.assertIn("시간이 초과되었습니다", message)
        
        # Custom message
        error_detail = ErrorDetail(
            code=ErrorCode.DB_CONNECTION_FAILED,
            message="Custom error message",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.ERROR
        )
        message = ErrorMessageGenerator.generate_user_friendly_message(error_detail)
        self.assertEqual(message, "Custom error message")


if __name__ == "__main__":
    unittest.main()