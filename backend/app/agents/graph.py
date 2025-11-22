"""
LangGraph workflow graph for story generation
"""
import logging
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledGraph

from .state import StoryState
from .planner import planner_agent
from .writer import writer_agent
from .illustrator import illustrator_agent
from .finalizer import finalizer_agent

logger = logging.getLogger(__name__)


def should_continue(state: StoryState) -> Literal["fanout", "end"]:
    """Check if planner needs more info or can continue"""
    if state.get("needs_info", False):
        return "end"
    return "fanout"


def check_completion(state: StoryState) -> Literal["finalize_text", "finalize_images", "wait"]:
    """Check completion status and route to finalizer if needed"""
    completed_writers = state.get("completed_writers", [])
    completed_image_gens = state.get("completed_image_gens", [])
    text_finalized = state.get("text_finalized", False)
    
    writers_done = len(completed_writers) == 4
    images_done = len(completed_image_gens) == 4
    
    if writers_done and not images_done and not text_finalized:
        return "finalize_text"
    elif images_done:
        return "finalize_images"
    return "wait"


def create_story_graph() -> CompiledGraph:
    """Create and compile the LangGraph workflow"""
    workflow = StateGraph(StoryState)
    
    workflow.add_node("planner", planner_agent)
    
    workflow.add_node("writer_1", lambda state: writer_agent(state, 1))
    workflow.add_node("writer_2", lambda state: writer_agent(state, 2))
    workflow.add_node("writer_3", lambda state: writer_agent(state, 3))
    workflow.add_node("writer_4", lambda state: writer_agent(state, 4))
    
    workflow.add_node("illustrator_1", lambda state: illustrator_agent(state, 1))
    workflow.add_node("illustrator_2", lambda state: illustrator_agent(state, 2))
    workflow.add_node("illustrator_3", lambda state: illustrator_agent(state, 3))
    workflow.add_node("illustrator_4", lambda state: illustrator_agent(state, 4))
    
    
    # Passthrough Node
    workflow.add_node("check_completion", lambda state: state)
    
    workflow.add_node("finalizer", finalizer_agent)
    
    workflow.set_entry_point("planner")
    
    workflow.add_conditional_edges(
        "planner",
        should_continue,
        {
            "end": END,
            "fanout": "fanout_parallel"
        }
    )
    
    # Passthrough Node
    workflow.add_node("fanout_parallel", lambda state: state)
    
    workflow.add_edge("fanout_parallel", "writer_1")
    workflow.add_edge("fanout_parallel", "writer_2")
    workflow.add_edge("fanout_parallel", "writer_3")
    workflow.add_edge("fanout_parallel", "writer_4")
    workflow.add_edge("fanout_parallel", "illustrator_1")
    workflow.add_edge("fanout_parallel", "illustrator_2")
    workflow.add_edge("fanout_parallel", "illustrator_3")
    workflow.add_edge("fanout_parallel", "illustrator_4")
    
    workflow.add_edge("writer_1", "check_completion")
    workflow.add_edge("writer_2", "check_completion")
    workflow.add_edge("writer_3", "check_completion")
    workflow.add_edge("writer_4", "check_completion")
    workflow.add_edge("illustrator_1", "check_completion")
    workflow.add_edge("illustrator_2", "check_completion")
    workflow.add_edge("illustrator_3", "check_completion")
    workflow.add_edge("illustrator_4", "check_completion")
    
    workflow.add_conditional_edges(
        "check_completion",
        check_completion,
        {
            "finalize_text": "finalizer",
            "finalize_images": "finalizer",
            "wait": END
        }
    )
    
    workflow.add_edge("finalizer", END)
    
    return workflow.compile()


def get_story_graph() -> CompiledGraph:
    """Get the compiled story generation graph"""
    return create_story_graph()

