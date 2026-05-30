"""Per-document knowledge scoring with 8 weighted metrics (0-100 each).

Each metric returns a dict with value, max, score, weight, weighted.
Public API: score_document, score_directory, format_report.
"""

import json
import logging
import math
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

from lib.frontmatter_utils import extract_frontmatter
from lib.knowledge_levels import assign_level

logger = logging.getLogger(__name__)

PESOS: dict[str, float] = {
    "completitud": 0.15,
    "confianza": 0.20,
    "conectividad": 0.15,
    "frescura": 0.10,
    "precision_factual": 0.15,
    "legibilidad": 0.10,
    "utilidad": 0.10,
    "coherencia": 0.05,
}

_BASE = Path(__file__).resolve().parent.parent.parent


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _frontmatter_dict(content: str) -> dict:
    return extract_frontmatter(content)


def _has_empty_sections(content: str) -> bool:
    """Detecta secciones vacías: heading seguido de otro heading sin contenido."""
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("##") or line.startswith("###"):
            for j in range(i + 1, len(lines)):
                next_line = lines[j].strip()
                if not next_line:
                    continue
                if next_line.startswith("#"):
                    break
                if len(next_line) > 10:
                    break
            else:
                if j == len(lines) - 1 and len(lines[-1].strip()) < 10:
                    return True
                continue
            if j == i + 1 or all(len(lines[k].strip()) < 5 for k in range(i + 1, j)):
                return True
    return False


def _avg_sentence_length(text: str) -> float:
    sentences = re.split(r"[.!?]+", text)
    sentences = [s for s in sentences if len(s.split()) > 1]
    if not sentences:
        return 0
    total_words = sum(len(s.split()) for s in sentences)
    return total_words / len(sentences)


# ── Individual metrics ──────────────────────────────────────────────


def _metric_completitud(path: Path, content: str) -> dict:
    """Analiza frontmatter y estructura del documento."""
    score = 0
    max_score = 100
    details = []

    fm = _frontmatter_dict(content)
    has_title = "title" in fm and bool(fm["title"])
    has_tags = "tags" in fm and bool(fm["tags"])
    has_created = "created" in fm and bool(fm["created"])

    if has_title and has_tags and has_created:
        score += 40
        details.append("frontmatter completo")
    elif has_title:
        score += 15
        details.append("frontmatter parcial (title)")

    headings = re.findall(r"^#{2,3}\s.+", content, re.MULTILINE)
    if headings:
        score += 20
        details.append(f"{len(headings)} secciones con headings")

    word_count = len(re.findall(r"\w+", content))
    if word_count > 100:
        score += 20
        details.append(f"{word_count} palabras")

    if not _has_empty_sections(content):
        score += 20
        details.append("sin secciones vacias")
    else:
        details.append("tiene secciones vacias")

    return {
        "value": score,
        "max": max_score,
        "score": score,
        "details": "; ".join(details),
    }


def _metric_confianza(path: Path, content: str) -> dict:
    """Confianza basada en matriz de confianza o Ebbinghaus decay."""
    score = 0
    max_score = 100
    details = []

    has_matrix = bool(
        re.search(r"(✅|⚡|❓|❌)", content)
        and ("## Matriz de Confianza" in content or "## Confianza" in content or "confidence" in content.lower())
    )
    has_confidence_section = bool(
        re.search(r"##\s*(Confianza|Confidence|Matriz)", content)
    )
    keywords = re.findall(r"\b(alta|media|baja|confirmed|verified|validado)\b", content.lower())

    if has_matrix:
        score = 100
        details.append("matriz de confianza presente con niveles")
    elif has_confidence_section and keywords:
        score = 75
        details.append(f"seccion de confianza con keywords: {', '.join(set(keywords))}")
    elif has_confidence_section:
        score = 60
        details.append("seccion de confianza sin matriz")
    elif keywords:
        score = 40
        details.append(f"keywords de confianza encontradas: {', '.join(set(keywords))}")
    else:
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            days = max(0, (datetime.now() - mtime).days)
        except Exception:
            days = 365
        decay = max(0.05, 1.0 * math.exp(-2.0 * days / 365))
        score = round(decay * 100)
        details.append(f"Ebbinghaus decay ({days}d): {score}pts")

    return {"value": score, "max": max_score, "score": score, "details": "; ".join(details)}


def _metric_conectividad(path: Path, content: str, vg=None) -> dict:
    """Wikilinks en el documento + PageRank del nodo.

    Args:
        path: Ruta al documento.
        content: Contenido del documento.
        vg: Optional VaultGraph instance (cached). If None, instantiate on demand.
    """
    score = 0
    max_score = 100
    details = []

    wikilinks_found = re.findall(r"\[\[([^\]]+?)\]\]", content)
    link_count = len([w for w in wikilinks_found if ":" not in w.split("|")[0].strip()])
    link_pt = min(30, link_count * 5)
    score += link_pt
    details.append(f"{link_count} wikilinks ({link_pt}pts)")

    if os.environ.get("KAOS_TESTING") != "1":
        try:
            if vg is None:
                from lib.graph_analysis import VaultGraph
                vg = VaultGraph()
            pr_results = vg.page_rank(top_k=100)
            node_name = path.stem
            node_pr = None
            for n in pr_results:
                if n["node"] == node_name:
                    node_pr = n["score"]
                    break
            if node_pr is not None:
                pr_pt = min(70, round(node_pr * 1000))
                score += pr_pt
                details.append(f"PageRank {node_pr:.4f} ({pr_pt}pts)")
            else:
                details.append("documento no encontrado en PageRank")
        except Exception as e:
            logger.debug("VaultGraph no disponible para conectividad: %s", e)
            details.append("PageRank no disponible")
    else:
        details.append("PageRank saltado (KAOS_TESTING)")

    return {"value": min(score, max_score), "max": max_score, "score": min(score, max_score), "details": "; ".join(details)}


def _metric_frescura(path: Path, content: str) -> dict:
    """Fecha de modificación."""
    max_score = 100
    try:
        mtime = path.stat().st_mtime
        days = max(0, (datetime.now() - datetime.fromtimestamp(mtime)).days)
    except Exception:
        days = 999

    if days <= 7:
        score = 100
    elif days <= 30:
        score = 80
    elif days <= 90:
        score = 60
    elif days <= 180:
        score = 40
    elif days <= 365:
        score = 20
    else:
        score = 10

    return {
        "value": days,
        "max": 365,
        "score": score,
        "details": f"modificado hace {days} dias ({score}pts)",
    }


def _metric_precision_factual(path: Path, content: str) -> dict:
    """Citas a fuentes + cross-references."""
    score = 0
    max_score = 100
    details = []

    urls = re.findall(r"https?://[^\s\)\"'<>]+", content)
    url_count = len(set(urls))
    url_pts = min(40, url_count * 15)
    score += url_pts
    if url_count:
        details.append(f"{url_count} URLs ({url_pts}pts)")

    source_links = re.findall(r"\[\[([^\]]*?(?:source|fuente|referencia)[^\]]*?)\]\]", content.lower())
    source_pts = min(30, len(source_links) * 15)
    score += source_pts
    if source_links:
        details.append(f"{len(source_links)} wikilinks a fuentes ({source_pts}pts)")

    if os.environ.get("KAOS_TESTING") != "1":
        try:
            from lib.crossref import verify_bidirectional

            unidir = verify_bidirectional()
            node_name = path.stem
            doc_unidir = [u for u in unidir if u["from"] == node_name or u["to"] == node_name]
            if not doc_unidir:
                score += 30
                details.append("todos los cross-refs son bidireccionales (+30pts)")
            else:
                details.append(f"{len(doc_unidir)} cross-refs unidireccionales")
        except Exception as e:
            logger.debug("crossref no disponible: %s", e)
            details.append("crossref no disponible")
    else:
        details.append("crossref saltado (KAOS_TESTING)")

    if score == 0:
        score = 10
        details.append("sin citas ni referencias (10pts base)")

    return {"value": score, "max": max_score, "score": score, "details": "; ".join(details)}


def _metric_legibilidad(path: Path, content: str) -> dict:
    """Estructura y claridad del texto."""
    score = 0
    max_score = 100
    details = []

    headings = re.findall(r"^#{2,3}\s.+", content, re.MULTILINE)
    paragraphs = [p for p in content.split("\n\n") if len(p.split()) > 5]
    num_headings = len(headings)

    if num_headings > 0:
        ratio = len(paragraphs) / num_headings
        if 2.5 <= ratio <= 5.5:
            score += 50
            details.append(f"ratio parrafos/headings ideal ({ratio:.1f})")
        else:
            score += 20
            details.append(f"ratio parrafos/headings: {ratio:.1f}")
    else:
        score += 10
        details.append("sin headings")

    avg_len = _avg_sentence_length(content)
    if 12 <= avg_len <= 28:
        score += 25
        details.append(f"longitud promedio de oracion ideal ({avg_len:.0f} palabras)")
    elif avg_len > 0:
        score += 10
        details.append(f"longitud promedio: {avg_len:.0f} palabras")
    else:
        details.append("sin oraciones detectadas")

    has_lists = bool(re.search(r"(?:^|\n)[\s]*[-*+]\s", content))
    has_tables = bool(re.search(r"\|.*\|.*\|", content))
    has_code = bool(re.search(r"```", content))
    extras = sum([has_lists, has_tables, has_code])
    score += extras * 8
    if extras:
        items = []
        if has_lists:
            items.append("listas")
        if has_tables:
            items.append("tablas")
        if has_code:
            items.append("code blocks")
        details.append(f"elementos extra: {', '.join(items)}")

    return {"value": score, "max": max_score, "score": min(score, max_score), "details": "; ".join(details)}


def _metric_utilidad(path: Path, content: str) -> dict:
    """Similaridad semántica a contenido del vault via txtai."""
    max_score = 100
    if os.environ.get("KAOS_TESTING") == "1":
        score = 50
        details = "txtai saltado (KAOS_TESTING, 50pts base)"
    else:
        try:
            from lib.vectorstore import query

            preview = content[:2000] if len(content) > 2000 else content
            if not preview.strip():
                return {"value": 0, "max": max_score, "score": 50, "details": "contenido vacio (50pts base)"}

            results = query(preview, top_k=10)
            doc_path = path.relative_to(_BASE).as_posix() if _BASE in path.parents else path.name
            matches = [r for r in results if r.get("path") != doc_path]

            if matches:
                score = min(100, 50 + len(matches) * 5)
                details = f"{len(matches)} documentos similares encontrados ({score}pts)"
            else:
                score = 50
                details = "sin documentos similares directos (50pts base)"
        except Exception as e:
            logger.debug("txtai no disponible para utilidad: %s", e)
            score = 50
            details = "txtai no disponible (50pts base)"

    return {"value": score, "max": max_score, "score": score, "details": details}


def _metric_coherencia(path: Path, content: str) -> dict:
    """Consistencia interna básica."""
    score = 0
    max_score = 100
    issues = []

    todo_wip = re.findall(r"\b(TODO|WIP|FIXME|HACK|XXX)\b", content)
    penalty = min(30, len(todo_wip) * 30)
    if todo_wip:
        issues.append(f"{len(todo_wip)} marcadores TODO/WIP/FIXME (-{penalty}pts)")

    fm = _frontmatter_dict(content)
    created_val = fm.get("created", "")
    if created_val:
        try:
            if hasattr(created_val, "strftime"):
                created_str = created_val.strftime("%Y-%m-%d")
            else:
                created_str = str(created_val)[:10]
            created_dt = datetime.strptime(created_str, "%Y-%m-%d")
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            if created_dt <= mtime:
                score += 20
            else:
                issues.append("created > modified")
        except (ValueError, OSError):
            pass

    paragraphs = [p.strip() for p in content.split("\n\n") if len(p.split()) > 10]
    seen = set()
    dupes = 0
    for p in paragraphs:
        norm = re.sub(r"\s+", " ", p).lower()
        if norm in seen:
            dupes += 1
        seen.add(norm)
    if dupes == 0:
        score += 30
    else:
        issues.append(f"{dupes} parrafos duplicados")

    if os.environ.get("KAOS_TESTING") != "1":
        try:
            from lib.wikilinks import parse as wl_parse

            wl_data = wl_parse()
            page_map = wl_data.get("page_map", {})
            doc_links = re.findall(r"\[\[([^\]]+?)\]\]", content)
            broken = 0
            for link in doc_links:
                target = link.split("|")[0].split("#")[0].strip()
                if target and target not in page_map:
                    broken += 1
            if broken == 0:
                score += 20
            else:
                issues.append(f"{broken} wikilinks rotos")
        except Exception as e:
            logger.debug("wikilinks no disponible para coherencia: %s", e)

    score = max(0, score - penalty)

    return {
        "value": score,
        "max": max_score,
        "score": min(score, max_score),
        "details": "; ".join(issues) if issues else "sin problemas de coherencia",
    }


# ── Metric registry ─────────────────────────────────────────────────

_METRICS: dict[str, callable] = {
    "completitud": _metric_completitud,
    "confianza": _metric_confianza,
    "conectividad": _metric_conectividad,
    "frescura": _metric_frescura,
    "precision_factual": _metric_precision_factual,
    "legibilidad": _metric_legibilidad,
    "utilidad": _metric_utilidad,
    "coherencia": _metric_coherencia,
}


# ── Public API ────────────────────────────────────────────────────────


def score_document(path: str | Path, vg=None) -> dict:
    """Score completo de un documento.

    Args:
        path: Ruta al archivo .md.
        vg: Optional VaultGraph instance (cached). If None, instantiate on demand.

    Returns:
        Dict con score global (0-100), level, metrics, breakdown.
    """
    path = Path(path)
    if not path.exists():
        return {
            "score": 0,
            "level": "RAW",
            "error": f"File not found: {path}",
            "metrics": {},
            "breakdown": {},
            "path": str(path),
        }

    content = _read(path)

    # Evaluate each metric
    metrics = {}
    breakdown = {}
    weighted_total = 0.0
    weight_sum = 0.0

    for name, metric_fn in _METRICS.items():
        try:
            if name == "conectividad":
                result = metric_fn(path, content, vg=vg)
            else:
                result = metric_fn(path, content)
        except Exception as e:
            logger.warning("Metric '%s' failed for %s: %s", name, path, e)
            result = {"value": 0, "max": 100, "score": 0, "details": f"Error: {e}"}

        weight = PESOS.get(name, 0)
        weighted_score = round(result["score"] * weight, 2)
        result["weight"] = weight
        result["weighted"] = weighted_score

        metrics[name] = {
            "value": result["value"],
            "max": result["max"],
            "score": result["score"],
            "weight": weight,
            "weighted": weighted_score,
        }
        breakdown[name] = weighted_score
        weighted_total += weighted_score
        weight_sum += weight

    if weight_sum > 0:
        final_score = round(weighted_total / weight_sum, 2)
    else:
        final_score = 0.0

    final_score = max(0.0, min(100.0, final_score))
    level = assign_level(final_score)

    return {
        "score": final_score,
        "level": level,
        "metrics": metrics,
        "breakdown": breakdown,
        "path": str(path),
    }


def score_directory(directory: str | Path = None, recursive: bool = True) -> list[dict]:
    """Scorear todos los .md en un directorio.

    Args:
        directory: Directorio a escanear (default: .memory/wiki).
        recursive: Si incluir subdirectorios.

    Returns:
        Lista de resultados de score_document ordenados por score ascendente.
    """
    if directory is None:
        directory = _BASE / "wiki"
    directory = Path(directory)

    if not directory.exists():
        logger.warning("Directory not found: %s", directory)
        return []

    # Instantiate VaultGraph once for PageRank cache across all documents
    vg = None
    if os.environ.get("KAOS_TESTING") != "1":
        try:
            from lib.graph_analysis import VaultGraph
            vg = VaultGraph()
        except Exception as e:
            logger.debug("VaultGraph not available for cached PageRank: %s", e)

    pattern = "**/*.md" if recursive else "*.md"
    results = []
    for f in sorted(directory.glob(pattern)):
        try:
            result = score_document(f, vg=vg)
            if "error" not in result or result.get("metrics"):
                results.append(result)
        except Exception as e:
            logger.error("Error scoring %s: %s", f, e)

    results.sort(key=lambda x: x.get("score", 0))

    # Telemetry: log structured summary after batch scoring
    if results:
        tiers = {}
        for r in results:
            t = r.get("level", "UNKNOWN")
            tiers[t] = tiers.get(t, 0) + 1
        avg = sum(r.get("score", 0) for r in results) / len(results)
        logger.info(
            "Knowledge scoring: %d docs, avg=%.1f, tiers=%s",
            len(results), avg, sorted(tiers.items()),
        )
        # Append to timeseries
        try:
            _save_timeseries(results)
        except Exception as e:
            logger.debug("Failed to save timeseries: %s", e)

    return results


def format_report(results: list[dict]) -> str:
    """Generar reporte markdown legible.

    Args:
        results: Lista de resultados de score_document o score_directory.

    Returns:
        String con reporte markdown.
    """
    if not results:
        return "# Knowledge Scoring Report\n\n*No documents scored.*\n"

    lines = [
        "# Knowledge Scoring Report",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"*Documents scored: {len(results)}*",
        "",
        "## Summary",
        "",
    ]

    tiers = {}
    for r in results:
        t = r.get("level", "UNKNOWN")
        tiers[t] = tiers.get(t, 0) + 1

    for tier in ["RAW", "ROUGH", "DRAFT", "REVIEW", "CURATED", "CANONICAL"]:
        count = tiers.get(tier, 0)
        if count:
            lines.append(f"- **{tier}**: {count}")

    lines.append("")
    avg_score = sum(r.get("score", 0) for r in results) / max(len(results), 1)
    lines.append(f"**Average score:** {avg_score:.1f} / 100")
    lines.append("")

    # Documents needing synthesis
    needs_synth = [r for r in results if r.get("score", 100) < 60]
    if needs_synth:
        lines.append(f"## Documents Needing Synthesis ({len(needs_synth)})")
        lines.append("")
        for r in needs_synth:
            lines.append(f"- **{r.get('path', '?')}** — score: {r.get('score', 0):.1f} ({r.get('level', '?')})")
        lines.append("")

    # Detail per document
    lines.append("## Per-Document Breakdown")
    lines.append("")
    for r in results:
        path = r.get("path", "?")
        score = r.get("score", 0)
        level = r.get("level", "?")
        lines.append(f"### {path}")
        lines.append(f"**Score:** {score:.1f} / 100 — **Level:** {level}")
        lines.append("")
        lines.append("| Metric | Score | Weight | Weighted |")
        lines.append("|--------|-------:|-------:|---------:|")
        metrics = r.get("metrics", {})
        for name, data in metrics.items():
            s = data.get("score", 0)
            w = data.get("weight", 0)
            ws = data.get("weighted", 0)
            lines.append(f"| {name} | {s:.1f} | {w:.2f} | {ws:.2f} |")
        lines.append("")

    return "\n".join(lines)


# ── Telemetry & Timeseries ──────────────────────────────────────────


KAOS_ROOT = _BASE.parent
_TIMESERIES_DIR = KAOS_ROOT / ".vault" / "quality" / "timeseries"


def _save_timeseries(results: list[dict]) -> None:
    """Append daily scoring summary to knowledge.jsonl (unified timeseries).

    Follows the same pattern as lib/quality.py which stores in
    `.vault/quality/timeseries/daily.jsonl`.
    """
    if not results:
        return
    ts_path = _TIMESERIES_DIR / "knowledge.jsonl"
    ts_path.parent.mkdir(parents=True, exist_ok=True)

    tiers = {}
    for r in results:
        t = r.get("level", "UNKNOWN")
        tiers[t] = tiers.get(t, 0) + 1
    avg = sum(r.get("score", 0) for r in results) / len(results)

    record = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "avg_score": round(avg, 1),
        "total_docs": len(results),
        "tiers": tiers,
    }
    try:
        with ts_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.debug("Error writing timeseries: %s", e)


def trend(days: int = 7) -> list[dict]:
    """Show evolution of knowledge scores over recent days.

    Args:
        days: Number of days to look back (default 7).

    Returns:
        List of daily summary dicts sorted by date ascending.
    """
    ts_path = _TIMESERIES_DIR / "knowledge.jsonl"
    if not ts_path.exists():
        return []

    cutoff = datetime.now() - timedelta(days=days)
    entries = []
    try:
        with ts_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entry_date = datetime.strptime(entry.get("date", ""), "%Y-%m-%d")
                    if entry_date >= cutoff:
                        entries.append(entry)
                except (json.JSONDecodeError, ValueError):
                    continue
    except Exception as e:
        logger.debug("Error reading timeseries: %s", e)
        return []

    entries.sort(key=lambda x: x.get("date", ""))
    return entries


# ── Dashboard ───────────────────────────────────────────────────────


def generate_dashboard(results: list[dict], output_path: str | Path = None) -> str:
    """Generate a simple HTML dashboard for knowledge tiers.

    Args:
        results: List of score_document results.
        output_path: Optional path to write the HTML file.
            Defaults to _BASE / 'dashboard' / 'knowledge-dashboard.html'.

    Returns:
        HTML string of the dashboard.
    """
    if output_path is None:
        output_path = _BASE / "dashboard" / "knowledge-dashboard.html"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total = len(results)
    avg_score = sum(r.get("score", 0) for r in results) / max(total, 1)

    tiers = {}
    for r in results:
        t = r.get("level", "UNKNOWN")
        tiers[t] = tiers.get(t, 0) + 1

    tier_order = ["RAW", "ROUGH", "DRAFT", "REVIEW", "CURATED", "CANONICAL"]
    tier_rows = ""
    for tier in tier_order:
        count = tiers.get(tier, 0)
        pct = round(count / max(total, 1) * 100, 1) if total else 0
        tier_rows += (
            f"<tr><td>{tier}</td><td>{count}</td><td>{pct}%</td></tr>\n"
        )

    needs_synth = [r for r in results if r.get("score", 100) < 60]
    synth_rows = ""
    for r in needs_synth[:20]:  # limit to 20
        p = r.get("path", "?")
        s = r.get("score", 0)
        lv = r.get("level", "?")
        synth_rows += f"<tr><td>{p}</td><td>{s:.1f}</td><td>{lv}</td></tr>\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Knowledge Dashboard</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; background: #f8f9fa; color: #333; }}
  h1 {{ color: #1a1a2e; border-bottom: 2px solid #e0e0e0; padding-bottom: 0.5rem; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  th, td {{ padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #eee; }}
  th {{ background: #1a1a2e; color: #fff; }}
  tr:hover {{ background: #f1f3f5; }}
  .summary {{ display: flex; gap: 1rem; margin: 1rem 0; }}
  .summary-card {{ background: #fff; padding: 1rem 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); flex: 1; text-align: center; }}
  .summary-card .value {{ font-size: 2rem; font-weight: bold; color: #1a1a2e; }}
  .summary-card .label {{ font-size: 0.85rem; color: #666; margin-top: 0.25rem; }}
  .footer {{ margin-top: 2rem; font-size: 0.8rem; color: #999; text-align: center; }}
</style>
</head>
<body>
<h1>📊 Knowledge Dashboard</h1>
<p><em>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</em></p>

<div class="summary">
  <div class="summary-card">
    <div class="value">{total}</div>
    <div class="label">Total Documents</div>
  </div>
  <div class="summary-card">
    <div class="value">{avg_score:.1f}</div>
    <div class="label">Average Score</div>
  </div>
  <div class="summary-card">
    <div class="value">{len(needs_synth)}</div>
    <div class="label">Need Synthesis</div>
  </div>
</div>

<h2>Tier Distribution</h2>
<table>
<thead><tr><th>Tier</th><th>Count</th><th>%</th></tr></thead>
<tbody>
{tier_rows}
</tbody>
</table>

<h2>Documents Needing Synthesis (score &lt; 60)</h2>
<table>
<thead><tr><th>Path</th><th>Score</th><th>Level</th></tr></thead>
<tbody>
{synth_rows if synth_rows else '<tr><td colspan="3" style="text-align:center;color:#999;">All documents are above synthesis threshold</td></tr>'}
</tbody>
</table>

<div class="footer">KAOS Knowledge Scorer — Dashboard auto-generated</div>
</body>
</html>"""

    try:
        output_path.write_text(html, encoding="utf-8")
        logger.info("Dashboard generated: %s", output_path)
    except Exception as e:
        logger.warning("Failed to write dashboard: %s", e)

    return html
