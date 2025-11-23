"""
LangGraph workflow graph for story generation
"""
import logging
from functools import partial
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver

from .state import StoryState
from .planner import planner_agent
from .writer import writer_agent
from .illustrator import illustrator_agent
from .finalizer import finalizer_text_agent, finalizer_image_agent

logger = logging.getLogger(__name__)


def should_continue(state: StoryState) -> Literal["fanout", "end"]:
    """Planner decides if workflow should continue or stop"""
    return "end" if state.get("needs_info", False) else "fanout"


def check_completion(state: StoryState) -> Literal["finalize_text", "finalize_images", "wait"]:
    """
    Completion logic:
    1. If all writers completed AND text not finalized -> finalize_text
    2. If text finalized AND all images completed -> finalize_images
    3. Otherwise -> wait (END this round, wait for next event)
    """
    completed_writers = state.get("completed_writers", [])
    completed_image_gens = state.get("completed_image_gens", [])
    finalized_text = state.get("finalized_text")
    
    unique_writers = set(completed_writers)
    unique_image_gens = set(completed_image_gens)
    
    writers_done = len(unique_writers) == 4
    images_done = len(unique_image_gens) == 4
    
    if writers_done and not finalized_text:
        return "finalize_text"
    elif finalized_text and images_done:
        return "finalize_images"
    return "wait"


def create_story_graph() -> CompiledStateGraph:
    """Create and compile the LangGraph workflow"""
    workflow = StateGraph(StoryState)
    
    # Planner
    workflow.add_node("planner", planner_agent)
    
    # Writers (parallel)
    workflow.add_node("writer_1", partial(writer_agent, chapter_id=1))
    workflow.add_node("writer_2", partial(writer_agent, chapter_id=2))
    workflow.add_node("writer_3", partial(writer_agent, chapter_id=3))
    workflow.add_node("writer_4", partial(writer_agent, chapter_id=4))
    
    # Illustrators (parallel)
    workflow.add_node("illustrator_1", partial(illustrator_agent, chapter_id=1))
    workflow.add_node("illustrator_2", partial(illustrator_agent, chapter_id=2))
    workflow.add_node("illustrator_3", partial(illustrator_agent, chapter_id=3))
    workflow.add_node("illustrator_4", partial(illustrator_agent, chapter_id=4))
    
    # Passthrough node used for branching
    workflow.add_node("check_completion", lambda s: s)
    
    # Finalizers (separate nodes for text and images)
    workflow.add_node("finalizer_text", finalizer_text_agent)
    workflow.add_node("finalizer_image", finalizer_image_agent)
    
    workflow.set_entry_point("planner")
    
    # Planner conditional routing
    workflow.add_conditional_edges(
        "planner",
        should_continue,
        {
            "end": END,
            "fanout": "fanout_parallel"
        }
    )
    
    # Fanout passthrough
    workflow.add_node("fanout_parallel", lambda s: s)
    
    # Parallel fanout edges
    for i in range(1, 5):
        workflow.add_edge("fanout_parallel", f"writer_{i}")
        workflow.add_edge("fanout_parallel", f"illustrator_{i}")
    
    # Writers & Illustrators go to completion checker
    for i in range(1, 5):
        workflow.add_edge(f"writer_{i}", "check_completion")
        workflow.add_edge(f"illustrator_{i}", "check_completion")
    
    # Completion logic routing
    workflow.add_conditional_edges(
        "check_completion",
        check_completion,
        {
            "finalize_text": "finalizer_text",
            "finalize_images": "finalizer_image",
            "wait": "check_completion",
        }
    )
    
    # Finalizer_text goes back to check_completion to wait for images
    workflow.add_edge("finalizer_text", "check_completion")
    
    # Finalizer_image completes the workflow
    workflow.add_edge("finalizer_image", END)
    
    # Enable checkpointer for multi-turn execution (required for cycles/reentrant nodes)
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


def get_story_graph() -> CompiledStateGraph:
    return create_story_graph()
