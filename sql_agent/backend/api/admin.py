from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..core.dependencies import get_current_admin_user, get_sync_db
from ..db.models.user import User as UserModel
from ..models.user import UserResponse
from ..models.system import (
    LogLevel, 
    LogCategory, 
    SystemStatsResponse, 
    PaginatedSystemLogs,
    LogFilterParams,
    UserActivityStatsResponse
)
from ..services.system_monitoring_service import SystemMonitoringService

bearer_scheme = HTTPBearer()

router = APIRouter(
    dependencies=[Security(bearer_scheme)]
)

@router.get("/users", response_model=List[Dict[str, Any]])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db)
):
    """
    모든 사용자 목록 조회 (관리자 전용)
    
    - **skip**: 건너뛸 레코드 수
    - **limit**: 반환할 최대 레코드 수
    """
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return [user.to_dict() for user in users]

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db)
):
    """
    시스템 통계 정보 조회 (관리자 전용)
    
    시스템의 현재 상태, 사용자 수, 쿼리 수, 오류 수 등 다양한 통계 정보를 반환합니다.
    """
    return SystemMonitoringService.get_system_stats(db)

@router.get("/logs", response_model=PaginatedSystemLogs)
async def get_system_logs(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(50, ge=1, le=100, description="페이지당 로그 수"),
    level: Optional[LogLevel] = None,
    category: Optional[LogCategory] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[str] = None,
    search_term: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db)
):
    """
    시스템 로그 조회 (관리자 전용)
    
    다양한 필터링 옵션을 사용하여 시스템 로그를 조회합니다.
    
    - **page**: 페이지 번호
    - **page_size**: 페이지당 로그 수
    - **level**: 로그 레벨 필터 (info, warning, error, critical)
    - **category**: 로그 카테고리 필터 (auth, query, system, security, database, llm, python, api)
    - **start_date**: 시작 날짜 필터
    - **end_date**: 종료 날짜 필터
    - **user_id**: 사용자 ID 필터
    - **search_term**: 검색어 (메시지 및 카테고리에서 검색)
    """
    filters = LogFilterParams(
        level=level,
        category=category,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        search_term=search_term
    )
    
    return SystemMonitoringService.get_paginated_logs(
        db=db,
        page=page,
        page_size=page_size,
        filters=filters
    )

@router.get("/user-activity", response_model=UserActivityStatsResponse)
async def get_user_activity(
    days: int = Query(7, ge=1, le=90, description="조회할 일수"),
    limit: int = Query(100, ge=1, le=1000, description="반환할 최대 사용자 수"),
    offset: int = Query(0, ge=0, description="건너뛸 사용자 수"),
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db)
):
    """
    사용자 활동 통계 조회 (관리자 전용)
    
    지정된 기간 동안의 사용자별 활동 통계를 조회합니다.
    
    - **days**: 조회할 일수 (1-90)
    - **limit**: 반환할 최대 사용자 수
    - **offset**: 건너뛸 사용자 수
    """
    return SystemMonitoringService.get_user_activity_stats(
        db=db,
        days=days,
        limit=limit,
        offset=offset
    )

@router.post("/log-event")
async def create_system_log(
    level: LogLevel,
    category: LogCategory,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db)
):
    """
    시스템 로그 이벤트 생성 (관리자 전용)
    
    관리자가 수동으로 시스템 로그 이벤트를 생성합니다.
    
    - **level**: 로그 레벨
    - **category**: 로그 카테고리
    - **message**: 로그 메시지
    - **details**: 추가 세부 정보 (선택 사항)
    """
    SystemMonitoringService.log_system_event(
        db=db,
        level=level,
        category=category,
        message=message,
        user_id=current_user.id,
        details=details
    )
    
    return {"status": "success", "message": "로그 이벤트가 생성되었습니다."}

@router.get("/status")
async def get_system_status(
    current_user: UserResponse = Depends(get_current_admin_user),
    db=Depends(get_sync_db)
):
    # 임시 Mock 데이터
    return {
        "status": "healthy",
        "components": {
            "database": "healthy",
            "api": "healthy",
            "llm": "healthy",
            "storage": "healthy"
        },
        "uptime": 123456,
        "lastChecked": "2024-06-01T12:00:00Z"
    }

@router.get("/usage-stats/{period}")
async def get_usage_stats(
    period: str = Path(..., regex="^(day|week|month)$"),
    current_user: UserResponse = Depends(get_current_admin_user),
    db=Depends(get_sync_db)
):
    # 임시 Mock 데이터
    return {
        "labels": ["2024-06-01", "2024-06-02"],
        "datasets": [
            {"label": "Queries", "data": [10, 20]}
        ]
    }

@router.get("/error-stats/{period}")
async def get_error_stats(
    period: str = Path(..., regex="^(day|week|month)$"),
    current_user: UserResponse = Depends(get_current_admin_user),
    db=Depends(get_sync_db)
):
    # 임시 Mock 데이터
    return {
        "labels": ["2024-06-01", "2024-06-02"],
        "datasets": [
            {"label": "Errors", "data": [1, 2]}
        ]
    }

@router.get("/performance/{period}")
async def get_performance_metrics(
    period: str = Path(..., regex="^(day|week|month)$"),
    current_user: UserResponse = Depends(get_current_admin_user),
    db=Depends(get_sync_db)
):
    # 임시 Mock 데이터
    return {
        "labels": ["2024-06-01", "2024-06-02"],
        "datasets": [
            {"label": "Response Time", "data": [0.5, 0.6]}
        ]
    }