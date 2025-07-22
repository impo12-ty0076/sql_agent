from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, Table, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import List, Optional

from ..base_model import BaseModel
from ...models.user import UserRole, ThemeType

# User-Role association table
user_roles = Table(
    'user_roles',
    BaseModel.metadata,
    Column('user_id', UNIQUEIDENTIFIER, ForeignKey('users.id'), primary_key=True),
    Column('role_id', UNIQUEIDENTIFIER, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('assigned_by', UNIQUEIDENTIFIER, ForeignKey('users.id'))
)

class User(BaseModel):
    """User database model"""
    __tablename__ = "users"
    
    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.USER.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    permissions = relationship("UserDatabasePermission", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"

class UserPreference(BaseModel):
    """User preferences database model"""
    __tablename__ = "user_preferences"
    
    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UNIQUEIDENTIFIER, ForeignKey("users.id"), nullable=False, unique=True)
    default_db = Column(String(100), nullable=True)
    theme = Column(String(20), default=ThemeType.LIGHT.value, nullable=False)
    results_per_page = Column(Integer, default=50, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreference for {self.user_id}>"

class UserDatabasePermission(BaseModel):
    """User database permissions model"""
    __tablename__ = "user_database_permissions"
    
    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UNIQUEIDENTIFIER, ForeignKey("users.id"), nullable=False)
    db_id = Column(String(100), nullable=False)
    db_type = Column(String(20), nullable=False)
    allowed_schemas = Column(String(1000), nullable=True)  # Comma-separated list
    allowed_tables = Column(String(1000), nullable=True)   # Comma-separated list
    
    # Relationships
    user = relationship("User", back_populates="permissions")
    
    def __repr__(self):
        return f"<UserDatabasePermission {self.user_id} -> {self.db_id}>"

class UserSession(BaseModel):
    """User session database model"""
    __tablename__ = "user_sessions"
    
    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UNIQUEIDENTIFIER, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession {self.user_id}>"

class Role(BaseModel):
    """Role database model"""
    __tablename__ = "roles"
    
    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    
    # Relationships
    users = relationship("User", secondary=user_roles, backref="roles")
    
    def __repr__(self):
        return f"<Role {self.name}>"