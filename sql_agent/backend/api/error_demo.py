"""
Demo API for error handling system
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging

from ..models.error import ErrorCode
from ..models.database_exceptions import (
    ConnectionError,
    QueryError,
    SchemaError,
    UnsupportedDatabaseTypeError,
    DatabasePermissionError
)
from ..services.error_service import ErrorService

router = APIRouter(prefix="/api/error-demo", tags=["오류 처리 데모"])

logger = logging.getLogger(__name__)


class ErrorDemoRequest(BaseModel):
    """Request model for error demo"""
    error_type: str = Field(..., description="Error type to simulate")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


@router.post("/simulate")
async def simulate_error(request: ErrorDemoRequest):
    """
    오류 시뮬레이션 엔드포인트
    
    다양한 유형의 오류를 시뮬레이션하여 오류 처리 시스템을 테스트합니다.
    
    Args:
        request: Error simulation request
        
    Returns:
        Success message if no error is simulated
    """
    error_type = request.error_type.lower()
    details = request.details or {}
    
    # Simulate database errors
    if error_type == "db_connection":
        db_id = details.get("db_id", "test_db")
        message = details.get("message", "Failed to connect to database")
        raise ConnectionError(db_id, message)
    
    if error_type == "db_query":
        query = details.get("query", "SELECT * FROM users")
        message = details.get("message", "Query execution failed")
        raise QueryError(query, message)
    
    if error_type == "db_schema":
        message = details.get("message", "Schema error")
        raise SchemaError(message)
    
    if error_type == "db_unsupported":
        db_type = details.get("db_type", "mongodb")
        raise UnsupportedDatabaseTypeError(db_type)
    
    if error_type == "db_permission":
        user_id = details.get("user_id", "user1")
        resource = details.get("resource", "users")
        action = details.get("action", "select")
        raise DatabasePermissionError(user_id, resource, action)
    
    # Simulate validation errors
    if error_type == "validation":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation error"
        )
    
    # Simulate authentication errors
    if error_type == "auth_invalid_credentials":
        error_response = ErrorService.create_error_response(
            code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            details=details
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response.dict()
        )
    
    if error_type == "auth_expired_token":
        error_response = ErrorService.create_error_response(
            code=ErrorCode.AUTH_EXPIRED_TOKEN,
            details=details
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response.dict()
        )
    
    # Simulate LLM service errors
    if error_type == "llm_api_error":
        error_response = ErrorService.create_error_response(
            code=ErrorCode.LLM_API_ERROR,
            details=details
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error_response.dict()
        )
    
    if error_type == "llm_quota_exceeded":
        error_response = ErrorService.create_error_response(
            code=ErrorCode.LLM_QUOTA_EXCEEDED,
            details=details
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_response.dict()
        )
    
    # Simulate system errors
    if error_type == "system_error":
        error_response = ErrorService.create_error_response(
            code=ErrorCode.SYS_INTERNAL_ERROR,
            details=details
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )
    
    # Default: no error
    return {
        "status": "success",
        "message": "No error simulated"
    }


@router.get("/test-db-connection")
async def test_db_connection(
    host: str = Query(..., description="Database host"),
    port: int = Query(..., description="Database port"),
    username: str = Query(..., description="Database username"),
    password: str = Query(..., description="Database password"),
    db_type: str = Query(..., description="Database type (mssql, hana)")
):
    """
    데이터베이스 연결 테스트 엔드포인트
    
    제공된 연결 정보로 데이터베이스 연결을 테스트합니다.
    
    Args:
        host: Database host
        port: Database port
        username: Database username
        password: Database password
        db_type: Database type
        
    Returns:
        Connection test result
    """
    # Simulate connection error for demonstration
    if host == "invalid-host":
        raise ConnectionError("test_db", f"Could not resolve host: {host}")
    
    if port < 0 or port > 65535:
        raise ConnectionError("test_db", f"Invalid port number: {port}")
    
    if username == "invalid-user" or password == "invalid-password":
        raise ConnectionError("test_db", "Authentication failed")
    
    if db_type not in ["mssql", "hana"]:
        raise UnsupportedDatabaseTypeError(db_type)
    
    # Success case
    return {
        "status": "success",
        "message": f"Successfully connected to {db_type} database at {host}:{port}"
    }


@router.get("/test-query")
async def test_query(
    query: str = Query(..., description="SQL query to test")
):
    """
    SQL 쿼리 테스트 엔드포인트
    
    제공된 SQL 쿼리의 유효성을 테스트합니다.
    
    Args:
        query: SQL query
        
    Returns:
        Query validation result
    """
    # Simulate query errors for demonstration
    if "FORM" in query:  # Common typo for FROM
        raise QueryError(query, "Syntax error in SQL statement: 'FORM' is not a valid keyword")
    
    if "DROP" in query or "DELETE" in query or "UPDATE" in query or "INSERT" in query:
        raise QueryError(query, "Data modification queries are not allowed")
    
    if "non_existent_table" in query:
        raise QueryError(query, "Table 'non_existent_table' not found")
    
    if "non_existent_column" in query:
        raise QueryError(query, "Column 'non_existent_column' not found")
    
    # Success case
    return {
        "status": "success",
        "message": "Query validation successful",
        "query": query
    }