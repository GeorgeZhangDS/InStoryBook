"""
Comprehensive tests for Chat Agent
"""
import pytest
from app.agents.state import StoryState
from app.agents.conversation.chat import chat_agent


def create_base_state(**kwargs) -> StoryState:
    """Helper to create base state"""
    defaults = {
        "theme": "",
        "memory_summary": None,
        "intent": None,
        "chat_response": None,
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
        "session_id": "test-session",
        "messages": [],
    }
    defaults.update(kwargs)
    return defaults


def has_chinese(text: str) -> bool:
    """Check if text contains Chinese characters"""
    return any('\u4e00' <= char <= '\u9fff' for char in text)


@pytest.mark.asyncio
class TestChatLanguageMatching:
    """Test Chat Agent language matching"""
    
    async def test_chinese_response(self):
        """Test Chat responds in Chinese for Chinese input"""
        state = create_base_state(theme="你好！今天过得怎么样？")
        result = await chat_agent(state)
        
        assert "chat_response" in result
        assert has_chinese(result["chat_response"])
    
    async def test_english_response(self):
        """Test Chat responds in English for English input"""
        state = create_base_state(theme="Hello! How are you today?")
        result = await chat_agent(state)
        
        assert "chat_response" in result
        assert not has_chinese(result["chat_response"])
    
    async def test_mixed_language_handling(self):
        """Test Chat handles mixed language input"""
        state = create_base_state(theme="Hello 你好")
        result = await chat_agent(state)
        
        assert "chat_response" in result
        assert len(result["chat_response"]) > 0


@pytest.mark.asyncio
class TestChatToneAndStyle:
    """Test Chat Agent tone and style"""
    
    async def test_friendly_tone(self):
        """Test Chat maintains friendly tone"""
        state = create_base_state(theme="Hi there!")
        result = await chat_agent(state)
        
        response = result["chat_response"].lower()
        assert len(response) > 0
        # Check for friendly indicators
        friendly_words = ["hello", "hi", "great", "happy", "excited", "fun"]
        assert any(word in response for word in friendly_words) or len(response) > 10
    
    async def test_child_appropriate_language(self):
        """Test Chat uses child-appropriate language"""
        state = create_base_state(theme="Tell me a joke")
        result = await chat_agent(state)
        
        response = result["chat_response"]
        # Should not contain inappropriate words
        inappropriate = ["damn", "hell", "stupid"]
        assert not any(word in response.lower() for word in inappropriate)


@pytest.mark.asyncio
class TestChatContextHandling:
    """Test Chat Agent context handling"""
    
    async def test_with_memory_summary(self):
        """Test Chat uses memory summary for context"""
        state = create_base_state(
            theme="What did we talk about?",
            memory_summary="Previous conversation about a story"
        )
        result = await chat_agent(state)
        
        assert "chat_response" in result
        assert len(result["chat_response"]) > 0
    
    async def test_without_memory_summary(self):
        """Test Chat works without memory summary"""
        state = create_base_state(
            theme="Hello!",
            memory_summary=None
        )
        result = await chat_agent(state)
        
        assert "chat_response" in result
        assert len(result["chat_response"]) > 0
    
    async def test_empty_memory_summary(self):
        """Test Chat with empty memory summary"""
        state = create_base_state(
            theme="Hi!",
            memory_summary=""
        )
        result = await chat_agent(state)
        
        assert "chat_response" in result


@pytest.mark.asyncio
class TestChatEdgeCases:
    """Test Chat Agent edge cases"""
    
    async def test_empty_theme(self):
        """Test with empty theme"""
        state = create_base_state(theme="")
        result = await chat_agent(state)
        
        assert "chat_response" in result
        assert len(result["chat_response"]) > 0
    
    async def test_very_long_theme(self):
        """Test with very long theme"""
        long_theme = "Tell me " * 100 + "a story"
        state = create_base_state(theme=long_theme)
        result = await chat_agent(state)
        
        assert "chat_response" in result
    
    async def test_question_input(self):
        """Test with question input"""
        state = create_base_state(theme="What's your favorite color?")
        result = await chat_agent(state)
        
        assert "chat_response" in result
        assert "?" in result["chat_response"] or len(result["chat_response"]) > 10
    
    async def test_greeting_input(self):
        """Test with greeting input"""
        state = create_base_state(theme="Hello!")
        result = await chat_agent(state)
        
        assert "chat_response" in result
        assert len(result["chat_response"]) > 0


@pytest.mark.asyncio
class TestChatOutputFormat:
    """Test Chat Agent output format"""
    
    async def test_output_structure(self):
        """Test output has correct structure"""
        state = create_base_state(theme="Test")
        result = await chat_agent(state)
        
        assert isinstance(result, dict)
        assert "chat_response" in result
        assert len(result) == 1
    
    async def test_chat_response_type(self):
        """Test chat_response is always a string"""
        test_cases = [
            "Hello",
            "你好",
            "What's up?",
            "",
        ]
        
        for theme in test_cases:
            state = create_base_state(theme=theme)
            result = await chat_agent(state)
            
            assert isinstance(result["chat_response"], str)
            assert len(result["chat_response"]) > 0
    
    async def test_json_format(self):
        """Test response is properly formatted JSON"""
        state = create_base_state(theme="Hi")
        result = await chat_agent(state)
        
        # Should be able to serialize
        import json
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        assert "chat_response" in parsed

