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
    
    # CORS config - allowed frontend origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    # AI Provider config - support multiple providers via MCP
    # Options: "openai", "anthropic", "google"
    AI_PROVIDER: str = "openai"
    
    # OpenAI config (read from env: OPENAI_API_KEY)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Anthropic config (read from env: ANTHROPIC_API_KEY)
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"
    
    # Google Gemini config (read from env: GOOGLE_API_KEY)
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_MODEL: str = "gemini-1.5-flash"
    
    # Image generation config - support multiple providers via MCP
    # Options: "stability", "flux"
    IMAGE_PROVIDER: str = "stability"
    
    # Stability AI config (read from env: STABILITY_API_KEY)
    STABILITY_API_KEY: Optional[str] = None
    STABILITY_MODEL: str = "sd-xl-lightning"  # SDXL Lightning
    
    # FLUX config (read from env: FLUX_API_KEY or STABILITY_API_KEY)
    FLUX_API_KEY: Optional[str] = None
    FLUX_MODEL: str = "flux-1-schnell"  # FLUX.1 Schnell
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
        # All API keys must come from environment variables
        # Never hardcode them in code


@lru_cache()
def get_settings() -> Settings:
    """Get settings singleton instance"""
    return Settings()


settings = get_settings()
