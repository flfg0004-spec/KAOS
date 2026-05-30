import argparse
import hashlib
import json
import logging
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_VECTORSTORE = None


def _get_vectorstore():
    global _VECTORSTORE
    if _VECTORSTORE is None:
        try:
            from lib.strategy_vectorstore import hybrid_search, embed_strategy
            _VECTORSTORE = {
                "hybrid_search": hybrid_search,
                "embed_strategy": embed_strategy,
            }
        except Exception as e:
            logger.warning("Vectorstore unavailable: %s", e)
            _VECTORSTORE = False
    return _VECTORSTORE


STOPWORDS = {
    "el", "la", "los", "las", "de", "del", "en", "un", "una", "y", "e", "o",
    "a", "que", "es", "por", "para", "con", "al", "lo", "su", "como", "más",
    "pero", "sus", "le", "ya", "este", "entre", "porque", "todo", "esta",
    "muy", "sin", "hay", "también", "the", "a", "an", "and", "or", "of",
    "to", "in", "is", "it", "for", "on", "that", "this", "with", "be", "are",
    "was", "were", "been", "have", "has", "had", "not", "but", "what",
    "which", "who", "how", "when", "where", "why",
}

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "strategy_memory.db"


class StrategicMemoryBank:
    def __init__(self, db_path: str | Path = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self._conn = None

    def _get_conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._init_db()
        return self._conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                plan_type TEXT NOT NULL,
                context_hash TEXT NOT NULL,
                context_json TEXT NOT NULL,
                content_json TEXT NOT NULL,
                outcome_score REAL DEFAULT NULL,
                feedback TEXT DEFAULT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_type TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                description TEXT NOT NULL,
                total_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_strategies_context_hash "
            "ON strategies(context_hash)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_strategies_plan_type ON strategies(plan_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_patterns_plan_type ON patterns(plan_type)")
        conn.commit()

    @staticmethod
    def _hash_context(context: dict) -> str:
        serialized = json.dumps(context, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def _normalize_text(self, text: str) -> str:
        tokens = re.findall(r"[a-záéíóúñ0-9]{4,}", text.lower())
        return " ".join(t for t in tokens if t not in STOPWORDS)

    def _text_signature(self, text: str, shingle_size: int = 1) -> set:
        normalized = self._normalize_text(text)
        words = normalized.split()
        if len(words) < shingle_size:
            return set(words)
        return set(" ".join(words[i:i+shingle_size]) for i in range(len(words) - shingle_size + 1))

    def _context_to_signature(self, context: dict) -> set:
        text = json.dumps(context, sort_keys=True, ensure_ascii=False)
        return self._text_signature(text)

    def semantic_similarity(self, sig_a: set, sig_b: set) -> float:
        if not sig_a or not sig_b:
            return 0.0
        intersection = sig_a & sig_b
        union = sig_a | sig_b
        return len(intersection) / len(union) if union else 0.0

    def store(
        self, context: dict, content: dict, plan_type: str,
        outcome_score: float = None, feedback: str = None,
    ) -> int:
        conn = self._get_conn()
        context_hash = self._hash_context(context)
        now = datetime.now().isoformat()
        cur = conn.execute(
            "INSERT INTO strategies "
            "(timestamp, plan_type, context_hash, context_json, "
            "content_json, outcome_score, feedback) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                now, plan_type, context_hash,
                json.dumps(context, ensure_ascii=False),
                json.dumps(content, ensure_ascii=False),
                outcome_score, feedback,
            ),
        )
        conn.commit()
        strategy_id = cur.lastrowid
        vs = _get_vectorstore()
        if vs:
            try:
                vs["embed_strategy"](strategy_id, context, content)
            except Exception as e:
                logger.warning("Failed to embed strategy %d: %s", strategy_id, e)
        else:
            logger.warning(
                "Vectorstore unavailable, strategy %d "
                "stored without vector embedding", strategy_id
            )
        return strategy_id

    def _recall_legacy(self, context, top_k=5, min_similarity=0.3):
        conn = self._get_conn()
        context_hash = self._hash_context(context)
        rows = conn.execute(
            "SELECT * FROM strategies WHERE context_hash = ? ORDER BY timestamp DESC LIMIT ?",
            (context_hash, top_k)
        ).fetchall()
        exact = [dict(r) for r in rows]
        if len(exact) >= top_k:
            return exact[:top_k]
        plan_type = context.get("plan_type")
        fallback = []
        if plan_type:
            rows = conn.execute(
                "SELECT * FROM strategies WHERE plan_type = ? ORDER BY timestamp DESC LIMIT ?",
                (plan_type, top_k)
            ).fetchall()
            fallback = [dict(r) for r in rows]
        if not fallback:
            rows = conn.execute(
                "SELECT * FROM strategies ORDER BY timestamp DESC LIMIT ?",
                (top_k,)
            ).fetchall()
            fallback = [dict(r) for r in rows]
        seen_ids = {r["id"] for r in exact}
        sig_query = self._context_to_signature(context)
        scored = []
        for r in fallback:
            if r["id"] in seen_ids:
                continue
            stored_context = json.loads(r["context_json"])
            sig_stored = self._context_to_signature(stored_context)
            sim = self.semantic_similarity(sig_query, sig_stored)
            if sim >= min_similarity:
                scored.append((sim, r))
        scored.sort(key=lambda x: -x[0])
        remaining = top_k - len(exact)
        combined = exact + [
            {"similarity": round(s, 3), **r} for s, r in scored[:remaining]
        ]
        if not combined:
            rows = conn.execute(
                "SELECT * FROM strategies ORDER BY timestamp DESC LIMIT ?",
                (top_k,)
            ).fetchall()
            combined = [dict(r) for r in rows]
        return combined[:top_k]

    def _enrich_vector_results(self, vector_results, conn, exact, top_k):
        seen_ids = {r["id"] for r in exact}
        enriched = list(exact)
        for r in vector_results:
            sid = r.get("strategy_id")
            if sid is not None and sid not in seen_ids:
                row = conn.execute("SELECT * FROM strategies WHERE id = ?", (sid,)).fetchone()
                if row:
                    d = dict(row)
                    d["similarity"] = round(r.get("score", 0), 3)
                    enriched.append(d)
                    seen_ids.add(sid)
                if len(enriched) >= top_k:
                    break
        return enriched[:top_k]

    def _rrf_fusion(self, rankings, k=60, top_k=5):
        scores = {}
        for rank_list in rankings:
            for pos, item in enumerate(rank_list):
                sid = item.get("id") or item.get("strategy_id")
                if sid is None:
                    continue
                try:
                    sid_int = int(sid)
                except (ValueError, TypeError):
                    import re as _re
                    m = _re.search(r'\d+$', str(sid))
                    sid_int = int(m.group()) if m else None
                if sid_int is None:
                    continue
                key = str(sid_int)
                scores[key] = scores.get(key, 0) + 1 / (k + pos + 1)
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        conn = self._get_conn()
        results = []
        for sid_str, score in ranked[:top_k]:
            row = conn.execute("SELECT * FROM strategies WHERE id = ?", (int(sid_str),)).fetchone()
            if row:
                results.append({"rrf_score": round(score, 4), **dict(row)})
        return results

    def recall_similar(self, context, top_k=5, min_similarity=0.3, mode="exact"):
        if mode == "exact":
            return self._recall_legacy(context, top_k, min_similarity)
        conn = self._get_conn()
        context_hash = self._hash_context(context)
        exact = [dict(r) for r in conn.execute(
            "SELECT * FROM strategies WHERE context_hash = ? ORDER BY timestamp DESC LIMIT ?",
            (context_hash, top_k)
        ).fetchall()]
        if mode == "vector":
            vs = _get_vectorstore()
            if vs:
                text = json.dumps(context, sort_keys=True, ensure_ascii=False)
                vector_results = vs["hybrid_search"](text, top_k=top_k)
                return self._enrich_vector_results(vector_results, conn, exact, top_k)
            return exact[:top_k]
        rankings = []
        if exact:
            rankings.append(exact)
        vs = _get_vectorstore()
        vs_results = []
        if vs:
            try:
                text = json.dumps(context, sort_keys=True, ensure_ascii=False)
                vs_results = vs["hybrid_search"](text, top_k=top_k)
                if vs_results:
                    rankings.append(vs_results)
            except Exception as e:
                logger.warning("Vector search failed in recall_similar (hybrid mode): %s", e)
        plan_type = context.get("plan_type")
        plan_results = []
        if plan_type:
            plan_rows = conn.execute(
                "SELECT * FROM strategies WHERE plan_type = ? ORDER BY timestamp DESC LIMIT ?",
                (plan_type, top_k * 2)
            ).fetchall()
            plan_results = [dict(r) for r in plan_rows]
            if plan_results:
                rankings.append(plan_results)
        combined = []
        if rankings:
            combined = self._rrf_fusion(rankings, top_k=top_k)
            if len(combined) < top_k and plan_results:
                seen_ids = {r["id"] for r in combined}
                for r in plan_results:
                    if r["id"] not in seen_ids:
                        combined.append(r)
                        seen_ids.add(r["id"])
                    if len(combined) >= top_k:
                        break
        if not combined:
            rows = conn.execute(
                "SELECT * FROM strategies ORDER BY timestamp DESC LIMIT ?",
                (top_k,)
            ).fetchall()
            combined = [dict(r) for r in rows]
        return combined[:top_k]

    def recall_semantic(
        self, context: dict, top_k: int = 5,
        min_similarity: float = 0.3,
    ) -> list[dict]:
        vs = _get_vectorstore()
        if vs:
            try:
                query_text = json.dumps(context, sort_keys=True, ensure_ascii=False)
                results = vs["hybrid_search"](query_text, top_k=top_k)
                if results:
                    conn = self._get_conn()
                    enriched = []
                    for r in results:
                        sid = r.get("strategy_id")
                        if sid is not None:
                            row = conn.execute(
                                "SELECT * FROM strategies WHERE id = ?", (sid,)
                            ).fetchone()
                            if row:
                                d = dict(row)
                                d["similarity"] = round(r.get("score", 0), 3)
                                enriched.append(d)
                    if enriched:
                        return enriched[:top_k]
            except Exception as e:
                logger.warning("Vector search failed in recall_semantic: %s", e)
        conn = self._get_conn()
        all_rows = conn.execute(
            "SELECT * FROM strategies ORDER BY timestamp DESC LIMIT 100"
        ).fetchall()
        sig_query = self._context_to_signature(context)
        scored = []
        for r in all_rows:
            stored_context = json.loads(r["context_json"])
            sig_stored = self._context_to_signature(stored_context)
            sim = self.semantic_similarity(sig_query, sig_stored)
            if sim >= min_similarity:
                scored.append((sim, dict(r)))
        scored.sort(key=lambda x: -x[0])
        return [{"similarity": round(s, 3), **r} for s, r in scored[:top_k]]

    def detect_patterns(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT plan_type,
                   COUNT(*) as total,
                   SUM(CASE WHEN outcome_score IS NOT NULL
                       AND outcome_score < 5.0 THEN 1 ELSE 0 END
                   ) as failures
            FROM strategies
            GROUP BY plan_type
            HAVING total > 0
        """).fetchall()
        results = []
        for r in rows:
            plan_type = r["plan_type"]
            total = r["total"]
            failures = r["failures"] or 0
            failure_rate = failures / total if total > 0 else 0
            if failure_rate >= 0.6:
                entry = {
                    "plan_type": plan_type,
                    "total": total,
                    "failures": failures,
                    "failure_rate": round(failure_rate, 2)
                }
                results.append(entry)
                conn.execute(
                    "INSERT INTO patterns "
                    "(plan_type, pattern_name, description, "
                    "total_count, fail_count, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        plan_type,
                        f"high_failure_{plan_type}",
                        f"Plan type {plan_type} has "
                        f"{failure_rate:.0%} failure rate "
                        f"({failures}/{total})",
                        total,
                        failures,
                        datetime.now().isoformat(),
                    ),
                )
        conn.commit()
        return results

    def stats(self) -> dict:
        conn = self._get_conn()
        total_strategies = conn.execute("SELECT COUNT(*) as c FROM strategies").fetchone()["c"]
        total_patterns = conn.execute("SELECT COUNT(*) as c FROM patterns").fetchone()["c"]
        by_type = {}
        for r in conn.execute(
            "SELECT plan_type, COUNT(*) as c "
            "FROM strategies GROUP BY plan_type"
        ).fetchall():
            by_type[r["plan_type"]] = r["c"]
        avg_score = conn.execute(
            "SELECT AVG(outcome_score) as a "
            "FROM strategies WHERE outcome_score IS NOT NULL"
        ).fetchone()["a"]
        return {
            "total_strategies": total_strategies,
            "total_patterns": total_patterns,
            "by_plan_type": by_type,
            "avg_outcome_score": round(avg_score, 2) if avg_score else None,
        }

    def add_pattern(self, plan_type: str, pattern_name: str, description: str) -> int:
        conn = self._get_conn()
        cur = conn.execute(
            "INSERT INTO patterns "
            "(plan_type, pattern_name, description, "
            "total_count, fail_count, created_at) "
            "VALUES (?, ?, ?, 0, 0, ?)",
            (plan_type, pattern_name, description,
             datetime.now().isoformat()),
        )
        conn.commit()
        return cur.lastrowid

    BETA_PRIORS = {
        "adopcion_nueva_funcionalidad": (3, 5),
        "velocidad_desarrollo": (4, 2),
        "engagement_stakeholders": (2, 3),
        "calidad_datos": (3, 3),
        "riesgo_competencia": (2, 4),
        "alineacion_organizacional": (5, 2),
        "capacidad_tecnica": (4, 3),
        "presupuesto_disponible": (3, 4),
    }

    def predict_outcome(self, context: dict, plan_type: str = None) -> dict:
        similar = self.recall_semantic(context, top_k=10)
        if plan_type:
            similar = [s for s in similar if s.get("plan_type") == plan_type]
        if not similar:
            similar = self.recall_similar(context, top_k=10)
        if not similar:
            return {"probability_success": None, "message": "No hay estrategias similares previas para basar una predicción."}
        scores = [s["outcome_score"] for s in similar if s["outcome_score"] is not None]
        if not scores:
            return {"probability_success": None, "message": "Estrategias similares encontradas pero sin outcome scores."}
        successes = sum(1 for s in scores if s >= 5.0)
        total = len(scores)
        p_success = successes / total
        avg_score = sum(scores) / total
        return {
            "probability_success": round(p_success, 2),
            "avg_outcome_score": round(avg_score, 2),
            "based_on_n_strategies": total,
            "plan_type": plan_type or "any",
            "message": f"Basado en {total} estrategias similares previas: P(éxito) = {p_success:.0%} (score promedio: {avg_score:.1f}/10)",
        }

    def get_failure_patterns(self) -> list[dict]:
        patterns = self.list_patterns()
        enriched = []
        for p in patterns:
            suggestion = self._generate_suggestion(p)
            enriched.append({**p, "suggestion": suggestion})
        return enriched

    def _generate_suggestion(self, pattern: dict) -> str:
        pt = pattern.get("plan_type", "")
        suggestions = {
            "okr": "Revisar realismo de KRs. Verificar baseline y target con SimulationEngine. Considerar reducir alcance.",
            "roadmap": "Roadmaps previos subestimaron dependencias. Usar CausalModeler para identificar efectos de segundo orden.",
            "foda": "FODAs previos omitieron amenazas externas. Ejecutar gap_service.detect() para identificar knowledge gaps.",
            "strategic_analysis": "Análisis previos fueron demasiado optimistas. Activar Bias Detection Layer y Creative Branching Protocol.",
        }
        for key, msg in suggestions.items():
            if key in pt:
                return msg
        return "Revisar metodología y considerar simulaciones Monte Carlo antes de finalizar."

    def generate_prevention_suggestions(self, context: dict, plan_type: str = None) -> list[dict]:
        prediction = self.predict_outcome(context, plan_type)
        patterns = self.get_failure_patterns()
        relevant = [p for p in patterns if not plan_type or p["plan_type"] == plan_type]
        suggestions = []
        if prediction.get("probability_success") is not None and prediction["probability_success"] < 0.5:
            suggestions.append({
                "type": "high_risk",
                "message": f"Predicción de éxito baja ({prediction['probability_success']:.0%}). {
                    'Recomendación: ' + (relevant[0]['suggestion'] if relevant else 'Revisar supuestos y usar SimulationEngine.')}"
            })
        for p in relevant[:3]:
            suggestions.append({
                "type": "pattern_warning",
                "plan_type": p["plan_type"],
                "message": f"Patrón recurrente: {p['description']}. {p.get('suggestion', '')}"
            })
        if not suggestions:
            suggestions.append({"type": "ok", "message": "No se detectaron patrones de riesgo para este contexto."})
        return suggestions

    def calibrate(self, feedback_file: str) -> dict:
        data = json.loads(Path(feedback_file).read_text(encoding="utf-8"))
        entries = data if isinstance(data, list) else data.get("feedback", [])
        adjustments = {}
        for entry in entries:
            pt = entry.get("plan_type", "unknown")
            predicted = entry.get("predicted_score", 5.0)
            actual = entry.get("actual_score", 5.0)
            error = actual - predicted
            prior = self.BETA_PRIORS.get(pt, (3, 3))
            adj_alpha = max(0.1, prior[0] + error * 0.1)
            adj_beta = max(0.1, prior[1] - error * 0.1)
            adjustments[pt] = {"prior_alpha": prior[0], "prior_beta": prior[1], "adjusted_alpha": round(adj_alpha, 2), "adjusted_beta": round(adj_beta, 2), "error": round(error, 2)}
            if pt in self.BETA_PRIORS:
                self.BETA_PRIORS[pt] = (round(adj_alpha, 2), round(adj_beta, 2))
        return {"entries_processed": len(entries), "adjustments": adjustments}

    def calibration_report(self) -> str:
        lines = []
        lines.append("# Auto-Calibration Report")
        lines.append(f"*Generated: {datetime.now().isoformat()}*")
        lines.append("")
        lines.append("## Current Beta Priors")
        lines.append("")
        lines.append("| Variable | Alpha | Beta | Mean |")
        lines.append("|----------|-------|------|------|")
        for name, (alpha, beta_val) in sorted(self.BETA_PRIORS.items()):
            mean = alpha / (alpha + beta_val) if (alpha + beta_val) > 0 else 0
            lines.append(f"| {name} | {alpha} | {beta_val} | {mean:.2f} |")
        lines.append("")
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) as c FROM strategies WHERE outcome_score IS NOT NULL").fetchone()["c"]
        avg = conn.execute("SELECT AVG(outcome_score) as a FROM strategies WHERE outcome_score IS NOT NULL").fetchone()["a"]
        lines.append(f"**Calibrated strategies**: {total}")
        lines.append(f"**Average outcome score**: {round(avg, 2) if avg else 'N/A'}")
        return "\n".join(lines)

    def list_patterns(self, plan_type: str = None) -> list[dict]:
        conn = self._get_conn()
        if plan_type:
            rows = conn.execute("SELECT * FROM patterns WHERE plan_type = ? ORDER BY created_at DESC", (plan_type,))
        else:
            rows = conn.execute("SELECT * FROM patterns ORDER BY created_at DESC")
        return [dict(r) for r in rows.fetchall()]


def _parse_json_arg(raw: str) -> dict:
    if os.path.isfile(raw):
        return json.loads(Path(raw).read_text(encoding="utf-8"))
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(
        description="Strategic Memory Bank — persistent strategy storage with context recall and pattern detection.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  strategy_memory.py store --plan-type okr --context '{\"industry\": \"cloud\"}' --content '{\"okrs\": [...]}'\n"
            "  strategy_memory.py recall --context '{\"industry\": \"cloud\"}'\n"
            "  strategy_memory.py patterns\n"
            "  strategy_memory.py stats\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    store_parser = subparsers.add_parser("store", help="Store a strategy")
    store_parser.add_argument("--plan-type", required=True, help="Type of plan (okr, roadmap, foda, etc.)")
    store_parser.add_argument("--context", required=True, help="Context JSON string or file path")
    store_parser.add_argument("--content", required=True, help="Content JSON string or file path")
    store_parser.add_argument("--outcome-score", type=float, help="Outcome score (0-10)")
    store_parser.add_argument("--feedback", help="Optional feedback text")

    recall_parser = subparsers.add_parser("recall", help="Recall similar strategies by context")
    recall_parser.add_argument("--context", required=True, help="Context JSON string or file path")
    recall_parser.add_argument("--top-k", type=int, default=5, help="Number of results (default: 5)")
    recall_parser.add_argument("--mode", choices=["hybrid", "vector", "exact"], default="hybrid",
        help="Recall mode: hybrid (RRF fusion), vector (semantic only), exact (hash + jaccard)")

    recall_sem_parser = subparsers.add_parser("recall-semantic", help="Recall semantically similar strategies (no hash dependency)")
    recall_sem_parser.add_argument("--context", required=True, help="Context JSON string or file path")
    recall_sem_parser.add_argument("--top-k", type=int, default=5, help="Number of results (default: 5)")
    recall_sem_parser.add_argument("--min-similarity", type=float, default=0.3, help="Minimum similarity threshold (default: 0.3)")

    patterns_parser = subparsers.add_parser("patterns", help="Detect and manage patterns")
    patterns_parser.add_argument("--detect", action="store_true", help="Run auto-pattern detection")
    patterns_parser.add_argument("--add", nargs=3, metavar=("PLAN_TYPE", "NAME", "DESC"), help="Add a pattern manually")
    patterns_parser.add_argument("--list", nargs="?", const=True, metavar="PLAN_TYPE", help="List patterns (optionally filter by plan_type)")

    subparsers.add_parser("stats", help="Show strategy memory statistics")

    predict_parser = subparsers.add_parser("predict", help="Predict outcome based on similar past strategies")
    predict_parser.add_argument("--context", required=True, help="Context JSON string or file path")
    predict_parser.add_argument("--plan-type", help="Filter by plan type")

    prevent_parser = subparsers.add_parser("prevent", help="Generate prevention suggestions based on patterns")
    prevent_parser.add_argument("--context", required=True, help="Context JSON string or file path")
    prevent_parser.add_argument("--plan-type", help="Filter by plan type")

    calibrate_parser = subparsers.add_parser("calibrate", help="Calibrate beta priors from feedback data")
    calibrate_parser.add_argument("--feedback", required=True, help="Path to feedback JSON file")

    subparsers.add_parser("calibration-report", help="Show calibration report")

    args = parser.parse_args()
    bank = StrategicMemoryBank()

    if args.command == "store":
        context = _parse_json_arg(args.context)
        content = _parse_json_arg(args.content)
        sid = bank.store(context, content, args.plan_type, args.outcome_score, args.feedback)
        print(f"Stored strategy id={sid} type={args.plan_type}")

    elif args.command == "recall":
        context = _parse_json_arg(args.context)
        results = bank.recall_similar(context, args.top_k, mode=args.mode)
        if not results:
            print("No similar strategies found.")
            return
        print(f"Found {len(results)} similar strategies (mode={args.mode}):")
        for r in results:
            score_label = ""
            if "rrf_score" in r:
                score_label = f" rrf={r['rrf_score']}"
            elif "similarity" in r:
                score_label = f" sim={r['similarity']}"
            print(f"  id={r['id']} type={r['plan_type']} ts={r['timestamp'][:19]} score={r['outcome_score']}{score_label}")

    elif args.command == "recall-semantic":
        context = _parse_json_arg(args.context)
        results = bank.recall_semantic(context, args.top_k, args.min_similarity)
        if not results:
            print("No semantically similar strategies found.")
            return
        print(f"Found {len(results)} semantically similar strategies (min_similarity={args.min_similarity}):")
        for r in results:
            print(f"  id={r['id']} type={r['plan_type']} sim={r['similarity']} ts={r['timestamp'][:19]} score={r['outcome_score']}")

    elif args.command == "patterns":
        if args.detect:
            detected = bank.detect_patterns()
            if detected:
                print(f"Detected {len(detected)} pattern(s) with failure rate >= 60%:")
                for d in detected:
                    print(f"  {d['plan_type']}: {d['failures']}/{d['total']} failures ({d['failure_rate']:.0%})")
            else:
                print("No high-failure patterns detected.")
        elif args.add:
            pt, name, desc = args.add
            pid = bank.add_pattern(pt, name, desc)
            print(f"Added pattern id={pid} type={pt}")
        elif args.list:
            filter_pt = args.list if isinstance(args.list, str) else None
            patterns = bank.list_patterns(filter_pt)
            if not patterns:
                print("No patterns found.")
                return
            print(f"{'ID':<5} {'Plan Type':<15} {'Pattern Name':<25} {'Description':<40} {'Fail/Total':<12}")
            print("-" * 100)
            for p in patterns:
                ratio = f"{p['fail_count']}/{p['total_count']}" if p['total_count'] else "0/0"
                print(f"{p['id']:<5} {p['plan_type']:<15} {p['pattern_name']:<25} {p['description'][:38]:<40} {ratio:<12}")

    elif args.command == "stats":
        s = bank.stats()
        print("Strategic Memory Bank — Statistics")
        print(f"  Total strategies: {s['total_strategies']}")
        print(f"  Total patterns:   {s['total_patterns']}")
        print(f"  By plan type:     {s['by_plan_type']}")
        print(f"  Avg outcome score: {s['avg_outcome_score']}")

    elif args.command == "predict":
        context = _parse_json_arg(args.context)
        result = bank.predict_outcome(context, args.plan_type)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "prevent":
        context = _parse_json_arg(args.context)
        suggestions = bank.generate_prevention_suggestions(context, args.plan_type)
        for s in suggestions:
            print(f"[{s['type']}] {s['message']}")

    elif args.command == "calibrate":
        result = bank.calibrate(args.feedback)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "calibration-report":
        print(bank.calibration_report())


if __name__ == "__main__":
    main()
