import logging
import uuid
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime

from .session import Base, SessionLocal, sync_engine
from .models.user import User, UserPreference, UserDatabasePermission, Role
from ..models.user import UserRole, ThemeType
from ..core.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 비밀번호 해싱을 위한 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db() -> None:
    """
    데이터베이스 초기화 및 기본 데이터 생성
    """
    # 테이블 생성
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=sync_engine)
    logger.info("Database tables created successfully")
    
    # 세션 생성
    db = SessionLocal()
    
    try:
        # 기본 역할 생성
        create_default_roles(db)
        
        # 기본 관리자 계정 생성
        create_admin_user(db)
        
        # 기타 초기 데이터 생성
        # TODO: 필요한 초기 데이터 생성 로직 추가
        
        logger.info("Database initialized successfully")
    finally:
        db.close()

def create_default_roles(db: Session) -> None:
    """
    기본 역할 생성
    """
    # 관리자 역할 생성
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        admin_role = Role(
            id=str(uuid.uuid4()),
            name="admin",
            description="시스템 관리자 역할"
        )
        db.add(admin_role)
        
    # 일반 사용자 역할 생성
    user_role = db.query(Role).filter(Role.name == "user").first()
    if not user_role:
        user_role = Role(
            id=str(uuid.uuid4()),
            name="user",
            description="일반 사용자 역할"
        )
        db.add(user_role)
        
    db.commit()
    logger.info("Default roles created successfully")

def create_admin_user(db: Session) -> None:
    """
    기본 관리자 계정 생성
    """
    # 관리자 계정이 이미 존재하는지 확인
    admin = db.query(User).filter(User.username == "admin").first()
    
    if admin:
        # Update password if it does not match current settings
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if not pwd_context.verify(settings.ADMIN_PASSWORD, admin.password_hash):
            logger.info("Updating existing admin user's password to match settings")
            admin.password_hash = pwd_context.hash(settings.ADMIN_PASSWORD)
            admin.updated_at = datetime.utcnow()
            db.commit()
        else:
            logger.info("Admin user already exists with up-to-date password")
        return
    
    # 관리자 계정 생성
    admin_id = str(uuid.uuid4())
    # Ensure password meets minimal length (6)
    password_value = settings.ADMIN_PASSWORD if len(settings.ADMIN_PASSWORD) >= 6 else "1qazXSW@"
    hashed_password = pwd_context.hash(password_value)
    
    admin_user = User(
        id=admin_id,
        username="admin",
        email="admin@example.com",
        password_hash=hashed_password,
        is_active=True,
        role=UserRole.ADMIN.value,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # 사용자 환경설정 생성
    admin_preferences = UserPreference(
        id=str(uuid.uuid4()),
        user_id=admin_id,
        theme=ThemeType.LIGHT.value,
        results_per_page=50,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(admin_user)
    db.add(admin_preferences)
    db.commit()
    logger.info("Admin user created successfully")

if __name__ == "__main__":
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialization completed")