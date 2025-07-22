from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class ThemeType(str, Enum):
    LIGHT = "light"
    DARK = "dark"

class DBType(str, Enum):
    MSSQL = "mssql"
    HANA = "hana"

class UserBase(BaseModel):
    """Base user model with common fields"""
    username: str
    email: EmailStr

class UserCreate(UserBase):
    """Model for creating a new user"""
    password: str

class UserLogin(BaseModel):
    """Model for user login credentials"""
    username: str
    password: str

class UserPreferences(BaseModel):
    """User preferences model"""
    default_db: Optional[str] = None
    theme: ThemeType = ThemeType.LIGHT
    results_per_page: int = Field(default=50, ge=10, le=1000)

    class Config:
        use_enum_values = True

class DatabasePermission(BaseModel):
    """Database permission model for a specific database"""
    db_id: str
    db_type: DBType
    allowed_schemas: List[str] = []
    allowed_tables: List[str] = []

    class Config:
        use_enum_values = True

class UserPermissions(BaseModel):
    """User permissions model containing all database permissions"""
    allowed_databases: List[DatabasePermission] = []

class User(UserBase):
    """Complete user model with all fields"""
    id: str
    password_hash: str
    role: UserRole
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    preferences: UserPreferences
    permissions: UserPermissions

    class Config:
        orm_mode = True
        use_enum_values = True

class UserResponse(UserBase):
    """User model for API responses (without sensitive data)"""
    id: str
    role: UserRole
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    preferences: UserPreferences
    permissions: UserPermissions

    class Config:
        orm_mode = True
        use_enum_values = True

class UserUpdate(BaseModel):
    """Model for updating user information"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    preferences: Optional[UserPreferences] = None
    permissions: Optional[UserPermissions] = None

    class Config:
        use_enum_values = True

class TokenData(BaseModel):
    """Model for JWT token data"""
    username: str
    role: UserRole
    exp: datetime

    class Config:
        use_enum_values = True

class Token(BaseModel):
    """Model for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime