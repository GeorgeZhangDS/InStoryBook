"""
Application configuration management
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
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
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[List[str], str]) -> List[str]:
        """Parse CORS_ORIGINS from string or list"""
        if isinstance(v, str):
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # TEXT GENERATION CONFIG
    AI_PROVIDER: str = "nova"
    AI_FALLBACK_PROVIDER: str = "openai"

    # Nova (Amazon Bedrock) configs
    # Options: nova-micro-v1:0 (fastest), nova-lite-v1:0 (balanced), nova-pro-v1:0 (most capable)
    AWS_ACCESS_KEY: Optional[str] = None
    AWS_SECRET_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    NOVA_MODEL: str = "us.amazon.nova-lite-v1:0"  # Upgraded from micro to lite for better intelligence while maintaining efficiency

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