"""System Scanner — inspecciona 10 subsistemas de KAOS, produce health report."""
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent  # KAOS root
MEMORY = ROOT / ".memory"
SCRIPTS = MEMORY / "_scripts"
CACHE = MEMORY / "cache"
TOOLS = ROOT / ".tools"
OPCODE = ROOT / ".opencode"
SKILLS = OPCODE / "skills"

os.environ["PYTHONIOENCODING"] = "utf-8"

def _try(fn, default=None):
    try:
        return fn()
    except Exception as e:
        return {"error": str(e)} if default is None else default

def scan_opencode() -> dict:
    """Scan opencode.json config."""
    path = OPCODE / "opencode.json"
    if not path.exists():
        return {"error": "opencode.json not found"}
    data = json.loads(path.read_text(encoding="utf-8"))
    agents = data.get("agent", {})
    mcps = data.get("mcp", {})
    active = sum(1 for v in mcps.values() if v.get("disabled") is not True)
    disabled = [k for k, v in mcps.items() if v.get("disabled") is True]
    return {
        "agents": {k: {"steps": v.get("steps", "?"), "temp": v.get("temperature", "?"), "tools": len(v.get("tools", {}))} for k, v in agents.items()},
        "mcps": {"total": len(mcps), "active": active, "disabled": disabled},
        "tools_defined": len(data.get("tools", {})),
    }

def scan_skills() -> dict:
    """Scan all agent skills."""
    skills = list(SKILLS.glob("*/SKILL.md"))
    return {
        "total": len(skills),
        "files": {s.parent.name: {"lines": len(s.read_text(encoding="utf-8").splitlines())} for s in skills},
    }

def scan_tools() -> dict:
    """Scan tool scripts."""
    tools = list(TOOLS.glob("*.py"))
    return {
        "total": len(tools),
        "largest": sorted([{"name": t.name, "kb": round(t.stat().st_size / 1024, 1)} for t in tools], key=lambda x: -x["kb"])[:5],
    }

def scan_libraries() -> dict:
    """Scan library modules."""
    libs = list((SCRIPTS / "lib").glob("*.py"))
    total_loc = sum(len(l.read_text(encoding="utf-8").splitlines()) for l in libs)
    return {"total_modules": len(libs), "total_loc": total_loc}

def scan_vectorstore() -> dict:
    """Scan vector store."""
    db = CACHE / "vectors.db"
    if not db.exists():
        return {"error": "vectors.db not found", "size_kb": 0}
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.enable_load_extension(True)
    try:
        import sqlite_vec
        sqlite_vec.load(conn)
    except ImportError:
        pass
    conn.enable_load_extension(False)
    pages = conn.execute("SELECT COUNT(DISTINCT path) FROM vault_chunks").fetchone()[0]
    chunks = conn.execute("SELECT COUNT(*) FROM vault_chunks").fetchone()[0]
    conn.close()
    return {"pages": pages, "chunks": chunks, "size_kb": round(db.stat().st_size / 1024, 1)}

def scan_codeexperience() -> dict:
    """Scan CodeExperience DB."""
    db = CACHE / "code_experiences.db"
    if not db.exists() or db.stat().st_size == 0:
        return {"error": "code_experiences.db not found or empty", "entries": 0}
    conn = sqlite3.connect(str(db))
    try:
        total = conn.execute("SELECT COUNT(*) FROM code_experiences").fetchone()[0]
        ast = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE ast_signature IS NOT NULL").fetchone()[0]
        conf = conn.execute("SELECT AVG(confidence) FROM code_experiences").fetchone()[0]
    except Exception:
        conn.close()
        return {"error": "table not found", "entries": 0}
    conn.close()
    return {"entries": total, "ast_signatures": ast, "avg_confidence": round(conf, 3) if conf else 0}

def scan_knowledgegraph() -> dict:
    """Scan knowledge graph."""
    kg = MEMORY / "cache" / "knowledge-graph"
    seed = kg / "seed.json"
    if not seed.exists():
        return {"error": "seed.json not found"}
    data = json.loads(seed.read_text(encoding="utf-8"))
    return {"entities": len(data.get("entities", [])), "relations": len(data.get("relations", []))}

def scan_pipeline() -> dict:
    """Scan LangGraph pipeline status."""
    try:
        sys.path.insert(0, str(SCRIPTS))
        from lib.orchestrator import build_graph
        g = build_graph(with_parallel=False)
        g2 = build_graph(with_parallel=True)
        nodes = list(g.nodes.keys())
        return {
            "langgraph_active": True,
            "nodes_sequential": nodes,
            "nodes_parallel": list(g2.nodes.keys()),
            "has_hitl": True,
            "has_parallel": True,
        }
    except Exception as e:
        return {"langgraph_active": False, "error": str(e)}

def scan_hermes() -> dict:
    """Scan Hermes status (nativo Windows)."""
    import json
    import urllib.request

    try:
        r = subprocess.run(["hermes", "--version"], capture_output=True, text=True, timeout=5)
        version = r.stdout.strip() if r.returncode == 0 else "no hermes"
    except FileNotFoundError:
        return {"status": "inactive", "version": "not installed", "error": "hermes binary not found"}
    except Exception as e:
        return {"status": "unknown", "version": "?", "error": str(e)}

    gateway_status = "inactive"
    try:
        req = urllib.request.Request("http://127.0.0.1:8642/health", method="GET")
        resp = urllib.request.urlopen(req, timeout=3)
        if resp.status == 200:
            body = json.loads(resp.read().decode())
            gateway_status = body.get("status", "ok")
        else:
            gateway_status = f"http_{resp.status}"
    except Exception:
        gateway_status = "inactive"

    return {
        "status": "active" if gateway_status in ("ok", "healthy", None) else gateway_status,
        "version": version,
        "gateway": gateway_status,
    }

def scan_scheduler() -> dict:
    """Scan Windows scheduled tasks."""
    try:
        r = subprocess.run(
            ["schtasks", "/query", "/fo", "LIST", "/v", "/nh"],
            capture_output=True, text=True, timeout=15
        )
        kaos_tasks = [l.strip() for l in r.stdout.split("\n") if "KAOS" in l]
        return {"kaos_tasks": len(kaos_tasks), "task_names": kaos_tasks[:5]}
    except Exception:
        return {"kaos_tasks": 0, "error": "schtasks not available"}

def scan_git() -> dict:
    """Scan git status."""
    try:
        r = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True, text=True, cwd=str(ROOT), timeout=10)
        recent = r.stdout.strip().split("\n")
        r2 = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=str(ROOT), timeout=10)
        changes = [l for l in r2.stdout.split("\n") if l.strip()]
        return {"recent_commits": recent[:5], "uncommitted_files": len(changes)}
    except Exception as e:
        return {"error": str(e)}

def scan_sessions() -> dict:
    """Scan saved session scores."""
    sessions = list(TOOLS.glob("session-*.json"))
    scores = []
    for s in sorted(sessions, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
        try:
            data = json.loads(s.read_text(encoding="utf-8"))
            scores.append({"name": s.stem, "composite": data.get("composite", "?")})
        except Exception:
            pass
    return {"total": len(sessions), "recent_scores": scores}


def scan() -> dict:
    """Full system scan — returns health report dict."""
    return {
        "opencode": _try(scan_opencode),
        "skills": _try(scan_skills),
        "tools": _try(scan_tools),
        "libraries": _try(scan_libraries),
        "vectorstore": _try(scan_vectorstore),
        "code_experience": _try(scan_codeexperience),
        "knowledge_graph": _try(scan_knowledgegraph),
        "pipeline": _try(scan_pipeline),
        "hermes": _try(scan_hermes),
        "scheduler": _try(scan_scheduler),
        "git": _try(scan_git),
        "sessions": _try(scan_sessions),
    }

def health_score(report: dict) -> float:
    """Compute composite health score from scan report."""
    scores = []
    weights = {
        "opencode": 0.10, "skills": 0.05, "tools": 0.05,
        "libraries": 0.05, "vectorstore": 0.15, "code_experience": 0.10,
        "knowledge_graph": 0.05, "pipeline": 0.15, "hermes": 0.10,
        "scheduler": 0.05, "git": 0.05, "sessions": 0.10,
    }
    for key, weight in weights.items():
        data = report.get(key, {})
        if isinstance(data, dict):
            if "error" in data:
                scores.append(0.0 * weight)
            elif key == "vectorstore":
                chunks = data.get("chunks", 0)
                scores.append(min(1.0, chunks / 5000) * weight)
            elif key == "code_experience":
                entries = data.get("entries", 0)
                scores.append(min(1.0, entries / 100) * weight)
            elif key == "pipeline":
                scores.append((1.0 if data.get("langgraph_active") else 0.0) * weight)
            elif key == "hermes":
                scores.append((1.0 if data.get("status") == "active" else 0.3) * weight)
            elif key == "opencode":
                agents = len(data.get("agents", {}))
                scores.append(min(1.0, agents / 5) * weight)
            else:
                scores.append(0.8 * weight)
    return round(sum(scores) * 100, 1)


if __name__ == "__main__":
    report = scan()
    print(json.dumps(report, indent=2, default=str))
    print(f"\nHealth Score: {health_score(report)}/100")
