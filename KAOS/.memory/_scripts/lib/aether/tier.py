"""Tier resolution — single source of truth for model→tier mapping."""


def resolve_tier(model: str) -> str:
    if model == "go-kimi-latest":
        return "kimi"
    if model == "go-pro":
        return "pro"
    if model == "go-mimo":
        return "mimo"
    return "flash"
