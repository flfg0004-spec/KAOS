"""CLI commands: quality, dashboard, speed, docker, validate, viz, test, wikilinks."""

import sys
import json
import subprocess
from pathlib import Path

from lib import quality, dashboard as dash, speed, viz, wikilinks, docker_health, cross_validator
from lib.agy_client import gpt55_status, call_gpt55
from lib.telegram import send as telegram_send


def register(sub, kaos_root):
    PYTHON = "py" if sys.platform == "win32" else "python3"

    def cmd_quality(args):
        if args.trend:
            t = quality.trend(days=args.trend_days)
            if "error" in t:
                print(t["error"])
            else:
                print(f"Trend ({t['days']}d, {t['data_points']} pts): {t['direction']} {t['delta']:+.1f}")
                print(f"  First: {t['first_score']:.1f} → Last: {t['last_score']:.1f}")
                for s in t.get("series", []):
                    print(f"  {s['date']}: {s['score']:.1f}")
        else:
            print(quality.status())

    def cmd_dashboard(args):
        print(dash.run())

    def cmd_speed(args):
        print(speed.report())

    def cmd_docker(args):
        print(docker_health.report())

    def cmd_validate(args):
        print(cross_validator.run(args.path, args.profile))

    def cmd_viz(args):
        output = Path(args.output) if args.output else None
        generated = viz.generate_all(output_dir=output)
        for f in generated:
            print(f"  Generated: {f.relative_to(kaos_root)}")
        print(f"\nOpen any .md file to see the rendered Mermaid diagram.")

    def cmd_test(args):
        runner = Path(__file__).resolve().parent / "tests" / "run.py"
        sys.exit(subprocess.run([sys.executable, str(runner)]).returncode)

    def cmd_graph(args):
        vg = graph_analysis.VaultGraph()
        if args.action == "report":
            s = vg.summary()
            print(f"  Nodes: {s['nodes']}, Edges: {s['edges']}, Density: {s['density']}")
            print(f"  Avg PageRank: {s['avg_page_rank']}, Communities: {s['communities']}")
            print(f"  Islands: {s['islands']}, Bridges: {s['bridges']}")
            print(f"  Info sinks: {s['info_sinks']}, Source orphans: {s['source_orphans']}")
            print(f"  Link ratio: {s['link_ratio']}")
        elif args.action == "hubs":
            for h in vg.hub_scores(top_k=args.top_k):
                print(f"  {h['node']}: {h['score']} (out: {h['out_degree']})")
        elif args.action == "bridges":
            for b in vg.bridge_notes():
                print(f"  {b['node']}: betweenness={b['betweenness']}, cross={b['cross_out']}/{b['cross_in']}")
        elif args.action == "clusters":
            for c in vg.louvain_communities()[:10]:
                print(f"  Community {c['id']}: {c['size']} members, density={c['density']}")
                for m in c['members'][:10]:
                    print(f"    - {m}")
        elif args.action == "islands":
            for i in vg.cluster_islands():
                print(f"  Island: {i['size']} nodes, {i['edges']} edges, density={i['density']}")
                for m in i['members'][:10]:
                    print(f"    - {m}")
        elif args.action == "dot":
            from lib.wikilinks import graph_dot
            print(graph_dot())

    def cmd_wikilinks(args):
        if args.action == "report":
            print(wikilinks.report(suggestions_enabled=args.suggest))
        elif args.action == "graph":
            print(wikilinks.graph_dot())
        elif args.action == "suggest":
            mode = args.mode or "hybrid"
            min_conf = args.min_confidence or 0.75
            for s in wikilinks.suggest(min_confidence=min_conf, mode=mode, top_k=20):
                rel = s.get("relation", "")
                rel_str = f" ({rel})" if rel else ""
                anchor = s.get("anchor_text", "")
                anchor_str = f" anchor='{anchor}'" if anchor else ""
                print(f"  {s['from']} <-> {s['to']} (score: {s['score']}, method: {s['method']}){rel_str}{anchor_str}")
        else:
            print("Unknown action. Use: report, graph, suggest")

    # Register parsers
    p = sub.add_parser("quality", help="Calculate dynamic quality score (F7)")
    p.add_argument("--trend", action="store_true", help="Show quality trend over time")
    p.add_argument("--trend-days", type=int, default=7, help="Days for trend calculation")
    p.set_defaults(func=cmd_quality)

    p = sub.add_parser("dashboard", help="Generate HTML dashboard")
    p.set_defaults(func=cmd_dashboard)

    p = sub.add_parser("speed", help="Show dual-system speed metrics")
    p.set_defaults(func=cmd_speed)

    p = sub.add_parser("docker", help="Check Docker service health")
    p.set_defaults(func=cmd_docker)

    p = sub.add_parser("validate", help="Cross-validate output with Gemini Flash")
    p.add_argument("--path", default="")
    p.add_argument("--profile", default="desarrollo", choices=["desarrollo", "produccion", "auditoria"])
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("viz", help="Generate Mermaid visualization files")
    p.add_argument("--output", default="")
    p.set_defaults(func=cmd_viz)

    p = sub.add_parser("test", help="Run test suite")
    p.set_defaults(func=cmd_test)

    p = sub.add_parser("graph", help="Topological graph analysis")
    p.add_argument("action", choices=["report", "hubs", "bridges", "clusters", "islands", "dot"])
    p.add_argument("--top-k", type=int, default=10)
    p.set_defaults(func=cmd_graph)

    def cmd_models(args):
        """Show available models and their status."""
        models_info = {
            "flash": {"model": "Gemini 3.5 Flash", "cost": "$0", "limit": "Ilimitado"},
            "sonnet": {"model": "Claude Sonnet 4.6", "cost": "Pago", "limit": "Ilimitado"},
            "opus": {"model": "Claude Opus 4.6", "cost": "Pago", "limit": "Ilimitado"},
            "gpt55": {"model": "GPT-5.5", "cost": "$20/mes (Plus)", "limit": "150/3h"},
            "gpt55_thinking": {"model": "GPT-5.5 Thinking", "cost": "$20/mes (Plus)", "limit": "3000/sem"},
        }
        print("# Modelos Disponibles\n")
        print(f"{'Tool':<25} {'Modelo':<30} {'Costo':<20} {'Límite'}")
        print("-" * 90)
        for tool, info in models_info.items():
            print(f"agy_ask_{tool:<18} {info['model']:<30} {info['cost']:<20} {info['limit']}")

        print("\n## GPT-5.5 Bridge Status\n")
        status = gpt55_status()
        print(f"Bridge online: {status.get('bridge_online', False)}")
        print(f"Rate limit: {status.get('rate_limit_msg', 'unknown')}")
        print(f"Calls this window: {status.get('calls_this_window', 0)}/{status.get('max_per_window', 150)}")
        if not status.get('bridge_online'):
            print("\nPara activar GPT-5.5:")
            print("1. pip install kitty-bridge")
            print("2. kitty auth openai  (abre browser para OAuth)")
            print("3. kitty bridge --port 8080 --profile plus")

    p = sub.add_parser("models", help="Show available models and status")
    p.set_defaults(func=cmd_models)

    def cmd_notify(args):
        """Send a notification to Telegram."""
        ok = telegram_send(args.message)
        print("Notificacion enviada" if ok else "Error: TELEGRAM_BOT_TOKEN no configurado")

    p = sub.add_parser("notify", help="Send notification to Telegram")
    p.add_argument("message", help="Message text to send")
    p.set_defaults(func=cmd_notify)

    p = sub.add_parser("wikilinks", help="Wikilink analysis")
    p.add_argument("action", choices=["report", "graph", "suggest"])
    p.add_argument("--suggest", action="store_true")
    p.add_argument("--mode", choices=["embedding", "llm", "hybrid"], default="hybrid",
                   help="Suggestion mode (default: hybrid)")
    p.add_argument("--min-confidence", type=float, default=0.75,
                   help="Minimum similarity threshold (0-1)")
    p.set_defaults(func=cmd_wikilinks)
