"""Roadmap 3 Horizontes — Generador de roadmaps estratégicos con clasificacion H1/H2/H3 y RICE scoring.

Usage:
    py -3 .tools/roadmap_3h.py --vision "Descripcion" --initiatives initiatives.json
    py -3 .tools/roadmap_3h.py --interactive
    py -3 .tools/roadmap_3h.py --help
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
KAOS_ROOT = TOOLS_DIR.parent

HORIZON_ORDER = ["h1", "h2", "h3"]

HORIZON_RISKS = {
    "h1": [
        "Riesgo de ejecucion: capacidad del equipo para entregar en plazo ajustado",
        "Riesgo de dependencias no identificadas entre iniciativas H1",
        "Riesgo de resource contention si multiples iniciativas H1 compiten por los mismos recursos",
    ],
    "h2": [
        "Riesgo de arrastre: iniciativas H1 retrasadas comprimen el timeline H2",
        "Riesgo de scope creep al expandir capacidades en fase de crecimiento",
        "Riesgo de desalineacion si los OKRs cambian entre H1 y H2",
    ],
    "h3": [
        "Riesgo de mercado: condiciones cambiantes pueden invalidar supuestos H3",
        "Riesgo tecnologico: nuevas tecnologias pueden hacer obsoleta la aproximacion",
        "Riesgo de inversion: apuestas a largo plazo requieren commitment sostenido",
    ],
}


def classify_horizon(initiatives):
    """Clasifica iniciativas en H1 (0-3mo), H2 (3-6mo), H3 (6-12mo)."""
    horizons = {"h1": [], "h2": [], "h3": []}
    assigned = {}

    name_map = {ini["name"]: ini for ini in initiatives}

    # Pass 1: classify by effort_days
    temp = {}
    for ini in initiatives:
        d = ini.get("effort_days", 30)
        if d <= 45:
            temp[ini["name"]] = "h1"
        elif d <= 90:
            temp[ini["name"]] = "h2"
        else:
            temp[ini["name"]] = "h3"

    # Pass 2: adjust for dependencies
    for ini in initiatives:
        h = temp[ini["name"]]
        for dep in ini.get("dependencies", []):
            dep_h = temp.get(dep, "h3")
            if HORIZON_ORDER.index(dep_h) > HORIZON_ORDER.index(h):
                h = dep_h
        assigned[ini["name"]] = h
        horizons[h].append(ini["name"])

    return horizons, assigned


def compute_rice(initiative):
    """RICE = (Reach x Impact x Confidence) / Effort(meses)."""
    reach = initiative.get("rice_reach", 1)
    impact = initiative.get("rice_impact", 1)
    confidence = initiative.get("rice_confidence", 0.5)
    effort_months = initiative.get("effort_days", 30) / 30.0
    if effort_months <= 0:
        effort_months = 0.5
    score = (reach * impact * confidence) / effort_months
    return round(score, 1)


def find_critical_path(initiatives):
    """Encuentra la cadena de dependencias mas larga (critical path)."""
    name_map = {ini["name"]: ini for ini in initiatives}
    graph = {}
    for ini in initiatives:
        graph[ini["name"]] = ini.get("dependencies", [])

    longest_path = []

    def dfs(node, path):
        nonlocal longest_path
        current_path = path + [node]
        deps = graph.get(node, [])
        if deps:
            for dep in deps:
                if dep in name_map:
                    dfs(dep, current_path)
        else:
            if len(current_path) > len(longest_path):
                longest_path = current_path

    for ini in initiatives:
        dfs(ini["name"], [])

    if not longest_path and initiatives:
        longest_path = [initiatives[0]["name"]]

    return longest_path


def horizon_label(h):
    labels = {"h1": "H1 (0-3 meses)", "h2": "H2 (3-6 meses)", "h3": "H3 (6-12 meses)"}
    return labels.get(h, h)


def generate_markdown(initiatives, vision, horizons, assigned, rice_scores, critical_path, dashboard_mode=False):
    """Genera reporte markdown completo del roadmap.

    Si dashboard_mode=True, incluye secciones OKR compatibles con
    dashboard_populate.py (## O{d}: + **Objective**: + tabla KRs).
    """
    name_map = {ini["name"]: ini for ini in initiatives}
    lines = []

    lines.append(f"# Roadmap 3 Horizontes\n")
    lines.append(f"**Vision**: {vision}\n")
    lines.append(f"**Generado**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"**Total iniciativas**: {len(initiatives)}\n")

    # Summary by horizon
    lines.append("## Resumen por Horizonte\n")
    lines.append("| Horizonte | Periodo | Iniciativas | Score RICE promedio |")
    lines.append("|-----------|---------|-------------|--------------------|")
    for h in HORIZON_ORDER:
        inis = horizons[h]
        if inis:
            avg_rice = sum(rice_scores.get(n, 0) for n in inis) / len(inis)
            lines.append(f"| {horizon_label(h)} | 0-3 / 3-6 / 6-12m | {len(inis)} | {avg_rice:.1f} |")
        else:
            lines.append(f"| {horizon_label(h)} | — | 0 | — |")
    lines.append("")

    # Full table sorted by RICE
    lines.append("## Iniciativas Detalladas\n")
    lines.append("| Iniciativa | Horizonte | Esfuerzo(d) | RICE | Dependencias | Categoria |")
    lines.append("|------------|-----------|-------------|------|--------------|-----------|")
    for ini in sorted(initiatives, key=lambda x: rice_scores.get(x["name"], 0), reverse=True):
        n = ini["name"]
        h = assigned.get(n, "h3")
        deps = ", ".join(ini.get("dependencies", [])) or "—"
        cat = ini.get("category", "—")
        lines.append(f"| {n} | {horizon_label(h)} | {ini['effort_days']} | {rice_scores.get(n, 0)} | {deps} | {cat} |")
    lines.append("")

    # RICE detail
    lines.append("## RICE Scores\n")
    lines.append("| Iniciativa | Reach | Impact | Confidence | Effort(mes) | Score |")
    lines.append("|------------|-------|--------|------------|-------------|-------|")
    for ini in sorted(initiatives, key=lambda x: rice_scores.get(x["name"], 0), reverse=True):
        n = ini["name"]
        rice = rice_scores.get(n, 0)
        effort_m = ini.get("effort_days", 30) / 30.0
        lines.append(f"| {n} | {ini.get('rice_reach', 1)} | {ini.get('rice_impact', 1)} | {ini.get('rice_confidence', 0.5)} | {effort_m:.1f} | {rice} |")
    lines.append("")

    # Critical path
    lines.append("## Critical Path\n")
    if critical_path and len(critical_path) > 1:
        lines.append(f"Ruta critica identificada: **{' → '.join(critical_path)}**\n")
        critical_rice = sum(rice_scores.get(n, 0) for n in critical_path)
        lines.append(f"- **Longitud**: {len(critical_path)} iniciativas\n")
        lines.append(f"- **Score RICE acumulado**: {critical_rice:.1f}\n")
        lines.append(f"- **Riesgo**: Si alguna iniciativa en esta ruta se retrasa, todo el roadmap se desplaza\n")
    else:
        lines.append("No se identifico una ruta critica unica (iniciativas independientes o cadena trivial).\n")
    lines.append("")

    # Milestones per horizon
    lines.append("## Milestones\n")
    for h in HORIZON_ORDER:
        inis = horizons[h]
        if inis:
            lines.append(f"### {horizon_label(h)}\n")
            for i, name in enumerate(inis, 1):
                ini = name_map[name]
                desc = ini.get("description", "")[:120]
                deps_str = f" (depende de: {', '.join(ini.get('dependencies', []))})" if ini.get("dependencies") else ""
                lines.append(f"{i}. **{name}** — {desc}{deps_str}")
            lines.append("")

    # Effort by horizon
    lines.append("## Esfuerzo Total por Horizonte\n")
    lines.append("| Horizonte | Dias totales | Meses totales | Iniciativas |")
    lines.append("|-----------|-------------|---------------|-------------|")
    for h in HORIZON_ORDER:
        inis = horizons[h]
        if inis:
            total_days = sum(name_map[n].get("effort_days", 0) for n in inis)
            total_months = round(total_days / 30, 1)
            lines.append(f"| {horizon_label(h)} | {total_days} | {total_months} | {len(inis)} |")
    lines.append("")

    # Risks per horizon
    lines.append("## Riesgos por Horizonte\n")
    for h in HORIZON_ORDER:
        inis = horizons[h]
        lines.append(f"### {horizon_label(h)}\n")
        if inis:
            for risk in HORIZON_RISKS.get(h, []):
                lines.append(f"- {risk}")
        else:
            lines.append("Sin iniciativas en este horizonte.\n")
        lines.append("")

    lines.append("---\n")
    lines.append("_Generado por roadmap_3h.py — RICE Score = (Reach x Impact x Confidence) / Effort (meses)_\n")

    if dashboard_mode:
        lines.extend(_generate_dashboard_sections(initiatives, vision, horizons, assigned, rice_scores))

    return "\n".join(lines)


def _generate_dashboard_sections(initiatives, vision, horizons, assigned, rice_scores):
    """Genera secciones compatibles con dashboard_populate.py parser.

    Formato: ## O{d}: {title} + **Objective**: + tabla KRs con targets.
    """
    name_map = {ini["name"]: ini for ini in initiatives}
    lines = []
    for idx, ini in enumerate(initiatives, 1):
        h = assigned.get(ini["name"], "h3")
        rice = rice_scores.get(ini["name"], 0)
        lines.append(f"\n## O{idx}: {ini['name']}\n")
        lines.append(f"**Objective**: {ini.get('description', ini['name'])} — Vision: {vision}\n")
        lines.append("| KR | Target |")
        lines.append("|----|--------|")
        kr1 = f"KR1: Implementar {ini['name']} — RICE score objetivo ≥ {rice}"
        lines.append(f"| {kr1} | {ini.get('effort_days', 30)} dias |")
        kr2 = f"KR2: Completar dependencias: {', '.join(ini.get('dependencies', ['ninguna']))}"
        lines.append(f"| {kr2} | Horizonte {h.upper()} |")
        cat = ini.get("category", "general")
        kr3 = f"KR3: Categoria {cat} — entregar con calidad BCG ≥ 7.0"
        lines.append(f"| {kr3} | {rice} RICE |")
        lines.append("")
    return lines


def load_initiatives(path):
    """Carga iniciativas desde archivo JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def interactive_mode():
    """Modo interactivo para ingresar iniciativas manualmente."""
    print("=== Roadmap 3 Horizontes — Modo Interactivo ===\n")
    vision = input("Vision estrategica: ").strip()
    n = int(input("Numero de iniciativas: ").strip())

    initiatives = []
    for i in range(1, n + 1):
        print(f"\n--- Iniciativa {i} ---")
        name = input("  Nombre: ").strip()
        desc = input("  Descripcion: ").strip()
        effort = int(input("  Effort (dias): ").strip())
        deps_input = input("  Dependencias (separadas por coma, vacio si ninguna): ").strip()
        deps = [d.strip() for d in deps_input.split(",") if d.strip()] if deps_input else []
        reach = int(input("  RICE Reach (1-10): ").strip())
        impact = int(input("  RICE Impact (1-5): ").strip())
        confidence = float(input("  RICE Confidence (0.0-1.0): ").strip())
        cat = input("  Categoria (producto/infra/estrategia): ").strip().lower()
        initiatives.append({
            "name": name,
            "description": desc,
            "effort_days": effort,
            "dependencies": deps,
            "rice_reach": reach,
            "rice_impact": impact,
            "rice_confidence": confidence,
            "category": cat,
        })

    return vision, initiatives


def main():
    parser = argparse.ArgumentParser(
        description="Roadmap 3 Horizontes — clasifica iniciativas en H1/H2/H3 con RICE scoring y critical path",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  py -3 .tools/roadmap_3h.py --vision \"Crecer mercado LATAM\" --initiatives initiatives.json\n"
            "  py -3 .tools/roadmap_3h.py --interactive\n"
            "\nFormato initiatives.json:\n"
            "  [{\"name\": \"Iniciativa A\", \"description\": \"...\", \"effort_days\": 30,\n"
            '    "dependencies": [], "rice_reach": 5, "rice_impact": 4,\n'
            '    "rice_confidence": 0.8, "category": "producto"}]\n'
        ),
    )
    parser.add_argument("--vision", type=str, help="Vision estrategica del roadmap")
    parser.add_argument("--initiatives", type=str, help="Archivo JSON con iniciativas")
    parser.add_argument(
        "--interactive", action="store_true", help="Modo interactivo para ingresar datos manualmente"
    )
    parser.add_argument("--output", type=str, help="Archivo de salida (default: stdout)")
    parser.add_argument(
        "--dashboard", action="store_true",
        help="Incluir secciones OKR compatibles con dashboard_populate.py",
    )

    args = parser.parse_args()

    if args.interactive:
        vision, initiatives = interactive_mode()
    elif args.initiatives and args.vision:
        vision = args.vision
        initiatives = load_initiatives(args.initiatives)
    else:
        parser.print_help()
        sys.exit(1)

    if not initiatives:
        print("Error: No se proporcionaron iniciativas.", file=sys.stderr)
        sys.exit(1)

    # Classify horizons
    horizons, assigned = classify_horizon(initiatives)

    # Compute RICE scores
    rice_scores = {}
    for ini in initiatives:
        rice_scores[ini["name"]] = compute_rice(ini)

    # Find critical path
    critical_path = find_critical_path(initiatives)

    # Generate markdown
    markdown = generate_markdown(
        initiatives, vision, horizons, assigned, rice_scores, critical_path,
        dashboard_mode=args.dashboard,
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Roadmap generado: {output_path.resolve()}")
    else:
        print(markdown)


if __name__ == "__main__":
    main()
