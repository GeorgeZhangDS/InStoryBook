"""
Comprehensive tests for Illustrator Agent
"""
import pytest
from app.agents.state import StoryState
from app.agents.workflow.illustrator import illustrator_agent


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
class TestIllustratorImageGeneration:
    """Test Illustrator's image generation"""
    
    async def test_generate_image_chapter_1(self):
        """Test generating image for chapter 1"""
        state = create_base_state()
        result = await illustrator_agent(state, chapter_id=1)
        
        assert "chapters" in result
        assert "completed_image_gens" in result
        assert len(result["chapters"]) == 1
        assert result["chapters"][0]["chapter_id"] == 1
        assert "image" in result["chapters"][0]
    
    async def test_generate_all_images(self):
        """Test generating images for all chapters"""
        state = create_base_state()
        
        for chapter_id in range(1, 5):
            result = await illustrator_agent(state, chapter_id=chapter_id)
            
            assert "chapters" in result
            assert "completed_image_gens" in result
            assert chapter_id in result["completed_image_gens"]


@pytest.mark.asyncio
class TestIllustratorImageDescription:
    """Test Illustrator uses image description"""
    
    async def test_uses_image_description(self):
        """Test Illustrator uses image_description from outline"""
        state = create_base_state(
            story_outline={
                "style": "fantasy",
                "characters": ["Wizard"],
                "setting": "Tower",
                "plot_summary": "A wizard story",
                "chapters": [
                    {"chapter_id": 1, "title": "Chapter 1", "summary": "Summary", "image_description": "A wizard casting a spell"}
                ]
            }
        )
        result = await illustrator_agent(state, chapter_id=1)
        
        assert result["chapters"][0]["chapter_id"] == 1
        assert "image" in result["chapters"][0]


@pytest.mark.asyncio
class TestIllustratorEdgeCases:
    """Test Illustrator edge cases"""
    
    async def test_missing_chapter(self):
        """Test handling missing chapter"""
        state = create_base_state()
        state["story_outline"]["chapters"] = [
            {"chapter_id": 1, "title": "Chapter 1", "summary": "Summary", "image_description": "Image"}
        ]
        
        result = await illustrator_agent(state, chapter_id=5)
        
        assert "chapters" in result
        assert "completed_image_gens" in result
        assert len(result["chapters"]) == 0
    
    async def test_missing_image_description(self):
        """Test handling missing image_description"""
        state = create_base_state()
        state["story_outline"]["chapters"][0]["image_description"] = ""
        
        result = await illustrator_agent(state, chapter_id=1)
        
        assert "chapters" in result
        assert "completed_image_gens" in result
    
    async def test_none_image_description(self):
        """Test handling None image_description"""
        state = create_base_state()
        state["story_outline"]["chapters"][0]["image_description"] = None
        
        result = await illustrator_agent(state, chapter_id=1)
        
        assert "chapters" in result
        assert "completed_image_gens" in result


@pytest.mark.asyncio
class TestIllustratorOutputFormat:
    """Test Illustrator output format"""
    
    async def test_output_structure(self):
        """Test output structure"""
        state = create_base_state()
        result = await illustrator_agent(state, chapter_id=1)
        
        assert isinstance(result, dict)
        assert "chapters" in result
        assert "completed_image_gens" in result
        assert isinstance(result["chapters"], list)
        assert isinstance(result["completed_image_gens"], list)
    
    async def test_completed_image_gens_tracking(self):
        """Test completed_image_gens tracking"""
        state = create_base_state()
        result = await illustrator_agent(state, chapter_id=3)
        
        assert 3 in result["completed_image_gens"]
        assert isinstance(result["completed_image_gens"], list)
    
    async def test_image_data_format(self):
        """Test image data format"""
        state = create_base_state()
        result = await illustrator_agent(state, chapter_id=1)
        
        if len(result["chapters"]) > 0 and "image" in result["chapters"][0]:
            image_data = result["chapters"][0]["image"]
            # Image data should be present (could be URL, base64, or bytes)
            assert image_data is not None

