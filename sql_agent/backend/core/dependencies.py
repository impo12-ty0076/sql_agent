from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional, List

from .config import settings
from ..db.session import get_db
from ..db.models.user import User
from ..models.user import UserResponse
from ..models.rbac import Permission
from ..services.auth import AuthService

# OAuth2 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    JWT 토큰에서 현재 사용자 정보를 추출하는 의존성 함수
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user = AuthService.get_user_from_token(db, token)
    
    if user is None:
        raise credentials_exception
        
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    활성 상태인 사용자만 허용하는 의존성 함수
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다."
        )
    
    # Convert DB model to Pydantic model
    user_response = UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        preferences={
            "default_db": current_user.preferences.default_db if current_user.preferences else None,
            "theme": current_user.preferences.theme if current_user.preferences else "light",
            "results_per_page": current_user.preferences.results_per_page if current_user.preferences else 50
        },
        permissions={
            "allowed_databases": [
                {
                    "db_id": perm.db_id,
                    "db_type": perm.db_type,
                    "allowed_schemas": perm.allowed_schemas.split(",") if perm.allowed_schemas else [],
                    "allowed_tables": perm.allowed_tables.split(",") if perm.allowed_tables else []
                }
                for perm in current_user.permissions
            ]
        }
    )
    
    return user_response

def get_current_admin_user(
    current_user: UserResponse = Depends(get_current_active_user)
) -> UserResponse:
    """
    관리자 권한을 가진 사용자만 허용하는 의존성 함수
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return current_user

def check_permission(required_permissions: List[Permission]):
    """
    특정 권한을 가진 사용자만 허용하는 의존성 함수 생성기
    """
    def permission_checker(
        current_user: UserResponse = Depends(get_current_active_user),
        request: Request = None,
        db: Session = Depends(get_db)
    ) -> UserResponse:
        # Admin users have all permissions
        if current_user.role == "admin":
            return current_user
            
        # TODO: Implement permission checking logic
        # For now, just check if the user is active
        return current_user
        
    return permission_checker