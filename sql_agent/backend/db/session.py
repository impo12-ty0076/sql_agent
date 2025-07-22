from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from ..core.config import settings

# 데이터베이스 URL 생성
SQLALCHEMY_DATABASE_URL = f"mssql+pymssql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # 연결 유효성 검사
    pool_recycle=3600,   # 1시간마다 연결 재활용
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성 (모델 클래스의 기본 클래스)
Base = declarative_base()

def get_db() -> Session:
    """
    데이터베이스 세션을 제공하는 의존성 함수
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()