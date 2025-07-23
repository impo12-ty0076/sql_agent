"""
Notification service for sending alerts to users and admins
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..utils.logging import log_event, log_error
from ..db.models.feedback import Feedback, FeedbackResponse
from ..db.crud.user import get_user, get_admin_users

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications to users and admins"""
    
    def __init__(self, db: Session):
        """
        Initialize the notification service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def notify_admins_new_feedback(self, feedback: Feedback) -> bool:
        """
        Notify admins about new feedback
        
        Args:
            feedback: Feedback object
            
        Returns:
            True if notification was sent, False otherwise
        """
        try:
            # Get admin users
            admin_users = get_admin_users(self.db)
            
            if not admin_users:
                logger.warning("No admin users found for notification")
                return False
            
            # In a real implementation, this would send emails, push notifications, etc.
            # For now, we'll just log the event
            admin_emails = [admin.email for admin in admin_users]
            
            log_event("admin_notification_sent", {
                "notification_type": "new_feedback",
                "feedback_id": feedback.id,
                "feedback_title": feedback.title,
                "admin_count": len(admin_users),
                "admin_emails": admin_emails
            })
            
            logger.info(f"Notification sent to {len(admin_users)} admins about new feedback: {feedback.title}")
            
            return True
            
        except Exception as e:
            log_error("admin_notification_failed", str(e), {
                "notification_type": "new_feedback",
                "feedback_id": feedback.id
            })
            return False
    
    def notify_user_feedback_resolved(self, user_id: str, feedback: Feedback) -> bool:
        """
        Notify user that their feedback has been resolved
        
        Args:
            user_id: User ID
            feedback: Feedback object
            
        Returns:
            True if notification was sent, False otherwise
        """
        try:
            # Get user
            user = get_user(self.db, user_id)
            
            if not user:
                logger.warning(f"User {user_id} not found for notification")
                return False
            
            # In a real implementation, this would send emails, push notifications, etc.
            # For now, we'll just log the event
            log_event("user_notification_sent", {
                "notification_type": "feedback_resolved",
                "user_id": user_id,
                "user_email": user.email,
                "feedback_id": feedback.id,
                "feedback_title": feedback.title
            })
            
            logger.info(f"Notification sent to user {user.username} about resolved feedback: {feedback.title}")
            
            return True
            
        except Exception as e:
            log_error("user_notification_failed", str(e), {
                "notification_type": "feedback_resolved",
                "user_id": user_id,
                "feedback_id": feedback.id
            })
            return False
    
    def notify_user_feedback_response(self, user_id: str, feedback: Feedback, response: FeedbackResponse) -> bool:
        """
        Notify user about a new response to their feedback
        
        Args:
            user_id: User ID
            feedback: Feedback object
            response: Response object
            
        Returns:
            True if notification was sent, False otherwise
        """
        try:
            # Get user
            user = get_user(self.db, user_id)
            
            if not user:
                logger.warning(f"User {user_id} not found for notification")
                return False
            
            # Get responder
            responder = get_user(self.db, response.user_id)
            responder_name = responder.username if responder else "Unknown"
            
            # In a real implementation, this would send emails, push notifications, etc.
            # For now, we'll just log the event
            log_event("user_notification_sent", {
                "notification_type": "feedback_response",
                "user_id": user_id,
                "user_email": user.email,
                "feedback_id": feedback.id,
                "feedback_title": feedback.title,
                "response_id": response.id,
                "responder_id": response.user_id,
                "responder_name": responder_name
            })
            
            logger.info(f"Notification sent to user {user.username} about new response to feedback: {feedback.title}")
            
            return True
            
        except Exception as e:
            log_error("user_notification_failed", str(e), {
                "notification_type": "feedback_response",
                "user_id": user_id,
                "feedback_id": feedback.id,
                "response_id": response.id
            })
            return False