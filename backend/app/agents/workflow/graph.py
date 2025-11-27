"""
Story Graph - Workflow container for story generation
"""
import logging
from functools import partial
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import StoryState
from .planner import planner_agent
from .writer import writer_agent
from .illustrator import illustrator_agent
from .finalizer import finalizer_text_agent, finalizer_image_agent

logger = logging.getLogger(__name__)


def should_continue(state: StoryState) -> Literal["fanout", "end"]:
    """Planner decides if workflow should continue or stop"""
    return "end" if state.get("needs_info", False) else "fanout"


def check_writers_completion(state: StoryState) -> Literal["finalize_text", "wait"]:
    """Check if all writers are completed"""
    completed_writers = state.get("completed_writers", [])
    finalized_text = state.get("finalized_text")
    
    unique_writers = set(completed_writers)
    writers_done = len(unique_writers) == 4
    
    if writers_done and not finalized_text:
        return "finalize_text"
    return "wait"


def check_illustrators_completion(state: StoryState) -> Literal["finalize_images", "wait"]:
    """Check if all illustrators are completed"""
    completed_image_gens = state.get("completed_image_gens", [])
    finalized_images = state.get("finalized_images")
    
    unique_image_gens = set(completed_image_gens)
    images_done = len(unique_image_gens) == 4
    
    if images_done and not finalized_images:
        return "finalize_images"
    return "wait"


def create_story_graph() -> CompiledStateGraph:
    """Create and compile the LangGraph workflow"""
    workflow = StateGraph(StoryState)
    
    workflow.add_node("planner", planner_agent)
    workflow.add_node("writer_1", partial(writer_agent, chapter_id=1))
    workflow.add_node("writer_2", partial(writer_agent, chapter_id=2))
    workflow.add_node("writer_3", partial(writer_agent, chapter_id=3))
    workflow.add_node("writer_4", partial(writer_agent, chapter_id=4))
    workflow.add_node("illustrator_1", partial(illustrator_agent, chapter_id=1))
    workflow.add_node("illustrator_2", partial(illustrator_agent, chapter_id=2))
    workflow.add_node("illustrator_3", partial(illustrator_agent, chapter_id=3))
    workflow.add_node("illustrator_4", partial(illustrator_agent, chapter_id=4))
    workflow.add_node("finalizer_text", finalizer_text_agent)
    workflow.add_node("finalizer_image", finalizer_image_agent)
    workflow.add_node("fanout_writers", lambda s: s)
    workflow.add_node("fanout_illustrators", lambda s: s)
    workflow.add_node("check_writers_completion", lambda s: s)
    workflow.add_node("check_illustrators_completion", lambda s: s)
    
    workflow.set_entry_point("planner")
    
    workflow.add_conditional_edges(
        "planner",
        should_continue,
        {
            "end": END,
            "fanout": "fanout_writers"
        }
    )
    
    # Writers: parallel execution, then check completion
    for i in range(1, 5):
        workflow.add_edge("fanout_writers", f"writer_{i}")
        workflow.add_edge(f"writer_{i}", "check_writers_completion")
    
    workflow.add_conditional_edges(
        "check_writers_completion",
        check_writers_completion,
        {
            "finalize_text": "finalizer_text",
            "wait": "check_writers_completion",
        }
    )
    
    # After text finalized, start illustrators
    workflow.add_edge("finalizer_text", "fanout_illustrators")
    
    # Illustrators: parallel execution, then check completion
    for i in range(1, 5):
        workflow.add_edge("fanout_illustrators", f"illustrator_{i}")
        workflow.add_edge(f"illustrator_{i}", "check_illustrators_completion")
    
    workflow.add_conditional_edges(
        "check_illustrators_completion",
        check_illustrators_completion,
        {
            "finalize_images": "finalizer_image",
            "wait": "check_illustrators_completion",
        }
    )
    
    workflow.add_edge("finalizer_image", END)
    
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


def get_story_graph() -> CompiledStateGraph:
    return create_story_graph()
