"""
Configuration settings for FitConnect Backend
"""

import os
import json
from typing import Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FitConnect Backend"

    # Database
    DATABASE_URL: Optional[str] = None

    # AI/LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # LangGraph Settings
    USE_LANGGRAPH_FOR_QUESTIONS: bool = True  # True: LangGraph, False: 기존 LangChain

    # STT Settings
    WHISPER_MODEL: str = "base"

    # Vector Database
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    
    # XAI Cache
    XAI_CACHE_PATH: str = "./data/xai_cache.db"

    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIRECTORY: str = "./uploads"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",
        "http://54.89.71.175:8000",
        "http://52.91.24.1:8000",
        "https://fitconnect-frontend.vercel.app",
        "https://fit-back.duckdns.org",
    ]

    # Backend API URL (for calling main backend from AI service)
    BACKEND_API_URL: str = "http://52.91.24.1:8000"

    @field_validator('BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v: Union[str, list]) -> list:
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # Fallback to comma-separated values
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
