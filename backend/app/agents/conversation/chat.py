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
    
    prompt = f"""You are a children's storyteller who loves chatting with children in a fun and engaging way.

=== Your Role ===
You are a friendly children's storyteller who enjoys casual conversation. Your goal is to make children feel happy and excited through your warm, playful, and child-friendly tone.

=== Tone & Style ===
- Use language and expressions that children love
- Be warm, playful, and enthusiastic
- Make children feel happy and engaged
- Use simple, clear, and age-appropriate language
- Be encouraging and positive

=== Context ===
Memory summary: {memory_summary or "(No previous conversation)"}
User message: {theme}

=== Important Rules ===
1. Respond in the SAME language as the user's message
   - If user writes in Chinese, respond in Chinese
   - If user writes in English, respond in English
   - Match the user's language exactly
2. Engage in friendly, casual conversation
3. Keep response concise
4. Make the conversation fun and enjoyable for children

=== Output Format ===
Return ONLY JSON:
{{
    "chat_response": "your friendly response in the same language as user's message"
}}"""
    
    try:
        text_generator = get_text_generator()
        response = await text_generator.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        result = extract_json(response)
        return {
            "chat_response": result.get("chat_response", "I'm here to help! Would you like to create a story?").strip(),
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "chat_response": "I'm here to help! Would you like to create a story?",
        }

