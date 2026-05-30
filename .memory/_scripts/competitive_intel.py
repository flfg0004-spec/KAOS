#!/usr/bin/env python3
"""Competitive Intelligence Pipeline — semi-automated.

Semi-automated pipeline: generates search queries, structures results,
compares competitors, and detects changes vs last report.

Usage:
  py -3 competitive_intel.py init --industry <name> --competitors "X,Y,Z"
  py -3 competitive_intel.py run [--industry <name>]
  py -3 competitive_intel.py report [--industry <name>]
  py -3 competitive_intel.py compare --file <report1.json> --file <report2.json>
  py -3 competitive_intel.py --help
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_HAS_YAML = False
try:
    import yaml
    _HAS_YAML = True
except ImportError:
    yaml = None



BASE = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE / "schema" / "competitive-intel.yaml"
CACHE_DIR = BASE / "cache" / "intel"


def _require_yaml():
    if not _HAS_YAML:
        print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)


def _load_config():
    _require_yaml()
    if not CONFIG_PATH.exists():
        print(f"ERROR: config not found at {CONFIG_PATH}", file=sys.stderr)
        print("Run 'init' first to create configuration.", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not cfg or "industries" not in cfg:
        print("ERROR: invalid config format", file=sys.stderr)
        sys.exit(1)
    return cfg


def _ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def _latest_report(industry):
    indir = CACHE_DIR / industry
    if not indir.exists():
        return None
    reports = sorted(indir.glob("report-*.json"))
    return reports[-1] if reports else None


def _read_report(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _fmt_date():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _cli_help():
    print("""Competitive Intelligence Pipeline — semi-automated

Usage:
  init       Create industry config
    --industry <name>        Industry identifier (e.g. cloud-gpu)
    --competitors "X,Y,Z"    Comma-separated competitor names
    [--topics "a,b,c"]       Optional topics (default: pricing,products,funding)
    [--schedule weekly|monthly]  Default: weekly

  run        Generate search queries (use exa-search MCP tool to fetch)
    [--industry <name>]      Filter to one industry (default: all)

  report     Generate comparison report from stored data
    [--industry <name>]      Filter to one industry (default: all)

  compare    Compare two reports
    --file <path>            First report JSON
    --file <path>            Second report JSON

  --help     Show this message

Examples:
  py -3 competitive_intel.py init --industry cloud-gpu --competitors "Nvidia,AMD,Google Cloud"
  py -3 competitive_intel.py run --industry cloud-gpu
  py -3 competitive_intel.py report --industry cloud-gpu
  py -3 competitive_intel.py compare --file report-2026-01.json --file report-2026-02.json
""")


def cmd_init(args):
    industry = None
    competitors = None
    topics = ["pricing", "new products", "market share", "funding"]
    schedule = "weekly"
    i = 1
    while i < len(args):
        if args[i] == "--industry" and i + 1 < len(args):
            industry = args[i + 1]
            i += 2
        elif args[i] == "--competitors" and i + 1 < len(args):
            competitors = [c.strip() for c in args[i + 1].split(",")]
            i += 2
        elif args[i] == "--topics" and i + 1 < len(args):
            topics = [c.strip() for c in args[i + 1].split(",")]
            i += 2
        elif args[i] == "--schedule" and i + 1 < len(args):
            schedule = args[i + 1]
            i += 2
        else:
            i += 1
    if not industry:
        print("ERROR: --industry is required", file=sys.stderr)
        sys.exit(1)
    if not competitors:
        print("ERROR: --competitors is required", file=sys.stderr)
        sys.exit(1)
    _require_yaml()
    cfg = {"industries": {}}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            existing = yaml.safe_load(f)
            if existing and "industries" in existing:
                cfg = existing
    cfg["industries"][industry] = {
        "competitors": competitors,
        "topics": topics,
        "schedule": schedule,
        "output_dir": f".memory/cache/intel/{industry}/",
    }
    _ensure_dir(CONFIG_PATH.parent)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"✓ Industry '{industry}' initialized with competitors: {', '.join(competitors)}")
    print(f"  Config: {CONFIG_PATH}")
    print(f"  Run 'py -3 competitive_intel.py run --industry {industry}' to generate queries")


SEARCH_QUERY_TEMPLATES = [
    "{competitor} {topic} 2025 2026",
    "{competitor} latest announcements {topic}",
    "{competitor} vs competitors comparison {topic}",
    "{competitor} market position {topic}",
    "{competitor} news funding partnership {topic}",
]


def _generate_queries(industry_cfg):
    queries = []
    for comp in industry_cfg["competitors"]:
        for topic in industry_cfg.get("topics", ["pricing", "products"]):
            for tpl in SEARCH_QUERY_TEMPLATES[:2]:
                q = tpl.format(competitor=comp, topic=topic)
                queries.append({"query": q, "competitor": comp, "topic": topic})
    return queries


def cmd_run(args):
    cfg = _load_config()
    target = None
    for i, a in enumerate(args):
        if a == "--industry" and i + 1 < len(args):
            target = args[i + 1]
    industries = {k: v for k, v in cfg["industries"].items()} if not target else (
        {target: cfg["industries"][target]} if target in cfg["industries"] else {}
    )
    if not industries:
        print(f"ERROR: industry '{target}' not found in config", file=sys.stderr)
        sys.exit(1)
    for ind_name, ind_cfg in industries.items():
        out_dir = BASE / ind_cfg.get("output_dir", f"cache/intel/{ind_name}/")
        _ensure_dir(out_dir)
        queries = _generate_queries(ind_cfg)
        print(f"\n{'='*60}")
        print(f"Industry: {ind_name}")
        print(f"Competitors: {', '.join(ind_cfg['competitors'])}")
        print(f"Generated {len(queries)} search queries")
        print(f"{'='*60}\n")
        for q in queries:
            print(f"  [{q['competitor']}] [{q['topic']}] {q['query']}")
        print()
        results = []
        for q in queries:
            entry = {
                "query": q["query"],
                "competitor": q["competitor"],
                "topic": q["topic"],
                "fetched_at": _fmt_date(),
                "snippets": [],
                "urls": [],
            }
            results.append(entry)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        report_file = out_dir / f"report-{ts}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "industry": ind_name,
                "competitors": ind_cfg["competitors"],
                "generated_at": _fmt_date(),
                "queries_count": len(queries),
                "results": results,
            }, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Report skeleton saved: {report_file}")
        print(f"  ⚡ To fetch results: pass these queries to exa-search MCP tool")
        print()


def cmd_report(args):
    cfg = _load_config()
    target = None
    for i, a in enumerate(args):
        if a == "--industry" and i + 1 < len(args):
            target = args[i + 1]
    industries = {k: v for k, v in cfg["industries"].items()} if not target else (
        {target: cfg["industries"][target]} if target in cfg["industries"] else {}
    )
    if not industries:
        print(f"ERROR: industry '{target}' not found in config", file=sys.stderr)
        sys.exit(1)
    for ind_name, ind_cfg in industries.items():
        latest = _latest_report(ind_name)
        if not latest:
            print(f"  No reports for '{ind_name}'. Run 'run' first.")
            continue
        data = _read_report(latest)
        print(f"\n{'='*60}")
        print(f"Competitive Intelligence Report: {ind_name}")
        print(f"Generated: {data.get('generated_at', 'unknown')}")
        print(f"Competitors: {', '.join(data.get('competitors', []))}")
        print(f"{'='*60}\n")
        results = data.get("results", [])
        if not results:
            print("  No results data available.")
            continue
        comp_data = {}
        for comp in ind_cfg["competitors"]:
            comp_data[comp] = {"mentions": 0, "snippets": [], "topics": set(), "urls": []}
        for r in results:
            comp = r.get("competitor", "unknown")
            if comp not in comp_data:
                comp_data[comp] = {"mentions": 0, "snippets": [], "topics": set(), "urls": []}
            comp_data[comp]["mentions"] += 1
            if r.get("topic"):
                comp_data[comp]["topics"].add(r["topic"])
            for s in r.get("snippets", []):
                if s and len(s) > 10:
                    comp_data[comp]["snippets"].append(s)
            for u in r.get("urls", []):
                if u:
                    comp_data[comp]["urls"].append(u)
        print("### Competitor Overview\n")
        headers = ["Competitor", "Mentions", "Topics Covered", "Insights"]
        rows = []
        for comp in ind_cfg["competitors"]:
            cd = comp_data.get(comp, {})
            topics_str = ", ".join(sorted(cd.get("topics", set()))) or "—"
            snippets = cd.get("snippets", [])
            insight = snippets[0][:120] + "..." if snippets else "No data"
            rows.append((comp, str(cd.get("mentions", 0)), topics_str, insight))
        print(_markdown_table(rows, headers))
        print()
        print("### Detailed Findings\n")
        for comp in ind_cfg["competitors"]:
            cd = comp_data.get(comp, {})
            snippets = cd.get("snippets", [])
            urls = cd.get("urls", [])
            print(f"**{comp}** ({cd.get('mentions', 0)} mentions)\n")
            if snippets:
                for s in snippets[:3]:
                    print(f"- {s[:200]}")
            if urls:
                print(f"  Sources: {', '.join(urls[:3])}")
            print()
        previous = None
        reports_list = sorted((CACHE_DIR / ind_name).glob("report-*.json")) if (CACHE_DIR / ind_name).exists() else []
        if len(reports_list) >= 2:
            prev_report = _read_report(reports_list[-2])
            curr_report = data
            print("### Changes Since Last Report\n")
            changes = _detect_changes(prev_report, curr_report, ind_cfg["competitors"])
            if changes:
                chg_headers = ["Dimension", "Competitor", "Previous", "Current"]
                chg_rows = [(c["dim"], c["comp"], c["prev"], c["curr"]) for c in changes]
                print(_markdown_table(chg_rows, chg_headers))
            else:
                print("  No significant changes detected.")
        print()


def cmd_compare(args):
    files = []
    for i, a in enumerate(args):
        if a == "--file" and i + 1 < len(args):
            files.append(Path(args[i + 1]))
    if len(files) < 2:
        print("ERROR: need at least 2 files. Usage: compare --file a.json --file b.json", file=sys.stderr)
        sys.exit(1)
    report_a = _read_report(files[0])
    report_b = _read_report(files[1])
    industry_a = report_a.get("industry", "unknown")
    industry_b = report_b.get("industry", "unknown")
    competitors = report_a.get("competitors", [])
    if not competitors:
        competitors = report_b.get("competitors", [])
    print(f"\n{'='*60}")
    print(f"Report Comparison")
    print(f"  A: {files[0].name} ({industry_a})")
    print(f"  B: {files[1].name} ({industry_b})")
    print(f"{'='*60}\n")
    a_count = report_a.get("queries_count", 0)
    b_count = report_b.get("queries_count", 0)
    print(f"**Queries:** A={a_count}, B={b_count}")
    print(f"**Generated:** A={report_a.get('generated_at','?')}, B={report_b.get('generated_at','?')}\n")
    changes = _detect_changes(report_a, report_b, competitors)
    if changes:
        print("### Detected Changes\n")
        headers = ["Dimension", "Competitor", "Report A", "Report B"]
        rows = [(c["dim"], c["comp"], c["prev"], c["curr"]) for c in changes]
        print(_markdown_table(rows, headers))
    else:
        print("No significant changes detected between reports.")
    print()
    print("### Query Coverage Comparison\n")
    a_results = {r["query"]: r for r in report_a.get("results", [])}
    b_results = {r["query"]: r for r in report_b.get("results", [])}
    all_queries = set(list(a_results.keys()) + list(b_results.keys()))
    cov_headers = ["Query", "Report A", "Report B"]
    cov_rows = []
    for q in sorted(all_queries):
        a_has = "✓" if q in a_results else "—"
        b_has = "✓" if q in b_results else "—"
        cov_rows.append((q[:80], a_has, b_has))
    print(_markdown_table(cov_rows, cov_headers))
    print()


def _detect_changes(prev, curr, competitors):
    changes = []
    prev_results = {r["query"]: r for r in prev.get("results", [])}
    curr_results = {r["query"]: r for r in curr.get("results", [])}
    for comp in competitors:
        prev_queries = [q for q, r in prev_results.items() if r.get("competitor") == comp]
        curr_queries = [q for q, r in curr_results.items() if r.get("competitor") == comp]
        if len(curr_queries) > len(prev_queries) * 1.5:
            changes.append({
                "dim": "Coverage",
                "comp": comp,
                "prev": f"{len(prev_queries)} queries",
                "curr": f"{len(curr_queries)} queries",
            })
        prev_snippets = sum(len(prev_results[q].get("snippets", [])) for q in prev_queries)
        curr_snippets = sum(len(curr_results[q].get("snippets", [])) for q in curr_queries)
        if curr_snippets > prev_snippets * 2 and prev_snippets > 0:
            changes.append({
                "dim": "Activity Spike",
                "comp": comp,
                "prev": f"{prev_snippets} snippets",
                "curr": f"{curr_snippets} snippets",
            })
    prev_date = prev.get("generated_at", "")
    curr_date = curr.get("generated_at", "")
    if prev_date and curr_date:
        changes.append({
            "dim": "Period",
            "comp": "—",
            "prev": prev_date[:10],
            "curr": curr_date[:10],
        })
    return changes


def _markdown_table(rows, headers):
    if not rows:
        return "_empty_"
    out = []
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    out.append("| " + " | ".join(headers) + " |")
    out.append(sep)
    for r in rows:
        vals = [str(v) if v is not None else "" for v in r]
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        _cli_help()
        return
    cmd = args[0]
    if cmd == "init":
        cmd_init(args)
    elif cmd == "run":
        cmd_run(args)
    elif cmd == "report":
        cmd_report(args)
    elif cmd == "compare":
        cmd_compare(args)
    else:
        print(f"ERROR: unknown command: {cmd}", file=sys.stderr)
        _cli_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
