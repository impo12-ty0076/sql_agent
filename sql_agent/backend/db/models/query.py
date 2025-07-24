"""
Database models for queries, results, and related entities
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, Integer, Text, JSON, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from ..base_model import BaseModel

class QueryDB(BaseModel):
    """Database model for user queries"""
    __tablename__ = "queries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    db_id = Column(String(100), nullable=False)
    natural_language = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=False)
    executed_sql = Column(Text, nullable=True)
    status = Column(String(20), nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    result_id = Column(String(36), ForeignKey("query_results.id"), nullable=True)
    
    # Relationships
    # Commented result relationship due to mapper direction conflict for now
    # result = relationship("QueryResultDB", back_populates="query", foreign_keys=[result_id], uselist=False)
    history = relationship("QueryHistoryDB", back_populates="query", uselist=False)
    shared_queries = relationship("SharedQueryDB", back_populates="query")
    feedbacks = relationship("Feedback", back_populates="query")
    
    def __repr__(self):
        return f"<Query {self.id} - {self.status}>"

class QueryResultDB(BaseModel):
    """Database model for query results"""
    __tablename__ = "query_results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String(36), ForeignKey("queries.id"), nullable=False)
    columns = Column(JSON, nullable=False)  # List of column definitions
    rows = Column(JSON, nullable=False)     # List of rows (each row is a list of values)
    row_count = Column(Integer, nullable=False)
    truncated = Column(Boolean, default=False, nullable=False)
    total_row_count = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=True)
    
    # Relationships
    # from .query import QueryDB  # type: ignore; for forward reference
    # query = relationship("QueryDB", back_populates="result", foreign_keys=[query_id], uselist=False)
    # report = relationship("ReportDB", back_populates="result", uselist=False)
    
    def __repr__(self):
        return f"<QueryResult {self.id} - {self.row_count} rows>"

class ReportDB(BaseModel):
    """Database model for analysis reports"""
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    result_id = Column(String(36), ForeignKey("query_results.id"), nullable=False)
    python_code = Column(Text, nullable=False)
    visualizations = Column(JSON, nullable=False)  # List of visualization objects
    insights = Column(JSON, nullable=False)        # List of insight strings
    
    # Relationships
    # result = relationship("QueryResultDB", back_populates="report")
    
    def __repr__(self):
        return f"<Report {self.id}>"

class QueryHistoryDB(BaseModel):
    """Database model for query history"""
    __tablename__ = "query_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    query_id = Column(String(36), ForeignKey("queries.id"), nullable=False, unique=True)
    favorite = Column(Boolean, default=False, nullable=False)
    tags = Column(JSON, nullable=False)  # List of tag strings
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", backref="query_history")
    query = relationship("QueryDB", back_populates="history")
    
    def __repr__(self):
        return f"<QueryHistory {self.id} - User: {self.user_id}>"

class SharedQueryDB(BaseModel):
    """Database model for shared queries"""
    __tablename__ = "shared_queries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String(36), ForeignKey("queries.id"), nullable=False)
    shared_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    access_token = Column(String(100), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    allowed_users = Column(JSON, nullable=False)  # List of user IDs
    
    # Relationships
    query = relationship("QueryDB", back_populates="shared_queries")
    owner = relationship("User", backref="shared_queries")
    
    def __repr__(self):
        return f"<SharedQuery {self.id} - Query: {self.query_id}>"
    
    def is_expired(self) -> bool:
        """Check if the shared query has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at