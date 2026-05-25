from datetime import datetime
from pathlib import Path
import json
import re
import os, sys, time

from lib.config import VAULT_ROOT

# LangGraph orchestrator integration (on-by-default, fallback to legacy)
USE_LANGGRAPH = True
_LANGGRAPH_AVAILABLE = None
def _use_orchestrator() -> bool:
    global _LANGGRAPH_AVAILABLE
    if _LANGGRAPH_AVAILABLE is not None:
        return _LANGGRAPH_AVAILABLE and USE_LANGGRAPH
    try:
        from lib import orchestrator
        _LANGGRAPH_AVAILABLE = True
    except Exception:
        _LANGGRAPH_AVAILABLE = False
    return _LANGGRAPH_AVAILABLE and USE_LANGGRAPH

STATUS_PATH = VAULT_ROOT / "_pipeline" / "status.md"
INPUT_PATH = VAULT_ROOT / "_pipeline" / "input.md"
PIPELINE_LOG = VAULT_ROOT / "_pipeline" / "log.md"
PROFILES_DIR = VAULT_ROOT / "_pipeline" / "profiles"
CONTEXT_PATH = VAULT_ROOT / "_pipeline" / "context.json"
STALE_MINUTES = 30
CANCEL_MINUTES = 120
PYTHON = "py" if __import__("sys").platform == "win32" else "python3"
SCRIPTS = (Path(__file__).resolve().parent.parent)


def _load_profile(profile: str) -> dict:
    path = PROFILES_DIR / f"{profile}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"name": "standard", "depth": 2, "tools": ["exa-search", "searxng", "sequential-thinking"]}


def _read_status() -> list[str]:
    if STATUS_PATH.exists():
        return STATUS_PATH.read_text(encoding="utf-8").split("\n")
    return []


def _write_status(lines: list[str]) -> None:
    STATUS_PATH.write_text("\n".join(lines), encoding="utf-8")


def _log_entry(msg: str) -> None:
    entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {msg}\n"
    with open(PIPELINE_LOG, "a", encoding="utf-8") as f:
        f.write(entry)


def save_context(agent: str, data: dict) -> None:
    """Guarda resumen de contexto del agente para el siguiente en el pipeline.
    
    Cross-agent memory:
    - Aletheia stores code_context → Kratos reads it
    - Kratos stores curation_context → Mnemosyne reads it
    - Metis stores strategy_summary → Kratos uses it for implementation
    """
    ctx = {"pipeline_id": "", "agents": [], "context_summary": {},
           "files_read": [], "files_written": [], "cross_agent": {}}
    if CONTEXT_PATH.exists():
        try:
            ctx = json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    if agent not in ctx["agents"]:
        ctx["agents"].append(agent)
    ctx["context_summary"][agent] = {
        "key_findings": data.get("key_findings", []),
        "sources_used": data.get("sources_used", []),
        "token_estimate": data.get("token_estimate", 0),
    }
    ctx["files_read"] = list(set(ctx["files_read"] + data.get("files_read", [])))
    ctx["files_written"] = list(set(ctx["files_written"] + data.get("files_written", [])))
    
    # Cross-agent memory passing
    if "cross_agent" not in ctx:
        ctx["cross_agent"] = {}
    if agent == "aletheia" and "code_context" in data:
        ctx["cross_agent"]["aletheia_to_kratos"] = data["code_context"]
    if agent == "metis" and "strategy_summary" in data:
        ctx["cross_agent"]["metis_to_kratos"] = data["strategy_summary"]
    if agent == "kratos":
        if "curation_context" in data:
            ctx["cross_agent"]["kratos_to_mnemosyne"] = data["curation_context"]
        # Kratos decision for deep routing
        kratos_decision = data.get("kratos_decision", "needs_curation")
        ctx["cross_agent"]["kratos_decision"] = kratos_decision
    
    # Flash exploration context (sistema DUAL)
    if agent == "flash_exploration" and "exploration" in data:
        if "cross_agent" not in ctx:
            ctx["cross_agent"] = {}
        ctx["cross_agent"]["flash_exploration"] = data["exploration"]
    
    # Leer pipeline_id del status
    status_lines = _read_status()
    for line in status_lines:
        m = re.search(r"\*\*status\*\*:\s*(\S+)", line)
    m_id = re.search(r"## Active:\s*(.+)", "\n".join(status_lines))
    if m_id:
        ctx["pipeline_id"] = m_id.group(1).strip()
    CONTEXT_PATH.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding="utf-8")


def load_context() -> dict:
    """Lee el contexto compartido del pipeline actual."""
    if CONTEXT_PATH.exists():
        try:
            return json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"pipeline_id": "", "agents": [], "context_summary": {},
            "files_read": [], "files_written": [], "cross_agent": {}}


def get_cross_context(target_agent: str) -> dict:
    """Get cross-agent context intended for a specific agent.
    
    Args:
        target_agent: "kratos" or "mnemosyne"
    
    Returns:
        dict with context from previous agents, or empty dict
    """
    ctx = load_context()
    ca = ctx.get("cross_agent", {})
    if target_agent == "kratos":
        return {
            "aletheia_code_context": ca.get("aletheia_to_kratos", {}),
            "metis_strategy": ca.get("metis_to_kratos", {}),
        }
    elif target_agent == "mnemosyne":
        return {
            "kratos_curation_context": ca.get("kratos_to_mnemosyne", {}),
            "kratos_decision": ca.get("kratos_decision", "needs_curation"),
        }
    return {}


def _check_flash_exploration(topic: str) -> dict | None:
    """Check if there's recent Flash exploration for this topic."""
    bridge_reports = list((VAULT_ROOT.parent / ".memory" / "bridge" / "reports").glob("*.md"))
    recent = [r for r in bridge_reports
              if (datetime.now() - datetime.fromtimestamp(r.stat().st_mtime)).total_seconds() < 3600]
    if not recent:
        return None
    topic_words = set(topic.lower().split())
    for r in sorted(recent, reverse=True):
        content = r.read_text(encoding="utf-8", errors="replace").lower()
        if any(w in content for w in topic_words):
            return {
                "source": str(r.name),
                "age_seconds": (datetime.now() - datetime.fromtimestamp(r.stat().st_mtime)).total_seconds(),
                "report_path": str(r.relative_to(VAULT_ROOT.parent / ".memory")),
            }
    return None


def init(topic: str, profile: str = "standard", check_flash: bool = True) -> str:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    pipeline_id = datetime.now().strftime("P-%Y%m%d-%H%M%S")
    slug = re.sub(r'[^a-z0-9\s-]', '', topic.lower())
    slug = re.sub(r'\s+', '-', slug)[:60]

    flash_ctx = _check_flash_exploration(topic) if check_flash else None
    if not flash_ctx:
        hint_cmd = 'vault.py dual "' + topic + '"'
        print("Sugerencia: explora primero con '" + hint_cmd + "' para iteracion rapida con Gemini Flash (gratis, <2min)")
    
    # Track estimated cost
    estimated_cost = 0.0
    try:
        from lib.dsol import TokenTracker
        tt = TokenTracker()
        stats = tt.get_stats()
        estimated_cost = stats.get("total_cost_usd", 0.0)
    except Exception:
        pass
    
    # Warm up model cache + seed CodeExperience
    try:
        from lib.vectorstore import warmup_model
        warmup_model()
    except Exception:
        pass
    try:
        from lib.seed_ce import seed_code_experiences
        seed_code_experiences()
    except Exception:
        pass
    try:
        from lib.kratos_hook import init_code_memory_hook
        init_code_memory_hook()
    except Exception:
        pass

    # Track flash→production link
    if flash_ctx:
        try:
            fps_dir = VAULT_ROOT.parent / ".vault" / "quality" / "timeseries"
            fps_dir.mkdir(parents=True, exist_ok=True)
            fps_file = fps_dir / "flash-production.json"
            data = {"links": []}
            if fps_file.exists():
                try:
                    data = json.loads(fps_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            data["links"].append({
                "pipeline_id": pipeline_id,
                "flash_report": flash_ctx.get("report_path", ""),
                "topic": topic,
                "timestamp": datetime.now().isoformat(),
            })
            data["links"] = data["links"][-100:]
            fps_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass
    
    prof = _load_profile(profile)
    tools_str = ", ".join(prof.get("tools", ["exa-search", "searxng", "sequential-thinking"]))

    code_keywords = ["code", "codigo", "implement", "program", "function", "class",
                     "bug", "error", "test", "refactor", "debug", "pull request", "pr",
                     "algorithm", "api", "script", "library", "package", "module"]
    has_code = any(kw in topic.lower() for kw in code_keywords)
    kratos_output = f"code/{slug}.md"
    mnemosyne_step = 5 if has_code else 4
    first_status = "aletheia-ready"

    lines = [
        f"# Pipeline Status",
        f"*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        f"## Active: {pipeline_id}",
        f"- **topic**: {topic}",
        f"- **profile**: {profile}",
        f"- **depth**: {prof.get('depth', 'standard')}",
        f"- **tools**: {tools_str}",
        f"- **created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- **status**: {first_status}",
        "",
        "## Steps",
        "| Step | Agent | Status | Output | Started | Elapsed |",
        "|------|-------|--------|--------|---------|--------|",
        f"| 1 | Aletheia | :clock1: ready | raw/{slug}.md | — | — |",
        f"| 2 | Kosmos | :hourglass: pending | schema/{slug}-adr.md | — | — |",
        f"| 3 | Metis | :hourglass: pending | wiki/{slug}-strategy.md | — | — |",
    ]
    if has_code:
        lines.append(f"| 4 | Kratos | :hourglass: pending | {kratos_output} | — | — |")
        lines.append(f"| 5 | Mnemosyne | :hourglass: pending | curation | — | — |")
    else:
        lines.append(f"| 4 | Mnemosyne | :hourglass: pending | curation | — | — |")
    if flash_ctx:
        lines.insert(0, f"> 🟢 Flash exploration found: `{flash_ctx['report_path']}` ({int(flash_ctx['age_seconds'])}s old)")
        lines.append("")
        lines.append("## Dual Context (Flash)")
        lines.append(f"- **Report**: {flash_ctx['report_path']}")
        lines.append(f"- **Age**: {int(flash_ctx['age_seconds'])}s")
        lines.append("")

    lines += [
        "",
        "## Profile Info",
        f"- **Type**: {profile}",
        f"- **Max queries**: {prof.get('max_queries', 'auto')}",
        f"- **Thinking mode**: {prof.get('thinking_mode', 'none')}",
        f"- **Model**: {prof.get('model', 'deepseek-v4-flash')}",
        f"- **Triangulation**: {'yes' if prof.get('triangulation') else 'no'}",
        f"- **Est. time**: {prof.get('time_estimate_min', '?')} min",
        "",
        "## Previous Pipelines",
        "| ID | Topic | Status | Completed |",
        "|----|-------|--------|-----------|",
    ]

    # Preserve previous pipelines
    old_text = "\n".join(_read_status())
    prev_section = re.search(r"## Previous Pipelines\n(.+?)(?=\n##|\Z)", old_text, re.DOTALL)
    if prev_section:
        prev_lines = [l for l in prev_section.group(1).split("\n") if l.strip() and not l.strip().startswith("| ID |")]
        if prev_lines:
            lines.extend(prev_lines)

    _write_status(lines)

    input_content = (
        f"# Pipeline Input: {topic}\n\n"
        f"*Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
        f"*Pipeline ID: {pipeline_id}*\n"
        f"*Profile: {profile}*\n"
        f"*Depth: {prof.get('depth', 'standard')}*\n"
        f"*Tools: {tools_str}*\n\n"
        f"## Research Question\n\n{topic}\n\n"
        f"## Expected Outputs\n\n"
        f"1. Aletheia: Investigation in raw/{slug}.md\n"
        f"2. Kosmos: Architecture analysis in schema/{slug}-adr.md\n"
        f"3. Metis: Strategy synthesis in wiki/{slug}-strategy.md\n"
    )
    INPUT_PATH.write_text(input_content, encoding="utf-8")

    # Save started_at for duration tracking
    try:
        (VAULT_ROOT / "_pipeline" / "started_at.txt").write_text(str(datetime.now().timestamp()), encoding="utf-8")
    except Exception:
        pass

    _log_entry(f"Pipeline {pipeline_id} initialized: {topic} [{profile}]")
    
    # LangGraph integration
    lg_msg = ""
    if _use_orchestrator():
        lg_msg = "\nOrchestrator: LangGraph DAG (checkpointing + LangSmith)"
        try:
            from lib.orchestrator import build_graph
            bg = build_graph()
            lg_msg += f"\nNodes: {', '.join(list(bg.nodes.keys())[1:])}"
        except Exception:
            lg_msg += "\nNodes: (graph build deferred)"
    
    return (f"Pipeline {pipeline_id} initialized.\n"
            f"Topic: {topic}\nProfile: {profile}\n"
            f"Status: aletheia-ready\n"
            f"Tools: {tools_str}\n"
            f"Next: vault.py hydrate --agent aletheia{lg_msg}")


def check(agent: str = "") -> str:
    lines = _read_status()
    if not lines:
        return "PIPELINE: no active pipeline"

    text = "\n".join(lines)

    m = re.search(r"\*\*status\*\*:\s*(\S+)", text)
    if not m:
        return "PIPELINE: status not found"
    status = m.group(1)

    if status in ("idle", "complete"):
        return "PIPELINE: idle (no active pipeline)"

    topic_m = re.search(r"\*\*topic\*\*:\s*(.+?)$", text, re.MULTILINE)
    topic = topic_m.group(1).strip() if topic_m else ""

    profile_m = re.search(r"\*\*profile\*\*:\s*(.+)", text)
    profile = profile_m.group(1).strip() if profile_m else "standard"

    if agent:
        pattern = r"\| \d+ \| " + re.escape(agent) + r" \| (.+?) \|"
        am = re.search(pattern, text, re.IGNORECASE)
        if am:
            agent_status = am.group(1).strip()
            if "ready" in agent_status or ":clock1:" in agent_status:
                return (
                    f"PIPELINE: task available for {agent}\n"
                    f"  Topic: {topic}\n"
                    f"  Profile: {profile}\n"
                    f"  Action: read _pipeline/input.md, work, write output, then: vault.py pipeline step-done --agent {agent}\n"
                )
            elif "done" in agent_status or ":white_check_mark:" in agent_status:
                return f"PIPELINE: {agent} completed. Next agent should be ready."
            else:
                return f"PIPELINE: {agent} not ready (status: {agent_status})"
        else:
            return f"PIPELINE: {agent} not found in pipeline"

    return f"PIPELINE: active ({status})\n  Topic: {topic}\n  Profile: {profile}"


def step_done(agent: str) -> str:
    lines = _read_status()
    if not lines:
        return "ERROR: no active pipeline"

    text_lines = lines
    text = "\n".join(text_lines)

    status_m = re.search(r"\*\*status\*\*:\s*(\S+)", text)
    if not status_m or status_m.group(1) == "idle":
        return "ERROR: no active pipeline to update"

    agents_order = ["Aletheia", "Kosmos", "Metis", "Kratos", "Mnemosyne"]
    agent_cap = agent.capitalize()
    if agent_cap not in agents_order:
        return f"ERROR: unknown agent {agent}"

    # Detect if Kratos is in the pipeline table (exclude Previous Pipelines section)
    pipeline_table = "\n".join(
        l for l in text_lines if not l.startswith("| `P-")  # skip Previous Pipelines rows
    )
    has_kratos = " Kratos " in pipeline_table

    agent_idx = agents_order.index(agent_cap)
    # Skip Kratos in the routing if he's not in the pipeline
    next_agent = None
    for i in range(agent_idx + 1, len(agents_order)):
        candidate = agents_order[i]
        if candidate == "Kratos" and not has_kratos:
            continue
        next_agent = candidate
        break

    new_lines = []
    for line in text_lines:
        if re.match(r"\| \d+ \| " + re.escape(agent_cap) + r" \|", line):
            line = re.sub(r":clock1: ready|:hourglass: pending", ":white_check_mark: done", line)
            now = datetime.now().strftime("%H:%M")
            if "Elapsed" not in line:
                line = line.rstrip() + f" | {now}"
            if next_agent:
                line = line.replace(f":hourglass: pending", ":clock1: ready", 1)
        if next_agent and re.match(r"\| \d+ \| " + re.escape(next_agent) + r" \|", line):
            line = line.replace(":hourglass: pending", ":clock1: ready")
        new_lines.append(line)

    for i, line in enumerate(new_lines):
        if line.strip().startswith("- **status**:"):
            if next_agent:
                new_lines[i] = f"- **status**: {next_agent.lower()}-ready"
            else:
                new_lines[i] = "- **status**: complete"
            break

    _write_status(new_lines)
    _log_entry(f"Pipeline step done: {agent}" + (f" → {next_agent} ready" if next_agent else " → COMPLETE"))

    if not next_agent:
        try:
            from lib.dsol import TokenTracker
            tt = TokenTracker()
            stats = tt.get_stats()
            qual_dir = VAULT_ROOT.parent / ".vault" / "quality" / "timeseries"
            qual_dir.mkdir(parents=True, exist_ok=True)
            durations_file = qual_dir / "pipeline-durations.json"
            data = {"entries": []}
            if durations_file.exists():
                try:
                    data = json.loads(durations_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            started_at_path = VAULT_ROOT / "_pipeline" / "started_at.txt"
            duration_s = 0
            if started_at_path.exists():
                try:
                    started = float(started_at_path.read_text().strip())
                    duration_s = int((datetime.now().timestamp() - started) * 1000) / 1000
                except Exception:
                    pass
            profile_from_status = "desarrollo"
            status_text = "\n".join(_read_status())
            pm = re.search(r"\*\*profile\*\*:\s*(\S+)", status_text)
            if pm: profile_from_status = pm.group(1)
            data["entries"].append({
                "timestamp": datetime.now().isoformat(),
                "duration_s": duration_s,
                "profile": profile_from_status,
                "total_cost_usd": stats.get("total_cost_usd", 0),
                "total_calls": stats.get("total_calls", 0),
            })
            data["entries"] = data["entries"][-100:]
            durations_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    # Capture Kratos output into CodeExperience
    if agent_cap == "Kratos":
        try:
            from lib.kratos_hook import capture_agent_output
            for line in text_lines:
                m = re.match(r"\| \d+ \| Kratos \|.+?\| (.+?) \|", line)
                if m:
                    output_path = (VAULT_ROOT / m.group(1).strip()).with_suffix(".md")
                    if output_path.exists():
                        capture_agent_output(output_path.read_text(errors="replace"))
                    break
        except Exception:
            pass

    # Auto-trigger curation when pipeline completes
    if not next_agent:
        import subprocess
        curation_cmd = [PYTHON, str(SCRIPTS / "run_curation.py")]
        try:
            subprocess.Popen(curation_cmd)
            _log_entry("Curation auto-triggered after pipeline completion")
        except Exception as e:
            _log_entry(f"Curation trigger failed: {e}")

        try:
            subprocess.Popen(
                [PYTHON, str(SCRIPTS / "vault.py"), "viz"],
                cwd=SCRIPTS.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            _log_entry("Viz auto-generated after pipeline completion")
        except Exception as e:
            _log_entry(f"Viz generation failed: {e}")

        try:
            subprocess.Popen(
                [PYTHON, str(SCRIPTS / "vault.py"), "consolidate"],
                cwd=SCRIPTS.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            _log_entry("Consolidation auto-triggered after pipeline completion")
        except Exception as e:
            _log_entry(f"Consolidation trigger failed: {e}")

        try:
            subprocess.Popen(
                [PYTHON, str(SCRIPTS / "vault.py"), "dashboard"],
                cwd=SCRIPTS.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            _log_entry("Dashboard auto-updated after pipeline completion")
        except Exception as e:
            _log_entry(f"Dashboard update failed: {e}")

        try:
            subprocess.Popen(
                [PYTHON, str(SCRIPTS / "vault.py"), "improve", "wikilinks", "--apply"],
                cwd=SCRIPTS.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            _log_entry("Wikilink auto-fix triggered after pipeline completion")
        except Exception as e:
            _log_entry(f"Wikilink auto-fix failed: {e}")

    return f"Pipeline: {agent} done" + (f", {next_agent} ready" if next_agent else ", pipeline complete!")


def check_stale() -> str:
    lines = _read_status()
    if not lines:
        return "No stale pipelines."

    text = "\n".join(lines)

    m = re.search(r"\*\*status\*\*:\s*(.+)", text)
    if not m or m.group(1).strip() in ("idle", "complete"):
        return "No active pipeline to check."

    stale_found = False
    results = []
    for line in lines:
        if re.match(r"\| \d+ \|", line):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                agent = parts[2]
                status = parts[3]
                elapsed_str = parts[6] if len(parts) > 6 else "—"

                if "ready" in status or ":clock1:" in status:
                    if elapsed_str and elapsed_str != "—":
                        try:
                            t = datetime.strptime(elapsed_str.strip(), "%H:%M")
                            elapsed_min = (datetime.now() - t).total_seconds() / 60
                            if elapsed_min > CANCEL_MINUTES:
                                results.append(f"CANCELLED: {agent} stale >{CANCEL_MINUTES}min")
                                stale_found = True
                            elif elapsed_min > STALE_MINUTES:
                                results.append(f"STALE: {agent} waiting {int(elapsed_min)}min")
                                stale_found = True
                        except ValueError:
                            pass

    if not stale_found:
        return "Pipeline healthy, no stale steps."

    return "\n".join(results)


def watch(interval: int = 15, max_cycles: int = 0, max_minutes: int = 0) -> str:
    """Poll pipeline status. Auto-detect handoffs. Optional max_minutes timeout."""
    import time

    cycle = 0
    last_status = ""
    start_time = time.time()
    while True:
        if max_minutes > 0 and (time.time() - start_time) > max_minutes * 60:
            print(f"[watch] Timeout after {max_minutes} minutes.")
            return "Watch timeout."
        lines = _read_status()
        text = "\n".join(lines)

        m = re.search(r"\*\*status\*\*:\s*(\S+)", text)
        current = m.group(1) if m else "idle"

        if current != last_status:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] Pipeline status: {current}")
            if current == "complete":
                print("[watch] Pipeline complete.")
                return "Pipeline complete."
            if current != "idle" and current != last_status:
                _log_entry(f"Auto-detected status change: {last_status} → {current}")
            last_status = current

        cycle += 1
        if max_cycles and cycle >= max_cycles:
            return f"Watch ended after {cycle} cycles."
        time.sleep(interval)
