"""Motor de scoring: evalúa una nota contra las 8 métricas.

Uso:
    from lib.scoring import score_note
    result = score_note(".memory/wiki/concepts/adr.md")
    print(result["total_score"], result["metrics"])
"""

from pathlib import Path

from lib.scoring.metrics import ALL_METRICS

# Pesos de cada métrica (suma = 10.0)
WEIGHTS = {
    "has_frontmatter": 2.0,
    "has_tags": 1.5,
    "has_wikilinks": 1.5,
    "min_length": 1.0,
    "audience_defined": 1.0,
    "has_backlinks": 1.0,
    "has_aliases": 1.0,
    "is_linked": 1.0,
}

DESCRIPTIONS = {
    "has_frontmatter": "Frontmatter completo (title, type, tags, created + opcionales)",
    "has_tags": "Densidad de tags (inline + frontmatter) por cada 100 palabras",
    "has_wikilinks": "Densidad de wikilinks por cada 100 palabras",
    "min_length": "Longitud mínima del contenido (≥300 chars = 1.0, <50 = 0.0)",
    "audience_defined": "Campo audience definido en frontmatter",
    "has_backlinks": "Cantidad de backlinks desde otros archivos wiki/",
    "has_aliases": "Lista de aliases definida y no vacía",
    "is_linked": "Página no huérfana — tiene enlaces salientes",
}


def _parse_frontmatter(content: str) -> dict:
    """Extrae frontmatter YAML de contenido markdown."""
    if not content.startswith("---"):
        return {}
    # Encontrar el segundo ---
    end_idx = content.find("---", 3)
    if end_idx == -1:
        return {}
    import yaml
    try:
        fm = yaml.safe_load(content[3:end_idx])
        if isinstance(fm, dict):
            return fm
        return {}
    except yaml.YAMLError:
        return {}


def score_note(path: str | Path) -> dict:
    """Evalúa una nota contra las 8 métricas.

    Args:
        path: Ruta al archivo .md de la nota.

    Returns:
        dict con:
            - path: str — ruta normalizada
            - total_score: float — puntuación total (0-10)
            - metrics: dict[str, float] — score individual por métrica
            - breakdown: dict — detalles por métrica (score, weight, weighted, description)
    """
    path = Path(path)
    content = path.read_text(encoding="utf-8")
    frontmatter = _parse_frontmatter(content)

    total_raw = 0.0
    metrics = {}
    breakdown = {}

    for name, func in ALL_METRICS.items():
        try:
            score = func(path, content, frontmatter)
        except Exception:
            score = 0.0  # fail safe

        weight = WEIGHTS.get(name, 1.0)
        weighted = score * weight
        total_raw += weighted
        metrics[name] = score
        breakdown[name] = {
            "score": score,
            "weight": weight,
            "weighted": weighted,
            "description": DESCRIPTIONS.get(name, ""),
        }

    # total_raw max = 10.0, escalamos a 0-10
    total_score = total_raw

    return {
        "path": str(path),
        "total_score": round(total_score, 2),
        "metrics": metrics,
        "breakdown": breakdown,
    }
