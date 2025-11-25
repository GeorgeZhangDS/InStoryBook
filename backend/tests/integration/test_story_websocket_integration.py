"""
Comprehensive integration tests for story.py and websocket.py
Tests WebSocket communication, state management, and agent integration
"""
import pytest
import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from app.api.story import (
    handle_websocket_message,
    load_state_from_redis,
    save_state_to_redis,
    _prepare_story_state,
    _restore_state,
    create_initial_state,
    process_chat_request,
    process_story_generation,
)
from app.api.websocket import (
    ConnectionManager,
    create_ws_message,
    manager,
)
from app.agents.state import StoryState
from app.core.redis import get_redis


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket"""
    ws = AsyncMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_text = AsyncMock()
    return ws


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


@pytest.mark.asyncio
class TestStateManagement:
    """Test state management functions"""
    
    async def test_create_initial_state(self):
        """Test creating initial state"""
        state = create_initial_state("test theme", "session-123")
        
        assert state["theme"] == "test theme"
        assert state["session_id"] == "session-123"
        assert state["memory_summary"] is None
        assert state["intent"] is None
        assert state["story_outline"] is None
        assert state["chapters"] == []
        assert state["completed_writers"] == []
        assert state["completed_image_gens"] == []
    
    async def test_prepare_story_state_story_generate(self, test_session_id):
        """Test _prepare_story_state for story_generate intent"""
        saved_state = {
            "memory_summary": "Previous conversation",
            "story_outline": {"chapters": [{"id": 1}]},
            "chapters": [{"chapter_id": 1, "content": "old"}],
            "completed_writers": [1, 2],
            "language": "zh",
        }
        
        state = _prepare_story_state(saved_state, "new theme", test_session_id, "story_generate")
        
        assert state["theme"] == "new theme"
        assert state["memory_summary"] == "Previous conversation"
        assert state["story_outline"] is None
        assert state["chapters"] == []
        assert state["completed_writers"] == []
        assert state["completed_image_gens"] == []
        assert state["language"] == "en"
        assert state["session_id"] == test_session_id
    
    async def test_prepare_story_state_regenerate(self, test_session_id):
        """Test _prepare_story_state for regenerate intent"""
        saved_state = {
            "memory_summary": "Previous conversation",
            "story_outline": {"chapters": [{"id": 1}]},
            "chapters": [{"chapter_id": 1, "content": "old"}],
            "completed_writers": [1, 2],
            "language": "zh",
        }
        
        state = _prepare_story_state(saved_state, "modify theme", test_session_id, "regenerate")
        
        assert state["theme"] == "modify theme"
        assert state["memory_summary"] == "Previous conversation"
        assert state["story_outline"] == {"chapters": [{"id": 1}]}
        assert state["chapters"] == []
        assert state["completed_writers"] == []
        assert state["completed_image_gens"] == []
        assert state["language"] == "zh"
        assert state["session_id"] == test_session_id
    
    async def test_prepare_story_state_regenerate_no_outline(self, test_session_id):
        """Test _prepare_story_state for regenerate intent without existing outline"""
        saved_state = {
            "memory_summary": "Previous conversation",
            "chapters": [{"chapter_id": 1}],
        }
        
        state = _prepare_story_state(saved_state, "new theme", test_session_id, "regenerate")
        
        assert state["story_outline"] is None
        assert state["language"] == "en"
    
    async def test_restore_state(self, test_session_id):
        """Test _restore_state for chat intent"""
        saved_state = {
            "memory_summary": "Previous conversation",
            "story_outline": {"chapters": [{"id": 1}]},
            "chapters": [{"chapter_id": 1}],
            "language": "zh",
        }
        
        state = _restore_state(saved_state, "chat theme", test_session_id)
        
        assert state["theme"] == "chat theme"
        assert state["memory_summary"] == "Previous conversation"
        assert state["story_outline"] == {"chapters": [{"id": 1}]}
        assert state["chapters"] == [{"chapter_id": 1}]
        assert state["language"] == "zh"
        assert state["session_id"] == test_session_id
    
    async def test_restore_state_empty(self, test_session_id):
        """Test _restore_state with empty saved state"""
        state = _restore_state({}, "new theme", test_session_id)
        
        assert state["theme"] == "new theme"
        assert state["session_id"] == test_session_id
        assert state["chapters"] == []


@pytest.mark.asyncio
class TestRedisStateManagement:
    """Test Redis state persistence"""
    
    @pytest.mark.skipif(
        not (bool(pytest.importorskip("os").getenv("REDIS_URL")) or 
             bool(pytest.importorskip("os").getenv("REDIS_HOST"))),
        reason="Redis connection required"
    )
    async def test_save_and_load_state(self, test_session_id, clean_redis):
        """Test saving and loading state from Redis"""
        test_state = {
            "theme": "test theme",
            "memory_summary": "test summary",
            "story_outline": {"chapters": [{"id": 1}]},
            "chapters": [{"chapter_id": 1, "content": "test"}],
            "session_id": test_session_id,
        }
        
        await save_state_to_redis(test_session_id, test_state)
        loaded_state = await load_state_from_redis(test_session_id)
        
        assert loaded_state["theme"] == "test theme"
        assert loaded_state["memory_summary"] == "test summary"
        assert loaded_state["story_outline"] == {"chapters": [{"id": 1}]}
        assert len(loaded_state["chapters"]) == 1
    
    async def test_load_state_not_found(self, test_session_id, clean_redis):
        """Test loading non-existent state"""
        loaded_state = await load_state_from_redis(test_session_id)
        assert loaded_state == {}
    
    @pytest.mark.skipif(
        not (bool(pytest.importorskip("os").getenv("REDIS_URL")) or 
             bool(pytest.importorskip("os").getenv("REDIS_HOST"))),
        reason="Redis connection required"
    )
    async def test_save_state_serialization(self, test_session_id, clean_redis):
        """Test state serialization handles all types"""
        test_state = {
            "string": "test",
            "int": 123,
            "float": 45.67,
            "bool": True,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
            "none": None,
        }
        
        await save_state_to_redis(test_session_id, test_state)
        loaded_state = await load_state_from_redis(test_session_id)
        
        assert loaded_state["string"] == "test"
        assert loaded_state["int"] == 123
        assert loaded_state["float"] == 45.67
        assert loaded_state["bool"] is True
        assert loaded_state["list"] == [1, 2, 3]
        assert loaded_state["dict"] == {"key": "value"}
        assert "none" not in loaded_state


@pytest.mark.asyncio
class TestWebSocketConnectionManager:
    """Test WebSocket connection management"""
    
    async def test_connection_manager_connect(self, mock_websocket):
        """Test connecting a WebSocket"""
        conn_manager = ConnectionManager()
        connection_id = "conn-1"
        session_id = "session-1"
        
        await conn_manager.connect(mock_websocket, connection_id, session_id)
        
        mock_websocket.accept.assert_called_once()
        assert connection_id in conn_manager.active_connections
        assert connection_id in conn_manager.session_connections[session_id]
    
    async def test_connection_manager_disconnect(self, mock_websocket):
        """Test disconnecting a WebSocket"""
        conn_manager = ConnectionManager()
        connection_id = "conn-1"
        session_id = "session-1"
        
        await conn_manager.connect(mock_websocket, connection_id, session_id)
        conn_manager.disconnect(connection_id, session_id)
        
        assert connection_id not in conn_manager.active_connections
        assert session_id not in conn_manager.session_connections
    
    async def test_send_to_session(self, mock_websocket):
        """Test sending message to session"""
        conn_manager = ConnectionManager()
        connection_id = "conn-1"
        session_id = "session-1"
        
        await conn_manager.connect(mock_websocket, connection_id, session_id)
        
        message = {"type": "test", "data": "test"}
        await conn_manager.send_to_session(message, session_id)
        
        mock_websocket.send_json.assert_called_once_with(message)
    
    async def test_send_to_session_multiple_connections(self, mock_websocket):
        """Test sending to session with multiple connections"""
        conn_manager = ConnectionManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        
        await conn_manager.connect(ws1, "conn-1", "session-1")
        await conn_manager.connect(ws2, "conn-2", "session-1")
        
        message = {"type": "test"}
        await conn_manager.send_to_session(message, "session-1")
        
        assert ws1.send_json.call_count == 1
        assert ws2.send_json.call_count == 1


@pytest.mark.asyncio
class TestWebSocketMessageFormat:
    """Test WebSocket message format"""
    
    def test_create_ws_message(self):
        """Test creating WebSocket message"""
        message = create_ws_message("test_type", "session-123", {"key": "value"})
        
        assert message["type"] == "test_type"
        assert message["session_id"] == "session-123"
        assert message["data"] == {"key": "value"}
        assert "event_id" in message
        assert "timestamp" in message


@pytest.mark.asyncio
class TestChatRequestProcessing:
    """Test chat request processing"""
    
    @patch('app.api.story.manager')
    @patch('app.api.story.save_state_to_redis')
    async def test_process_chat_request_sends_messages(
        self, mock_save, mock_manager, test_session_id
    ):
        """Test that process_chat_request sends WebSocket messages"""
        with patch('app.agents.conversation.chat.chat_agent', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {
                "chat_response": "Hello!",
                "memory_summary": "Updated summary"
            }
            mock_manager.send_to_session = AsyncMock()
            
            state = create_initial_state("Hello", test_session_id)
            await process_chat_request(test_session_id, state)
            
            assert mock_manager.send_to_session.call_count >= 2
            
            calls = [call[0][0] for call in mock_manager.send_to_session.call_args_list]
            message_types = [call["type"] for call in calls]
            assert "agent_started" in message_types
            assert "chat_response" in message_types or "agent_completed" in message_types


@pytest.mark.asyncio
class TestStoryGenerationProcessing:
    """Test story generation processing"""
    
    @patch('app.api.story.manager')
    @patch('app.api.story.get_story_graph')
    @patch('app.api.story.save_state_to_redis')
    async def test_process_story_generation_success(
        self, mock_save, mock_graph, mock_manager, test_session_id
    ):
        """Test successful story generation processing"""
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        
        async def mock_astream(state, config):
            yield {
                "planner": {"story_outline": {"chapters": []}},
                "writer_1": {"chapters": [{"chapter_id": 1}]},
            }
            yield {
                "finalizer_text": {
                    "finalized_text": {"chapters": [{"chapter_id": 1, "text": "test"}]}
                }
            }
            yield {
                "finalizer_image": {
                    "finalized_images": {"chapters": [{"chapter_id": 1, "image_url": "url"}]}
                }
            }
        
        mock_graph_instance.astream = mock_astream
        mock_manager.send_to_session = AsyncMock()
        
        state = create_initial_state("Test story", test_session_id)
        state["story_outline"] = {"chapters": []}
        
        await process_story_generation(test_session_id, state)
        
        assert mock_manager.send_to_session.call_count >= 3
        
        calls = [call[0][0] for call in mock_manager.send_to_session.call_args_list]
        assert any(call["type"] == "agent_started" for call in calls)
        assert any(call["type"] == "finalizer_text" for call in calls)
        assert any(call["type"] == "finalizer_image" for call in calls)
        assert any(call["type"] == "pipeline_completed" for call in calls)
        
        assert mock_save.called
    
    @patch('app.api.story.manager')
    @patch('app.api.story.get_story_graph')
    async def test_process_story_generation_error(
        self, mock_graph, mock_manager, test_session_id
    ):
        """Test story generation error handling"""
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_graph_instance.astream.side_effect = Exception("Graph error")
        mock_manager.send_to_session = AsyncMock()
        
        state = create_initial_state("Test story", test_session_id)
        await process_story_generation(test_session_id, state)
        
        error_calls = [
            call for call in mock_manager.send_to_session.call_args_list
            if call[0][0]["type"] == "error"
        ]
        assert len(error_calls) > 0


@pytest.mark.asyncio
class TestWebSocketMessageHandling:
    """Test WebSocket message handling with agent integration"""
    
    @patch('app.api.story.router_agent')
    @patch('app.api.story.process_chat_request')
    @patch('app.api.story.load_state_from_redis')
    @patch('app.api.story.save_state_to_redis')
    async def test_handle_websocket_message_chat(
        self, mock_save, mock_load, mock_chat, mock_router, test_session_id, clean_redis
    ):
        """Test handling chat intent message"""
        mock_load.return_value = {"memory_summary": "Previous"}
        mock_router.return_value = {
            "intent": "chat",
            "memory_summary": "Updated summary"
        }
        mock_chat.return_value = None
        
        await handle_websocket_message(test_session_id, "Hello, how are you?")
        
        mock_router.assert_called_once()
        mock_chat.assert_called_once()
        assert mock_save.called
    
    @patch('app.api.story.router_agent')
    @patch('app.api.story.process_story_generation')
    @patch('app.api.story.load_state_from_redis')
    @patch('app.api.story.save_state_to_redis')
    async def test_handle_websocket_message_story_generate(
        self, mock_save, mock_load, mock_story, mock_router, test_session_id, clean_redis
    ):
        """Test handling story_generate intent message"""
        mock_load.return_value = {}
        mock_router.return_value = {
            "intent": "story_generate",
            "memory_summary": "New summary"
        }
        mock_story.return_value = None
        
        await handle_websocket_message(test_session_id, "Create a story about a brave rabbit")
        
        mock_router.assert_called_once()
        mock_story.assert_called_once()
        
        call_args = mock_story.call_args[0]
        state = call_args[1]
        assert state["theme"] == "Create a story about a brave rabbit"
        assert state["story_outline"] is None
        assert state["chapters"] == []
        assert state["intent"] == "story_generate"
    
    @patch('app.api.story.router_agent')
    @patch('app.api.story.process_story_generation')
    @patch('app.api.story.load_state_from_redis')
    @patch('app.api.story.save_state_to_redis')
    async def test_handle_websocket_message_regenerate(
        self, mock_save, mock_load, mock_story, mock_router, test_session_id, clean_redis
    ):
        """Test handling regenerate intent message"""
        existing_outline = {
            "style": "adventure",
            "characters": ["Rabbit"],
            "chapters": [{"chapter_id": 1, "title": "Chapter 1"}]
        }
        mock_load.return_value = {
            "memory_summary": "Previous",
            "story_outline": existing_outline,
            "language": "en",
            "chapters": [{"chapter_id": 1, "content": "old"}],
            "completed_writers": [1, 2],
        }
        mock_router.return_value = {
            "intent": "regenerate",
            "memory_summary": "Updated summary"
        }
        mock_story.return_value = None
        
        await handle_websocket_message(test_session_id, "Change the main character to a cat")
        
        mock_router.assert_called_once()
        mock_story.assert_called_once()
        
        call_args = mock_story.call_args[0]
        state = call_args[1]
        assert state["theme"] == "Change the main character to a cat"
        assert state["story_outline"] == existing_outline
        assert state["language"] == "en"
        assert state["chapters"] == []
        assert state["completed_writers"] == []
        assert state["intent"] == "regenerate"
    
    @patch('app.api.story.manager')
    @patch('app.api.story.router_agent')
    @patch('app.api.story.load_state_from_redis')
    async def test_handle_websocket_message_unsupported_intent(
        self, mock_load, mock_router, mock_manager, test_session_id, clean_redis
    ):
        """Test handling unsupported intent"""
        mock_load.return_value = {}
        mock_router.return_value = {
            "intent": "unknown_intent",
            "memory_summary": "Summary"
        }
        mock_manager.send_to_session = AsyncMock()
        
        await handle_websocket_message(test_session_id, "Test message")
        
        error_calls = [
            call for call in mock_manager.send_to_session.call_args_list
            if call[0][0]["type"] == "error"
        ]
        assert len(error_calls) > 0
    
    @patch('app.api.story.manager')
    @patch('app.api.story.load_state_from_redis')
    async def test_handle_websocket_message_error(
        self, mock_load, mock_manager, test_session_id, clean_redis
    ):
        """Test error handling in message processing"""
        mock_load.side_effect = Exception("Redis error")
        mock_manager.send_to_session = AsyncMock()
        
        await handle_websocket_message(test_session_id, "Test message")
        
        error_calls = [
            call for call in mock_manager.send_to_session.call_args_list
            if call[0][0]["type"] == "error"
        ]
        assert len(error_calls) > 0


@pytest.mark.asyncio
class TestDataAccumulationPrevention:
    """Test that data accumulation is prevented"""
    
    @patch('app.api.story.router_agent')
    @patch('app.api.story.process_story_generation')
    @patch('app.api.story.load_state_from_redis')
    @patch('app.api.story.save_state_to_redis')
    async def test_story_generate_clears_old_data(
        self, mock_save, mock_load, mock_story, mock_router, test_session_id, clean_redis
    ):
        """Test that story_generate clears old story data"""
        mock_load.return_value = {
            "memory_summary": "Previous",
            "story_outline": {"chapters": [{"id": 1}]},
            "chapters": [{"chapter_id": 1}, {"chapter_id": 2}],
            "completed_writers": [1, 2, 3, 4],
            "completed_image_gens": [1, 2, 3, 4],
            "finalized_text": {"chapters": []},
            "finalized_images": {"chapters": []},
        }
        mock_router.return_value = {
            "intent": "story_generate",
            "memory_summary": "New summary"
        }
        
        await handle_websocket_message(test_session_id, "New story")
        
        call_args = mock_story.call_args[0]
        state = call_args[1]
        
        assert state["story_outline"] is None
        assert state["chapters"] == []
        assert state["completed_writers"] == []
        assert state["completed_image_gens"] == []
        assert state["finalized_text"] is None
        assert state["finalized_images"] is None
        assert state["memory_summary"] == "New summary"
    
    @patch('app.api.story.router_agent')
    @patch('app.api.story.process_story_generation')
    @patch('app.api.story.load_state_from_redis')
    @patch('app.api.story.save_state_to_redis')
    async def test_regenerate_preserves_outline_clears_accumulative(
        self, mock_save, mock_load, mock_story, mock_router, test_session_id, clean_redis
    ):
        """Test that regenerate preserves outline but clears accumulative fields"""
        existing_outline = {"chapters": [{"chapter_id": 1}]}
        mock_load.return_value = {
            "memory_summary": "Previous",
            "story_outline": existing_outline,
            "language": "zh",
            "chapters": [{"chapter_id": 1}, {"chapter_id": 2}],
            "completed_writers": [1, 2, 3, 4],
            "completed_image_gens": [1, 2, 3, 4],
        }
        mock_router.return_value = {
            "intent": "regenerate",
            "memory_summary": "Updated summary"
        }
        
        await handle_websocket_message(test_session_id, "Modify story")
        
        call_args = mock_story.call_args[0]
        state = call_args[1]
        
        assert state["story_outline"] == existing_outline
        assert state["language"] == "zh"
        assert state["chapters"] == []
        assert state["completed_writers"] == []
        assert state["completed_image_gens"] == []
        assert state["memory_summary"] == "Updated summary"
    
    @patch('app.api.story.router_agent')
    @patch('app.api.story.process_chat_request')
    @patch('app.api.story.load_state_from_redis')
    @patch('app.api.story.save_state_to_redis')
    async def test_chat_preserves_all_data(
        self, mock_save, mock_load, mock_chat, mock_router, test_session_id, clean_redis
    ):
        """Test that chat preserves all data"""
        existing_data = {
            "memory_summary": "Previous",
            "story_outline": {"chapters": [{"id": 1}]},
            "chapters": [{"chapter_id": 1}],
            "completed_writers": [1, 2],
            "language": "zh",
        }
        mock_load.return_value = existing_data
        mock_router.return_value = {
            "intent": "chat",
            "memory_summary": "Updated summary"
        }
        
        await handle_websocket_message(test_session_id, "Hello")
        
        call_args = mock_chat.call_args[0]
        state = call_args[1]
        
        assert state["story_outline"] == existing_data["story_outline"]
        assert state["chapters"] == existing_data["chapters"]
        assert state["completed_writers"] == existing_data["completed_writers"]
        assert state["language"] == existing_data["language"]
        assert state["memory_summary"] == "Updated summary"


@pytest.mark.asyncio
class TestEndToEndFlow:
    """Test end-to-end flows with real agent integration"""
    
    @pytest.mark.skipif(
        not (bool(pytest.importorskip("os").getenv("AWS_ACCESS_KEY")) and 
             bool(pytest.importorskip("os").getenv("OPENAI_API_KEY"))),
        reason="API keys required"
    )
    async def test_complete_chat_flow(self, test_session_id, clean_redis):
        """Test complete chat flow with real agents"""
        await handle_websocket_message(test_session_id, "Hello, how are you?")
        
        state = await load_state_from_redis(test_session_id)
        assert "memory_summary" in state
        assert state.get("intent") == "chat" or state.get("memory_summary") is not None
    
    @pytest.mark.skipif(
        not (bool(pytest.importorskip("os").getenv("AWS_ACCESS_KEY")) and 
             bool(pytest.importorskip("os").getenv("OPENAI_API_KEY"))),
        reason="API keys required"
    )
    async def test_complete_story_generate_flow(self, test_session_id, clean_redis):
        """Test complete story generation flow with real agents"""
        await handle_websocket_message(
            test_session_id, 
            "Create a story about a brave little rabbit who learns to fly"
        )
        
        state = await load_state_from_redis(test_session_id)
        assert state.get("intent") in ["story_generate", "regenerate"]
        assert state.get("story_outline") is None or isinstance(state.get("story_outline"), dict)
    
    @pytest.mark.skipif(
        not (bool(pytest.importorskip("os").getenv("AWS_ACCESS_KEY")) and 
             bool(pytest.importorskip("os").getenv("OPENAI_API_KEY"))),
        reason="API keys required"
    )
    async def test_multi_turn_conversation(self, test_session_id, clean_redis):
        """Test multi-turn conversation flow"""
        await handle_websocket_message(test_session_id, "Hello")
        
        state1 = await load_state_from_redis(test_session_id)
        memory_summary_1 = state1.get("memory_summary")
        
        await handle_websocket_message(test_session_id, "Create a story about a cat")
        
        state2 = await load_state_from_redis(test_session_id)
        memory_summary_2 = state2.get("memory_summary")
        
        assert memory_summary_2 is not None
        if memory_summary_1:
            assert len(memory_summary_2) >= len(memory_summary_1)
        
        await handle_websocket_message(test_session_id, "Change the cat to a dog")
        
        state3 = await load_state_from_redis(test_session_id)
        assert state3.get("story_outline") is not None or state3.get("intent") == "regenerate"

