"""Shared utility functions extracted from agent_executor.py.

Provides context management, LLM routing, subtask detection, code analysis,
and scoring helpers used across agent nodes.

This file is the canonical home for these functions.
agent_executor.py imports and re-exports them for backward compatibility.
"""

import json
import logging
import re
import subprocess
import tempfile
import threading
from functools import lru_cache

from lib.config import (
    EXECUTOR_ENABLED,
    EXECUTOR_TIMEOUT,
    HERMES_ENABLED,
    HYBRID_PRO_ENABLED,
    RAG_ENABLED,
    VAULT_ROOT,
)
from lib.hermes_bridge import pipeline_notify
from lib.llm import agent_llm_call
from lib.rag_injector import inject_context

logger = logging.getLogger(__name__)

RAW_DIR = VAULT_ROOT / "_pipeline" / "raw"
CONTEXT_PATH = VAULT_ROOT / "_pipeline" / "context.json"
PLAN_PATH = VAULT_ROOT / "_pipeline" / "plan.json"

RAW_DIR.mkdir(parents=True, exist_ok=True)

_ctx_cache: dict | None = None
_ctx_dirty: bool = False
_ctx_lock: threading.Lock = threading.Lock()

AGENT_SLUGS = {
    "aletheia": "raw",
    "kosmos": "schema",
    "metis": "wiki",
    "kratos": "code",
    "mnemosyne": "wiki",
}

COMPLEXITY_KEYWORDS = {
    "alta": [
        "microservicio",
        "distribuido",
        "escalable",
        "cluster",
        "kubernetes",
        "orquestacion",
        "eventos",
        "cqrs",
        "event-sourcing",
        "multi-tenant",
        "alta disponibilidad",
        "ha",
        "failover",
        "replicacion",
    ],
    "moderada": [
        "api",
        "rest",
        "graphql",
        "base de datos",
        "autenticacion",
        "jwt",
        "oauth",
        "cache",
        "cola",
        "middleware",
        "testing",
        "ci/cd",
    ],
    "simple": ["script", "funcion", "componente", "vista", "formulario", "pagina", "endpoint", "consulta", "archivo"],
}

SUBTASK_PATTERNS = [
    ("research", "investigacion", "research", "analisis", "requerimientos", "estudio", "explorar"),
    (
        "architecture",
        "arquitectura",
        "adr",
        "c4",
        "diseno",
        "disenar",
        "estructura",
        "patron",
        "patrones",
        "microservicio",
        "distribuido",
        "escalable",
    ),
    ("strategy", "estrategia", "roadmap", "okr", "plan", "planeacion", "hoja de ruta"),
    (
        "code",
        "implementacion",
        "codigo",
        "programar",
        "desarrollar",
        "implementa",
        "implementar",
        "construir",
        "crear",
        "hacer",
        "api",
        "rest",
        "endpoint",
        "funcion",
        "clase",
        "modulo",
        "script",
        "algoritmo",
    ),
    ("test", "test", "testing", "pruebas", "unit", "integracion"),
    ("docs", "documentacion", "docs", "wiki", "readme", "manual"),
]

_CODECOMPLETE_KEYWORDS = [
    "def ",
    "class ",
    "function",
    "import ",
    "fn ",
    "pub ",
    "```",
    "#include",
    "package ",
    "module ",
    "impl ",
    "trait ",
    "enum ",
    "struct ",
]

DANGEROUS_PATTERNS = [
    (r"eval\s*\(", "eval() usage"),
    (r"exec\s*\(", "exec() usage"),
    (r"__import__\s*\(", "dynamic import"),
    (r"pickle\.loads?\s*\(", "unsafe deserialization"),
    (r"os\.system\s*\(", "shell injection risk"),
    (r"subprocess\.\w+.*shell\s*=\s*True", "shell=True risk"),
    (r"(?i)password\s*=\s*['\"]", "hardcoded password"),
    (r"(?i)api_key\s*=\s*['\"]", "hardcoded API key"),
    (r"(?i)secret\s*=\s*['\"]", "hardcoded secret"),
    (r"(?i)token\s*=\s*['\"]", "hardcoded token"),
]

# ── Context Cache Management ────────────────────────────────────────


def load_context() -> dict:
    """Load cross-agent context from _pipeline/context.json with caching."""
    global _ctx_cache
    with _ctx_lock:
        if _ctx_cache is not None:
            return _ctx_cache
        if CONTEXT_PATH.exists():
            try:
                _ctx_cache = json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
                return _ctx_cache
            except Exception:
                pass
        _ctx_cache = {"agents": [], "context_summary": {}, "cross_agent": {}}
        return _ctx_cache


def save_context(ctx: dict) -> None:
    """Update in-memory context cache (call flush_context to persist)."""
    global _ctx_cache, _ctx_dirty
    with _ctx_lock:
        _ctx_cache = ctx
        _ctx_dirty = True


def flush_context() -> None:
    """Write dirty context to disk."""
    global _ctx_dirty
    with _ctx_lock:
        if _ctx_cache is not None and _ctx_dirty:
            CONTEXT_PATH.write_text(
                json.dumps(_ctx_cache, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            _ctx_dirty = False


def reset_context_cache() -> None:
    """Clear the in-memory context cache (forces re-read from disk)."""
    global _ctx_cache, _ctx_dirty
    with _ctx_lock:
        _ctx_cache = None
        _ctx_dirty = False


# ── Text / Slug Utilities ───────────────────────────────────────────


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug (max 60 chars)."""
    slug = re.sub(r"[^a-z0-9\s-]", "", text.lower())
    return re.sub(r"\s+", "-", slug)[:60]


def detect_subtasks(topic: str) -> list[dict]:
    """Detect subtasks from topic text using keyword matching."""
    tl = topic.lower()
    detected = []
    for task_id, name, *keywords in SUBTASK_PATTERNS:
        if any(kw in tl for kw in [name] + keywords):
            detected.append({"id": task_id, "name": name, "enabled": True})
    if not detected:
        detected = [{"id": "research", "name": "research", "enabled": True}]
    return detected


def detect_complexity(topic: str) -> str:
    """Detect complexity level from topic by keyword frequency."""
    tl = topic.lower()
    weights = {"alta": 0, "moderada": 0, "simple": 0}
    for level, keywords in COMPLEXITY_KEYWORDS.items():
        weights[level] = sum(1 for kw in keywords if kw in tl)
    return max(weights, key=weights.get)


# ── LLM / Executor Routing ──────────────────────────────────────────


def executor_call(prompt: str, agent_name: str, model_override: str = "") -> str:
    """Invoke opencode CLI subprocess as the agent executor.

    Falls back to direct LLM call if CLI is unavailable or times out.
    """
    try:
        if len(prompt) > 7000:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
                f.write(prompt)
                tmp = f.name
            result = subprocess.run(["opencode", "-p", tmp], capture_output=True, text=True, timeout=EXECUTOR_TIMEOUT)
        else:
            result = subprocess.run(
                ["opencode", "-p", prompt], capture_output=True, text=True, timeout=EXECUTOR_TIMEOUT
            )
        output = result.stdout.strip()
        if output:
            return output
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return agent_llm_call(agent_name, prompt, model_override=model_override)


def llm_or_executor_call(
    agent_name: str,
    prompt: str,
    model_override: str = "",
    step_type: str = None,
) -> str:
    """Route: executor → LLM, with optional model override and step type."""
    if EXECUTOR_ENABLED:
        return executor_call(prompt, agent_name, model_override)
    kwargs = {}
    if model_override:
        kwargs["model_override"] = model_override
    if step_type:
        kwargs["step_type"] = step_type
    return call_with_langfuse(agent_name, prompt, **kwargs)


def call_with_langfuse(
    agent_name: str,
    prompt: str,
    trace_id: str = "",
    **kwargs,
):
    """Execute LLM call with Langfuse tracing."""
    try:
        from lib.langfuse_handler import get_handler

        handler = get_handler()
        if handler:
            return agent_llm_call(agent_name, prompt, langfuse_handler=handler, **kwargs)
    except Exception:
        pass
    return agent_llm_call(agent_name, prompt, **kwargs)


@lru_cache(maxsize=50)
def _cached_rag(topic: str) -> str:
    return inject_context(topic)


def build_rag_context(topic: str) -> str:
    """Build RAG context string for the given topic."""
    if not RAG_ENABLED:
        return ""
    try:
        return _cached_rag(topic)
    except Exception:
        return ""


def notify_step(state, agent_name: str, status: str = "in_progress"):
    """Notify Hermes pipeline of a step status change."""
    if HERMES_ENABLED:
        pipeline_notify(state, agent_name, status)


# ── Output Validation ──────────────────────────────────────────


def validate_aletheia_output(raw: str, topic: str = "") -> dict:
    """Validates Aletheia research output against quality schema.

    Returns dict with: valid (bool), score (0-1), warnings (list), sections_found (list).
    Auto-persists to score store if topic is provided.
    """
    required_sections = [
        "resumen ejecutivo",
        "hallazgos",
        "fuentes",
        "conclusiones",
        "recomendaciones",
    ]
    found = [s for s in required_sections if s.lower() in raw.lower()]
    missing = [s for s in required_sections if s.lower() not in raw.lower()]

    has_sources = bool(re.findall(r"https?://[^\s\)\]]+", raw))
    has_wikilinks = "[[" in raw
    min_length = len(raw.strip()) > 500
    has_confidence = bool(re.search(r"(?:confianza|matriz|certeza|fuente)", raw.lower()))

    warnings = []
    if missing:
        warnings.append(f"Faltan secciones: {', '.join(missing)}")
    if not has_sources:
        warnings.append("Sin URLs de fuentes")
    if not min_length:
        warnings.append("Output demasiado corto (<500 chars)")
    if not has_confidence:
        warnings.append("Sin matriz de confianza/certeza")

    score = round(
        (len(found) / len(required_sections)) * 0.5  # 50% por secciones
        + (0.15 if has_sources else 0)  # 15% fuentes
        + (0.10 if has_wikilinks else 0)  # 10% wikilinks
        + (0.10 if min_length else 0)  # 10% longitud mínima
        + (0.15 if has_confidence else 0),  # 15% confianza
        3,
    )

    result = {
        "valid": score >= 0.6,
        "score": score,
        "warnings": warnings,
        "sections_found": found,
        "sections_missing": missing,
        "has_sources": has_sources,
        "has_wikilinks": has_wikilinks,
    }

    if topic:
        try:
            from lib.aletheia_score_store import save as _save_score
            _save_score(topic=topic, score=score, valid=score >= 0.6,
                       sections_found=found, warnings=warnings)
        except Exception:
            pass

    return result


def is_complete_code(text: str) -> bool:
    """Heuristic to determine if Kratos output contains real code.

    Checks for: code blocks, function/class definitions, imports,
    and minimum structural length.
    """
    if not text or len(text) < 200:
        return False
    has_code_block = "```" in text
    has_definition = any(kw in text for kw in _CODECOMPLETE_KEYWORDS)
    has_structure = bool(re.search(r"(?m)^#{1,3}\s", text))
    return has_code_block and (has_definition or has_structure)


def check_security(code: str) -> list:
    """Check code for dangerous patterns. Returns list of issue descriptions."""
    issues = []
    for pattern, desc in DANGEROUS_PATTERNS:
        if re.search(pattern, code):
            issues.append(f"security: {desc}")
    return issues


def resolve_kratos_model(state: dict) -> str:
    """Return model key: go-flash default, go-pro if hybrid enabled + alta complexity."""
    if HYBRID_PRO_ENABLED:
        if complexity_override and complexity_override.lower() == "alta":
            return "go-pro"
        if state and state.get("plan", {}).get("complexity", "").lower() == "alta":
            return "go-pro"
    return "go-flash"


def extract_json_from_output(text: str) -> dict:
    """Try to extract JSON object from agent output."""
    # Try direct parse first
    try:
        return json.loads(text)
    except Exception:
        pass
    # Try between ```json markers
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except Exception:
            pass
    return {}
