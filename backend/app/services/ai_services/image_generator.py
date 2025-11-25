"""
Image generation service using OpenAI
"""
import logging
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Image generator class"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_IMAGE_MODEL

    def _build_prompt(self, prompt: str) -> str:
        return f"{prompt}, children's book illustration"

    async def generate(self, prompt: str) -> str:
        """Generate image and return URL"""
        full_prompt = self._build_prompt(prompt)

        response = await self.client.images.generate(
            model=self.model,
            prompt=full_prompt,
            n=1,
            size="1024x1024",
        )

        if not response.data or len(response.data) == 0:
            raise ValueError("No image data from OpenAI")

        item = response.data[0]
        
        if not item.url:
            raise ValueError("No image URL from OpenAI")

        return item.url


def get_image_generator() -> ImageGenerator:
    """Create OpenAI image generator"""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key required")
    
    return ImageGenerator()
