from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum

class AuthMethod(str, Enum):
    """Authentication methods supported by the system"""
    PASSWORD = "password"
    MFA = "mfa"

class LoginRequest(BaseModel):
    """Model for login request"""
    username: str
    password: str
    remember_me: bool = False

class LoginResponse(BaseModel):
    """Model for login response"""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user_id: str
    username: str
    role: str

class RefreshTokenRequest(BaseModel):
    """Model for refresh token request"""
    refresh_token: str

class LogoutRequest(BaseModel):
    """Model for logout request"""
    token: Optional[str] = None

class SessionInfo(BaseModel):
    """Model for session information"""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True
    last_activity: datetime

class MFASetupResponse(BaseModel):
    """Model for MFA setup response"""
    secret_key: str
    qr_code: str
    recovery_codes: List[str]

class MFAVerifyRequest(BaseModel):
    """Model for MFA verification request"""
    code: str
    remember_device: bool = False

class PasswordResetRequest(BaseModel):
    """Model for password reset request"""
    email: str

class PasswordResetConfirmRequest(BaseModel):
    """Model for password reset confirmation"""
    token: str
    new_password: str

class SecurityAuditLog(BaseModel):
    """Model for security audit logging"""
    id: str
    timestamp: datetime
    user_id: Optional[str] = None
    event_type: str
    ip_address: str
    user_agent: str
    details: dict
    success: bool