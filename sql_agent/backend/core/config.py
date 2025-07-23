"""
Application configuration
"""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # API settings
    API_HOST: str = Field("0.0.0.0", env="API_HOST")
    API_PORT: int = Field(8000, env="API_PORT")
    
    # Debug mode
    DEBUG: bool = Field(False, env="DEBUG")
    
    # CORS settings
    CORS_ORIGINS: str = Field("*", env="CORS_ORIGINS")
    
    # Database settings
    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./sql_agent.db",
        env="DATABASE_URL"
    )
    
    # JWT settings
    SECRET_KEY: str = Field("secret_key", env="SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # LLM settings
    LLM_PROVIDER: str = Field("openai", env="LLM_PROVIDER")
    OPENAI_API_KEY: str = Field("", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field("gpt-4", env="OPENAI_MODEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()