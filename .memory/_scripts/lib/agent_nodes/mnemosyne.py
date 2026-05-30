import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from lib.agent_tools import (
    slugify, load_context, save_context,
    RAW_DIR,
)
from lib.feature_flags import is_enabled
from lib.file_lock import acquire_lock
from lib.config import PHASE_B_WORKERS


def mnemosyne_node(state: dict) -> dict:
    return _mnemosyne_node_impl(state)


def _get_modified_files() -> list:
    try:
        from lib.incremental import get_modified_files
        return get_modified_files()
    except Exception:
        return []


def _mnemosyne_node_impl(state: dict) -> dict:
    topic = state.get("topic", "")
    slug = slugify(topic)
    start_time = time.time()

    results = {
        "tags_added": 0, "wikilinks_added": 0, "duplicates_merged": 0,
        "gaps_detected": 0, "quality_score": 0, "lint_issues": 0,
        "graph_nodes": 0, "graph_edges": 0,
        "crossref_unidirectional": 0,
        "lifecycle_total": 0, "lifecycle_avg_confidence": 0,
        "compress_entries": 0,
        "phases": [], "errors": [],
        "incremental": False, "files_skipped": 0, "files_processed": 0,
    }

    incremental = is_enabled("use_incremental_analysis")
    changed_files = _get_modified_files() if incremental else []

    if incremental and changed_files is not None:
        results["incremental"] = True
        results["files_processed"] = len(changed_files)
        results["files_skipped"] = 0

    has_changes = True
    if incremental:
        total_md = 0
        try:
            exclude = {"cache", "_pending", ".git", "_scripts", "_pipeline", "_archive", "dashboard"}
            vault_root = RAW_DIR.parent
            for f in vault_root.rglob("*.md"):
                if any(part in exclude for part in f.parts):
                    continue
                total_md += 1
        except Exception:
            pass
        results["files_skipped"] = max(0, total_md - len(changed_files)) if total_md else 0
        has_changes = len(changed_files) > 0

    if not incremental or has_changes:
        if not is_enabled("use_enhanced_parallelism"):
            try:
                from lib.lint import run as lint_run
                issues, report_text = lint_run([])
                results["lint_issues"] = len(issues) if isinstance(issues, list) else 0
                results["phases"].append("A:lint")
            except Exception as e:
                results["errors"].append(f"lint: {e}")

            try:
                from lib.tagger import suggest_tags
                tags = suggest_tags(topic)
                if tags:
                    results["tags_added"] = len(tags) if isinstance(tags, list) else 0
                results["phases"].append("A:tagger")
            except Exception as e:
                results["errors"].append(f"tagger: {e}")

    def _run_wikilinks():
        try:
            from lib.wikilinks import suggest
            s = suggest(topic)
            return ("wikilinks", len(s) if isinstance(s, list) else 0)
        except Exception:
            return ("wikilinks", 0)

    def _run_crystallize():
        try:
            from lib.crystallize import find_candidates
            c = find_candidates()
            return ("crystallize", len(c) if isinstance(c, list) else 0)
        except Exception:
            return ("crystallize", 0)

    def _run_lint_worker():
        try:
            from lib.lint import run as lint_run
            issues, _ = lint_run([])
            return ("lint", len(issues) if isinstance(issues, list) else 0)
        except Exception:
            return ("lint", 0)

    def _run_tagger_worker():
        try:
            from lib.tagger import suggest_tags
            t = suggest_tags(topic)
            return ("tagger", len(t) if isinstance(t, list) else 0)
        except Exception:
            return ("tagger", 0)

    def _run_gap_detection():
        try:
            from lib.gaps import GapDetector
            detector = GapDetector()
            gaps = detector.suggest_gaps(min_confidence=0.2)
            gap_descriptions = []
            for g in gaps:
                if isinstance(g, dict):
                    desc = g.get("missing", g.get("node", g.get("members", str(g))))
                    gap_descriptions.append(str(desc))
                else:
                    gap_descriptions.append(str(g))
            return ("gaps", len(gaps), gap_descriptions)
        except Exception:
            return ("gaps", 0, [])

    if is_enabled("use_enhanced_parallelism"):
        with ThreadPoolExecutor(max_workers=PHASE_B_WORKERS) as ex:
            futs = {
                ex.submit(_run_wikilinks): "wikilinks",
                ex.submit(_run_crystallize): "crystallize",
                ex.submit(_run_lint_worker): "lint",
                ex.submit(_run_tagger_worker): "tagger",
            }
            futs[ex.submit(_run_gap_detection)] = "gaps"
            for f in as_completed(futs):
                p = futs[f]
                try:
                    name, val, *extra = f.result(timeout=120)
                    if name == "wikilinks": results["wikilinks_added"] += val
                    elif name == "crystallize": results["duplicates_merged"] += val
                    elif name == "lint": results["lint_issues"] += val
                    elif name == "tagger": results["tags_added"] += val
                    elif name == "gaps":
                        results["gaps_detected"] += val
                        if extra and extra[0]:
                            results.setdefault("gap_details", []).extend(extra[0])
                    results["phases"].append(f"B:{p}")
                except Exception as e:
                    results["errors"].append(f"{p}: {e}")
    else:
        if not incremental or has_changes:
            with ThreadPoolExecutor(max_workers=2) as ex:
                futs = {ex.submit(_run_wikilinks): "wikilinks", ex.submit(_run_crystallize): "crystallize"}
                for f in as_completed(futs):
                    p = futs[f]
                    try:
                        name, val = f.result(timeout=120)
                        if name == "wikilinks": results["wikilinks_added"] += val
                        elif name == "crystallize": results["duplicates_merged"] += val
                        results["phases"].append(f"B:{p}")
                    except Exception as e:
                        results["errors"].append(f"{p}: {e}")

    if not incremental or has_changes:
        if not is_enabled("use_enhanced_parallelism"):
            try:
                from lib.gaps import GapDetector
                detector = GapDetector()
                gaps = detector.suggest_gaps(min_confidence=0.2)
                results["gaps_detected"] = len(gaps)
                results["gap_details"] = [str(g)[:200] for g in gaps] if gaps else []
                results["phases"].append("C:gaps")
            except Exception as e:
                results["errors"].append(f"gaps: {e}")

    skip_heavy = incremental and not has_changes
    if not skip_heavy:
        try:
            from lib.quality import calculate as quality_calc
            quality_data = quality_calc()
            results["quality_score"] = quality_data.get("score", 0) if isinstance(quality_data, dict) else 0
            results["phases"].append("D:quality")
        except Exception as e:
            results["errors"].append(f"quality: {e}")

        try:
            from lib.extract import compress_log
            compress_result = compress_log(dry_run=False)
            if isinstance(compress_result, dict):
                results["compress_entries"] = compress_result.get("entries_compressed", 0)
            results["phases"].append("E:compress")
        except Exception as e:
            results["errors"].append(f"compress: {e}")

        try:
            from lib.index import regenerate as index_regenerate
            index_result = index_regenerate()
            results["phases"].append("F:index")
        except Exception as e:
            results["errors"].append(f"index: {e}")

        try:
            from lib.graph_analysis import VaultGraph
            vg = VaultGraph()
            pr = vg.page_rank(top_k=10)
            results["graph_nodes"] = vg.node_count if hasattr(vg, 'node_count') else vg.graph.number_of_nodes()
            results["graph_edges"] = vg.edge_count if hasattr(vg, 'edge_count') else vg.graph.number_of_edges()
            results["phases"].append("G:graph")
        except Exception as e:
            results["errors"].append(f"graph: {e}")

        try:
            from lib.crossref import verify_bidirectional, suggest_backlinks
            unidirectional = verify_bidirectional()
            backlink_suggestions = suggest_backlinks()
            results["crossref_unidirectional"] = len(unidirectional)
            results["phases"].append("H:crossref")
        except Exception as e:
            results["errors"].append(f"crossref: {e}")

        try:
            from lib.memory_lifecycle import run_evaluate_all, run_promotion
            lifecycle_results = run_evaluate_all(dry_run=False)
            if isinstance(lifecycle_results, list):
                results["lifecycle_total"] = len(lifecycle_results)
                confs = [r.get("confidence", 0) for r in lifecycle_results if isinstance(r, dict)]
                results["lifecycle_avg_confidence"] = round(sum(confs) / max(len(confs), 1), 3) if confs else 0
            promo_actions = run_promotion()
            if promo_actions:
                results["lifecycle_archived"] = len([a for a in promo_actions if a.get("action") == "archived"])
            results["phases"].append("I:lifecycle")
        except Exception as e:
            results["errors"].append(f"lifecycle: {e}")

        try:
            from lib.dashboard import run as dashboard_run
            dashboard_result = dashboard_run()
            results["dashboard_path"] = str(dashboard_result) if dashboard_result else ""
            results["phases"].append("J:dashboard")
        except Exception as e:
            results["errors"].append(f"dashboard: {e}")
    else:
        results["phases"].append("D:quality(skip)")
        results["phases"].append("E:compress(skip)")
        results["phases"].append("F:index(skip)")
        results["phases"].append("G:graph(skip)")
        results["phases"].append("H:crossref(skip)")
        results["phases"].append("I:lifecycle(skip)")
        results["phases"].append("J:dashboard(skip)")

    results["duration_s"] = round(time.time() - start_time, 1)

    inc_line = ""
    if incremental:
        inc_line = f"- Incremental: {results['incremental']}\n- Files processed: {results['files_processed']}\n- Files skipped: {results['files_skipped']}\n"

    report = (
        f"# Mnemosyne Curation Report\n\n## Topic\n{topic}\n\n"
        f"## Duration\n{results['duration_s']}s\n\n## Results\n"
        f"{inc_line}"
        f"- Tags added: {results['tags_added']}\n"
        f"- Wikilinks added: {results['wikilinks_added']}\n"
        f"- Duplicates merged: {results['duplicates_merged']}\n"
        f"- Gaps detected: {results['gaps_detected']}\n"
        f"- Quality score: {results['quality_score']}\n"
        f"- Lint issues: {results['lint_issues']}\n"
        f"- Graph nodes: {results['graph_nodes']}\n"
        f"- Graph edges: {results['graph_edges']}\n"
        f"- Unidirectional links: {results['crossref_unidirectional']}\n"
        f"- Lifecycle entries: {results['lifecycle_total']}\n"
        f"- Lifecycle avg confidence: {results['lifecycle_avg_confidence']}\n"
        f"- Compress entries: {results['compress_entries']}\n"
        f"- Governance allowed: {results.get('governance_allowed', 'N/A')}\n"
        f"- Governance denials: {len(results.get('governance_denials', []))}\n"
        f"- Viz paths: {len(results.get('viz_paths', []))}\n\n"
        f"## Phases\n" + "\n".join(f"- {p}" for p in results["phases"]) + "\n\n"
        f"## Errors\n" + ("\n".join(f"- {e}" for e in results["errors"]) if results["errors"] else "None") + "\n"
    )

    output_path = RAW_DIR / f"{slug}-curation.md"
    with acquire_lock(f"curation-{slug}", "mnemosyne"):
        output_path.write_text(report, encoding="utf-8")

    try:
        from lib.quality.agent import record as kq_record
        kq_record("mnemosyne", report, topic=topic)
    except Exception:
        pass

    try:
        from lib.bridge.feedback_consumer import consume_gap_feedback
        n = consume_gap_feedback()
        if n:
            logger.info("Mnemosyne processed %d gap feedback signals", n)
    except Exception:
        pass

    try:
        from lib.opa_bridge import check_agent
        gov = check_agent("mnemosyne", report)
        results["governance_allowed"] = gov["allowed"]
        results["governance_denials"] = gov.get("denials", [])
    except Exception:
        results["governance_allowed"] = True

    try:
        ctx = load_context()
        ctx["agents"].append("mnemosyne")
        ctx["cross_agent"]["mnemosyne_to_aletheia"] = {
            "gaps_detected": results.get("gaps_detected", 0),
            "gap_details": results.get("gap_details", []),
            "quality_score": results.get("quality_score", 0),
        }
        save_context(ctx)
    except Exception:
        pass

    try:
        from lib.viz_orchestrator import orchestrate
        results["curation_phases"] = "\n".join(results["phases"])
        results["topic"] = topic
        viz_result = orchestrate("mnemosyne", data=results)
        if viz_result.paths:
            results["viz_paths"] = viz_result.paths
    except Exception:
        pass

    return {
        **state,
        "mnemosyne_output": report,
        "mnemosyne_prompt": f"Curation: {topic}",
        "curation_metrics": results,
        "aletheia_pending_gaps": results.get("gaps_detected", 0) > 0,
    }
