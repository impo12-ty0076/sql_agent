"""
API endpoints for system settings and backup management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import os

from ..core.dependencies import get_current_admin_user
from ..db.session import get_db
from ..models.user import UserResponse
from ..models.system_settings import (
    SystemSettingCreate,
    SystemSettingUpdate,
    SystemSettingResponse,
    DatabaseConnectionCreate,
    DatabaseConnectionUpdate,
    DatabaseConnectionResponse,
    ApiKeyCreate,
    ApiKeyUpdate,
    ApiKeyResponse,
    SystemBackupCreate,
    SystemBackupResponse,
    BackupType,
    SystemRestoreRequest
)
from ..services.system_settings_service import (
    SystemSettingsService,
    DatabaseConnectionService,
    ApiKeyService,
    BackupService
)
from ..services.system_monitoring_service import SystemMonitoringService

router = APIRouter()

# System Settings endpoints

@router.get("/settings", response_model=List[SystemSettingResponse])
async def get_system_settings(
    skip: int = 0,
    limit: int = 100,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    시스템 설정 목록 조회 (관리자 전용)
    
    - **skip**: 건너뛸 레코드 수
    - **limit**: 반환할 최대 레코드 수
    """
    return SystemSettingsService.get_settings(db, skip, limit)


@router.get("/settings/{key}", response_model=SystemSettingResponse)
async def get_system_setting(
    key: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    특정 시스템 설정 조회 (관리자 전용)
    
    - **key**: 설정 키
    """
    setting = SystemSettingsService.get_setting(db, key)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting with key '{key}' not found"
        )
    return setting


@router.post("/settings", response_model=SystemSettingResponse)
async def create_system_setting(
    setting: SystemSettingCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    시스템 설정 생성 (관리자 전용)
    
    - **key**: 설정 키
    - **value**: 설정 값
    - **description**: 설정 설명 (선택 사항)
    """
    return SystemSettingsService.create_setting(db, setting)


@router.put("/settings/{key}", response_model=SystemSettingResponse)
async def update_system_setting(
    key: str,
    setting: SystemSettingUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    시스템 설정 업데이트 (관리자 전용)
    
    - **key**: 설정 키
    - **value**: 새 설정 값
    - **description**: 새 설정 설명 (선택 사항)
    """
    updated_setting = SystemSettingsService.update_setting(db, key, setting)
    if not updated_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting with key '{key}' not found"
        )
    return updated_setting


@router.delete("/settings/{key}")
async def delete_system_setting(
    key: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    시스템 설정 삭제 (관리자 전용)
    
    - **key**: 설정 키
    """
    result = SystemSettingsService.delete_setting(db, key)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting with key '{key}' not found"
        )
    return {"status": "success", "message": f"Setting '{key}' deleted"}


# Database Connection endpoints

@router.get("/connections", response_model=List[DatabaseConnectionResponse])
async def get_database_connections(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    데이터베이스 연결 목록 조회 (관리자 전용)
    
    - **skip**: 건너뛸 레코드 수
    - **limit**: 반환할 최대 레코드 수
    - **active_only**: 활성 연결만 반환할지 여부
    """
    return DatabaseConnectionService.get_connections(db, skip, limit, active_only)


@router.get("/connections/{connection_id}", response_model=DatabaseConnectionResponse)
async def get_database_connection(
    connection_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    특정 데이터베이스 연결 조회 (관리자 전용)
    
    - **connection_id**: 연결 ID
    """
    connection = DatabaseConnectionService.get_connection(db, connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection with ID '{connection_id}' not found"
        )
    return connection


@router.post("/connections", response_model=DatabaseConnectionResponse)
async def create_database_connection(
    connection: DatabaseConnectionCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    데이터베이스 연결 생성 (관리자 전용)
    
    - **name**: 연결 이름
    - **type**: 데이터베이스 유형 (mssql, hana)
    - **host**: 호스트 주소
    - **port**: 포트 번호
    - **username**: 사용자 이름
    - **password**: 비밀번호
    - **database**: 데이터베이스 이름 (선택 사항)
    - **options**: 추가 연결 옵션 (선택 사항)
    - **is_active**: 활성 상태 여부
    """
    return DatabaseConnectionService.create_connection(db, connection)


@router.put("/connections/{connection_id}", response_model=DatabaseConnectionResponse)
async def update_database_connection(
    connection_id: str,
    connection: DatabaseConnectionUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    데이터베이스 연결 업데이트 (관리자 전용)
    
    - **connection_id**: 연결 ID
    - **name**: 새 연결 이름 (선택 사항)
    - **host**: 새 호스트 주소 (선택 사항)
    - **port**: 새 포트 번호 (선택 사항)
    - **username**: 새 사용자 이름 (선택 사항)
    - **password**: 새 비밀번호 (선택 사항)
    - **database**: 새 데이터베이스 이름 (선택 사항)
    - **options**: 새 추가 연결 옵션 (선택 사항)
    - **is_active**: 새 활성 상태 여부 (선택 사항)
    """
    updated_connection = DatabaseConnectionService.update_connection(db, connection_id, connection)
    if not updated_connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection with ID '{connection_id}' not found"
        )
    return updated_connection


@router.delete("/connections/{connection_id}")
async def delete_database_connection(
    connection_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    데이터베이스 연결 삭제 (관리자 전용)
    
    - **connection_id**: 연결 ID
    """
    result = DatabaseConnectionService.delete_connection(db, connection_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection with ID '{connection_id}' not found"
        )
    return {"status": "success", "message": f"Database connection with ID '{connection_id}' deleted"}


@router.post("/connections/{connection_id}/test")
async def test_database_connection(
    connection_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    데이터베이스 연결 테스트 (관리자 전용)
    
    - **connection_id**: 연결 ID
    """
    result = DatabaseConnectionService.test_connection(db, connection_id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    return result


# API Key endpoints

@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def get_api_keys(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    service: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    API 키 목록 조회 (관리자 전용)
    
    - **skip**: 건너뛸 레코드 수
    - **limit**: 반환할 최대 레코드 수
    - **active_only**: 활성 API 키만 반환할지 여부
    - **service**: 서비스별 필터링 (선택 사항)
    """
    return ApiKeyService.get_api_keys(db, skip, limit, active_only, service)


@router.get("/api-keys/{key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    특정 API 키 조회 (관리자 전용)
    
    - **key_id**: API 키 ID
    """
    api_key = ApiKeyService.get_api_key(db, key_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with ID '{key_id}' not found"
        )
    return api_key


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    api_key: ApiKeyCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    API 키 생성 (관리자 전용)
    
    - **name**: API 키 이름
    - **service**: 서비스 유형 (openai, azure_openai, huggingface, other)
    - **key**: API 키 값
    - **is_active**: 활성 상태 여부
    """
    return ApiKeyService.create_api_key(db, api_key)


@router.put("/api-keys/{key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    key_id: str,
    api_key: ApiKeyUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    API 키 업데이트 (관리자 전용)
    
    - **key_id**: API 키 ID
    - **name**: 새 API 키 이름 (선택 사항)
    - **key**: 새 API 키 값 (선택 사항)
    - **is_active**: 새 활성 상태 여부 (선택 사항)
    """
    updated_api_key = ApiKeyService.update_api_key(db, key_id, api_key)
    if not updated_api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with ID '{key_id}' not found"
        )
    return updated_api_key


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    API 키 삭제 (관리자 전용)
    
    - **key_id**: API 키 ID
    """
    result = ApiKeyService.delete_api_key(db, key_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with ID '{key_id}' not found"
        )
    return {"status": "success", "message": f"API key with ID '{key_id}' deleted"}


@router.post("/api-keys/{key_id}/test")
async def test_api_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    API 키 테스트 (관리자 전용)
    
    - **key_id**: API 키 ID
    """
    result = ApiKeyService.test_api_key(db, key_id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    return result


# Backup endpoints

@router.get("/backups", response_model=List[SystemBackupResponse])
async def get_backups(
    skip: int = 0,
    limit: int = 100,
    backup_type: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    시스템 백업 목록 조회 (관리자 전용)
    
    - **skip**: 건너뛸 레코드 수
    - **limit**: 반환할 최대 레코드 수
    - **backup_type**: 백업 유형별 필터링 (선택 사항)
    """
    return BackupService.get_backups(db, skip, limit, backup_type)


@router.get("/backups/{backup_id}", response_model=SystemBackupResponse)
async def get_backup(
    backup_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    특정 시스템 백업 조회 (관리자 전용)
    
    - **backup_id**: 백업 ID
    """
    backup = BackupService.get_backup(db, backup_id)
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID '{backup_id}' not found"
        )
    return backup


@router.post("/backups", response_model=SystemBackupResponse)
async def create_backup(
    backup: SystemBackupCreate,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    시스템 백업 생성 (관리자 전용)
    
    - **name**: 백업 이름
    - **description**: 백업 설명 (선택 사항)
    - **backup_type**: 백업 유형 (full, settings, users, queries, history)
    """
    # Log the backup start
    SystemMonitoringService.log_system_event(
        db=db,
        level="info",
        category="system",
        message=f"Starting system backup '{backup.name}' of type '{backup.backup_type.value}'",
        user_id=current_user.id
    )
    
    # For large backups, run in background
    if backup.backup_type == BackupType.FULL:
        # Create a placeholder backup record
        placeholder = SystemBackupCreate(
            name=f"{backup.name} (in progress)",
            description="Backup in progress...",
            backup_type=backup.backup_type
        )
        db_backup = BackupService.create_backup(db, placeholder, current_user.id)
        
        # Run the actual backup in the background
        background_tasks.add_task(
            BackupService.create_backup,
            db=db,
            backup=backup,
            user_id=current_user.id
        )
        
        return db_backup
    
    # For smaller backups, run synchronously
    return BackupService.create_backup(db, backup, current_user.id)


@router.delete("/backups/{backup_id}")
async def delete_backup(
    backup_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    시스템 백업 삭제 (관리자 전용)
    
    - **backup_id**: 백업 ID
    """
    result = BackupService.delete_backup(db, backup_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID '{backup_id}' not found"
        )
    return {"status": "success", "message": f"Backup with ID '{backup_id}' deleted"}


@router.post("/backups/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    restore_options: Optional[Dict[str, Any]] = None,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    시스템 백업 복원 (관리자 전용)
    
    - **backup_id**: 백업 ID
    - **restore_options**: 복원 옵션 (선택 사항)
    """
    restore_request = SystemRestoreRequest(
        backup_id=backup_id,
        restore_options=restore_options
    )
    
    result = BackupService.restore_backup(db, restore_request, current_user.id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    return result


@router.get("/backups/{backup_id}/download")
async def download_backup(
    backup_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    시스템 백업 다운로드 (관리자 전용)
    
    - **backup_id**: 백업 ID
    """
    backup_file = BackupService.download_backup(db, backup_id)
    if not backup_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup file for ID '{backup_id}' not found"
        )
    
    return FileResponse(
        path=backup_file["file_path"],
        filename=backup_file["file_name"],
        media_type="application/zip"
    )