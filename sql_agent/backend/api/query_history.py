"""
API endpoints for query history management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from datetime import datetime, date

from ..services.query_history_service import QueryHistoryService
from ..core.auth import get_current_user, get_current_user_id

router = APIRouter(
    prefix="/api/query-history",
    tags=["query-history"],
    responses={401: {"description": "Unauthorized"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Service instance
query_history_service = QueryHistoryService()

# Request and response models
class QueryHistoryUpdate(BaseModel):
    favorite: Optional[bool] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

class QueryHistorySave(BaseModel):
    query_id: str
    favorite: bool = False
    tags: List[str] = []
    notes: Optional[str] = None

class QueryHistoryResponse(BaseModel):
    id: str
    user_id: str
    query_id: str
    favorite: bool
    tags: List[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

class QueryHistoryListResponse(BaseModel):
    items: List[QueryHistoryResponse]
    total: int
    limit: int
    offset: int

@router.post("/save", response_model=QueryHistoryResponse)
async def save_query_to_history(
    history_data: QueryHistorySave,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    쿼리를 이력에 저장
    
    이 엔드포인트는 쿼리를 사용자의 이력에 저장합니다.
    이미 저장된 쿼리인 경우 업데이트합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 쿼리 이력 저장
        result = await query_history_service.save_query_to_history(
            user_id=user_id,
            query_id=history_data.query_id,
            favorite=history_data.favorite,
            tags=history_data.tags,
            notes=history_data.notes
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
            detail=f"Error saving query to history: {str(e)}"
        )

@router.get("/", response_model=QueryHistoryListResponse)
async def get_query_history(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    favorite_only: bool = Query(False),
    tags: Optional[List[str]] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    쿼리 이력 조회
    
    이 엔드포인트는 사용자의 쿼리 이력을 조회합니다.
    다양한 필터를 적용하여 결과를 필터링할 수 있습니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 날짜 필터를 datetime으로 변환
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        # 쿼리 이력 조회
        history_items = await query_history_service.get_query_history(
            user_id=user_id,
            limit=limit,
            offset=offset,
            favorite_only=favorite_only,
            tags=tags,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        # 응답 생성
        response = {
            "items": history_items,
            "total": len(history_items),  # 실제 구현에서는 전체 개수를 별도로 조회해야 함
            "limit": limit,
            "offset": offset
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting query history: {str(e)}"
        )

@router.put("/{history_id}", response_model=QueryHistoryResponse)
async def update_history_item(
    history_id: str,
    update_data: QueryHistoryUpdate,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    쿼리 이력 항목 업데이트
    
    이 엔드포인트는 쿼리 이력 항목을 업데이트합니다.
    즐겨찾기 상태, 태그, 메모를 업데이트할 수 있습니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 쿼리 이력 항목 업데이트
        result = await query_history_service.update_history_item(
            user_id=user_id,
            history_id=history_id,
            favorite=update_data.favorite,
            tags=update_data.tags,
            notes=update_data.notes
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
            detail=f"Error updating history item: {str(e)}"
        )

@router.delete("/{history_id}")
async def delete_history_item(
    history_id: str,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    쿼리 이력 항목 삭제
    
    이 엔드포인트는 쿼리 이력 항목을 삭제합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 쿼리 이력 항목 삭제
        success = await query_history_service.delete_history_item(
            user_id=user_id,
            history_id=history_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"History item with ID {history_id} not found"
            )
        
        return {"message": "History item deleted successfully"}
        
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
            detail=f"Error deleting history item: {str(e)}"
        )

@router.post("/favorite/{history_id}")
async def toggle_favorite(
    history_id: str,
    favorite: bool,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    쿼리 이력 항목 즐겨찾기 토글
    
    이 엔드포인트는 쿼리 이력 항목의 즐겨찾기 상태를 토글합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 즐겨찾기 상태 업데이트
        result = await query_history_service.update_history_item(
            user_id=user_id,
            history_id=history_id,
            favorite=favorite
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
            detail=f"Error toggling favorite: {str(e)}"
        )

@router.post("/tags/{history_id}")
async def update_tags(
    history_id: str,
    tags: List[str],
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    쿼리 이력 항목 태그 업데이트
    
    이 엔드포인트는 쿼리 이력 항목의 태그를 업데이트합니다.
    """
    try:
        # 현재 사용자 ID 가져오기
        user_id = await get_current_user_id(token)
        
        # 태그 업데이트
        result = await query_history_service.update_history_item(
            user_id=user_id,
            history_id=history_id,
            tags=tags
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
            detail=f"Error updating tags: {str(e)}"
        )