from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from typing import Union, Dict, Any, Optional
import logging
import traceback
import time

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("middleware")

class ErrorHandler:
    """
    전역 오류 처리를 위한 미들웨어 클래스
    """
    
    @staticmethod
    async def http_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        HTTP 예외 처리기
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "code": "internal_server_error",
                "message": "내부 서버 오류가 발생했습니다.",
                "details": str(exc),
            }
        )
    
    @staticmethod
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        요청 검증 오류 처리기
        """
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "code": "validation_error",
                "message": "요청 데이터 검증에 실패했습니다.",
                "details": exc.errors(),
            }
        )
    
    @staticmethod
    async def db_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """
        데이터베이스 오류 처리기
        """
        logger.error(f"Database error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "code": "database_error",
                "message": "데이터베이스 작업 중 오류가 발생했습니다.",
                "details": str(exc),
            }
        )

class LoggingMiddleware:
    """
    요청 로깅을 위한 미들웨어
    """
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # 요청 정보 로깅
        logger.info(f"Request: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            
            # 응답 시간 계산 및 로깅
            process_time = time.time() - start_time
            logger.info(f"Response: {response.status_code} (took {process_time:.4f}s)")
            
            return response
        except Exception as e:
            # 예외 로깅
            logger.error(f"Error processing request: {str(e)}")
            logger.error(traceback.format_exc())
            
            # 예외 처리 후 응답
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "code": "internal_server_error",
                    "message": "요청 처리 중 오류가 발생했습니다.",
                    "details": str(e),
                }
            )