"""Fase 1: Data Farming — CodeExperience Stress Test
Genera experiencias de código RELEVANTES para KAOS.
Proyecto borrador de feature futura: sistema de caché inteligente para agents.
"""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".memory" / "_scripts"))
from lib.code_memory import init, status
from lib.kratos_hook import run_and_capture

def run(code, lang="python", desc=""):
    if lang == "python":
        r = run_and_capture(["py", "-3", "-c", code], cwd=str(SCRIPTS))
    elif lang == "shell":
        r = run_and_capture(code, shell=True, cwd=str(SCRIPTS))
    else:
        return
    if r.returncode != 0:
        print(f"  [{lang}] {desc}: exit={r.returncode}")

SCRIPTS = Path(__file__).resolve().parent.parent / ".memory" / "_scripts"

def main():
    init()
    print("="*60)
    print(" DATA FARMING — CodeExperience Stress Test")
    print(" Proyecto: Sistema de Caché Inteligente para Agents")
    print("="*60)
    
    # ─── Python: Errores de Caché ───
    print("\n--- Python: Cache Feature ---")
    run("cache=None; value=cache['key']", "python", "NoneType cache")
    run("cache={}; value=cache['nonexistent']", "python", "KeyError cache miss")
    run("import json; cache={'data':set([1,2,3])}; json.dumps(cache)", "python", "JSON set")
    run("cache={'data':None}; cache['data'].append(1)", "python", "AttributeError None")
    run("import json; json.loads('invalid json')", "python", "JSON parse")
    run("cache=[]; item=cache[0]", "python", "IndexError empty")
    run("from cache_engine import SmartCache", "python", "ImportError")
    run("cache={}; cache.get('key','default','extra')", "python", "TypeError args")
    
    # ─── Python: Pipeline ───
    print("\n--- Python: Pipeline ---")
    run("agents=['aletheia','kosmos',42,'mnemosyne'];[a.upper() for a in agents]", "python", "Int in agent list")
    run("import yaml; yaml.safe_load('invalid: [yaml: broken')", "python", "YAML parse")
    run("c={'steps':10,'timeout':'30s'}; max(0,c['timeout'])", "python", "TypeError config")
    run("results=[1,2,3]; results+=None", "python", "TypeError list+None")
    run("open('/nonexistent/path/file.txt')", "python", "FileNotFoundError")
    run("x = 1/0", "python", "ZeroDivisionError")
    run("import os; os.chdir('/nonexistent')", "python", "FileNotFoundError chdir")
    run("d={}; d['a']['b']", "python", "KeyError nested")
    
    # ─── Shell ───
    print("\n--- Shell ---")
    run("npx nonexistent-pkg --help 2>&1", "shell", "npx not found")
    run("py -3 -c \"import nonexistent_module\"", "shell", "Python import")
    run("curl http://localhost:19999/api/test 2>&1", "shell", "Connection refused")
    run("ls /nonexistent/directory 2>&1", "shell", "ls nonexitent")
    
    # ─── Resultados ───
    s = status()
    print(f"\n{'='*60}")
    print(f" CodeExperience: {s['active']} activas, {s['avg_confidence']} conf, {s['top_language']}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
