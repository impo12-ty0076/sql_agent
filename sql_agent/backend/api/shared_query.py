"""
API endpoints for shared query management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import Dict, Any, List, Optional
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from datetime import datetime, date

from ..services.shared_query_service import SharedQueryService
from ..services.query_execution_service import QueryExecutionService
from ..core.auth import get_current_user, get_current_user_id

router = APIRouter(
    prefix="/shared-query",
    tags=["shared-query"],
    responses={401: {"description": "Unauthorized"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Service instances
shared_query_service = SharedQueryService()
query_execution_service = QueryExecutionService()

# Request and response models
class SharedQueryCreate(BaseModel):
    query_id: str
    allowed_users: List[str] = []
    expires_in_days: Optional[int] = 7

class SharedQueryUpdate(BaseModel):
    allowed_users: Optional[List[str]] = None
    expires_in_days: Optional[int] = None

class SharedQueryResponse(BaseModel):
    id: str
    query_id: str
    shared_by: str
    access_token: str
    expires_at: Optional[datetime] = None
    allowed_users: List[str]
    created_at: datetime
    updated_at: datetime

class SharedQueryListResponse(BaseModel):
    items: List[SharedQueryResponse]
    total: int

@router.post("/create", response_model=SharedQueryResponse)
async def create_shared_link(
    shared_data: SharedQueryCreate,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    쿼리 공유 링크 생성
    
    이 엔드포인트는 쿼리에 대한 공유 링크를 생성합니다.
    접근 권한 및 만료 기간을 설정할 수 있습니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 공유 링크 생성
        result = await shared_query_service.create_shared_link(
            user_id=user_id,
            query_id=shared_data.query_id,
            allowed_users=shared_data.allowed_users,
            expires_in_days=shared_data.expires_in_days
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating shared link: {str(e)}"
        )

@router.get("/list", response_model=SharedQueryListResponse)
async def get_user_shared_queries(
    include_expired: bool = Query(False),
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    사용자가 공유한 쿼리 목록 조회
    
    이 엔드포인트는 현재 사용자가 공유한 쿼리 목록을 반환합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 공유 쿼리 목록 조회
        shared_queries = await shared_query_service.get_user_shared_queries(
            user_id=user_id,
            include_expired=include_expired
        )
        
        # 응답 생성
        response = {
            "items": shared_queries,
            "total": len(shared_queries)
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting shared queries: {str(e)}"
        )

@router.get("/{shared_id}", response_model=SharedQueryResponse)
async def get_shared_link(
    shared_id: str = Path(..., description="Shared query ID"),
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    공유 링크 정보 조회
    
    이 엔드포인트는 공유 링크의 상세 정보를 반환합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 공유 링크 정보 조회
        shared_query = await shared_query_service.get_shared_link(shared_id)
        
        # 접근 권한 확인
        if not await shared_query_service.check_access_permission(user_id, shared_query):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this shared query"
            )
        
        return shared_query
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting shared link: {str(e)}"
        )

@router.put("/{shared_id}", response_model=SharedQueryResponse)
async def update_shared_link(
    shared_id: str,
    update_data: SharedQueryUpdate,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    공유 링크 설정 업데이트
    
    이 엔드포인트는 공유 링크의 접근 권한 및 만료 기간을 업데이트합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 공유 링크 업데이트
        result = await shared_query_service.update_shared_link(
            user_id=user_id,
            shared_id=shared_id,
            allowed_users=update_data.allowed_users,
            expires_in_days=update_data.expires_in_days
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating shared link: {str(e)}"
        )

@router.post("/{shared_id}/refresh-token", response_model=SharedQueryResponse)
async def refresh_access_token(
    shared_id: str,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    공유 링크 액세스 토큰 갱신
    
    이 엔드포인트는 공유 링크의 액세스 토큰을 새로 생성합니다.
    기존 토큰은 더 이상 사용할 수 없게 됩니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 액세스 토큰 갱신
        result = await shared_query_service.refresh_access_token(
            user_id=user_id,
            shared_id=shared_id
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refreshing access token: {str(e)}"
        )

@router.delete("/{shared_id}")
async def delete_shared_link(
    shared_id: str,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    공유 링크 삭제
    
    이 엔드포인트는 공유 링크를 삭제합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 공유 링크 삭제
        success = await shared_query_service.delete_shared_link(
            user_id=user_id,
            shared_id=shared_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shared link with ID {shared_id} not found"
            )
        
        return {"message": "Shared link deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting shared link: {str(e)}"
        )

@router.get("/access/{access_token}")
async def access_shared_query(
    access_token: str,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    공유 쿼리 접근
    
    이 엔드포인트는 액세스 토큰을 사용하여 공유된 쿼리에 접근합니다.
    쿼리 정보와 결과를 반환합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 공유 쿼리 정보 조회
        shared_query = await shared_query_service.get_shared_query_by_token(access_token)
        
        # 접근 권한 확인
        if not await shared_query_service.check_access_permission(user_id, shared_query):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this shared query"
            )
        
        # 쿼리 정보 조회
        query_info = await query_execution_service.get_query_by_id(shared_query["query_id"])
        
        # 쿼리 결과 조회
        if query_info.get("result_id"):
            result = await query_execution_service.get_query_result(query_info["result_id"])
            query_info["result"] = result
        
        return {
            "shared_info": shared_query,
            "query": query_info
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accessing shared query: {str(e)}"
        )