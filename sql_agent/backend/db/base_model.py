from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from typing import Any

from .session import Base

class BaseModel(Base):
    """
    모든 모델의 기본 클래스
    """
    __abstract__ = True
    
    # 테이블 이름을 클래스 이름의 소문자 형태로 자동 생성
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    # 생성 시간
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 수정 시간
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    def __repr__(self) -> str:
        """
        객체의 문자열 표현
        """
        attrs = []
        for c in self.__table__.columns:
            if hasattr(self, c.name):
                val = getattr(self, c.name)
                if val is not None:
                    attrs.append(f"{c.name}={val}")
        
        return f"<{self.__class__.__name__}({', '.join(attrs)})>"
    
    def to_dict(self) -> dict:
        """
        객체를 딕셔너리로 변환
        """
        result = {}
        for c in self.__table__.columns:
            if hasattr(self, c.name):
                val = getattr(self, c.name)
                result[c.name] = val
        
        return result