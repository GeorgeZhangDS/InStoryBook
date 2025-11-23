"""
Unit tests for writer agent
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.writer import writer_agent, _fill_defaults
from app.agents.state import StoryState


class TestWriterAgent:
    """Test writer_agent"""

    @pytest.fixture
    def mock_text_generator(self):
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
                    {"chapter_id": 1, "title": "Start", "summary": "Beginning", "image_description": "A rabbit"},
                    {"chapter_id": 2, "title": "Middle", "summary": "Middle", "image_description": "A rabbit"},
                    {"chapter_id": 3, "title": "Climax", "summary": "Climax", "image_description": "A rabbit"},
                    {"chapter_id": 4, "title": "End", "summary": "End", "image_description": "A rabbit"}
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
    @patch('app.agents.writer.get_text_generator')
    async def test_writer_success(self, mock_get_gen, mock_text_generator, state_with_outline):
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(return_value='{"content": "Once upon a time, a brave rabbit set out on an adventure."}')
        
        result = await writer_agent(state_with_outline, chapter_id=1)
        
        assert "chapters" in result
        assert len(result["chapters"]) == 1
        assert result["chapters"][0]["chapter_id"] == 1
        assert "content" in result["chapters"][0]
        assert result["completed_writers"] == [1]
        mock_text_generator.generate.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.agents.writer.get_text_generator')
    async def test_writer_chinese_language(self, mock_get_gen, mock_text_generator, state_with_outline):
        state_with_outline["language"] = "zh"
        state_with_outline["story_outline"]["chapters"][0]["title"] = "开始"
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(return_value='{"content": "从前，有一只勇敢的兔子开始了冒险。"}')
        
        result = await writer_agent(state_with_outline, chapter_id=1)
        
        assert result["chapters"][0]["title"] == "开始"
        assert "从前" in result["chapters"][0]["content"]

    @pytest.mark.asyncio
    @patch('app.agents.writer.get_text_generator')
    async def test_writer_chapter_not_found(self, mock_get_gen, mock_text_generator, state_with_outline):
        mock_get_gen.return_value = mock_text_generator
        
        result = await writer_agent(state_with_outline, chapter_id=99)
        
        assert result["chapters"] == []
        assert result["completed_writers"] == []
        mock_text_generator.generate.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.agents.writer.get_text_generator')
    async def test_writer_empty_json(self, mock_get_gen, mock_text_generator, state_with_outline):
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(return_value='{}')
        
        result = await writer_agent(state_with_outline, chapter_id=1)
        
        assert len(result["chapters"]) == 1
        assert result["chapters"][0]["chapter_id"] == 1
        assert "content" in result["chapters"][0]

    @pytest.mark.asyncio
    @patch('app.agents.writer.get_text_generator')
    async def test_writer_exception_handling(self, mock_get_gen, mock_text_generator, state_with_outline):
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(side_effect=Exception("API error"))
        
        result = await writer_agent(state_with_outline, chapter_id=1)
        
        assert len(result["chapters"]) == 1
        assert result["completed_writers"] == [1]


class TestFillDefaults:
    """Test _fill_defaults function"""

    def test_fill_defaults_with_content(self):
        data = {"content": "Story content here"}
        chapter_id = 1
        chapter_outline = {"title": "Chapter 1", "summary": "Summary"}
        result = _fill_defaults(data, chapter_id, chapter_outline)
        assert result["chapter_id"] == 1
        assert result["title"] == "Chapter 1"
        assert result["content"] == "Story content here"

    def test_fill_defaults_empty_content(self):
        data = {}
        chapter_id = 2
        chapter_outline = {"title": "Chapter 2", "summary": "Summary"}
        result = _fill_defaults(data, chapter_id, chapter_outline)
        assert result["content"] == "Chapter 2 content"

