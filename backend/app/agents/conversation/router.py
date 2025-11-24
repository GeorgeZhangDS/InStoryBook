"""
Router Agent - Conversation management (outside Graph)
"""
import logging
from typing import Dict, Any

from app.agents.state import StoryState
from app.services.ai_services import get_text_generator
from app.utils import extract_json

logger = logging.getLogger(__name__)


async def router_agent(state: StoryState) -> Dict[str, Any]:
    user_input = state.get("theme", "").strip()
    current_summary = (state.get("memory_summary") or "").strip()
    
    if not user_input:
        return {
            "intent": "story_generate",
            "memory_summary": current_summary
        }
    
    prompt = f"""You are a router agent. Classify user intent and update memory summary.

=== Input ===
User input: {user_input}
Current summary: {current_summary or "(No previous summary)"}

=== Task 1: Intent Classification ===
Based on user input, classify intent:
- "chat": User is just chatting or asking unrelated questions
- "story_generate": User wants to generate or modify story (default)
- "regenerate": User wants to restart/regenerate

=== Task 2: Summary Update ===
Based on current summary and user input, generate updated summary:
1. Extract new information from user input that is NOT already in current summary
2. Add only the new information to current summary
3. Keep summary concise and under 500 words, compress it while keeping key info

=== Output Format ===
Return ONLY JSON:
{{
    "intent": "story_generate" | "chat" | "regenerate",
    "memory_summary": "updated summary based on current summary + new info from user input"
}}"""
    
    try:
        text_generator = get_text_generator()
        response = await text_generator.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        result = extract_json(response)
        intent = result.get("intent", "story_generate")
        summary = result.get("memory_summary", current_summary)
        
        return {
            "intent": intent if intent in ["story_generate", "chat", "regenerate"] else "story_generate",
            "memory_summary": summary
        }
    except Exception as e:
        logger.error(f"Router error: {e}")
        return {
            "intent": "story_generate",
            "memory_summary": current_summary
        }
