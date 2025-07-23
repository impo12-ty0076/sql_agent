"""
Authentication and permission middleware
"""
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
import jwt
import logging
from typing import Callable, Dict, Any, List

from ..core.config import settings

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
        """
        Check permissions for request
        
        Args:
            request: FastAPI request
            call_next: Next middleware or endpoint
            
        Returns:
            Response
        """
        # Skip permission check for public paths
        path = request.url.path
        if any(path.startswith(public_path) for public_path in PUBLIC_PATHS):
            return await call_next(request)
        
        # Check for authentication token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # Skip permission check for OPTIONS requests (CORS preflight)
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
        
        # Extract token
        token = auth_header.split(" ")[1]
        
        try:
            # Decode token
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check admin permission for admin paths
            if any(path.startswith(admin_path) for admin_path in ADMIN_PATHS):
                role = payload.get("role", "user")
                if role != "admin":
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "status": "error",
                            "code": "forbidden",
                            "message": "Permission denied",
                            "details": "Admin permission required"
                        }
                    )
            
            # Add user info to request state
            request.state.user = {
                "id": payload.get("sub"),
                "username": payload.get("username", ""),
                "email": payload.get("email", ""),
                "role": payload.get("role", "user")
            }
            
            # Continue with request
            return await call_next(request)
            
        except jwt.PyJWTError as e:
            logger.warning(f"Invalid token: {str(e)}")
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "status": "error",
                    "code": "unauthorized",
                    "message": "Authentication required",
                    "details": "Invalid or expired token"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )