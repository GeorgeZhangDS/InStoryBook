"""
API routes module
"""
from fastapi import APIRouter

from app.api import story

# Create main API router
router = APIRouter()

# Include sub-routers
router.include_router(story.router, prefix="/story", tags=["story"])