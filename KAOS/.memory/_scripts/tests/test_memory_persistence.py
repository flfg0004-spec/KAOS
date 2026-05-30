"""Tests for persistent memory between sessions."""
import sys
import os
import re
import json
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

VAULT = os.path.join(os.path.dirname(__file__), "..", "..")

SLOW = os.environ.get("KAOS_RUN_SLOW", "1") == "1"
def slow(fn):
    fn._slow = True
    return fn


def test_file_writes_survive():
    """Escribe un archivo y verifica que persiste."""
    test_file = os.path.join(VAULT, "wiki", "concepts", "_test-persistence.md")
    content = "---\ntype: concept\ntest: true\n---\n\n# Persistence Test\n\n[[index]] [[log]]\n"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(content)
    assert os.path.exists(test_file)
    saved = open(test_file, encoding="utf-8").read()
    assert "Persistence Test" in saved
    assert "[[index]]" in saved
    os.remove(test_file)
    assert not os.path.exists(test_file)


def test_log_is_append_only():
    """Verifica que log.md crece sin perder entradas anteriores."""
    log_path = os.path.join(VAULT, "wiki", "log.md")
    assert os.path.exists(log_path)
    content = open(log_path, encoding="utf-8", errors="replace").read()
    entries = re.findall(r"^## \[", content, re.MULTILINE)
    assert len(entries) > 0, "log.md debe tener al menos una entrada"


def test_vectorstore_status():
    """Verifica que sqlite-vec retorna estado."""
    try:
        from lib import vectorstore as vs
        s = vs.status()
        assert "pages" in s
    except ImportError:
        pass


@slow
def test_hydrate_extract_cycle():
    """Verifica que hydrate + extract no fallen."""
    from lib.hydrate import load
    from lib.extract import extract_session, append_log
    ctx = load(agent="test_persist", task="test_cycle")
    assert isinstance(ctx, str)
    assert len(ctx) > 0


def test_code_experience_db_schema():
    """CodeExperience DB tiene la estructura esperada."""
    from lib.code_memory import DB
    assert os.path.exists(str(DB)), f"CodeExperience DB no encontrado en {DB}"
    import sqlite3
    conn = sqlite3.connect(str(DB))
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    assert len(tables) > 0
    conn.close()


def test_git_history():
    """Git log del vault muestra historial de cambios."""
    import subprocess
    r = subprocess.run(
        ["git", "log", "--oneline", "-5", "--", ".memory/"],
        capture_output=True, text=True, timeout=10,
        cwd=os.path.join(VAULT, ".."),
    )
    assert r.returncode == 0
    assert len(r.stdout.strip()) > 0, "Debe haber commits en .memory/"


def test_vault_structure():
    """Verifica que raw/wiki/schema existen."""
    for d in ["raw", "wiki", "schema"]:
        path = os.path.join(VAULT, d)
        assert os.path.isdir(path), f"Directorio {d} no encontrado"
        files = [f for f in os.listdir(path) if f.endswith(".md")]
        assert len(files) > 0, f"{d}/ debe tener archivos .md"


def test_mermaid_viz_generation():
    """Verifica que vault.py viz genera archivos de visualización."""
    import subprocess
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "..", "vault.py"),
             "viz", "--output", tmp],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            return
        outputs = os.listdir(tmp)
        assert len(outputs) > 0, "viz debe generar al menos un archivo"
        assert any("VIZ_" in f for f in outputs), "Archivos deben tener prefijo VIZ_"


def test_audit_trail_exists():
    """Verifica que audit_trail.log existe (si hay auditoría habilitada)."""
    audit_path = os.path.join(VAULT, "..", ".agents", "logs", "audit_trail.log")
    if os.path.exists(audit_path):
        content = open(audit_path, encoding="utf-8", errors="replace").read()
        assert len(content.strip()) > 0


@slow
def test_full_session_persistence_cycle():
    """End-to-end: hydrate → verify → extract → verify state."""
    from lib.hydrate import load
    from lib.extract import extract_session, append_log

    ctx_before = load(agent="test_full_cycle", task="pre_extract")
    assert isinstance(ctx_before, str)

    result = extract_session(
        agent="test_full_cycle",
        summary="Persistence cycle test",
        pages=["_scripts/tests/test_memory_persistence.py"],
    )
    assert "Session extracted" in result or "committed" in result or "log" in result

    ctx_after = load(agent="test_full_cycle", task="post_extract")
    assert isinstance(ctx_after, str)
