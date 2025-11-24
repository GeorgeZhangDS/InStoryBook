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
    
    # Router Agent (Conversation Layer)
    intent: Optional[str]
    memory_summary: Optional[str]
    
    # Chat Agent (Conversation Layer)
    chat_response: Optional[str]
    
    # Planner Agent (Workflow Layer)
    language: str
    story_outline: Optional[Dict[str, Any]]
    needs_info: bool
    missing_fields: Optional[List[str]]
    suggestions: Optional[List[str]]
    
    # Writer Agents (Workflow Layer)
    chapters: Annotated[List[Dict[str, Any]], operator.add]
    completed_writers: Annotated[List[int], operator.add]
    completed_image_gens: Annotated[List[int], operator.add]
    
    # Finalizer Agents (Workflow Layer)
    finalized_text: Optional[Dict[str, Any]]
    finalized_images: Optional[Dict[str, Any]]
    
    # System
    session_id: str
    messages: Annotated[List[BaseMessage], add_messages]