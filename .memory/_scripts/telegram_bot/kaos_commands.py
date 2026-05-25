"""Comandos de control de KAOS: pipeline, agentes, salud, calidad."""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from lib.format import boxify as _box

_LOG = logging.getLogger(__name__)

SCRIPTS = Path(__file__).resolve().parent.parent
VAULT_ROOT = SCRIPTS.parent
PIPELINE_DIR = VAULT_ROOT / "_pipeline"
PROFILES_DIR = PIPELINE_DIR / "profiles"
STATUS_PATH = PIPELINE_DIR / "status.md"
CONTEXT_PATH = PIPELINE_DIR / "context.json"
DASHBOARD_DIR = VAULT_ROOT / "dashboard"
QUALITY_DIR = VAULT_ROOT.parent / ".vault" / "quality"

PYTHON = "py"

def _read_status() -> dict:
    info = {"status": "idle", "topic": "", "profile": "", "agents": []}
    if not STATUS_PATH.exists():
        return info
    try:
        text = STATUS_PATH.read_text(encoding="utf-8")
        import re
        sm = re.search(r"\*\*status\*\*:\s*(\S+)", text)
        if sm:
            info["status"] = sm.group(1)
        tm = re.search(r"\*\*topic\*\*:\s*(.+?)$", text, re.MULTILINE)
        if tm:
            info["topic"] = tm.group(1).strip()
        pm = re.search(r"\*\*profile\*\*:\s*(.+)", text)
        if pm:
            info["profile"] = pm.group(1).strip()
        for m in re.finditer(r"\| \d+ \| (\w+) \| (.+?) \|", text):
            info["agents"].append({"name": m.group(1), "status": m.group(2).strip()})
    except Exception:
        pass
    return info

def _load_token_usage() -> dict:
    p = VAULT_ROOT / "cache" / "token-usage.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

async def cmd_kaospipeline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = _read_status()
    status = info["status"]
    topic = info["topic"] or "—"
    profile = info["profile"] or "—"
    agents = info.get("agents", [])
    agent_lines = []
    for a in agents:
        icon = {"ready": "🟡", "done": "✅", "running": "🟢", "pending": "⏳", "failed": "❌"}
        s = a["status"].lower()
        agent_lines.append(f"  {icon.get(s, '⏳')} {a['name']}: {a['status']}")

    msg = (
        f"📌 Estado: {status}\n"
        f"📋 Tema: {topic}\n"
        f"👤 Perfil: {profile}\n"
        f"{chr(10).join(agent_lines) if agent_lines else '  (sin pipeline activo)'}"
    )
    await update.message.reply_text(_box(msg, "🤖 KAOS PIPELINE"), parse_mode="Markdown")

async def cmd_kaosstart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(context.args) if context.args else ""
    if not topic:
        await update.message.reply_text("Uso: /kaosstart <tema> [--profile produccion]")
        return
    profile = "desarrollo"
    args_list = context.args
    if "--profile" in args_list:
        idx = args_list.index("--profile")
        if idx + 1 < len(args_list):
            profile = args_list[idx + 1]
            topic_parts = [a for a in args_list if not a.startswith("--")]
            topic = " ".join(topic_parts[:topic_parts.index("--profile")] if "--profile" in topic_parts else topic_parts)
    await update.message.reply_text(
        _box(f"Iniciando pipeline para:\n\n{topic}\n\nPerfil: {profile}", "🚀 KAOS START"),
        parse_mode="Markdown"
    )
    asyncio = __import__("asyncio")
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _run_pipeline, topic, profile)

def _run_pipeline(topic: str, profile: str):
    try:
        from lib.pipeline import init
        result = init(topic, profile=profile)
        _LOG.info("Pipeline started: %s", result)
    except Exception as e:
        _LOG.error("Pipeline start failed: %s", e)

async def cmd_kaosstop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        _box("⏹ Señal de stop enviada.\n\nPara pipelines en OpenCode,\ncierra el proceso manualmente.", "⏹ KAOS STOP"),
        parse_mode="Markdown"
    )

async def cmd_kaosagentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = _read_status()
    agents = info.get("agents", [])
    if not agents:
        await update.message.reply_text("No hay pipeline activo.")
        return
    lines = [f"{'✅' if 'done' in a['status'] else '🟡' if 'ready' in a['status'] else '⏳'} {a['name']}: {a['status']}" for a in agents]
    await update.message.reply_text(
        _box("\n".join(lines), "🤖 AGENTES"),
        parse_mode="Markdown"
    )

async def cmd_kaoshealth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    health_data = {}
    try:
        dashboard = DASHBOARD_DIR / "dashboard.json"
        if dashboard.exists():
            health_data = json.loads(dashboard.read_text(encoding="utf-8")).get("health", {})
    except Exception:
        pass
    overall = health_data.get("overall", "N/A")
    lint = health_data.get("lint_issues", "N/A")
    git = health_data.get("git_clean", "N/A")
    msg = (
        f"💚 Salud: {overall}\n"
        f"📋 Lint: {lint}\n"
        f"📁 Git clean: {'✅' if git else '❌' if git != 'N/A' else 'N/A'}"
    )
    await update.message.reply_text(_box(msg, "💚 KAOS HEALTH"), parse_mode="Markdown")

async def cmd_kaosscores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scores = {}
    try:
        ev = PIPELINE_DIR / "evaluation.json"
        if ev.exists():
            scores = json.loads(ev.read_text(encoding="utf-8"))
    except Exception:
        pass
    composite = scores.get("composite", scores.get("critic_score", "N/A"))
    msg = f"📊 Score compuesto: {composite}/100"
    for k, v in scores.items():
        if isinstance(v, (int, float)) and k not in ("composite",):
            msg += f"\n  {k}: {v}"
    await update.message.reply_text(_box(msg, "⭐ KAOS SCORES"), parse_mode="Markdown")
