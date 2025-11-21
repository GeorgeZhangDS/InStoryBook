"""
Text generation service with fallback
Primary: Nova, Fallback: GPT-4o-mini
"""
from typing import Optional, Dict, Any, Callable
from abc import ABC, abstractmethod
import json
from langchain_aws import ChatBedrockConverse
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class TextGenerator(ABC):
    """Base text generator class"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        validate_json: Optional[Callable[[str], None]] = None
    ) -> str:
        """Generate text from prompt"""
        pass

    def _extract_content(self, response: BaseMessage) -> str:
        """Extract text content from LangChain message response"""
        if isinstance(response.content, str):
            return response.content
        elif isinstance(response.content, list):
            text_parts = []
            for item in response.content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict):
                    if "text" in item:
                        text_parts.append(item["text"])
                    elif "type" in item and item["type"] == "text":
                        text_parts.append(item.get("text", ""))
            return "".join(text_parts)
        return str(response.content)


class NovaGenerator(TextGenerator):
    """Amazon Nova generator - uses prompt engineering for JSON output"""

    def __init__(self):
        self.client = ChatBedrockConverse(
            model=settings.NOVA_MODEL,
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
        )

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        validate_json: Optional[Callable[[str], None]] = None
    ) -> str:
        kwargs = {"temperature": temperature}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        
        if response_format is not None:
            system_prompt = """You are a JSON-only response generator. Your responses MUST follow these strict rules:

1. Output ONLY valid JSON. No markdown code blocks, no ```json```, no explanations, no natural language.
2. Start directly with { and end with }. No leading or trailing text.
3. Ensure all required fields are present and properly formatted.
4. Use proper JSON syntax: double quotes for strings, proper commas, no trailing commas.
5. If you cannot generate valid JSON, return an empty object {}.

CRITICAL: Your response will be parsed as raw JSON. Any non-JSON text will cause parsing failure."""
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=prompt)]
        else:
            messages = [HumanMessage(content=prompt)]
        
        response = await self.client.ainvoke(messages, **kwargs)
        return self._extract_content(response)


class OpenAIGenerator(TextGenerator):
    """OpenAI GPT-4o-mini generator"""

    def __init__(self):
        self.client = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        validate_json: Optional[Callable[[str], None]] = None
    ) -> str:
        kwargs = {"temperature": temperature}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if response_format is not None:
            kwargs["response_format"] = response_format
        
        messages = [HumanMessage(content=prompt)]
        response = await self.client.ainvoke(messages, **kwargs)
        return self._extract_content(response)


class FallbackGenerator(TextGenerator):
    """Generator with automatic fallback, JSON validation, and retry"""

    def __init__(self, primary: TextGenerator, fallback: TextGenerator):
        self.primary = primary
        self.fallback = fallback

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        validate_json: Optional[Callable[[str], None]] = None,
        max_retries: int = 3
    ) -> str:
        result = await self._try_generator(self.primary, prompt, temperature, max_tokens, response_format, validate_json, 1)
        if result:
            return result
        
        result = await self._try_generator(self.fallback, prompt, temperature, max_tokens, response_format, validate_json, max_retries)
        return "{}" if response_format else (result or "")

    async def _try_generator(
        self,
        generator: TextGenerator,
        prompt: str,
        temperature: float,
        max_tokens: Optional[int],
        response_format: Optional[Dict[str, Any]],
        validate_json: Optional[Callable[[str], None]],
        max_attempts: int
    ) -> Optional[str]:
        for attempt in range(max_attempts):
            try:
                logger.info(f"Trying {generator.__class__.__name__} (attempt {attempt + 1}/{max_attempts})")
                result = await generator.generate(prompt, temperature, max_tokens, response_format, validate_json=None)
                
                if not result or not result.strip():
                    continue
                
                if validate_json:
                    validate_json(result)
                    logger.info(f"{generator.__class__.__name__} response passed validation")
                
                return result
            except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
                logger.warning(f"Validation failed (attempt {attempt + 1}): {e}")
            except Exception as e:
                logger.warning(f"{generator.__class__.__name__} failed (attempt {attempt + 1}): {e}")
        
        return None


def get_text_generator() -> TextGenerator:
    """Create text generator with Nova primary and OpenAI fallback"""
    if not settings.AWS_ACCESS_KEY or not settings.AWS_SECRET_KEY:
        raise ValueError("AWS credentials required for Nova")
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key required for fallback")
    
    return FallbackGenerator(NovaGenerator(), OpenAIGenerator())
