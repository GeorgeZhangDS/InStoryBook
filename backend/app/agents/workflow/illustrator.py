"""
IllustratorAgent - Generates images for chapters
"""
import logging
from typing import Dict, Any

from app.agents.state import StoryState
from app.services.ai_services import get_image_generator

logger = logging.getLogger(__name__)


async def illustrator_agent(state: StoryState, chapter_id: int) -> Dict[str, Any]:
    """Generates image for a single chapter using planner's image_description"""

    story_outline = state["story_outline"]
    chapters = story_outline["chapters"]
    
    chapter_outline = next((ch for ch in chapters if ch["chapter_id"] == chapter_id), None)

    if not chapter_outline:
        logger.warning(f"Chapter {chapter_id} not found in outline")
        return {"chapters": [], "completed_image_gens": []}
    
    image_description = chapter_outline["image_description"]

    if not image_description:
        logger.warning(f"No image_description for chapter {chapter_id}")
        return {"chapters": [], "completed_image_gens": []}
    
    try:
        image_generator = get_image_generator()
        image_data = await image_generator.generate(image_description)
        
        return {
            "chapters": [{
                "chapter_id": chapter_id,
                "image": image_data
            }],
            "completed_image_gens": [chapter_id]
        }
        
    except Exception as e:
        logger.error(f"Failed to generate image for chapter {chapter_id}: {e}")
        return {"chapters": [], "completed_image_gens": [chapter_id]}

