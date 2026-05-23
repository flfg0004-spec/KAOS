"""Garbage orchestrator: scan → clean → report."""

from lib import scanner, cleaner, lint as lint_mod


def report() -> str:
    return scanner.summary()


def collect(dry_run: bool = True) -> str:
    steps = []
    steps.append(cleaner.fix_dead_refs(dry_run))
    steps.append(cleaner.remove_index_duplicates(dry_run))
    steps.append(cleaner.remove_pycache(dry_run))
    steps.append(cleaner.remove_deprecated_ps(dry_run))
    steps.append(cleaner.add_mnemosyne_to_index(dry_run))
    steps.append(lint_mod.run())
    return "\n".join(steps)


def auto(dry_run: bool = True) -> str:
    """Lightweight auto-clean: removes pycache and stale lint artifacts."""
    from lib.cleaner import remove_pycache
    from lib.lint import run as lint_run
    steps = []
    steps.append(remove_pycache(dry_run=dry_run))
    steps.append(lint_run())
    return "\n".join(steps)
