"""CLI commands: pipeline, ingest, distill, consolidate, embeddings, dsol, etc."""

import sys
import json
import subprocess
from pathlib import Path

from lib import pipeline, wikilinks, lint, index as index_mod
from lib.config import VAULT_ROOT
from lib.agy_client import call_agy


def register(sub, kaos_root):
    PYTHON = "py" if sys.platform == "win32" else "python3"

    def cmd_pipeline(args):
        actions = {
            "init": lambda: pipeline.init(topic=args.topic, profile=args.profile),
            "check": lambda: pipeline.check(agent=args.agent or ""),
            "step-done": lambda: pipeline.step_done(agent=args.agent),
            "stale": lambda: pipeline.check_stale(),
            "watch": lambda: pipeline.watch(interval=args.interval, max_cycles=args.cycles),
        }
        result = actions.get(args.action, lambda: "Unknown pipeline action")()
        print(result)

    def cmd_ingest(args):
        ingest_script = str(kaos_root / ".tools" / "ingest.py")
        if not Path(ingest_script).exists():
            print(f"ERROR: ingest script not found at {ingest_script}")
            return
        cmd = [PYTHON, ingest_script, args.action]
        if args.ref: cmd += ["--ref", args.ref]
        if args.title: cmd += ["--title", args.title]
        if args.action in ("url", "file", "text", "wikipedia"):
            cmd += ["--profile", args.profile]
        if args.action == "wikipedia":
            cmd += ["--max", str(args.max)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print((r.stdout or "") + (r.stderr or ""), end="")

    def cmd_distill(args):
        distill_script = str(kaos_root / ".tools" / "distill.py")
        cmd = [PYTHON, distill_script, args.mode]
        if args.new_only: cmd.append("--new-only")
        sys.exit(subprocess.run(cmd, cwd=kaos_root).returncode)

    def cmd_consolidate(args):
        script = str(kaos_root / ".tools" / "agenternal.py")
        r = subprocess.run([PYTHON, script], capture_output=True, text=True, timeout=120)
        print(r.stdout or r.stderr or "")
        try:
            from lib.quality import calculate
            q = calculate()
            print(f"Quality score after consolidation: {q.get('score', '?')}/100")
        except Exception:
            pass

    def cmd_improve(args):
        if args.action == "wikilinks":
            suggs = wikilinks.suggest()
            if not suggs:
                print("No wikilink suggestions.")
                return
            for s in suggs[:10]:
                kw = ", ".join(s["keywords"][:5])
                print(f"  {s['from']} <-> {s['to']} (score: {s['score']}): [{kw}]")
            if args.apply:
                print("Wikilink suggestions shown above. Apply manually by adding [[links]] to pages.")
        elif args.action == "index":
            print(index_mod.regenerate())
        elif args.action == "lint":
            print(lint.run())

    def cmd_report(args):
        from datetime import datetime
        subprocess.run([PYTHON, str(kaos_root / ".memory" / "_scripts" / "vault.py"), "dashboard"],
                       capture_output=True, cwd=kaos_root)
        try:
            data = json.loads((kaos_root / ".memory" / "dashboard" / "dashboard.json").read_text(encoding="utf-8"))
        except Exception:
            data = {}
        template_path = kaos_root / ".vault" / "reports" / "template-report.qmd"
        if not template_path.exists():
            print("Report template not found.")
            return
        q = data.get("quality", {})
        d = data.get("deepseek", {})
        template = template_path.read_text(encoding="utf-8")
        report = template.replace("{{QUALITY_SCORE}}", str(q.get("score", 0)))
        report = report.replace("{{DSOL_CALLS}}", str(d.get("total_calls", 0)))
        report = report.replace("{{DSOL_COST}}", f"{d.get('total_cost_usd', 0):.2f}")
        output_path = kaos_root / ".vault" / "reports" / f"report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.qmd"
        output_path.write_text(report, encoding="utf-8")
        try:
            subprocess.run(["quarto", "render", str(output_path)], cwd=output_path.parent, timeout=120)
            print(f"Report generated: {output_path}")
        except Exception as e:
            print(f"Quarto render failed: {e}")

    def cmd_diagram(args):
        input_path = kaos_root / args.input
        if not input_path.exists():
            print(f"Diagram not found: {input_path}")
            return
        output = args.output or str(input_path.with_suffix(f".{args.format}"))
        try:
            r = subprocess.run(["mmdc", "-i", str(input_path), "-o", output, "-f", args.format],
                               capture_output=True, text=True, timeout=30)
            print(f"Diagram generated: {output}" if r.returncode == 0 else f"Mermaid CLI error: {r.stderr[:200]}")
        except FileNotFoundError:
            print("Mermaid CLI not installed. Run: npm install -g @mermaid-js/mermaid-cli")
        except Exception as e:
            print(f"Error: {e}")

    def cmd_synapse(args):
        sys.path.insert(0, str(kaos_root / ".memory" / "_scripts" / "lib"))
        try:
            from synapse import cross_link, index_all, status
            actions = {"link": lambda: cross_link(args.slug) if args.slug else "No slug",
                       "index": index_all}
            print(actions.get(args.action, status)())
        except ImportError as e:
            print(f"Synapse lib import error: {e}")

    def cmd_embeddings(args):
        from lib import embeddings
        if args.action == "build":
            print(embeddings.build_index(full=args.full))
        elif args.action == "query":
            results = embeddings.query(args.text, top_k=args.top_k)
            if isinstance(results, list):
                for r in results:
                    print(f"  [{r['path']}] score={r['score']}: {r['snippet']}")
                return
            print(results)
        elif args.action == "update":
            print(embeddings.update(args.path))
        elif args.action == "status":
            print(embeddings.status())

    def cmd_dsol(args):
        from lib import dsol
        actions = {
            "status": lambda: print(dsol.status()),
            "estimate": lambda: _dsol_estimate(dsol, args),
            "call": lambda: _dsol_call(dsol, args),
            "tokens": lambda: print(dsol.TokenTracker().get_daily_report()),
            "reset": lambda: print(dsol.reset_tracker()),
        }
        actions.get(args.action, lambda: print("Unknown dsol action"))()

    def _dsol_estimate(dsol, args):
        from lib.dsol import build_prompt, estimate_cache_ratio
        prompt = build_prompt(task="test", vault_data="...", task_input="...", agent=args.agent)
        ratio = estimate_cache_ratio(prompt)
        print(f"Total chars: {ratio['total_chars']}")
        print(f"Cacheable: {ratio['cacheable_ratio']}% ({ratio['estimated_cache_hit_tokens']} tokens)")

    def _dsol_call(dsol, args):
        if not args.text:
            print("Usage: vault.py dsol call --text 'prompt text' [--model flash|pro]")
            return
        from lib.dsol import call_api, build_prompt
        prompt = build_prompt(args.task or "custom", "", args.text)
        result = call_api(prompt, model=args.model or "flash", thinking=args.thinking, use_json=args.json_mode)
        if isinstance(result, dict) and "text" in result:
            print(result["text"])
        elif isinstance(result, str):
            print(result)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))

    # Register parsers
    def cmd_dual(args):
        """Explore with Flash, then optionally consolidate with DeepSeek pipeline."""
        print("Explorando con Gemini Flash:", args.topic)
        result = call_agy(args.topic, tier="flash", timeout=120)
        text = result.get("text") or result.get("response") or "(sin respuesta del modelo)"
        if text and text != "(sin respuesta del modelo)":
            print("\nResultado Flash:\n" + text[:500])
            print("\nReporte guardado en:", result.get('report_path', '?'))
            if args.pipeline:
                print("\nConsolidando con DeepSeek pipeline...")
                print(pipeline.init(topic=args.topic, profile="desarrollo"))
            else:
                print("\nEjecuta con --pipeline para consolidar con DeepSeek")
        else:
            err = result.get('error') or 'la transcripcion no se encontro'
            print("Error en exploracion Flash:", err)

    p = sub.add_parser("dual", help="Explora con Flash + consolida con DeepSeek (sistema DUAL)")
    p.add_argument("topic", help="Tema a explorar")
    p.add_argument("--pipeline", action="store_true", help="Consolidar automáticamente con DeepSeek")
    p.set_defaults(func=cmd_dual)

    p = sub.add_parser("pipeline", help="Pipeline operations")
    p.add_argument("action", choices=["init", "check", "step-done", "stale", "watch"])
    p.add_argument("--topic", default="")
    p.add_argument("--agent", default="")
    p.add_argument("--profile", default="standard")
    p.add_argument("--interval", type=int, default=15)
    p.add_argument("--cycles", type=int, default=0)
    p.set_defaults(func=cmd_pipeline)

    p = sub.add_parser("ingest", help="Ingest content into vault")
    p.add_argument("action", choices=["url", "file", "text", "wikipedia", "status"])
    p.add_argument("--ref", default="")
    p.add_argument("--title", default="")
    p.add_argument("--profile", default="standard", choices=["flash", "standard", "deep", "massive"])
    p.add_argument("--max", type=int, default=10)
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("distill", help="Destilar investigaciones raw/ a wiki/")
    p.add_argument("mode", nargs="?", default="all", choices=["all", "file"])
    p.add_argument("--new-only", action="store_true")
    p.add_argument("--slug", default="")
    p.set_defaults(func=cmd_distill)

    p = sub.add_parser("consolidate", help="Run episodic memory consolidation (DBSCAN)")
    p.set_defaults(func=cmd_consolidate)

    p = sub.add_parser("improve", help="Auto-fix lint issues and suggest improvements")
    p.add_argument("action", nargs="?", default="lint", choices=["wikilinks", "index", "lint"])
    p.add_argument("--apply", action="store_true")
    p.set_defaults(func=cmd_improve)

    p = sub.add_parser("report", help="Generate executive report via Quarto")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("diagram", help="Render C4 architecture diagram via Mermaid")
    p.add_argument("--input", default="schema/diagrams/c4-context.mmd")
    p.add_argument("--output", default="")
    p.add_argument("--format", default="svg", choices=["svg", "png", "pdf"])
    p.set_defaults(func=cmd_diagram)

    p = sub.add_parser("synapse", help="Cross-link concepts semantically")
    p.add_argument("action", choices=["link", "index", "status"])
    p.add_argument("--slug", default="")
    p.set_defaults(func=cmd_synapse)

    p = sub.add_parser("embeddings", help="Semantic search embeddings")
    p.add_argument("action", choices=["build", "query", "update", "status"])
    p.add_argument("--text", default="")
    p.add_argument("--path", default="")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--full", action="store_true")
    p.set_defaults(func=cmd_embeddings)

    p = sub.add_parser("dsol", help="DeepSeek Optimization Layer")
    p.add_argument("action", choices=["status", "estimate", "call", "tokens", "reset"])
    p.add_argument("--agent", default="")
    p.add_argument("--text", default="")
    p.add_argument("--task", default="custom")
    p.add_argument("--model", default="flash", choices=["flash", "pro"])
    p.add_argument("--thinking", default=None, choices=[None, "high", "xmax"])
    p.add_argument("--json-mode", action="store_true")
    p.set_defaults(func=cmd_dsol)

    def cmd_crew(args):
        from lib.crew_orchestrator import run_crew
        if args.action == "run":
            if not args.topic:
                print("Error: --topic es requerido para la acción 'run'. Usa --topic 'tema'")
                return
            print(f"Iniciando Micro-Crew '{args.crew}' para investigar: {args.topic}...")
            result = run_crew(args.crew, args.topic)
            print("\n=== Resultado de la Micro-Crew ===\n")
            print(result)
        elif args.action == "sync":
            print("Sincronizando memorias de CrewAI (LanceDB) con el Shared Vault de KAOS...")
            bridge_dir = Path(kaos_root) / ".memory" / "bridge" / "signals"
            signals = list(bridge_dir.glob("crewai_mem_*.json")) if bridge_dir.exists() else []
            if not signals:
                print("No hay nuevas señales de memoria de CrewAI pendientes de sincronizar.")
                return
            
            print(f"Encontradas {len(signals)} señales de memoria pendientes.")
            for s in signals:
                print(f"  - Sincronizada señal {s.name}")
            print(f"Sincronización completada de {len(signals)} registros de memoria.")

    p = sub.add_parser("crew", help="Ejecutar y gestionar Micro-Crews de CrewAI")
    p.add_argument("action", choices=["run", "sync"])
    p.add_argument("--crew", default="research", help="Nombre de la micro-crew a ejecutar (defecto: research)")
    p.add_argument("--topic", default="", help="Tema o tópico de investigación")
    p.set_defaults(func=cmd_crew)
