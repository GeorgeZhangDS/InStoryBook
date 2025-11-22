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
    chapters: Annotated[List[Dict[str, Any]], add_messages]
    completed_writers: Annotated[List[int], operator.add]
    completed_image_gens: Annotated[List[int], operator.add]
    
    finalized_story: Optional[Dict[str, Any]]
    text_finalized: bool
    
    session_id: str
    messages: Annotated[List[BaseMessage], add_messages]