"""
Image generation service using Runware SDK
"""
import logging
from runware import Runware, IImageInference

from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Image generator class using Runware SDK"""

    def __init__(self):
        self.runware = Runware(api_key=settings.RUNWARE_API_KEY)
        self.model = settings.RUNWARE_IMAGE_MODEL
        self._connected = False

    async def connect(self):
        if not self._connected:
            await self.runware.connect()
            self._connected = True

    def _build_prompt(self, prompt: str) -> str:
        """Build image generation prompt with fixed style"""
        return f"{prompt}, {settings.IMAGE_STYLE}"

    async def generate(self, prompt: str) -> str:
        """Generate image and return URL"""
        await self.connect()

        request = IImageInference(
            positivePrompt=self._build_prompt(prompt),
            model=self.model,
            width=1024,
            height=1024,
            numberResults=1,
        )

        try:
            results = await self.runware.imageInference(requestImage=request)
            if not results:
                raise RuntimeError("Runware returned empty result")
            return results[0].imageURL
        except Exception as e:
            logger.exception("Runware image generation failed")
            raise RuntimeError("Image generation failed") from e


def get_image_generator() -> ImageGenerator:
    """Create Runware image generator"""
    if not settings.RUNWARE_API_KEY:
        raise ValueError("Runware API key required")
    
    return ImageGenerator()
