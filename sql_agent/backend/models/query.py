from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum


class QueryStatus(str, Enum):
    """Status of a query execution"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VisualizationType(str, Enum):
    """Types of visualizations supported in reports"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    CUSTOM = "custom"


class ResultColumn(BaseModel):
    """Column definition in query results"""
    name: str
    type: str

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Column name cannot be empty")
        return v
    
    @validator('type')
    def validate_type(cls, v):
        if not v or not v.strip():
            raise ValueError("Column type cannot be empty")
        return v


class Query(BaseModel):
    """
    Model representing a user query, including both natural language and SQL forms.
    """
    id: str
    user_id: str
    db_id: str
    natural_language: str
    generated_sql: str
    executed_sql: Optional[str] = None
    status: QueryStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    result_id: Optional[str] = None
    created_at: datetime

    @validator('natural_language', 'generated_sql')
    def validate_query_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Query text cannot be empty")
        return v
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if v and 'start_time' in values and v < values['start_time']:
            raise ValueError("End time cannot be before start time")
        return v

    class Config:
        orm_mode = True
        use_enum_values = True


class QueryCreate(BaseModel):
    """Model for creating a new query"""
    user_id: str
    db_id: str
    natural_language: str
    generated_sql: str
    executed_sql: Optional[str] = None


class QueryUpdate(BaseModel):
    """Model for updating an existing query"""
    executed_sql: Optional[str] = None
    status: Optional[QueryStatus] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    result_id: Optional[str] = None

    class Config:
        use_enum_values = True


class QueryResult(BaseModel):
    """
    Model representing the result of a query execution.
    """
    id: str
    query_id: str
    columns: List[ResultColumn]
    rows: List[List[Any]]
    row_count: int
    truncated: bool = False
    total_row_count: Optional[int] = None
    summary: Optional[str] = None
    report_id: Optional[str] = None
    created_at: datetime

    @validator('columns')
    def validate_columns(cls, v):
        if not v:
            raise ValueError("Result must have at least one column")
        return v
    
    @validator('row_count')
    def validate_row_count(cls, v, values):
        if 'rows' in values and len(values['rows']) != v:
            raise ValueError("Row count must match the number of rows")
        return v

    class Config:
        orm_mode = True


class QueryResultCreate(BaseModel):
    """Model for creating a new query result"""
    query_id: str
    columns: List[ResultColumn]
    rows: List[List[Any]]
    row_count: int
    truncated: bool = False
    total_row_count: Optional[int] = None
    summary: Optional[str] = None


class Visualization(BaseModel):
    """
    Model representing a data visualization in a report.
    """
    id: str
    type: VisualizationType
    title: str
    description: Optional[str] = None
    image_data: str  # Base64 encoded image

    @validator('image_data')
    def validate_image_data(cls, v):
        if not v or not v.strip():
            raise ValueError("Image data cannot be empty")
        # Could add more validation for Base64 format if needed
        return v

    class Config:
        orm_mode = True
        use_enum_values = True


class Report(BaseModel):
    """
    Model representing an analysis report generated from query results.
    """
    id: str
    result_id: str
    python_code: str
    visualizations: List[Visualization] = []
    insights: List[str] = []
    created_at: datetime

    @validator('python_code')
    def validate_python_code(cls, v):
        if not v or not v.strip():
            raise ValueError("Python code cannot be empty")
        return v

    class Config:
        orm_mode = True


class ReportCreate(BaseModel):
    """Model for creating a new report"""
    result_id: str
    python_code: str
    visualizations: List[Visualization] = []
    insights: List[str] = []


class QueryHistory(BaseModel):
    """
    Model representing a saved query in the user's history.
    """
    id: str
    user_id: str
    query_id: str
    favorite: bool = False
    tags: List[str] = []
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class SharedQuery(BaseModel):
    """
    Model representing a query shared with other users.
    """
    id: str
    query_id: str
    shared_by: str
    access_token: str
    expires_at: Optional[datetime] = None
    allowed_users: List[str] = []
    created_at: datetime

    @validator('expires_at')
    def validate_expires_at(cls, v, values):
        if v and 'created_at' in values and v < values['created_at']:
            raise ValueError("Expiration time cannot be before creation time")
        return v

    class Config:
        orm_mode = True