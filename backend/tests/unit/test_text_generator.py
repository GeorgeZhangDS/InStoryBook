"""
Unit tests for text generation service
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

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
        from abc import ABC
        assert issubclass(TextGenerator, ABC)
        with pytest.raises(TypeError):
            generator = TextGenerator()


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
        call_args = mock_client.ainvoke.call_args
        assert isinstance(call_args[0][0], list)

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
        assert isinstance(call_args[0][0], list)

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

    @pytest.mark.asyncio
    @patch('app.services.ai_services.text_generator.ChatBedrockConverse')
    async def test_nova_with_response_format(self, mock_chat_bedrock):
        """Test Nova with response_format uses system message"""
        mock_response = AIMessage(content='{"result": "test"}')
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_bedrock.return_value = mock_client
        
        generator = NovaGenerator()
        await generator.generate("test", response_format={"type": "json_object"})
        
        call_args = mock_client.ainvoke.call_args
        messages = call_args[0][0]
        assert len(messages) == 2
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[1], HumanMessage)


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
        call_args = mock_client.ainvoke.call_args
        assert isinstance(call_args[0][0], list)

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
        assert isinstance(call_args[0][0], list)

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

    @pytest.mark.asyncio
    @patch('app.services.ai_services.text_generator.ChatOpenAI')
    async def test_openai_with_response_format(self, mock_chat_openai):
        """Test OpenAI with response_format parameter"""
        mock_response = AIMessage(content='{"result": "test"}')
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_openai.return_value = mock_client
        
        generator = OpenAIGenerator()
        await generator.generate("test", response_format={"type": "json_object"})
        
        call_args = mock_client.ainvoke.call_args
        assert call_args[1]["response_format"] == {"type": "json_object"}


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
        assert primary.generate.call_count == 1
        assert fallback.generate.call_count >= 1

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
        
        fallback_calls = fallback.generate.call_args_list
        assert len(fallback_calls) > 0
        call = fallback_calls[0]
        args = call[0]
        assert args[0] == "test"
        assert args[1] == 0.9
        assert args[2] == 500

    @pytest.mark.asyncio
    async def test_fallback_with_validation(self):
        """Test fallback with JSON validation"""
        primary = MagicMock(spec=TextGenerator)
        fallback = MagicMock(spec=TextGenerator)
        
        def validate_json(text):
            import json
            data = json.loads(text)
            if "needs_info" not in data:
                raise ValueError("Missing needs_info")
        
        primary.generate = AsyncMock(return_value='{"needs_info": false}')
        fallback.generate = AsyncMock(return_value='{"needs_info": true}')
        
        generator = FallbackGenerator(primary, fallback)
        result = await generator.generate("test", validate_json=validate_json)
        
        assert result == '{"needs_info": false}'
        primary.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_validation_failure_retry(self):
        """Test fallback retries when validation fails"""
        primary = MagicMock(spec=TextGenerator)
        fallback = MagicMock(spec=TextGenerator)
        
        def validate_json(text):
            import json
            data = json.loads(text)
            if "needs_info" not in data:
                raise ValueError("Missing needs_info")
        
        primary.generate = AsyncMock(return_value='{"invalid": true}')
        fallback.generate = AsyncMock(side_effect=[
            '{"invalid": true}',
            '{"invalid": true}',
            '{"needs_info": true}'
        ])
        
        generator = FallbackGenerator(primary, fallback)
        result = await generator.generate("test", validate_json=validate_json, max_retries=3)
        
        assert result == '{"needs_info": true}'
        assert fallback.generate.call_count == 3

    @pytest.mark.asyncio
    async def test_fallback_returns_empty_json_on_failure(self):
        """Test fallback returns empty JSON when all attempts fail"""
        primary = MagicMock(spec=TextGenerator)
        fallback = MagicMock(spec=TextGenerator)
        
        def validate_json(text):
            raise ValueError("Always fails")
        
        primary.generate = AsyncMock(return_value='{"invalid": true}')
        fallback.generate = AsyncMock(return_value='{"invalid": true}')
        
        generator = FallbackGenerator(primary, fallback)
        result = await generator.generate("test", validate_json=validate_json, response_format={"type": "json_object"})
        
        assert result == "{}"


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

