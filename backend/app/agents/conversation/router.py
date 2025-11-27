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
    
    prompt = f"""You are a router agent. Classify user intent based on the current user input.

    === Input ===
    User input: {user_input}
    Current summary: {current_summary or "(No previous summary)"}

    === Task 1: Intent Classification ===
    Analyze ONLY the user's CURRENT input to determine their intent.
    Do NOT infer intent from previous turns except to distinguish between "new story" and "current story".

    Intent definitions (STRICT):

    1. "story_generate" — ONLY for creating a BRAND NEW story from scratch.
    Choose this if and ONLY if the user explicitly requests to create or generate a NEW story.
    Examples:
    - 写一个新的故事
    - 生成一个全新的故事
    - 给我一个新故事
    - create a new story
    - write a brand new story

    Do NOT choose this if the user is modifying, continuing, or adjusting an existing story.

    2. "regenerate" — For ANY modification, continuation, or rewriting of the CURRENT story.
    Choose this if the user explicitly requests to:
    - Modify any part of the current story
    - Change characters, setting, plot, or ending
    - Continue the existing story
    - Rewrite the current story

    Examples:
    - 把这个故事的主角改成小狗
    - 换一个结局
    - 继续这个故事
    - 把背景改成太空
    - rewrite this story
    - continue the story

    3. "chat" — For all NON-generation behaviors, including:
    - Asking questions about the story
    - Discussing or evaluating the story
    - Casual conversation
    - Technical or system questions
    - Any input that does NOT explicitly request creation or modification

    Examples:
    - 这个故事讲什么？
    - 主角是谁？
    - 这个结局合理吗？
    - 你好
    - vite 是 hot reload 吗

    STRICT RULES:
    - Classification MUST be based ONLY on the user's CURRENT input.
    - NEVER infer generation or modification intent from context alone.
    - NEVER choose "story_generate" unless the user clearly wants a BRAND NEW story.
    - ANY request that modifies or continues the current story MUST be "regenerate".
    - Story-related QUESTIONS must ALWAYS be "chat".
    - IF there is ANY uncertainty, ambiguity, or missing explicit instruction, ALWAYS choose "chat".

    === Task 2: Summary Update ===
    Based on current summary and user input, generate updated summary:
    1. Extract new factual information NOT already in current summary
    2. Add only truly new information
    3. Keep the summary concise and under 500 words
    4. If the input is only a question or generic chat, the summary may remain unchanged

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
        intent = result.get("intent", "chat")
        summary = result.get("memory_summary", current_summary)
        
        # Validate intent, default to "chat" if invalid (safer default)
        valid_intents = ["story_generate", "chat", "regenerate"]
        if intent not in valid_intents:
            logger.warning(f"Invalid intent '{intent}', defaulting to 'chat'")
            intent = "chat"
        
        return {
            "intent": intent,
            "memory_summary": summary
        }
    except Exception as e:
        logger.error(f"Router error: {e}")
        return {
            "intent": "chat",
            "memory_summary": current_summary
        }
