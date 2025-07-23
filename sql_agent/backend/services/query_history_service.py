"""
Service for managing query history
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..db.crud.query_history import (
    create_query_history,
    get_query_history_by_id,
    get_query_history_by_query_id,
    get_query_history_by_user,
    update_query_history,
    delete_query_history
)
from ..utils.logging import log_event, log_error

class QueryHistoryService:
    """
    쿼리 이력 관리 서비스
    """
    
    async def save_query_to_history(
        self, user_id: str, query_id: str, favorite: bool = False, tags: List[str] = None, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        쿼리를 이력에 저장
        
        Args:
            user_id: 사용자 ID
            query_id: 쿼리 ID
            favorite: 즐겨찾기 여부
            tags: 태그 목록
            notes: 추가 메모
            
        Returns:
            저장된 쿼리 이력 정보
        """
        try:
            # 이미 저장된 이력이 있는지 확인
            existing_history = await get_query_history_by_query_id(query_id)
            
            if existing_history:
                # 이미 존재하는 경우 업데이트
                updated_history = await update_query_history(
                    existing_history.id,
                    favorite=favorite if favorite is not None else existing_history.favorite,
                    tags=tags if tags is not None else existing_history.tags,
                    notes=notes if notes is not None else existing_history.notes
                )
                
                log_event("update_query_history", {
                    "user_id": user_id,
                    "query_id": query_id,
                    "history_id": existing_history.id
                })
                
                return updated_history.dict()
            else:
                # 새로 생성
                new_history = await create_query_history(
                    user_id=user_id,
                    query_id=query_id,
                    favorite=favorite,
                    tags=tags,
                    notes=notes
                )
                
                log_event("create_query_history", {
                    "user_id": user_id,
                    "query_id": query_id,
                    "history_id": new_history.id
                })
                
                return new_history.dict()
                
        except Exception as e:
            log_error("save_query_history_error", str(e), {
                "user_id": user_id,
                "query_id": query_id
            })
            raise
    
    async def get_query_history(
        self, user_id: str, limit: int = 100, offset: int = 0, favorite_only: bool = False,
        tags: List[str] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        사용자의 쿼리 이력 조회
        
        Args:
            user_id: 사용자 ID
            limit: 최대 반환 항목 수
            offset: 페이지네이션 오프셋
            favorite_only: 즐겨찾기만 조회 여부
            tags: 태그 필터
            start_date: 시작 날짜 필터
            end_date: 종료 날짜 필터
            
        Returns:
            쿼리 이력 목록
        """
        try:
            history_items = await get_query_history_by_user(
                user_id=user_id,
                limit=limit,
                offset=offset,
                favorite_only=favorite_only,
                tags=tags,
                start_date=start_date,
                end_date=end_date
            )
            
            log_event("get_query_history", {
                "user_id": user_id,
                "count": len(history_items),
                "filters": {
                    "favorite_only": favorite_only,
                    "tags": tags,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            })
            
            return [item.dict() for item in history_items]
            
        except Exception as e:
            log_error("get_query_history_error", str(e), {
                "user_id": user_id
            })
            raise
    
    async def update_history_item(
        self, user_id: str, history_id: str, favorite: Optional[bool] = None,
        tags: Optional[List[str]] = None, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        쿼리 이력 항목 업데이트
        
        Args:
            user_id: 사용자 ID
            history_id: 이력 ID
            favorite: 즐겨찾기 여부
            tags: 태그 목록
            notes: 추가 메모
            
        Returns:
            업데이트된 쿼리 이력 정보
        """
        try:
            # 이력 항목 존재 여부 확인
            history_item = await get_query_history_by_id(history_id)
            
            if not history_item:
                raise ValueError(f"Query history with ID {history_id} not found")
                
            # 사용자 권한 확인
            if history_item.user_id != user_id:
                raise ValueError("You don't have permission to update this history item")
                
            # 업데이트
            updated_item = await update_query_history(
                history_id=history_id,
                favorite=favorite,
                tags=tags,
                notes=notes
            )
            
            log_event("update_history_item", {
                "user_id": user_id,
                "history_id": history_id,
                "updates": {
                    "favorite": favorite,
                    "tags": tags,
                    "notes": notes
                }
            })
            
            return updated_item.dict()
            
        except Exception as e:
            log_error("update_history_item_error", str(e), {
                "user_id": user_id,
                "history_id": history_id
            })
            raise
    
    async def delete_history_item(self, user_id: str, history_id: str) -> bool:
        """
        쿼리 이력 항목 삭제
        
        Args:
            user_id: 사용자 ID
            history_id: 이력 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            # 이력 항목 존재 여부 확인
            history_item = await get_query_history_by_id(history_id)
            
            if not history_item:
                raise ValueError(f"Query history with ID {history_id} not found")
                
            # 사용자 권한 확인
            if history_item.user_id != user_id:
                raise ValueError("You don't have permission to delete this history item")
                
            # 삭제
            success = await delete_query_history(history_id)
            
            log_event("delete_history_item", {
                "user_id": user_id,
                "history_id": history_id,
                "success": success
            })
            
            return success
            
        except Exception as e:
            log_error("delete_history_item_error", str(e), {
                "user_id": user_id,
                "history_id": history_id
            })
            raise