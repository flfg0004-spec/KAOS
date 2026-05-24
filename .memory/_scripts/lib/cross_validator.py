"""Cross-validation: Gemini Flash critiques DeepSeek output.

For production profile, runs after pipeline completes.
Flash critica el output → si discrepancia > umbral, Opus arbitra.
"""

import json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent.parent


def run(output_path: str = "", profile: str = "desarrollo") -> str:
    """Run cross-validation on an output file using Gemini Flash.

    Args:
        output_path: Path to the markdown output to validate
        profile: Evaluation profile (desarrollo/produccion/auditoria)

    Returns:
        Validation report as string
    """
    if not output_path:
        output_path = str(BASE / "wiki" / "index.md")

    target = Path(output_path)
    if not target.exists():
        return f"ERROR: file not found: {output_path}"

    content = target.read_text(encoding="utf-8", errors="replace")

    # Build critique prompt
    prompt = (
        "Eres un crítico de calidad. Evalúa este output de un agente IA.\n\n"
        f"## Output a evaluar\n\n{content[:3000]}\n\n"
        "## Criterios\n"
        "- Veracidad: ¿los datos parecen correctos?\n"
        "- Completitud: ¿cubre el tema adecuadamente?\n"
        "- Coherencia: ¿es internamente consistente?\n"
        "- Utilidad: ¿es accionable?\n\n"
        "## Formato de respuesta\n"
        "```json\n"
        '{"veracidad": <0-100>, "completitud": <0-100>, '
        '"coherencia": <0-100>, "utilidad": <0-100>, '
        '"discrepancias": ["...", "..."], "recomendacion": "..."}\n'
        "```\n"
    )

    try:
        from lib.agy_client import call_agy
        result = call_agy(prompt, tier="flash", timeout=120)
        flash_text = result.get("text", "")

        # Extract JSON from response
        json_start = flash_text.find("```json")
        json_end = flash_text.rfind("```")
        if json_start >= 0:
            json_str = flash_text[json_start + 7:json_end].strip()
            scores = json.loads(json_str)
        else:
            scores = {"veracidad": 0, "completitud": 0, "coherencia": 0, "utilidad": 0}

        avg_score = sum(scores.get(k, 0) for k in ("veracidad", "completitud", "coherencia", "utilidad")) / 4

        lines = [
            f"# Cross-Validation Report",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            f"*Output: {output_path}*",
            f"*Profile: {profile}*",
            "",
            f"## Scores (Gemini Flash)",
            f"- Veracidad: {scores.get('veracidad', '?')}/100",
            f"- Completitud: {scores.get('completitud', '?')}/100",
            f"- Coherencia: {scores.get('coherencia', '?')}/100",
            f"- Utilidad: {scores.get('utilidad', '?')}/100",
            f"- **Promedio: {avg_score:.0f}/100**",
            "",
        ]

        discrepancies = scores.get("discrepancias", [])
        if discrepancies:
            lines.append("## Discrepancias Detectadas")
            for d in discrepancies:
                lines.append(f"- {d}")

            if profile == "produccion" and avg_score < 60:
                lines.append("")
                lines.append("### Arbitraje con Opus (discrepancia crítica)")
                try:
                    opus_result = call_agy(
                        f"Arbitra este conflicto de evaluación. Output:\n{content[:2000]}\nCrítica:\n{flash_text[:1000]}",
                        tier="opus", timeout=180,
                    )
                    lines.append(opus_result.get("text", "(sin respuesta)")[:500])
                except Exception as e:
                    lines.append(f"Arbitraje falló: {e}")
        else:
            lines.append("## Discrepancias: Ninguna detectada ✅")

        report = "\n".join(lines)

        # Save report
        reports_dir = BASE.parent / ".vault" / "quality" / "verifications"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"cross-val-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        report_path.write_text(report, encoding="utf-8")

        return report

    except Exception as e:
        return f"ERROR en cross-validation: {e}"
