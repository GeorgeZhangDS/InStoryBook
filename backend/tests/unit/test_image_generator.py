"""
Unit tests for image generation service
"""
import pytest
import base64
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.ai_services.image_generator import (
    ImageGenerator,
    StabilityGenerator,
    OpenAIImageGenerator,
    FallbackImageGenerator,
    get_image_generator,
)
from app.core.config import settings


class TestImageGenerator:
    """Test base ImageGenerator class"""

    def test_image_generator_abstract(self):
        """Test that ImageGenerator is abstract"""
        generator = ImageGenerator()
        with pytest.raises(NotImplementedError):
            # This will raise NotImplementedError
            import asyncio
            asyncio.run(generator.generate("test prompt"))


class TestStabilityGenerator:
    """Test StabilityGenerator class"""

    def test_build_prompt_without_style(self):
        """Test prompt building without style"""
        generator = StabilityGenerator()
        prompt = generator._build_prompt("a rabbit")
        assert "a rabbit" in prompt
        assert "children's book illustration" in prompt

    def test_build_prompt_with_style(self):
        """Test prompt building with style"""
        generator = StabilityGenerator()
        prompt = generator._build_prompt("a rabbit", style="watercolor")
        assert "a rabbit" in prompt
        assert "style: watercolor" in prompt
        assert "children's book illustration" in prompt

    @pytest.mark.asyncio
    async def test_stability_generate_success(self):
        """Test successful image generation with Stability"""
        generator = StabilityGenerator()
        
        # Create mock image bytes
        mock_image_bytes = b"fake_image_data"
        mock_base64 = base64.b64encode(mock_image_bytes).decode()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.content = mock_image_bytes
            mock_response.raise_for_status = MagicMock()
            
            mock_post = AsyncMock(return_value=mock_response)
            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.post = mock_post
            mock_client.return_value = mock_client_instance
            
            result = await generator.generate("a brave rabbit")
            
            assert result.startswith("data:image/png;base64,")
            assert mock_base64 in result
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_stability_generate_with_style(self):
        """Test generation with style parameter"""
        generator = StabilityGenerator()
        
        mock_image_bytes = b"fake_image_data"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.content = mock_image_bytes
            mock_response.raise_for_status = MagicMock()
            
            mock_post = AsyncMock(return_value=mock_response)
            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.post = mock_post
            mock_client.return_value = mock_client_instance
            
            await generator.generate("a rabbit", style="cartoon")
            
            call_args = mock_post.call_args
            assert "style: cartoon" in call_args[1]["data"]["prompt"]

    @pytest.mark.asyncio
    async def test_stability_generate_empty_response(self):
        """Test handling of empty image response"""
        generator = StabilityGenerator()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.content = b""
            mock_response.raise_for_status = MagicMock()
            
            mock_post = AsyncMock(return_value=mock_response)
            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.post = mock_post
            mock_client.return_value = mock_client_instance
            
            with pytest.raises(ValueError, match="Empty image data"):
                await generator.generate("a rabbit")


class TestOpenAIImageGenerator:
    """Test OpenAIImageGenerator class"""

    @patch('app.services.ai_services.image_generator.AsyncOpenAI')
    def test_build_prompt_without_style(self, mock_openai):
        """Test prompt building without style"""
        generator = OpenAIImageGenerator()
        prompt = generator._build_prompt("a rabbit")
        assert "a rabbit" in prompt
        assert "children's book illustration" in prompt

    @patch('app.services.ai_services.image_generator.AsyncOpenAI')
    def test_build_prompt_with_style(self, mock_openai):
        """Test prompt building with style"""
        generator = OpenAIImageGenerator()
        prompt = generator._build_prompt("a rabbit", style="watercolor")
        assert "a rabbit" in prompt
        assert "style: watercolor" in prompt

    @pytest.mark.asyncio
    @patch('app.services.ai_services.image_generator.AsyncOpenAI')
    async def test_openai_generate_success(self, mock_openai):
        """Test successful image generation with OpenAI"""
        mock_b64 = "base64_encoded_image_data"
        mock_image_data = MagicMock()
        mock_image_data.b64_json = mock_b64
        mock_response_data = MagicMock()
        mock_response_data.data = [mock_image_data]
        
        mock_client = MagicMock()
        mock_client.images.generate = AsyncMock(return_value=mock_response_data)
        mock_openai.return_value = mock_client
        
        generator = OpenAIImageGenerator()
        result = await generator.generate("a brave rabbit")
        
        assert result.startswith("data:image/png;base64,")
        assert mock_b64 in result
        mock_client.images.generate.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.ai_services.image_generator.AsyncOpenAI')
    async def test_openai_generate_no_data(self, mock_openai):
        """Test handling of empty response"""
        mock_response_data = MagicMock()
        mock_response_data.data = []
        
        mock_client = MagicMock()
        mock_client.images.generate = AsyncMock(return_value=mock_response_data)
        mock_openai.return_value = mock_client
        
        generator = OpenAIImageGenerator()
        
        with pytest.raises(ValueError, match="No image data"):
            await generator.generate("a rabbit")

    @pytest.mark.asyncio
    @patch('app.services.ai_services.image_generator.AsyncOpenAI')
    async def test_openai_generate_empty_b64(self, mock_openai):
        """Test handling of empty base64 data"""
        mock_image_data = MagicMock()
        mock_image_data.b64_json = None
        mock_response_data = MagicMock()
        mock_response_data.data = [mock_image_data]
        
        mock_client = MagicMock()
        mock_client.images.generate = AsyncMock(return_value=mock_response_data)
        mock_openai.return_value = mock_client
        
        generator = OpenAIImageGenerator()
        
        with pytest.raises(ValueError, match="Empty base64 data"):
            await generator.generate("a rabbit")


class TestFallbackImageGenerator:
    """Test FallbackImageGenerator class"""

    @pytest.mark.asyncio
    async def test_fallback_primary_success(self):
        """Test fallback uses primary when it succeeds"""
        primary = MagicMock(spec=ImageGenerator)
        fallback = MagicMock(spec=ImageGenerator)
        
        primary.generate = AsyncMock(return_value="data:image/png;base64,xxx")
        
        generator = FallbackImageGenerator(primary, fallback)
        result = await generator.generate("test prompt")
        
        assert result == "data:image/png;base64,xxx"
        primary.generate.assert_called_once()
        fallback.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_primary_invalid_response(self):
        """Test fallback uses fallback when primary returns invalid response"""
        primary = MagicMock(spec=ImageGenerator)
        fallback = MagicMock(spec=ImageGenerator)
        
        primary.generate = AsyncMock(return_value="invalid_response")
        fallback.generate = AsyncMock(return_value="data:image/png;base64,yyy")
        
        generator = FallbackImageGenerator(primary, fallback)
        result = await generator.generate("test prompt")
        
        assert result == "data:image/png;base64,yyy"
        primary.generate.assert_called_once()
        fallback.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_primary_exception(self):
        """Test fallback uses fallback when primary raises exception"""
        primary = MagicMock(spec=ImageGenerator)
        fallback = MagicMock(spec=ImageGenerator)
        
        primary.generate = AsyncMock(side_effect=Exception("API error"))
        fallback.generate = AsyncMock(return_value="data:image/png;base64,zzz")
        
        generator = FallbackImageGenerator(primary, fallback)
        result = await generator.generate("test prompt")
        
        assert result == "data:image/png;base64,zzz"
        primary.generate.assert_called_once()
        fallback.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_preserves_parameters(self):
        """Test that fallback preserves generation parameters"""
        primary = MagicMock(spec=ImageGenerator)
        fallback = MagicMock(spec=ImageGenerator)
        
        primary.generate = AsyncMock(side_effect=Exception("Error"))
        fallback.generate = AsyncMock(return_value="data:image/png;base64,result")
        
        generator = FallbackImageGenerator(primary, fallback)
        await generator.generate("test", style="cartoon")
        
        fallback.generate.assert_called_once_with("test", style="cartoon")


class TestGetImageGenerator:
    """Test get_image_generator factory function"""

    @patch('app.services.ai_services.image_generator.settings')
    def test_get_image_generator_missing_stability_key(self, mock_settings):
        """Test that missing Stability API key raises error"""
        mock_settings.STABILITY_API_KEY = None
        
        with pytest.raises(ValueError, match="Stability API key required"):
            get_image_generator()

    @patch('app.services.ai_services.image_generator.settings')
    def test_get_image_generator_missing_openai_key(self, mock_settings):
        """Test that missing OpenAI key raises error"""
        mock_settings.STABILITY_API_KEY = "test_stability_key"
        mock_settings.OPENAI_API_KEY = None
        
        with pytest.raises(ValueError, match="OpenAI API key required"):
            get_image_generator()

    @patch('app.services.ai_services.image_generator.settings')
    @patch('app.services.ai_services.image_generator.StabilityGenerator')
    @patch('app.services.ai_services.image_generator.OpenAIImageGenerator')
    def test_get_image_generator_success(self, mock_openai, mock_stability, mock_settings):
        """Test successful generator creation"""
        mock_settings.STABILITY_API_KEY = "test_stability_key"
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        
        mock_stability_instance = MagicMock()
        mock_openai_instance = MagicMock()
        mock_stability.return_value = mock_stability_instance
        mock_openai.return_value = mock_openai_instance
        
        generator = get_image_generator()
        
        assert isinstance(generator, FallbackImageGenerator)
        assert generator.primary == mock_stability_instance
        assert generator.fallback == mock_openai_instance

