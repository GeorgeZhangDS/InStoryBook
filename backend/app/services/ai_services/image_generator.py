"""
Image generation service with fallback
Primary: GPT-image-1-mini, Fallback: Stability AI
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
            # Stability AI v2beta core API requires multipart/form-data
            # Using files parameter ensures proper multipart encoding with correct field names
            response = await client.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "image/*",
                },
                files={
                    "prompt": (None, full_prompt),
                    "output_format": (None, "png"),
                    "model": (None, self.model),
                    "width": (None, "1024"),  # SDXL native size
                    "height": (None, "1024"),  # SDXL native size
                    "steps": (None, "30"),
                    "cfg_scale": (None, "6"),
                    "sampler": (None, "K_EULER_ANCESTRAL"),
                    "style_preset": (None, "digital-art"),  # Digital art style
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

        # Use the configured model (gpt-image-1-mini)
        # Get URL first, then download and convert to base64
        response = await self.client.images.generate(
            model=self.model,
            prompt=full_prompt,
            n=1,
            size="1024x1024",  # Unified with SDXL
        )

        if not response.data or len(response.data) == 0:
            raise ValueError("No image data from OpenAI")

        item = response.data[0]
        
        # Check if b64_json is available
        if hasattr(item, 'b64_json') and item.b64_json:
            image_base64 = item.b64_json
            return f"data:image/png;base64,{image_base64}"
        
        # Otherwise, try to download from URL
        image_url = item.url
        if not image_url:
            raise ValueError("No image URL or b64_json from OpenAI")

        # Download image and convert to base64
        async with httpx.AsyncClient() as client:
            image_response = await client.get(image_url)
            image_response.raise_for_status()
            image_bytes = image_response.content
            
        if not image_bytes:
            raise ValueError("Empty image data from OpenAI")

        image_base64 = base64.b64encode(image_bytes).decode()
        return f"data:image/png;base64,{image_base64}"


class FallbackImageGenerator(ImageGenerator):
    """Image generator with automatic fallback"""

    def __init__(self, primary: ImageGenerator, fallback: ImageGenerator):
        self.primary = primary
        self.fallback = fallback

    async def generate(self, prompt: str, style: Optional[str] = None) -> str:
        try:
            logger.info(f"Trying primary: {self.primary.__class__.__name__}")
            result = await self.primary.generate(prompt, style=style)
            if result and result.startswith("data:image/"):
                return result
            raise ValueError("Invalid response from primary")
        except Exception as e:
            logger.warning(f"Primary failed: {e}, using fallback")
            return await self.fallback.generate(prompt, style=style)


def get_image_generator() -> ImageGenerator:
    """Create image generator with OpenAI primary and Stability fallback"""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key required")
    
    if not settings.STABILITY_API_KEY:
        raise ValueError("Stability API key required for fallback")
    
    primary = OpenAIImageGenerator()
    fallback = StabilityGenerator()
    
    return FallbackImageGenerator(primary, fallback)