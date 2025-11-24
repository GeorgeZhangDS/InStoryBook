"""
Finalizer Agents - Two separate agents for text and image finalization
"""
import logging
from typing import Dict, Any

from app.agents.state import StoryState
from app.services.ai_services import get_text_generator
from app.utils import extract_json

logger = logging.getLogger(__name__)


async def finalizer_text_agent(state: StoryState) -> Dict[str, Any]:
    """Finalizes text content, returns text chapters in order (1-4)"""
    chapters_list = []
    for chapter in state.get("chapters", []):
        if "content" in chapter:
            chapters_list.append({
                "chapter_id": chapter["chapter_id"],
                "title": chapter.get("title", f"Chapter {chapter['chapter_id']}"),
                "content": chapter["content"]
            })
    
    chapters_list.sort(key=lambda x: x["chapter_id"])
    
    ordered_chapters = []
    for chapter_id in range(1, 5):
        chapter = next((ch for ch in chapters_list if ch["chapter_id"] == chapter_id), None)
        if chapter:
            ordered_chapters.append(chapter)
        else:
            logger.warning(f"Chapter {chapter_id} text missing")
            ordered_chapters.append({
                "chapter_id": chapter_id,
                "title": f"Chapter {chapter_id}",
                "content": ""
            })
    
    chapters_text = "\n\n".join([
        f"Chapter {ch['chapter_id']}: {ch['title']}\n{ch['content']}"
        for ch in ordered_chapters
    ])
    
    outline = state["story_outline"]
    prompt = f"""You are a professional children's story editor. Review and optimize the following 4-chapter children's story in {state["language"]} language.

STORY CONTEXT:
- Style: {outline["style"]}
- Characters: {', '.join(outline["characters"])}
- Setting: {outline["setting"]}
- Overall Plot: {outline["plot_summary"]}

STORY CONTENT:
{chapters_text}

OPTIMIZATION TASKS:
1. Improve transitions between chapters
2. Enhance story flow and coherence
3. Refine turning points and plot transitions
4. Ensure smooth narrative progression
5. Maintain consistency with the original style and characters

Return JSON with optimized chapters in order (chapter_id 1, 2, 3, 4):
{{
    "chapters": [
        {{"chapter_id": 1, "title": "Title", "content": "Optimized content"}},
        {{"chapter_id": 2, "title": "Title", "content": "Optimized content"}},
        {{"chapter_id": 3, "title": "Title", "content": "Optimized content"}},
        {{"chapter_id": 4, "title": "Title", "content": "Optimized content"}}
    ]
}}

IMPORTANT: Only optimize text content, keep same structure. Return chapters in order: 1, 2, 3, 4. Return ONLY valid JSON."""

    try:
        response_text = await get_text_generator().generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )
        
        response_json = extract_json(response_text)
        if not response_json:
            logger.warning("FinalizerTextAgent received empty JSON, using original chapters")
            optimized_chapters = ordered_chapters
        else:
            optimized_chapters = response_json.get("chapters", ordered_chapters)
            optimized_chapters.sort(key=lambda x: x.get("chapter_id", 0))
        
        text_only_chapters = []
        for ch in optimized_chapters:
            text_only_chapters.append({
                "chapter_id": ch.get("chapter_id"),
                "title": ch.get("title", f"Chapter {ch.get('chapter_id')}"),
                "content": ch.get("content", "")
            })
        
        return {
            "finalized_text": {"chapters": text_only_chapters}
        }
        
    except Exception as e:
        logger.error(f"Finalizer text optimization error: {e}")
        text_only_chapters = []
        for ch in ordered_chapters:
            text_only_chapters.append({
                "chapter_id": ch["chapter_id"],
                "title": ch.get("title", f"Chapter {ch['chapter_id']}"),
                "content": ch.get("content", "")
            })
        return {
            "finalized_text": {"chapters": text_only_chapters}
        }


async def finalizer_image_agent(state: StoryState) -> Dict[str, Any]:
    """Finalizes images only, returns chapter_id and image in order (1-4)"""
    images_list = []
    for chapter in state.get("chapters", []):
        if "image" in chapter:
            images_list.append({
                "chapter_id": chapter["chapter_id"],
                "image": chapter["image"]
            })
    
    images_list.sort(key=lambda x: x["chapter_id"])
    images_map = {img["chapter_id"]: img["image"] for img in images_list}
    
    image_only_chapters = []
    for chapter_id in range(1, 5):
        image_only_chapters.append({
            "chapter_id": chapter_id,
            "image": images_map.get(chapter_id, None)
        })
    
    return {"finalized_images": {"chapters": image_only_chapters}}
