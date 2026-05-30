"""dashboard_populate.py — Puebla dashboard.md con scores BCG y OKR Health.

Lee un archivo de OKRs en markdown, ejecuta la evaluación BCG (estrategia + OKR
health) internamente vía lib.bcg_evaluator, y actualiza los marcadores
correspondientes en dashboard.md.

Uso:
  py -3 .memory/_scripts/dashboard_populate.py
  py -3 .memory/_scripts/dashboard_populate.py --file KAOS/okrs/KAOS-OKRs-Q2-2026.md
  py -3 .memory/_scripts/dashboard_populate.py --dashboard .vault/quality/dashboard.md
  py -3 .memory/_scripts/dashboard_populate.py --file ruta/okrs.md --dashboard ruta/dashboard.md
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
KAOS_ROOT = SCRIPT_DIR.parents[2]  # .memory/_scripts/ → KAOS/
# Fallback: si KAOS_ROOT no contiene /KAOS/, corregir
if not (KAOS_ROOT / ".memory").exists():
    # Probablemente el CWD no es KAOS, buscar hacia arriba
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / ".memory").exists():
            KAOS_ROOT = p
            break

sys.path.insert(0, str(SCRIPT_DIR))
from lib.bcg_evaluator import evaluate_okrs, evaluate_strategy
from lib.file_lock import acquire_lock, release_lock

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_OKRS = KAOS_ROOT / "KAOS" / "okrs" / "KAOS-OKRs-Q2-2026.md"
DEFAULT_DASHBOARD = KAOS_ROOT / ".vault" / "quality" / "dashboard.md"


# ── OKR parser ────────────────────────────────────────────────────────────────
def _parse_okrs_from_markdown(text: str) -> list[dict]:
    """Extract OKR objects from markdown sections like ``## O1: …``.

    Returns a list of dicts with ``objective`` and ``key_results`` keys,
    compatible with ``lib.bcg_evaluator.evaluate_okrs()``.
    """
    okrs = []
    # Split on ``## O{digit}:`` headers (keep delimiter in next chunk)
    chunks = re.split(r"\n(?=## O\d+:)", text)

    for chunk in chunks:
        if not re.match(r"## O\d+:", chunk):
            continue

        # Extract section title (e.g. "O1: Consolidar la base…")
        title_match = re.match(r"## (O\d+:.*?)(?:\n|$)", chunk)
        title = title_match.group(1).strip() if title_match else ""

        # Extract the **Objective:** line
        obj_match = re.search(r"\*\*Objective\*\*:\s*(.*?)(?:\n|$)", chunk)
        objective = obj_match.group(1).strip() if obj_match else title

        # Extract KR rows from the markdown table
        krs = re.findall(r"\|\s*(KR\d+:.*?)\s*\|", chunk)

        okrs.append(
            {
                "objective": f"{title}: {objective}" if title else objective,
                "key_results": [kr.strip() for kr in krs],
            }
        )

    return okrs


# ── Marker helpers ────────────────────────────────────────────────────────────
def _replace_between_markers(
    text: str,
    start_marker: str,
    end_marker: str,
    new_content: str,
) -> str:
    """Replace everything between *start_marker* and *end_marker*.

    Expects the markers on their own lines.  Returns the original *text*
    unchanged if either marker is missing.
    """
    pattern = re.compile(
        rf"({re.escape(start_marker)}\n).*?(\n{re.escape(end_marker)})",
        re.DOTALL,
    )
    if not pattern.search(text):
        return text
    return pattern.sub(rf"\1{new_content}\2", text)


def _build_scores_block(bcg_result: dict, okr_result: dict) -> str:
    """Build the markdown table rows for the METIS_SCORES section."""
    bcg = bcg_result.get("total_score_10", 0)
    bcg_pass = bcg_result.get("passed", False)
    bcg_status = "✅ Pasa" if bcg_pass else "❌ No pasa"

    okr_health = okr_result.get("score_100", 0)
    okr_pass = okr_result.get("passed", False)
    okr_status = "✅ OK" if okr_pass else "❌ Revisión"

    return (
        f"| BCG Strategy Score | {bcg}/10 | ≥ 7.0/10 | {bcg_status} |\n"
        f"| OKR Health | {okr_health}% | ≥ 70% | {okr_status} |\n"
        f"| Quality Report | — | Semanal | ⏳ Pendiente |"
    )


def _build_eval_block(bcg_result: dict, profile: str = "standard") -> str:
    """Build the markdown list for the METIS_EVAL section."""
    today = date.today().isoformat()
    bcg = bcg_result.get("total_score_10", 0)

    return f"- Fecha: {today}\n- Perfil: {profile}\n- Modo: Strategy\n- BCG Score: {bcg}/10\n- Observaciones: —"


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Puebla dashboard.md con scores BCG y OKR Health.",
    )
    parser.add_argument(
        "--file",
        default=None,
        help=f"Ruta al archivo de OKRs (default: {DEFAULT_OKRS})",
    )
    parser.add_argument(
        "--dashboard",
        default=None,
        help=f"Ruta a dashboard.md (default: {DEFAULT_DASHBOARD})",
    )
    args = parser.parse_args()

    # Resolve paths
    okrs_path = Path(args.file).resolve() if args.file else DEFAULT_OKRS
    dashboard_path = Path(args.dashboard).resolve() if args.dashboard else DEFAULT_DASHBOARD

    # ── 1. Read OKRs ──
    if not okrs_path.exists():
        print(f"Error: OKRs file not found: {okrs_path}", file=sys.stderr)
        sys.exit(1)

    okrs_text = okrs_path.read_text(encoding="utf-8")
    print(f"✓ OKRs leídos: {okrs_path}")

    # ── 2. BCG evaluation ──
    bcg_result = evaluate_strategy(okrs_text)
    bcg_score = bcg_result.get("total_score_10", 0)
    bcg_pass = bcg_result.get("passed", False)
    print(f"  BCG Strategy Score: {bcg_score}/10 {'✅' if bcg_pass else '❌'}")

    # ── 3. OKR Health ──
    okrs = _parse_okrs_from_markdown(okrs_text)
    okr_result = evaluate_okrs(okrs) if okrs else {"score_100": 0, "passed": False}
    okr_health = okr_result.get("score_100", 0)
    okr_pass = okr_result.get("passed", False)
    print(f"  OKR Health: {okr_health}% {'✅' if okr_pass else '❌'}")
    print(f"  OKRs parseados: {len(okrs)}")

    # ── 4. Read dashboard (con file_lock) ──
    if not acquire_lock("quality_dashboard", timeout=10):
        print("Error: Could not acquire lock for quality_dashboard", file=sys.stderr)
        sys.exit(1)

    try:
        if not dashboard_path.exists():
            print(f"Error: Dashboard not found: {dashboard_path}", file=sys.stderr)
            sys.exit(1)

        dashboard_text = dashboard_path.read_text(encoding="utf-8")

        # ── 5. Replace scores block ──
        scores_block = _build_scores_block(bcg_result, okr_result)
        updated = _replace_between_markers(
            dashboard_text,
            "<!-- METIS_SCORES_START -->",
            "<!-- METIS_SCORES_END -->",
            scores_block,
        )
        if updated == dashboard_text:
            print(
                "Warning: <!-- METIS_SCORES_START/END --> markers not found. Scores not updated.",
                file=sys.stderr,
            )

        # ── 6. Replace eval block ──
        eval_block = _build_eval_block(bcg_result)
        updated = _replace_between_markers(
            updated,
            "<!-- METIS_EVAL_START -->",
            "<!-- METIS_EVAL_END -->",
            eval_block,
        )
        if updated == dashboard_text:
            print(
                "Warning: <!-- METIS_EVAL_START/END --> markers not found. Eval info not updated.",
                file=sys.stderr,
            )

        # ── 7. Write back ──
        if updated != dashboard_text:
            dashboard_path.write_text(updated, encoding="utf-8")
            print(f"\n✓ Dashboard actualizado: {dashboard_path}")
        else:
            print("\n⚠ Dashboard sin cambios (no se encontraron marcadores).")

        print(f"  BCG Score: {bcg_score}/10")
        print(f"  OKR Health: {okr_health}%")
        print(f"  Fecha: {date.today().isoformat()}")
    finally:
        release_lock("quality_dashboard")


if __name__ == "__main__":
    main()
