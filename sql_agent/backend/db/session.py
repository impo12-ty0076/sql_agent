"""
Database session management
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from sqlalchemy import create_engine

from ..core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Create async session factory
async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Create base class for models
Base = declarative_base()

# 동기 엔진 (init_db 등 동기 코드에서 사용)
sync_engine = create_engine(
    settings.DATABASE_URL.replace("+aiosqlite", ""),
    echo=settings.DEBUG,
    future=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session
    
    Yields:
        AsyncSession: Database session
    """
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session
    
    Yields:
        AsyncSession: Database session
    """
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()