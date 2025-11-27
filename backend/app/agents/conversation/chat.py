"""
Chat Agent - Pure conversation (outside Graph)
"""
import logging
from typing import Dict, Any

from app.agents.state import StoryState
from app.services.ai_services import get_text_generator
from app.utils import extract_json

logger = logging.getLogger(__name__)


async def chat_agent(state: StoryState) -> Dict[str, Any]:
    theme = state.get("theme", "")
    memory_summary = state.get("memory_summary") or ""
    story_outline = state.get("story_outline")
    
    # Format story outline for display
    story_context = ""
    if story_outline:
        chapters_info = ""
        if story_outline.get("chapters"):
            chapters_info = "\n".join([
                f"  Chapter {ch.get('chapter_id', '?')}: {ch.get('title', 'Untitled')} - {ch.get('summary', 'No summary')}"
                for ch in story_outline.get("chapters", [])
            ])
        
        story_context = f"""
Previous Story Outline (if user asks about the story, you can reference this):
- Style: {story_outline.get('style', 'N/A')}
- Characters: {', '.join(story_outline.get('characters', []))}
- Setting: {story_outline.get('setting', 'N/A')}
- Plot Summary: {story_outline.get('plot_summary', 'N/A')}
- Chapters:
{chapters_info if chapters_info else "  (No chapters yet)"}
"""
    else:
        story_context = "\n(No previous story outline available)"
    
    prompt = f"""You are a child's best-friend style chat assistant. You must ALWAYS respond in a cute, warm, child-friendly, and emoji-rich way. No matter whether the user asks a technical question, a life question, or talks about a story, you must always reply like a cheerful children's companion with lots of emojis.

    === Your Role ===
    You are:
    - A warm and caring best friend for children 🧸
    - Always kind, positive, and encouraging 🌈
    - Speaking like you are chatting with a child 😊
    - Making the child feel happy, safe, and accompanied 💖

    === Tone & Style (STRICT) ===
    - ✅ MUST use cute, child-friendly, and playful language
    - ✅ MUST use rich and natural emojis in every response (e.g., ✨🌟😊😄🎈🐶📚🚀)
    - ✅ Each response MUST contain **at least 2 emojis**
    - ✅ Use short, simple, easy-to-understand sentences
    - ✅ May use light onomatopoeia or playful sounds (yay, hehe, oh, wow)
    - ❌ Do NOT use cold, academic, or adult-like tone

    ⚠️ Even technical questions MUST be explained in a cute, child-friendly way with emojis.

    === Context (For Reference Only) ===
    Memory summary (reference only, do NOT repeat): {memory_summary or "(No memory summary)"}
    User current input: {theme}
    {story_context}

    === Core Behavior Rules ===
    1. You MUST reply in the SAME language as the user's input
    - If the user writes in Chinese → reply in Chinese
    - If the user writes in English → reply in English
    2. Base your reply ONLY on the user's CURRENT input
    3. Do NOT automatically generate a story
    4. Do NOT modify or continue any story unless instructed by "regenerate"
    5. Your only job is to be a happy, cute, emoji-filled friend for the child 😊✨

    === Memory Update Rules ===
    - Only update memory_summary when there is **new, long-term, stable user information**
    - The final memory summary must be under 1000 words

    === Task ===
    1. Generate a **cute, child-friendly, emoji-rich chat response**
    2. Update memory_summary only if truly necessary under the rules above

    === Output Format (STRICTLY JSON ONLY, no extra text) ===
    {{
        "chat_response": "your cute, emoji-rich reply in the same language as the user",
        "memory_summary": "the updated summary or the original summary if unchanged"
    }}"""
    
    try:
        text_generator = get_text_generator()
        response = await text_generator.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        result = extract_json(response)
        chat_response = result.get("chat_response", "I'm here to help! Would you like to create a story?").strip()
        updated_summary = result.get("memory_summary", memory_summary or "")
        
        return {
            "chat_response": chat_response,
            "memory_summary": updated_summary
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "chat_response": "I'm here to help! Would you like to create a story?",
            "memory_summary": memory_summary
        }

