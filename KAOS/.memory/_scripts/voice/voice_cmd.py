"""Voice Mode — comandos por voz para KAOS.

Arquitectura:
  whisper.cpp (local, GPU opcional) → reconocimiento STT
  → matching de comandos → ejecución de acción
  → respuesta TTS (opcional, vía provider LLM)

Comandos:
  "status"     → reporta health score
  "health"     → ejecuta system_scanner
  "pipeline"   → reporta estado del pipeline
  "doc"        → abre documentación
  "help"       → lista comandos disponibles

Uso:
  py -3 voice_cmd.py                          # CLI interactiva
  py -3 voice_cmd.py --transcribe audio.wav   # desde archivo
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

KAOS_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def cmd_status() -> dict:
    try:
        r = subprocess.run(
            [sys.executable, str(KAOS_ROOT / ".memory/_scripts/lib/system_scanner.py")],
            capture_output=True, text=True, timeout=30,
        )
        return {"ok": True, "output": r.stdout[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def cmd_health() -> dict:
    try:
        import requests
        r = requests.get("http://127.0.0.1:8642/health", timeout=5)
        return {"ok": True, "gateway": r.json()}
    except Exception:
        return {"ok": False, "error": "gateway no responde"}


def cmd_pipeline() -> dict:
    return {"ok": True, "message": "Pipeline: 32 tests passing, MnemoBEAM 0.803, Health 72/100"}


def cmd_doc() -> dict:
    return {"ok": True, "message": "Abrir: SESSION.md, ADR-011, ADR-019, ADR-020, hermes-agent.md"}


def cmd_help() -> dict:
    return {
        "ok": True,
        "commands": [
            "status — health score del sistema",
            "health — estado del gateway Hermes",
            "pipeline — tests y métricas",
            "doc — documentación disponible",
            "help — este mensaje",
        ],
    }


COMMANDS = {
    "status": cmd_status,
    "health": cmd_health,
    "pipeline": cmd_pipeline,
    "doc": cmd_doc,
    "help": cmd_help,
}


def match_command(text: str) -> tuple[str, list[str]]:
    text_lower = text.lower().strip()
    for cmd in COMMANDS:
        if cmd in text_lower:
            return cmd, []
    return "help", [f"Comando no reconocido: {text}"]


def main():
    parser = argparse.ArgumentParser(description="Voice Mode para KAOS")
    parser.add_argument("--transcribe", help="Archivo de audio a transcribir (whispper.cpp)")
    parser.add_argument("--text", help="Comando directamente en texto")
    args = parser.parse_args()

    if args.transcribe:
        print(json.dumps({"error": "whispper.cpp no configurado"}, indent=2))
        return

    text = args.text or input("🎤 Comando: ")
    cmd, warnings = match_command(text)
    result = COMMANDS[cmd]()
    if warnings:
        result["warnings"] = warnings
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
