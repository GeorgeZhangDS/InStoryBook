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
    IMAGE_PROVIDER: str = "stability"
    IMAGE_FALLBACK_PROVIDER: str = "openai"

    # Stability AI configs
    STABILITY_API_KEY: Optional[str] = None
    STABILITY_MODEL: str = "stable-diffusion-xl-1024-v1-0"

    # OpenAI Image configs
    OPENAI_IMAGE_MODEL: str = "gpt-image-1-mini"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()