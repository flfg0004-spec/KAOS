import json
from datetime import datetime
from lib.config import MAX_TOKENS, TOKEN_RATIO, PRESSURE_THRESHOLDS


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, round(len(text) / TOKEN_RATIO))


def get_level(current: int, max_tokens: int = MAX_TOKENS) -> dict:
    ratio = current / max_tokens if max_tokens > 0 else 0
    pressure = round(ratio * 100, 1)

    if ratio >= PRESSURE_THRESHOLDS["critical"]:
        return {
            "pressure": pressure,
            "level": "critical",
            "action": "archive",
            "recommendation": "ARCHIVE: Move working memory to raw/archive/. Keep only core context.",
        }
    if ratio >= PRESSURE_THRESHOLDS["high"]:
        return {
            "pressure": pressure,
            "level": "high",
            "action": "compress",
            "recommendation": "COMPRESS: Summaries (~500 chars per page). Cache LRU limited to 3.",
        }
    if ratio >= PRESSURE_THRESHOLDS["warning"]:
        return {
            "pressure": pressure,
            "level": "warning",
            "action": "trim",
            "recommendation": "TRIM: Load only index + agent entity. Skip schema/log/policy.",
        }
    return {
        "pressure": pressure,
        "level": "normal",
        "action": "none",
        "recommendation": "No action needed.",
    }


def check(current: int, max_tokens: int = MAX_TOKENS) -> str:
    result = get_level(current, max_tokens)
    result["contextTokens"] = current
    result["maxTokens"] = max_tokens
    result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return json.dumps(result)
