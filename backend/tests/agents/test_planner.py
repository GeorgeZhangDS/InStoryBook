"""
Unit tests for planner agent
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.planner import planner_agent, _fill_defaults
from app.agents.state import StoryState


class TestPlannerAgent:
    """Test planner_agent"""

    @pytest.fixture
    def mock_text_generator(self):
        mock_gen = AsyncMock()
        return mock_gen

    @pytest.fixture
    def initial_state(self):
        return {
            "theme": "A brave rabbit exploring a magical forest",
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
            "messages": []
        }

    @pytest.mark.asyncio
    @patch('app.agents.planner.get_text_generator')
    async def test_planner_success(self, mock_get_gen, mock_text_generator, initial_state):
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(return_value='{"needs_info": false, "language": "en", "story_outline": {"style": "adventure", "characters": ["Rabbit"], "setting": "Forest", "plot_summary": "A rabbit explores", "chapters": [{"chapter_id": 1, "title": "Start", "summary": "Beginning", "image_description": "A rabbit"}, {"chapter_id": 2, "title": "Middle", "summary": "Middle", "image_description": "A rabbit"}, {"chapter_id": 3, "title": "Climax", "summary": "Climax", "image_description": "A rabbit"}, {"chapter_id": 4, "title": "End", "summary": "End", "image_description": "A rabbit"}]}}')
        
        result = await planner_agent(initial_state)
        
        assert result["needs_info"] is False
        assert result["language"] == "en"
        assert "story_outline" in result
        assert len(result["story_outline"]["chapters"]) == 4
        mock_text_generator.generate.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.agents.planner.get_text_generator')
    async def test_planner_needs_info(self, mock_get_gen, mock_text_generator, initial_state):
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(return_value='{"needs_info": true, "language": "en", "missing_fields": ["characters"], "suggestions": ["Add characters"]}')
        
        result = await planner_agent(initial_state)
        
        assert result["needs_info"] is True
        assert "missing_fields" in result
        assert "suggestions" in result

    @pytest.mark.asyncio
    @patch('app.agents.planner.get_text_generator')
    async def test_planner_detects_chinese(self, mock_get_gen, mock_text_generator, initial_state):
        initial_state["theme"] = "一只勇敢的兔子在森林中探险"
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(return_value='{"needs_info": false, "language": "zh", "story_outline": {"style": "adventure", "characters": ["兔子"], "setting": "森林", "plot_summary": "兔子探险", "chapters": [{"chapter_id": 1, "title": "开始", "summary": "开始", "image_description": "A rabbit"}, {"chapter_id": 2, "title": "中间", "summary": "中间", "image_description": "A rabbit"}, {"chapter_id": 3, "title": "高潮", "summary": "高潮", "image_description": "A rabbit"}, {"chapter_id": 4, "title": "结束", "summary": "结束", "image_description": "A rabbit"}]}}')
        
        result = await planner_agent(initial_state)
        
        assert result["language"] == "zh"
        assert result["story_outline"]["chapters"][0]["title"] == "开始"

    @pytest.mark.asyncio
    @patch('app.agents.planner.get_text_generator')
    async def test_planner_empty_json(self, mock_get_gen, mock_text_generator, initial_state):
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(return_value='{}')
        
        result = await planner_agent(initial_state)
        
        assert result["needs_info"] is False
        assert "story_outline" in result
        assert len(result["story_outline"]["chapters"]) == 4

    @pytest.mark.asyncio
    @patch('app.agents.planner.get_text_generator')
    async def test_planner_exception_handling(self, mock_get_gen, mock_text_generator, initial_state):
        mock_get_gen.return_value = mock_text_generator
        mock_text_generator.generate = AsyncMock(side_effect=Exception("API error"))
        
        result = await planner_agent(initial_state)
        
        assert result["needs_info"] is False
        assert result["language"] == "en"
        assert "story_outline" in result


class TestFillDefaults:
    """Test _fill_defaults function"""

    def test_fill_defaults_needs_info(self):
        data = {"needs_info": True, "language": "zh", "missing_fields": ["characters"]}
        result = _fill_defaults(data)
        assert result["needs_info"] is True
        assert result["language"] == "zh"
        assert "missing_fields" in result

    def test_fill_defaults_complete_outline(self):
        data = {
            "needs_info": False,
            "language": "en",
            "story_outline": {
                "style": "adventure",
                "characters": ["Rabbit"],
                "setting": "Forest",
                "plot_summary": "A story",
                "chapters": [
                    {"chapter_id": 1, "title": "Ch1", "summary": "S1", "image_description": "Img1"},
                    {"chapter_id": 2, "title": "Ch2", "summary": "S2", "image_description": "Img2"}
                ]
            }
        }
        result = _fill_defaults(data)
        assert result["needs_info"] is False
        assert len(result["story_outline"]["chapters"]) == 4

    def test_fill_defaults_missing_chapters(self):
        data = {
            "needs_info": False,
            "language": "en",
            "story_outline": {
                "style": "adventure",
                "chapters": [
                    {"chapter_id": 1, "title": "Ch1", "summary": "S1", "image_description": "Img1"}
                ]
            }
        }
        result = _fill_defaults(data)
        assert len(result["story_outline"]["chapters"]) == 4

