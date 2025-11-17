"""
Unit tests for configuration management
"""
import pytest
from app.core.config import settings, get_settings


def test_settings_loaded():
    """Test that settings are loaded correctly"""
    assert settings.APP_NAME == "InStoryBook"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.REDIS_URL == "redis://localhost:6379/0"


def test_settings_singleton():
    """Test that get_settings returns singleton"""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_cors_origins():
    """Test CORS origins configuration"""
    assert isinstance(settings.CORS_ORIGINS, list)
    assert "http://localhost:5173" in settings.CORS_ORIGINS


def test_ai_provider_config():
    """Test AI provider configuration"""
    assert settings.AI_PROVIDER in ["nova", "openai"]
    assert settings.AI_FALLBACK_PROVIDER in ["nova", "openai"]


def test_image_provider_config():
    """Test image provider configuration"""
    assert settings.IMAGE_PROVIDER in ["stability", "openai"]
    assert settings.IMAGE_FALLBACK_PROVIDER in ["stability", "openai"]

