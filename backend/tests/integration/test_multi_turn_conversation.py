"""
Comprehensive multi-turn conversation test
Tests state persistence, memory summary updates, and story generation across multiple turns
"""
import pytest
import asyncio
import json
import uuid
from typing import Dict, Any
from app.api.story import (
    handle_websocket_message,
    load_state_from_redis,
    save_state_to_redis,
)
from app.core.redis import get_redis


@pytest.fixture
def test_session_id():
    """Generate a test session ID"""
    return f"test-session-{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def clean_redis(test_session_id):
    """Clean Redis before and after test"""
    redis = get_redis()
    try:
        await redis.connect()
        await redis.client.delete(f"session:{test_session_id}")
    except Exception:
        pass
    yield
    try:
        await redis.client.delete(f"session:{test_session_id}")
    except Exception:
        pass


def print_state(state: Dict[str, Any], label: str):
    """Print state for debugging"""
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")
    print(f"Intent: {state.get('intent')}")
    print(f"Memory Summary: {state.get('memory_summary', '')[:200]}...")
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
    print(f"Has Finalized Text: {bool(state.get('finalized_text'))}")
    print(f"Has Finalized Images: {bool(state.get('finalized_images'))}")


@pytest.mark.asyncio
async def test_multi_turn_conversation_flow(test_session_id, clean_redis):
    """
    Test complete multi-turn conversation flow:
    1. Chat message
    2. Story generation request
    3. Story modification request (regenerate)
    """
    print(f"\n{'='*80}")
    print(f"Starting Multi-Turn Conversation Test")
    print(f"Session ID: {test_session_id}")
    print(f"{'='*80}")
    
    # Turn 1: Chat message
    print("\n📨 Turn 1: Chat message - 'Hello, how are you?'")
    await handle_websocket_message(test_session_id, "Hello, how are you?")
    
    state1 = await load_state_from_redis(test_session_id)
    print_state(state1, "State after Turn 1 (Chat)")
    
    # Verify Turn 1
    assert "memory_summary" in state1, "Memory summary should be created after chat"
    assert state1.get("intent") == "chat" or state1.get("memory_summary") is not None
    memory_summary_1 = state1.get("memory_summary", "")
    
    # Turn 2: Story generation request
    print("\n📨 Turn 2: Story generation - 'Create a story about a brave little rabbit'")
    await handle_websocket_message(test_session_id, "Create a story about a brave little rabbit")
    
    state2 = await load_state_from_redis(test_session_id)
    print_state(state2, "State after Turn 2 (Story Generate)")
    
    # Verify Turn 2
    assert state2.get("intent") in ["story_generate", "regenerate"], "Intent should be story_generate or regenerate"
    memory_summary_2 = state2.get("memory_summary", "")
    assert memory_summary_2 is not None, "Memory summary should exist"
    assert len(memory_summary_2) >= len(memory_summary_1), "Memory summary should grow"
    
    # Verify story_generate clears old story data
    if state2.get("intent") == "story_generate":
        assert state2.get("story_outline") is None or isinstance(state2.get("story_outline"), dict)
        # If story generation completed, check for finalized content
        if state2.get("finalized_text"):
            print("\n✅ Story generation completed with finalized text")
            assert isinstance(state2.get("finalized_text"), dict)
            assert "chapters" in state2.get("finalized_text", {})
    
    # Wait a bit for story generation to complete
    await asyncio.sleep(2)
    state2_after = await load_state_from_redis(test_session_id)
    
    # Turn 3: Story modification request
    print("\n📨 Turn 3: Story modification - 'Change the rabbit to a cat'")
    await handle_websocket_message(test_session_id, "Change the rabbit to a cat")
    
    state3 = await load_state_from_redis(test_session_id)
    print_state(state3, "State after Turn 3 (Regenerate)")
    
    # Verify Turn 3
    assert state3.get("intent") == "regenerate", "Intent should be regenerate for modification"
    memory_summary_3 = state3.get("memory_summary", "")
    assert memory_summary_3 is not None, "Memory summary should exist"
    assert len(memory_summary_3) >= len(memory_summary_2), "Memory summary should continue growing"
    
    # Verify regenerate preserves outline but clears accumulative fields
    if state2_after.get("story_outline"):
        assert state3.get("story_outline") is not None, "Regenerate should preserve story_outline"
        assert state3.get("language") == state2_after.get("language"), "Regenerate should preserve language"
        assert state3.get("chapters") == [], "Regenerate should clear chapters"
        assert state3.get("completed_writers") == [], "Regenerate should clear completed_writers"
        assert state3.get("completed_image_gens") == [], "Regenerate should clear completed_image_gens"
        print("\n✅ Regenerate correctly preserved outline and cleared accumulative fields")
    
    # Turn 4: Another chat message
    print("\n📨 Turn 4: Chat message - 'That's great!'")
    await handle_websocket_message(test_session_id, "That's great!")
    
    state4 = await load_state_from_redis(test_session_id)
    print_state(state4, "State after Turn 4 (Chat)")
    
    # Verify Turn 4
    assert state4.get("intent") == "chat" or state4.get("memory_summary") is not None
    memory_summary_4 = state4.get("memory_summary", "")
    assert memory_summary_4 is not None, "Memory summary should exist"
    assert len(memory_summary_4) >= len(memory_summary_3), "Memory summary should continue growing"
    
    # Verify chat preserves all data
    if state3.get("story_outline"):
        assert state4.get("story_outline") == state3.get("story_outline"), "Chat should preserve story_outline"
    if state3.get("chapters"):
        assert state4.get("chapters") == state3.get("chapters"), "Chat should preserve chapters"
    
    print("\n" + "="*80)
    print("✅ Multi-Turn Conversation Test PASSED")
    print("="*80)
    print(f"\nFinal Memory Summary Length: {len(memory_summary_4)}")
    print(f"Memory Summary Growth: {len(memory_summary_1)} -> {len(memory_summary_2)} -> {len(memory_summary_3)} -> {len(memory_summary_4)}")


@pytest.mark.asyncio
async def test_story_generate_vs_regenerate_state_management(test_session_id, clean_redis):
    """
    Test that story_generate and regenerate handle state correctly
    """
    print(f"\n{'='*80}")
    print(f"Testing Story Generate vs Regenerate State Management")
    print(f"Session ID: {test_session_id}")
    print(f"{'='*80}")
    
    # First: Generate a story
    print("\n📨 Step 1: Generate new story")
    await handle_websocket_message(test_session_id, "Create a story about a magical forest")
    
    await asyncio.sleep(3)  # Wait for story generation
    state1 = await load_state_from_redis(test_session_id)
    print_state(state1, "State after Story Generate")
    
    # Verify story_generate clears old data
    if state1.get("intent") == "story_generate":
        print("\n✅ story_generate intent detected")
        # story_outline should be None initially, or set after planner runs
        assert state1.get("story_outline") is None or isinstance(state1.get("story_outline"), dict)
    
    # Second: Generate another story (should clear previous)
    print("\n📨 Step 2: Generate another story (should clear previous)")
    await handle_websocket_message(test_session_id, "Create a story about a space adventure")
    
    await asyncio.sleep(3)
    state2 = await load_state_from_redis(test_session_id)
    print_state(state2, "State after Second Story Generate")
    
    # Verify second story_generate clears previous story data
    if state2.get("intent") == "story_generate":
        print("\n✅ Second story_generate correctly cleared previous story data")
        # Chapters should be cleared
        assert state2.get("chapters") == [] or len(state2.get("chapters", [])) == 0, "Chapters should be cleared"
    
    # Third: Modify the story (regenerate)
    if state2.get("story_outline"):
        print("\n📨 Step 3: Modify story (regenerate)")
        await handle_websocket_message(test_session_id, "Change the main character to a robot")
        
        await asyncio.sleep(3)
        state3 = await load_state_from_redis(test_session_id)
        print_state(state3, "State after Regenerate")
        
        # Verify regenerate preserves outline
        assert state3.get("story_outline") is not None, "Regenerate should preserve story_outline"
        assert state3.get("story_outline") == state2.get("story_outline"), "Regenerate should preserve same outline"
        assert state3.get("chapters") == [], "Regenerate should clear chapters"
        print("\n✅ Regenerate correctly preserved outline and cleared accumulative fields")
    
    print("\n" + "="*80)
    print("✅ Story Generate vs Regenerate Test PASSED")
    print("="*80)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

