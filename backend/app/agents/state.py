"""
LangGraph state definition for story generation workflow
"""
from typing import TypedDict, List, Optional, Dict, Any, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class StoryState(TypedDict):
    """LangGraph state for story generation workflow"""
    theme: str
    language: str
    
    story_outline: Optional[Dict[str, Any]]
    needs_info: bool
    missing_fields: Optional[List[str]]
    suggestions: Optional[List[str]]
    
    chapters: Annotated[List[Dict[str, Any]], add_messages]
    
    completed_writers: List[int]
    completed_image_prompts: List[int]
    completed_image_gens: List[int]
    
    quality_check_passed: bool
    quality_issues: Optional[List[str]]
    
    formatted_story: Optional[Dict[str, Any]]
    
    session_id: str
    messages: Annotated[List[BaseMessage], add_messages]