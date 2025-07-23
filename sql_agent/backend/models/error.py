"""
Error models and utilities for structured error handling
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories"""
    AUTHENTICATION = "authentication"  # 인증 관련 오류
    AUTHORIZATION = "authorization"    # 권한 관련 오류
    DATABASE = "database"              # 데이터베이스 관련 오류
    VALIDATION = "validation"          # 입력 검증 관련 오류
    BUSINESS_LOGIC = "business_logic"  # 비즈니스 로직 관련 오류
    EXTERNAL_SERVICE = "external_service"  # 외부 서비스 관련 오류
    LLM = "llm"                        # LLM 서비스 관련 오류
    SYSTEM = "system"                  # 시스템 관련 오류
    NETWORK = "network"                # 네트워크 관련 오류
    RESOURCE = "resource"              # 리소스 관련 오류
    UNKNOWN = "unknown"                # 알 수 없는 오류


class ErrorCode(str, Enum):
    """Error codes with structured naming convention: CATEGORY_SPECIFIC_ERROR"""
    # Authentication errors (100-199)
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_EXPIRED_TOKEN = "AUTH_EXPIRED_TOKEN"
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_MISSING_TOKEN = "AUTH_MISSING_TOKEN"
    AUTH_SESSION_EXPIRED = "AUTH_SESSION_EXPIRED"
    AUTH_ACCOUNT_LOCKED = "AUTH_ACCOUNT_LOCKED"
    
    # Authorization errors (200-299)
    AUTHZ_INSUFFICIENT_PERMISSIONS = "AUTHZ_INSUFFICIENT_PERMISSIONS"
    AUTHZ_RESOURCE_FORBIDDEN = "AUTHZ_RESOURCE_FORBIDDEN"
    AUTHZ_DB_ACCESS_DENIED = "AUTHZ_DB_ACCESS_DENIED"
    AUTHZ_TABLE_ACCESS_DENIED = "AUTHZ_TABLE_ACCESS_DENIED"
    
    # Database errors (300-399)
    DB_CONNECTION_FAILED = "DB_CONNECTION_FAILED"
    DB_QUERY_FAILED = "DB_QUERY_FAILED"
    DB_SCHEMA_ERROR = "DB_SCHEMA_ERROR"
    DB_TIMEOUT = "DB_TIMEOUT"
    DB_UNSUPPORTED_TYPE = "DB_UNSUPPORTED_TYPE"
    DB_RESOURCE_LIMIT = "DB_RESOURCE_LIMIT"
    DB_DATA_INTEGRITY = "DB_DATA_INTEGRITY"
    
    # Validation errors (400-499)
    VAL_INVALID_INPUT = "VAL_INVALID_INPUT"
    VAL_MISSING_REQUIRED = "VAL_MISSING_REQUIRED"
    VAL_TYPE_MISMATCH = "VAL_TYPE_MISMATCH"
    VAL_CONSTRAINT_VIOLATION = "VAL_CONSTRAINT_VIOLATION"
    VAL_INVALID_FORMAT = "VAL_INVALID_FORMAT"
    
    # Business logic errors (500-599)
    BIZ_INVALID_OPERATION = "BIZ_INVALID_OPERATION"
    BIZ_RESOURCE_NOT_FOUND = "BIZ_RESOURCE_NOT_FOUND"
    BIZ_DUPLICATE_RESOURCE = "BIZ_DUPLICATE_RESOURCE"
    BIZ_RESOURCE_CONFLICT = "BIZ_RESOURCE_CONFLICT"
    BIZ_OPERATION_TIMEOUT = "BIZ_OPERATION_TIMEOUT"
    BIZ_QUOTA_EXCEEDED = "BIZ_QUOTA_EXCEEDED"
    
    # External service errors (600-699)
    EXT_SERVICE_UNAVAILABLE = "EXT_SERVICE_UNAVAILABLE"
    EXT_SERVICE_TIMEOUT = "EXT_SERVICE_TIMEOUT"
    EXT_SERVICE_ERROR = "EXT_SERVICE_ERROR"
    EXT_SERVICE_INVALID_RESPONSE = "EXT_SERVICE_INVALID_RESPONSE"
    
    # LLM service errors (700-799)
    LLM_API_ERROR = "LLM_API_ERROR"
    LLM_QUOTA_EXCEEDED = "LLM_QUOTA_EXCEEDED"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_INVALID_RESPONSE = "LLM_INVALID_RESPONSE"
    LLM_CONTENT_FILTER = "LLM_CONTENT_FILTER"
    LLM_SQL_GENERATION_FAILED = "LLM_SQL_GENERATION_FAILED"
    
    # System errors (800-899)
    SYS_INTERNAL_ERROR = "SYS_INTERNAL_ERROR"
    SYS_NOT_IMPLEMENTED = "SYS_NOT_IMPLEMENTED"
    SYS_MAINTENANCE = "SYS_MAINTENANCE"
    SYS_RESOURCE_EXHAUSTED = "SYS_RESOURCE_EXHAUSTED"
    SYS_DEPENDENCY_FAILURE = "SYS_DEPENDENCY_FAILURE"
    
    # Network errors (900-999)
    NET_CONNECTION_ERROR = "NET_CONNECTION_ERROR"
    NET_TIMEOUT = "NET_TIMEOUT"
    NET_REQUEST_FAILED = "NET_REQUEST_FAILED"
    
    # Unknown errors (1000+)
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ErrorDetail(BaseModel):
    """Detailed error information"""
    code: ErrorCode
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    details: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    retryable: bool = False
    
    class Config:
        use_enum_values = True


class ErrorResponse(BaseModel):
    """API error response model"""
    status: str = "error"
    error: ErrorDetail
    
    class Config:
        use_enum_values = True


# Error code to user-friendly message mapping
ERROR_MESSAGES = {
    # Authentication errors
    ErrorCode.AUTH_INVALID_CREDENTIALS: "제공된 인증 정보가 올바르지 않습니다. 사용자 이름과 비밀번호를 확인해주세요.",
    ErrorCode.AUTH_EXPIRED_TOKEN: "인증 토큰이 만료되었습니다. 다시 로그인해주세요.",
    ErrorCode.AUTH_INVALID_TOKEN: "유효하지 않은 인증 토큰입니다. 다시 로그인해주세요.",
    ErrorCode.AUTH_MISSING_TOKEN: "인증 토큰이 필요합니다. 로그인 후 다시 시도해주세요.",
    ErrorCode.AUTH_SESSION_EXPIRED: "세션이 만료되었습니다. 다시 로그인해주세요.",
    ErrorCode.AUTH_ACCOUNT_LOCKED: "계정이 잠겼습니다. 관리자에게 문의하세요.",
    
    # Authorization errors
    ErrorCode.AUTHZ_INSUFFICIENT_PERMISSIONS: "이 작업을 수행할 권한이 없습니다.",
    ErrorCode.AUTHZ_RESOURCE_FORBIDDEN: "요청한 리소스에 접근할 권한이 없습니다.",
    ErrorCode.AUTHZ_DB_ACCESS_DENIED: "이 데이터베이스에 접근할 권한이 없습니다.",
    ErrorCode.AUTHZ_TABLE_ACCESS_DENIED: "이 테이블에 접근할 권한이 없습니다.",
    
    # Database errors
    ErrorCode.DB_CONNECTION_FAILED: "데이터베이스 연결에 실패했습니다. 연결 정보를 확인하거나 나중에 다시 시도해주세요.",
    ErrorCode.DB_QUERY_FAILED: "쿼리 실행 중 오류가 발생했습니다. SQL 문법을 확인해주세요.",
    ErrorCode.DB_SCHEMA_ERROR: "데이터베이스 스키마 오류가 발생했습니다.",
    ErrorCode.DB_TIMEOUT: "데이터베이스 쿼리 시간이 초과되었습니다. 쿼리를 최적화하거나 나중에 다시 시도해주세요.",
    ErrorCode.DB_UNSUPPORTED_TYPE: "지원되지 않는 데이터베이스 유형입니다.",
    ErrorCode.DB_RESOURCE_LIMIT: "데이터베이스 리소스 한도에 도달했습니다.",
    ErrorCode.DB_DATA_INTEGRITY: "데이터 무결성 오류가 발생했습니다.",
    
    # Validation errors
    ErrorCode.VAL_INVALID_INPUT: "입력값이 유효하지 않습니다.",
    ErrorCode.VAL_MISSING_REQUIRED: "필수 입력값이 누락되었습니다.",
    ErrorCode.VAL_TYPE_MISMATCH: "입력값 유형이 일치하지 않습니다.",
    ErrorCode.VAL_CONSTRAINT_VIOLATION: "입력값이 제약 조건을 위반했습니다.",
    ErrorCode.VAL_INVALID_FORMAT: "입력값 형식이 올바르지 않습니다.",
    
    # Business logic errors
    ErrorCode.BIZ_INVALID_OPERATION: "유효하지 않은 작업입니다.",
    ErrorCode.BIZ_RESOURCE_NOT_FOUND: "요청한 리소스를 찾을 수 없습니다.",
    ErrorCode.BIZ_DUPLICATE_RESOURCE: "이미 존재하는 리소스입니다.",
    ErrorCode.BIZ_RESOURCE_CONFLICT: "리소스 충돌이 발생했습니다.",
    ErrorCode.BIZ_OPERATION_TIMEOUT: "작업 시간이 초과되었습니다.",
    ErrorCode.BIZ_QUOTA_EXCEEDED: "할당량을 초과했습니다.",
    
    # External service errors
    ErrorCode.EXT_SERVICE_UNAVAILABLE: "외부 서비스를 사용할 수 없습니다. 나중에 다시 시도해주세요.",
    ErrorCode.EXT_SERVICE_TIMEOUT: "외부 서비스 응답 시간이 초과되었습니다.",
    ErrorCode.EXT_SERVICE_ERROR: "외부 서비스에서 오류가 발생했습니다.",
    ErrorCode.EXT_SERVICE_INVALID_RESPONSE: "외부 서비스에서 유효하지 않은 응답을 받았습니다.",
    
    # LLM service errors
    ErrorCode.LLM_API_ERROR: "LLM API 호출 중 오류가 발생했습니다.",
    ErrorCode.LLM_QUOTA_EXCEEDED: "LLM API 할당량을 초과했습니다.",
    ErrorCode.LLM_TIMEOUT: "LLM API 응답 시간이 초과되었습니다.",
    ErrorCode.LLM_INVALID_RESPONSE: "LLM에서 유효하지 않은 응답을 받았습니다.",
    ErrorCode.LLM_CONTENT_FILTER: "LLM 콘텐츠 필터에 의해 요청이 차단되었습니다.",
    ErrorCode.LLM_SQL_GENERATION_FAILED: "자연어에서 SQL 생성에 실패했습니다. 질의를 더 명확하게 작성해주세요.",
    
    # System errors
    ErrorCode.SYS_INTERNAL_ERROR: "내부 시스템 오류가 발생했습니다. 관리자에게 문의하세요.",
    ErrorCode.SYS_NOT_IMPLEMENTED: "아직 구현되지 않은 기능입니다.",
    ErrorCode.SYS_MAINTENANCE: "시스템이 현재 유지보수 중입니다. 나중에 다시 시도해주세요.",
    ErrorCode.SYS_RESOURCE_EXHAUSTED: "시스템 리소스가 부족합니다. 나중에 다시 시도해주세요.",
    ErrorCode.SYS_DEPENDENCY_FAILURE: "시스템 의존성 오류가 발생했습니다.",
    
    # Network errors
    ErrorCode.NET_CONNECTION_ERROR: "네트워크 연결 오류가 발생했습니다.",
    ErrorCode.NET_TIMEOUT: "네트워크 요청 시간이 초과되었습니다.",
    ErrorCode.NET_REQUEST_FAILED: "네트워크 요청이 실패했습니다.",
    
    # Unknown errors
    ErrorCode.UNKNOWN_ERROR: "알 수 없는 오류가 발생했습니다. 관리자에게 문의하세요.",
}


# Error code to category mapping
ERROR_CATEGORIES = {
    # Authentication errors
    ErrorCode.AUTH_INVALID_CREDENTIALS: ErrorCategory.AUTHENTICATION,
    ErrorCode.AUTH_EXPIRED_TOKEN: ErrorCategory.AUTHENTICATION,
    ErrorCode.AUTH_INVALID_TOKEN: ErrorCategory.AUTHENTICATION,
    ErrorCode.AUTH_MISSING_TOKEN: ErrorCategory.AUTHENTICATION,
    ErrorCode.AUTH_SESSION_EXPIRED: ErrorCategory.AUTHENTICATION,
    ErrorCode.AUTH_ACCOUNT_LOCKED: ErrorCategory.AUTHENTICATION,
    
    # Authorization errors
    ErrorCode.AUTHZ_INSUFFICIENT_PERMISSIONS: ErrorCategory.AUTHORIZATION,
    ErrorCode.AUTHZ_RESOURCE_FORBIDDEN: ErrorCategory.AUTHORIZATION,
    ErrorCode.AUTHZ_DB_ACCESS_DENIED: ErrorCategory.AUTHORIZATION,
    ErrorCode.AUTHZ_TABLE_ACCESS_DENIED: ErrorCategory.AUTHORIZATION,
    
    # Database errors
    ErrorCode.DB_CONNECTION_FAILED: ErrorCategory.DATABASE,
    ErrorCode.DB_QUERY_FAILED: ErrorCategory.DATABASE,
    ErrorCode.DB_SCHEMA_ERROR: ErrorCategory.DATABASE,
    ErrorCode.DB_TIMEOUT: ErrorCategory.DATABASE,
    ErrorCode.DB_UNSUPPORTED_TYPE: ErrorCategory.DATABASE,
    ErrorCode.DB_RESOURCE_LIMIT: ErrorCategory.DATABASE,
    ErrorCode.DB_DATA_INTEGRITY: ErrorCategory.DATABASE,
    
    # Validation errors
    ErrorCode.VAL_INVALID_INPUT: ErrorCategory.VALIDATION,
    ErrorCode.VAL_MISSING_REQUIRED: ErrorCategory.VALIDATION,
    ErrorCode.VAL_TYPE_MISMATCH: ErrorCategory.VALIDATION,
    ErrorCode.VAL_CONSTRAINT_VIOLATION: ErrorCategory.VALIDATION,
    ErrorCode.VAL_INVALID_FORMAT: ErrorCategory.VALIDATION,
    
    # Business logic errors
    ErrorCode.BIZ_INVALID_OPERATION: ErrorCategory.BUSINESS_LOGIC,
    ErrorCode.BIZ_RESOURCE_NOT_FOUND: ErrorCategory.BUSINESS_LOGIC,
    ErrorCode.BIZ_DUPLICATE_RESOURCE: ErrorCategory.BUSINESS_LOGIC,
    ErrorCode.BIZ_RESOURCE_CONFLICT: ErrorCategory.BUSINESS_LOGIC,
    ErrorCode.BIZ_OPERATION_TIMEOUT: ErrorCategory.BUSINESS_LOGIC,
    ErrorCode.BIZ_QUOTA_EXCEEDED: ErrorCategory.BUSINESS_LOGIC,
    
    # External service errors
    ErrorCode.EXT_SERVICE_UNAVAILABLE: ErrorCategory.EXTERNAL_SERVICE,
    ErrorCode.EXT_SERVICE_TIMEOUT: ErrorCategory.EXTERNAL_SERVICE,
    ErrorCode.EXT_SERVICE_ERROR: ErrorCategory.EXTERNAL_SERVICE,
    ErrorCode.EXT_SERVICE_INVALID_RESPONSE: ErrorCategory.EXTERNAL_SERVICE,
    
    # LLM service errors
    ErrorCode.LLM_API_ERROR: ErrorCategory.LLM,
    ErrorCode.LLM_QUOTA_EXCEEDED: ErrorCategory.LLM,
    ErrorCode.LLM_TIMEOUT: ErrorCategory.LLM,
    ErrorCode.LLM_INVALID_RESPONSE: ErrorCategory.LLM,
    ErrorCode.LLM_CONTENT_FILTER: ErrorCategory.LLM,
    ErrorCode.LLM_SQL_GENERATION_FAILED: ErrorCategory.LLM,
    
    # System errors
    ErrorCode.SYS_INTERNAL_ERROR: ErrorCategory.SYSTEM,
    ErrorCode.SYS_NOT_IMPLEMENTED: ErrorCategory.SYSTEM,
    ErrorCode.SYS_MAINTENANCE: ErrorCategory.SYSTEM,
    ErrorCode.SYS_RESOURCE_EXHAUSTED: ErrorCategory.SYSTEM,
    ErrorCode.SYS_DEPENDENCY_FAILURE: ErrorCategory.SYSTEM,
    
    # Network errors
    ErrorCode.NET_CONNECTION_ERROR: ErrorCategory.NETWORK,
    ErrorCode.NET_TIMEOUT: ErrorCategory.NETWORK,
    ErrorCode.NET_REQUEST_FAILED: ErrorCategory.NETWORK,
    
    # Unknown errors
    ErrorCode.UNKNOWN_ERROR: ErrorCategory.UNKNOWN,
}


# Error code to severity mapping
ERROR_SEVERITIES = {
    # Authentication errors
    ErrorCode.AUTH_INVALID_CREDENTIALS: ErrorSeverity.WARNING,
    ErrorCode.AUTH_EXPIRED_TOKEN: ErrorSeverity.INFO,
    ErrorCode.AUTH_INVALID_TOKEN: ErrorSeverity.WARNING,
    ErrorCode.AUTH_MISSING_TOKEN: ErrorSeverity.INFO,
    ErrorCode.AUTH_SESSION_EXPIRED: ErrorSeverity.INFO,
    ErrorCode.AUTH_ACCOUNT_LOCKED: ErrorSeverity.ERROR,
    
    # Authorization errors
    ErrorCode.AUTHZ_INSUFFICIENT_PERMISSIONS: ErrorSeverity.WARNING,
    ErrorCode.AUTHZ_RESOURCE_FORBIDDEN: ErrorSeverity.WARNING,
    ErrorCode.AUTHZ_DB_ACCESS_DENIED: ErrorSeverity.WARNING,
    ErrorCode.AUTHZ_TABLE_ACCESS_DENIED: ErrorSeverity.WARNING,
    
    # Database errors
    ErrorCode.DB_CONNECTION_FAILED: ErrorSeverity.ERROR,
    ErrorCode.DB_QUERY_FAILED: ErrorSeverity.ERROR,
    ErrorCode.DB_SCHEMA_ERROR: ErrorSeverity.ERROR,
    ErrorCode.DB_TIMEOUT: ErrorSeverity.ERROR,
    ErrorCode.DB_UNSUPPORTED_TYPE: ErrorSeverity.ERROR,
    ErrorCode.DB_RESOURCE_LIMIT: ErrorSeverity.ERROR,
    ErrorCode.DB_DATA_INTEGRITY: ErrorSeverity.ERROR,
    
    # Validation errors
    ErrorCode.VAL_INVALID_INPUT: ErrorSeverity.WARNING,
    ErrorCode.VAL_MISSING_REQUIRED: ErrorSeverity.WARNING,
    ErrorCode.VAL_TYPE_MISMATCH: ErrorSeverity.WARNING,
    ErrorCode.VAL_CONSTRAINT_VIOLATION: ErrorSeverity.WARNING,
    ErrorCode.VAL_INVALID_FORMAT: ErrorSeverity.WARNING,
    
    # Business logic errors
    ErrorCode.BIZ_INVALID_OPERATION: ErrorSeverity.WARNING,
    ErrorCode.BIZ_RESOURCE_NOT_FOUND: ErrorSeverity.WARNING,
    ErrorCode.BIZ_DUPLICATE_RESOURCE: ErrorSeverity.WARNING,
    ErrorCode.BIZ_RESOURCE_CONFLICT: ErrorSeverity.WARNING,
    ErrorCode.BIZ_OPERATION_TIMEOUT: ErrorSeverity.WARNING,
    ErrorCode.BIZ_QUOTA_EXCEEDED: ErrorSeverity.WARNING,
    
    # External service errors
    ErrorCode.EXT_SERVICE_UNAVAILABLE: ErrorSeverity.ERROR,
    ErrorCode.EXT_SERVICE_TIMEOUT: ErrorSeverity.ERROR,
    ErrorCode.EXT_SERVICE_ERROR: ErrorSeverity.ERROR,
    ErrorCode.EXT_SERVICE_INVALID_RESPONSE: ErrorSeverity.ERROR,
    
    # LLM service errors
    ErrorCode.LLM_API_ERROR: ErrorSeverity.ERROR,
    ErrorCode.LLM_QUOTA_EXCEEDED: ErrorSeverity.ERROR,
    ErrorCode.LLM_TIMEOUT: ErrorSeverity.ERROR,
    ErrorCode.LLM_INVALID_RESPONSE: ErrorSeverity.ERROR,
    ErrorCode.LLM_CONTENT_FILTER: ErrorSeverity.WARNING,
    ErrorCode.LLM_SQL_GENERATION_FAILED: ErrorSeverity.ERROR,
    
    # System errors
    ErrorCode.SYS_INTERNAL_ERROR: ErrorSeverity.CRITICAL,
    ErrorCode.SYS_NOT_IMPLEMENTED: ErrorSeverity.WARNING,
    ErrorCode.SYS_MAINTENANCE: ErrorSeverity.INFO,
    ErrorCode.SYS_RESOURCE_EXHAUSTED: ErrorSeverity.CRITICAL,
    ErrorCode.SYS_DEPENDENCY_FAILURE: ErrorSeverity.CRITICAL,
    
    # Network errors
    ErrorCode.NET_CONNECTION_ERROR: ErrorSeverity.ERROR,
    ErrorCode.NET_TIMEOUT: ErrorSeverity.ERROR,
    ErrorCode.NET_REQUEST_FAILED: ErrorSeverity.ERROR,
    
    # Unknown errors
    ErrorCode.UNKNOWN_ERROR: ErrorSeverity.ERROR,
}


# Error code to retryable flag mapping
ERROR_RETRYABLE = {
    # Authentication errors
    ErrorCode.AUTH_INVALID_CREDENTIALS: False,
    ErrorCode.AUTH_EXPIRED_TOKEN: True,
    ErrorCode.AUTH_INVALID_TOKEN: False,
    ErrorCode.AUTH_MISSING_TOKEN: False,
    ErrorCode.AUTH_SESSION_EXPIRED: True,
    ErrorCode.AUTH_ACCOUNT_LOCKED: False,
    
    # Authorization errors
    ErrorCode.AUTHZ_INSUFFICIENT_PERMISSIONS: False,
    ErrorCode.AUTHZ_RESOURCE_FORBIDDEN: False,
    ErrorCode.AUTHZ_DB_ACCESS_DENIED: False,
    ErrorCode.AUTHZ_TABLE_ACCESS_DENIED: False,
    
    # Database errors
    ErrorCode.DB_CONNECTION_FAILED: True,
    ErrorCode.DB_QUERY_FAILED: False,
    ErrorCode.DB_SCHEMA_ERROR: False,
    ErrorCode.DB_TIMEOUT: True,
    ErrorCode.DB_UNSUPPORTED_TYPE: False,
    ErrorCode.DB_RESOURCE_LIMIT: True,
    ErrorCode.DB_DATA_INTEGRITY: False,
    
    # Validation errors
    ErrorCode.VAL_INVALID_INPUT: False,
    ErrorCode.VAL_MISSING_REQUIRED: False,
    ErrorCode.VAL_TYPE_MISMATCH: False,
    ErrorCode.VAL_CONSTRAINT_VIOLATION: False,
    ErrorCode.VAL_INVALID_FORMAT: False,
    
    # Business logic errors
    ErrorCode.BIZ_INVALID_OPERATION: False,
    ErrorCode.BIZ_RESOURCE_NOT_FOUND: False,
    ErrorCode.BIZ_DUPLICATE_RESOURCE: False,
    ErrorCode.BIZ_RESOURCE_CONFLICT: True,
    ErrorCode.BIZ_OPERATION_TIMEOUT: True,
    ErrorCode.BIZ_QUOTA_EXCEEDED: False,
    
    # External service errors
    ErrorCode.EXT_SERVICE_UNAVAILABLE: True,
    ErrorCode.EXT_SERVICE_TIMEOUT: True,
    ErrorCode.EXT_SERVICE_ERROR: True,
    ErrorCode.EXT_SERVICE_INVALID_RESPONSE: False,
    
    # LLM service errors
    ErrorCode.LLM_API_ERROR: True,
    ErrorCode.LLM_QUOTA_EXCEEDED: False,
    ErrorCode.LLM_TIMEOUT: True,
    ErrorCode.LLM_INVALID_RESPONSE: False,
    ErrorCode.LLM_CONTENT_FILTER: False,
    ErrorCode.LLM_SQL_GENERATION_FAILED: False,
    
    # System errors
    ErrorCode.SYS_INTERNAL_ERROR: False,
    ErrorCode.SYS_NOT_IMPLEMENTED: False,
    ErrorCode.SYS_MAINTENANCE: True,
    ErrorCode.SYS_RESOURCE_EXHAUSTED: True,
    ErrorCode.SYS_DEPENDENCY_FAILURE: True,
    
    # Network errors
    ErrorCode.NET_CONNECTION_ERROR: True,
    ErrorCode.NET_TIMEOUT: True,
    ErrorCode.NET_REQUEST_FAILED: True,
    
    # Unknown errors
    ErrorCode.UNKNOWN_ERROR: False,
}


# Error code to suggestion mapping
ERROR_SUGGESTIONS = {
    # Authentication errors
    ErrorCode.AUTH_INVALID_CREDENTIALS: [
        "사용자 이름과 비밀번호를 다시 확인해주세요.",
        "비밀번호를 잊으셨다면 비밀번호 재설정을 시도해보세요."
    ],
    ErrorCode.AUTH_EXPIRED_TOKEN: [
        "다시 로그인해주세요.",
        "자동 로그인을 설정하면 다음에 더 편리하게 이용할 수 있습니다."
    ],
    ErrorCode.AUTH_INVALID_TOKEN: [
        "다시 로그인해주세요.",
        "브라우저 캐시를 지우고 다시 시도해보세요."
    ],
    ErrorCode.AUTH_MISSING_TOKEN: [
        "로그인 후 다시 시도해주세요."
    ],
    ErrorCode.AUTH_SESSION_EXPIRED: [
        "다시 로그인해주세요.",
        "장시간 활동이 없으면 보안을 위해 자동으로 로그아웃됩니다."
    ],
    ErrorCode.AUTH_ACCOUNT_LOCKED: [
        "관리자에게 문의하여 계정 잠금을 해제해주세요.",
        "일정 시간 후 자동으로 잠금이 해제될 수 있습니다."
    ],
    
    # Database errors
    ErrorCode.DB_CONNECTION_FAILED: [
        "데이터베이스 연결 정보를 확인해주세요.",
        "데이터베이스 서버가 실행 중인지 확인해주세요.",
        "네트워크 연결을 확인해주세요.",
        "방화벽 설정을 확인해주세요."
    ],
    ErrorCode.DB_QUERY_FAILED: [
        "SQL 문법을 확인해주세요.",
        "테이블과 필드 이름이 올바른지 확인해주세요.",
        "쿼리에 사용된 데이터 타입이 올바른지 확인해주세요."
    ],
    ErrorCode.DB_TIMEOUT: [
        "쿼리를 더 간단하게 수정해보세요.",
        "결과를 제한하는 WHERE 절을 추가해보세요.",
        "나중에 서버 부하가 적을 때 다시 시도해보세요."
    ],
    
    # LLM service errors
    ErrorCode.LLM_SQL_GENERATION_FAILED: [
        "질의를 더 명확하고 구체적으로 작성해보세요.",
        "테이블과 필드 이름을 명시적으로 언급해보세요.",
        "복잡한 질의는 여러 단계로 나누어 시도해보세요."
    ],
    
    # System errors
    ErrorCode.SYS_INTERNAL_ERROR: [
        "페이지를 새로고침하고 다시 시도해보세요.",
        "문제가 지속되면 관리자에게 문의해주세요."
    ],
    ErrorCode.SYS_MAINTENANCE: [
        "잠시 후 다시 시도해주세요.",
        "정기 유지보수 일정은 공지사항을 확인해주세요."
    ],
    ErrorCode.SYS_RESOURCE_EXHAUSTED: [
        "요청을 간소화하여 다시 시도해보세요.",
        "나중에 서버 부하가 적을 때 다시 시도해보세요."
    ],
}