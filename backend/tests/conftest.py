"""
Pytest configuration and shared fixtures
"""
import pytest
import os
from typing import Generator


@pytest.fixture(scope="session")
def api_keys_available() -> dict:
    """Check which API keys are available"""
    return {
        "aws_access_key": bool(os.getenv("AWS_ACCESS_KEY")),
        "aws_secret_key": bool(os.getenv("AWS_SECRET_KEY")),
        "openai_key": bool(os.getenv("OPENAI_API_KEY")),
    }


@pytest.fixture(scope="session")
def skip_if_no_api_keys(api_keys_available: dict):
    """Fixture to skip tests if required API keys are missing"""
    def _skip_if_missing(*required_keys: str):
        missing = []
        for key in required_keys:
            if not api_keys_available.get(key, False):
                missing.append(key)
        
        if missing:
            pytest.skip(f"Missing required API keys: {', '.join(missing)}")
    
    return _skip_if_missing

