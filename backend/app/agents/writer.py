"""
ChapterWriterAgent - Generates chapter text content
"""
import logging
from typing import Dict, Any

from app.agents.state import StoryState
from app.services.ai_services import get_text_generator
from app.utils import extract_json

logger = logging.getLogger(__name__)


def _fill_defaults(data: Dict[str, Any], chapter_id: int, chapter_outline: Dict[str, Any]) -> Dict[str, Any]:
    """Fill missing output fields with defaults (input fields already filled by planner)"""
    content = data.get("content", "")
    if not content or not content.strip():
        content = f"Chapter {chapter_id} content"
    
    return {
        "chapter_id": chapter_id,
        "title": chapter_outline["title"],
        "content": content.strip()
    }


async def writer_agent(state: StoryState, chapter_id: int) -> Dict[str, Any]:
    """Generates chapter text content for a single chapter"""
    story_outline = state["story_outline"]
    chapters = story_outline["chapters"]
    
    chapter = next((ch for ch in chapters if ch["chapter_id"] == chapter_id), None)
    if not chapter:
        logger.warning(f"Chapter {chapter_id} not found")
        return {"chapters": [], "completed_writers": []}
    
    language = state["language"]
    outline = story_outline
    
    prompt = f"""You are a professional children's story writer. Write Chapter {chapter_id} of a children's story in {language} language.

STORY CONTEXT:
- Style: {outline["style"]}
- Main Characters: {', '.join(outline["characters"])}
- Setting: {outline["setting"]}
- Overall Plot: {outline["plot_summary"]}

CHAPTER REQUIREMENTS:
- Title: {chapter["title"]}
- Summary: {chapter["summary"]}
- Length: 200-300 words
- Target Audience: Children (age-appropriate language and themes)

WRITING GUIDELINES:
1. Write ONLY the story content - no meta-commentary, no notes, no explanations
2. Use vivid, descriptive language that engages children's imagination
3. Show, don't tell - use actions and dialogue to convey emotions and events
4. Maintain consistency with the established characters, setting, and style
5. Use simple but rich vocabulary appropriate for children
6. Include sensory details (sights, sounds, smells) to make scenes come alive

CRITICAL RULES:
- DO NOT include any text outside the story narrative
- DO NOT add comments, notes, or explanations
- DO NOT mention "Chapter {chapter_id}" or any chapter numbers in the text
- DO NOT include meta-information about the story
- ONLY write the actual story content that children will read

Return JSON format:
{{
    "content": "The complete chapter text - pure story narrative only, no extra information"
}}"""

    try:
        response_text = await get_text_generator().generate(
            prompt=prompt,
            temperature=0.8,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        response_json = extract_json(response_text)
        if not response_json:
            logger.warning(f"WriterAgent received empty JSON for chapter {chapter_id}, using defaults")
        
        chapter_content = _fill_defaults(response_json, chapter_id, chapter)
        
        return {
            "chapters": [chapter_content],
            "completed_writers": [chapter_id]
        }
        
    except Exception as e:
        logger.error(f"Failed to generate chapter {chapter_id}: {e}")
        return {
            "chapters": [_fill_defaults({}, chapter_id, chapter)],
            "completed_writers": [chapter_id]
        }

