"""
JSON utility functions for extracting and parsing JSON from text
"""
import json
import re
from typing import Dict, Any


def extract_json(text: str) -> Dict[str, Any]:
    """ Extract JSON from text, handling markdown code blocks """
    text = text.strip()
    json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(0))
    return {}

