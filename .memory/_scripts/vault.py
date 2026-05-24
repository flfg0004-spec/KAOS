#!/usr/bin/env python3
"""KAOS Memory Vault CLI — unified entry point.

Delegates to domain modules:
- cli_core: hydrate, extract, lint, health, index, commit, pressure, cache, log, scan, archive, clean, garbage, audit
- cli_pipeline: pipeline, ingest, distill, consolidate, improve, report, diagram, synapse, embeddings, dsol
- cli_quality: quality, dashboard, speed, docker, validate, viz, test, wikilinks
"""

import sys
import argparse
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # .memory/
KAOS_ROOT = BASE.parent  # KAOS project root
sys.path.insert(0, str(BASE / "_scripts"))
sys.path.insert(0, str(BASE / "_scripts" / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cli_core import register as register_core
from cli_pipeline import register as register_pipeline
from cli_quality import register as register_quality


def main():
    parser = argparse.ArgumentParser(description="KAOS Memory Vault CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    register_core(sub, KAOS_ROOT)
    register_pipeline(sub, KAOS_ROOT)
    register_quality(sub, KAOS_ROOT)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
