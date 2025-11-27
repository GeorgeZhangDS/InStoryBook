"""
Application configuration management
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # App basic config
    APP_NAME: str = "InStoryBook"
    DEBUG: bool = False

    # API config
    API_V1_PREFIX: str = "/api/v1"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
    ]

    # TEXT GENERATION CONFIG
    AI_PROVIDER: str = "nova"
    AI_FALLBACK_PROVIDER: str = "openai"

    # Nova (Amazon Bedrock) configs
    AWS_ACCESS_KEY: Optional[str] = None
    AWS_SECRET_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    NOVA_MODEL: str = "us.amazon.nova-micro-v1:0"

    # OpenAI configs
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # IMAGE GENERATION CONFIG
    # Runware Image configs
    RUNWARE_API_KEY: Optional[str] = None
    RUNWARE_IMAGE_MODEL: str = "runware:101@1" 
    RUNWARE_API_BASE_URL: str = "https://api.runware.ai/v1"

    # Fixed style for consistent image generation
    # This style description will be appended to all image prompts
    IMAGE_STYLE: str = "Children's storybook illustration style, no text, no words in the image."
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()