"""
Authentication utilities
"""
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from datetime import datetime, timedelta

from ..core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get current user from token
    
    Args:
        token: JWT token
        
    Returns:
        User data
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Extract user ID
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check token expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Return user data
        return {
            "id": user_id,
            "username": payload.get("username", ""),
            "email": payload.get("email", ""),
            "role": payload.get("role", "user")
        }
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """
    Get current user ID from token
    
    Args:
        token: JWT token
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    user = await get_current_user(token)
    return user["id"]

async def get_current_active_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get current active user from token
    
    Args:
        token: JWT token
        
    Returns:
        Active user data
        
    Raises:
        HTTPException: If token is invalid, expired, or user is inactive
    """
    user = await get_current_user(token)
    
    # Check if user is active (you can add more logic here)
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user