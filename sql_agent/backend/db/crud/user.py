"""
CRUD operations for users
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.user import User
from ...models.user import UserRole


def get_user(db: Session, user_id: str) -> Optional[User]:
    """
    Get user by ID
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get user by username
    
    Args:
        db: Database session
        username: Username
        
    Returns:
        User if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get user by email
    
    Args:
        db: Database session
        email: Email
        
    Returns:
        User if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get users
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of users
    """
    return db.query(User).offset(skip).limit(limit).all()


def get_admin_users(db: Session) -> List[User]:
    """
    Get admin users
    
    Args:
        db: Database session
        
    Returns:
        List of admin users
    """
    return db.query(User).filter(User.role == UserRole.ADMIN.value).all()