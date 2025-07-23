"""
Feedback models
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class FeedbackCategory(str, Enum):
    """Feedback categories"""
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    QUERY_ISSUE = "query_issue"
    UI_ISSUE = "ui_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    DOCUMENTATION_ISSUE = "documentation_issue"
    OTHER = "other"


class FeedbackStatus(str, Enum):
    """Feedback status"""
    NEW = "new"
    UNDER_REVIEW = "under_review"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"


class FeedbackPriority(str, Enum):
    """Feedback priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackBase(BaseModel):
    """Base feedback model"""
    title: str = Field(..., description="Feedback title")
    description: str = Field(..., description="Detailed feedback description")
    category: FeedbackCategory = Field(..., description="Feedback category")
    related_query_id: Optional[str] = Field(None, description="Related query ID if applicable")
    related_error_code: Optional[str] = Field(None, description="Related error code if applicable")
    is_anonymous: bool = Field(False, description="Whether the feedback should be anonymous")


class FeedbackCreate(FeedbackBase):
    """Feedback creation model"""
    screenshot_url: Optional[str] = Field(None, description="URL to screenshot if uploaded")


class FeedbackUpdate(BaseModel):
    """Feedback update model"""
    title: Optional[str] = Field(None, description="Updated feedback title")
    description: Optional[str] = Field(None, description="Updated feedback description")
    category: Optional[FeedbackCategory] = Field(None, description="Updated feedback category")
    status: Optional[FeedbackStatus] = Field(None, description="Updated feedback status")
    priority: Optional[FeedbackPriority] = Field(None, description="Updated feedback priority")
    admin_notes: Optional[str] = Field(None, description="Admin notes on the feedback")


class FeedbackResponseBase(BaseModel):
    """Base feedback response model"""
    response_text: str = Field(..., description="Response text")
    is_internal: bool = Field(False, description="Whether this is an internal note visible only to admins")


class FeedbackResponseCreate(FeedbackResponseBase):
    """Feedback response creation model"""
    pass


class FeedbackResponseUpdate(BaseModel):
    """Feedback response update model"""
    response_text: Optional[str] = Field(None, description="Updated response text")
    is_internal: Optional[bool] = Field(None, description="Updated internal flag")


class FeedbackResponseRead(FeedbackResponseBase):
    """Feedback response read model"""
    id: str = Field(..., description="Response ID")
    feedback_id: str = Field(..., description="Feedback ID")
    user_id: str = Field(..., description="User ID who created the response")
    created_at: datetime = Field(..., description="Response creation timestamp")
    updated_at: datetime = Field(..., description="Response last update timestamp")
    
    class Config:
        orm_mode = True


class FeedbackRead(FeedbackBase):
    """Feedback read model"""
    id: str = Field(..., description="Feedback ID")
    user_id: str = Field(..., description="User ID who submitted the feedback")
    status: FeedbackStatus = Field(..., description="Feedback status")
    priority: FeedbackPriority = Field(..., description="Feedback priority")
    screenshot_url: Optional[str] = Field(None, description="URL to screenshot if uploaded")
    admin_notes: Optional[str] = Field(None, description="Admin notes on the feedback")
    created_at: datetime = Field(..., description="Feedback creation timestamp")
    updated_at: datetime = Field(..., description="Feedback last update timestamp")
    responses: List[FeedbackResponseRead] = Field([], description="Responses to this feedback")
    
    class Config:
        orm_mode = True


class FeedbackSummary(BaseModel):
    """Feedback summary model for listings"""
    id: str = Field(..., description="Feedback ID")
    title: str = Field(..., description="Feedback title")
    category: FeedbackCategory = Field(..., description="Feedback category")
    status: FeedbackStatus = Field(..., description="Feedback status")
    priority: FeedbackPriority = Field(..., description="Feedback priority")
    created_at: datetime = Field(..., description="Feedback creation timestamp")
    response_count: int = Field(0, description="Number of responses")
    
    class Config:
        orm_mode = True


class FeedbackStatistics(BaseModel):
    """Feedback statistics model"""
    total_count: int = Field(..., description="Total number of feedback items")
    by_category: Dict[str, int] = Field(..., description="Feedback count by category")
    by_status: Dict[str, int] = Field(..., description="Feedback count by status")
    by_priority: Dict[str, int] = Field(..., description="Feedback count by priority")
    recent_feedback_count: int = Field(..., description="Number of feedback items in the last 30 days")
    resolved_feedback_count: int = Field(..., description="Number of resolved feedback items")
    average_resolution_time_days: Optional[float] = Field(None, description="Average time to resolve feedback in days")