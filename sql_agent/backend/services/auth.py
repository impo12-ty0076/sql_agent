from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext
import uuid

from ..core.config import settings
from ..db.models.user import User, UserSession
from ..models.user import UserRole, UserResponse, TokenData
from ..models.auth import LoginRequest, LoginResponse

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Authentication service for handling user authentication and token management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a new JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm="HS256"
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_user_session(
        db: Session, 
        user: User, 
        token: str, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """Create a new user session"""
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        session = UserSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token=token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
            last_activity=datetime.utcnow()
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    @staticmethod
    def invalidate_session(db: Session, token: str) -> bool:
        """Invalidate a user session"""
        session = db.query(UserSession).filter(UserSession.token == token).first()
        if not session:
            return False
            
        session.is_active = False
        session.expires_at = datetime.utcnow()
        db.commit()
        
        return True
    
    @staticmethod
    def get_user_from_token(db: Session, token: str) -> Optional[User]:
        """Get user from token"""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
            username: str = payload.get("sub")
            
            if username is None:
                return None
                
            # Check if token is in active sessions
            session = db.query(UserSession).filter(
                UserSession.token == token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if not session:
                return None
                
            # Update last activity
            session.last_activity = datetime.utcnow()
            db.commit()
            
            return db.query(User).filter(User.username == username).first()
            
        except jwt.JWTError:
            return None
    
    @staticmethod
    def login(
        db: Session, 
        login_data: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[LoginResponse]:
        """Login a user and create a session"""
        user = AuthService.authenticate_user(
            db, 
            login_data.username, 
            login_data.password
        )
        
        if not user:
            return None
            
        # Update last login time
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create access token
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        token_data = {
            "sub": user.username,
            "role": user.role
        }
        
        access_token = AuthService.create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        # Create session
        AuthService.create_user_session(
            db, 
            user, 
            access_token, 
            ip_address, 
            user_agent
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_at=datetime.utcnow() + access_token_expires,
            user_id=user.id,
            username=user.username,
            role=user.role
        )
    
    @staticmethod
    def logout(db: Session, token: str) -> bool:
        """Logout a user by invalidating their session"""
        return AuthService.invalidate_session(db, token)

def get_current_user(db: Session, token: str) -> Optional[User]:
    """Get current user from token - wrapper function for compatibility"""
    return AuthService.get_user_from_token(db, token)