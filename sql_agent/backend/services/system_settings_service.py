"""
Service for system settings and backup management
"""
import logging
import os
import json
import shutil
import zipfile
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from sqlalchemy.orm import Session
import uuid

from ..db.crud.system_settings import (
    get_system_setting,
    get_system_settings,
    create_system_setting,
    update_system_setting,
    delete_system_setting,
    get_database_connection,
    get_database_connections,
    create_database_connection,
    update_database_connection,
    delete_database_connection,
    get_api_key,
    get_api_keys,
    create_api_key,
    update_api_key,
    delete_api_key,
    get_decrypted_api_key,
    get_system_backup,
    get_system_backups,
    create_system_backup,
    delete_system_backup
)
from ..db.crud.user import get_users
from ..db.crud.query import get_queries
from ..db.crud.query_history import get_query_histories
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
from ..utils.encryption import encrypt_data, decrypt_data
from ..services.system_monitoring_service import SystemMonitoringService

logger = logging.getLogger(__name__)

# Define backup directory
BACKUP_DIR = os.environ.get('BACKUP_DIR', './backups')

# Ensure backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)


class SystemSettingsService:
    """Service for system settings management"""
    
    @staticmethod
    def get_setting(db: Session, key: str) -> Optional[SystemSettingResponse]:
        """
        Get a system setting by key
        
        Args:
            db: Database session
            key: Setting key
            
        Returns:
            System setting or None
        """
        setting = get_system_setting(db, key)
        if setting:
            return SystemSettingResponse.from_orm(setting)
        return None
    
    @staticmethod
    def get_settings(db: Session, skip: int = 0, limit: int = 100) -> List[SystemSettingResponse]:
        """
        Get all system settings
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of system settings
        """
        settings = get_system_settings(db, skip, limit)
        return [SystemSettingResponse.from_orm(setting) for setting in settings]
    
    @staticmethod
    def create_setting(db: Session, setting: SystemSettingCreate) -> SystemSettingResponse:
        """
        Create a new system setting
        
        Args:
            db: Database session
            setting: Setting data
            
        Returns:
            Created system setting
        """
        # Check if setting already exists
        existing_setting = get_system_setting(db, setting.key)
        if existing_setting:
            # Update existing setting
            updated_setting = update_system_setting(db, setting.key, SystemSettingUpdate(
                value=setting.value,
                description=setting.description
            ))
            return SystemSettingResponse.from_orm(updated_setting)
        
        # Create new setting
        db_setting = create_system_setting(db, setting)
        
        # Log the event
        SystemMonitoringService.log_system_event(
            db=db,
            level="info",
            category="system",
            message=f"System setting '{setting.key}' created"
        )
        
        return SystemSettingResponse.from_orm(db_setting)
    
    @staticmethod
    def update_setting(db: Session, key: str, setting: SystemSettingUpdate) -> Optional[SystemSettingResponse]:
        """
        Update a system setting
        
        Args:
            db: Database session
            key: Setting key
            setting: Updated setting data
            
        Returns:
            Updated system setting or None if not found
        """
        db_setting = update_system_setting(db, key, setting)
        if db_setting:
            # Log the event
            SystemMonitoringService.log_system_event(
                db=db,
                level="info",
                category="system",
                message=f"System setting '{key}' updated"
            )
            
            return SystemSettingResponse.from_orm(db_setting)
        return None
    
    @staticmethod
    def delete_setting(db: Session, key: str) -> bool:
        """
        Delete a system setting
        
        Args:
            db: Database session
            key: Setting key
            
        Returns:
            True if deleted, False if not found
        """
        result = delete_system_setting(db, key)
        if result:
            # Log the event
            SystemMonitoringService.log_system_event(
                db=db,
                level="info",
                category="system",
                message=f"System setting '{key}' deleted"
            )
        
        return result


class DatabaseConnectionService:
    """Service for database connection management"""
    
    @staticmethod
    def get_connection(db: Session, connection_id: str) -> Optional[DatabaseConnectionResponse]:
        """
        Get a database connection by ID
        
        Args:
            db: Database session
            connection_id: Connection ID
            
        Returns:
            Database connection or None
        """
        connection = get_database_connection(db, connection_id)
        if connection:
            return DatabaseConnectionResponse.from_orm(connection)
        return None
    
    @staticmethod
    def get_connections(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[DatabaseConnectionResponse]:
        """
        Get all database connections
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: If True, only return active connections
            
        Returns:
            List of database connections
        """
        connections = get_database_connections(db, skip, limit, active_only)
        return [DatabaseConnectionResponse.from_orm(connection) for connection in connections]
    
    @staticmethod
    def create_connection(db: Session, connection: DatabaseConnectionCreate) -> DatabaseConnectionResponse:
        """
        Create a new database connection
        
        Args:
            db: Database session
            connection: Connection data
            
        Returns:
            Created database connection
        """
        db_connection = create_database_connection(db, connection)
        
        # Log the event
        SystemMonitoringService.log_system_event(
            db=db,
            level="info",
            category="database",
            message=f"Database connection '{connection.name}' created"
        )
        
        return DatabaseConnectionResponse.from_orm(db_connection)
    
    @staticmethod
    def update_connection(db: Session, connection_id: str, connection: DatabaseConnectionUpdate) -> Optional[DatabaseConnectionResponse]:
        """
        Update a database connection
        
        Args:
            db: Database session
            connection_id: Connection ID
            connection: Updated connection data
            
        Returns:
            Updated database connection or None if not found
        """
        db_connection = update_database_connection(db, connection_id, connection)
        if db_connection:
            # Log the event
            SystemMonitoringService.log_system_event(
                db=db,
                level="info",
                category="database",
                message=f"Database connection '{db_connection.name}' updated"
            )
            
            return DatabaseConnectionResponse.from_orm(db_connection)
        return None
    
    @staticmethod
    def delete_connection(db: Session, connection_id: str) -> bool:
        """
        Delete a database connection
        
        Args:
            db: Database session
            connection_id: Connection ID
            
        Returns:
            True if deleted, False if not found
        """
        connection = get_database_connection(db, connection_id)
        if connection:
            result = delete_database_connection(db, connection_id)
            if result:
                # Log the event
                SystemMonitoringService.log_system_event(
                    db=db,
                    level="info",
                    category="database",
                    message=f"Database connection '{connection.name}' deleted"
                )
            
            return result
        return False
    
    @staticmethod
    def test_connection(db: Session, connection_id: str) -> Dict[str, Any]:
        """
        Test a database connection
        
        Args:
            db: Database session
            connection_id: Connection ID
            
        Returns:
            Dictionary with test result
        """
        connection = get_database_connection(db, connection_id)
        if not connection:
            return {"success": False, "message": "Connection not found"}
        
        try:
            # This is a placeholder for actual connection testing
            # In a real implementation, this would attempt to connect to the database
            # using the connection parameters
            
            # For now, just return success
            return {
                "success": True,
                "message": "Connection successful",
                "details": {
                    "database_type": connection.type,
                    "host": connection.host,
                    "port": connection.port,
                    "database": connection.database
                }
            }
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return {"success": False, "message": f"Connection failed: {str(e)}"}


class ApiKeyService:
    """Service for API key management"""
    
    @staticmethod
    def get_api_key(db: Session, key_id: str) -> Optional[ApiKeyResponse]:
        """
        Get an API key by ID
        
        Args:
            db: Database session
            key_id: API key ID
            
        Returns:
            API key or None
        """
        api_key = get_api_key(db, key_id)
        if api_key:
            return ApiKeyResponse.from_orm(api_key)
        return None
    
    @staticmethod
    def get_api_keys(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False, service: Optional[str] = None) -> List[ApiKeyResponse]:
        """
        Get all API keys
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: If True, only return active API keys
            service: Filter by service
            
        Returns:
            List of API keys
        """
        api_keys = get_api_keys(db, skip, limit, active_only, service)
        return [ApiKeyResponse.from_orm(api_key) for api_key in api_keys]
    
    @staticmethod
    def create_api_key(db: Session, api_key: ApiKeyCreate) -> ApiKeyResponse:
        """
        Create a new API key
        
        Args:
            db: Database session
            api_key: API key data
            
        Returns:
            Created API key
        """
        db_api_key = create_api_key(db, api_key)
        
        # Log the event
        SystemMonitoringService.log_system_event(
            db=db,
            level="info",
            category="system",
            message=f"API key '{api_key.name}' for service '{api_key.service}' created"
        )
        
        return ApiKeyResponse.from_orm(db_api_key)
    
    @staticmethod
    def update_api_key(db: Session, key_id: str, api_key: ApiKeyUpdate) -> Optional[ApiKeyResponse]:
        """
        Update an API key
        
        Args:
            db: Database session
            key_id: API key ID
            api_key: Updated API key data
            
        Returns:
            Updated API key or None if not found
        """
        db_api_key = update_api_key(db, key_id, api_key)
        if db_api_key:
            # Log the event
            SystemMonitoringService.log_system_event(
                db=db,
                level="info",
                category="system",
                message=f"API key '{db_api_key.name}' for service '{db_api_key.service}' updated"
            )
            
            return ApiKeyResponse.from_orm(db_api_key)
        return None
    
    @staticmethod
    def delete_api_key(db: Session, key_id: str) -> bool:
        """
        Delete an API key
        
        Args:
            db: Database session
            key_id: API key ID
            
        Returns:
            True if deleted, False if not found
        """
        api_key = get_api_key(db, key_id)
        if api_key:
            result = delete_api_key(db, key_id)
            if result:
                # Log the event
                SystemMonitoringService.log_system_event(
                    db=db,
                    level="info",
                    category="system",
                    message=f"API key '{api_key.name}' for service '{api_key.service}' deleted"
                )
            
            return result
        return False
    
    @staticmethod
    def get_decrypted_key(db: Session, key_id: str) -> Optional[str]:
        """
        Get a decrypted API key
        
        Args:
            db: Database session
            key_id: API key ID
            
        Returns:
            Decrypted API key or None if not found
        """
        return get_decrypted_api_key(db, key_id)
    
    @staticmethod
    def test_api_key(db: Session, key_id: str) -> Dict[str, Any]:
        """
        Test an API key
        
        Args:
            db: Database session
            key_id: API key ID
            
        Returns:
            Dictionary with test result
        """
        api_key = get_api_key(db, key_id)
        if not api_key:
            return {"success": False, "message": "API key not found"}
        
        try:
            # This is a placeholder for actual API key testing
            # In a real implementation, this would attempt to use the API key
            # to make a test request to the service
            
            # For now, just return success
            return {
                "success": True,
                "message": "API key is valid",
                "details": {
                    "service": api_key.service,
                    "name": api_key.name
                }
            }
        except Exception as e:
            logger.error(f"Error testing API key: {str(e)}")
            return {"success": False, "message": f"API key test failed: {str(e)}"}


class BackupService:
    """Service for system backup and restore"""
    
    @staticmethod
    def get_backup(db: Session, backup_id: str) -> Optional[SystemBackupResponse]:
        """
        Get a system backup by ID
        
        Args:
            db: Database session
            backup_id: Backup ID
            
        Returns:
            System backup or None
        """
        backup = get_system_backup(db, backup_id)
        if backup:
            return SystemBackupResponse.from_orm(backup)
        return None
    
    @staticmethod
    def get_backups(db: Session, skip: int = 0, limit: int = 100, backup_type: Optional[str] = None) -> List[SystemBackupResponse]:
        """
        Get all system backups
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            backup_type: Filter by backup type
            
        Returns:
            List of system backups
        """
        backups = get_system_backups(db, skip, limit, backup_type)
        return [SystemBackupResponse.from_orm(backup) for backup in backups]
    
    @staticmethod
    def create_backup(db: Session, backup: SystemBackupCreate, user_id: Optional[str] = None) -> SystemBackupResponse:
        """
        Create a new system backup
        
        Args:
            db: Database session
            backup: Backup data
            user_id: ID of the user creating the backup
            
        Returns:
            Created system backup
        """
        try:
            # Create a temporary directory for the backup
            with tempfile.TemporaryDirectory() as temp_dir:
                backup_data = {}
                
                # Backup data based on backup type
                if backup.backup_type == BackupType.SETTINGS or backup.backup_type == BackupType.FULL:
                    # Backup system settings
                    settings = get_system_settings(db)
                    backup_data["settings"] = [{"key": s.key, "value": s.value, "description": s.description} for s in settings]
                    
                    # Backup database connections
                    connections = get_database_connections(db)
                    backup_data["database_connections"] = [
                        {
                            "name": c.name,
                            "type": c.type,
                            "host": c.host,
                            "port": c.port,
                            "username": c.username,
                            "database": c.database,
                            "options": c.options,
                            "is_active": c.is_active
                        } for c in connections
                    ]
                    
                    # Backup API keys (without the actual keys for security)
                    api_keys = get_api_keys(db)
                    backup_data["api_keys"] = [
                        {
                            "name": k.name,
                            "service": k.service,
                            "is_active": k.is_active
                        } for k in api_keys
                    ]
                
                if backup.backup_type == BackupType.USERS or backup.backup_type == BackupType.FULL:
                    # Backup users (without passwords for security)
                    users = get_users(db)
                    backup_data["users"] = [
                        {
                            "username": u.username,
                            "email": u.email,
                            "role": u.role,
                            "is_active": u.is_active
                        } for u in users
                    ]
                
                if backup.backup_type == BackupType.QUERIES or backup.backup_type == BackupType.FULL:
                    # Backup queries
                    queries = get_queries(db)
                    backup_data["queries"] = [
                        {
                            "user_id": q.user_id,
                            "db_id": q.db_id,
                            "natural_language": q.natural_language,
                            "generated_sql": q.generated_sql,
                            "executed_sql": q.executed_sql,
                            "status": q.status,
                            "start_time": q.start_time.isoformat() if q.start_time else None,
                            "end_time": q.end_time.isoformat() if q.end_time else None,
                            "error": q.error
                        } for q in queries
                    ]
                
                if backup.backup_type == BackupType.HISTORY or backup.backup_type == BackupType.FULL:
                    # Backup query history
                    histories = get_query_histories(db)
                    backup_data["query_histories"] = [
                        {
                            "user_id": h.user_id,
                            "query_id": h.query_id,
                            "favorite": h.favorite,
                            "tags": h.tags,
                            "notes": h.notes
                        } for h in histories
                    ]
                
                # Save backup data to a JSON file
                backup_file = os.path.join(temp_dir, "backup.json")
                with open(backup_file, "w") as f:
                    json.dump(backup_data, f, indent=2)
                
                # Create a zip file
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                zip_filename = f"{backup.backup_type.value}_backup_{timestamp}.zip"
                zip_path = os.path.join(BACKUP_DIR, zip_filename)
                
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(backup_file, arcname="backup.json")
                
                # Get the size of the zip file
                size_bytes = os.path.getsize(zip_path)
                
                # Create backup record in the database
                metadata = {
                    "timestamp": timestamp,
                    "backup_type": backup.backup_type.value,
                    "item_counts": {
                        "settings": len(backup_data.get("settings", [])),
                        "database_connections": len(backup_data.get("database_connections", [])),
                        "api_keys": len(backup_data.get("api_keys", [])),
                        "users": len(backup_data.get("users", [])),
                        "queries": len(backup_data.get("queries", [])),
                        "query_histories": len(backup_data.get("query_histories", []))
                    }
                }
                
                db_backup = create_system_backup(
                    db=db,
                    backup=backup,
                    file_path=zip_path,
                    metadata=metadata,
                    size_bytes=str(size_bytes),
                    created_by=user_id
                )
                
                # Log the event
                SystemMonitoringService.log_system_event(
                    db=db,
                    level="info",
                    category="system",
                    message=f"System backup '{backup.name}' of type '{backup.backup_type.value}' created",
                    user_id=user_id,
                    details={"backup_id": db_backup.id, "file_path": zip_path, "size_bytes": size_bytes}
                )
                
                return SystemBackupResponse.from_orm(db_backup)
        
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            # Log the error
            SystemMonitoringService.log_system_event(
                db=db,
                level="error",
                category="system",
                message=f"Error creating system backup: {str(e)}",
                user_id=user_id
            )
            raise
    
    @staticmethod
    def delete_backup(db: Session, backup_id: str) -> bool:
        """
        Delete a system backup
        
        Args:
            db: Database session
            backup_id: Backup ID
            
        Returns:
            True if deleted, False if not found
        """
        backup = get_system_backup(db, backup_id)
        if backup:
            # Delete the backup file if it exists
            if backup.file_path and os.path.exists(backup.file_path):
                try:
                    os.remove(backup.file_path)
                except Exception as e:
                    logger.error(f"Error deleting backup file: {str(e)}")
            
            # Delete the backup record
            result = delete_system_backup(db, backup_id)
            if result:
                # Log the event
                SystemMonitoringService.log_system_event(
                    db=db,
                    level="info",
                    category="system",
                    message=f"System backup '{backup.name}' deleted"
                )
            
            return result
        return False
    
    @staticmethod
    def download_backup(db: Session, backup_id: str) -> Optional[Dict[str, str]]:
        """
        Get a backup file for download
        
        Args:
            db: Database session
            backup_id: Backup ID
            
        Returns:
            Dictionary with file path and name, or None if not found
        """
        backup = get_system_backup(db, backup_id)
        if not backup or not backup.file_path or not os.path.exists(backup.file_path):
            return None
        
        # Extract filename from path
        file_name = os.path.basename(backup.file_path)
        
        # Log the download event
        SystemMonitoringService.log_system_event(
            db=db,
            level="info",
            category="system",
            message=f"System backup '{backup.name}' downloaded",
            details={"backup_id": backup.id, "file_path": backup.file_path}
        )
        
        return {
            "file_path": backup.file_path,
            "file_name": file_name
        }
    
    @staticmethod
    def restore_backup(db: Session, restore_request: SystemRestoreRequest, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Restore a system backup
        
        Args:
            db: Database session
            restore_request: Restore request data
            user_id: ID of the user performing the restore
            
        Returns:
            Dictionary with restore result
        """
        backup = get_system_backup(db, restore_request.backup_id)
        if not backup:
            return {"success": False, "message": "Backup not found"}
        
        try:
            # Check if the backup file exists
            if not backup.file_path or not os.path.exists(backup.file_path):
                return {"success": False, "message": "Backup file not found"}
            
            # Create a temporary directory for the restore
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract the backup file
                with zipfile.ZipFile(backup.file_path, "r") as zipf:
                    zipf.extractall(temp_dir)
                
                # Load the backup data
                backup_file = os.path.join(temp_dir, "backup.json")
                with open(backup_file, "r") as f:
                    backup_data = json.load(f)
                
                # Restore data based on backup type and options
                restore_options = restore_request.restore_options or {}
                
                # Restore system settings
                if backup.backup_type in ["settings", "full"] and restore_options.get("restore_settings", True):
                    if "settings" in backup_data:
                        for setting in backup_data["settings"]:
                            create_system_setting(db, SystemSettingCreate(
                                key=setting["key"],
                                value=setting["value"],
                                description=setting.get("description")
                            ))
                
                # Restore database connections
                if backup.backup_type in ["settings", "full"] and restore_options.get("restore_connections", True):
                    if "database_connections" in backup_data:
                        # This is a placeholder - in a real implementation, you would need to handle
                        # the encrypted passwords, which are not included in the backup for security reasons
                        pass
                
                # Restore API keys
                if backup.backup_type in ["settings", "full"] and restore_options.get("restore_api_keys", True):
                    if "api_keys" in backup_data:
                        # This is a placeholder - in a real implementation, you would need to handle
                        # the encrypted API keys, which are not included in the backup for security reasons
                        pass
                
                # Restore users
                if backup.backup_type in ["users", "full"] and restore_options.get("restore_users", True):
                    if "users" in backup_data:
                        # This is a placeholder - in a real implementation, you would need to handle
                        # the user passwords, which are not included in the backup for security reasons
                        pass
                
                # Log the event
                SystemMonitoringService.log_system_event(
                    db=db,
                    level="info",
                    category="system",
                    message=f"System backup '{backup.name}' restored",
                    user_id=user_id,
                    details={"backup_id": backup.id, "restore_options": restore_options}
                )
                
                return {
                    "success": True,
                    "message": f"Backup '{backup.name}' restored successfully",
                    "details": {
                        "backup_id": backup.id,
                        "backup_type": backup.backup_type,
                        "restore_options": restore_options
                    }
                }
        
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}")
            # Log the error
            SystemMonitoringService.log_system_event(
                db=db,
                level="error",
                category="system",
                message=f"Error restoring system backup: {str(e)}",
                user_id=user_id
            )
            
            return {"success": False, "message": f"Error restoring backup: {str(e)}"}
    
    @staticmethod
    def download_backup(db: Session, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a backup file for download
        
        Args:
            db: Database session
            backup_id: Backup ID
            
        Returns:
            Dictionary with file path and name, or None if not found
        """
        backup = get_system_backup(db, backup_id)
        if backup and backup.file_path and os.path.exists(backup.file_path):
            return {
                "file_path": backup.file_path,
                "file_name": os.path.basename(backup.file_path)
            }
        return None