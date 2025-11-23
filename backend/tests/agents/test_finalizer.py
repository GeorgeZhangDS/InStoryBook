"""
Unit tests for finalizer agents
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.finalizer import finalizer_text_agent, finalizer_image_agent
from app.agents.state import StoryState


class TestFinalizerTextAgent:
    """Test finalizer_text_agent"""

    @pytest.fixture
    def mock_text_generator(self):
        mock_gen = AsyncMock()
        return mock_gen

    @pytest.fixture
    def state_with_chapters(self):
        return {
            "theme": "A brave rabbit",
            "language": "en",
            "story_outline": {
                "style": "adventure",
                "characters": ["Rabbit"],
                "setting": "Forest",
                "plot_summary": "A rabbit explores"
            },
            "chapters": [
                {"chapter_id": 1, "title": "Start", "content": "Chapter 1 content"},
                {"chapter_id": 2, "title": "Middle", "content": "Chapter 2 content"},
                {"chapter_id": 3, "title": "Climax", "content": "Chapter 3 content"},
                {"chapter_id": 4, "title": "End", "content": "Chapter 4 content"}
            ],
            "completed_writers": [1, 2, 3, 4],
            "completed_image_gens": [],
            "finalized_text": None,
            "finalized_images": None,
            "session_id": "test-session",
            "messages": []
        }

    @pytest.mark.asyncio
    @patch('app.agents.finalizer.get_text_generator')
    async def test_finalizer_text_success(self, mock_get_gen, mock_text_generator, state_with_chapters):
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(return_value='{"chapters": [{"chapter_id": 1, "title": "Start", "content": "Optimized Chapter 1"}, {"chapter_id": 2, "title": "Middle", "content": "Optimized Chapter 2"}, {"chapter_id": 3, "title": "Climax", "content": "Optimized Chapter 3"}, {"chapter_id": 4, "title": "End", "content": "Optimized Chapter 4"}]}')
        
        result = await finalizer_text_agent(state_with_chapters)
        
        assert "finalized_text" in result
        assert "chapters" in result["finalized_text"]
        assert len(result["finalized_text"]["chapters"]) == 4
        assert result["finalized_text"]["chapters"][0]["chapter_id"] == 1
        assert "content" in result["finalized_text"]["chapters"][0]
        mock_text_generator.generate.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.agents.finalizer.get_text_generator')
    async def test_finalizer_text_missing_chapters(self, mock_get_gen, mock_text_generator, state_with_chapters):
        state_with_chapters["chapters"] = [
            {"chapter_id": 1, "title": "Start", "content": "Chapter 1"},
            {"chapter_id": 3, "title": "Climax", "content": "Chapter 3"}
        ]
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(return_value='{"chapters": [{"chapter_id": 1, "title": "Start", "content": "Chapter 1"}, {"chapter_id": 2, "title": "Middle", "content": ""}, {"chapter_id": 3, "title": "Climax", "content": "Chapter 3"}, {"chapter_id": 4, "title": "End", "content": ""}]}')
        
        result = await finalizer_text_agent(state_with_chapters)
        
        assert len(result["finalized_text"]["chapters"]) == 4
        assert result["finalized_text"]["chapters"][1]["content"] == ""

    @pytest.mark.asyncio
    @patch('app.agents.finalizer.get_text_generator')
    async def test_finalizer_text_empty_json(self, mock_get_gen, mock_text_generator, state_with_chapters):
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(return_value='{}')
        
        result = await finalizer_text_agent(state_with_chapters)
        
        assert len(result["finalized_text"]["chapters"]) == 4
        assert result["finalized_text"]["chapters"][0]["content"] == "Chapter 1 content"

    @pytest.mark.asyncio
    @patch('app.agents.finalizer.get_text_generator')
    async def test_finalizer_text_exception_handling(self, mock_get_gen, mock_text_generator, state_with_chapters):
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(side_effect=Exception("API error"))
        
        result = await finalizer_text_agent(state_with_chapters)
        
        assert "finalized_text" in result
        assert len(result["finalized_text"]["chapters"]) == 4

    @pytest.mark.asyncio
    @patch('app.agents.finalizer.get_text_generator')
    async def test_finalizer_text_chinese_language(self, mock_get_gen, mock_text_generator, state_with_chapters):
        state_with_chapters["language"] = "zh"
        state_with_chapters["chapters"][0]["title"] = "开始"
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(return_value='{"chapters": [{"chapter_id": 1, "title": "开始", "content": "优化后的第一章内容"}]}')
        
        result = await finalizer_text_agent(state_with_chapters)
        
        assert result["finalized_text"]["chapters"][0]["title"] == "开始"


class TestFinalizerImageAgent:
    """Test finalizer_image_agent"""

    @pytest.fixture
    def state_with_images(self):
        return {
            "theme": "A brave rabbit",
            "language": "en",
            "story_outline": {},
            "chapters": [
                {"chapter_id": 1, "image": "data:image/png;base64,img1"},
                {"chapter_id": 2, "image": "data:image/png;base64,img2"},
                {"chapter_id": 3, "image": "data:image/png;base64,img3"},
                {"chapter_id": 4, "image": "data:image/png;base64,img4"}
            ],
            "completed_writers": [],
            "completed_image_gens": [1, 2, 3, 4],
            "finalized_text": None,
            "finalized_images": None,
            "session_id": "test-session",
            "messages": []
        }

    @pytest.mark.asyncio
    async def test_finalizer_image_success(self, state_with_images):
        result = await finalizer_image_agent(state_with_images)
        
        assert "finalized_images" in result
        assert "chapters" in result["finalized_images"]
        assert len(result["finalized_images"]["chapters"]) == 4
        assert result["finalized_images"]["chapters"][0]["chapter_id"] == 1
        assert result["finalized_images"]["chapters"][0]["image"] == "data:image/png;base64,img1"

    @pytest.mark.asyncio
    async def test_finalizer_image_missing_images(self, state_with_images):
        state_with_images["chapters"] = [
            {"chapter_id": 1, "image": "data:image/png;base64,img1"},
            {"chapter_id": 3, "image": "data:image/png;base64,img3"}
        ]
        
        result = await finalizer_image_agent(state_with_images)
        
        assert len(result["finalized_images"]["chapters"]) == 4
        assert result["finalized_images"]["chapters"][1]["image"] is None
        assert result["finalized_images"]["chapters"][3]["image"] is None

    @pytest.mark.asyncio
    async def test_finalizer_image_empty_chapters(self):
        state = {
            "chapters": [],
            "story_outline": {}
        }
        
        result = await finalizer_image_agent(state)
        
        assert len(result["finalized_images"]["chapters"]) == 4
        assert all(ch["image"] is None for ch in result["finalized_images"]["chapters"])

