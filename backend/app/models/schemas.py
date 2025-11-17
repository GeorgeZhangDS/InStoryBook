"""
Pydantic data models for request/response and state management
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class AgentType(str, Enum):
    """Agent type enum"""
    PLANNER = "planner"
    WRITER = "writer"
    IMAGE_PROMPT = "image_prompt"
    IMAGE_GEN = "image_gen"
    QUALITY_CHECK = "quality_check"
    FORMATTER = "formatter"


class AgentStatus(str, Enum):
    """Agent status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StoryStyle(str, Enum):
    """Story style enum - used for prompt generation"""
    ADVENTURE = "adventure"
    FANTASY = "fantasy"
    EDUCATIONAL = "educational"
    FRIENDSHIP = "friendship"
    NATURE = "nature"
    ANIMAL = "animal"
    MAGICAL = "magical"
    SCIENTIFIC = "scientific"


class StoryRequest(BaseModel):
    """Story generation request - user only inputs theme"""
    theme: str = Field(..., description="Story theme", min_length=30, max_length=2000)
    style: Optional[StoryStyle] = Field(None, description="Story style - auto-detected if not provided")
    chapter_count: Optional[int] = Field(4, description="Number of chapters", ge=1, le=8)


class ChapterContent(BaseModel):
    """Chapter content with text and image"""
    chapter_id: int
    title: str
    text: str
    image_url: Optional[str] = None
    image_prompt: Optional[str] = None


class AgentProgress(BaseModel):
    """Agent execution progress"""
    agent_id: str
    agent_type: AgentType
    chapter_id: Optional[int] = None
    status: AgentStatus
    progress: float = Field(0.0, ge=0.0, le=1.0)
    elapsed_time: float = 0.0
    estimated_remaining: Optional[float] = None
    error_message: Optional[str] = None


class StoryState(BaseModel):
    """Story generation state"""
    session_id: str
    theme: str
    status: str
    chapters: List[ChapterContent] = []
    agent_progress: Dict[str, AgentProgress] = {}
    created_at: datetime
    updated_at: datetime
    total_time: Optional[float] = None


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    event_id: str
    type: str
    timestamp: float
    session_id: str
    data: Dict[str, Any]


class StoryGenerateResponse(BaseModel):
    """Response for story generation request"""
    session_id: str
    message: str
    status: str  # "pending", "running", "completed", "failed"


class StoryResponse(BaseModel):
    """Story generation response"""
    session_id: str
    theme: str
    chapters: List[ChapterContent]
    total_time: float
    metadata: Dict[str, Any] = {}