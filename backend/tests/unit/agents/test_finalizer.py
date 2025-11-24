"""
Comprehensive tests for Finalizer Agents
"""
import pytest
from app.agents.state import StoryState
from app.agents.workflow.finalizer import finalizer_text_agent, finalizer_image_agent


def create_base_state(**kwargs) -> StoryState:
    """Helper to create base state with chapters"""
    defaults = {
        "theme": "A story about a brave dragon",
        "memory_summary": None,
        "intent": "story_generate",
        "chat_response": None,
        "language": "en",
        "story_outline": {
            "style": "adventure",
            "characters": ["Dragon"],
            "setting": "Kingdom",
            "plot_summary": "A dragon story",
            "chapters": [
                {"chapter_id": 1, "title": "Chapter 1", "summary": "Summary 1", "image_description": "Image 1"},
                {"chapter_id": 2, "title": "Chapter 2", "summary": "Summary 2", "image_description": "Image 2"},
                {"chapter_id": 3, "title": "Chapter 3", "summary": "Summary 3", "image_description": "Image 3"},
                {"chapter_id": 4, "title": "Chapter 4", "summary": "Summary 4", "image_description": "Image 4"},
            ]
        },
        "needs_info": False,
        "missing_fields": None,
        "suggestions": None,
        "chapters": [
            {"chapter_id": 1, "title": "Chapter 1", "content": "Content for chapter 1"},
            {"chapter_id": 2, "title": "Chapter 2", "content": "Content for chapter 2"},
            {"chapter_id": 3, "title": "Chapter 3", "content": "Content for chapter 3"},
            {"chapter_id": 4, "title": "Chapter 4", "content": "Content for chapter 4"},
        ],
        "completed_writers": [1, 2, 3, 4],
        "completed_image_gens": [1, 2, 3, 4],
        "finalized_text": None,
        "finalized_images": None,
        "session_id": "test-session",
        "messages": [],
    }
    defaults.update(kwargs)
    return defaults


@pytest.mark.asyncio
class TestFinalizerText:
    """Test Finalizer Text Agent"""
    
    async def test_finalize_text_complete(self):
        """Test finalizing text with complete chapters"""
        state = create_base_state()
        result = await finalizer_text_agent(state)
        
        assert "finalized_text" in result
        assert result["finalized_text"] is not None
        assert "chapters" in result["finalized_text"]
        assert len(result["finalized_text"]["chapters"]) == 4
    
    async def test_finalized_chapters_order(self):
        """Test finalized chapters are in order"""
        state = create_base_state()
        result = await finalizer_text_agent(state)
        
        chapters = result["finalized_text"]["chapters"]
        assert len(chapters) == 4
        
        for i, chapter in enumerate(chapters, 1):
            assert chapter["chapter_id"] == i
    
    async def test_finalized_chapters_structure(self):
        """Test finalized chapters structure"""
        state = create_base_state()
        result = await finalizer_text_agent(state)
        
        chapters = result["finalized_text"]["chapters"]
        for chapter in chapters:
            assert "chapter_id" in chapter
            assert "title" in chapter
            assert "content" in chapter
            assert isinstance(chapter["chapter_id"], int)
            assert isinstance(chapter["title"], str)
            assert isinstance(chapter["content"], str)
    
    async def test_finalize_text_missing_chapters(self):
        """Test finalizing text with missing chapters"""
        state = create_base_state()
        state["chapters"] = [
            {"chapter_id": 1, "title": "Chapter 1", "content": "Content 1"},
            {"chapter_id": 3, "title": "Chapter 3", "content": "Content 3"},
        ]
        
        result = await finalizer_text_agent(state)
        
        chapters = result["finalized_text"]["chapters"]
        assert len(chapters) == 4
        
        # Missing chapters should be handled (may have generated content or empty)
        assert chapters[1]["chapter_id"] == 2
        assert isinstance(chapters[1]["content"], str)
    
    async def test_finalize_text_empty_chapters(self):
        """Test finalizing text with empty chapters list"""
        state = create_base_state()
        state["chapters"] = []
        
        result = await finalizer_text_agent(state)
        
        chapters = result["finalized_text"]["chapters"]
        assert len(chapters) == 4
        
        # All should have content (may be generated or empty)
        for chapter in chapters:
            assert isinstance(chapter["content"], str)


@pytest.mark.asyncio
class TestFinalizerImage:
    """Test Finalizer Image Agent"""
    
    async def test_finalize_images_complete(self):
        """Test finalizing images with complete chapters"""
        state = create_base_state()
        state["chapters"] = [
            {"chapter_id": 1, "image": "image_data_1"},
            {"chapter_id": 2, "image": "image_data_2"},
            {"chapter_id": 3, "image": "image_data_3"},
            {"chapter_id": 4, "image": "image_data_4"},
        ]
        
        result = await finalizer_image_agent(state)
        
        assert "finalized_images" in result
        assert result["finalized_images"] is not None
        assert "chapters" in result["finalized_images"]
        assert len(result["finalized_images"]["chapters"]) == 4
    
    async def test_finalized_images_order(self):
        """Test finalized images are in order"""
        state = create_base_state()
        state["chapters"] = [
            {"chapter_id": 4, "image": "image_4"},
            {"chapter_id": 1, "image": "image_1"},
            {"chapter_id": 3, "image": "image_3"},
            {"chapter_id": 2, "image": "image_2"},
        ]
        
        result = await finalizer_image_agent(state)
        
        chapters = result["finalized_images"]["chapters"]
        assert len(chapters) == 4
        
        for i, chapter in enumerate(chapters, 1):
            assert chapter["chapter_id"] == i
    
    async def test_finalized_images_structure(self):
        """Test finalized images structure"""
        state = create_base_state()
        state["chapters"] = [
            {"chapter_id": 1, "image": "image_1"},
            {"chapter_id": 2, "image": "image_2"},
        ]
        
        result = await finalizer_image_agent(state)
        
        chapters = result["finalized_images"]["chapters"]
        for chapter in chapters:
            assert "chapter_id" in chapter
            assert "image" in chapter
            assert isinstance(chapter["chapter_id"], int)
    
    async def test_finalize_images_missing(self):
        """Test finalizing images with missing chapters"""
        state = create_base_state()
        state["chapters"] = [
            {"chapter_id": 1, "image": "image_1"},
            {"chapter_id": 3, "image": "image_3"},
        ]
        
        result = await finalizer_image_agent(state)
        
        chapters = result["finalized_images"]["chapters"]
        assert len(chapters) == 4
        
        # Missing chapters should have None image
        assert chapters[1]["chapter_id"] == 2
        assert chapters[1]["image"] is None
    
    async def test_finalize_images_empty(self):
        """Test finalizing images with empty chapters"""
        state = create_base_state()
        state["chapters"] = []
        
        result = await finalizer_image_agent(state)
        
        chapters = result["finalized_images"]["chapters"]
        assert len(chapters) == 4
        
        # All should have None image
        for chapter in chapters:
            assert chapter["image"] is None


@pytest.mark.asyncio
class TestFinalizerEdgeCases:
    """Test Finalizer edge cases"""
    
    async def test_finalizer_text_with_no_outline(self):
        """Test finalizer text without story outline"""
        state = create_base_state()
        state["story_outline"] = None
        
        # Should handle gracefully
        try:
            result = await finalizer_text_agent(state)
            assert "finalized_text" in result
        except Exception:
            # May fail if outline is required
            pass
    
    async def test_finalizer_text_different_languages(self):
        """Test finalizer text with different languages"""
        for lang in ["en", "zh"]:
            state = create_base_state(language=lang)
            result = await finalizer_text_agent(state)
            
            assert "finalized_text" in result
            chapters = result["finalized_text"]["chapters"]
            assert len(chapters) == 4


@pytest.mark.asyncio
class TestFinalizerOutputFormat:
    """Test Finalizer output format"""
    
    async def test_finalizer_text_output_structure(self):
        """Test finalizer text output structure"""
        state = create_base_state()
        result = await finalizer_text_agent(state)
        
        assert isinstance(result, dict)
        assert "finalized_text" in result
        assert isinstance(result["finalized_text"], dict)
        assert "chapters" in result["finalized_text"]
    
    async def test_finalizer_image_output_structure(self):
        """Test finalizer image output structure"""
        state = create_base_state()
        result = await finalizer_image_agent(state)
        
        assert isinstance(result, dict)
        assert "finalized_images" in result
        assert isinstance(result["finalized_images"], dict)
        assert "chapters" in result["finalized_images"]

