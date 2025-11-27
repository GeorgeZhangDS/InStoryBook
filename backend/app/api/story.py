"""
Story generation message handling for WebSocket
"""
import json
import logging
from typing import Dict, Any

from app.agents.state import StoryState
from app.agents.conversation import router_agent
from app.agents.workflow import get_story_graph
from app.core.redis import get_redis
from app.api.websocket import manager, create_ws_message

logger = logging.getLogger(__name__)


def create_initial_state(theme: str, session_id: str) -> StoryState:
    """Create initial state for story generation"""
    return {
        "theme": theme,
        "memory_summary": None,
        "intent": None,
        "language": "en",
        "story_outline": None,
        "needs_info": False,
        "missing_fields": None,
        "suggestions": None,
        "chapters": [],
        "completed_writers": [],
        "completed_image_gens": [],
        "finalized_text": None,
        "finalized_images": None,
        "session_id": session_id,
    }


async def load_state_from_redis(session_id: str) -> Dict[str, Any]:
    """Load state from Redis"""
    try:
        redis = get_redis()
        data = await redis.client.get(f"session:{session_id}")
        return json.loads(data) if data else {}
    except Exception as e:
        logger.error(f"Error loading state from Redis: {e}")
        return {}


async def save_state_to_redis(session_id: str, state: Dict[str, Any]):
    """Save state to Redis"""
    try:
        redis = get_redis()
        serializable_state = {
            k: v for k, v in state.items() 
            if v is not None and isinstance(v, (dict, list, str, int, float, bool))
        }
        await redis.client.setex(
            f"session:{session_id}",
            86400,
            json.dumps(serializable_state, ensure_ascii=False)
        )
    except Exception as e:
        logger.error(f"Error saving state to Redis: {e}")


async def process_chat_request(session_id: str, state: StoryState):
    """Process chat request"""
    from app.agents.conversation import chat_agent
    
    try:
        await manager.send_to_session(
            create_ws_message("agent_started", session_id, {"agent": "chat", "status": "running"}),
            session_id
        )
        
        chat_result = await chat_agent(state)
        state.update({"memory_summary": chat_result.get("memory_summary")})
        await save_state_to_redis(session_id, state)
        
        await manager.send_to_session(
            create_ws_message("chat_response", session_id, {
                "response": chat_result.get("chat_response"),
                "memory_summary": chat_result.get("memory_summary")
            }),
            session_id
        )
        
        await manager.send_to_session(
            create_ws_message("agent_completed", session_id, {"agent": "chat", "status": "completed"}),
            session_id
        )
        
        await manager.send_to_session(
            create_ws_message("pipeline_completed", session_id, {"status": "completed"}),
            session_id
        )
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        await manager.send_to_session(
            create_ws_message("error", session_id, {"agent": "chat", "error": str(e)}),
            session_id
        )


async def process_story_generation(session_id: str, state: StoryState):
    """Process story generation request"""
    try:
        await manager.send_to_session(
            create_ws_message("agent_started", session_id, {"agent": "planner", "status": "running"}),
            session_id
        )
        
        graph = get_story_graph()
        config = {"configurable": {"thread_id": session_id}}
        final_state = state.copy()
        writer_started_sent = False
        writer_completed_count = 0
        illustrator_started_sent = False
        illustrator_completed_count = 0
        
        async for event in graph.astream(state, config):
            for node_name, node_output in event.items():
                if isinstance(node_output, dict):
                    final_state.update(node_output)
                
                if node_name == "planner":
                    await manager.send_to_session(
                        create_ws_message("agent_completed", session_id, {"agent": "planner", "status": "completed"}),
                        session_id
                    )
                    if not writer_started_sent:
                        await manager.send_to_session(
                            create_ws_message("agent_started", session_id, {"agent": "writer", "status": "running"}),
                            session_id
                        )
                        writer_started_sent = True
                
                elif node_name.startswith("writer_"):
                    chapter_id = int(node_name.split("_")[1])
                    if node_output and isinstance(node_output, dict) and "completed_writers" in node_output:
                        writer_completed_count += 1
                        await manager.send_to_session(
                            create_ws_message("agent_completed", session_id, {"agent": f"writer_{chapter_id}", "status": "completed", "chapter_id": chapter_id}),
                            session_id
                        )
                        if writer_completed_count == 4:
                            await manager.send_to_session(
                                create_ws_message("agent_completed", session_id, {"agent": "writer", "status": "completed"}),
                                session_id
                            )
                
                elif node_name == "finalizer_text":
                    finalized_text = node_output.get("finalized_text", {}) if isinstance(node_output, dict) else {}
                    chapters = finalized_text.get("chapters", [])
                    if chapters:
                        await manager.send_to_session(
                            create_ws_message("finalizer_text", session_id, {"chapters": chapters}),
                            session_id
                        )
                        logger.info(f"finalizer_text event sent with {len(chapters)} chapters")
                    # Start illustrators after text is finalized
                    if not illustrator_started_sent:
                        await manager.send_to_session(
                            create_ws_message("agent_started", session_id, {"agent": "illustrator", "status": "running"}),
                            session_id
                        )
                        illustrator_started_sent = True
                
                elif node_name.startswith("illustrator_"):
                    chapter_id = int(node_name.split("_")[1])
                    if node_output and isinstance(node_output, dict) and "completed_image_gens" in node_output:
                        illustrator_completed_count += 1
                        await manager.send_to_session(
                            create_ws_message("agent_completed", session_id, {"agent": f"illustrator_{chapter_id}", "status": "completed", "chapter_id": chapter_id}),
                            session_id
                        )
                        if illustrator_completed_count == 4:
                            await manager.send_to_session(
                                create_ws_message("agent_completed", session_id, {"agent": "illustrator", "status": "completed"}),
                                session_id
                            )
                
                elif node_name == "finalizer_image":
                    finalized_images = node_output.get("finalized_images", {}) if isinstance(node_output, dict) else {}
                    chapters = finalized_images.get("chapters", [])
                    if chapters:
                        await manager.send_to_session(
                            create_ws_message("finalizer_image", session_id, {"chapters": chapters}),
                            session_id
                        )
                        logger.info(f"finalizer_image event sent with {len(chapters)} chapters")
                    await save_state_to_redis(session_id, final_state)
        
        await manager.send_to_session(
            create_ws_message("pipeline_completed", session_id, {"status": "completed"}),
            session_id
        )
    except Exception as e:
        logger.error(f"Story generation error: {e}")
        await manager.send_to_session(
            create_ws_message("error", session_id, {"agent": "story_generation", "error": str(e)}),
            session_id
        )


def _restore_state(saved_state: Dict[str, Any], theme: str, session_id: str) -> StoryState:
    """Restore state from saved data for chat (preserve all data)"""
    if saved_state:
        return {
            "theme": theme,
            "memory_summary": saved_state.get("memory_summary"),
            "intent": saved_state.get("intent"),
            "language": saved_state.get("language", "en"),
            "story_outline": saved_state.get("story_outline"),
            "needs_info": saved_state.get("needs_info", False),
            "missing_fields": saved_state.get("missing_fields"),
            "suggestions": saved_state.get("suggestions"),
            "chapters": saved_state.get("chapters", []),
            "completed_writers": saved_state.get("completed_writers", []),
            "completed_image_gens": saved_state.get("completed_image_gens", []),
            "finalized_text": saved_state.get("finalized_text"),
            "finalized_images": saved_state.get("finalized_images"),
            "session_id": session_id,
        }
    return create_initial_state(theme, session_id)


def _prepare_story_state(
    saved_state: Dict[str, Any], 
    theme: str, 
    session_id: str,
    intent: str
) -> StoryState:
    """Prepare Story Graph state, avoid data accumulation"""
    base_state = {
        "theme": theme,
        "memory_summary": saved_state.get("memory_summary") if saved_state else None,
        "session_id": session_id,
        "intent": None,
        "needs_info": False,
        "missing_fields": None,
        "suggestions": None,
        "chapters": [],
        "completed_writers": [],
        "completed_image_gens": [],
        "finalized_text": None,
        "finalized_images": None,
    }
    
    if intent == "regenerate" and saved_state and saved_state.get("story_outline"):
        base_state.update({
            "story_outline": saved_state.get("story_outline"),
            "language": saved_state.get("language", "en"),
        })
    else:
        base_state.update({
            "story_outline": None,
            "language": "en",
        })
    
    return base_state


async def handle_websocket_message(session_id: str, theme: str):
    """Handle message from WebSocket"""
    try:
        saved_state = await load_state_from_redis(session_id)
        
        router_result = await router_agent({
            "theme": theme,
            "memory_summary": saved_state.get("memory_summary") if saved_state else None,
            "session_id": session_id,
        })
        
        intent = router_result.get("intent", "story_generate")
        
        if intent in ["story_generate", "regenerate"]:
            state = _prepare_story_state(saved_state, theme, session_id, intent)
            state.update(router_result)
            await save_state_to_redis(session_id, state)
            await process_story_generation(session_id, state)
        elif intent == "chat":
            state = _restore_state(saved_state, theme, session_id)
            state.update(router_result)
            await save_state_to_redis(session_id, state)
            await process_chat_request(session_id, state)
        else:
            await manager.send_to_session(
                create_ws_message("error", session_id, {"error": f"Unsupported intent: {intent}"}),
                session_id
            )
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await manager.send_to_session(
            create_ws_message("error", session_id, {"error": str(e)}),
            session_id
        )
