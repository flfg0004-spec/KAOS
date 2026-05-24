"""CLI commands: quality, dashboard, speed, docker, validate, viz, test, wikilinks."""

import sys
import subprocess
from pathlib import Path

from lib import quality, dashboard as dash, speed, viz, wikilinks, docker_health, cross_validator


def register(sub, kaos_root):
    PYTHON = "py" if sys.platform == "win32" else "python3"

    def cmd_quality(args):
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

    def cmd_wikilinks(args):
        if args.action == "report":
            print(wikilinks.report(suggestions_enabled=args.suggest))
        elif args.action == "graph":
            print(wikilinks.graph_dot())
        elif args.action == "suggest":
            for s in wikilinks.suggest()[:20]:
                kw = ", ".join(s["keywords"])
                print(f"  {s['from']} <-> {s['to']} (score: {s['score']}): {kw}")
        else:
            print("Unknown action. Use: report, graph, suggest")

    # Register parsers
    p = sub.add_parser("quality", help="Calculate dynamic quality score")
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

    p = sub.add_parser("wikilinks", help="Wikilink analysis")
    p.add_argument("action", choices=["report", "graph", "suggest"])
    p.add_argument("--suggest", action="store_true")
    p.set_defaults(func=cmd_wikilinks)
