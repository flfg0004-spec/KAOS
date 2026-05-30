import re
from datetime import datetime

from lib import git
from lib import index as index_mod
from lib.config import VAULT_ROOT

LOG_PATH = VAULT_ROOT / "wiki" / "log.md"
ARCHIVE_DIR = VAULT_ROOT / "raw" / "archive"


def _parse_entries(text: str) -> list[dict]:
    entries = []
    current = None
    for line in text.split("\n"):
        m = re.match(r"^## \[(\d{4}-\d{2}-\d{2})\] (\S+)(?: \| (.+))?$", line)
        if m:
            if current:
                entries.append(current)
            current = {
                "date": m.group(1),
                "type": m.group(2),
                "summary": m.group(3) or "",
                "lines": [line],
                "age_days": (datetime.now() - datetime.strptime(m.group(1), "%Y-%m-%d")).days,
            }
        elif current:
            current["lines"].append(line)
    if current:
        entries.append(current)
    return entries


def append_log(agent: str, summary: str, pages: list[str]) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pages_str = ", ".join(pages)

    entry = (
        f"\n## [{today}] session | {agent} session completed\n"
        f"- Result: {summary}\n"
        f"- Pages affected: {pages_str}\n"
        f"- Timestamp: {timestamp}\n"
    )
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(entry)


def compress_log(dry_run: bool = False) -> str:
    if not LOG_PATH.exists():
        return "No log.md found."

    text = LOG_PATH.read_text(encoding="utf-8", errors="replace")
    entries = _parse_entries(text)

    changes = []

    archive_entries = [e for e in entries if e["age_days"] > 90]
    if archive_entries:
        archive_path = ARCHIVE_DIR / f"log-{datetime.now().strftime('%Y-%m')}.md"
        archive_lines = ["# Archived Log", f"*Archived: {datetime.now().strftime('%Y-%m-%d %H:%M')}*", ""]
        for e in archive_entries:
            archive_lines.extend(e["lines"])
            archive_lines.append("")
        if not dry_run:
            ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
            archive_path.write_text("\n".join(archive_lines), encoding="utf-8")
        changes.append(f"Archived {len(archive_entries)} entries >90 days to {archive_path.name}")
        entries = [e for e in entries if e not in archive_entries]

    for e in entries:
        if e["age_days"] > 30:
            old_lines = "\n".join(e["lines"])
            line_count = len(e["lines"])
            if line_count > 1:
                e["lines"] = [f"## [{e['date']}] {e['type']} | {e['summary'][:80]}"]
                e["lines"].append(f"  _compressed: was {line_count} lines_")
                changes.append(f"Compressed [{e['date']}] {e['type']} ({e['summary'][:40]}...)")

    keep_full = 20
    full_entries = [e for e in entries if e["age_days"] <= 30]
    compressed_entries = [e for e in entries if e["age_days"] > 30]

    if full_entries:
        full_entries = full_entries[-keep_full:]

    new_text_lines = [text.split("\n")[0]] if text else []
    for e in full_entries + compressed_entries:
        new_text_lines.extend(e["lines"])

    if not dry_run:
        LOG_PATH.write_text("\n".join(new_text_lines) + "\n", encoding="utf-8")

    if not changes:
        return "No log compression needed."

    return f"Log compressed: {'; '.join(changes)}"


def extract_session(agent: str, summary: str, pages: list[str] | None = None) -> str:
    if pages is None:
        pages = []

    append_log(agent, summary, pages)

    index_result = ""
    if pages:
        index_result = index_mod.regenerate()

    compress_result = compress_log()

    if pages:
        try:
            from lib.embeddings import update_many
            embed_result = update_many(pages)
        except Exception:
            embed_result = ""
    else:
        embed_result = ""

    try:
        from lib.pipeline import check_stale
        stale_result = check_stale()
        if stale_result and "STALE" in stale_result:
            from lib.config import VAULT_ROOT
            with open(VAULT_ROOT / "_pipeline" / "log.md", "a") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] WARNING: {stale_result}\n")
    except Exception:
        stale_result = ""

    mnemosyne_result = ""
    if agent and agent.lower() != "mnemosyne":
        try:
            import subprocess
            import sys
            vault = VAULT_ROOT
            script = vault / "_scripts" / "vault.py"
            r = subprocess.run(
                [sys.executable, str(script), "lint"],
                capture_output=True, text=True, cwd=vault, timeout=60,
            )
            if "0 issues" in r.stdout or "0 issues" in r.stderr:
                pass
        except Exception:
            pass

    commit_msg = f"session: {agent} - {summary}"
    commit_result = git.add_and_commit(commit_msg)

    try:
        import subprocess
        import sys
        subprocess.run(
            [sys.executable, str(VAULT_ROOT / "_scripts/vault.py"), "dashboard"],
            capture_output=True, timeout=30,
            cwd=VAULT_ROOT,
        )
    except Exception:
        pass

    results = [
        f"Session extracted for {agent}.",
        "log.md updated.",
    ]
    if index_result:
        results.append(index_result)
    if embed_result:
        results.append(embed_result)
    if compress_result and "No log compression" not in compress_result:
        results.append(compress_result)
    if stale_result and "STALE" in stale_result:
        results.append(f"⚠️ {stale_result}")
    results.append(commit_result)

    feedback_msg = (
        f"\n💬 **Feedback**: ¿Qué tan útil fue esta sesión de {agent}?\n"
        f"   Responde con: /feedback {agent} <rating 1-5> [comentario opcional]\n"
        f"   Ejemplo: `/feedback {agent} 5` o `/feedback {agent} 3 faltó profundidad`"
    )
    results.append(feedback_msg)

    return "\n".join(results)
