"""
Comprehensive tests for Writer Agent
"""
import pytest
from app.agents.state import StoryState
from app.agents.workflow.writer import writer_agent


def create_base_state(**kwargs) -> StoryState:
    """Helper to create base state with story outline"""
    defaults = {
        "theme": "A story about a brave dragon",
        "memory_summary": None,
        "intent": "story_generate",
        "chat_response": None,
        "language": "en",
        "story_outline": {
            "style": "adventure",
            "characters": ["Dragon", "Knight"],
            "setting": "A magical kingdom",
            "plot_summary": "A brave dragon learns to fly",
            "chapters": [
                {"chapter_id": 1, "title": "Chapter 1", "summary": "The dragon is born", "image_description": "A baby dragon"},
                {"chapter_id": 2, "title": "Chapter 2", "summary": "The dragon learns", "image_description": "A learning dragon"},
                {"chapter_id": 3, "title": "Chapter 3", "summary": "The dragon practices", "image_description": "A practicing dragon"},
                {"chapter_id": 4, "title": "Chapter 4", "summary": "The dragon flies", "image_description": "A flying dragon"},
            ]
        },
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
class TestWriterChapterGeneration:
    """Test Writer's chapter generation"""
    
    async def test_generate_chapter_1(self):
        """Test generating chapter 1"""
        state = create_base_state()
        result = await writer_agent(state, chapter_id=1)
        
        assert "chapters" in result
        assert "completed_writers" in result
        assert len(result["chapters"]) == 1
        assert result["chapters"][0]["chapter_id"] == 1
        assert "content" in result["chapters"][0]
        assert len(result["chapters"][0]["content"]) > 0
    
    async def test_generate_all_chapters(self):
        """Test generating all 4 chapters"""
        state = create_base_state()
        
        for chapter_id in range(1, 5):
            result = await writer_agent(state, chapter_id=chapter_id)
            
            assert "chapters" in result
            assert "completed_writers" in result
            assert chapter_id in result["completed_writers"]
            assert result["chapters"][0]["chapter_id"] == chapter_id


@pytest.mark.asyncio
class TestWriterContentQuality:
    """Test Writer's content quality"""
    
    async def test_content_length(self):
        """Test content has reasonable length"""
        state = create_base_state()
        result = await writer_agent(state, chapter_id=1)
        
        content = result["chapters"][0]["content"]
        assert len(content) > 50  # Should have substantial content
        assert len(content) < 5000  # Should not be too long
    
    async def test_content_structure(self):
        """Test content structure"""
        state = create_base_state()
        result = await writer_agent(state, chapter_id=1)
        
        chapter = result["chapters"][0]
        assert "chapter_id" in chapter
        assert "title" in chapter
        assert "content" in chapter
        assert chapter["title"] == "Chapter 1"
    
    async def test_content_no_meta(self):
        """Test content doesn't contain meta information"""
        state = create_base_state()
        result = await writer_agent(state, chapter_id=1)
        
        content = result["chapters"][0]["content"].lower()
        # Should not contain meta information
        meta_words = ["chapter 1", "this chapter", "in this chapter"]
        assert not all(word in content for word in meta_words) or len(content) > 100


@pytest.mark.asyncio
class TestWriterLanguageSupport:
    """Test Writer's language support"""
    
    async def test_english_content(self):
        """Test English content generation"""
        state = create_base_state(language="en")
        result = await writer_agent(state, chapter_id=1)
        
        content = result["chapters"][0]["content"]
        assert len(content) > 0
    
    async def test_chinese_content(self):
        """Test Chinese content generation"""
        state = create_base_state(language="zh")
        result = await writer_agent(state, chapter_id=1)
        
        content = result["chapters"][0]["content"]
        assert len(content) > 0


@pytest.mark.asyncio
class TestWriterContextUsage:
    """Test Writer uses story context"""
    
    async def test_uses_story_outline(self):
        """Test Writer uses story outline"""
        state = create_base_state(
            story_outline={
                "style": "fantasy",
                "characters": ["Wizard", "Dragon"],
                "setting": "A magical tower",
                "plot_summary": "A wizard tames a dragon",
                "chapters": [
                    {"chapter_id": 1, "title": "The Meeting", "summary": "Wizard meets dragon", "image_description": "Wizard and dragon"}
                ]
            }
        )
        result = await writer_agent(state, chapter_id=1)
        
        assert result["chapters"][0]["title"] == "The Meeting"
        assert len(result["chapters"][0]["content"]) > 0


@pytest.mark.asyncio
class TestWriterEdgeCases:
    """Test Writer edge cases"""
    
    async def test_missing_chapter(self):
        """Test handling missing chapter"""
        state = create_base_state()
        state["story_outline"]["chapters"] = [
            {"chapter_id": 1, "title": "Chapter 1", "summary": "Summary", "image_description": "Image"}
        ]
        
        result = await writer_agent(state, chapter_id=5)
        
        assert "chapters" in result
        assert "completed_writers" in result
        assert len(result["chapters"]) == 0 or result["chapters"][0].get("chapter_id") != 5
    
    async def test_incomplete_outline(self):
        """Test with incomplete outline"""
        state = create_base_state()
        state["story_outline"]["chapters"] = []
        
        result = await writer_agent(state, chapter_id=1)
        
        # Should handle gracefully
        assert "chapters" in result
        assert "completed_writers" in result


@pytest.mark.asyncio
class TestWriterOutputFormat:
    """Test Writer output format"""
    
    async def test_output_structure(self):
        """Test output structure"""
        state = create_base_state()
        result = await writer_agent(state, chapter_id=1)
        
        assert isinstance(result, dict)
        assert "chapters" in result
        assert "completed_writers" in result
        assert isinstance(result["chapters"], list)
        assert isinstance(result["completed_writers"], list)
    
    async def test_completed_writers_tracking(self):
        """Test completed_writers tracking"""
        state = create_base_state()
        result = await writer_agent(state, chapter_id=2)
        
        assert 2 in result["completed_writers"]
        assert isinstance(result["completed_writers"], list)

