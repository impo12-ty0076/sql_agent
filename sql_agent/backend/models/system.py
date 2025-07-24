"""
Pydantic models for system logs, metrics, and admin dashboard
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    """Log level enum"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(str, Enum):
    """Log category enum"""
    AUTH = "auth"
    QUERY = "query"
    SYSTEM = "system"
    SECURITY = "security"
    DATABASE = "database"
    LLM = "llm"
    PYTHON = "python"
    API = "api"


class SystemLogCreate(BaseModel):
    """Model for creating a system log"""
    level: LogLevel
    category: LogCategory
    message: str
    user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SystemLogResponse(BaseModel):
    """Model for system log response"""
    id: str
    timestamp: datetime
    level: str
    category: str
    message: str
    user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class SystemMetricCreate(BaseModel):
    """Model for creating a system metric"""
    metric_name: str
    metric_value: str
    details: Optional[Dict[str, Any]] = None


class SystemMetricResponse(BaseModel):
    """Model for system metric response"""
    id: str
    timestamp: datetime
    metric_name: str
    metric_value: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class SystemStatsResponse(BaseModel):
    """Model for system stats response"""
    status: str = Field(..., description="System operational status")
    user_count: int = Field(..., description="Total number of users")
    active_users_24h: int = Field(..., description="Number of active users in the last 24 hours")
    query_count_total: int = Field(..., description="Total number of queries executed")
    query_count_24h: int = Field(..., description="Number of queries executed in the last 24 hours")
    avg_query_time_ms: float = Field(..., description="Average query execution time in milliseconds")
    error_count_24h: int = Field(..., description="Number of errors in the last 24 hours")
    active_connections: int = Field(..., description="Current number of active database connections")
    system_uptime_seconds: int = Field(..., description="System uptime in seconds")
    cpu_usage_percent: float = Field(..., description="Current CPU usage percentage")
    memory_usage_percent: float = Field(..., description="Current memory usage percentage")
    storage_usage_percent: float = Field(..., description="Current storage usage percentage")


class LogFilterParams(BaseModel):
    """Model for log filter parameters"""
    level: Optional[LogLevel] = None
    category: Optional[LogCategory] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[str] = None
    search_term: Optional[str] = None


class PaginatedSystemLogs(BaseModel):
    """Model for paginated system logs response"""
    logs: List[SystemLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserActivityStats(BaseModel):
    """Model for user activity statistics"""
    user_id: str
    username: str
    email: str
    query_count: int
    last_active: datetime
    avg_query_time_ms: float
    error_count: int


class UserActivityStatsResponse(BaseModel):
    """Model for user activity statistics response"""
    users: List[UserActivityStats]
    total: int