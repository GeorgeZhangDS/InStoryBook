"""
API routes module
"""
from fastapi import APIRouter

from app.api import websocket

router = APIRouter()
router.include_router(websocket.router, tags=["websocket"])