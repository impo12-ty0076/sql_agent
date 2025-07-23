"""
CRUD operations for feedback
"""
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

from ..models.feedback import Feedback, FeedbackResponse
from ...models.feedback import (
    FeedbackCreate, 
    FeedbackUpdate, 
    FeedbackResponseCreate, 
    FeedbackResponseUpdate,
    FeedbackCategory,
    FeedbackStatus,
    FeedbackPriority
)


def create_feedback(db: Session, user_id: str, feedback: FeedbackCreate) -> Feedback:
    """
    Create a new feedback
    
    Args:
        db: Database session
        user_id: User ID
        feedback: Feedback data
        
    Returns:
        Created feedback
    """
    db_feedback = Feedback(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=feedback.title,
        description=feedback.description,
        category=feedback.category,
        status=FeedbackStatus.NEW,
        priority=FeedbackPriority.MEDIUM,
        related_query_id=feedback.related_query_id,
        related_error_code=feedback.related_error_code,
        screenshot_url=feedback.screenshot_url,
        is_anonymous=feedback.is_anonymous
    )
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback


def get_feedback(db: Session, feedback_id: str) -> Optional[Feedback]:
    """
    Get feedback by ID
    
    Args:
        db: Database session
        feedback_id: Feedback ID
        
    Returns:
        Feedback if found, None otherwise
    """
    return db.query(Feedback).filter(Feedback.id == feedback_id).first()


def get_feedbacks(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    user_id: Optional[str] = None,
    category: Optional[FeedbackCategory] = None,
    status: Optional[FeedbackStatus] = None,
    priority: Optional[FeedbackPriority] = None,
    search_query: Optional[str] = None
) -> List[Feedback]:
    """
    Get feedbacks with optional filtering
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        user_id: Filter by user ID
        category: Filter by category
        status: Filter by status
        priority: Filter by priority
        search_query: Search in title and description
        
    Returns:
        List of feedbacks
    """
    query = db.query(Feedback)
    
    # Apply filters
    if user_id:
        query = query.filter(Feedback.user_id == user_id)
    
    if category:
        query = query.filter(Feedback.category == category)
    
    if status:
        query = query.filter(Feedback.status == status)
    
    if priority:
        query = query.filter(Feedback.priority == priority)
    
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
            or_(
                Feedback.title.ilike(search),
                Feedback.description.ilike(search)
            )
        )
    
    # Order by created_at (newest first)
    query = query.order_by(desc(Feedback.created_at))
    
    return query.offset(skip).limit(limit).all()


def update_feedback(db: Session, feedback_id: str, feedback_update: FeedbackUpdate) -> Optional[Feedback]:
    """
    Update feedback
    
    Args:
        db: Database session
        feedback_id: Feedback ID
        feedback_update: Feedback update data
        
    Returns:
        Updated feedback if found, None otherwise
    """
    db_feedback = get_feedback(db, feedback_id)
    
    if not db_feedback:
        return None
    
    # Update fields if provided
    update_data = feedback_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_feedback, key, value)
    
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback


def delete_feedback(db: Session, feedback_id: str) -> bool:
    """
    Delete feedback
    
    Args:
        db: Database session
        feedback_id: Feedback ID
        
    Returns:
        True if deleted, False if not found
    """
    db_feedback = get_feedback(db, feedback_id)
    
    if not db_feedback:
        return False
    
    db.delete(db_feedback)
    db.commit()
    
    return True


def create_feedback_response(
    db: Session, 
    feedback_id: str, 
    user_id: str, 
    response: FeedbackResponseCreate
) -> Optional[FeedbackResponse]:
    """
    Create a new feedback response
    
    Args:
        db: Database session
        feedback_id: Feedback ID
        user_id: User ID
        response: Response data
        
    Returns:
        Created response if feedback exists, None otherwise
    """
    db_feedback = get_feedback(db, feedback_id)
    
    if not db_feedback:
        return None
    
    db_response = FeedbackResponse(
        id=str(uuid.uuid4()),
        feedback_id=feedback_id,
        user_id=user_id,
        response_text=response.response_text,
        is_internal=response.is_internal
    )
    
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    
    return db_response


def get_feedback_response(db: Session, response_id: str) -> Optional[FeedbackResponse]:
    """
    Get feedback response by ID
    
    Args:
        db: Database session
        response_id: Response ID
        
    Returns:
        Response if found, None otherwise
    """
    return db.query(FeedbackResponse).filter(FeedbackResponse.id == response_id).first()


def update_feedback_response(
    db: Session, 
    response_id: str, 
    response_update: FeedbackResponseUpdate
) -> Optional[FeedbackResponse]:
    """
    Update feedback response
    
    Args:
        db: Database session
        response_id: Response ID
        response_update: Response update data
        
    Returns:
        Updated response if found, None otherwise
    """
    db_response = get_feedback_response(db, response_id)
    
    if not db_response:
        return None
    
    # Update fields if provided
    update_data = response_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_response, key, value)
    
    db.commit()
    db.refresh(db_response)
    
    return db_response


def delete_feedback_response(db: Session, response_id: str) -> bool:
    """
    Delete feedback response
    
    Args:
        db: Database session
        response_id: Response ID
        
    Returns:
        True if deleted, False if not found
    """
    db_response = get_feedback_response(db, response_id)
    
    if not db_response:
        return False
    
    db.delete(db_response)
    db.commit()
    
    return True


def get_feedback_statistics(db: Session) -> Dict[str, Any]:
    """
    Get feedback statistics
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with feedback statistics
    """
    # Total count
    total_count = db.query(func.count(Feedback.id)).scalar()
    
    # Count by category
    category_counts = db.query(
        Feedback.category, 
        func.count(Feedback.id)
    ).group_by(Feedback.category).all()
    
    by_category = {str(category): count for category, count in category_counts}
    
    # Count by status
    status_counts = db.query(
        Feedback.status, 
        func.count(Feedback.id)
    ).group_by(Feedback.status).all()
    
    by_status = {str(status): count for status, count in status_counts}
    
    # Count by priority
    priority_counts = db.query(
        Feedback.priority, 
        func.count(Feedback.id)
    ).group_by(Feedback.priority).all()
    
    by_priority = {str(priority): count for priority, count in priority_counts}
    
    # Recent feedback count (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_count = db.query(func.count(Feedback.id)).filter(
        Feedback.created_at >= thirty_days_ago
    ).scalar()
    
    # Resolved feedback count
    resolved_count = db.query(func.count(Feedback.id)).filter(
        Feedback.status == FeedbackStatus.RESOLVED
    ).scalar()
    
    # Average resolution time
    avg_resolution_time = None
    if resolved_count > 0:
        # This is a simplified calculation and might need adjustment based on your database
        # It assumes you have a way to track when a feedback was resolved
        # For now, we'll use the updated_at field as an approximation
        resolved_feedbacks = db.query(
            Feedback.created_at,
            Feedback.updated_at
        ).filter(Feedback.status == FeedbackStatus.RESOLVED).all()
        
        total_days = 0
        for created_at, updated_at in resolved_feedbacks:
            resolution_time = updated_at - created_at
            total_days += resolution_time.total_seconds() / (60 * 60 * 24)  # Convert to days
        
        avg_resolution_time = total_days / resolved_count if resolved_count > 0 else None
    
    return {
        "total_count": total_count,
        "by_category": by_category,
        "by_status": by_status,
        "by_priority": by_priority,
        "recent_feedback_count": recent_count,
        "resolved_feedback_count": resolved_count,
        "average_resolution_time_days": avg_resolution_time
    }