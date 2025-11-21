"""
StoryPlannerAgent - Plans story outline
"""
import json
import re
import logging
from typing import Dict, Any

from app.agents.state import StoryState
from app.services.ai_services import get_text_generator

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from text"""
    text = text.strip()
    json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(0))
    return {}


def _fill_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    """Fill missing fields with defaults"""
    if data.get("needs_info", False):
        return {
            "needs_info": True,
            "language": data.get("language", "en"),
            "missing_fields": data.get("missing_fields", []),
            "suggestions": data.get("suggestions", [])
        }
    
    outline = data.get("story_outline", {})
    chapters = outline.get("chapters", [])
    
    while len(chapters) < 4:
        chapters.append({
            "chapter_id": len(chapters) + 1,
            "title": f"Chapter {len(chapters) + 1}",
            "summary": "Story continues...",
            "image_description": "A scene from the story"
        })
    
    return {
        "needs_info": False,
        "language": data.get("language", "en"),
        "story_outline": {
            "style": outline.get("style", "adventure"),
            "characters": outline.get("characters", ["Main Character"]),
            "setting": outline.get("setting", "A magical place"),
            "plot_summary": outline.get("plot_summary", "An exciting adventure unfolds"),
            "chapters": chapters[:4]
        }
    }


async def planner_agent(state: StoryState) -> Dict[str, Any]:
    """StoryPlannerAgent - Generates story outline and detects language"""
    theme = state.get("theme", "")
    text_generator = get_text_generator()
    
    prompt = f"""Analyze the user's theme and determine if there's enough information to create a complete 4-chapter children's story.

User theme: {theme}

Steps:
1. Detect the language of the user's input (e.g., "en" for English, "zh" for Chinese, "es" for Spanish, etc.). Default to "en" if uncertain.
2. Evaluate if the theme has enough information (clear characters, setting, plot direction). If not, set needs_info=true.
3. If needs_info=true, provide missing_fields and suggestions.
4. If needs_info=false, generate the complete story outline.

IMPORTANT: The "image_description" field for each chapter MUST be in English, regardless of the detected language. This is for image generation services.

Return JSON in one of these formats:

If information is INCOMPLETE:
{{
    "needs_info": true,
    "language": "en",
    "missing_fields": ["field1", "field2"],
    "suggestions": ["suggestion1", "suggestion2"]
}}

If information is COMPLETE:
{{
    "needs_info": false,
    "language": "en",
    "story_outline": {{
        "style": "adventure|fantasy|educational|friendship",
        "characters": ["character1", "character2"],
        "setting": "setting description",
        "plot_summary": "overall plot",
        "chapters": [
            {{"chapter_id": 1, "title": "Title", "summary": "Summary", "image_description": "English description for image generation"}},
            {{"chapter_id": 2, "title": "Title", "summary": "Summary", "image_description": "English description for image generation"}},
            {{"chapter_id": 3, "title": "Title", "summary": "Summary", "image_description": "English description for image generation"}},
            {{"chapter_id": 4, "title": "Title", "summary": "Summary", "image_description": "English description for image generation"}}
        ]
    }}
}}"""

    try:
        response_text = await text_generator.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        response_json = _extract_json(response_text)
        if not response_json: logger.warning("PlannerAgent received empty JSON, using defaults.")
        return _fill_defaults(response_json)
        
    except Exception as e:
        logger.error(f"Planner error: {e}")
        return {
            "needs_info": False,
            "language": "en",
            "story_outline": {
                "style": "adventure",
                "characters": ["Hero"],
                "setting": "A magical world",
                "plot_summary": f"A story about {theme[:50]}",
                "chapters": [
                    {"chapter_id": i, "title": f"Chapter {i}", "summary": "Story begins...", "image_description": "A scene from the story"}
                    for i in range(1, 5)
                ]
            }
        }
