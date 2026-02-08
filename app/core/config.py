"""
Configuration module for CrossInsure AI backend.
Loads environment variables and provides centralized configuration.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./crossinsure.db"

    # JWT Configuration
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # API Configuration
    api_title: str = "CrossInsure AI"
    api_version: str = "1.0.0"
    api_description: str = "AI-Powered Insurance Fraud Detection System"

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

    # AI Service - Google Gemini
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"  # or "gemini-1.5-pro"
    gemini_embedding_model: str = "models/text-embedding-004"
    gemini_vision_model: str = "gemini-1.5-flash"
    
    # Gemini Configuration
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 8192

    # Image Storage (local blob store)
    image_storage_path: str = "./storage/claim-images"

    # Supabase Storage (optional)
    supabase_url: Optional[str] = None
    supabase_service_key: Optional[str] = None
    supabase_storage_bucket: str = "claims-images"
    supabase_signed_url_ttl_seconds: int = 600

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
