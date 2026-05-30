#!/usr/bin/env python3
"""Aether CLI — dashboard and configuration tool for the Aether routing system."""

import argparse
import sys
from pathlib import Path

AETHER_YAML = Path(__file__).resolve().parent.parent.parent / "aether.yaml"


def _rich():
    try:
        from rich.console import Console
        from rich.layout import Layout
        from rich.live import Live
        from rich.panel import Panel
        from rich.progress import BarColumn, Progress, TextColumn
        from rich.table import Table
        return Console, Table, Layout, Panel, Progress, BarColumn, TextColumn, Live
    except ImportError:
        return None


def cmd_status(args):
    R = _rich()
    if R:
        Console, Table, Layout, Panel, Progress, BarColumn, TextColumn, Live = R
        console = Console()
    else:
        console = None

    from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER
    from lib.aether.config_loader import get_config
    from lib.aether.quality_store import QualityStore
    from lib.aether.tracker import EtherTracker

    cfg = get_config(str(AETHER_YAML))
    tracker = EtherTracker()
    stats = tracker.get_stats()
    cb_status = _ETHER_CIRCUIT_BREAKER.get_status()
    qs = QualityStore()
    quality_summary = qs.get_summary() if qs else {}
    budget = tracker.check_budget()
    model_bd = tracker.get_model_breakdown()

    if console:
        layout = Layout()
        layout.split_column(
            Layout(name="top", size=3),
            Layout(name="middle"),
            Layout(name="bottom", size=6),
        )
        layout["middle"].split_row(
            Layout(name="routing"),
            Layout(name="costs"),
        )

        layout["top"].update(Panel(
            f"Aether Dashboard  |  {stats.get('total_calls', 0)} calls  |  "
            f"${stats.get('total_cost_usd', 0):.4f} total  |  "
            f"Budget: {budget.get('status', 'unknown')}",
            style="bold cyan",
        ))

        task_map = cfg.TASK_MODEL_MAP
        t = Table(title="Task \u2192 Model Routing", show_header=True)
        t.add_column("Task", style="cyan")
        t.add_column("Model", style="green")
        t.add_column("Tier", style="yellow")
        for task, rule in sorted(task_map.items()):
            model = rule["model"] if isinstance(rule, dict) else rule[0]["model"]
            tier = rule.get("tier", "") if isinstance(rule, dict) else rule[0].get("tier", "")
            t.add_row(task, model, tier)
        layout["routing"].update(Panel(t))

        cost_table = Table(title="Cost & Traffic by Model")
        cost_table.add_column("Model", style="cyan")
        cost_table.add_column("Calls", style="green")
        cost_table.add_column("Cost", style="yellow")
        cost_table.add_column("Avg Latency", style="magenta")
        for model, data in sorted(model_bd.items()):
            cost_table.add_row(
                model,
                str(data.get("calls", 0)),
                f"${data.get('cost_usd', 0):.4f}",
                f"{data.get('latency_ms', 0):.0f}ms",
            )
        layout["costs"].update(Panel(cost_table))

        layout["bottom"].split_row(
            Layout(name="quality"),
            Layout(name="trends"),
        )

        q_table = Table(title="Quality Scores by Task")
        q_table.add_column("Task", style="cyan")
        q_table.add_column("Model", style="green")
        q_table.add_column("Score", style="yellow")
        for task, data in sorted(quality_summary.get("by_task", {}).items()):
            model = data.get("best_model", "?")
            score = data.get("avg_score", 0)
            color = "green" if score >= 7 else ("yellow" if score >= 4 else "red")
            q_table.add_row(task, model, f"[{color}]{score:.1f}[/{color}]")
        layout["quality"].update(Panel(q_table))

        daily = stats.get("daily_breakdown", {})
        trend_table = Table(title="Last 7 Days Trend")
        trend_table.add_column("Date", style="cyan")
        trend_table.add_column("Calls", style="green")
        trend_table.add_column("Cost", style="yellow")
        for day, data in sorted(daily.items(), reverse=True)[:7]:
            trend_table.add_row(day, str(data.get("calls", 0)), f"${data.get('cost_usd', 0):.4f}")
        layout["trends"].update(Panel(trend_table))

        # Budget alerts panel
        if budget.get("alerts"):
            alert_text = "\n".join(budget["alerts"])
            console.print(Panel(alert_text, title="[bold red]Budget Alerts[/bold red]", style="red"))

        console.print(layout)
    else:
        print("=== Aether Status ===")
        print(f"Calls: {stats.get('total_calls', 0)} | Cost: ${stats.get('total_cost_usd', 0):.4f} | Budget: {budget.get('status', 'unknown')}")
        print(f"\nRouting ({len(cfg.TASK_MODEL_MAP)} tasks):")
        for task, rule in sorted(cfg.TASK_MODEL_MAP.items()):
            model = rule["model"] if isinstance(rule, dict) else rule[0]["model"]
            tier = rule.get("tier", "") if isinstance(rule, dict) else rule[0].get("tier", "")
            print(f"  {task}: {model} ({tier})")
        print("\nTraffic by Model:")
        for model, data in sorted(model_bd.items()):
            print(f"  {model}: {data.get('calls', 0)} calls, ${data.get('cost_usd', 0):.4f}")
        print("\nQuality Scores:")
        for task, data in sorted(quality_summary.get("by_task", {}).items()):
            print(f"  {task}: {data.get('avg_score', 0):.1f} (best: {data.get('best_model', '?')})")
        print("\nTrends (last 7 days):")
        for day, data in sorted(stats.get("daily_breakdown", {}).items(), reverse=True)[:7]:
            print(f"  {day}: {data.get('calls', 0)} calls, ${data.get('cost_usd', 0):.4f}")
        if budget.get("alerts"):
            print(f"\n[ALERTS] {budget['message']}")


def cmd_config(args):
    if AETHER_YAML.exists():
        print(AETHER_YAML.read_text(encoding="utf-8"))
    else:
        print("# aether.yaml not found")


def cmd_routing(args):
    from lib.aether.config_loader import get_config
    cfg = get_config(str(AETHER_YAML))
    R = _rich()
    if R:
        Console, Table, Layout, Panel, Progress, BarColumn, TextColumn, Live = R
        console = Console()
        t = Table(title="Task \u2192 Model Routing", show_header=True)
        t.add_column("Task", style="cyan")
        t.add_column("Model", style="green")
        t.add_column("Thinking", style="yellow")
        t.add_column("Tier", style="magenta")
        for task, rule in sorted(cfg.TASK_MODEL_MAP.items()):
            thinking = str(rule.get("thinking", ""))
            t.add_row(task, rule["model"], thinking, rule.get("tier", ""))
        console.print(t)
    else:
        print(f"{'Task':<20} {'Model':<20} {'Thinking':<10} {'Tier':<10}")
        print("-" * 60)
        for task, rule in sorted(cfg.TASK_MODEL_MAP.items()):
            thinking = str(rule.get("thinking", ""))
            print(f"{task:<20} {rule['model']:<20} {thinking:<10} {rule.get('tier', ''):<10}")


def cmd_costs(args):
    from lib.aether.config_loader import get_config
    from lib.aether.tracker import EtherTracker
    cfg = get_config(str(AETHER_YAML))
    tracker = EtherTracker()
    stats = tracker.get_stats()
    caps = cfg.COST_CAPS
    total = stats.get("total_cost_usd", 0)
    R = _rich()
    if R:
        Console, Table, Layout, Panel, Progress, BarColumn, TextColumn, Live = R
        console = Console()
        cap_table = Table(title="Budget Caps")
        cap_table.add_column("Tier", style="cyan")
        cap_table.add_column("Weekly Cap", style="green")
        cap_table.add_column("Daily Limit", style="yellow")
        for tier, cap in caps.items():
            cap_table.add_row(tier, f"${cap.get('weekly_usd', 0):.2f}", f"{cap.get('daily_calls', 0)} calls")
        console.print(cap_table)
        progress = Progress(TextColumn("[progress.description]{task.description}"), BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"))
        task_total = progress.add_task("[cyan]Total tracked", total=100)
        weekly_cap = sum(c.get("weekly_usd", 0) for c in caps.values())
        pct = min(total / weekly_cap * 100, 100) if weekly_cap else 0
        progress.update(task_total, completed=pct)
        console.print(progress)
        console.print(f"\nTotal tracked cost: [bold green]${total:.4f}[/bold green]")
    else:
        print(f"{'Tier':<10} {'Weekly Cap':<12} {'Daily Limit':<12}")
        print("-" * 34)
        for tier, cap in caps.items():
            print(f"{tier:<10} ${cap.get('weekly_usd', 0):<8.2f} {cap.get('daily_calls', 0):<8} calls")
        print(f"\nTotal tracked cost: ${total:.4f}")


def cmd_serve(args):
    port = args.port or 9090
    print(f"Starting web dashboard on port {port}...")
    import subprocess
    subprocess.run([sys.executable, "-m", "http.server", str(port), "--directory", str(AETHER_YAML.parent)], cwd=AETHER_YAML.parent)


def main():
    parser = argparse.ArgumentParser(description="Aether CLI — routing dashboard and configuration")
    sub = parser.add_subparsers(dest="command")

    p_status = sub.add_parser("status", help="Full routing dashboard")
    p_config = sub.add_parser("config", help="Display current YAML config")
    p_routing = sub.add_parser("routing", help="Task \u2192 Model mapping table")
    p_costs = sub.add_parser("costs", help="Budget status per tier")
    p_serve = sub.add_parser("serve", help="Start web dashboard server")
    p_serve.add_argument("--port", type=int, default=9090, help="Port (default: 9090)")

    args = parser.parse_args()
    if args.command == "status":
        cmd_status(args)
    elif args.command == "config":
        cmd_config(args)
    elif args.command == "routing":
        cmd_routing(args)
    elif args.command == "costs":
        cmd_costs(args)
    elif args.command == "serve":
        cmd_serve(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
