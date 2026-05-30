"""metis_mode.py — Detección de modo de operación de Metis.

Lee eval-profile.yaml y determina el modo (strategy|quality) basado en el perfil activo,
temperatura efectiva, y herramientas recomendadas.

Uso:
  py -3 .memory/_scripts/metis_mode.py              # modo actual + perfil
  py -3 .memory/_scripts/metis_mode.py --set quality  # sugerir cambio a quality
  py -3 .memory/_scripts/metis_mode.py --profile desarrollo  # ver modo para perfil
  py -3 .memory/_scripts/metis_mode.py --format json  # output JSON
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ─── Profile → Mode mapping ──────────────────────────────────────────────────
PROFILE_MODE_MAP = {
    "exploracion": "strategy",
    "desarrollo": "strategy",
    "produccion": "strategy",
    "auditoria": "quality",
    "qa": "quality",
}

MODE_TEMPS = {
    "strategy": 0.4,
    "quality": 0.2,
}

MODE_TOOLS = {
    "strategy": [
        "strategy-mcp (RICE, OKR, Wardley, Initiative Scoper)",
        "strategy-extras (SWOT, BMC, Goal Health, Impact Analysis)",
        "exa-search (investigacion de mercado y competencia)",
        "sequential-thinking (descomposicion de problemas)",
        "excalidraw (mapas estrategicos visuales)",
        "paperjsx (reportes ejecutivos PPTX)",
        "bcg_eval_cli.py (evaluacion BCG post-output)",
    ],
    "quality": [
        "session_runner.py (smoke / functional / audit tests)",
        "verification_chain.py (cadena de verificacion cruzada)",
        "score_engine.py (calculo de scores compuestos)",
        "paperjsx (reportes semanales PPTX con tendencias)",
        "bcg_eval_cli.py (evaluacion BCG de OKRs)",
        "quality dashboard (actualizacion de .vault/quality/dashboard.md)",
    ],
}

PROFILE_DESC = {
    "exploracion": "Investigacion inicial, prototipos, brainstorming",
    "desarrollo": "Trabajo estandar, features, refactors",
    "produccion": "Decisiones criticas, ADRs, releases",
    "auditoria": "Revisiones trimestrales, compliance",
    "qa": "Validacion pre-release, compliance",
}

MODE_FOCUS = {
    "strategy": {
        "exploracion": "Brainstorming, prototipos, ideas",
        "desarrollo": "OKRs, roadmaps, analisis estandar",
        "produccion": "ADRs, releases, decisiones criticas",
    },
    "quality": {
        "auditoria": "Auditoria completa, compliance",
        "qa": "Validacion pre-release, compliance",
    },
}


def load_profiles(yaml_path: str | Path) -> dict:
    """Load eval-profile.yaml and return profiles dict."""
    path = Path(yaml_path)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def get_profile_info(profiles: dict, profile_name: str) -> dict | None:
    """Get profile info by name."""
    return profiles.get("profiles", {}).get(profile_name)


def determine_mode(profile_name: str) -> str:
    """Map profile name to mode (strategy | quality)."""
    return PROFILE_MODE_MAP.get(profile_name, "strategy")


def build_mode_info(profile_name: str, profiles: dict) -> dict:
    """Build full mode info dict from profile data."""
    info = get_profile_info(profiles, profile_name)
    mode = determine_mode(profile_name)
    temp = MODE_TEMPS.get(mode, 0.4)
    focus = MODE_FOCUS.get(mode, {}).get(
        profile_name,
        "Estandar" if mode == "strategy" else "Evaluacion",
    )

    return {
        "profile": profile_name,
        "mode": mode,
        "temperature": temp,
        "focus": focus,
        "description": PROFILE_DESC.get(
            profile_name,
            (info.get("description", "") if info else ""),
        ),
        "composite_good": (info.get("thresholds", {}).get("composite_good", "-") if info else "-"),
        "thresholds": (info.get("thresholds", {}) if info else {}),
        "recommended_tools": MODE_TOOLS.get(mode, []),
    }


def format_text(info: dict) -> str:
    """Format mode info as human-readable text."""
    lines = [
        "=" * 50,
        f"  Metis Mode: {info['mode'].upper()}",
        "=" * 50,
        f"  Profile:     {info['profile']}",
        f"  Description: {info['description']}",
        f"  Temperature: {info['temperature']}",
        f"  Focus:       {info['focus']}",
        f"  Comp. Good:  >= {info['composite_good']}",
        "",
        "  Recommended Tools:",
    ]
    for tool in info["recommended_tools"]:
        lines.append(f"    - {tool}")
    return "\n".join(lines)


def format_json(info: dict) -> str:
    """Format mode info as JSON."""
    return json.dumps(info, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Metis Mode Detector — determina modo de operacion basado en perfil activo",
    )
    parser.add_argument(
        "--profile",
        help="Nombre del perfil a evaluar (default: del eval-profile.yaml)",
    )
    parser.add_argument(
        "--set",
        metavar="MODE",
        choices=["strategy", "quality"],
        help="Sugerir cambio de modo (strategy|quality)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Formato de output (default: text)",
    )
    args = parser.parse_args()

    yaml_path = Path(__file__).resolve().parent.parent / "schema" / "eval-profile.yaml"
    profiles = load_profiles(yaml_path)

    # --set mode: suggest mode change
    if args.set:
        temp = MODE_TEMPS.get(args.set, 0.4)
        tools = MODE_TOOLS.get(args.set, [])
        if args.format == "json":
            print(
                json.dumps(
                    {
                        "suggested_mode": args.set,
                        "temperature": temp,
                        "recommended_tools": tools,
                        "message": f"Cambiar a modo {args.set.upper()}",
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print(f">> Mode change suggested: -> {args.set.upper()}")
            print(f"   Temperature: {temp}")
            print("   Recommended Tools:")
            for tool in tools:
                print(f"     - {tool}")
        return

    # Determine profile
    profile_name = args.profile or profiles.get("default_profile", "desarrollo")
    available = list(profiles.get("profiles", {}).keys())
    if profile_name not in available:
        print(
            f"Error: Unknown profile '{profile_name}'. Available: {', '.join(available)}",
            file=sys.stderr,
        )
        sys.exit(1)

    info = build_mode_info(profile_name, profiles)

    if args.format == "json":
        print(format_json(info))
    else:
        print(format_text(info))


if __name__ == "__main__":
    main()
