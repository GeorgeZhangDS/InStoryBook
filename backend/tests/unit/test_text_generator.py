"""
Unit tests for text generation service
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.messages import AIMessage

from app.services.ai_services.text_generator import (
    TextGenerator,
    NovaGenerator,
    OpenAIGenerator,
    FallbackGenerator,
    get_text_generator,
)
from app.core.config import settings


class TestTextGenerator:
    """Test base TextGenerator class"""

    def test_text_generator_abstract(self):
        """Test that TextGenerator is abstract"""
        generator = TextGenerator()
        with pytest.raises(NotImplementedError):
            # This will raise NotImplementedError
            import asyncio
            asyncio.run(generator.generate("test prompt"))


class TestNovaGenerator:
    """Test NovaGenerator class"""

    @pytest.mark.asyncio
    @patch('app.services.ai_services.text_generator.ChatBedrockConverse')
    async def test_nova_generate_success(self, mock_chat_bedrock):
        """Test successful text generation with Nova"""
        mock_response = AIMessage(content="Generated story text")
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_bedrock.return_value = mock_client
        
        generator = NovaGenerator()
        result = await generator.generate("Write a story about a rabbit")
        
        assert result == "Generated story text"
        mock_client.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.ai_services.text_generator.ChatBedrockConverse')
    async def test_nova_generate_with_params(self, mock_chat_bedrock):
        """Test generation with temperature and max_tokens"""
        mock_response = AIMessage(content="Generated text")
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_bedrock.return_value = mock_client
        
        generator = NovaGenerator()
        await generator.generate(
            "Write a story",
            temperature=0.9,
            max_tokens=500
        )
        
        call_args = mock_client.ainvoke.call_args
        assert call_args[1]["temperature"] == 0.9
        assert call_args[1]["max_tokens"] == 500

    @pytest.mark.asyncio
    @patch('app.services.ai_services.text_generator.ChatBedrockConverse')
    async def test_nova_extract_content_string(self, mock_chat_bedrock):
        """Test content extraction from string response"""
        mock_response = AIMessage(content="Simple string content")
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_bedrock.return_value = mock_client
        
        generator = NovaGenerator()
        result = await generator.generate("test")
        assert result == "Simple string content"

    @pytest.mark.asyncio
    @patch('app.services.ai_services.text_generator.ChatBedrockConverse')
    async def test_nova_extract_content_list(self, mock_chat_bedrock):
        """Test content extraction from list response"""
        mock_response = AIMessage(content=["Part 1", "Part 2", {"text": "Part 3"}])
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_bedrock.return_value = mock_client
        
        generator = NovaGenerator()
        result = await generator.generate("test")
        assert "Part 1" in result
        assert "Part 2" in result
        assert "Part 3" in result


class TestOpenAIGenerator:
    """Test OpenAIGenerator class"""

    @pytest.mark.asyncio
    @patch('app.services.ai_services.text_generator.ChatOpenAI')
    async def test_openai_generate_success(self, mock_chat_openai):
        """Test successful text generation with OpenAI"""
        mock_response = AIMessage(content="Generated story text")
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_openai.return_value = mock_client
        
        generator = OpenAIGenerator()
        result = await generator.generate("Write a story about a rabbit")
        
        assert result == "Generated story text"
        mock_client.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.ai_services.text_generator.ChatOpenAI')
    async def test_openai_generate_with_params(self, mock_chat_openai):
        """Test generation with temperature and max_tokens"""
        mock_response = AIMessage(content="Generated text")
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_openai.return_value = mock_client
        
        generator = OpenAIGenerator()
        await generator.generate(
            "Write a story",
            temperature=0.8,
            max_tokens=1000
        )
        
        call_args = mock_client.ainvoke.call_args
        assert call_args[1]["temperature"] == 0.8
        assert call_args[1]["max_tokens"] == 1000

    @pytest.mark.asyncio
    @patch('app.services.ai_services.text_generator.ChatOpenAI')
    async def test_openai_extract_content_complex(self, mock_chat_openai):
        """Test content extraction from complex response"""
        mock_response = AIMessage(content=[
            {"type": "text", "text": "First part"},
            "Second part"
        ])
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_openai.return_value = mock_client
        
        generator = OpenAIGenerator()
        result = await generator.generate("test")
        assert "First part" in result
        assert "Second part" in result


class TestFallbackGenerator:
    """Test FallbackGenerator class"""

    @pytest.mark.asyncio
    async def test_fallback_primary_success(self):
        """Test fallback uses primary when it succeeds"""
        primary = MagicMock(spec=TextGenerator)
        fallback = MagicMock(spec=TextGenerator)
        
        primary.generate = AsyncMock(return_value="Primary result")
        
        generator = FallbackGenerator(primary, fallback)
        result = await generator.generate("test prompt")
        
        assert result == "Primary result"
        primary.generate.assert_called_once()
        fallback.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_primary_empty_response(self):
        """Test fallback uses fallback when primary returns empty"""
        primary = MagicMock(spec=TextGenerator)
        fallback = MagicMock(spec=TextGenerator)
        
        primary.generate = AsyncMock(return_value="")
        fallback.generate = AsyncMock(return_value="Fallback result")
        
        generator = FallbackGenerator(primary, fallback)
        result = await generator.generate("test prompt")
        
        assert result == "Fallback result"
        primary.generate.assert_called_once()
        fallback.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_primary_exception(self):
        """Test fallback uses fallback when primary raises exception"""
        primary = MagicMock(spec=TextGenerator)
        fallback = MagicMock(spec=TextGenerator)
        
        primary.generate = AsyncMock(side_effect=Exception("API error"))
        fallback.generate = AsyncMock(return_value="Fallback result")
        
        generator = FallbackGenerator(primary, fallback)
        result = await generator.generate("test prompt")
        
        assert result == "Fallback result"
        primary.generate.assert_called_once()
        fallback.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_preserves_parameters(self):
        """Test that fallback preserves generation parameters"""
        primary = MagicMock(spec=TextGenerator)
        fallback = MagicMock(spec=TextGenerator)
        
        primary.generate = AsyncMock(side_effect=Exception("Error"))
        fallback.generate = AsyncMock(return_value="Result")
        
        generator = FallbackGenerator(primary, fallback)
        await generator.generate("test", temperature=0.9, max_tokens=500)
        
        fallback.generate.assert_called_once_with("test", temperature=0.9, max_tokens=500)


class TestGetTextGenerator:
    """Test get_text_generator factory function"""

    @patch('app.services.ai_services.text_generator.settings')
    def test_get_text_generator_missing_aws_credentials(self, mock_settings):
        """Test that missing AWS credentials raises error"""
        mock_settings.AWS_ACCESS_KEY = None
        mock_settings.AWS_SECRET_KEY = None
        
        with pytest.raises(ValueError, match="AWS credentials required"):
            get_text_generator()

    @patch('app.services.ai_services.text_generator.settings')
    def test_get_text_generator_missing_openai_key(self, mock_settings):
        """Test that missing OpenAI key raises error"""
        mock_settings.AWS_ACCESS_KEY = "test_key"
        mock_settings.AWS_SECRET_KEY = "test_secret"
        mock_settings.OPENAI_API_KEY = None
        
        with pytest.raises(ValueError, match="OpenAI API key required"):
            get_text_generator()

    @patch('app.services.ai_services.text_generator.settings')
    @patch('app.services.ai_services.text_generator.NovaGenerator')
    @patch('app.services.ai_services.text_generator.OpenAIGenerator')
    def test_get_text_generator_success(self, mock_openai, mock_nova, mock_settings):
        """Test successful generator creation"""
        mock_settings.AWS_ACCESS_KEY = "test_key"
        mock_settings.AWS_SECRET_KEY = "test_secret"
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        
        mock_nova_instance = MagicMock()
        mock_openai_instance = MagicMock()
        mock_nova.return_value = mock_nova_instance
        mock_openai.return_value = mock_openai_instance
        
        generator = get_text_generator()
        
        assert isinstance(generator, FallbackGenerator)
        assert generator.primary == mock_nova_instance
        assert generator.fallback == mock_openai_instance

