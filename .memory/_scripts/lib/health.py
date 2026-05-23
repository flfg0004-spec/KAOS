import subprocess
from pathlib import Path
from datetime import datetime
from lib.config import VAULT_ROOT, IGNORED_PAGES

EXPECTED_DIRS = [
    "wiki/entities", "wiki/concepts", "wiki/sources",
    "raw", "schema", "_scripts", "_pending", "_pipeline",
]

_AUTO_MODE = False


def git_status() -> tuple[bool, str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=VAULT_ROOT, capture_output=True, text=True,
    )
    output = result.stdout.strip()
    if output:
        return False, f"## WARNING: Uncommitted Changes\n\n```\n{output}\n```\n"
    return True, "## OK: Git clean\n\n"


def frontmatter() -> tuple[bool, str]:
    issues = 0
    lines = ["## Frontmatter Validation\n"]
    for f in (VAULT_ROOT / "wiki").rglob("*.md"):
        if f.stem in IGNORED_PAGES:
            continue
        content = f.read_text(encoding="utf-8", errors="replace")
        if not content.startswith("---"):
            rel = f.relative_to(VAULT_ROOT)
            lines.append(f"- WARNING: {rel} missing frontmatter\n")
            issues += 1
    if issues == 0:
        lines.append("- OK: All files have frontmatter\n")
    return issues == 0, "".join(lines)


def directories() -> tuple[bool, str]:
    ok = True
    lines = ["\n## Directory Structure\n"]
    for d in EXPECTED_DIRS:
        full = VAULT_ROOT / d
        if full.exists():
            md_count = len(list(full.rglob("*.md")))
            total_files = len(list(full.iterdir())) if full.is_dir() else 0
            lines.append(f"- OK: {d} ({md_count} .md files, {total_files} total entries)\n")
        else:
            lines.append(f"- ERROR: {d} (missing)\n")
            ok = False
    return ok, "".join(lines)


def run() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# Vault Health Report\n*Generated: {now}*\n"]

    git_ok, git_lines = git_status()
    fm_ok, fm_lines = frontmatter()
    dir_ok, dir_lines = directories()

    lines.append(git_lines)
    lines.append(fm_lines)
    lines.append(dir_lines)

    healthy = git_ok and fm_ok and dir_ok
    lines.append("---\n")
    if healthy:
        lines.append("**Vault health: OK Healthy**\n")
    else:
        lines.append("**Vault health: WARNING Issues found**\n")

    report = "".join(lines)
    report_path = VAULT_ROOT / "schema" / "health-report.md"
    report_path.write_text(report, encoding="utf-8")

    if _AUTO_MODE:
        return "0" if healthy else "1"
    return "Health check complete. Report written to schema/health-report.md"


def auto_check() -> str:
    """Run health check in auto mode. Returns '0' if healthy, '1' if issues found."""
    global _AUTO_MODE
    _AUTO_MODE = True
    result = run()
    _AUTO_MODE = False
    return result
