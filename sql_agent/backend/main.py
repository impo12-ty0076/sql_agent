from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging
import time

# 내부 모듈 임포트
from .api import auth, database, query, result, admin
from .core.config import settings
from .core.middleware import LoggingMiddleware, ErrorHandler
from .core.auth_middleware import PermissionMiddleware
from .db.session import engine, Base

# 로깅 설정
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("main")

# FastAPI 앱 생성
app = FastAPI(
    title="SQL DB LLM Agent API",
    description="자연어로 SQL 데이터베이스에 질의하고 결과를 분석하는 LLM 기반 에이전트 시스템",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# 데이터베이스 테이블 생성 (개발 환경에서만 사용)
if settings.DEBUG:
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 미들웨어 추가
app.middleware("http")(LoggingMiddleware())

# 권한 검증 미들웨어 추가
app.middleware("http")(PermissionMiddleware())

# 예외 핸들러 등록
app.add_exception_handler(RequestValidationError, ErrorHandler.validation_error_handler)
app.add_exception_handler(SQLAlchemyError, ErrorHandler.db_error_handler)
app.add_exception_handler(Exception, ErrorHandler.http_error_handler)

# API 라우터 등록 (모든 라우터는 /api 접두사 사용)
app.include_router(auth.router, prefix="/api", tags=["인증"])
app.include_router(database.router, prefix="/api", tags=["데이터베이스"])
app.include_router(query.router, prefix="/api", tags=["쿼리"])
app.include_router(result.router, prefix="/api", tags=["결과"])
app.include_router(admin.router, prefix="/api/admin", tags=["관리자"])

@app.get("/")
async def root():
    """
    루트 엔드포인트 - API 서버 정보 반환
    """
    return {
        "message": "SQL DB LLM Agent API",
        "version": "0.1.0",
        "docs_url": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    """
    헬스 체크 엔드포인트 - 서버 상태 확인
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": "development" if settings.DEBUG else "production"
    }

# 서버 시작 코드
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "main:app", 
        host=settings.API_HOST, 
        port=settings.API_PORT,
        reload=settings.DEBUG
    )