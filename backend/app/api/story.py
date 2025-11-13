"""
Story generation API endpoints
"""
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import StoryRequest, StoryResponse, StoryGenerateResponse

router = APIRouter()


@router.post("/generate", response_model=StoryGenerateResponse)
async def generate_story(request: StoryRequest):
    """
    Create a new story generation task
    Returns session_id for tracking the generation progress
    """
    # TODO: Implement story generation logic
    # 1. Create session
    # 2. Initialize LangGraph workflow
    # 3. Start async task
    # 4. Return session_id
    
    return StoryGenerateResponse(
        session_id="placeholder-session-id",
        message="Story generation started",
        status="pending",
    )


@router.get("/{session_id}", response_model=StoryResponse)
async def get_story(session_id: str):
    """
    Get story generation status and result
    Returns current state of story generation
    """
    # TODO: Implement story retrieval logic
    # 1. Query Redis for session state
    # 2. Return StoryState or 404 if not found
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Session {session_id} not found",
    )

