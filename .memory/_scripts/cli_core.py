"""CLI commands: vault core operations (hydrate, extract, lint, health, etc.)."""

import sys
import json
from pathlib import Path

from lib import lint, health, hydrate, extract, index as index_mod, git, pressure, scanner, cleaner, garbage, auditor
from lib import tagger
from lib import crystallize
from lib import gaps
from lib.config import VAULT_ROOT


def register(sub, kaos_root):
    PYTHON = "py" if sys.platform == "win32" else "python3"

    def cmd_hydrate(args):
        result = hydrate.load(agent=args.agent, task=args.task)
        print(result)

    def cmd_extract(args):
        result = extract.extract_session(agent=args.agent, summary=args.summary, pages=args.pages)
        print(result)

    def cmd_lint(args):
        result = lint.coverage_check() if args.action == "coverage" else lint.run()
        print(result)

    def cmd_health(args):
        if args.auto:
            result = health.auto_check()
            print(result)
            return
        result = health.run()
        print(result)

    def cmd_index(args):
        print(index_mod.regenerate())

    def cmd_commit(args):
        print(git.add_and_commit(message=args.message))

    def cmd_pressure(args):
        print(pressure.check(current=args.tokens, max_tokens=args.max_tokens))

    def cmd_cache(args):
        cache_file = hydrate.CACHE_FILE
        if cache_file.exists():
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
        print(compress_log(dry_run=args.dry_run))

    def cmd_scan(args):
        from lib import scanner as sc
        actions = {
            "dead-refs": lambda: [print(f"  {r['ref']} → {r['file']} ({r['status']})") for r in sc.dead_refs()],
            "duplicates": lambda: [print(f"  {r['a']} ≈ {r['b']} ({r['type']})") for r in sc.duplicates()],
            "orphans": lambda: [print(f"  {r['name']} ({r['path']})") for r in sc.orphans()],
            "stale": lambda: [print(f"  {r['path']} — {r['days']} days") for r in sc.stale()[:10]],
            "summary": lambda: print(sc.summary()),
        }
        actions.get(args.action, lambda: print("Unknown scan action"))()

    def cmd_archive(args):
        from lib.cleaner import archive_raw_older_than
        print(archive_raw_older_than(days=args.days, dry_run=not args.really))

    def cmd_clean(args):
        dry_run = not args.really
        print(f"{'DRY-RUN' if dry_run else 'REAL'} mode")
        tasks = [cleaner.fix_dead_refs, cleaner.remove_index_duplicates, cleaner.remove_pycache,
                 cleaner.remove_deprecated_ps, cleaner.add_mnemosyne_to_index]
        for t in tasks:
            print(t(dry_run=True) if dry_run else t(dry_run=False))

    def cmd_garbage(args):
        dry_run = not args.really
        actions = {"report": garbage.report, "collect": lambda: garbage.collect(dry_run=dry_run),
                   "auto": garbage.auto}
        print(actions.get(args.action, lambda: "Unknown garbage action")())

    def cmd_tag(args):
        if args.all:
            results = tagger.tag_all(dry_run=args.dry_run)
        elif args.path:
            results = [tagger.tag_file(args.path, dry_run=args.dry_run)]
        else:
            print("Specify --all or --path")
            return
        for r in results:
            added = r.get("added", [])
            if added:
                print(f"  {r['path']}: +{added}")
            else:
                print(f"  {r['path']}: up-to-date")

    def cmd_dedup(args):
        if args.crystallize:
            results = crystallize.run_dedup(dry_run=args.dry_run, min_confidence=args.min_confidence)
            for r in results:
                if "error" in r:
                    print(f"  ERROR: {r['error']}")
                else:
                    print(f"  Merged: {r['title']} → {r['merged_path']}")
                    if r.get("supersedes"):
                        print(f"  Supersedes: {', '.join(r['supersedes'])}")
        else:
            candidates = crystallize.find_candidates()
            if candidates:
                print(f"  Found {len(candidates)} candidate pairs:")
                for c in candidates[:10]:
                    print(f"    {c['method']} ({c['confidence']}): {Path(c['file_a']).stem} ≈ {Path(c['file_b']).stem}")
            else:
                print("  No duplicate candidates found.")

    def cmd_gaps(args):
        if args.action == "report":
            print(gaps.report(min_confidence=args.min_confidence))
        elif args.action == "suggest":
            detector = gaps.GapDetector()
            for g in detector.suggest_gaps(min_confidence=args.min_confidence):
                print(f"  [{g['type']}] {g.get('missing', g.get('node', g.get('id', '?')))} "
                      f"(conf: {g.get('confidence', '-')})")
                if g.get("reason"):
                    print(f"    {g['reason']}")
                if g.get("suggestion"):
                    print(f"    → {g['suggestion']}")

    def cmd_audit(args):
        actions = {"pre": lambda: [print(f"  {k}: {v}") for k, v in auditor.pre_snapshot().items()],
                   "report": auditor.report}
        print(actions.get(args.action, lambda: "Unknown audit action")())

    # Register parsers
    p = sub.add_parser("hydrate", help="Load context for an agent")
    p.add_argument("--agent", default="")
    p.add_argument("--task", default="")
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
    p.add_argument("--auto", action="store_true")
    p.set_defaults(func=cmd_health)

    p = sub.add_parser("index", help="Regenerate wiki/index.md")
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("commit", help="Git add + commit all changes")
    p.add_argument("--message", default="auto-commit: vault update")
    p.set_defaults(func=cmd_commit)

    p = sub.add_parser("pressure", help="Check token pressure")
    p.add_argument("--tokens", type=int, default=0)
    p.add_argument("--max-tokens", type=int, default=128000)
    p.set_defaults(func=cmd_pressure)

    p = sub.add_parser("cache", help="Show cache status")
    p.set_defaults(func=cmd_cache)

    p = sub.add_parser("log", help="Compress log.md")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("scan", help="Scan vault for issues")
    p.add_argument("action", choices=["dead-refs", "duplicates", "orphans", "stale", "summary"])
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("archive", help="Archive old raw/ files (>30 days)")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--really", action="store_true")
    p.set_defaults(func=cmd_archive)

    p = sub.add_parser("clean", help="Fix vault issues")
    p.add_argument("--really", action="store_true")
    p.set_defaults(func=cmd_clean)

    p = sub.add_parser("garbage", help="Garbage collection orchestrator")
    p.add_argument("action", choices=["report", "collect", "auto"])
    p.add_argument("--really", action="store_true")
    p.set_defaults(func=cmd_garbage)

    p = sub.add_parser("tag", help="Auto-tag notes with LLM + embeddings")
    p.add_argument("--all", action="store_true", help="Tag all untagged notes")
    p.add_argument("--path", default="", help="Tag a specific file")
    p.add_argument("--dry-run", action="store_true", help="Show suggestions without modifying")
    p.set_defaults(func=cmd_tag)

    p = sub.add_parser("dedup", help="Detect and fuse duplicate notes")
    p.add_argument("--crystallize", action="store_true", help="AI merge of duplicates")
    p.add_argument("--dry-run", action="store_true", help="Show candidates without merging")
    p.add_argument("--min-confidence", type=float, default=0.90, help="Minimum confidence threshold")
    p.set_defaults(func=cmd_dedup)

    p = sub.add_parser("gaps", help="Knowledge gap detection")
    p.add_argument("action", choices=["report", "suggest"])
    p.add_argument("--min-confidence", type=float, default=0.2, help="Minimum confidence threshold")
    p.set_defaults(func=cmd_gaps)

    p = sub.add_parser("audit", help="Audit vault health")
    p.add_argument("action", choices=["pre", "report"])
    p.set_defaults(func=cmd_audit)
