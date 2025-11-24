"""
Comprehensive tests for Router Agent
"""
import pytest
from app.agents.state import StoryState
from app.agents.conversation.router import router_agent


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


@pytest.mark.asyncio
class TestRouterIntentClassification:
    """Test Router's intent classification"""
    
    async def test_story_generate_intent_chinese(self):
        """Test story generation intent with Chinese input"""
        state = create_base_state(theme="我想创建一个关于小兔子的冒险故事")
        result = await router_agent(state)
        
        assert result["intent"] == "story_generate"
        assert "memory_summary" in result
        assert len(result["memory_summary"]) > 0
    
    async def test_story_generate_intent_english(self):
        """Test story generation intent with English input"""
        state = create_base_state(theme="Create a story about a brave little dragon")
        result = await router_agent(state)
        
        assert result["intent"] == "story_generate"
        assert "memory_summary" in result
    
    async def test_chat_intent_greeting(self):
        """Test chat intent with greeting"""
        state = create_base_state(theme="你好，今天天气真好！")
        result = await router_agent(state)
        
        assert result["intent"] == "chat"
    
    async def test_chat_intent_question(self):
        """Test chat intent with question"""
        state = create_base_state(theme="What's your favorite color?")
        result = await router_agent(state)
        
        assert result["intent"] == "chat"
    
    async def test_regenerate_intent_chinese(self):
        """Test regenerate intent with Chinese"""
        state = create_base_state(
            theme="我不喜欢这个故事，请重新生成一个",
            memory_summary="Previous story about a rabbit"
        )
        result = await router_agent(state)
        
        assert result["intent"] in ["regenerate", "story_generate"]
    
    async def test_regenerate_intent_english(self):
        """Test regenerate intent with English"""
        state = create_base_state(
            theme="I don't like this story, please regenerate",
            memory_summary="Previous story about a dragon"
        )
        result = await router_agent(state)
        
        assert result["intent"] in ["regenerate", "story_generate"]


@pytest.mark.asyncio
class TestRouterMemorySummary:
    """Test Router's memory summary management"""
    
    async def test_summary_initial_creation(self):
        """Test summary creation from first input"""
        state = create_base_state(
            theme="A story about a magical forest",
            memory_summary=None
        )
        result = await router_agent(state)
        
        assert result["memory_summary"] is not None
        assert len(result["memory_summary"]) > 0
    
    async def test_summary_incremental_update(self):
        """Test summary incremental update"""
        initial_summary = "User wants a story about a rabbit"
        state = create_base_state(
            theme="The rabbit should be brave and adventurous",
            memory_summary=initial_summary
        )
        result = await router_agent(state)
        
        assert result["memory_summary"] is not None
        assert initial_summary in result["memory_summary"] or len(result["memory_summary"]) > len(initial_summary)
    
    async def test_summary_with_empty_input(self):
        """Test summary preservation with empty input"""
        initial_summary = "Previous conversation summary"
        state = create_base_state(
            theme="",
            memory_summary=initial_summary
        )
        result = await router_agent(state)
        
        assert result["intent"] == "story_generate"
        assert result["memory_summary"] == initial_summary
    
    async def test_summary_with_none(self):
        """Test summary handling when None"""
        state = create_base_state(
            theme="New story request",
            memory_summary=None
        )
        result = await router_agent(state)
        
        assert result["memory_summary"] is not None
        assert isinstance(result["memory_summary"], str)


@pytest.mark.asyncio
class TestRouterEdgeCases:
    """Test Router edge cases and error handling"""
    
    async def test_empty_theme(self):
        """Test with empty theme"""
        state = create_base_state(theme="")
        result = await router_agent(state)
        
        assert result["intent"] == "story_generate"
        assert "memory_summary" in result
    
    async def test_very_long_theme(self):
        """Test with very long theme"""
        long_theme = "A " * 500 + "story"
        state = create_base_state(theme=long_theme)
        result = await router_agent(state)
        
        assert result["intent"] in ["story_generate", "chat", "regenerate"]
        assert "memory_summary" in result
    
    async def test_whitespace_only_theme(self):
        """Test with whitespace only theme"""
        state = create_base_state(theme="   \n\t   ")
        result = await router_agent(state)
        
        assert result["intent"] == "story_generate"
    
    async def test_special_characters(self):
        """Test with special characters"""
        state = create_base_state(theme="Story with 🐰 emoji and !@#$% symbols")
        result = await router_agent(state)
        
        assert "intent" in result
        assert "memory_summary" in result
    
    async def test_multilingual_input(self):
        """Test with mixed language input"""
        state = create_base_state(theme="Hello 你好 Bonjour")
        result = await router_agent(state)
        
        assert "intent" in result
        assert "memory_summary" in result


@pytest.mark.asyncio
class TestRouterOutputFormat:
    """Test Router output format and structure"""
    
    async def test_output_structure(self):
        """Test output has correct structure"""
        state = create_base_state(theme="Test input")
        result = await router_agent(state)
        
        assert isinstance(result, dict)
        assert "intent" in result
        assert "memory_summary" in result
        assert len(result) == 2
    
    async def test_intent_values(self):
        """Test intent values are valid"""
        test_cases = [
            "Create a story",
            "Hello there",
            "重新生成",
        ]
        
        for theme in test_cases:
            state = create_base_state(theme=theme)
            result = await router_agent(state)
            
            assert result["intent"] in ["story_generate", "chat", "regenerate"]
    
    async def test_memory_summary_type(self):
        """Test memory_summary is always a string"""
        test_cases = [
            ("New story", None),
            ("Update story", "Previous summary"),
            ("", "Existing summary"),
        ]
        
        for theme, summary in test_cases:
            state = create_base_state(theme=theme, memory_summary=summary)
            result = await router_agent(state)
            
            assert isinstance(result["memory_summary"], str)

