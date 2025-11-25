"""
LangGraph state definition for story generation workflow
"""
import operator
from typing import TypedDict, List, Optional, Dict, Any, Annotated


class StoryState(TypedDict):
    """ Conversation Layer """
    # User input
    theme: str
    
    # Router Agent
    intent: Optional[str]
    memory_summary: Optional[str]
    
    """ Workflow Layer """
    # Planner Agent
    language: str
    story_outline: Optional[Dict[str, Any]]
    needs_info: bool
    missing_fields: Optional[List[str]]
    suggestions: Optional[List[str]]
    
    # Writer Agents
    chapters: Annotated[List[Dict[str, Any]], operator.add]
    completed_writers: Annotated[List[int], operator.add]
    completed_image_gens: Annotated[List[int], operator.add]
    
    # Finalizer Agents
    finalized_text: Optional[Dict[str, Any]]
    finalized_images: Optional[Dict[str, Any]]
    
    # System
    session_id: str