"""
Text generation service with fallback
Primary: Nova, Fallback: GPT-4o-mini
"""
from typing import Optional
from langchain_aws import ChatBedrockConverse
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class TextGenerator:
    """Base text generator class"""

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text from prompt"""
        raise NotImplementedError


class NovaGenerator(TextGenerator):
    """Amazon Nova generator"""

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
        max_tokens: Optional[int] = None
    ) -> str:
        kwargs = {"temperature": temperature}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        
        response = await self.client.ainvoke(prompt, **kwargs)
        return self._extract_content(response)

    def _extract_content(self, response: BaseMessage) -> str:
        if isinstance(response.content, str):
            return response.content
        elif isinstance(response.content, list):
            text_parts = []
            for item in response.content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
            return "".join(text_parts)
        return str(response.content)


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
        max_tokens: Optional[int] = None
    ) -> str:
        kwargs = {"temperature": temperature}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        
        response = await self.client.ainvoke(prompt, **kwargs)
        return self._extract_content(response)

    def _extract_content(self, response: BaseMessage) -> str:
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


class FallbackGenerator(TextGenerator):
    """Generator with automatic fallback"""

    def __init__(self, primary: TextGenerator, fallback: TextGenerator):
        self.primary = primary
        self.fallback = fallback

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        try:
            logger.info(f"Trying primary: {self.primary.__class__.__name__}")
            result = await self.primary.generate(prompt, temperature=temperature, max_tokens=max_tokens)
            if result and result.strip():
                return result
            raise ValueError("Empty response from primary")
        except Exception as e:
            logger.warning(f"Primary failed: {e}, using fallback")
            return await self.fallback.generate(prompt, temperature=temperature, max_tokens=max_tokens)


def get_text_generator() -> TextGenerator:
    """Create text generator with Nova primary and OpenAI fallback"""
    if not settings.AWS_ACCESS_KEY or not settings.AWS_SECRET_KEY:
        raise ValueError("AWS credentials required for Nova")
    
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key required for fallback")
    
    primary = NovaGenerator()
    fallback = OpenAIGenerator()
    
    return FallbackGenerator(primary, fallback)