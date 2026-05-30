"""kosmos_evaluator_v2.py — Evaluación Dimensional de KosmosV2.

5 dimensiones alineadas con eval-profile.yaml:
- Veracidad (V): ¿El output está basado en hechos verificables?
- Coherencia (C): ¿El output es internamente consistente?
- Completitud (CP): ¿Cubre todos los aspectos requeridos?
- Reproducibilidad (R): ¿Puede otro agente reproducir el análisis?
- Utilidad (U): ¿Es accionable y relevante para el destinatario?

Cada dimensión tiene score 0-100, thresholds por perfil (eval-profile.yaml).

ADVERTENCIA: NO usa DeepEval. Usa SOLO heurística basada en reglas + análisis
de contenido. La evaluación es rápida (<1s) y no dependiente de LLM externo.
"""

import json
import logging
import math
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _load_profiles_from_yaml(yaml_path: str = None) -> Tuple[Dict, Dict]:
    """Load dimension weights and thresholds from eval-profile.yaml.

    Si el archivo no existe o hay error, retorna los valores hardcodeados como fallback.
    Esto asegura que los perfiles SIEMPRE estén sincronizados con el YAML.

    Args:
        yaml_path: Optional explicit path to eval-profile.yaml. If None,
                   busca en ``.memory/schema/eval-profile.yaml`` relativo al módulo.

    Returns:
        Tuple of (weights_dict, thresholds_dict) with the same structure as
        DIMENSION_WEIGHTS and PROFILE_THRESHOLDS.
    """
    if yaml_path is None:
        # .memory/_scripts/lib/kosmos_evaluator_v2.py → .memory/schema/eval-profile.yaml
        base = Path(__file__).resolve().parent.parent.parent  # → .memory/
        yaml_path = str(base / "schema" / "eval-profile.yaml")

    yaml_file = Path(yaml_path)
    if not yaml_file.exists():
        logger.warning("eval-profile.yaml not found at %s — using hardcoded defaults", yaml_file)
        # Import here to avoid circular dependency at module level
        return DIMENSION_WEIGHTS, PROFILE_THRESHOLDS

    try:
        text = yaml_file.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Cannot read eval-profile.yaml: %s — using hardcoded defaults", exc)
        return DIMENSION_WEIGHTS, PROFILE_THRESHOLDS

    weights: Dict[str, Dict[str, float]] = {}
    thresholds: Dict[str, Dict[str, float]] = {}
    current_profile: str | None = None
    current_section: str | None = None
    # Track indentation of the current section to detect when it ends
    section_indent: int = -1

    # Skip to profiles section
    in_profiles = False
    for line in text.split("\n"):
        stripped = line.rstrip()

        # Detect top-level profiles: key
        if re.match(r"^profiles:\s*$", stripped):
            in_profiles = True
            continue

        if not in_profiles:
            continue

        # Skip empty lines
        if not stripped.strip():
            continue

        # Detect new profile (2-space indent, word followed by colon, not a known key)
        profile_match = re.match(r"^  ([a-z_]\w*):\s*$", stripped)
        if profile_match:
            name = profile_match.group(1)
            if name not in ("label", "description", "weights", "thresholds",
                            "anti_hallucination", "kratos"):
                current_profile = name
                current_section = None
                section_indent = -1
                if name not in weights:
                    weights[name] = {}
                    thresholds[name] = {}
                continue

        # Detect section headers within a profile (4-space indent)
        section_match = re.match(r"^    ([a-z_]\w*):\s*$", stripped)
        if section_match and current_profile:
            section = section_match.group(1)
            if section == "weights":
                current_section = "weights"
                section_indent = 6
            elif section == "thresholds":
                current_section = "thresholds"
                section_indent = 6
            else:
                # Unknown section (e.g. anti_hallucination, kratos) — skip it
                current_section = None
                section_indent = -1
            continue

        # Detect key-value pairs within a section (6-space indent)
        kv_match = re.match(r"^      ([a-z_]\w*):\s*(.*)$", stripped)
        if kv_match and current_profile and current_section:
            key = kv_match.group(1)
            raw_value = kv_match.group(2).strip().strip('"').strip("'")
            # Parse numeric values
            try:
                if raw_value and re.match(r"^-?\d+\.?\d*$", raw_value):
                    value: float | int = float(raw_value) if "." in raw_value else int(raw_value)
                elif raw_value.lower() in ("true", "false"):
                    continue  # skip booleans
                else:
                    continue  # skip strings
            except (ValueError, TypeError):
                continue

            target = weights if current_section == "weights" else thresholds
            target[current_profile][key] = value

    # Validate we got at least something
    if not weights:
        logger.warning("No profiles parsed from eval-profile.yaml — using hardcoded defaults")
        return DIMENSION_WEIGHTS, PROFILE_THRESHOLDS

    logger.info("Loaded %d profiles from eval-profile.yaml", len(weights))
    return weights, thresholds


# ── Dimension weights per profile (from eval-profile.yaml) ──

DIMENSION_WEIGHTS: Dict[str, Dict[str, float]] = {
    "exploracion": {
        "veracidad": 0.15,
        "coherencia": 0.15,
        "completitud": 0.20,
        "reproducibilidad": 0.15,
        "utilidad": 0.35,
    },
    "desarrollo": {
        "veracidad": 0.20,
        "coherencia": 0.20,
        "completitud": 0.20,
        "reproducibilidad": 0.20,
        "utilidad": 0.20,
    },
    "produccion": {
        "veracidad": 0.30,
        "coherencia": 0.25,
        "completitud": 0.20,
        "reproducibilidad": 0.15,
        "utilidad": 0.10,
    },
    "auditoria": {
        "veracidad": 0.35,
        "coherencia": 0.25,
        "completitud": 0.25,
        "reproducibilidad": 0.10,
        "utilidad": 0.05,
    },
    "qa": {
        "veracidad": 0.30,
        "coherencia": 0.25,
        "completitud": 0.20,
        "reproducibilidad": 0.15,
        "utilidad": 0.10,
    },
}

# ── Thresholds per profile ──

PROFILE_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "exploracion": {
        "veracidad_min": 50,
        "coherencia_min": 40,
        "completitud_min": 40,
        "reproducibilidad_min": 30,
        "utilidad_min": 50,
        "composite_good": 60,
        "composite_critical": 30,
    },
    "desarrollo": {
        "veracidad_min": 65,
        "coherencia_min": 60,
        "completitud_min": 55,
        "reproducibilidad_min": 50,
        "utilidad_min": 55,
        "composite_good": 70,
        "composite_critical": 40,
    },
    "produccion": {
        "veracidad_min": 80,
        "coherencia_min": 75,
        "completitud_min": 70,
        "reproducibilidad_min": 60,
        "utilidad_min": 50,
        "composite_good": 80,
        "composite_critical": 55,
    },
    "auditoria": {
        "veracidad_min": 85,
        "coherencia_min": 80,
        "completitud_min": 75,
        "reproducibilidad_min": 70,
        "utilidad_min": 40,
        "composite_good": 85,
        "composite_critical": 60,
    },
    "qa": {
        "veracidad_min": 85,
        "coherencia_min": 80,
        "completitud_min": 80,
        "reproducibilidad_min": 75,
        "utilidad_min": 50,
        "composite_good": 80,
        "composite_critical": 65,
    },
}

# ── Heuristic signals per dimension ──

# Veracidad signals: citations, sources, references, evidence, data
_VERACIDAD_PATTERNS = {
    "positive": [
        r'https?://\S+', r'(?:fuente|source|ref)\s*:?\s*\S', r'\*\*Fuente',
        r'(?:evidencia|evidence)\s*:?', r'(?:datos?|data)\s*:?', r'(?:estadística|estadistico|stat)',
        r'(?:cita|cite|citación|referencia)\s*:', r'\[\[\w+', r'basado en',
        r'(?:investigación|research|estudio)\s+', r'según\s+',
        r'(?:reporte|informe|report|paper)\s*:', r'nº?\s*\d+', r'fuentes?',
        r'(?:resultados|hallazgos|findings)', r'(?:análisis|analysis)\s+de',
    ],
    "negative": [
        r'(?:creo|pienso|me parece|quizás|tal vez|maybe|i think)',
    ],
}

# Coherencia signals: logical structure, connectors, consistent formatting
_COHERENCIA_PATTERNS = {
    "positive": [
        r'^##\s+\w', r'^###\s+\w', r'^\d+\.\s', r'^- ', r'\* ',  # structure
        r'(?:por lo tanto|therefore|consecuentemente|hence)',
        r'(?:en primer|primero|first|second|segundo|tercero)',
        r'(?:por otro lado|on the other hand|however|sin embargo)',
        r'(?:además|furthermore|moreover|adicionalmente)',
        r'(?:en conclusión|conclusion|in summary|resumiendo)',
        r'(?:consistente|consistency|coherente|coherence)',
        r'(?:porque|because|ya que|since|dado que)',
        r'(?:no obstante|nevertheless|nonetheless)',
        r'(?:así mismo|likewise|similarly|igualmente)',
        r'(?:como resultado|as a result|consequently)',
        r'\|.*\|.*\|',  # table
        r'```\w*\n',  # code blocks
    ],
    "negative": [
        r'(?:\n\n\n+)', r'(?:(?:^|\n)#{4,}\s)',  # excess spacing or bad headings
    ],
}

# Completitud signals: coverage of required sections
_COMPLETITUD_PATTERNS = {
    "positive": [
        r'^#\s+.*(?:ADR|adr)',  # has title
        r'^##\s*Contexto', r'^##\s*contexto', r'^##\s*CONTEXTO',
        r'^##\s*Decisión', r'^##\s*Decision', r'^##\s*DECISIÓN',
        r'^##\s*Opciones', r'^##\s*options', r'^##\s*alternativas',
        r'^##\s*Consecuencias', r'^##\s*consequences',
        r'^##\s*Recomendacion', r'^##\s*Recommendation',
        r'^##\s*Anális', r'^##\s*Analysis',
        r'^##\s*Diagram', r'^##\s*Diagrama',
        r'^##\s*Referencias', r'^##\s*referencias',
        r'^##\s*Resumen', r'^##\s*Summary', r'^##\s*Ejecutivo',
        r'(?:métricas?|metrics?|scores?)',
    ],
    "negative": [],
}

# Reproducibilidad signals: methodology, steps, replicability
_REPRODUCIBILIDAD_PATTERNS = {
    "positive": [
        r'(?:metodología|methodology|método|method)\s*:',
        r'(?:pasos?|steps?|fases?|phases?)\s*:',
        r'(?:proceso|process|procedimiento|procedure)',
        r'(?:herramientas?|tools?|tecnologías?|technologies?)',
        r'(?:configuración|configuration|setup|set up)',
        r'(?:reproducible|reproducibilidad|replicable)',
        r'(?:código|code|script)\s*:',
        r'(?:comando|command|CLI|terminal)',
        r'(?:versión|version|v?\d+\.\d+\.\d+)',
        r'(?:dependencias?|dependencies?|requirements?)',
        r'(?:instrucciones?|instructions?|guide|guía)',
        r'(?:parámetros?|parameters?|param|args?)',
        r'```(?:bash|sh|shell|python|yaml|json)',  # executable examples
    ],
    "negative": [],
}

# Utilidad signals: actionable recommendations, concrete value
_UTILIDAD_PATTERNS = {
    "positive": [
        r'(?:recomendaci[oó]n|recommendation|sugerencia)s?\s*:',
        r'(?:acción|action|siguiente paso|next step|todo|todos)',
        r'(?:prioridad|priority|prioritario|critical|crítico)',
        r'(?:impacto|impact|afecta|affects)\s*:',
        r'(?:beneficio|benefit|ventaja|advantage|mejora)',
        r'(?:riesgo|risk|mitigación|mitigation)',
        r'(?:implementar|implement|desarrollar|develop)',
        r'(?:propuesta|proposal|plan|plan de acción)',
        r'(?:costo|cost|budget|presupuesto|recursos?)',
        r'(?:ROI|retorno|value|valor|beneficio\s+costo)',
        r'(?:deadline|fecha límite|timeline|cronograma)',
        r'(?:kpi|metric|métrica|indicador|target|objetivo)',
        r'(?:entregable|deliverable|output|resultado)',
    ],
    "negative": [
        r'(?:sin relevancia|no importante|irrelevant|trivial)',
    ],
}

_DIMENSION_PATTERNS = {
    "veracidad": _VERACIDAD_PATTERNS,
    "coherencia": _COHERENCIA_PATTERNS,
    "completitud": _COMPLETITUD_PATTERNS,
    "reproducibilidad": _REPRODUCIBILIDAD_PATTERNS,
    "utilidad": _UTILIDAD_PATTERNS,
}

_RE_TITLE_H1 = re.compile(r'^#\s+(.+)$', re.MULTILINE)
_RE_SECTIONS = re.compile(r'^##\s+(.+)$', re.MULTILINE)
_RE_LISTS = re.compile(r'^[\s]*[-*\d]+[.)]\s', re.MULTILINE)
_RE_CODE_BLOCK = re.compile(r'```')
_RE_TABLE = re.compile(r'\|[^|]+\|')
_RE_LINKS = re.compile(r'\[\[([^\]]+)\]\]')
_RE_WORDS = re.compile(r'\w+')


def _count_sections(text: str) -> int:
    """Count the number of H2 sections (## ...) in text."""
    return len(_RE_SECTIONS.findall(text))


def _count_h1(text: str) -> int:
    """Count H1 titles."""
    return len(_RE_TITLE_H1.findall(text))


def _count_list_items(text: str) -> int:
    """Count list items (both bullet and numbered)."""
    return len(_RE_LISTS.findall(text))


def _count_code_blocks(text: str) -> int:
    """Count code blocks (number of ``` pairs / 2)."""
    return len(_RE_CODE_BLOCK.findall(text)) // 2


def _count_tables(text: str) -> int:
    """Count table rows (rough estimate by | count / columns)."""
    rows = _RE_TABLE.findall(text)
    return len(rows)


def _count_wikilinks(text: str) -> int:
    """Count wikilinks [[...]]."""
    return len(_RE_LINKS.findall(text))


def _count_urls(text: str) -> int:
    """Count http/https URLs."""
    return len(re.findall(r'https?://\S+', text))


def _word_count(text: str) -> int:
    """Count words in text."""
    return len(_RE_WORDS.findall(text))


def _score_dimension_heuristic(text: str, dimension: str) -> Tuple[float, List[str]]:
    """Score a single dimension using heuristic pattern matching.

    Returns:
        Tuple of (score 0-100, list of evidence strings).
    """
    if not text or not text.strip():
        return (0.0, ["empty text"])

    text_lower = text.lower()
    patterns = _DIMENSION_PATTERNS.get(dimension, _VERACIDAD_PATTERNS)
    positives = patterns.get("positive", [])
    negatives = patterns.get("negative", [])

    evidence: List[str] = []
    pos_hits = 0
    neg_hits = 0

    for pat in positives:
        matches = re.findall(pat, text, re.MULTILINE | re.IGNORECASE)
        if matches:
            pos_hits += len(matches)
            evidence.append(f"+{pat[:40]}… ({len(matches)})")

    for pat in negatives:
        matches = re.findall(pat, text, re.MULTILINE | re.IGNORECASE)
        if matches:
            neg_hits += len(matches)
            evidence.append(f"-{pat[:40]}… ({len(matches)})")

    # Base score: start at a moderate level and adjust
    base = 50.0
    base += min(40.0, pos_hits * 8.0)          # up to +40 for positive signals
    base -= min(30.0, neg_hits * 10.0)          # up to -30 for negative signals

    # Dimension-specific bonuses
    wc = _word_count(text)
    sec_count = _count_sections(text)
    list_count = _count_list_items(text)
    code_blocks = _count_code_blocks(text)
    tables = _count_tables(text)
    urls = _count_urls(text)
    wikilinks = _count_wikilinks(text)

    if dimension == "veracidad":
        # More URLs/sources = higher veracidad
        base += min(20, urls * 5)
        base += min(10, wikilinks * 2)
        if urls >= 3:
            evidence.append("3+ external sources")
    elif dimension == "coherencia":
        # Structured content with sections and lists
        base += min(20, sec_count * 3)
        base += min(10, list_count * 1.5)
        base += min(10, tables * 3)
        if sec_count >= 4:
            evidence.append("4+ well-defined sections")
    elif dimension == "completitud":
        # Coverage of key sections
        has_context = bool(re.search(r'^##\s*Contexto', text, re.MULTILINE | re.IGNORECASE))
        has_decision = bool(re.search(r'^##\s*(?:Decisi[oó]n|Decision)', text, re.MULTILINE | re.IGNORECASE))
        has_options = bool(re.search(r'^##\s*(?:Opciones|Options|Alternativas)', text, re.MULTILINE | re.IGNORECASE))
        has_consequences = bool(re.search(r'^##\s*(?:Consecuencias|Consequences)', text, re.MULTILINE | re.IGNORECASE))
        has_diagram = bool(re.search(r'^##\s*Diagram', text, re.MULTILINE | re.IGNORECASE))

        covered = sum([has_context, has_decision, has_options, has_consequences, has_diagram])
        base += min(30, covered * 6)
        if covered >= 4:
            evidence.append("4+ standard ADR sections present")
        # Minimum content threshold
        if wc < 100:
            base -= 20
            evidence.append("too short (<100 words)")
        elif wc > 500:
            base += 5
            evidence.append("substantial content")
    elif dimension == "reproducibilidad":
        # Methodology, code blocks, detailed steps
        base += min(20, code_blocks * 5)
        base += min(15, list_count * 2)
        base += min(10, tables * 3)
        base += min(15, urls * 3)
        if code_blocks >= 2:
            evidence.append("2+ code/config blocks")
    elif dimension == "utilidad":
        # Actionable recommendations
        base += min(20, pos_hits * 3)
        base += min(15, list_count * 2)
        base += min(15, tables * 3)
        if sec_count >= 3:
            evidence.append("3+ actionable sections")

    # Clamp
    score = max(0.0, min(100.0, base))

    # Round and produce evidence summary
    if not evidence:
        evidence = ["no strong signals detected"]

    return (round(score, 1), evidence[:5])


def evaluate_dimension(text: str, dimension: str, profile: str = "desarrollo") -> Dict[str, Any]:
    """Evaluate a single dimension of the given text.

    Args:
        text: The output text to evaluate.
        dimension: One of ``veracidad``, ``coherencia``, ``completitud``,
                   ``reproducibilidad``, ``utilidad``.
        profile: Evaluation profile name (default ``desarrollo``).

    Returns:
        Dict with keys: dimension, score, justification, evidence,
        threshold, passed.
    """
    dimension = dimension.lower().strip()
    if dimension not in DIMENSION_WEIGHTS[profile]:
        raise ValueError(f"Unknown dimension '{dimension}'. Valid: {list(DIMENSION_WEIGHTS[profile].keys())}")

    score, evidence = _score_dimension_heuristic(text, dimension)
    thresholds = PROFILE_THRESHOLDS.get(profile, PROFILE_THRESHOLDS["desarrollo"])
    threshold_key = f"{dimension}_min"
    threshold = thresholds.get(threshold_key, 50.0)
    passed = score >= threshold

    return {
        "dimension": dimension,
        "score": score,
        "justification": f"{'Pasa' if passed else 'No pasa'} threshold {threshold} (score={score})",
        "evidence": evidence,
        "threshold": threshold,
        "passed": passed,
    }


def evaluate_all_dimensions(text: str, profile: str = "desarrollo") -> Dict[str, Any]:
    """Evaluate all 5 dimensions and compute a weighted composite score.

    Args:
        text: The output text to evaluate.
        profile: Evaluation profile name (default ``desarrollo``).

    Returns:
        Dict with keys: scores (per-dimension), weighted_score, profile,
        passed, thresholds, evidences, timestamp.
    """
    if profile not in DIMENSION_WEIGHTS:
        logger.warning("Unknown profile '%s', falling back to 'desarrollo'", profile)
        profile = "desarrollo"

    weights = DIMENSION_WEIGHTS[profile]
    thresholds = PROFILE_THRESHOLDS.get(profile, PROFILE_THRESHOLDS["desarrollo"])

    scores: Dict[str, float] = {}
    evidences: Dict[str, List[str]] = {}
    all_passed = True

    for dim in ["veracidad", "coherencia", "completitud", "reproducibilidad", "utilidad"]:
        result = evaluate_dimension(text, dim, profile)
        scores[dim] = result["score"]
        evidences[dim] = result["evidence"]
        if not result["passed"]:
            all_passed = False

    # Weighted composite
    weighted_score = sum(scores[dim] * weights[dim] for dim in scores)

    # Determine pass/fail based on composite
    composite_good = thresholds.get("composite_good", 70.0)
    composite_critical = thresholds.get("composite_critical", 40.0)

    if weighted_score >= composite_good:
        passed = True
    elif weighted_score < composite_critical:
        passed = False
    else:
        passed = all_passed  # borderline: all dimensions must pass

    return {
        "scores": scores,
        "weighted_score": round(weighted_score, 1),
        "profile": profile,
        "passed": passed,
        "thresholds": {
            "composite_good": composite_good,
            "composite_critical": composite_critical,
            "per_dimension": {dim: thresholds.get(f"{dim}_min", 50.0) for dim in scores},
        },
        "evidences": evidences,
        "timestamp": datetime.now().isoformat(),
    }


def check_adherence(adr_text: str, existing_adrs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Verify consistency of an ADR against existing ADRs in L0 memory.

    Checks for:
    - Contradicting decisions with existing ADRs
    - Missing references to related ADRs
    - Consistency of terminology

    Args:
        adr_text: The new ADR text to check.
        existing_adrs: List of existing ADR dicts (must have 'title' and
                       'content' keys).

    Returns:
        Dict with keys: adherence_score, contradictions, warnings,
        valid_references, missing_references.
    """
    text_lower = adr_text.lower()
    contradictions: List[str] = []
    warnings: List[str] = []
    valid_refs: List[str] = []
    missing_refs: List[str] = []

    # Extract ADR references from text
    adr_refs = re.findall(r'(ADR-\d+)', adr_text)

    # Check referenced ADRs exist
    existing_titles = {e.get("title", ""): e for e in existing_adrs}
    existing_ids = {e.get("id", ""): e for e in existing_adrs}

    for ref in adr_refs:
        found = False
        for title, adr in existing_titles.items():
            if ref in title:
                valid_refs.append(ref)
                found = True
                break
        if not found and ref in existing_ids:
            valid_refs.append(ref)
            found = True
        if not found:
            missing_refs.append(ref)
            warnings.append(f"Reference to {ref} not found in L0")

    # Check for common contradictions
    contradiction_keywords = [
        (r'microservicio', r'monolito'),
        (r'sql', r'nosql'),
        (r'rest', r'graphql'),
    ]

    for kw1, kw2 in contradiction_keywords:
        if kw1 in text_lower and kw2 in text_lower:
            # Both present — might be a comparison (OK) or contradiction (not OK)
            # Check if they're in different sections suggesting conflict
            if re.search(r'(?:contradice|inconsistente|conflicto)', text_lower):
                contradictions.append(f"Potential conflict between {kw1} and {kw2}")

    # Check for consistency with existing ADR decisions
    for adr in existing_adrs:
        adr_title = adr.get("title", "")
        adr_content = adr.get("content", "").lower()
        # Look for decision statements in existing ADR
        decision_match = re.search(r'##\s*Decisi[oó]n\s*\n(.*?)(?:\n##|\Z)', adr_content, re.DOTALL)
        if decision_match:
            decision = decision_match.group(1).strip().lower()
            # If new ADR seems to contradict an established decision, flag it
            if "no" in decision and any(kw in text_lower for kw in ["migrar", "cambiar", "reemplazar"]):
                if "migración" not in adr_title.lower():
                    contradictions.append(
                        f"New ADR may contradict decision in '{adr_title[:50]}'"
                    )
                    break

    # Score
    total_refs = len(valid_refs) + len(missing_refs)
    adherence_score = 100.0
    if total_refs > 0:
        adherence_score = (len(valid_refs) / total_refs) * 100.0
    if contradictions:
        adherence_score -= len(contradictions) * 15.0
    if warnings:
        adherence_score -= len(warnings) * 10.0
    adherence_score = max(0.0, min(100.0, adherence_score))

    return {
        "adherence_score": round(adherence_score, 1),
        "contradictions": contradictions,
        "warnings": warnings,
        "valid_references": valid_refs,
        "missing_references": missing_refs,
    }


@dataclass
class EvaluationResult:
    """Result of a full dimensional evaluation.

    Attributes:
        scores: Per-dimension scores (0-100).
        weighted_score: Composite weighted score.
        thresholds: Thresholds from the active profile.
        passed: Whether the evaluation passes the composite threshold.
        evidences: Evidence strings per dimension.
        timestamp: ISO timestamp of evaluation.
        profile_used: Profile name used.
    """
    scores: Dict[str, float] = field(default_factory=dict)
    weighted_score: float = 0.0
    thresholds: Dict[str, Any] = field(default_factory=dict)
    passed: bool = False
    evidences: Dict[str, List[str]] = field(default_factory=dict)
    timestamp: str = ""
    profile_used: str = "desarrollo"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dict for serialization."""
        return asdict(self)

    def summary(self) -> str:
        """Return a human-readable summary string."""
        dims = " | ".join(f"{k}={v:.1f}" for k, v in self.scores.items())
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return (
            f"[{status}] {self.profile_used}: "
            f"composite={self.weighted_score:.1f} {dims}"
        )


class DimensionalEvaluator:
    """Evaluador dimensional de outputs arquitectónicos.

    Evalúa texto en 5 dimensiones usando heurística basada en reglas.
    No requiere DeepEval ni LLM externo.
    """

    def __init__(self, profile: str = "desarrollo", use_yaml: bool = True) -> None:
        """Initialize evaluator with a profile.

        Args:
            profile: Profile name. One of: exploracion, desarrollo,
                     produccion, auditoria, qa.
            use_yaml: If True, try to load weights/thresholds from
                      eval-profile.yaml before falling back to hardcoded values.
        """
        self._profile = profile if profile in DIMENSION_WEIGHTS else "desarrollo"
        self._weights = DIMENSION_WEIGHTS
        self._thresholds = PROFILE_THRESHOLDS.get(self._profile, PROFILE_THRESHOLDS["desarrollo"])
        self._all_weights: Dict[str, Dict[str, float]] = DIMENSION_WEIGHTS
        self._all_thresholds: Dict[str, Dict[str, float]] = PROFILE_THRESHOLDS

        if use_yaml:
            try:
                yaml_weights, yaml_thresholds = _load_profiles_from_yaml()
                if yaml_weights and self._profile in yaml_weights:
                    self._all_weights = yaml_weights
                    self._all_thresholds = yaml_thresholds
                    self._weights = yaml_weights
                    self._thresholds = yaml_thresholds.get(self._profile, yaml_thresholds.get("desarrollo", self._thresholds))
                    logger.info("Loaded profiles from eval-profile.yaml (profile=%s)", self._profile)
            except Exception as exc:
                logger.warning("Failed to load profiles from YAML, using hardcoded: %s", exc)

        logger.debug("DimensionalEvaluator initialized with profile='%s'", self._profile)

    def load_profile(self, profile: str) -> None:
        """Switch to a different evaluation profile.

        Args:
            profile: One of: exploracion, desarrollo, produccion,
                     auditoria, qa.
        """
        if profile not in self._all_weights:
            logger.warning("Unknown profile '%s', keeping '%s'", profile, self._profile)
            return
        self._profile = profile
        self._weights = self._all_weights
        self._thresholds = self._all_thresholds.get(profile, self._all_thresholds.get("desarrollo", PROFILE_THRESHOLDS["desarrollo"]))
        logger.info("Switched to profile '%s'", profile)

    @property
    def profile(self) -> str:
        """Current profile name."""
        return self._profile

    def evaluate(self, text: str) -> EvaluationResult:
        """Run full evaluation on the given text.

        Uses weights and thresholds loaded from YAML (if available)
        instead of module-level constants.

        Args:
            text: The text to evaluate.

        Returns:
            EvaluationResult dataclass with all scores.
        """
        profile = self._profile
        weights = self._weights.get(profile, self._weights.get("desarrollo", DIMENSION_WEIGHTS["desarrollo"]))
        thresholds = self._thresholds if isinstance(self._thresholds, dict) else PROFILE_THRESHOLDS.get(profile, PROFILE_THRESHOLDS["desarrollo"])

        scores: Dict[str, float] = {}
        evidences: Dict[str, List[str]] = {}
        all_passed = True

        for dim in ["veracidad", "coherencia", "completitud", "reproducibilidad", "utilidad"]:
            dim_result = evaluate_dimension(text, dim, profile)
            scores[dim] = dim_result["score"]
            evidences[dim] = dim_result["evidence"]
            if not dim_result["passed"]:
                all_passed = False

        # Weighted composite using instance-level weights
        weighted_score = sum(scores[dim] * weights.get(dim, 0.20) for dim in scores)

        composite_good = thresholds.get("composite_good", 70.0)
        composite_critical = thresholds.get("composite_critical", 40.0)

        if weighted_score >= composite_good:
            passed = True
        elif weighted_score < composite_critical:
            passed = False
        else:
            passed = all_passed

        return EvaluationResult(
            scores=scores,
            weighted_score=round(weighted_score, 1),
            thresholds={
                "composite_good": composite_good,
                "composite_critical": composite_critical,
                "per_dimension": {dim: thresholds.get(f"{dim}_min", 50.0) for dim in scores},
            },
            passed=passed,
            evidences=evidences,
            timestamp=datetime.now().isoformat(),
            profile_used=profile,
        )

    def compare_with_v1(self, text: str) -> Dict[str, Any]:
        """Compare evaluation scores between V2 (current) and legacy V1 style.

        Legacy V1 (``kosmos_evaluator.py``) used simple pattern-matching with
        min_lines + required_patterns. This method approximates the V1 score
        for comparison and migration tracking.

        Args:
            text: The text to evaluate.

        Returns:
            Dict with keys: v2_scores, v2_composite, v1_approximation, delta.
        """
        v2_result = evaluate_all_dimensions(text, self._profile)
        v2_composite = v2_result["weighted_score"]

        # Approximate V1 score: line count + keyword presence
        lines = text.strip().split("\n") if text else []
        line_count = len(lines)
        text_lower = text.lower()
        required = ["adr", "architecture", "arquitectur", "recommendation",
                     "recomend", "diagram", "c4", "decisión", "decision"]
        hits = sum(1 for p in required if p in text_lower)
        completeness = min(1.0, hits / max(1, len(required) / 2))
        length_score = min(1.0, line_count / 15.0)
        v1_composite = round((completeness * 0.6 + length_score * 0.4) * 90.0, 1)

        return {
            "v2_scores": v2_result["scores"],
            "v2_composite": v2_composite,
            "v1_approximation": v1_composite,
            "delta": round(v2_composite - v1_composite, 1),
            "profile_used": self._profile,
        }


# ── Quick test ──
# ── Backward compatibility with kosmos_evaluator v1 ──

def evaluate_system(state: dict = None) -> dict:
    """Compatibility wrapper for kosmos_evaluator.evaluate_system().
    
    Proporciona la misma interfaz que la función evaluate_system del
    kosmos_evaluator v1 para mantener compatibilidad con orchestrator.py.
    """
    from lib.system_scanner import scan, health_score
    from lib.kosmos_evaluator_v2 import DimensionalEvaluator
    
    system = scan()
    sys_score = health_score(system)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "system_health": round(sys_score, 1),
        "system_components": {k: "ok" if "error" not in str(v) else "error" for k, v in system.items()},
        "pipeline_evaluation": {},
        "pipeline_score": 0.0,
        "composite": round(sys_score * 0.7, 1),  # simplified composite
    }
    return result


def run_evaluator(state: dict = None) -> dict:
    """Compatibility wrapper for kosmos_evaluator.run_evaluator()."""
    result = evaluate_system(state=state)
    if state is None:
        return result
    state["evaluation"] = result
    state["evaluation_score"] = result["composite"]
    return state


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sample_text = """# ADR-019: Prueba de Evaluación

## Contexto
El sistema actual tiene 3 problemas fundamentales:
1. No hay memoria persistente entre invocaciones de agentes
2. Los ADRs no tienen referencias cruzadas verificables
3. La evaluación de calidad es superficial y no dimensional

## Opciones Consideradas
1. **Sistema FTS5**: Rápido, sin dependencias externas
2. **Vector Store**: Más potente pero requiere infraestructura
3. **Knowledge Graph**: Máxima expresividad pero mayor complejidad

## Decisión
Implementar un sistema híbrido: FTS5 para L0 (búsqueda textual inmediata)
con planes de migrar a embeddings vectoriales en Fase 2. Esta decisión
se basa en la necesidad de tener memoria funcional desde el día 1.

## Consecuencias
- Positivas: Memoria disponible inmediatamente, sin nuevas dependencias
- Negativas: Búsqueda semántica limitada hasta Fase 2

## Diagrama de Arquitectura
```mermaid
graph TD
    A[KosmosV2] --> B[L0 FTS5]
    A --> C[L1 Embeddings - Fase 2]
```

## Referencias
- [[ADR-001-sistema-memoria]]
- Fuente: https://sqlite.org/fts5.html

## Métricas
- Precisión de búsqueda: ~85% en tests iniciales
- Tiempo de indexación: <100ms por ADR
"""

    evaluator = DimensionalEvaluator(profile="desarrollo")
    result = evaluator.evaluate(sample_text)
    print(result.summary())
    print("\nDetailed scores:")
    for dim, score in result.scores.items():
        print(f"  {dim}: {score:.1f} (evidences: {result.evidences.get(dim, [])})")
    print(f"\nWeighted composite: {result.weighted_score:.1f}")
    print(f"Passed: {result.passed}")

    # Test compare_with_v1
    v1_comp = evaluator.compare_with_v1(sample_text)
    print(f"\nV2 vs V1 delta: {v1_comp['delta']:.1f}")

    print("\nDimensionalEvaluator: OK")
