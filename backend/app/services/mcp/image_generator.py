"""
Image generation service with fallback
Primary: Stability AI, Fallback: GPT-image-1-mini
"""
from typing import Optional
import httpx
import logging
import base64
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Base image generator class"""

    async def generate(self, prompt: str, style: Optional[str] = None) -> str:
        """Generate image and return base64 data URI"""
        raise NotImplementedError


class StabilityGenerator(ImageGenerator):
    """Stability AI SDXL generator"""

    def __init__(self):
        self.api_key = settings.STABILITY_API_KEY
        self.model = settings.STABILITY_MODEL
        self.url = "https://api.stability.ai/v2beta/stable-image/generate/core"

    def _build_prompt(self, prompt: str, style: Optional[str] = None) -> str:
        if style:
            return f"{prompt}, style: {style}, children's book illustration"
        return f"{prompt}, children's book illustration"

    async def generate(self, prompt: str, style: Optional[str] = None) -> str:
        full_prompt = self._build_prompt(prompt, style)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "image/*"
                },
                data={
                    "prompt": full_prompt,
                    "output_format": "png",
                    "model": self.model,
                    "width": 1152,
                    "height": 768,
                },
            )
            response.raise_for_status()

            image_bytes = response.content
            if not image_bytes:
                raise ValueError("Empty image data from Stability")

            image_base64 = base64.b64encode(image_bytes).decode()
            return f"data:image/png;base64,{image_base64}"


class OpenAIImageGenerator(ImageGenerator):
    """OpenAI GPT-image-1-mini generator"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_IMAGE_MODEL

    def _build_prompt(self, prompt: str, style: Optional[str] = None) -> str:
        if style:
            return f"{prompt}, style: {style}, children's book illustration"
        return f"{prompt}, children's book illustration"

    async def generate(self, prompt: str, style: Optional[str] = None) -> str:
        full_prompt = self._build_prompt(prompt, style)

        response = await self.client.images.generate(
            model=self.model,
            prompt=full_prompt,
            n=1,
            size="1152x768",
            response_format="b64_json",
        )

        if not response.data or len(response.data) == 0:
            raise ValueError("No image data from OpenAI")

        b64 = response.data[0].b64_json
        if not b64:
            raise ValueError("Empty base64 data from OpenAI")

        return f"data:image/png;base64,{b64}"


class FallbackImageGenerator(ImageGenerator):
    """Image generator with automatic fallback"""

    def __init__(self, primary: ImageGenerator, fallback: ImageGenerator):
        self.primary = primary
        self.fallback = fallback

    async def generate(self, prompt: str, style: Optional[str] = None) -> str:
        try:
            logger.info(f"Trying primary: {self.primary.__class__.__name__}")
            result = await self.primary.generate(prompt, style)
            if result and result.startswith("data:image/"):
                return result
            raise ValueError("Invalid response from primary")
        except Exception as e:
            logger.warning(f"Primary failed: {e}, using fallback")
            return await self.fallback.generate(prompt, style)


def get_image_generator() -> ImageGenerator:
    """Create image generator with Stability primary and OpenAI fallback"""
    if not settings.STABILITY_API_KEY:
        raise ValueError("Stability API key required")
    
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key required for fallback")
    
    primary = StabilityGenerator()
    fallback = OpenAIImageGenerator()
    
    return FallbackImageGenerator(primary, fallback)