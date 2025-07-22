from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Callable, Dict, Any
import logging

from ..db.session import get_db
from ..models.rbac import Permission, ResourceType
from ..services.auth import AuthService

logger = logging.getLogger("auth_middleware")

class PermissionMiddleware:
    """
    권한 검증을 위한 미들웨어 클래스
    """
    
    def __init__(
        self,
        required_permissions: Optional[List[Permission]] = None,
        resource_type: Optional[ResourceType] = None,
        get_resource_id: Optional[Callable[[Request], str]] = None
    ):
        self.required_permissions = required_permissions or []
        self.resource_type = resource_type
        self.get_resource_id = get_resource_id
    
    async def __call__(self, request: Request, call_next):
        # Skip permission check for authentication endpoints
        if request.url.path.startswith("/api/auth"):
            return await call_next(request)
        
        # Skip permission check for health check endpoint
        if request.url.path == "/api/health":
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)
        
        token = auth_header.replace("Bearer ", "")
        
        # Get database session
        db = next(get_db())
        
        # Get user from token
        user = AuthService.get_user_from_token(db, token)
        if not user:
            return await call_next(request)
        
        # Admin users have all permissions
        if user.role == "admin":
            return await call_next(request)
        
        # If no required permissions, continue
        if not self.required_permissions:
            return await call_next(request)
        
        # TODO: Implement permission checking logic
        # For now, just check if the user is active
        if not user.is_active:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "status": "error",
                    "code": "permission_denied",
                    "message": "비활성화된 사용자입니다.",
                }
            )
        
        # Continue with the request
        return await call_next(request)

def permission_required(
    required_permissions: List[Permission],
    resource_type: Optional[ResourceType] = None,
    get_resource_id: Optional[Callable[[Request], str]] = None
):
    """
    특정 권한이 필요한 엔드포인트를 위한 데코레이터
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Get authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="인증 정보가 필요합니다.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token = auth_header.replace("Bearer ", "")
            
            # Get database session
            db = next(get_db())
            
            # Get user from token
            user = AuthService.get_user_from_token(db, token)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="인증 정보가 유효하지 않습니다.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Admin users have all permissions
            if user.role == "admin":
                return await func(request, *args, **kwargs)
            
            # TODO: Implement permission checking logic
            # For now, just check if the user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="비활성화된 사용자입니다."
                )
            
            # Continue with the request
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator