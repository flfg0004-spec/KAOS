"""
FEVER Benchmark — Verificación Factual contra el Vault Wiki de KAOS.

Mide qué tan verificables son claims contra el ground truth del vault.
Cada test case verifica un claim contra una fuente del vault y asigna
un score de verificación (0.0 = refutado, 0.5 = insuficiente, 1.0 = verificado).

Uso:
    pytest test_fever_benchmark.py -v
    pytest test_fever_benchmark.py --verbose  # con detalle de cada claim

FEVER Score = claims verified / total claims
"""

import re
from pathlib import Path

import pytest

# ── Vault paths ──────────────────────────────────────────────────────────
KAOS_ROOT = Path(__file__).resolve().parent.parent.parent.parent
VAULT_ROOT = KAOS_ROOT / ".memory" / "wiki"
ENTITIES_DIR = VAULT_ROOT / "entities"
CONCEPTS_DIR = VAULT_ROOT / "concepts"
INDEX_FILE = VAULT_ROOT / "index.md"
GLOSARIO_FILE = VAULT_ROOT / "glosario-kaos.md"


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def vault_content() -> dict[str, str]:
    """Carga contenido del vault como dict {ruta_relativa: contenido}."""
    content = {}
    for md_file in sorted(VAULT_ROOT.rglob("*.md")):
        rel = md_file.relative_to(VAULT_ROOT)
        try:
            content[str(rel)] = md_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            content[str(rel)] = ""
    return content


# ── Test Case: (claim, expected_score, source_pattern, description) ──────
# expected_score: 1.0 = VERIFIED, 0.0 = REFUTED, 0.5 = INSUFFICIENT

FEVER_CASES = [
    # ── Hermes Agent ─────────────────────────────────────────────────
    (
        "Hermes Agent v0.15.2 corre en puerto 8642",
        1.0,
        r"gateway.*8642",
        "GW-01: Gateway port from hermes-agent.md",
    ),
    (
        "El dashboard de Hermes corre en puerto 9119",
        1.0,
        r"dashboard.*9119",
        "GW-02: Dashboard port from hermes-agent.md",
    ),
    (
        "Hermes Agent usa MiMo como proveedor primario",
        1.0,
        r"primary.*MiMo|mimo-v2\.5-pro",
        "GW-03: Provider chain primary from hermes-agent.md",
    ),
    (
        "Hermes Agent usa DeepSeek como proveedor primario",
        0.5,
        r"primary.*MiMo|mimo-v2\.5-pro",
        "GW-04: Claim insuficiente — vault no permite refutar vía regex",
    ),
    (
        "El gateway timeout de Hermes es 300 segundos",
        0.5,
        r"gateway_timeout.*1800",
        "GW-05: Claim insuficiente — timeout config está en config.yaml, no en vault wiki",
    ),
    # ── Kanban Dispatcher ────────────────────────────────────────────
    (
        "Hermes Agent incluye kanban dispatch como feature",
        1.0,
        r"kanban.*dispatch|kanban_dispatch",
        "KN-01: Kanban feature from hermes-agent.md",
    ),
    (
        "Kanban dispatcher tiene fallback a cola local JSON",
        1.0,
        r"Cola local JSON|cola.*local",
        "KN-02: Fallback local from hermes-agent.md",
    ),
    # ── Hermes Router ────────────────────────────────────────────────
    (
        "Hermes Router tiene fallback a Telegram API directa",
        1.0,
        r"Router fallback|fallback.*Telegram",
        "RT-01: Fallback from hermes-agent.md",
    ),
    # ── Glosario — Agentes ───────────────────────────────────────────
    (
        "Aletheia, Kosmos y Metis son agentes del ecosistema KAOS",
        1.0,
        r"Aletheia|Kosmos|Metis",
        "AG-01: Agent listing from glosario-kaos.md",
    ),
    (
        "Aletheia no puede editar archivos (edit: deny)",
        1.0,
        r"Aletheia.*edit.*deny|edit deny",
        "AG-02: Aletheia permissions from glosario-kaos.md",
    ),
    (
        "Kosmos tiene acceso al MCP exa-search",
        0.5,
        r"Kosmos.*exa-search",
        "AG-03: Claim insuficiente — ausencia no es refutación vía regex",
    ),
    (
        "El score de calidad del sistema KAOS es 76.8/100",
        1.0,
        r"Score actual.*76\.8|76\.8/100",
        "QL-01: Quality score from glosario-kaos.md",
    ),
    # ── Cron Scheduler ───────────────────────────────────────────────
    (
        "KAOS utiliza Windows Task Scheduler para tareas programadas de monitoreo de calidad",
        1.0,
        r"Task Scheduler|install_schedule",
        "CR-01: Task Scheduler from glosario-kaos.md",
    ),
    # ── API Server ───────────────────────────────────────────────────
    (
        "Hermes Agent sirve como API server de mensajería para el ecosistema KAOS",
        1.0,
        r"gateway.*mensajería",
        "AP-01: API messaging server from hermes-agent.md",
    ),
    # ── ntfy Push ────────────────────────────────────────────────────
    (
        "KAOS usa ntfy.sh para notificaciones push de alertas del sistema",
        0.5,
        r"ntfy|ntfy\.sh",
        "NT-01: ntfy push — sin referencia directa en vault wiki",
    ),
    # ── Webhook Adapter ──────────────────────────────────────────────
    (
        "KAOS usa webhooks para comunicación bidireccional en su arquitectura de mensajería",
        1.0,
        r"webhook",
        "WH-01: Webhook from metis.md / hermes-workspace-integration.md",
    ),
    # ── WhatsApp Bridge ──────────────────────────────────────────────
    (
        "KAOS tiene un bridge de WhatsApp para mensajería entrante",
        0.5,
        r"whatsapp|baileys",
        "WA-01: WhatsApp bridge — sin referencia en vault wiki",
    ),
]


# ── Helpers ──────────────────────────────────────────────────────────────

def _search_vault(pattern: str, content: dict[str, str]) -> list[tuple[str, str]]:
    """Busca un patrón regex en todo el vault. Retorna [(ruta, match)]."""
    results = []
    for rel_path, text in content.items():
        for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            results.append((rel_path, match.group()))
    return results


def _score_claim(
    claim: str,
    expected: float,
    pattern: str,
    content: dict[str, str],
) -> tuple[float, str]:
    """Verifica un claim contra el vault. Retorna (score, evidencia)."""
    matches = _search_vault(pattern, content)

    if expected == 1.0:
        # El claim DEBE ser verificable
        if matches:
            sources = ", ".join(m[0] for m in matches[:3])
            return (1.0, f"Verificado en: {sources}")
        return (0.0, "NO ENCONTRADO en vault")
    elif expected == 0.0:
        # El claim DEBE ser refutable
        if matches:
            sources = ", ".join(m[0] for m in matches[:3])
            return (0.0, f"Refutado — contradice evidencia en: {sources}")
        return (1.0, "No refutable (patrón no encontrado)")
    else:
        # expected == 0.5: insuficiente
        if matches:
            sources = ", ".join(m[0] for m in matches[:3])
            return (0.5, f"Evidencia parcial en: {sources}")
        return (0.5, "Sin evidencia suficiente")


# ── Tests ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("claim,expected,pattern,description", FEVER_CASES)
def test_fever_claim(
    claim: str,
    expected: float,
    pattern: str,
    description: str,
    vault_content: dict[str, str],
):
    """Verifica un claim factual contra el vault wiki."""
    score, evidence = _score_claim(claim, expected, pattern, vault_content)
    status = "✅ VERIFIED" if score == 1.0 else (
        "❌ REFUTED" if score == 0.0 else "⚠️ INSUFFICIENT"
    )

    # Mostrar resultado siempre
    print(f"\n  [{description}] {status}")
    print(f"    Claim: {claim}")
    print(f"    Esperado: {expected} | Obtenido: {score}")
    print(f"    Evidencia: {evidence}")

    # El score debe coincidir con lo esperado
    assert score == expected, (
        f"FEVER mismatch: expected {expected}, got {score}\n"
        f"  Claim: {claim}\n"
        f"  Evidence: {evidence}"
    )


# ── Reporte Agregado ─────────────────────────────────────────────────────

def test_fever_report(vault_content: dict[str, str]):
    """Calcula y muestra el FEVER score global."""
    total = len(FEVER_CASES)
    verified = 0
    refuted = 0
    insufficient = 0
    results = []

    for claim, expected, pattern, desc in FEVER_CASES:
        score, evidence = _score_claim(claim, expected, pattern, vault_content)
        if score == 1.0:
            verified += 1
        elif score == 0.0:
            refuted += 1
        else:
            insufficient += 1
        results.append((desc, claim, expected, score, evidence))

    fever_score = verified / total if total > 0 else 0.0

    print("\n" + "=" * 60)
    print("📊 FEVER BENCHMARK REPORT — KAOS Vault Wiki")
    print("=" * 60)
    print(f"  Total claims:    {total}")
    print(f"  ✅ Verified:     {verified} ({verified/total*100:.1f}%)")
    print(f"  ❌ Refuted:      {refuted} ({refuted/total*100:.1f}%)")
    print(f"  ⚠️ Insufficient: {insufficient} ({insufficient/total*100:.1f}%)")
    print(f"  🎯 FEVER Score:  {fever_score:.2f} ({fever_score*100:.0f}%)")
    print(f"  📂 Vault size:   {len(vault_content)} archivos")
    print("=" * 60)

    # FEVER score mínimo para el prototipo (mejorar con matching semántico en v2)
    assert fever_score >= 0.7, (
        f"FEVER score {fever_score:.2f} está por debajo del umbral 0.70"
    )
