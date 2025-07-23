"""
Feedback service for handling user feedback
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..db.crud.feedback import (
    create_feedback,
    get_feedback,
    get_feedbacks,
    update_feedback,
    delete_feedback,
    create_feedback_response,
    get_feedback_response,
    update_feedback_response,
    delete_feedback_response,
    get_feedback_statistics
)
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
from ..utils.logging import log_event, log_error
from ..services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for handling user feedback"""
    
    def __init__(self, notification_service: Optional[NotificationService] = None):
        """
        Initialize the feedback service
        
        Args:
            notification_service: Optional notification service for sending alerts
        """
        self.notification_service = notification_service
    
    def submit_feedback(self, db: Session, user_id: str, feedback: FeedbackCreate) -> FeedbackRead:
        """
        Submit new feedback
        
        Args:
            db: Database session
            user_id: User ID
            feedback: Feedback data
            
        Returns:
            Created feedback
        """
        try:
            # Create feedback in database
            db_feedback = create_feedback(db, user_id, feedback)
            
            # Log the event
            log_event("feedback_submitted", {
                "feedback_id": db_feedback.id,
                "user_id": user_id,
                "category": str(db_feedback.category),
                "title": db_feedback.title
            })
            
            # Send notification to admins if notification service is available
            if self.notification_service:
                self.notification_service.notify_admins_new_feedback(db_feedback)
            
            return FeedbackRead.from_orm(db_feedback)
            
        except Exception as e:
            log_error("feedback_submission_failed", str(e), {
                "user_id": user_id,
                "feedback_title": feedback.title
            })
            raise
    
    def get_feedback_by_id(self, db: Session, feedback_id: str) -> Optional[FeedbackRead]:
        """
        Get feedback by ID
        
        Args:
            db: Database session
            feedback_id: Feedback ID
            
        Returns:
            Feedback if found, None otherwise
        """
        db_feedback = get_feedback(db, feedback_id)
        
        if not db_feedback:
            return None
        
        return FeedbackRead.from_orm(db_feedback)
    
    def get_all_feedbacks(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
        category: Optional[FeedbackCategory] = None,
        status: Optional[FeedbackStatus] = None,
        priority: Optional[FeedbackPriority] = None,
        search_query: Optional[str] = None
    ) -> List[FeedbackSummary]:
        """
        Get all feedbacks with optional filtering
        
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
            List of feedback summaries
        """
        db_feedbacks = get_feedbacks(
            db, 
            skip=skip, 
            limit=limit, 
            user_id=user_id,
            category=category,
            status=status,
            priority=priority,
            search_query=search_query
        )
        
        # Convert to summary models and add response count
        result = []
        for db_feedback in db_feedbacks:
            feedback_summary = FeedbackSummary.from_orm(db_feedback)
            feedback_summary.response_count = len(db_feedback.responses)
            result.append(feedback_summary)
        
        return result
    
    def update_feedback_by_id(
        self, 
        db: Session, 
        feedback_id: str, 
        feedback_update: FeedbackUpdate,
        user_id: str,
        is_admin: bool
    ) -> Optional[FeedbackRead]:
        """
        Update feedback by ID
        
        Args:
            db: Database session
            feedback_id: Feedback ID
            feedback_update: Feedback update data
            user_id: User ID performing the update
            is_admin: Whether the user is an admin
            
        Returns:
            Updated feedback if found and user has permission, None otherwise
        """
        # Get the feedback
        db_feedback = get_feedback(db, feedback_id)
        
        if not db_feedback:
            return None
        
        # Check permissions
        if not is_admin and db_feedback.user_id != user_id:
            log_event("feedback_update_denied", {
                "feedback_id": feedback_id,
                "user_id": user_id,
                "reason": "not_owner_or_admin"
            })
            return None
        
        # Non-admins can only update title, description, and category
        if not is_admin:
            restricted_update = FeedbackUpdate(
                title=feedback_update.title,
                description=feedback_update.description,
                category=feedback_update.category
            )
            feedback_update = restricted_update
        
        # Update the feedback
        updated_feedback = update_feedback(db, feedback_id, feedback_update)
        
        if updated_feedback:
            log_event("feedback_updated", {
                "feedback_id": feedback_id,
                "user_id": user_id,
                "is_admin": is_admin
            })
            
            # If status changed to resolved, notify the feedback submitter
            if (feedback_update.status == FeedbackStatus.RESOLVED and 
                self.notification_service and 
                not db_feedback.is_anonymous):
                self.notification_service.notify_user_feedback_resolved(
                    db_feedback.user_id, 
                    updated_feedback
                )
        
        return FeedbackRead.from_orm(updated_feedback) if updated_feedback else None
    
    def delete_feedback_by_id(
        self, 
        db: Session, 
        feedback_id: str, 
        user_id: str,
        is_admin: bool
    ) -> bool:
        """
        Delete feedback by ID
        
        Args:
            db: Database session
            feedback_id: Feedback ID
            user_id: User ID performing the deletion
            is_admin: Whether the user is an admin
            
        Returns:
            True if deleted, False if not found or user has no permission
        """
        # Get the feedback
        db_feedback = get_feedback(db, feedback_id)
        
        if not db_feedback:
            return False
        
        # Check permissions
        if not is_admin and db_feedback.user_id != user_id:
            log_event("feedback_deletion_denied", {
                "feedback_id": feedback_id,
                "user_id": user_id,
                "reason": "not_owner_or_admin"
            })
            return False
        
        # Delete the feedback
        result = delete_feedback(db, feedback_id)
        
        if result:
            log_event("feedback_deleted", {
                "feedback_id": feedback_id,
                "user_id": user_id,
                "is_admin": is_admin
            })
        
        return result
    
    def add_response(
        self, 
        db: Session, 
        feedback_id: str, 
        user_id: str,
        response: FeedbackResponseCreate,
        is_admin: bool
    ) -> Optional[FeedbackResponseRead]:
        """
        Add a response to feedback
        
        Args:
            db: Database session
            feedback_id: Feedback ID
            user_id: User ID adding the response
            response: Response data
            is_admin: Whether the user is an admin
            
        Returns:
            Created response if successful, None otherwise
        """
        # Get the feedback
        db_feedback = get_feedback(db, feedback_id)
        
        if not db_feedback:
            return None
        
        # Check permissions for internal notes
        if response.is_internal and not is_admin:
            response.is_internal = False  # Force to false for non-admins
        
        # Create the response
        db_response = create_feedback_response(db, feedback_id, user_id, response)
        
        if not db_response:
            return None
        
        log_event("feedback_response_added", {
            "feedback_id": feedback_id,
            "response_id": db_response.id,
            "user_id": user_id,
            "is_internal": response.is_internal
        })
        
        # Notify the feedback submitter if this is an admin response and not internal
        if (is_admin and 
            not response.is_internal and 
            self.notification_service and 
            not db_feedback.is_anonymous and 
            db_feedback.user_id != user_id):
            self.notification_service.notify_user_feedback_response(
                db_feedback.user_id, 
                db_feedback, 
                db_response
            )
        
        return FeedbackResponseRead.from_orm(db_response)
    
    def update_response(
        self, 
        db: Session, 
        response_id: str, 
        user_id: str,
        response_update: FeedbackResponseUpdate,
        is_admin: bool
    ) -> Optional[FeedbackResponseRead]:
        """
        Update a feedback response
        
        Args:
            db: Database session
            response_id: Response ID
            user_id: User ID updating the response
            response_update: Response update data
            is_admin: Whether the user is an admin
            
        Returns:
            Updated response if successful, None otherwise
        """
        # Get the response
        db_response = get_feedback_response(db, response_id)
        
        if not db_response:
            return None
        
        # Check permissions
        if not is_admin and db_response.user_id != user_id:
            log_event("feedback_response_update_denied", {
                "response_id": response_id,
                "user_id": user_id,
                "reason": "not_owner_or_admin"
            })
            return None
        
        # Non-admins can't change internal flag
        if not is_admin:
            response_update.is_internal = None
        
        # Update the response
        updated_response = update_feedback_response(db, response_id, response_update)
        
        if updated_response:
            log_event("feedback_response_updated", {
                "response_id": response_id,
                "user_id": user_id,
                "is_admin": is_admin
            })
        
        return FeedbackResponseRead.from_orm(updated_response) if updated_response else None
    
    def delete_response(
        self, 
        db: Session, 
        response_id: str, 
        user_id: str,
        is_admin: bool
    ) -> bool:
        """
        Delete a feedback response
        
        Args:
            db: Database session
            response_id: Response ID
            user_id: User ID deleting the response
            is_admin: Whether the user is an admin
            
        Returns:
            True if deleted, False if not found or user has no permission
        """
        # Get the response
        db_response = get_feedback_response(db, response_id)
        
        if not db_response:
            return False
        
        # Check permissions
        if not is_admin and db_response.user_id != user_id:
            log_event("feedback_response_deletion_denied", {
                "response_id": response_id,
                "user_id": user_id,
                "reason": "not_owner_or_admin"
            })
            return False
        
        # Delete the response
        result = delete_feedback_response(db, response_id)
        
        if result:
            log_event("feedback_response_deleted", {
                "response_id": response_id,
                "user_id": user_id,
                "is_admin": is_admin
            })
        
        return result
    
    def get_statistics(self, db: Session) -> FeedbackStatistics:
        """
        Get feedback statistics
        
        Args:
            db: Database session
            
        Returns:
            Feedback statistics
        """
        stats_data = get_feedback_statistics(db)
        return FeedbackStatistics(**stats_data)