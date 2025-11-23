"""
Unit tests for illustrator agent
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.illustrator import illustrator_agent
from app.agents.state import StoryState


class TestIllustratorAgent:
    """Test illustrator_agent"""

    @pytest.fixture
    def mock_image_generator(self):
        mock_gen = AsyncMock()
        return mock_gen

    @pytest.fixture
    def state_with_outline(self):
        return {
            "theme": "A brave rabbit",
            "language": "en",
            "story_outline": {
                "style": "adventure",
                "characters": ["Rabbit"],
                "setting": "Forest",
                "plot_summary": "A rabbit explores",
                "chapters": [
                    {"chapter_id": 1, "title": "Start", "summary": "Beginning", "image_description": "A brave rabbit in the forest"},
                    {"chapter_id": 2, "title": "Middle", "summary": "Middle", "image_description": "A rabbit exploring"},
                    {"chapter_id": 3, "title": "Climax", "summary": "Climax", "image_description": "A rabbit discovering"},
                    {"chapter_id": 4, "title": "End", "summary": "End", "image_description": "A rabbit celebrating"}
                ]
            },
            "chapters": [],
            "completed_writers": [],
            "completed_image_gens": [],
            "finalized_text": None,
            "finalized_images": None,
            "session_id": "test-session",
            "messages": []
        }

    @pytest.mark.asyncio
    @patch('app.agents.illustrator.get_image_generator')
    async def test_illustrator_success(self, mock_get_gen, mock_image_generator, state_with_outline):
        mock_get_gen.return_value = mock_image_generator
        mock_image_generator.generate = AsyncMock(return_value="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
        
        result = await illustrator_agent(state_with_outline, chapter_id=1)
        
        assert "chapters" in result
        assert len(result["chapters"]) == 1
        assert result["chapters"][0]["chapter_id"] == 1
        assert "image" in result["chapters"][0]
        assert result["chapters"][0]["image"].startswith("data:image/")
        assert result["completed_image_gens"] == [1]
        mock_image_generator.generate.assert_called_once_with("A brave rabbit in the forest")

    @pytest.mark.asyncio
    @patch('app.agents.illustrator.get_image_generator')
    async def test_illustrator_chapter_not_found(self, mock_get_gen, mock_image_generator, state_with_outline):
        mock_get_gen.return_value = mock_image_generator
        
        result = await illustrator_agent(state_with_outline, chapter_id=99)
        
        assert result["chapters"] == []
        assert result["completed_image_gens"] == []
        mock_image_generator.generate.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.agents.illustrator.get_image_generator')
    async def test_illustrator_no_image_description(self, mock_get_gen, mock_image_generator, state_with_outline):
        state_with_outline["story_outline"]["chapters"][0]["image_description"] = None
        mock_get_gen.return_value = mock_image_generator
        
        result = await illustrator_agent(state_with_outline, chapter_id=1)
        
        assert result["chapters"] == []
        assert result["completed_image_gens"] == []
        mock_image_generator.generate.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.agents.illustrator.get_image_generator')
    async def test_illustrator_exception_handling(self, mock_get_gen, mock_image_generator, state_with_outline):
        mock_get_gen.return_value = mock_image_generator
        mock_image_generator.generate = AsyncMock(side_effect=Exception("API error"))
        
        result = await illustrator_agent(state_with_outline, chapter_id=1)
        
        assert result["chapters"] == []
        assert result["completed_image_gens"] == [1]

