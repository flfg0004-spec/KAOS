"""Plugin registry for quality gates."""

_GATE_REGISTRY: dict[str, dict] = {}


def register_gate(name: str, func, weight: float = 0.0, languages: list[str] | None = None) -> None:
    _GATE_REGISTRY[name] = {"func": func, "weight": weight, "languages": languages or ["python"]}


def get_gate(name: str) -> dict | None:
    return _GATE_REGISTRY.get(name)


def list_gates() -> list[str]:
    return list(_GATE_REGISTRY.keys())
