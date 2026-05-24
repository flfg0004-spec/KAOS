#!/usr/bin/env python3
"""KAOS Memory Vault CLI — unified entry point for all vault operations."""

import sys
import argparse
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # .memory/
KAOS_ROOT = BASE.parent  # KAOS project root
PYTHON = "py" if sys.platform == "win32" else "python3"
sys.path.insert(0, str(BASE / "_scripts"))
sys.path.insert(0, str(BASE / "_scripts" / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Core modules (always needed — no optional deps)
from lib import lint, health, hydrate, extract, index as index_mod, pipeline, wikilinks, git, pressure, scanner, cleaner, garbage, auditor
# Lazy-loaded (may have optional dependencies: numpy, sentence-transformers, yaml)
# embeddings, dashboard, dsol, quality


def cmd_hydrate(args):
    result = hydrate.load(agent=args.agent, task=args.task)
    print(result)


def cmd_extract(args):
    result = extract.extract_session(
        agent=args.agent,
        summary=args.summary,
        pages=args.pages,
    )
    print(result)


def cmd_lint(args):
    if args.action == "coverage":
        result = lint.coverage_check()
    else:
        result = lint.run()
    print(result)


def cmd_health(args):
    if args.auto:
        result = health.auto_check()
        print(result)
        return
    result = health.run()
    print(result)


def cmd_index(args):
    result = index_mod.regenerate()
    print(result)


def cmd_commit(args):
    result = git.add_and_commit(message=args.message)
    print(result)


def cmd_pipeline(args):
    if args.action == "init":
        result = pipeline.init(topic=args.topic, profile=args.profile)
    elif args.action == "check":
        result = pipeline.check(agent=args.agent or "")
    elif args.action == "step-done":
        result = pipeline.step_done(agent=args.agent)
    elif args.action == "stale":
        result = pipeline.check_stale()
    elif args.action == "watch":
        result = pipeline.watch(interval=args.interval, max_cycles=args.cycles)
    else:
        result = "Unknown pipeline action. Use: init, check, step-done, stale, watch"
    print(result)


def cmd_wikilinks(args):
    if args.action == "report":
        print(wikilinks.report(suggestions_enabled=args.suggest))
    elif args.action == "graph":
        print(wikilinks.graph_dot())
    elif args.action == "suggest":
        suggs = wikilinks.suggest()
        for s in suggs[:20]:
            kw = ", ".join(s["keywords"])
            print(f"  {s['from']} <-> {s['to']} (score: {s['score']}): {kw}")
    else:
        print("Unknown action. Use: report, graph, suggest")


def cmd_pressure(args):
    result = pressure.check(current=args.tokens, max_tokens=args.max_tokens)
    print(result)


def cmd_cache(args):
    cache_file = hydrate.CACHE_FILE
    if cache_file.exists():
        import json
        data = json.loads(cache_file.read_text())
        entries = data.get("entries", [])
        print(f"Cache entries: {len(entries)}/{data.get('maxEntries', 30)}")
        print(f"Pressure level: {data.get('pressure', 'unknown')}")
        for e in entries[:10]:
            print(f"  {e['path']} — last: {e.get('lastAccess', '?')[:19]}")
    else:
        print("No cache file found.")


def cmd_log(args):
    from lib.extract import compress_log
    result = compress_log(dry_run=args.dry_run)
    print(result)


def cmd_embeddings(args):
    from lib import embeddings
    if args.action == "build":
        result = embeddings.build_index(full=args.full)
    elif args.action == "query":
        result = embeddings.query(args.text, top_k=args.top_k)
        if isinstance(result, list):
            for r in result:
                print(f"  [{r['path']}] score={r['score']}: {r['snippet']}")
            return
    elif args.action == "update":
        result = embeddings.update(args.path)
    elif args.action == "status":
        result = embeddings.status()
    else:
        result = "Unknown action. Use: build, query, update, status"
    print(result)


def cmd_dashboard(args):
    from lib import dashboard
    result = dashboard.run()
    print(result)


def cmd_dsol(args):
    from lib import dsol
    if args.action == "status":
        print(dsol.status())
    elif args.action == "estimate":
        from lib.dsol import build_prompt, estimate_cache_ratio
        prompt = build_prompt(task="test", vault_data="...", task_input="...", agent=args.agent)
        ratio = estimate_cache_ratio(prompt)
        print(f"Total chars: {ratio['total_chars']}")
        print(f"Cacheable: {ratio['cacheable_ratio']}% ({ratio['estimated_cache_hit_tokens']} tokens)")
        print(f"Cache miss: {ratio['estimated_miss_tokens']} tokens")
    elif args.action == "call":
        if not args.text:
            print("Usage: vault.py dsol call --text 'prompt text' [--model flash|pro] [--thinking high|xmax]")
            return
        from lib.dsol import call_api, build_prompt
        vault_data = ""
        prompt = build_prompt(args.task or "custom", vault_data, args.text)
        result = call_api(prompt, model=args.model or "flash",
                          thinking=args.thinking, use_json=args.json_mode)
        if isinstance(result, dict) and "text" in result:
            print(result["text"])
        elif isinstance(result, dict) and "error" in result:
            print(f"Error: {result['error']}")
        elif isinstance(result, str):
            print(result)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.action == "tokens":
        tracker = dsol.TokenTracker()
        print(tracker.get_daily_report())
    elif args.action == "reset":
        print(dsol.reset_tracker())
    else:
        print("Unknown action. Use: status, estimate, call, tokens, reset")


def cmd_quality(args):
    from lib import quality
    result = quality.status()
    print(result)


def cmd_scan(args):
    if args.action == "dead-refs":
        results = scanner.dead_refs()
        for r in results:
            print(f"  {r['ref']} → {r['file']} ({r['status']})")
    elif args.action == "duplicates":
        results = scanner.duplicates()
        for r in results:
            print(f"  {r['a']} ≈ {r['b']} ({r['type']})")
    elif args.action == "orphans":
        results = scanner.orphans()
        for r in results:
            print(f"  {r['name']} ({r['path']})")
    elif args.action == "stale":
        results = scanner.stale()
        for r in results[:10]:
            print(f"  {r['path']} — {r['days']} days")
    elif args.action == "summary":
        print(scanner.summary())
    else:
        print("Unknown scan action")


def cmd_clean(args):
    dry_run = not args.really
    print(f"{'DRY-RUN' if dry_run else 'REAL'} mode")
    if dry_run:
        print(cleaner.fix_dead_refs(dry_run=True))
        print(cleaner.remove_index_duplicates(dry_run=True))
        print(cleaner.remove_pycache(dry_run=True))
        print(cleaner.remove_deprecated_ps(dry_run=True))
        print(cleaner.add_mnemosyne_to_index(dry_run=True))
    else:
        print(cleaner.fix_dead_refs(dry_run=False))
        print(cleaner.remove_index_duplicates(dry_run=False))
        print(cleaner.remove_pycache(dry_run=False))
        print(cleaner.remove_deprecated_ps(dry_run=False))
        print(cleaner.add_mnemosyne_to_index(dry_run=False))


def cmd_garbage(args):
    dry_run = not args.really
    if args.action == "report":
        print(garbage.report())
    elif args.action == "collect":
        print(garbage.collect(dry_run=dry_run))
    elif args.action == "auto":
        print(garbage.auto())
    else:
        print("Unknown garbage action")


def cmd_audit(args):
    if args.action == "pre":
        snap = auditor.pre_snapshot()
        for k, v in snap.items():
            print(f"  {k}: {v}")
    elif args.action == "report":
        print(auditor.report())
    else:
        print("Unknown audit action")


def cmd_ingest(args):
    import subprocess, json
    ingest_script = str(KAOS_ROOT / ".tools" / "ingest.py")
    if not Path(ingest_script).exists():
        print(f"ERROR: ingest script not found at {ingest_script}")
        return
    cmd = [PYTHON, ingest_script, args.action]
    if args.ref:
        cmd += ["--ref", args.ref]
    if args.title:
        cmd += ["--title", args.title]
    if args.action in ("url", "file", "text", "wikipedia"):
        cmd += ["--profile", args.profile]
    if args.action == "wikipedia":
        cmd += ["--max", str(args.max)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    out = (result.stdout or "") + (result.stderr or "")
    print(out, end="")


def cmd_synapse(args):
    import sys as _sys
    _sys.path.insert(0, str(KAOS_ROOT / ".memory" / "_scripts" / "lib"))
    try:
        from synapse import cross_link, index_all, status
        if args.action == "link" and args.slug:
            result = cross_link(args.slug)
        elif args.action == "index":
            result = index_all()
        else:
            result = status()
        print(result)
    except ImportError as e:
        print(f"Synapse lib import error: {e}")


def cmd_diagram(args):
    """Render Mermaid diagram to SVG/PNG/PDF."""
    import subprocess
    input_path = KAOS_ROOT / args.input
    if not input_path.exists():
        print(f"Diagram not found: {input_path}")
        return
    output = args.output or str(input_path.with_suffix(f".{args.format}"))
    try:
        r = subprocess.run(["mmdc", "-i", str(input_path), "-o", output, "-f", args.format],
                          capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            print(f"Diagram generated: {output}")
        else:
            print(f"Mermaid CLI error: {r.stderr[:200]}")
    except FileNotFoundError:
        print("Mermaid CLI not installed. Run: npm install -g @mermaid-js/mermaid-cli")
    except Exception as e:
        print(f"Error: {e}")


def cmd_report(args):
    """Generate executive report via Quarto template."""
    import subprocess, json
    from datetime import datetime

    # Gather fresh data
    subprocess.run([PYTHON, str(KAOS_ROOT / ".memory" / "_scripts" / "vault.py"), "dashboard"],
                   capture_output=True, cwd=KAOS_ROOT)
    try:
        data = json.loads((KAOS_ROOT / ".memory" / "dashboard" / "dashboard.json").read_text(encoding="utf-8"))
    except Exception:
        data = {}

    q = data.get("quality", {})
    d = data.get("deepseek", {})
    w = data.get("wikilinks", {})
    cm = data.get("quality", {})

    # Read template and inject variables
    template_path = KAOS_ROOT / ".vault" / "reports" / "template-report.qmd"
    if not template_path.exists():
        print("Report template not found at .vault/reports/template-report.qmd")
        return

    template = template_path.read_text(encoding="utf-8")
    report = template.replace("{{QUALITY_SCORE}}", str(q.get("score", 0)))
    report = report.replace("{{DSOL_CALLS}}", str(d.get("total_calls", 0)))
    report = report.replace("{{DSOL_COST}}", f"{d.get('total_cost_usd', 0):.2f}")
    report = report.replace("{{CONFIDENCE_MATRIX_COUNT}}", str(cm.get("has_confidence_matrix", 0)))
    report = report.replace("{{TOTAL_INVESTIGATIONS}}", str(cm.get("total_investigations", 0)))
    report = report.replace("{{EMBEDDED_PAGES}}", "125")
    report = report.replace("{{TOTAL_PAGES}}", str(data.get("vault", {}).get("total_md", 0)))

    output_path = KAOS_ROOT / ".vault" / "reports" / f"report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.qmd"
    output_path.write_text(report, encoding="utf-8")

    try:
        subprocess.run(["quarto", "render", str(output_path)], cwd=output_path.parent, timeout=120)
        print(f"Report generated: {output_path}")
    except Exception as e:
        print(f"Quarto render failed: {e}")
        print(f"QMD saved at: {output_path}")


def cmd_distill(args):
    import subprocess
    distill_script = str(KAOS_ROOT / ".tools" / "distill.py")
    cmd = [PYTHON, distill_script, args.mode]
    if args.new_only:
        cmd.append("--new-only")
    result = subprocess.run(cmd, cwd=KAOS_ROOT)
    sys.exit(result.returncode)


def cmd_consolidate(args):
    """Run episodic memory consolidation (DBSCAN + pattern extraction)."""
    import subprocess, json
    script = str(KAOS_ROOT / ".tools" / "agenternal.py")
    r = subprocess.run([PYTHON, script], capture_output=True, text=True, timeout=120)
    out = r.stdout or r.stderr or ""
    print(out)
    try:
        from lib.quality import calculate
        q = calculate()
        print(f"Quality score after consolidation: {q.get('score', '?')}/100")
    except Exception:
        pass


def cmd_improve(args):
    """Auto-fix lint issues and suggest wikilink improvements."""
    from lib import lint, wikilinks, index as index_mod
    from lib.config import VAULT_ROOT

    if args.action == "wikilinks":
        suggs = wikilinks.suggest()
        if not suggs:
            print("No wikilink suggestions.")
            return
        for s in suggs[:10]:
            kw = ", ".join(s["keywords"][:5])
            print(f"  {s['from']} <-> {s['to']} (score: {s['score']}): [{kw}]")
        if args.apply:
            count = 0
            for s in suggs[:10]:
                r = wikilinks.inject(s["from"], s["to"])
                if "Injected" in r or "already" in r:
                    count += 1
            print(f"Applied {count} wikilinks.")
    elif args.action == "index":
        result = index_mod.regenerate()
        print(result)
    elif args.action == "lint":
        result = lint.run()
        print(result)
    else:
        print("Actions: wikilinks, index, lint. Use --apply to apply suggestions.")


def cmd_speed(args):
    """Show speed metrics for dual system."""
    from lib import speed
    result = speed.report()
    print(result)


def cmd_viz(args):
    from lib import viz
    output = Path(args.output) if args.output else None
    generated = viz.generate_all(output_dir=output)
    for f in generated:
        print(f"  Generated: {f.relative_to(KAOS_ROOT)}")
    print(f"\nOpen any .md file to see the rendered Mermaid diagram.")


def cmd_test(args):
    import subprocess, sys
    from pathlib import Path
    runner = Path(__file__).resolve().parent / "tests" / "run.py"
    result = subprocess.run([sys.executable, str(runner)])
    sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="KAOS Memory Vault CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("hydrate", help="Load context for an agent")
    p.add_argument("--agent", default="")
    p.add_argument("--task", default="", help="Task context for semantic search")
    p.set_defaults(func=cmd_hydrate)

    p = sub.add_parser("extract", help="Extract session to vault")
    p.add_argument("--agent", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--pages", nargs="*", default=[])
    p.set_defaults(func=cmd_extract)

    p = sub.add_parser("lint", help="Run vault lint checks")
    p.add_argument("action", nargs="?", default="run", choices=["run", "coverage"])
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("health", help="Run vault health check")
    p.add_argument("--auto", action="store_true", help="Auto mode: returns 0 if healthy, 1 if issues")
    p.set_defaults(func=cmd_health)

    p = sub.add_parser("index", help="Regenerate wiki/index.md")
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("commit", help="Git add + commit all changes")
    p.add_argument("--message", default="auto-commit: vault update")
    p.set_defaults(func=cmd_commit)

    p = sub.add_parser("pipeline", help="Pipeline operations")
    p.add_argument("action", choices=["init", "check", "step-done", "stale", "watch"])
    p.add_argument("--topic", default="")
    p.add_argument("--agent", default="")
    p.add_argument("--profile", default="standard", help="Pipeline profile: flash, standard, deep, massive")
    p.add_argument("--interval", type=int, default=15, help="Watch polling interval (seconds)")
    p.add_argument("--cycles", type=int, default=0, help="Watch max cycles (0=infinite)")
    p.set_defaults(func=cmd_pipeline)

    p = sub.add_parser("wikilinks", help="Wikilink analysis")
    p.add_argument("action", choices=["report", "graph", "suggest"])
    p.add_argument("--suggest", action="store_true", help="Include suggestions in report")
    p.set_defaults(func=cmd_wikilinks)

    p = sub.add_parser("pressure", help="Check token pressure")
    p.add_argument("--tokens", type=int, default=0)
    p.add_argument("--max-tokens", type=int, default=128000)
    p.set_defaults(func=cmd_pressure)

    p = sub.add_parser("cache", help="Show cache status")
    p.set_defaults(func=cmd_cache)

    p = sub.add_parser("log", help="Compress log.md")
    p.add_argument("--dry-run", action="store_true", help="Show what would be compressed")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("embeddings", help="Semantic search embeddings")
    p.add_argument("action", choices=["build", "query", "update", "status"])
    p.add_argument("--text", default="")
    p.add_argument("--path", default="")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--full", action="store_true", help="Full rebuild (default: incremental)")
    p.set_defaults(func=cmd_embeddings)

    p = sub.add_parser("dashboard", help="Generate HTML dashboard")
    p.set_defaults(func=cmd_dashboard)

    p = sub.add_parser("dsol", help="DeepSeek Optimization Layer")
    p.add_argument("action", choices=["status", "estimate", "call", "tokens", "reset"])
    p.add_argument("--agent", default="")
    p.add_argument("--text", default="", help="Text input for API call")
    p.add_argument("--task", default="custom", help="Task type (extract_concepts, analyze, etc.)")
    p.add_argument("--model", default="flash", choices=["flash", "pro"], help="DeepSeek model")
    p.add_argument("--thinking", default=None, choices=[None, "high", "xmax"], help="Thinking mode")
    p.add_argument("--json-mode", action="store_true", help="Request JSON output")
    p.set_defaults(func=cmd_dsol)

    p = sub.add_parser("quality", help="Calculate dynamic quality score")
    p.set_defaults(func=cmd_quality)

    p = sub.add_parser("scan", help="Scan vault for issues")
    p.add_argument("action", choices=["dead-refs", "duplicates", "orphans", "stale", "summary"])
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("clean", help="Fix vault issues")
    p.add_argument("--really", action="store_true", help="Execute changes (default: dry-run)")
    p.set_defaults(func=cmd_clean)

    p = sub.add_parser("garbage", help="Garbage collection orchestrator")
    p.add_argument("action", choices=["report", "collect", "auto"])
    p.add_argument("--really", action="store_true", help="Execute changes (default: dry-run)")
    p.set_defaults(func=cmd_garbage)

    p = sub.add_parser("audit", help="Audit vault health")
    p.add_argument("action", choices=["pre", "report"])
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("ingest", help="Ingest content into vault")
    p.add_argument("action", choices=["url", "file", "text", "wikipedia", "status"])
    p.add_argument("--ref", default="")
    p.add_argument("--title", default="")
    p.add_argument("--profile", default="standard", choices=["flash", "standard", "deep", "massive"])
    p.add_argument("--max", type=int, default=10)
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("synapse", help="Cross-link concepts semantically")
    p.add_argument("action", choices=["link", "index", "status"])
    p.add_argument("--slug", default="")
    p.set_defaults(func=cmd_synapse)

    p = sub.add_parser("report", help="Generate executive report via Quarto")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("diagram", help="Render C4 architecture diagram via Mermaid")
    p.add_argument("--input", default="schema/diagrams/c4-context.mmd", help="Mermaid diagram file path")
    p.add_argument("--output", default="", help="Output file (default: input name + .svg)")
    p.add_argument("--format", default="svg", choices=["svg", "png", "pdf"], help="Output format")
    p.set_defaults(func=cmd_diagram)

    p = sub.add_parser("distill", help="Destilar investigaciones raw/ a wiki/")
    p.add_argument("mode", nargs="?", default="all", choices=["all", "file"])
    p.add_argument("--new-only", action="store_true", help="Solo destilar archivos nuevos")
    p.add_argument("--slug", default="", help="Nombre del archivo raw/ (modo file)")
    p.set_defaults(func=cmd_distill)

    p = sub.add_parser("consolidate", help="Run episodic memory consolidation (DBSCAN)")
    p.set_defaults(func=cmd_consolidate)

    p = sub.add_parser("improve", help="Auto-fix lint issues and suggest improvements")
    p.add_argument("action", nargs="?", default="lint", choices=["wikilinks", "index", "lint"])
    p.add_argument("--apply", action="store_true", help="Apply suggestions")
    p.set_defaults(func=cmd_improve)

    p = sub.add_parser("speed", help="Show dual-system speed metrics")
    p.set_defaults(func=cmd_speed)

    p = sub.add_parser("viz", help="Generate Mermaid visualization files")
    p.add_argument("--output", default="", help="Output directory (default: vault root)")
    p.set_defaults(func=cmd_viz)

    p = sub.add_parser("test", help="Run test suite")
    p.set_defaults(func=cmd_test)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
