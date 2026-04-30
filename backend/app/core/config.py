"""
Application configuration settings.
Uses pydantic-settings for environment variable management.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # App Info
    PROJECT_NAME: str = "Enterprise Policy & Knowledge Assistant"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Security
    SECRET_KEY: str = "change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/policy_assistant"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # Vector DB (FAISS)
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    
    # Google Drive (to be configured later)
    GOOGLE_DRIVE_CREDENTIALS_PATH: str = "./credentials.json"
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse comma-separated allowed hosts."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
