"""
Multi-turn conversation test with mocked Redis
Tests state persistence logic and agent integration
"""
import pytest
import asyncio
import json
import uuid
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock
from app.api.story import (
    handle_websocket_message,
    _prepare_story_state,
    _restore_state,
)
from app.agents.state import StoryState


@pytest.fixture
def test_session_id():
    """Generate a test session ID"""
    return f"test-session-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def mock_redis_state():
    """Mock Redis state storage"""
    return {}


def print_state(state: Dict[str, Any], label: str):
    """Print state for debugging"""
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")
    print(f"Theme: {state.get('theme', '')[:50]}")
    print(f"Intent: {state.get('intent')}")
    print(f"Memory Summary: {(state.get('memory_summary') or '')[:200]}...")
    print(f"Language: {state.get('language')}")
    print(f"Has Story Outline: {bool(state.get('story_outline'))}")
    if state.get('story_outline'):
        outline = state.get('story_outline', {})
        print(f"  Style: {outline.get('style')}")
        print(f"  Characters: {outline.get('characters', [])}")
        print(f"  Chapters: {len(outline.get('chapters', []))}")
    print(f"Chapters Count: {len(state.get('chapters', []))}")
    print(f"Completed Writers: {state.get('completed_writers', [])}")
    print(f"Completed Image Gens: {state.get('completed_image_gens', [])}")


@pytest.mark.asyncio
@patch('app.api.story.manager')
@patch('app.api.story.router_agent')
@patch('app.api.story.process_chat_request')
@patch('app.api.story.process_story_generation')
@patch('app.api.story.load_state_from_redis')
@patch('app.api.story.save_state_to_redis')
async def test_multi_turn_conversation_state_flow(
    mock_save,
    mock_load,
    mock_story_gen,
    mock_chat,
    mock_router,
    mock_manager,
    test_session_id
):
    """
    Test multi-turn conversation state management:
    1. Chat -> preserves all data, updates memory_summary
    2. Story Generate -> clears story data, keeps memory_summary
    3. Regenerate -> preserves outline, clears accumulative fields
    """
    mock_manager.send_to_session = AsyncMock()
    mock_chat.return_value = None
    mock_story_gen.return_value = None
    
    # Track state across turns
    saved_states = {}
    
    def mock_load_impl(session_id: str):
        return saved_states.get(session_id, {})
    
    def mock_save_impl(session_id: str, state: Dict[str, Any]):
        saved_states[session_id] = state.copy()
    
    mock_load.side_effect = mock_load_impl
    mock_save.side_effect = mock_save_impl
    
    print(f"\n{'='*80}")
    print(f"Multi-Turn Conversation State Flow Test")
    print(f"Session ID: {test_session_id}")
    print(f"{'='*80}")
    
    # Turn 1: Chat
    print("\n📨 Turn 1: Chat - 'Hello, how are you?'")
    mock_router.return_value = {
        "intent": "chat",
        "memory_summary": "User greeted: Hello, how are you?"
    }
    
    await handle_websocket_message(test_session_id, "Hello, how are you?")
    
    state1 = saved_states.get(test_session_id, {})
    print_state(state1, "State after Turn 1 (Chat)")
    
    assert state1.get("intent") == "chat"
    assert state1.get("memory_summary") == "User greeted: Hello, how are you?"
    assert mock_chat.called
    
    # Turn 2: Story Generate
    print("\n📨 Turn 2: Story Generate - 'Create a story about a rabbit'")
    mock_router.return_value = {
        "intent": "story_generate",
        "memory_summary": "User greeted: Hello, how are you? User wants: Create a story about a rabbit"
    }
    mock_chat.reset_mock()
    mock_story_gen.reset_mock()
    
    await handle_websocket_message(test_session_id, "Create a story about a rabbit")
    
    state2 = saved_states.get(test_session_id, {})
    print_state(state2, "State after Turn 2 (Story Generate)")
    
    assert state2.get("intent") == "story_generate"
    assert state2.get("theme") == "Create a story about a rabbit"
    assert state2.get("story_outline") is None, "story_generate should clear story_outline"
    assert state2.get("chapters") == [], "story_generate should clear chapters"
    assert state2.get("completed_writers") == [], "story_generate should clear completed_writers"
    assert state2.get("memory_summary") is not None, "memory_summary should be preserved"
    assert mock_story_gen.called
    assert not mock_chat.called
    
    # Simulate story generation completion
    saved_states[test_session_id].update({
        "story_outline": {
            "style": "adventure",
            "characters": ["Rabbit"],
            "chapters": [{"chapter_id": 1, "title": "Chapter 1"}]
        },
        "language": "en",
        "finalized_text": {"chapters": [{"chapter_id": 1, "text": "Once upon a time..."}]},
        "finalized_images": {"chapters": [{"chapter_id": 1, "image_url": "http://example.com/img1.jpg"}]}
    })
    
    # Turn 3: Regenerate (modify story)
    print("\n📨 Turn 3: Regenerate - 'Change the rabbit to a cat'")
    mock_router.return_value = {
        "intent": "regenerate",
        "memory_summary": "User greeted: Hello, how are you? User wants: Create a story about a rabbit. User wants to modify: Change the rabbit to a cat"
    }
    mock_story_gen.reset_mock()
    
    await handle_websocket_message(test_session_id, "Change the rabbit to a cat")
    
    state3 = saved_states.get(test_session_id, {})
    print_state(state3, "State after Turn 3 (Regenerate)")
    
    assert state3.get("intent") == "regenerate"
    assert state3.get("theme") == "Change the rabbit to a cat"
    assert state3.get("story_outline") is not None, "regenerate should preserve story_outline"
    assert state3.get("language") == "en", "regenerate should preserve language"
    assert state3.get("chapters") == [], "regenerate should clear chapters"
    assert state3.get("completed_writers") == [], "regenerate should clear completed_writers"
    assert state3.get("completed_image_gens") == [], "regenerate should clear completed_image_gens"
    assert state3.get("finalized_text") is None, "regenerate should clear finalized_text"
    assert state3.get("finalized_images") is None, "regenerate should clear finalized_images"
    assert state3.get("memory_summary") is not None, "memory_summary should be preserved"
    assert mock_story_gen.called
    
    # Turn 4: Another Story Generate (should clear previous)
    print("\n📨 Turn 4: Story Generate - 'Create a new story about space'")
    mock_router.return_value = {
        "intent": "story_generate",
        "memory_summary": state3.get("memory_summary") + " User wants: Create a new story about space"
    }
    mock_story_gen.reset_mock()
    
    await handle_websocket_message(test_session_id, "Create a new story about space")
    
    state4 = saved_states.get(test_session_id, {})
    print_state(state4, "State after Turn 4 (Story Generate)")
    
    assert state4.get("intent") == "story_generate"
    assert state4.get("story_outline") is None, "story_generate should clear story_outline"
    assert state4.get("chapters") == [], "story_generate should clear chapters"
    assert state4.get("language") == "en", "story_generate should reset language to default"
    assert state4.get("memory_summary") is not None, "memory_summary should be preserved"
    
    print("\n" + "="*80)
    print("✅ Multi-Turn Conversation State Flow Test PASSED")
    print("="*80)
    print("\nKey Validations:")
    print("✅ Chat preserves all data")
    print("✅ story_generate clears all story data")
    print("✅ regenerate preserves outline and language, clears accumulative fields")
    print("✅ memory_summary is preserved across all turns")


@pytest.mark.asyncio
async def test_prepare_story_state_logic():
    """Test _prepare_story_state logic directly"""
    session_id = "test-session"
    
    # Test story_generate
    saved_state = {
        "memory_summary": "Previous",
        "story_outline": {"chapters": [{"id": 1}]},
        "chapters": [{"chapter_id": 1}],
        "completed_writers": [1, 2],
        "language": "zh",
    }
    
    state = _prepare_story_state(saved_state, "new theme", session_id, "story_generate")
    
    assert state["theme"] == "new theme"
    assert state["memory_summary"] == "Previous"
    assert state["story_outline"] is None
    assert state["chapters"] == []
    assert state["completed_writers"] == []
    assert state["language"] == "en"
    
    # Test regenerate with outline
    state = _prepare_story_state(saved_state, "modify theme", session_id, "regenerate")
    
    assert state["theme"] == "modify theme"
    assert state["memory_summary"] == "Previous"
    assert state["story_outline"] == {"chapters": [{"id": 1}]}
    assert state["chapters"] == []
    assert state["completed_writers"] == []
    assert state["language"] == "zh"
    
    print("\n✅ _prepare_story_state logic test PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

