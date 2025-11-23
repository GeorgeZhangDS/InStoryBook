"""
LangGraph state definition for story generation workflow
"""
import operator
from typing import TypedDict, List, Optional, Dict, Any, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class StoryState(TypedDict):
    # User input
    theme: str
    
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
    
    finalized_text: Optional[Dict[str, Any]]
    finalized_images: Optional[Dict[str, Any]]
    
    session_id: str
    messages: Annotated[List[BaseMessage], add_messages]