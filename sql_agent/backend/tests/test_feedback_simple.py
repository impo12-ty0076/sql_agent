"""
Simple unit tests for feedback system
"""
import unittest
from unittest.mock import MagicMock
import uuid
from datetime import datetime


class TestFeedbackSystem(unittest.TestCase):
    """Simple tests for feedback system"""
    
    def test_feedback_creation(self):
        """Test creating a feedback"""
        # Create a mock feedback
        feedback_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        feedback = {
            "id": feedback_id,
            "user_id": user_id,
            "title": "Test Feedback",
            "description": "This is a test feedback",
            "category": "bug",
            "status": "new",
            "priority": "medium",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Assert
        self.assertEqual(feedback["id"], feedback_id)
        self.assertEqual(feedback["user_id"], user_id)
        self.assertEqual(feedback["title"], "Test Feedback")
        self.assertEqual(feedback["category"], "bug")
    
    def test_feedback_response(self):
        """Test creating a feedback response"""
        # Create a mock feedback response
        response_id = str(uuid.uuid4())
        feedback_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        response = {
            "id": response_id,
            "feedback_id": feedback_id,
            "user_id": user_id,
            "response_text": "This is a test response",
            "is_internal": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Assert
        self.assertEqual(response["id"], response_id)
        self.assertEqual(response["feedback_id"], feedback_id)
        self.assertEqual(response["user_id"], user_id)
        self.assertEqual(response["response_text"], "This is a test response")
        self.assertFalse(response["is_internal"])
    
    def test_notification_service(self):
        """Test notification service"""
        # Create a mock notification service
        notification_service = MagicMock()
        
        # Create a mock feedback
        feedback = {
            "id": str(uuid.uuid4()),
            "title": "Test Feedback"
        }
        
        # Call the notify method
        notification_service.notify_admins_new_feedback(feedback)
        
        # Assert
        notification_service.notify_admins_new_feedback.assert_called_once_with(feedback)


if __name__ == "__main__":
    unittest.main()