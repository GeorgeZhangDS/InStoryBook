"""
AI service abstraction layer
"""
from app.services.ai_services.text_generator import get_text_generator
from app.services.ai_services.image_generator import get_image_generator

__all__ = ["get_text_generator", "get_image_generator"]

