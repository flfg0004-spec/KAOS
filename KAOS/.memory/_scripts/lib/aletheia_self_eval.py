"""Aletheia Self-Evaluation — measures research output quality across 5 dimensions."""

import logging
import re

_LOG = logging.getLogger(__name__)


def _check_citations(text: str) -> dict:
    patterns = [
        r"\[[\d\s,.\-]+\]",
        r"\([\w\s]+,?\s*\d{4}\)",
        r"(?:see|cf\.|ref\.?)\s+[\w\s]+",
        r"https?://\S+",
        r"DOI:\s*10\.\d{4,}/",
    ]
    found = []
    for p in patterns:
        matches = re.findall(p, text)
        found.extend(matches)
    return {"count": len(found), "references": found}


def _check_claims_without_sources(text: str) -> list[str]:
    claim_patterns = [
        (
            r"(?:the|this|our)\s+(?:study|research|analysis|data|results?)"
            r"\s+(?:shows?|demonstrates?|indicates?|proves?|suggests?|reveals?|confirms?)"
        ),
        (
            r"(?:it\s+is|this\s+is)\s+(?:clear|evident|obvious|proven|"
            r"well-known|established)\s+(?:that\s+)"
        ),
        (
            r"(?:significantly|dramatically|substantially|critically)"
            r"\s+(?:impacts?|affects?|changes?|reduces?|increases?)"
        ),
    ]
    claims = []
    lines = text.lower().split("\n")
    for line in lines:
        for cp in claim_patterns:
            if re.search(cp, line):
                has_citation = any(c in line for c in ["[", "(", "http", "doi", "doi:"])
                if not has_citation:
                    claims.append(line.strip()[:100])
    return claims


def _estimate_coherence(text: str) -> dict:
    sections = re.split(r"\n#{1,3}\s+", text)
    section_count = len([s for s in sections if len(s.strip()) > 50])
    has_intro = bool(re.search(r"(?i)(introducci[óo]n|introduction|background)", text))
    has_conclusion = bool(re.search(r"(?i)(conclusi[óo]n|conclusion|summary|resumen)", text))
    has_structure = bool(re.search(r"(?i)(primero|first|segundo|second|finalmente|finally|\d\.\s)", text))
    return {
        "section_count": section_count,
        "has_intro": has_intro,
        "has_conclusion": has_conclusion,
        "has_structure": has_structure,
    }


def aletheia_self_eval(agent: str, output: dict) -> dict:
    output = output or {}
    content = output.get("content", "")
    sources = output.get("sources", [])
    reasoning = output.get("reasoning", "")
    summary = output.get("summary", "")

    if not content:
        return {
            "agent": agent,
            "score": 0.0,
            "dimensions": {
                "veracidad": {"score": 0.0, "justificacion": "No content provided"},
                "coherencia": {"score": 0.0, "justificacion": "No content provided"},
                "completitud": {"score": 0.0, "justificacion": "No content provided"},
                "citacion": {"score": 0.0, "justificacion": "No content provided"},
                "utilidad": {"score": 0.0, "justificacion": "No content provided"},
            },
        }

    citation_info = _check_citations(content)
    unsourced_claims = _check_claims_without_sources(content)
    coherence = _estimate_coherence(content)

    content_len = len(content)

    veracidad = 1.0
    if unsourced_claims:
        veracidad = max(0.0, 1.0 - 0.15 * len(unsourced_claims))
    if len(sources) == 0 and citation_info["count"] == 0:
        veracidad = min(veracidad, 0.3)

    coherence_score = 0.5
    if coherence["has_intro"]:
        coherence_score += 0.2
    if coherence["has_conclusion"]:
        coherence_score += 0.2
    if coherence["has_structure"]:
        coherence_score += 0.1
    if coherence["section_count"] >= 3:
        coherence_score = min(1.0, coherence_score + 0.1)
    coherencia = max(0.0, min(1.0, coherence_score))

    completitud = 0.5
    if content_len > 500:
        completitud = 0.7
    if content_len > 2000:
        completitud = 0.9
    if content_len > 5000:
        completitud = 1.0
    if summary:
        completitud = min(1.0, completitud + 0.1)
    if reasoning:
        completitud = min(1.0, completitud + 0.1)

    citacion = 0.3
    if citation_info["count"] > 0:
        citacion = min(1.0, 0.3 + 0.1 * min(citation_info["count"], 7))
    if len(sources) > 0:
        citacion = min(1.0, citacion + 0.2)
    citacion = max(0.0, min(1.0, citacion))

    utilidad = 0.6
    if summary:
        utilidad += 0.2
    if coherence["has_conclusion"]:
        utilidad += 0.1
    if content_len > 1000:
        utilidad += 0.1
    utilidad = max(0.0, min(1.0, utilidad))

    score = round((veracidad + coherencia + completitud + citacion + utilidad) / 5, 2)

    return {
        "agent": agent,
        "score": score,
        "dimensions": {
            "veracidad": {
                "score": veracidad,
                "justificacion": (
                    f"{len(unsourced_claims)} unsourced claims, "
                    f"{len(sources)} sources, {citation_info['count']} citations"
                ),
            },
            "coherencia": {
                "score": coherencia,
                "justificacion": (
                    f"{coherence['section_count']} sections, "
                    f"intro={coherence['has_intro']}, "
                    f"conclusion={coherence['has_conclusion']}"
                ),
            },
            "completitud": {
                "score": completitud,
                "justificacion": (
                    f"{content_len} chars, has_summary={bool(summary)}, "
                    f"has_reasoning={bool(reasoning)}"
                ),
            },
            "citacion": {
                "score": citacion,
                "justificacion": (
                    f"{citation_info['count']} citation patterns, "
                    f"{len(sources)} structured sources"
                ),
            },
            "utilidad": {
                "score": utilidad,
                "justificacion": (
                    f"Has summary={bool(summary)}, "
                    f"has conclusion={coherence['has_conclusion']}, "
                    f"length={content_len}"
                ),
            },
        },
    }
