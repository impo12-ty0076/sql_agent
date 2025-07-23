"""
CRUD operations for system settings and backups
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from ..models.system_settings import (
    SystemSetting,
    DatabaseConnection,
    ApiKey,
    SystemBackup
)
from ...models.system_settings import (
    SystemSettingCreate,
    SystemSettingUpdate,
    DatabaseConnectionCreate,
    DatabaseConnectionUpdate,
    ApiKeyCreate,
    ApiKeyUpdate,
    SystemBackupCreate
)
from ...utils.encryption import encrypt_data, decrypt_data


# System Settings CRUD

def get_system_setting(db: Session, key: str):
    """
    Get a system setting by key
    
    Args:
        db: Database session
        key: Setting key
        
    Returns:
        SystemSetting or None
    """
    return db.query(SystemSetting).filter(SystemSetting.key == key).first()


def get_system_setting_by_id(db: Session, setting_id: str):
    """
    Get a system setting by ID
    
    Args:
        db: Database session
        setting_id: Setting ID
        
    Returns:
        SystemSetting or None
    """
    return db.query(SystemSetting).filter(SystemSetting.id == setting_id).first()


def get_system_settings(db: Session, skip: int = 0, limit: int = 100):
    """
    Get all system settings
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of SystemSetting
    """
    return db.query(SystemSetting).offset(skip).limit(limit).all()


def create_system_setting(db: Session, setting: SystemSettingCreate):
    """
    Create a new system setting
    
    Args:
        db: Database session
        setting: Setting data
        
    Returns:
        Created SystemSetting
    """
    db_setting = SystemSetting(
        key=setting.key,
        value=setting.value,
        description=setting.description
    )
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


def update_system_setting(db: Session, key: str, setting: SystemSettingUpdate):
    """
    Update a system setting
    
    Args:
        db: Database session
        key: Setting key
        setting: Updated setting data
        
    Returns:
        Updated SystemSetting or None if not found
    """
    db_setting = get_system_setting(db, key)
    if db_setting:
        db_setting.value = setting.value
        if setting.description is not None:
            db_setting.description = setting.description
        db_setting.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_setting)
    return db_setting


def delete_system_setting(db: Session, key: str):
    """
    Delete a system setting
    
    Args:
        db: Database session
        key: Setting key
        
    Returns:
        True if deleted, False if not found
    """
    db_setting = get_system_setting(db, key)
    if db_setting:
        db.delete(db_setting)
        db.commit()
        return True
    return False


# Database Connection CRUD

def get_database_connection(db: Session, connection_id: str):
    """
    Get a database connection by ID
    
    Args:
        db: Database session
        connection_id: Connection ID
        
    Returns:
        DatabaseConnection or None
    """
    return db.query(DatabaseConnection).filter(DatabaseConnection.id == connection_id).first()


def get_database_connection_by_name(db: Session, name: str):
    """
    Get a database connection by name
    
    Args:
        db: Database session
        name: Connection name
        
    Returns:
        DatabaseConnection or None
    """
    return db.query(DatabaseConnection).filter(DatabaseConnection.name == name).first()


def get_database_connections(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False):
    """
    Get all database connections
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: If True, only return active connections
        
    Returns:
        List of DatabaseConnection
    """
    query = db.query(DatabaseConnection)
    if active_only:
        query = query.filter(DatabaseConnection.is_active == True)
    return query.offset(skip).limit(limit).all()


def create_database_connection(db: Session, connection: DatabaseConnectionCreate):
    """
    Create a new database connection
    
    Args:
        db: Database session
        connection: Connection data
        
    Returns:
        Created DatabaseConnection
    """
    # Encrypt the password
    password_encrypted = encrypt_data(connection.password.get_secret_value())
    
    db_connection = DatabaseConnection(
        name=connection.name,
        type=connection.type.value,
        host=connection.host,
        port=connection.port,
        username=connection.username,
        password_encrypted=password_encrypted,
        database=connection.database,
        options=connection.options,
        is_active=connection.is_active
    )
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection


def update_database_connection(db: Session, connection_id: str, connection: DatabaseConnectionUpdate):
    """
    Update a database connection
    
    Args:
        db: Database session
        connection_id: Connection ID
        connection: Updated connection data
        
    Returns:
        Updated DatabaseConnection or None if not found
    """
    db_connection = get_database_connection(db, connection_id)
    if db_connection:
        if connection.name is not None:
            db_connection.name = connection.name
        if connection.host is not None:
            db_connection.host = connection.host
        if connection.port is not None:
            db_connection.port = connection.port
        if connection.username is not None:
            db_connection.username = connection.username
        if connection.password is not None:
            db_connection.password_encrypted = encrypt_data(connection.password.get_secret_value())
        if connection.database is not None:
            db_connection.database = connection.database
        if connection.options is not None:
            db_connection.options = connection.options
        if connection.is_active is not None:
            db_connection.is_active = connection.is_active
        
        db_connection.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_connection)
    return db_connection


def delete_database_connection(db: Session, connection_id: str):
    """
    Delete a database connection
    
    Args:
        db: Database session
        connection_id: Connection ID
        
    Returns:
        True if deleted, False if not found
    """
    db_connection = get_database_connection(db, connection_id)
    if db_connection:
        db.delete(db_connection)
        db.commit()
        return True
    return False


# API Key CRUD

def get_api_key(db: Session, key_id: str):
    """
    Get an API key by ID
    
    Args:
        db: Database session
        key_id: API key ID
        
    Returns:
        ApiKey or None
    """
    return db.query(ApiKey).filter(ApiKey.id == key_id).first()


def get_api_key_by_name_and_service(db: Session, name: str, service: str):
    """
    Get an API key by name and service
    
    Args:
        db: Database session
        name: API key name
        service: API service
        
    Returns:
        ApiKey or None
    """
    return db.query(ApiKey).filter(ApiKey.name == name, ApiKey.service == service).first()


def get_api_keys(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False, service: Optional[str] = None):
    """
    Get all API keys
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: If True, only return active API keys
        service: Filter by service
        
    Returns:
        List of ApiKey
    """
    query = db.query(ApiKey)
    if active_only:
        query = query.filter(ApiKey.is_active == True)
    if service:
        query = query.filter(ApiKey.service == service)
    return query.offset(skip).limit(limit).all()


def create_api_key(db: Session, api_key: ApiKeyCreate):
    """
    Create a new API key
    
    Args:
        db: Database session
        api_key: API key data
        
    Returns:
        Created ApiKey
    """
    # Encrypt the API key
    key_encrypted = encrypt_data(api_key.key.get_secret_value())
    
    db_api_key = ApiKey(
        name=api_key.name,
        service=api_key.service.value,
        key_encrypted=key_encrypted,
        is_active=api_key.is_active
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    return db_api_key


def update_api_key(db: Session, key_id: str, api_key: ApiKeyUpdate):
    """
    Update an API key
    
    Args:
        db: Database session
        key_id: API key ID
        api_key: Updated API key data
        
    Returns:
        Updated ApiKey or None if not found
    """
    db_api_key = get_api_key(db, key_id)
    if db_api_key:
        if api_key.name is not None:
            db_api_key.name = api_key.name
        if api_key.key is not None:
            db_api_key.key_encrypted = encrypt_data(api_key.key.get_secret_value())
        if api_key.is_active is not None:
            db_api_key.is_active = api_key.is_active
        
        db_api_key.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_api_key)
    return db_api_key


def delete_api_key(db: Session, key_id: str):
    """
    Delete an API key
    
    Args:
        db: Database session
        key_id: API key ID
        
    Returns:
        True if deleted, False if not found
    """
    db_api_key = get_api_key(db, key_id)
    if db_api_key:
        db.delete(db_api_key)
        db.commit()
        return True
    return False


def get_decrypted_api_key(db: Session, key_id: str):
    """
    Get a decrypted API key
    
    Args:
        db: Database session
        key_id: API key ID
        
    Returns:
        Decrypted API key or None if not found
    """
    db_api_key = get_api_key(db, key_id)
    if db_api_key:
        return decrypt_data(db_api_key.key_encrypted)
    return None


# System Backup CRUD

def get_system_backup(db: Session, backup_id: str):
    """
    Get a system backup by ID
    
    Args:
        db: Database session
        backup_id: Backup ID
        
    Returns:
        SystemBackup or None
    """
    return db.query(SystemBackup).filter(SystemBackup.id == backup_id).first()


def get_system_backups(db: Session, skip: int = 0, limit: int = 100, backup_type: Optional[str] = None):
    """
    Get all system backups
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        backup_type: Filter by backup type
        
    Returns:
        List of SystemBackup
    """
    query = db.query(SystemBackup).order_by(desc(SystemBackup.created_at))
    if backup_type:
        query = query.filter(SystemBackup.backup_type == backup_type)
    return query.offset(skip).limit(limit).all()


def create_system_backup(db: Session, backup: SystemBackupCreate, file_path: Optional[str] = None, 
                        backup_data: Optional[bytes] = None, metadata: Optional[Dict[str, Any]] = None, 
                        size_bytes: Optional[str] = None, created_by: Optional[str] = None):
    """
    Create a new system backup
    
    Args:
        db: Database session
        backup: Backup data
        file_path: Path to backup file
        backup_data: Backup data bytes
        metadata: Backup metadata
        size_bytes: Backup size in bytes
        created_by: User ID who created the backup
        
    Returns:
        Created SystemBackup
    """
    db_backup = SystemBackup(
        name=backup.name,
        description=backup.description,
        backup_type=backup.backup_type.value,
        file_path=file_path,
        backup_data=backup_data,
        metadata=metadata,
        size_bytes=size_bytes,
        created_by=created_by
    )
    db.add(db_backup)
    db.commit()
    db.refresh(db_backup)
    return db_backup


def delete_system_backup(db: Session, backup_id: str):
    """
    Delete a system backup
    
    Args:
        db: Database session
        backup_id: Backup ID
        
    Returns:
        True if deleted, False if not found
    """
    db_backup = get_system_backup(db, backup_id)
    if db_backup:
        db.delete(db_backup)
        db.commit()
        return True
    return False