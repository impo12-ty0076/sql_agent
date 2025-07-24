from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from ..services.database import DatabaseService
from ..core.auth import get_current_user

router = APIRouter(
    prefix="/db",
    tags=["database"],
    responses={401: {"description": "Unauthorized"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

class ConnectDatabaseRequest(BaseModel):
    """Request model for database connection"""
    db_id: str

class DisconnectDatabaseRequest(BaseModel):
    """Request model for database disconnection"""
    connection_id: str

@router.get("/list")
async def list_databases(current_user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """
    사용자가 접근 가능한 데이터베이스 목록 조회
    
    Returns:
        List of databases the user has access to
    """
    # Get databases accessible by the user
    return await DatabaseService.get_user_databases(current_user["id"])

@router.post("/connect")
async def connect_database(
    request: ConnectDatabaseRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    특정 데이터베이스에 연결
    
    Args:
        request: Database connection request with db_id
        
    Returns:
        Connection status information including connection_id
    """
    # Connect to the database
    return await DatabaseService.connect_database(request.db_id, current_user["id"])

@router.get("/schema")
async def get_database_schema(
    db_id: str = Query(..., description="Database ID to get schema for"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    데이터베이스 스키마 정보 조회
    
    Args:
        db_id: Database ID
        
    Returns:
        Database schema information including tables, columns, and relationships
    """
    # Get the database schema
    return await DatabaseService.get_database_schema(db_id, current_user["id"])

@router.post("/disconnect")
async def disconnect_database(
    request: DisconnectDatabaseRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    데이터베이스 연결 종료
    
    Args:
        request: Database disconnection request with connection_id
        
    Returns:
        Disconnection status information
    """
    # Disconnect from the database
    return await DatabaseService.disconnect_database(request.connection_id, current_user["id"])