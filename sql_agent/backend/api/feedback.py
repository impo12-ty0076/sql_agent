"""
Feedback API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from sqlalchemy.orm import Session
from typing import List, Optional

from ..db.session import get_db
from ..models.feedback import (
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackResponseCreate,
    FeedbackResponseUpdate,
    FeedbackRead,
    FeedbackSummary,
    FeedbackResponseRead,
    FeedbackStatistics,
    FeedbackCategory,
    FeedbackStatus,
    FeedbackPriority
)
from ..services.feedback_service import FeedbackService
from ..services.notification_service import NotificationService
from ..core.auth import get_current_user, get_current_active_user
from ..models.user import UserRole, User

router = APIRouter(prefix="/api/feedback", tags=["피드백"])


def get_feedback_service(db: Session = Depends(get_db)) -> FeedbackService:
    """
    Get feedback service instance
    
    Args:
        db: Database session
        
    Returns:
        FeedbackService instance
    """
    notification_service = NotificationService(db)
    return FeedbackService(notification_service)


def is_admin(user: User) -> bool:
    """
    Check if user is an admin
    
    Args:
        user: User object
        
    Returns:
        True if user is an admin, False otherwise
    """
    return user.role == UserRole.ADMIN.value


@router.post("", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    사용자 피드백 제출
    
    사용자가 시스템에 대한 피드백을 제출합니다.
    
    Args:
        feedback: Feedback data
        db: Database session
        current_user: Current authenticated user
        feedback_service: Feedback service
        
    Returns:
        Created feedback
    """
    return feedback_service.submit_feedback(db, current_user.id, feedback)


@router.get("", response_model=List[FeedbackSummary])
async def get_feedbacks(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    category: Optional[FeedbackCategory] = Query(None, description="Filter by category"),
    status: Optional[FeedbackStatus] = Query(None, description="Filter by status"),
    priority: Optional[FeedbackPriority] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    my_feedbacks_only: bool = Query(False, description="Show only my feedbacks"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    피드백 목록 조회
    
    시스템에 제출된 피드백 목록을 조회합니다. 관리자는 모든 피드백을 볼 수 있으며,
    일반 사용자는 자신이 제출한 피드백만 볼 수 있습니다.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        category: Filter by category
        status: Filter by status
        priority: Filter by priority
        search: Search in title and description
        my_feedbacks_only: Show only my feedbacks
        db: Database session
        current_user: Current authenticated user
        feedback_service: Feedback service
        
    Returns:
        List of feedback summaries
    """
    # Determine if we should filter by user ID
    user_id_filter = None
    if my_feedbacks_only or not is_admin(current_user):
        user_id_filter = current_user.id
    
    return feedback_service.get_all_feedbacks(
        db,
        skip=skip,
        limit=limit,
        user_id=user_id_filter,
        category=category,
        status=status,
        priority=priority,
        search_query=search
    )


@router.get("/statistics", response_model=FeedbackStatistics)
async def get_feedback_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    피드백 통계 조회
    
    피드백 관련 통계 정보를 조회합니다. 관리자만 접근 가능합니다.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        feedback_service: Feedback service
        
    Returns:
        Feedback statistics
    """
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access feedback statistics"
        )
    
    return feedback_service.get_statistics(db)


@router.get("/{feedback_id}", response_model=FeedbackRead)
async def get_feedback_by_id(
    feedback_id: str = Path(..., description="Feedback ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    피드백 상세 조회
    
    특정 피드백의 상세 정보를 조회합니다. 관리자는 모든 피드백을 볼 수 있으며,
    일반 사용자는 자신이 제출한 피드백만 볼 수 있습니다.
    
    Args:
        feedback_id: Feedback ID
        db: Database session
        current_user: Current authenticated user
        feedback_service: Feedback service
        
    Returns:
        Feedback details
    """
    feedback = feedback_service.get_feedback_by_id(db, feedback_id)
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    # Check if user has permission to view this feedback
    if not is_admin(current_user) and feedback.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this feedback"
        )
    
    return feedback


@router.put("/{feedback_id}", response_model=FeedbackRead)
async def update_feedback(
    feedback_update: FeedbackUpdate,
    feedback_id: str = Path(..., description="Feedback ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    피드백 수정
    
    특정 피드백을 수정합니다. 관리자는 모든 피드백을 수정할 수 있으며,
    일반 사용자는 자신이 제출한 피드백만 수정할 수 있습니다.
    
    Args:
        feedback_update: Feedback update data
        feedback_id: Feedback ID
        db: Database session
        current_user: Current authenticated user
        feedback_service: Feedback service
        
    Returns:
        Updated feedback
    """
    updated_feedback = feedback_service.update_feedback_by_id(
        db, 
        feedback_id, 
        feedback_update, 
        current_user.id, 
        is_admin(current_user)
    )
    
    if not updated_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found or you don't have permission to update it"
        )
    
    return updated_feedback


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: str = Path(..., description="Feedback ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    피드백 삭제
    
    특정 피드백을 삭제합니다. 관리자는 모든 피드백을 삭제할 수 있으며,
    일반 사용자는 자신이 제출한 피드백만 삭제할 수 있습니다.
    
    Args:
        feedback_id: Feedback ID
        db: Database session
        current_user: Current authenticated user
        feedback_service: Feedback service
        
    Returns:
        No content
    """
    result = feedback_service.delete_feedback_by_id(
        db, 
        feedback_id, 
        current_user.id, 
        is_admin(current_user)
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found or you don't have permission to delete it"
        )


@router.post("/{feedback_id}/responses", response_model=FeedbackResponseRead)
async def add_feedback_response(
    response: FeedbackResponseCreate,
    feedback_id: str = Path(..., description="Feedback ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    피드백 응답 추가
    
    특정 피드백에 응답을 추가합니다. 모든 사용자는 피드백에 응답할 수 있지만,
    내부 노트는 관리자만 작성할 수 있습니다.
    
    Args:
        response: Response data
        feedback_id: Feedback ID
        db: Database session
        current_user: Current authenticated user
        feedback_service: Feedback service
        
    Returns:
        Created response
    """
    created_response = feedback_service.add_response(
        db, 
        feedback_id, 
        current_user.id, 
        response, 
        is_admin(current_user)
    )
    
    if not created_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    return created_response


@router.put("/responses/{response_id}", response_model=FeedbackResponseRead)
async def update_feedback_response(
    response_update: FeedbackResponseUpdate,
    response_id: str = Path(..., description="Response ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    피드백 응답 수정
    
    특정 피드백 응답을 수정합니다. 관리자는 모든 응답을 수정할 수 있으며,
    일반 사용자는 자신이 작성한 응답만 수정할 수 있습니다.
    
    Args:
        response_update: Response update data
        response_id: Response ID
        db: Database session
        current_user: Current authenticated user
        feedback_service: Feedback service
        
    Returns:
        Updated response
    """
    updated_response = feedback_service.update_response(
        db, 
        response_id, 
        current_user.id, 
        response_update, 
        is_admin(current_user)
    )
    
    if not updated_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found or you don't have permission to update it"
        )
    
    return updated_response


@router.delete("/responses/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback_response(
    response_id: str = Path(..., description="Response ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    피드백 응답 삭제
    
    특정 피드백 응답을 삭제합니다. 관리자는 모든 응답을 삭제할 수 있으며,
    일반 사용자는 자신이 작성한 응답만 삭제할 수 있습니다.
    
    Args:
        response_id: Response ID
        db: Database session
        current_user: Current authenticated user
        feedback_service: Feedback service
        
    Returns:
        No content
    """
    result = feedback_service.delete_response(
        db, 
        response_id, 
        current_user.id, 
        is_admin(current_user)
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found or you don't have permission to delete it"
        )