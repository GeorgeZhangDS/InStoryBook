"""
Unit tests for image generation service
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.ai_services.image_generator import (
    ImageGenerator,
    get_image_generator,
)
from app.core.config import settings


class TestImageGenerator:
    """Test ImageGenerator class"""

    def test_build_prompt(self):
        """Test prompt building"""
        generator = ImageGenerator()
        prompt = generator._build_prompt("a rabbit")
        assert "a rabbit" in prompt
        assert "children's book illustration" in prompt

    @pytest.mark.asyncio
    @patch('app.services.ai_services.image_generator.AsyncOpenAI')
    async def test_generate_success(self, mock_openai):
        """Test successful image generation with OpenAI"""
        mock_image_url = "https://oaidalleapiprodscus.blob.core.windows.net/private/xxx.png"
        mock_image_data = MagicMock()
        mock_image_data.url = mock_image_url
        mock_response_data = MagicMock()
        mock_response_data.data = [mock_image_data]
        
        mock_client = MagicMock()
        mock_client.images.generate = AsyncMock(return_value=mock_response_data)
        mock_openai.return_value = mock_client
        
        generator = ImageGenerator()
        result = await generator.generate("a brave rabbit")
        
        assert result == mock_image_url
        assert result.startswith("http")
        mock_client.images.generate.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.ai_services.image_generator.AsyncOpenAI')
    async def test_generate_no_data(self, mock_openai):
        """Test handling of empty response"""
        mock_response_data = MagicMock()
        mock_response_data.data = []
        
        mock_client = MagicMock()
        mock_client.images.generate = AsyncMock(return_value=mock_response_data)
        mock_openai.return_value = mock_client
        
        generator = ImageGenerator()
        
        with pytest.raises(ValueError, match="No image data"):
            await generator.generate("a rabbit")

    @pytest.mark.asyncio
    @patch('app.services.ai_services.image_generator.AsyncOpenAI')
    async def test_generate_no_url(self, mock_openai):
        """Test handling of missing URL"""
        mock_image_data = MagicMock()
        mock_image_data.url = None
        mock_response_data = MagicMock()
        mock_response_data.data = [mock_image_data]
        
        mock_client = MagicMock()
        mock_client.images.generate = AsyncMock(return_value=mock_response_data)
        mock_openai.return_value = mock_client
        
        generator = ImageGenerator()
        
        with pytest.raises(ValueError, match="No image URL"):
            await generator.generate("a rabbit")


class TestGetImageGenerator:
    """Test get_image_generator factory function"""

    @patch('app.services.ai_services.image_generator.settings')
    def test_get_image_generator_missing_openai_key(self, mock_settings):
        """Test that missing OpenAI key raises error"""
        mock_settings.OPENAI_API_KEY = None
        
        with pytest.raises(ValueError, match="OpenAI API key required"):
            get_image_generator()

    @patch('app.services.ai_services.image_generator.settings')
    def test_get_image_generator_success(self, mock_settings):
        """Test successful generator creation"""
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        
        generator = get_image_generator()
        
        assert isinstance(generator, ImageGenerator)
