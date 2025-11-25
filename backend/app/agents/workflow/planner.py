"""
StoryPlannerAgent - Plans story outline
"""
import logging
from typing import Dict, Any

from app.agents.state import StoryState
from app.services.ai_services import get_text_generator
from app.utils import extract_json

logger = logging.getLogger(__name__)


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
    memory_summary = state.get("memory_summary", "")
    intent = state.get("intent", "story_generate")
    existing_outline = state.get("story_outline")
    text_generator = get_text_generator()
    
    context = f"Memory summary: {memory_summary}\n" if memory_summary else ""
    
    if intent == "regenerate" and existing_outline:
        outline_context = f"""
=== EXISTING STORY OUTLINE (MODIFY THIS) ===
Style: {existing_outline.get('style', 'adventure')}
Characters: {', '.join(existing_outline.get('characters', []))}
Setting: {existing_outline.get('setting', '')}
Plot Summary: {existing_outline.get('plot_summary', '')}
Chapters:
"""
        for chapter in existing_outline.get('chapters', []):
            outline_context += f"  Chapter {chapter.get('chapter_id')}: {chapter.get('title', '')} - {chapter.get('summary', '')}\n"
        
        prompt = f"""You are modifying an existing story based on user feedback.

{context}User request: {theme}

{outline_context}
=== YOUR TASK ===
Based on the user's request, MODIFY the existing story outline above:
1. Keep elements that the user doesn't want to change
2. Modify elements based on user's feedback
3. Maintain story coherence and consistency
4. Detect the language from user's input (keep same language if not specified)

IMPORTANT RULES:
- The "language" field MUST match the language of the user's input
- The "image_description" field for each chapter MUST be in English, regardless of the detected language (for image generation services)

Return JSON format:
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
    else:
        prompt = f"""Analyze the user's theme and determine if there's enough information to create a complete 4-chapter children's story.

{context}User theme: {theme}

Steps:
1. Detect the language of the user's input:
   - If the input contains Chinese characters, return "zh"
   - If the input is in English, return "en"
   - For other languages, use appropriate codes: "es" for Spanish, "fr" for French, "de" for German, etc.
   - IMPORTANT: Accurately detect the language based on the actual content, not default to "en"
2. Evaluate if the theme has enough information (clear characters, setting, plot direction). If not, set needs_info=true.
3. If needs_info=true, provide missing_fields and suggestions in the detected language.
4. If needs_info=false, generate the complete story outline in the detected language.

IMPORTANT RULES:
- The "language" field MUST match the language of the user's input
- The "image_description" field for each chapter MUST be in English, regardless of the detected language (for image generation services)

Return JSON in one of these formats:

If information is INCOMPLETE (use the detected language code):
{{
    "needs_info": true,
    "language": "en",
    "missing_fields": ["field1", "field2"],
    "suggestions": ["suggestion1", "suggestion2"]
}}

If information is COMPLETE (use the detected language for language field, titles, and summaries):
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
        
        response_json = extract_json(response_text)
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
