"""
Comprehensive tests for Planner Agent
"""
import pytest
from app.agents.state import StoryState
from app.agents.workflow.planner import planner_agent


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
class TestPlannerLanguageDetection:
    """Test Planner's language detection"""
    
    async def test_chinese_language_detection(self):
        """Test Chinese language detection"""
        state = create_base_state(theme="我想创建一个关于小兔子的故事")
        result = await planner_agent(state)
        
        assert result["language"] == "zh"
    
    async def test_english_language_detection(self):
        """Test English language detection"""
        state = create_base_state(theme="Create a story about a brave dragon")
        result = await planner_agent(state)
        
        assert result["language"] == "en"
    
    async def test_mixed_language_handling(self):
        """Test mixed language input"""
        state = create_base_state(theme="Hello 你好")
        result = await planner_agent(state)
        
        assert result["language"] in ["zh", "en"]


@pytest.mark.asyncio
class TestPlannerStoryOutline:
    """Test Planner's story outline generation"""
    
    async def test_complete_story_outline(self):
        """Test complete story outline generation"""
        state = create_base_state(
            theme="A brave little dragon learns to fly in a magical forest",
            memory_summary="User wants a dragon story"
        )
        result = await planner_agent(state)
        
        assert result["needs_info"] == False
        assert "story_outline" in result
        assert result["story_outline"] is not None
        
        outline = result["story_outline"]
        assert "style" in outline
        assert "characters" in outline
        assert "setting" in outline
        assert "plot_summary" in outline
        assert "chapters" in outline
        assert len(outline["chapters"]) == 4
    
    async def test_outline_chapters_structure(self):
        """Test outline chapters have correct structure"""
        state = create_base_state(
            theme="A story about a rabbit and a turtle racing",
            memory_summary=None
        )
        result = await planner_agent(state)
        
        if not result["needs_info"]:
            chapters = result["story_outline"]["chapters"]
            assert len(chapters) == 4
            
            for i, chapter in enumerate(chapters, 1):
                assert chapter["chapter_id"] == i
                assert "title" in chapter
                assert "summary" in chapter
                assert "image_description" in chapter
                # image_description should be in English
                assert isinstance(chapter["image_description"], str)
    
    async def test_outline_with_memory_summary(self):
        """Test outline generation uses memory summary"""
        state = create_base_state(
            theme="Continue the story",
            memory_summary="Previous story about a brave knight"
        )
        result = await planner_agent(state)
        
        assert "story_outline" in result or result["needs_info"] == True


@pytest.mark.asyncio
class TestPlannerNeedsInfo:
    """Test Planner's needs_info detection"""
    
    async def test_incomplete_info_detection(self):
        """Test detection of incomplete information"""
        state = create_base_state(theme="A story")
        result = await planner_agent(state)
        
        # Should either need info or generate outline
        assert "needs_info" in result
        assert isinstance(result["needs_info"], bool)
    
    async def test_needs_info_structure(self):
        """Test needs_info response structure"""
        state = create_base_state(theme="Story")
        result = await planner_agent(state)
        
        if result["needs_info"]:
            assert "missing_fields" in result
            assert "suggestions" in result
            assert isinstance(result["missing_fields"], list)
            assert isinstance(result["suggestions"], list)
            assert "language" in result
            assert isinstance(result["language"], str)


@pytest.mark.asyncio
class TestPlannerEdgeCases:
    """Test Planner edge cases"""
    
    async def test_empty_theme(self):
        """Test with empty theme"""
        state = create_base_state(theme="")
        result = await planner_agent(state)
        
        assert "needs_info" in result
        assert "language" in result
    
    async def test_very_long_theme(self):
        """Test with very long theme"""
        long_theme = "A " * 200 + "story"
        state = create_base_state(theme=long_theme)
        result = await planner_agent(state)
        
        assert "needs_info" in result
        assert "language" in result
    
    async def test_special_characters(self):
        """Test with special characters"""
        state = create_base_state(theme="Story with 🐰 emoji and !@#$% symbols")
        result = await planner_agent(state)
        
        assert "needs_info" in result
        assert "language" in result


@pytest.mark.asyncio
class TestPlannerOutputFormat:
    """Test Planner output format"""
    
    async def test_output_structure_complete(self):
        """Test output structure for complete outline"""
        state = create_base_state(
            theme="A complete story about a magical adventure"
        )
        result = await planner_agent(state)
        
        assert isinstance(result, dict)
        assert "needs_info" in result
        assert "language" in result
        
        if not result["needs_info"]:
            assert "story_outline" in result
    
    async def test_output_structure_incomplete(self):
        """Test output structure for incomplete info"""
        state = create_base_state(theme="Story")
        result = await planner_agent(state)
        
        assert isinstance(result, dict)
        assert "needs_info" in result
        assert "language" in result
        
        if result["needs_info"]:
            assert "missing_fields" in result
            assert "suggestions" in result
    
    async def test_language_consistency(self):
        """Test language field consistency"""
        test_cases = [
            ("Create a story", "en"),
            ("创建一个故事", "zh"),
        ]
        
        for theme, expected_lang in test_cases:
            state = create_base_state(theme=theme)
            result = await planner_agent(state)
            
            assert result["language"] == expected_lang

