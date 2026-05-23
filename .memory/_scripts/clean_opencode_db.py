#!/usr/bin/env python3
"""Analyze, vacuum, and clean OpenCode's internal SQLite database (opencode.db)."""

import argparse
import datetime
import os
import shutil
import sqlite3
import struct
import sys
from pathlib import Path

# ── platform-agnostic DB path detection ──────────────────────────────
def find_opencode_db() -> Path | None:
    candidates = []
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", ""))
        if base.exists():
            candidates.append(base / "opencode" / "opencode.db")
        # fallback: USERPROFILE\.local\share (some installs)
        user = Path.home()
        candidates.append(user / ".local/share/opencode/opencode.db")
    elif sys.platform == "darwin":
        candidates.append(
            Path.home() / "Library/Application Support/opencode/opencode.db"
        )
    else:  # linux / wsl
        candidates.append(Path.home() / ".local/share/opencode/opencode.db")

    for p in candidates:
        if p.exists():
            return p.resolve()
    return None


# ── helpers ──────────────────────────────────────────────────────────
def ms_to_dt(ts: int) -> str:
    return datetime.datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M")


def fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ── analysis ────────────────────────────────────────────────────────
def analyze(db_path: Path):
    print(f"{'='*60}")
    print(f"  opencode.db analysis")
    print(f"{'='*60}")
    print(f"  Path     : {db_path}")
    print(f"  File size: {fmt_size(db_path.stat().st_size)}")

    wal = db_path.with_suffix(".db-wal")
    shm = db_path.with_suffix(".db-shm")
    if wal.exists():
        print(f"  WAL size : {fmt_size(wal.stat().st_size)}")
    if shm.exists():
        print(f"  SHM size : {fmt_size(shm.stat().st_size)}")

    conn = sqlite3.connect(str(db_path))
    pages = conn.execute("PRAGMA page_count").fetchone()[0]
    page_sz = conn.execute("PRAGMA page_size").fetchone()[0]
    print(f"  Pages    : {pages:,} x {page_sz} B = {fmt_size(pages * page_sz)}")
    conn.execute("PRAGMA schema_version")

    # sessions
    cur = conn.execute("""
        SELECT COUNT(*), MIN(time_created), MAX(time_created)
        FROM session
    """)
    cnt, t_min, t_max = cur.fetchone()
    print(f"\n  Sessions  : {cnt:,}")
    if cnt:
        print(f"  Earliest  : {ms_to_dt(t_min)}")
        print(f"  Latest    : {ms_to_dt(t_max)}")
        days = (t_max - t_min) / 86_400_000
        print(f"  Span      : {days:.0f} days")

    # sessions per project
    cur = conn.execute("""
        SELECT COALESCE(p.name, '(no project)'), COUNT(s.id)
        FROM session s LEFT JOIN project p ON s.project_id = p.id
        GROUP BY s.project_id ORDER BY COUNT(s.id) DESC
    """)
    print(f"\n  Sessions per project:")
    for name, n in cur.fetchall():
        print(f"    {name}: {n}")

    # messages & parts
    cur = conn.execute("""
        SELECT COUNT(*), COALESCE(SUM(LENGTH(data)), 0)
        FROM message
    """)
    msg_cnt, msg_bytes = cur.fetchone()
    cur = conn.execute("""
        SELECT COUNT(*), COALESCE(SUM(LENGTH(data)), 0)
        FROM part
    """)
    part_cnt, part_bytes = cur.fetchone()
    print(f"\n  Messages  : {msg_cnt:,} — {fmt_size(msg_bytes)}")
    print(f"  Parts     : {part_cnt:,} — {fmt_size(part_bytes)}")
    total_data = msg_bytes + part_bytes
    print(f"  Total data: {fmt_size(total_data)}")

    # biggest sessions
    cur = conn.execute("""
        SELECT s.id, COALESCE(p.name, '(none)'),
               COUNT(m.id), COALESCE(SUM(LENGTH(m.data)), 0)
        FROM session s
        LEFT JOIN project p ON s.project_id = p.id
        LEFT JOIN message m ON m.session_id = s.id
        GROUP BY s.id
        ORDER BY SUM(LENGTH(m.data)) DESC
        LIMIT 10
    """)
    print(f"\n  Top-10 largest sessions:")
    for sid, proj, mc, mb in cur.fetchall():
        print(f"    [{proj}] {sid[:12]}… — {mc} msgs, {fmt_size(mb)}")

    # orphan messages (messages whose session no longer exists)
    cur = conn.execute("""
        SELECT COUNT(*), COALESCE(SUM(LENGTH(data)), 0)
        FROM message WHERE session_id NOT IN (SELECT id FROM session)
    """)
    orphan_cnt, orphan_bytes = cur.fetchone()
    if orphan_cnt:
        print(f"\n  ⚠ Orphan messages: {orphan_cnt:,} — {fmt_size(orphan_bytes)}")
    cur = conn.execute("""
        SELECT COUNT(*), COALESCE(SUM(LENGTH(data)), 0)
        FROM part WHERE session_id NOT IN (SELECT id FROM session)
    """)
    op_cnt, op_bytes = cur.fetchone()
    if op_cnt:
        print(f"  ⚠ Orphan parts   : {op_cnt:,} — {fmt_size(op_bytes)}")

    # todos
    cur = conn.execute("SELECT COUNT(*) FROM todo")
    todo_cnt = cur.fetchone()[0]
    if todo_cnt:
        print(f"\n  Todos     : {todo_cnt:,}")

    # VACUUM estimate
    cur = conn.execute("PRAGMA freelist_count")
    free = cur.fetchone()[0]
    total_pages = pages
    pct_free = free / total_pages * 100 if total_pages else 0
    print(f"\n  Freelist  : {free:,} pages ({pct_free:.1f}% free — reclaimable)")
    print(f"  Reclaimable: ~{fmt_size(free * page_sz)}")
    conn.close()


# ── vacuum ──────────────────────────────────────────────────────────
def do_vacuum(db_path: Path, dry_run: bool):
    sz_before = db_path.stat().st_size
    print(f"  Size before: {fmt_size(sz_before)}")
    if dry_run:
        print(f"  [DRY RUN] VACUUM would be executed — ~{fmt_size(sz_before)} to reclaim")
        return

    print(f"  Running VACUUM (may take a while for large DBs)…", end="", flush=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("VACUUM")
    conn.close()
    sz_after = db_path.stat().st_size
    saved = sz_before - sz_after
    print(f" done")
    print(f"  Size after : {fmt_size(sz_after)}")
    print(f"  Reclaimed  : {fmt_size(saved)} ({saved/sz_before*100:.1f}%)")


# ── clean by age ────────────────────────────────────────────────────
def clean_days(db_path: Path, days: int, dry_run: bool):
    cutoff = int(
        (datetime.datetime.now() - datetime.timedelta(days=days)).timestamp() * 1000
    )
    print(f"  Removing sessions older than {days} days (before {ms_to_dt(cutoff)})")

    conn = sqlite3.connect(str(db_path))
    cur = conn.execute(
        "SELECT COUNT(*) FROM session WHERE time_created < ?", (cutoff,)
    )
    to_delete = cur.fetchone()[0]

    if to_delete == 0:
        print(f"  No sessions to remove.")
        conn.close()
        return

    print(f"  Sessions to delete: {to_delete}")
    if dry_run:
        print(f"  [DRY RUN] no changes made")
        conn.close()
        return

    # delete messages, parts, session_messages, todos for these sessions
    ids = conn.execute(
        "SELECT id FROM session WHERE time_created < ?", (cutoff,)
    ).fetchall()
    ids_list = tuple(r[0] for r in ids)

    if not ids_list:
        conn.close()
        return

    placeholders = ",".join("?" * len(ids_list))
    deleted = {}
    for table in ("part", "message", "session_message", "todo"):
        cur = conn.execute(
            f"DELETE FROM {table} WHERE session_id IN ({placeholders})", ids_list
        )
        deleted[table] = cur.rowcount

    cur = conn.execute(
        f"DELETE FROM session WHERE id IN ({placeholders})", ids_list
    )
    deleted["session"] = cur.rowcount

    conn.commit()
    conn.close()

    print(f"  Deleted:")
    for tbl, n in deleted.items():
        print(f"    {tbl}: {n}")


# ── keep only last N sessions per project ───────────────────────────
def clean_last(db_path: Path, keep: int, dry_run: bool):
    print(f"  Keeping only the last {keep} sessions per project")

    conn = sqlite3.connect(str(db_path))
    projects = conn.execute(
        "SELECT DISTINCT COALESCE(project_id, '') FROM session"
    ).fetchall()

    total_delete = 0
    for (proj_id,) in projects:
        proj_name = proj_id or "(no project)"
        # get all session ids ordered by time_created desc
        cur = conn.execute(
            "SELECT id, time_created FROM session WHERE COALESCE(project_id, '') = ? ORDER BY time_created DESC",
            (proj_id,),
        )
        sessions = cur.fetchall()
        if len(sessions) <= keep:
            continue
        to_remove = sessions[keep:]  # keep first N (most recent)
        total_delete += len(to_remove)
        ids = [r[0] for r in to_remove]
        print(f"  [{proj_name}] {len(to_remove)} sessions to delete (keeping latest {keep})")

        if dry_run:
            continue

        placeholders = ",".join("?" * len(ids))
        for table in ("part", "message", "session_message", "todo"):
            conn.execute(
                f"DELETE FROM {table} WHERE session_id IN ({placeholders})", ids
            )
        conn.execute(f"DELETE FROM session WHERE id IN ({placeholders})", ids)

    if total_delete == 0:
        print(f"  All projects already have ≤ {keep} sessions.")
    elif dry_run:
        print(f"\n  [DRY RUN] {total_delete} sessions would be deleted — no changes made")

    if not dry_run and total_delete:
        conn.commit()
        print(f"\n  Deleted {total_delete} sessions total.")

    conn.close()


# ── remove orphan records ──────────────────────────────────────────
def clean_orphans(db_path: Path, dry_run: bool):
    conn = sqlite3.connect(str(db_path))

    for table in ("message", "part"):
        cur = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE session_id NOT IN (SELECT id FROM session)"
        )
        cnt = cur.fetchone()[0]
        if cnt == 0:
            print(f"  No orphan {table}s")
            continue
        print(f"  {cnt} orphan {table}s found")
        if not dry_run:
            conn.execute(
                f"DELETE FROM {table} WHERE session_id NOT IN (SELECT id FROM session)"
            )
            print(f"  Deleted {cnt} orphan {table}s")

    if not dry_run:
        conn.commit()
    conn.close()


# ── main ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Analyze, vacuum, and clean OpenCode's internal database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --analyze
  %(prog)s --vacuum
  %(prog)s --clean-days 30 --dry-run
  %(prog)s --clean-last 10
  %(prog)s --clean-orphans
  %(prog)s --vacuum --clean-days 60
        """,
    )
    parser.add_argument("--path", help="Path to opencode.db (auto-detected if omitted)")
    parser.add_argument("--analyze", action="store_true", help="Show database statistics")
    parser.add_argument("--vacuum", action="store_true", help="Reclaim unused space (VACUUM)")
    parser.add_argument(
        "--clean-days",
        type=int,
        metavar="N",
        help="Delete sessions older than N days",
    )
    parser.add_argument(
        "--clean-last",
        type=int,
        metavar="N",
        help="Keep only the last N sessions per project",
    )
    parser.add_argument(
        "--clean-orphans",
        action="store_true",
        help="Delete messages/parts with no parent session",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    # ── locate DB ─────────────────────────────────────
    if args.path:
        db_path = Path(args.path).resolve()
    else:
        found = find_opencode_db()
        if not found:
            print("ERROR: opencode.db not found.", file=sys.stderr)
            print("  Tried:", file=sys.stderr)
            for c in _candidates():
                print(f"    {c}", file=sys.stderr)
            sys.exit(1)
        db_path = found

    if not db_path.exists():
        print(f"ERROR: {db_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"  Target DB: {db_path}\n")

    # ── backup hint ────────────────────────────────────
    if any([args.clean_days, args.clean_last, args.clean_orphans, args.vacuum]):
        print(f"  💡 Tip: use --dry-run first to preview changes\n")

    # ── run requested commands ─────────────────────────
    ran = False
    if args.analyze or not any([args.clean_days, args.clean_last, args.clean_orphans]):
        analyze(db_path)
        ran = True

    if args.clean_orphans:
        if ran:
            print()
        print(f"{'─'*60}")
        print(f"  Clean orphans")
        print(f"{'─'*60}")
        clean_orphans(db_path, args.dry_run)
        ran = True

    if args.clean_days is not None:
        if ran:
            print()
        print(f"{'─'*60}")
        print(f"  Clean by age (> {args.clean_days} days)")
        print(f"{'─'*60}")
        clean_days(db_path, args.clean_days, args.dry_run)
        ran = True

    if args.clean_last is not None:
        if ran:
            print()
        print(f"{'─'*60}")
        print(f"  Clean by count (keep last {args.clean_last} per project)")
        print(f"{'─'*60}")
        clean_last(db_path, args.clean_last, args.dry_run)
        ran = True

    if args.vacuum:
        if ran:
            print()
        print(f"{'─'*60}")
        print(f"  Vacuum")
        print(f"{'─'*60}")
        do_vacuum(db_path, args.dry_run)
        ran = True

    if not ran:
        parser.print_help()


def _candidates():
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", ""))
        if base.exists():
            yield base / "opencode" / "opencode.db"
        yield Path.home() / ".local/share/opencode/opencode.db"
    elif sys.platform == "darwin":
        yield Path.home() / "Library/Application Support/opencode/opencode.db"
    else:
        yield Path.home() / ".local/share/opencode/opencode.db"


if __name__ == "__main__":
    main()
