from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..core.dependencies import get_sync_db
from ..models.auth import LoginRequest, LoginResponse
from ..models.user import UserResponse
from ..services.auth import AuthService
from ..core.dependencies import get_current_user, get_current_active_user

router = APIRouter(
    prefix="/auth",
    tags=["인증"],
    responses={401: {"description": "인증되지 않음"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_sync_db)
) -> LoginResponse:
    """
    사용자 로그인 및 액세스 토큰 발급
    
    - **username**: 사용자 이름
    - **password**: 비밀번호
    """
    login_data = LoginRequest(
        username=form_data.username,
        password=form_data.password
    )
    
    # 클라이언트 정보 추출
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # 로그인 처리
    login_response = AuthService.login(
        db, 
        login_data,
        ip_address,
        user_agent
    )
    
    if not login_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 사용자 이름 또는 비밀번호",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return login_response

@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_sync_db)
) -> Dict[str, Any]:
    """
    사용자 로그아웃
    
    현재 세션을 무효화합니다.
    """
    success = AuthService.logout(db, token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="로그아웃 처리 중 오류가 발생했습니다."
        )
    
    return {"message": "성공적으로 로그아웃되었습니다."}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_active_user)
) -> UserResponse:
    """
    현재 인증된 사용자 정보 조회
    
    토큰에서 추출한 현재 사용자의 정보를 반환합니다.
    """
    return current_user