"""
Utility for generating user-friendly error messages
"""
from typing import Dict, List, Optional, Any
import re

from ..models.error import ErrorCode, ErrorDetail


class ErrorMessageGenerator:
    """Utility for generating user-friendly error messages"""
    
    @staticmethod
    def generate_db_connection_error_message(details: Dict[str, Any]) -> str:
        """
        Generate user-friendly message for database connection errors
        
        Args:
            details: Error details
            
        Returns:
            User-friendly error message
        """
        base_message = "데이터베이스 연결에 실패했습니다."
        
        # Extract specific error information
        error_message = details.get("exception_message", "")
        db_id = details.get("db_id", "")
        
        if "timeout" in error_message.lower():
            return f"{base_message} 데이터베이스 서버 응답 시간이 초과되었습니다. 나중에 다시 시도해주세요."
        
        if "authentication" in error_message.lower() or "login" in error_message.lower():
            return f"{base_message} 인증 정보가 올바르지 않습니다. 데이터베이스 사용자 이름과 비밀번호를 확인해주세요."
        
        if "host" in error_message.lower() or "server" in error_message.lower():
            return f"{base_message} 데이터베이스 서버를 찾을 수 없습니다. 호스트 이름과 포트 번호를 확인해주세요."
        
        if db_id:
            return f"{base_message} 데이터베이스 '{db_id}'에 연결할 수 없습니다. 연결 정보를 확인하거나 관리자에게 문의하세요."
        
        return f"{base_message} 연결 정보를 확인하거나 나중에 다시 시도해주세요."
    
    @staticmethod
    def generate_db_query_error_message(details: Dict[str, Any]) -> str:
        """
        Generate user-friendly message for database query errors
        
        Args:
            details: Error details
            
        Returns:
            User-friendly error message
        """
        base_message = "쿼리 실행 중 오류가 발생했습니다."
        
        # Extract specific error information
        error_message = details.get("exception_message", "")
        query = details.get("query", "")
        
        if "syntax" in error_message.lower():
            return f"{base_message} SQL 문법 오류가 있습니다. 쿼리 구문을 확인해주세요."
        
        if "column" in error_message.lower() and "not found" in error_message.lower():
            # Try to extract column name
            match = re.search(r"column ['\"]?([^'\"]+)['\"]? not found", error_message, re.IGNORECASE)
            if match:
                column_name = match.group(1)
                return f"{base_message} '{column_name}' 컬럼을 찾을 수 없습니다. 컬럼 이름이 올바른지 확인해주세요."
        
        if "table" in error_message.lower() and "not found" in error_message.lower():
            # Try to extract table name
            match = re.search(r"table ['\"]?([^'\"]+)['\"]? not found", error_message, re.IGNORECASE)
            if match:
                table_name = match.group(1)
                return f"{base_message} '{table_name}' 테이블을 찾을 수 없습니다. 테이블 이름이 올바른지 확인해주세요."
        
        if "permission" in error_message.lower() or "denied" in error_message.lower():
            return f"{base_message} 데이터베이스 권한이 부족합니다. 필요한 권한이 있는지 확인하거나 관리자에게 문의하세요."
        
        if "timeout" in error_message.lower():
            return f"{base_message} 쿼리 실행 시간이 초과되었습니다. 쿼리를 최적화하거나 결과를 제한해보세요."
        
        return f"{base_message} SQL 문법과 테이블/컬럼 이름을 확인해주세요."
    
    @staticmethod
    def generate_llm_error_message(details: Dict[str, Any]) -> str:
        """
        Generate user-friendly message for LLM service errors
        
        Args:
            details: Error details
            
        Returns:
            User-friendly error message
        """
        base_message = "AI 서비스 처리 중 오류가 발생했습니다."
        
        # Extract specific error information
        error_message = details.get("exception_message", "")
        
        if "quota" in error_message.lower() or "rate limit" in error_message.lower():
            return f"{base_message} API 할당량을 초과했습니다. 잠시 후 다시 시도해주세요."
        
        if "timeout" in error_message.lower():
            return f"{base_message} 응답 시간이 초과되었습니다. 질의를 간소화하거나 나중에 다시 시도해주세요."
        
        if "content filter" in error_message.lower() or "content policy" in error_message.lower():
            return f"{base_message} 콘텐츠 필터에 의해 요청이 차단되었습니다. 질의 내용을 수정해주세요."
        
        if "invalid" in error_message.lower() and "api key" in error_message.lower():
            return f"{base_message} API 키가 유효하지 않습니다. 관리자에게 문의하세요."
        
        return f"{base_message} 잠시 후 다시 시도하거나 질의를 수정해주세요."
    
    @staticmethod
    def generate_validation_error_message(details: Dict[str, Any]) -> str:
        """
        Generate user-friendly message for validation errors
        
        Args:
            details: Error details
            
        Returns:
            User-friendly error message
        """
        base_message = "입력값이 유효하지 않습니다."
        
        # Extract validation errors
        validation_errors = details.get("validation_errors", [])
        if not validation_errors:
            return base_message
        
        # Process first error for user-friendly message
        first_error = validation_errors[0]
        location = ".".join([str(loc) for loc in first_error.get("loc", [])])
        message = first_error.get("msg", "")
        
        if location and message:
            return f"{base_message} '{location}': {message}"
        
        return base_message
    
    @staticmethod
    def generate_user_friendly_message(error_detail: ErrorDetail) -> str:
        """
        Generate user-friendly message based on error details
        
        Args:
            error_detail: Error detail object
            
        Returns:
            User-friendly error message
        """
        # Use custom message if provided
        if error_detail.message:
            return error_detail.message
        
        # Generate message based on error code and details
        code = error_detail.code
        details = error_detail.details or {}
        
        # Database connection errors
        if code == ErrorCode.DB_CONNECTION_FAILED:
            return ErrorMessageGenerator.generate_db_connection_error_message(details)
        
        # Database query errors
        if code == ErrorCode.DB_QUERY_FAILED:
            return ErrorMessageGenerator.generate_db_query_error_message(details)
        
        # LLM service errors
        if code.startswith("LLM_"):
            return ErrorMessageGenerator.generate_llm_error_message(details)
        
        # Validation errors
        if code.startswith("VAL_"):
            return ErrorMessageGenerator.generate_validation_error_message(details)
        
        # Default: return the standard message for this error code
        from ..models.error import ERROR_MESSAGES
        return ERROR_MESSAGES.get(code, "알 수 없는 오류가 발생했습니다.")