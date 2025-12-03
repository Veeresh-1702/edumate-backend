import json
import re

def try_parse_structured_response(raw: str):
    # Remove surrounding markdown fences if any
    cleaned = raw.strip()
    cleaned = re.sub(r"```(?:json)?", "", cleaned)
    cleaned = cleaned.replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except Exception:
        # Attempt to extract JSON object substring
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None
    return None