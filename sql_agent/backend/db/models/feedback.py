"""
Feedback database models
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..base_model import Base


class FeedbackCategory(str, enum.Enum):
    """Feedback categories"""
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    QUERY_ISSUE = "query_issue"
    UI_ISSUE = "ui_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    DOCUMENTATION_ISSUE = "documentation_issue"
    OTHER = "other"


class FeedbackStatus(str, enum.Enum):
    """Feedback status"""
    NEW = "new"
    UNDER_REVIEW = "under_review"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"


class FeedbackPriority(str, enum.Enum):
    """Feedback priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Feedback(Base):
    """Feedback model"""
    __tablename__ = "feedbacks"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(FeedbackCategory), nullable=False)
    status = Column(Enum(FeedbackStatus), nullable=False, default=FeedbackStatus.NEW)
    priority = Column(Enum(FeedbackPriority), nullable=False, default=FeedbackPriority.MEDIUM)
    related_query_id = Column(String(36), ForeignKey("queries.id"), nullable=True)
    related_error_code = Column(String(50), nullable=True)
    screenshot_url = Column(String(255), nullable=True)
    is_anonymous = Column(Boolean, default=False)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="feedbacks")
    query = relationship("Query", back_populates="feedbacks")
    responses = relationship("FeedbackResponse", back_populates="feedback", cascade="all, delete-orphan")


class FeedbackResponse(Base):
    """Feedback response model"""
    __tablename__ = "feedback_responses"

    id = Column(String(36), primary_key=True, index=True)
    feedback_id = Column(String(36), ForeignKey("feedbacks.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    response_text = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # True for admin-only notes
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    feedback = relationship("Feedback", back_populates="responses")
    user = relationship("User", back_populates="feedback_responses")