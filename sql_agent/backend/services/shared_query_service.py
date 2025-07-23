"""
Service for managing shared queries
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..db.crud.shared_query import (
    create_shared_query,
    get_shared_query_by_id,
    get_shared_query_by_token,
    get_shared_queries_by_query_id,
    get_shared_queries_by_user,
    update_shared_query,
    refresh_shared_query_token,
    delete_shared_query
)
from ..db.crud.query_history import get_query_history_by_query_id
from ..utils.logging import log_event, log_error

class SharedQueryService:
    """
    쿼리 및 결과 공유 서비스
    """
    
    async def create_shared_link(
        self, user_id: str, query_id: str, allowed_users: List[str] = None, expires_in_days: Optional[int] = 7
    ) -> Dict[str, Any]:
        """
        쿼리 공유 링크 생성
        
        Args:
            user_id: 공유하는 사용자 ID
            query_id: 공유할 쿼리 ID
            allowed_users: 접근 허용할 사용자 ID 목록 (빈 목록이면 모든 인증된 사용자 접근 가능)
            expires_in_days: 만료 기간(일), None이면 만료 없음
            
        Returns:
            생성된 공유 링크 정보
        """
        try:
            # 쿼리 이력 확인 (사용자가 해당 쿼리의 소유자인지 확인)
            history = await get_query_history_by_query_id(query_id)
            
            if not history or history.user_id != user_id:
                raise ValueError("You don't have permission to share this query")
            
            # 공유 링크 생성
            shared_query = await create_shared_query(
                query_id=query_id,
                shared_by=user_id,
                allowed_users=allowed_users or [],
                expires_in_days=expires_in_days
            )
            
            log_event("create_shared_query", {
                "user_id": user_id,
                "query_id": query_id,
                "shared_id": shared_query.id,
                "expires_in_days": expires_in_days
            })
            
            return shared_query.to_dict()
            
        except Exception as e:
            log_error("create_shared_link_error", str(e), {
                "user_id": user_id,
                "query_id": query_id
            })
            raise
    
    async def get_shared_link(self, shared_id: str) -> Dict[str, Any]:
        """
        공유 링크 정보 조회
        
        Args:
            shared_id: 공유 링크 ID
            
        Returns:
            공유 링크 정보
        """
        try:
            shared_query = await get_shared_query_by_id(shared_id)
            
            if not shared_query:
                raise ValueError(f"Shared query with ID {shared_id} not found")
            
            # 만료 여부 확인
            if shared_query.is_expired():
                raise ValueError("This shared link has expired")
            
            log_event("get_shared_link", {
                "shared_id": shared_id,
                "query_id": shared_query.query_id
            })
            
            return shared_query.to_dict()
            
        except Exception as e:
            log_error("get_shared_link_error", str(e), {
                "shared_id": shared_id
            })
            raise
    
    async def get_shared_query_by_token(self, access_token: str) -> Dict[str, Any]:
        """
        액세스 토큰으로 공유 쿼리 조회
        
        Args:
            access_token: 액세스 토큰
            
        Returns:
            공유 쿼리 정보
        """
        try:
            shared_query = await get_shared_query_by_token(access_token)
            
            if not shared_query:
                raise ValueError("Invalid access token")
            
            # 만료 여부 확인
            if shared_query.is_expired():
                raise ValueError("This shared link has expired")
            
            log_event("get_shared_query_by_token", {
                "access_token": access_token[:8] + "...",  # 보안을 위해 토큰 일부만 로깅
                "shared_id": shared_query.id,
                "query_id": shared_query.query_id
            })
            
            return shared_query.to_dict()
            
        except Exception as e:
            log_error("get_shared_query_by_token_error", str(e), {
                "access_token": access_token[:8] + "..." if access_token else None
            })
            raise
    
    async def get_user_shared_queries(self, user_id: str, include_expired: bool = False) -> List[Dict[str, Any]]:
        """
        사용자가 공유한 쿼리 목록 조회
        
        Args:
            user_id: 사용자 ID
            include_expired: 만료된 공유 링크 포함 여부
            
        Returns:
            공유 쿼리 목록
        """
        try:
            shared_queries = await get_shared_queries_by_user(
                user_id=user_id,
                include_expired=include_expired
            )
            
            log_event("get_user_shared_queries", {
                "user_id": user_id,
                "count": len(shared_queries),
                "include_expired": include_expired
            })
            
            return [query.to_dict() for query in shared_queries]
            
        except Exception as e:
            log_error("get_user_shared_queries_error", str(e), {
                "user_id": user_id
            })
            raise
    
    async def update_shared_link(
        self, user_id: str, shared_id: str, allowed_users: Optional[List[str]] = None, expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        공유 링크 설정 업데이트
        
        Args:
            user_id: 사용자 ID (권한 확인용)
            shared_id: 공유 링크 ID
            allowed_users: 접근 허용할 사용자 ID 목록
            expires_in_days: 만료 기간(일), 음수면 만료 없음, None이면 변경 없음
            
        Returns:
            업데이트된 공유 링크 정보
        """
        try:
            # 공유 링크 조회
            shared_query = await get_shared_query_by_id(shared_id)
            
            if not shared_query:
                raise ValueError(f"Shared query with ID {shared_id} not found")
            
            # 권한 확인
            if shared_query.shared_by != user_id:
                raise ValueError("You don't have permission to update this shared link")
            
            # 업데이트
            updated_query = await update_shared_query(
                shared_id=shared_id,
                allowed_users=allowed_users,
                expires_in_days=expires_in_days
            )
            
            log_event("update_shared_link", {
                "user_id": user_id,
                "shared_id": shared_id,
                "updates": {
                    "allowed_users": allowed_users is not None,
                    "expires_in_days": expires_in_days
                }
            })
            
            return updated_query.to_dict()
            
        except Exception as e:
            log_error("update_shared_link_error", str(e), {
                "user_id": user_id,
                "shared_id": shared_id
            })
            raise
    
    async def refresh_access_token(self, user_id: str, shared_id: str) -> Dict[str, Any]:
        """
        공유 링크의 액세스 토큰 갱신
        
        Args:
            user_id: 사용자 ID (권한 확인용)
            shared_id: 공유 링크 ID
            
        Returns:
            새 액세스 토큰이 포함된 공유 링크 정보
        """
        try:
            # 공유 링크 조회
            shared_query = await get_shared_query_by_id(shared_id)
            
            if not shared_query:
                raise ValueError(f"Shared query with ID {shared_id} not found")
            
            # 권한 확인
            if shared_query.shared_by != user_id:
                raise ValueError("You don't have permission to refresh this access token")
            
            # 토큰 갱신
            updated_query = await refresh_shared_query_token(shared_id)
            
            log_event("refresh_access_token", {
                "user_id": user_id,
                "shared_id": shared_id
            })
            
            return updated_query.to_dict()
            
        except Exception as e:
            log_error("refresh_access_token_error", str(e), {
                "user_id": user_id,
                "shared_id": shared_id
            })
            raise
    
    async def delete_shared_link(self, user_id: str, shared_id: str) -> bool:
        """
        공유 링크 삭제
        
        Args:
            user_id: 사용자 ID (권한 확인용)
            shared_id: 공유 링크 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            # 공유 링크 조회
            shared_query = await get_shared_query_by_id(shared_id)
            
            if not shared_query:
                raise ValueError(f"Shared query with ID {shared_id} not found")
            
            # 권한 확인
            if shared_query.shared_by != user_id:
                raise ValueError("You don't have permission to delete this shared link")
            
            # 삭제
            success = await delete_shared_query(shared_id)
            
            log_event("delete_shared_link", {
                "user_id": user_id,
                "shared_id": shared_id,
                "success": success
            })
            
            return success
            
        except Exception as e:
            log_error("delete_shared_link_error", str(e), {
                "user_id": user_id,
                "shared_id": shared_id
            })
            raise
    
    async def check_access_permission(self, user_id: str, shared_query: Dict[str, Any]) -> bool:
        """
        사용자의 공유 쿼리 접근 권한 확인
        
        Args:
            user_id: 접근 시도하는 사용자 ID
            shared_query: 공유 쿼리 정보
            
        Returns:
            접근 허용 여부
        """
        # 만료 여부 확인
        if shared_query.get("expires_at") and datetime.fromisoformat(shared_query["expires_at"]) < datetime.utcnow():
            return False
        
        # 공유한 사용자는 항상 접근 가능
        if shared_query["shared_by"] == user_id:
            return True
        
        # 허용된 사용자 목록이 비어있으면 모든 인증된 사용자 접근 가능
        allowed_users = shared_query.get("allowed_users", [])
        if not allowed_users:
            return True
        
        # 허용된 사용자 목록에 포함되어 있는지 확인
        return user_id in allowed_users