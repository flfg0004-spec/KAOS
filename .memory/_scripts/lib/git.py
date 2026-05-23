import subprocess
from lib.config import VAULT_ROOT


def add_all() -> None:
    subprocess.run(["git", "add", "-A"], cwd=VAULT_ROOT, check=True, capture_output=True)


def commit(message: str) -> str:
    result = subprocess.run(
        ["git", "commit", "-m", message, "--allow-empty"],
        cwd=VAULT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return f"Committed: {message}"
    return f"Warning: {result.stderr.strip()}"


def status_porcelain() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=VAULT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def add_and_commit(message: str) -> str:
    add_all()
    return commit(message)
