"""
FinalizerAgent - Reentrant agent that processes text first, then images
Can be triggered multiple times: once when writers complete, once when illustrators complete
"""
import logging
from typing import Dict, Any

from app.agents.state import StoryState
from app.services.ai_services import get_text_generator
from app.utils import extract_json

logger = logging.getLogger(__name__)


async def finalizer_agent(state: StoryState) -> Dict[str, Any]:
    """
    Reentrant agent that can be triggered multiple times:
    1. When all writers complete: optimizes text and returns optimized chapters
    2. When all illustrators complete: merges images and returns complete chapters
    """
    completed_writers = state.get("completed_writers", [])
    completed_image_gens = state.get("completed_image_gens", [])
    
    writers_done = len(completed_writers) == 4
    images_done = len(completed_image_gens) == 4
    
    if writers_done and not images_done:
        return await _process_text_optimization(state)
    elif images_done:
        return await _process_image_merge(state)
    else:
        logger.warning(f"Finalizer triggered but not ready: writers={len(completed_writers)}/4, images={len(completed_image_gens)}/4")
        return {}


async def _process_text_optimization(state: StoryState) -> Dict[str, Any]:
    """Optimize text content when all writers complete"""
    chapters_list = []
    for chapter in state.get("chapters", []):
        if "content" in chapter:
            chapters_list.append({
                "chapter_id": chapter["chapter_id"],
                "title": chapter.get("title", f"Chapter {chapter['chapter_id']}"),
                "content": chapter["content"]
            })
    
    chapters_list.sort(key=lambda x: x["chapter_id"])
    
    chapters_text = "\n\n".join([
        f"Chapter {ch['chapter_id']}: {ch['title']}\n{ch['content']}"
        for ch in chapters_list
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

Return JSON with optimized chapters:
{{
    "chapters": [
        {{"chapter_id": 1, "title": "Title", "content": "Optimized content"}},
        {{"chapter_id": 2, "title": "Title", "content": "Optimized content"}},
        {{"chapter_id": 3, "title": "Title", "content": "Optimized content"}},
        {{"chapter_id": 4, "title": "Title", "content": "Optimized content"}}
    ]
}}

IMPORTANT: Only optimize the text content, keep the same chapter structure and titles. Return ONLY valid JSON."""

    try:
        response_text = await get_text_generator().generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )
        
        response_json = extract_json(response_text)
        if not response_json:
            logger.warning("FinalizerAgent received empty JSON, using original chapters")
            optimized_chapters = chapters_list
        else:
            optimized_chapters = response_json.get("chapters", chapters_list)
        
        return {"finalized_story": {"chapters": optimized_chapters}}
        
    except Exception as e:
        logger.error(f"Finalizer text optimization error: {e}")
        return {"finalized_story": {"chapters": chapters_list}}


async def _process_image_merge(state: StoryState) -> Dict[str, Any]:
    images_list = []
    for chapter in state.get("chapters", []):
        if "image" in chapter:
            images_list.append({
                "chapter_id": chapter["chapter_id"],
                "image": chapter["image"]
            })
    
    images_list.sort(key=lambda x: x["chapter_id"])
    
    return {"finalized_story": {"chapters": images_list}}

