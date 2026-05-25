"""Auto-ADR Generator — detecta patrones y genera propuestas de ADR.

Decision Estrategica (Principio 6):
  Sistema que se mejora a si mismo. Auto-ADR propone, humano aprueba
  (timeout 30min auto-aplica). ADRs de alto riesgo (arquitectura, seguridad)
  requieren aprobacion. ADRs de bajo riesgo (formato, docs) son autonomos.

Mecanismo:
  1. Monitor: cada output de agente se evalua contra metricas
  2. Detector: 3 ejecuciones consecutivas con score < 80 gatillan propuesta
  3. Kosmos genera ADR propuesta analizando el contexto
  4. Humano aprueba o timeout 30min auto-aplica
"""

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("auto_adr")

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
ADRS_DIR = VAULT_ROOT / ".memory" / "schema"
LINT_REPORT = ADRS_DIR / "lint-report.md"
HEALTH_REPORT = ADRS_DIR / "health-report.md"
SCHEMA_DIR = ADRS_DIR

SCORE_THRESHOLD = 80
CONSECUTIVE_FAILURES = 3
TIMEOUT_MINUTES = 30


class AdrProposal:
    def __init__(self, title: str, context: str, decision: str, consequences: list,
                 risk_level: str = "minor", source: str = "auto-adr"):
        self.title = title
        self.context = context
        self.decision = decision
        self.consequences = consequences
        self.risk_level = risk_level
        self.source = source
        self.timestamp = datetime.now().isoformat()
        self.status = "proposed"

    def to_markdown(self, adr_number: int) -> str:
        pos = [c for c in self.consequences if c.startswith("+")]
        neg = [c for c in self.consequences if c.startswith("-")]
        return (
            f"# ADR-{adr_number:03d}: {self.title}\n\n"
            f"## Estado\nPropuesto (Auto-ADR)\n\n"
            f"## Contexto\n{self.context}\n\n"
            f"## Decision\n{self.decision}\n\n"
            f"## Consecuencias\n"
            + "\n".join(pos) + "\n" + "\n".join(neg) + "\n\n"
            f"## Source\n{self.source} | {self.timestamp}\n"
            f"## Risk Level\n{self.risk_level}\n"
        )

    def save(self):
        nums = [int(p.stem.split("-")[1]) for p in ADRS_DIR.glob("adr-*.md")
                if p.stem.split("-")[1].isdigit()]
        next_num = max(nums) + 1 if nums else 12
        path = ADRS_DIR / f"adr-{next_num:03d}-{self._slug()}.md"
        path.write_text(self.to_markdown(next_num))
        logger.info(f"Auto-ADR saved: {path.name}")
        return path

    def _slug(self):
        s = self.title.lower().strip()[:40]
        return re.sub(r'[^a-z0-9]+', '-', s).strip('-') or "auto-adr"


class AutoADRDetector:
    def __init__(self):
        self.consecutive_low = {}

    def record_score(self, agent: str, score: float, topic: str) -> AdrProposal | None:
        if agent not in self.consecutive_low:
            self.consecutive_low[agent] = {"count": 0, "scores": [], "topics": []}

        record = self.consecutive_low[agent]
        if score < SCORE_THRESHOLD:
            record["count"] += 1
            record["scores"].append(score)
            record["topics"].append(topic)
        else:
            record["count"] = 0
            record["scores"] = []
            record["topics"] = []

        if record["count"] >= CONSECUTIVE_FAILURES:
            proposal = self._generate_proposal(agent, record)
            self.consecutive_low[agent] = {"count": 0, "scores": [], "topics": []}
            return proposal

        return None

    def _generate_proposal(self, agent: str, record: dict) -> AdrProposal:
        avg_score = sum(record["scores"]) / len(record["scores"])
        last_topic = record["topics"][-1] if record["topics"] else "unknown"

        context = (
            f"El agente {agent} ha obtenido puntajes por debajo de {SCORE_THRESHOLD} "
            f"en {CONSECUTIVE_FAILURES} ejecuciones consecutivas (promedio: {avg_score:.1f}/100). "
            f"Ultimo topic: '{last_topic}'. Se requiere una revision de la configuracion "
            f"del agente para mejorar su calidad de output."
        )
        decision = (
            f"Revisar el prompt del agente {agent}, ajustar su temperatura, "
            f"y considerar agregar ejemplos (few-shot) para mejorar la consistencia."
        )
        consequences = [
            f"+ Mejora la calidad del output del agente {agent}",
            f"+ Establece un baseline de calidad para monitoreo futuro",
            f"- Puede requerir iteraciones adicionales para ajustar parametros",
            f"- El cambio puede afectar otros agentes que dependen de {agent}",
        ]

        risk = "critical" if avg_score < 60 else "minor"
        return AdrProposal(
            title=f"Optimizar calidad del agente {agent}",
            context=context,
            decision=decision,
            consequences=consequences,
            risk_level=risk,
        )

    def scan_vault_health(self) -> AdrProposal | None:
        """Escanea reportes de salud y lint para proponer ADRs."""
        issues = []
        if LINT_REPORT.exists():
            content = LINT_REPORT.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"Total issues:\s*(\d+)", content)
            if m and int(m.group(1)) > 5:
                issues.append(f"lint: {m.group(1)} issues")

        if HEALTH_REPORT.exists():
            content = HEALTH_REPORT.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"Score:\s*([\d.]+)", content)
            if m and float(m.group(1)) < 80:
                issues.append(f"health: {m.group(1)}/100")

        if not issues:
            return None

        return AdrProposal(
            title="Mantenimiento preventivo del vault",
            context="Issues detectados: " + "; ".join(issues),
            decision="Ejecutar tareas de mantenimiento: linting, actualizar wikilinks, revisar orphan pages",
            consequences=["+ Reduce deuda tecnica", "+ Mejora calidad del vault"],
            risk_level="minor",
        )


detector = AutoADRDetector()
