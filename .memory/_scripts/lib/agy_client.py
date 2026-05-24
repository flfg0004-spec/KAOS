"""Wrapper for agy --print with transcript parsing and filesystem signaling.

Uses direct agy --print subprocess (bypasses agy-mcp auth checks)
and reads response from agy's local brain/transcript storage.
Includes file locking for safe concurrent access to settings.json.
"""

import json
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

ModelTier = Literal["flash", "sonnet", "opus"]

BRIDGE_DIR = Path(__file__).resolve().parent.parent.parent / "bridge"
SIGNALS_DIR = BRIDGE_DIR / "signals"
REPORTS_DIR = BRIDGE_DIR / "reports"
LOCKS_DIR = BRIDGE_DIR / "locks"

SETTINGS_DIR = Path.home() / ".gemini" / "antigravity-cli"
BRAIN_DIR = SETTINGS_DIR / "brain"
POOL = {tier: SETTINGS_DIR / f"settings.{tier}.json" for tier in ("flash", "sonnet", "opus")}
LOCK_FILE = LOCKS_DIR / "settings.lock"

MODEL_NAMES = {
    "flash": "Gemini 3.5 Flash",
    "sonnet": "Claude Sonnet 4.6",
    "opus": "Claude Opus 4.6",
}


def _ensure_dirs():
    for d in (SIGNALS_DIR, REPORTS_DIR, LOCKS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _acquire_lock(timeout: float = 10.0) -> bool:
    """Try to acquire the settings lock. Returns True if acquired."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            fd = LOCK_FILE.open("x")
            fd.write(str(time.time()))
            fd.close()
            return True
        except FileExistsError:
            time.sleep(0.1)
    return False


def _release_lock():
    try:
        LOCK_FILE.unlink()
    except FileNotFoundError:
        pass


def _brain_snapshot() -> set[str]:
    """Return set of conversation IDs currently in brain/."""
    if not BRAIN_DIR.exists():
        return set()
    return {p.name for p in BRAIN_DIR.iterdir() if p.is_dir()}


def _switch_model(tier: ModelTier) -> str:
    """Swap agy settings.json to desired model. Returns previous model."""
    settings_path = SETTINGS_DIR / "settings.json"
    current = json.loads(settings_path.read_text(encoding="utf-8"))
    prev = current["model"]
    pool_path = POOL[tier]
    if pool_path.exists():
        import shutil
        shutil.copy(str(pool_path), str(settings_path))
    else:
        current["model"] = MODEL_NAMES[tier]
        settings_path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return prev


def _restore_model(model: str):
    settings_path = SETTINGS_DIR / "settings.json"
    current = json.loads(settings_path.read_text(encoding="utf-8"))
    current["model"] = model
    settings_path.write_text(json.dumps(current, indent=2), encoding="utf-8")


def _read_transcript(conv_id: str) -> str:
    """Read the model response from a conversation transcript."""
    transcript = BRAIN_DIR / conv_id / ".system_generated" / "logs" / "transcript.jsonl"
    if not transcript.exists():
        return ""
    for line in transcript.read_text(encoding="utf-8").strip().split("\n"):
        try:
            entry = json.loads(line)
            if entry.get("source") == "MODEL" and entry.get("type") == "PLANNER_RESPONSE":
                return entry.get("content", "")
        except Exception:
            continue
    return ""


def call_agy(prompt: str, tier: ModelTier = "flash", timeout: int = 180) -> dict:
    """Call agy --print with model tier. Returns structured result.

    Thread-safe: uses file locking to prevent concurrent settings.json corruption.
    """
    _ensure_dirs()
    call_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    if not _acquire_lock(timeout=15):
        return {"success": False, "text": "", "error": "Could not acquire lock (agy busy)",
                "model_used": MODEL_NAMES.get(tier, tier), "call_id": call_id, "conv_id": ""}

    try:
        (SIGNALS_DIR / f"call-{timestamp}-{call_id}.json").write_text(
            json.dumps({"id": call_id, "tier": tier, "prompt": prompt[:200]}, indent=2),
            encoding="utf-8",
        )

        brain_before = _brain_snapshot()
        prev_model = _switch_model(tier)

        try:
            r = subprocess.run(
                ["agy", "--dangerously-skip-permissions", "-p", prompt],
                timeout=timeout, capture_output=True, text=True,
            )

            brain_after = _brain_snapshot()
            new_convs = brain_after - brain_before
            response_text = ""
            conv_id = ""

            if new_convs:
                conv_id = new_convs.pop()
                response_text = _read_transcript(conv_id)

            if not response_text and r.stdout:
                response_text = r.stdout

            success = r.returncode == 0 and bool(response_text)

            result = {
                "success": success,
                "text": response_text,
                "error": r.stderr if not success else None,
                "model_used": MODEL_NAMES.get(tier, tier),
                "call_id": call_id,
                "conv_id": conv_id,
            }

        except subprocess.TimeoutExpired:
            result = {"success": False, "text": "", "error": f"Timeout after {timeout}s",
                      "model_used": MODEL_NAMES.get(tier, tier), "call_id": call_id, "conv_id": ""}
        except FileNotFoundError:
            result = {"success": False, "text": "", "error": "agy binary not found",
                      "model_used": MODEL_NAMES.get(tier, tier), "call_id": call_id, "conv_id": ""}
        except Exception as e:
            result = {"success": False, "text": "", "error": str(e),
                      "model_used": MODEL_NAMES.get(tier, tier), "call_id": call_id, "conv_id": ""}
        finally:
            _restore_model(prev_model)

        report_path = REPORTS_DIR / f"response-{timestamp}-{call_id}.md"
        text_content = result.get("text", "") or "(empty response)"
        error_content = result.get("error") or ""
        report_path.write_text(
            f"# agy Response ({tier})\n\n"
            f"**Call**: {call_id}\n"
            f"**Model**: {MODEL_NAMES.get(tier, tier)}\n"
            f"**Time**: {timestamp}\n\n"
            f"{text_content}\n\n"
            + (f"---\n⚠️ Error: {error_content}\n" if error_content else ""),
            encoding="utf-8",
        )
        result["report_path"] = str(report_path.relative_to(
            Path(__file__).resolve().parent.parent.parent.parent
        ))

        return result

    finally:
        _release_lock()


def bridge_reports(limit: int = 10) -> list[dict]:
    """List recent bridge reports."""
    _ensure_dirs()
    reports = sorted(REPORTS_DIR.glob("response-*.md"), reverse=True)[:limit]
    return [
        {"path": p.name, "time": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
         "size": p.stat().st_size}
        for p in reports
    ]
