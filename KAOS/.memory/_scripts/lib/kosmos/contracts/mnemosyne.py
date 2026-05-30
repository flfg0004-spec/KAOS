"""mnemosyne.py — KosmosMnemosyneContract: Curation Quality.

Extraído de kosmos_contracts.py (D3).
"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import (
    _WIKI_ENTITIES_DIR,
    CurationFeedback,
)

logger = logging.getLogger(__name__)


class KosmosMnemosyneContract:
    """Contrato Kosmos → Mnemosyne para curación de ADRs.

    Kosmos envía ADRs a Mnemosyne para curación (wikilinks, tags, metadatos)
    y verifica la calidad de la curación recibida.
    """

    def __init__(self) -> None:
        """Initialize the Kosmos-Mnemosyne contract."""
        self._status: dict[str, Any] = {
            "active": True,
            "last_run": "",
            "last_score": 0.0,
            "total_runs": 0,
            "errors": 0,
        }
        self._entities_dir = _WIKI_ENTITIES_DIR
        self._entities_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("KosmosMnemosyneContract initialized")

    # ── Public API ──

    def request_curation(self, adr_path: str) -> str:
        """Request Mnemosyne curation by writing an entity file.

        Escribe una entidad en `.memory/wiki/entities/` para que Mnemosyne
        la procese en su próximo ciclo de curación.

        Args:
            adr_path: Path to the ADR markdown file to curate.

        Returns:
            Status string describing the action taken.
        """
        try:
            path = Path(adr_path)
            if not path.exists():
                logger.warning("ADR file not found for curation: %s", adr_path)
                return f"ERROR: File not found: {adr_path}"

            adr_text = path.read_text(encoding="utf-8", errors="replace")

            # Extract metadata for the entity file
            title_match = re.search(r'^#\s+(.+)$', adr_text, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else path.stem

            id_match = re.search(r'(ADR-\d+)', adr_text)
            adr_id = id_match.group(1) if id_match else path.stem

            tags = []
            tag_match = re.search(r'tags:\s*\[([^\]]+)\]', adr_text)
            if tag_match:
                tags = [t.strip().strip('"').strip("'") for t in tag_match.group(1).split(",")]

            # Extract wikilinks already present
            existing_links = re.findall(r'\[\[([^\]]+)\]\]', adr_text)

            # Create entity file
            entity = {
                "id": adr_id,
                "title": title,
                "source_path": str(path),
                "type": "adr",
                "tags": tags,
                "existing_wikilinks": existing_links,
                "needs_curation": True,
                "requested_at": datetime.now().isoformat(),
                "priority": "medium",
            }

            entity_path = self._entities_dir / f"{adr_id}-curation.json"
            entity_path.write_text(
                json.dumps(entity, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            self._status["last_run"] = datetime.now().isoformat()
            self._status["total_runs"] += 1
            logger.info("Curation requested for %s at %s", adr_id, entity_path)
            return f"Curation entity written: {entity_path}"

        except Exception as exc:
            logger.error("request_curation failed: %s", exc)
            self._status["errors"] += 1
            return f"ERROR requesting curation: {exc}"

    def parse_curation_response(self, response_text: str) -> CurationFeedback:
        """Parse Mnemosyne's curation response and extract quality score.

        Args:
            response_text: Text response from Mnemosyne containing curation results.

        Returns:
            CurationFeedback with score, wikilinks, tags, and issues.
        """
        try:
            text = response_text or ""

            # Extract score
            score_match = re.search(r'(?:curation_score|quality_score|score)\s*[:=]\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
            curation_score = float(score_match.group(1)) if score_match else 50.0

            # Clamp score
            curation_score = max(0.0, min(100.0, curation_score))

            # Count wikilinks added ([[...]] in response that are new)
            wikilinks = re.findall(r'\[\[([^\]]+)\]\]', text)
            wikilinks_added = len(wikilinks)

            # Extract tags
            tags = re.findall(r'(?:tag|tags?)\s*:?\s*\[([^\]]+)\]', text, re.IGNORECASE)
            tags_added: list[str] = []
            for t in tags:
                tags_added.extend([x.strip().strip('"').strip("'") for x in t.split(",") if x.strip()])

            # Extract issues
            issues = re.findall(r'(?:issue|problema|warning|error)\s*:?\s*([^.\n]+)', text, re.IGNORECASE)
            issues_found = [i.strip() for i in issues if len(i.strip()) > 5]

            passed = curation_score >= 70.0

            feedback = CurationFeedback(
                adr_id=self._extract_adr_id(text),
                curation_score=round(curation_score, 1),
                wikilinks_added=wikilinks_added,
                tags_added=tags_added,
                issues_found=issues_found,
                passed=passed,
                timestamp=datetime.now().isoformat(),
            )

            self._status["last_run"] = datetime.now().isoformat()
            self._status["last_score"] = feedback.curation_score
            self._status["total_runs"] += 1
            logger.info("Curation score=%.1f, passed=%s", curation_score, passed)
            return feedback

        except Exception as exc:
            logger.error("parse_curation_response failed: %s", exc)
            self._status["errors"] += 1
            return CurationFeedback(
                curation_score=0.0,
                issues_found=[f"Parse error: {exc}"],
                timestamp=datetime.now().isoformat(),
            )

    def check_curation_quality(self, adr_path: str, min_score: float = 70.0) -> dict[str, Any]:
        """Check if an ADR's curation meets quality threshold.

        Args:
            adr_path: Path to the ADR file.
            min_score: Minimum curation score to pass (default 70.0).

        Returns:
            Dict con keys: passed (bool), score (float), issues (list),
            improvement_plan (list).
        """
        try:
            path = Path(adr_path)
            if not path.exists():
                return {"passed": False, "score": 0.0, "issues": ["ADR file not found"], "improvement_plan": []}

            adr_text = path.read_text(encoding="utf-8", errors="replace")

            issues: list[str] = []
            improvement_plan: list[str] = []

            # Heuristic curation quality check
            # 1. Check if it has YAML frontmatter
            has_frontmatter = bool(re.match(r'^---\s*$', adr_text, re.MULTILINE))
            if not has_frontmatter:
                issues.append("Sin frontmatter YAML — agregar id, title, status, date, tags")

            # 2. Check for wikilinks
            wikilinks = re.findall(r'\[\[([^\]]+)\]\]', adr_text)
            if len(wikilinks) < 2:
                issues.append("Pocos wikilinks (<2) — añadir referencias cruzadas a conceptos relacionados")
                improvement_plan.append("Agregar wikilinks [[Concepto]] a términos clave del ADR")

            # 3. Check for tags
            has_tags = bool(re.search(r'tags:\s*\[', adr_text))
            if not has_tags:
                issues.append("Sin tags en frontmatter — añadir etiquetas para facilitar búsqueda")
                improvement_plan.append("Agregar tags descriptivos al frontmatter YAML")

            # 4. Check for status
            has_status = bool(re.search(r'status:\s*\w+', adr_text))
            if not has_status:
                issues.append("Sin status en frontmatter — indicar estado (proposed/accepted/deprecated)")

            # 5. Check for date
            has_date = bool(re.search(r'date:\s*\d{4}-\d{2}-\d{2}', adr_text))
            if not has_date:
                issues.append("Sin fecha en frontmatter")

            # Compute score
            score = 100.0
            score -= (5 - (1 if has_frontmatter else 0)) * 10
            score -= max(0, 2 - len(wikilinks)) * 10
            score -= (5 if not has_tags else 0)
            score -= (5 if not has_status else 0)
            score -= (5 if not has_date else 0)
            score = max(0.0, min(100.0, score))

            passed = score >= min_score

            if not improvement_plan:
                improvement_plan.append("ADR curado correctamente — mantener prácticas actuales")

            result = {
                "passed": passed,
                "score": round(score, 1),
                "min_score": min_score,
                "issues": issues,
                "improvement_plan": improvement_plan if not passed else ["Curación aceptable — no requiere cambios"],
                "adr_path": adr_path,
            }

            self._status["last_run"] = datetime.now().isoformat()
            self._status["last_score"] = score
            logger.info("Curation quality: score=%.1f, passed=%s, issues=%d", score, passed, len(issues))
            return result

        except Exception as exc:
            logger.error("check_curation_quality failed: %s", exc)
            self._status["errors"] += 1
            return {"passed": False, "score": 0.0, "issues": [f"Error: {exc}"], "improvement_plan": []}

    def status(self) -> dict[str, Any]:
        """Return contract status."""
        return dict(self._status)

    # ── Internal helpers ──

    @staticmethod
    def _extract_adr_id(text: str) -> str:
        match = re.search(r'(ADR-\d+)', text or "")
        return match.group(1) if match else ""
