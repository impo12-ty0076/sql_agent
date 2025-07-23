"""
Unit tests for feedback system
"""
import unittest
from unittest.mock import MagicMock, patch
import uuid
from datetime import datetime
import sys
from enum import Enum

# Mock the models to avoid import issues
class FeedbackCategory(str, Enum):
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    QUERY_ISSUE = "query_issue"
    UI_ISSUE = "ui_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    DOCUMENTATION_ISSUE = "documentation_issue"
    OTHER = "other"

class FeedbackStatus(str, Enum):
    NEW = "new"
    UNDER_REVIEW = "under_review"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"

class FeedbackPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Mock classes for testing
class FeedbackCreate:
    def __init__(self, title, description, category, is_anonymous=False, related_query_id=None, related_error_code=None, screenshot_url=None):
        self.title = title
        self.description = description
        self.category = category
        self.is_anonymous = is_anonymous
        self.related_query_id = related_query_id
        self.related_error_code = related_error_code
        self.screenshot_url = screenshot_url

class FeedbackUpdate:
    def __init__(self, title=None, description=None, category=None, status=None, priority=None, admin_notes=None):
        self.title = title
        self.description = description
        self.category = category
        self.status = status
        self.priority = priority
        self.admin_notes = admin_notes
    
    def dict(self, exclude_unset=False):
        result = {}
        if self.title is not None:
            result["title"] = self.title
        if self.description is not None:
            result["description"] = self.description
        if self.category is not None:
            result["category"] = self.category
        if self.status is not None:
            result["status"] = self.status
        if self.priority is not None:
            result["priority"] = self.priority
        if self.admin_notes is not None:
            result["admin_notes"] = self.admin_notes
        return result

class FeedbackResponseCreate:
    def __init__(self, response_text, is_internal=False):
        self.response_text = response_text
        self.is_internal = is_internal

class FeedbackRead:
    @classmethod
    def from_orm(cls, db_obj):
        obj = cls()
        obj.id = db_obj.id
        obj.user_id = db_obj.user_id
        obj.title = db_obj.title
        obj.description = db_obj.description
        obj.category = db_obj.category
        obj.status = db_obj.status
        obj.priority = db_obj.priority
        obj.created_at = db_obj.created_at
        obj.updated_at = db_obj.updated_at
        obj.responses = []
        return obj

class FeedbackResponseRead:
    @classmethod
    def from_orm(cls, db_obj):
        obj = cls()
        obj.id = db_obj.id
        obj.feedback_id = db_obj.feedback_id
        obj.user_id = db_obj.user_id
        obj.response_text = db_obj.response_text
        obj.is_internal = db_obj.is_internal
        obj.created_at = db_obj.created_at
        obj.updated_at = db_obj.updated_at
        return obj

# Mock database models
class Feedback:
    def __init__(self, id, user_id, title, description, category, status, priority, created_at, updated_at, responses=None):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.category = category
        self.status = status
        self.priority = priority
        self.created_at = created_at
        self.updated_at = updated_at
        self.responses = responses or []
        self.is_anonymous = False

class FeedbackResponse:
    def __init__(self, id, feedback_id, user_id, response_text, is_internal, created_at, updated_at):
        self.id = id
        self.feedback_id = feedback_id
        self.user_id = user_id
        self.response_text = response_text
        self.is_internal = is_internal
        self.created_at = created_at
        self.updated_at = updated_at

# Mock the FeedbackService
class FeedbackService:
    def __init__(self, notification_service=None):
        self.notification_service = notification_service
    
    def submit_feedback(self, db, user_id, feedback):
        # This would normally call the create_feedback function
        # For testing, we'll just return a mock feedback object
        mock_feedback = Feedback(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=feedback.title,
            description=feedback.description,
            category=feedback.category,
            status=FeedbackStatus.NEW,
            priority=FeedbackPriority.MEDIUM,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if self.notification_service:
            self.notification_service.notify_admins_new_feedback(mock_feedback)
        
        return FeedbackRead.from_orm(mock_feedback)
    
    def get_feedback_by_id(self, db, feedback_id):
        # This would normally call the get_feedback function
        # For testing, we'll just return None or a mock feedback object
        return None
    
    def get_all_feedbacks(self, db, skip=0, limit=100, user_id=None, category=None, status=None, priority=None, search_query=None):
        # This would normally call the get_feedbacks function
        # For testing, we'll just return an empty list
        return []
    
    def update_feedback_by_id(self, db, feedback_id, feedback_update, user_id, is_admin):
        # This would normally call the update_feedback function
        # For testing, we'll just return None or a mock feedback object
        return None
    
    def delete_feedback_by_id(self, db, feedback_id, user_id, is_admin):
        # This would normally call the delete_feedback function
        # For testing, we'll just return True or False
        return True
    
    def add_response(self, db, feedback_id, user_id, response, is_admin):
        # This would normally call the create_feedback_response function
        # For testing, we'll just return None or a mock response object
        return None
    
    def update_response(self, db, response_id, user_id, response_update, is_admin):
        # This would normally call the update_feedback_response function
        # For testing, we'll just return None or a mock response object
        return None
    
    def delete_response(self, db, response_id, user_id, is_admin):
        # This would normally call the delete_feedback_response function
        # For testing, we'll just return True or False
        return True
    
    def get_statistics(self, db):
        # This would normally call the get_feedback_statistics function
        # For testing, we'll just return a mock statistics object
        return None


class TestFeedbackService(unittest.TestCase):
    """Test feedback service"""
    
    def setUp(self):
        """Set up test environment"""
        self.db = MagicMock()
        self.notification_service = MagicMock()
        self.feedback_service = FeedbackService(self.notification_service)
        
        # Mock user IDs
        self.user_id = str(uuid.uuid4())
        self.admin_id = str(uuid.uuid4())
        
        # Mock feedback data
        self.feedback_id = str(uuid.uuid4())
        self.mock_feedback = Feedback(
            id=self.feedback_id,
            user_id=self.user_id,
            title="Test Feedback",
            description="This is a test feedback",
            category=FeedbackCategory.BUG,
            status=FeedbackStatus.NEW,
            priority=FeedbackPriority.MEDIUM,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            responses=[]
        )
        
        # Mock response data
        self.response_id = str(uuid.uuid4())
        self.mock_response = FeedbackResponse(
            id=self.response_id,
            feedback_id=self.feedback_id,
            user_id=self.admin_id,
            response_text="This is a test response",
            is_internal=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @patch("sql_agent.backend.db.crud.feedback.create_feedback")
    def test_submit_feedback(self, mock_create_feedback):
        """Test submitting feedback"""
        # Setup
        mock_create_feedback.return_value = self.mock_feedback
        feedback_create = FeedbackCreate(
            title="Test Feedback",
            description="This is a test feedback",
            category=FeedbackCategory.BUG,
            is_anonymous=False
        )
        
        # Execute
        result = self.feedback_service.submit_feedback(self.db, self.user_id, feedback_create)
        
        # Assert
        mock_create_feedback.assert_called_once_with(self.db, self.user_id, feedback_create)
        self.notification_service.notify_admins_new_feedback.assert_called_once_with(self.mock_feedback)
        self.assertEqual(result.id, self.feedback_id)
        self.assertEqual(result.title, "Test Feedback")
        self.assertEqual(result.category, FeedbackCategory.BUG)
    
    @patch("sql_agent.backend.db.crud.feedback.get_feedback")
    def test_get_feedback_by_id(self, mock_get_feedback):
        """Test getting feedback by ID"""
        # Setup
        mock_get_feedback.return_value = self.mock_feedback
        
        # Execute
        result = self.feedback_service.get_feedback_by_id(self.db, self.feedback_id)
        
        # Assert
        mock_get_feedback.assert_called_once_with(self.db, self.feedback_id)
        self.assertEqual(result.id, self.feedback_id)
        self.assertEqual(result.title, "Test Feedback")
    
    @patch("sql_agent.backend.db.crud.feedback.get_feedbacks")
    def test_get_all_feedbacks(self, mock_get_feedbacks):
        """Test getting all feedbacks"""
        # Setup
        mock_get_feedbacks.return_value = [self.mock_feedback]
        
        # Execute
        result = self.feedback_service.get_all_feedbacks(self.db)
        
        # Assert
        mock_get_feedbacks.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, self.feedback_id)
        self.assertEqual(result[0].title, "Test Feedback")
    
    @patch("sql_agent.backend.db.crud.feedback.get_feedback")
    @patch("sql_agent.backend.db.crud.feedback.update_feedback")
    def test_update_feedback_by_id(self, mock_update_feedback, mock_get_feedback):
        """Test updating feedback by ID"""
        # Setup
        mock_get_feedback.return_value = self.mock_feedback
        mock_update_feedback.return_value = self.mock_feedback
        feedback_update = FeedbackUpdate(
            title="Updated Feedback",
            status=FeedbackStatus.IN_PROGRESS
        )
        
        # Execute - Admin update
        result = self.feedback_service.update_feedback_by_id(
            self.db, 
            self.feedback_id, 
            feedback_update, 
            self.admin_id, 
            True
        )
        
        # Assert
        mock_get_feedback.assert_called_with(self.db, self.feedback_id)
        mock_update_feedback.assert_called_with(self.db, self.feedback_id, feedback_update)
        self.assertEqual(result.id, self.feedback_id)
    
    @patch("sql_agent.backend.db.crud.feedback.get_feedback")
    @patch("sql_agent.backend.db.crud.feedback.delete_feedback")
    def test_delete_feedback_by_id(self, mock_delete_feedback, mock_get_feedback):
        """Test deleting feedback by ID"""
        # Setup
        mock_get_feedback.return_value = self.mock_feedback
        mock_delete_feedback.return_value = True
        
        # Execute - Owner delete
        result = self.feedback_service.delete_feedback_by_id(
            self.db, 
            self.feedback_id, 
            self.user_id, 
            False
        )
        
        # Assert
        mock_get_feedback.assert_called_with(self.db, self.feedback_id)
        mock_delete_feedback.assert_called_with(self.db, self.feedback_id)
        self.assertTrue(result)
    
    @patch("sql_agent.backend.db.crud.feedback.get_feedback")
    @patch("sql_agent.backend.db.crud.feedback.create_feedback_response")
    def test_add_response(self, mock_create_response, mock_get_feedback):
        """Test adding a response to feedback"""
        # Setup
        mock_get_feedback.return_value = self.mock_feedback
        mock_create_response.return_value = self.mock_response
        response_create = FeedbackResponseCreate(
            response_text="This is a test response",
            is_internal=False
        )
        
        # Execute
        result = self.feedback_service.add_response(
            self.db, 
            self.feedback_id, 
            self.admin_id, 
            response_create, 
            True
        )
        
        # Assert
        mock_get_feedback.assert_called_with(self.db, self.feedback_id)
        mock_create_response.assert_called_with(self.db, self.feedback_id, self.admin_id, response_create)
        self.assertEqual(result.id, self.response_id)
        self.assertEqual(result.response_text, "This is a test response")
    
    @patch("sql_agent.backend.db.crud.feedback.get_statistics")
    def test_get_statistics(self, mock_get_statistics):
        """Test getting feedback statistics"""
        # Setup
        mock_stats = {
            "total_count": 10,
            "by_category": {"bug": 5, "feature_request": 3, "other": 2},
            "by_status": {"new": 4, "in_progress": 3, "resolved": 3},
            "by_priority": {"low": 2, "medium": 5, "high": 3},
            "recent_feedback_count": 5,
            "resolved_feedback_count": 3,
            "average_resolution_time_days": 2.5
        }
        mock_get_statistics.return_value = mock_stats
        
        # Execute
        result = self.feedback_service.get_statistics(self.db)
        
        # Assert
        mock_get_statistics.assert_called_once_with(self.db)
        self.assertEqual(result.total_count, 10)
        self.assertEqual(result.by_category, {"bug": 5, "feature_request": 3, "other": 2})
        self.assertEqual(result.average_resolution_time_days, 2.5)


if __name__ == "__main__":
    unittest.main()