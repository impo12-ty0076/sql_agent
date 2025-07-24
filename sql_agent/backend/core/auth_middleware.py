"""
Authentication and permission middleware
"""
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
import jwt
import logging
from typing import Callable, Dict, Any, List

from ..core.config import settings
from ..services.auth import AuthService
from ..db.session import SessionLocal

logger = logging.getLogger(__name__)

# Public paths that don't require authentication
PUBLIC_PATHS = [
    "/",
    "/api/health",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/api/auth/login",
    "/api/auth/register"
]

# Admin-only paths
ADMIN_PATHS = [
    "/api/admin/"
]

class PermissionMiddleware:
    """Middleware for permission checking"""
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if any(path.startswith(public_path) for public_path in PUBLIC_PATHS):
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            if request.method == "OPTIONS":
                return await call_next(request)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "status": "error",
                    "code": "unauthorized",
                    "message": "Authentication required",
                    "details": "Missing or invalid authentication token"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        token = auth_header.split(" ")[1]
        # DB 세션 생성
        db = SessionLocal()
        try:
            user = AuthService.get_user_from_token(db, token)
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "status": "error",
                        "code": "unauthorized",
                        "message": "Authentication required",
                        "details": "Invalid, expired, or inactive session token"
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )
            # 관리자 권한 체크
            if any(path.startswith(admin_path) for admin_path in ADMIN_PATHS):
                if getattr(user, "role", "user") != "admin":
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "status": "error",
                            "code": "forbidden",
                            "message": "Permission denied",
                            "details": "Admin permission required"
                        }
                    )
            # 사용자 정보 저장
            request.state.user = {
                "id": getattr(user, "id", None),
                "username": getattr(user, "username", ""),
                "email": getattr(user, "email", ""),
                "role": getattr(user, "role", "user")
            }
            return await call_next(request)
        finally:
            db.close()