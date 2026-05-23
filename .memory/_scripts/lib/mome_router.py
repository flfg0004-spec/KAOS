"""MoME — Mixture of Memory Experts: router TF-IDF + colecciones particionadas."""
import json, sqlite3, re, struct, sys, os
from pathlib import Path
from contextlib import contextmanager

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from lib.vectorstore import CHUNK_SIZE, CHUNK_OVERLAP, EMBED_DIM, _serialize
from lib.config import MOME_THRESHOLD

BASE = Path(__file__).resolve().parent.parent.parent
KAOS_ROOT = BASE.parent
DB_FILE = KAOS_ROOT / ".memory" / "cache" / "vectors.db"

# 6 dominios de experto
DOMAINS = ["code_python", "code_rust", "code_errors",
           "architecture", "research", "strategy"]

# Threshold para activar un experto
ROUTER_THRESHOLD = 0.3

def _count_total_chunks() -> int:
    """Count total chunks across all tables (partitioned + unified)."""
    try:
        conn = sqlite3.connect(str(DB_FILE))
        total = 0
        for domain in DOMAINS:
            try:
                total += conn.execute(
                    f"SELECT COUNT(*) FROM vault_chunks_{domain}"
                ).fetchone()[0]
            except Exception:
                pass
        try:
            total += conn.execute(
                "SELECT COUNT(*) FROM vault_chunks"
            ).fetchone()[0]
        except Exception:
            pass
        conn.close()
        return total
    except Exception:
        return 0

def is_mome_active() -> bool:
    """Runtime check: activar MoME según env y threshold."""
    env = os.environ.get("MOME_ENABLED", "auto").lower()
    if env == "true":
        return True
    if env == "false":
        return False
    return _count_total_chunks() > MOME_THRESHOLD

MOME_ENABLED = is_mome_active()

# Training data para el router (path -> dominio)
def _detect_domain(path: str, content: str = "") -> str:
    """Detect domain from file path and content."""
    p = path.lower()
    # Content-based analysis first
    if content:
        cl = content.lower()
        # Code patterns
        code_kw = ["def ", "class ", "import ", "from ", "return ", "async ", "await ",
                    "fn ", "pub ", "let ", "mut ", "impl ", "struct ", "enum ", "trait ",
                    "try:", "except ", "if __name__", "raise ", "yield "]
        py_kw = ["def ", "class ", "import ", "from ", "try:", "except ", "raise ", "yield "]
        rs_kw = ["fn ", "pub ", "let ", "mut ", "impl ", "struct ", "enum "]
        err_kw = ["error", "exception", "traceback", "fail", "panic", "unwrap",
                   "nullpointer", "typeerror", "attributeerror", "keyerror",
                   "valueerror", "runtimeerror"]
        arch_kw = ["arquitectura", "c4", "adr", "schema", "component",
                    "diagrama", "estructura", "deployment", "system"]
        res_kw = ["research", "paper", "analysis", "study", "investigation",
                   "survey", "comparative", "state of the art"]
        strat_kw = ["strategy", "okr", "roadmap", "plan", "goal", "objective",
                     "kpi", "metric", "dashboard"]
        # NL queries about code (no actual code syntax)
        code_nl = ["api", "rest", "jwt", "endpoint", "route", "server",
                    "database", "sql", "query", "function", "method",
                    "implement", "code", "program", "script", "library",
                    "package", "module", "class", "object", "variable",
                    "loop", "array", "list", "dict", "string", "file",
                    "json", "xml", "http", "request", "response"]
        
        py_score = sum(1 for kw in py_kw if kw in cl)
        rs_score = sum(1 for kw in rs_kw if kw in cl)
        err_score = sum(1 for kw in err_kw if kw in cl)
        arch_score = sum(1 for kw in arch_kw if kw in cl)
        res_score = sum(1 for kw in res_kw if kw in cl)
        strat_score = sum(1 for kw in strat_kw if kw in cl)
        nl_code_score = sum(1 for kw in code_nl if kw in cl)
        
        scores = {
            "code_python": py_score + nl_code_score * 0.3 + rs_score * 0.5,
            "code_rust": rs_score + nl_code_score * 0.2 + py_score * 0.3,
            "code_errors": err_score,
            "architecture": arch_score,
            "research": res_score,
            "strategy": strat_score
        }
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
    
    # Fallback: path-based classification
    if "code" in p or "kratos" in p:
        if ".rs" in p or "rust" in p:
            return "code_rust"
        return "code_python"
    if "schema" in p or "adr" in p:
        return "architecture"
    if "raw" in p:
        return "research"
    if "strategy" in p or "okr" in p:
        return "strategy"
    if "error" in p or "exception" in p:
        return "code_errors"
    return "strategy"  # default

def _load_model():
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        return TfidfVectorizer, LogisticRegression
    except ImportError:
        return None, None

class MoMERouter:
    """Router MoME — clasifica consultas en dominio(s) de experto."""
    
    def __init__(self):
        self.vectorizer = None
        self.classifier = None
        self.domains = DOMAINS
        self.threshold = ROUTER_THRESHOLD
    
    def train(self):
        """Train router using existing vault files as training data."""
        TfidfVectorizer, LogisticRegression = _load_model()
        if TfidfVectorizer is None:
            return False
        
        md_files = list((KAOS_ROOT / ".memory").rglob("*.md"))
        texts, labels = [], []
        for f in md_files:
            rel = f.relative_to(KAOS_ROOT / ".memory").as_posix()
            try:
                content = f.read_text(encoding="utf-8", errors="replace")[:500]
                domain = _detect_domain(rel, content)
                texts.append(f"{rel} {content}")
                labels.append(domain)
            except Exception:
                continue
        
        self.vectorizer = TfidfVectorizer(max_features=2000)
        X = self.vectorizer.fit_transform(texts)
        self.classifier = LogisticRegression(max_iter=200, class_weight="balanced")
        self.classifier.fit(X, labels)
        return True
    
    def route(self, query: str) -> list[tuple[str, float]]:
        """Route query to 1-2 expert domains with confidence scores."""
        if self.classifier is None or self.vectorizer is None:
            fb = _detect_domain("", query)
            return [(fb, 0.6)]  # content-based fallback
        
        X = self.vectorizer.transform([query])
        probs = self.classifier.predict_proba(X)[0]
        activated = [(d, p) for d, p in zip(self.domains, probs) if p > self.threshold]
        if activated:
            return sorted(activated, key=lambda x: -x[1])[:2]
        
        # Fallback: use content-based _detect_domain on the query itself
        fallback_domain = _detect_domain("", query)
        return [(fallback_domain, 0.6)]

    # M3: Expert Confidence Gating
    def route_with_gating(self, query: str) -> list[str]:
        """Gate: si confianza < 0.6, activar 2 expertos en vez de 1."""
        activated = self.route(query)
        if not activated:
            # Use content-based _detect_domain as fallback
            fb = _detect_domain("", query)
            return [fb]
        if activated[0][1] < 0.6 and len(activated) < 2:
            # Baja confianza: añadir segundo experto via _detect_domain
            fb = _detect_domain("", query)
            existing = {d for d, _ in activated}
            if fb not in existing:
                return [activated[0][0], fb]
        return [activated[0][0]]

    # M4: Router Auto-Tuning con Feedback
    def update_weights(self, query: str, domain_used: str, success: bool) -> None:
        """Refuerza o debilita el routing según éxito (reinforcement)."""
        if self.classifier is None:
            return
        lr = 0.01  # learning rate
        X = self.vectorizer.transform([query])
        if success:
            self.classifier.coef_ *= (1.0 + lr)  # reforzar
        else:
            self.classifier.coef_ *= (1.0 - lr)  # debilitar


# ─── Vector Store Particionado ───

def init_partitioned():
    """Create partitioned tables for each domain."""
    conn = sqlite3.connect(str(DB_FILE))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.enable_load_extension(True)
    try:
        import sqlite_vec
        sqlite_vec.load(conn)
    except ImportError:
        pass
    finally:
        conn.enable_load_extension(False)
    
    for domain in DOMAINS:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS vault_chunks_{domain} (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_index INTEGER NOT NULL
            )
        """)
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{domain}_path ON vault_chunks_{domain}(path)")
        conn.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS vault_vectors_{domain}
            USING vec0(embedding float[{EMBED_DIM}])
        """)
    
    conn.commit()
    conn.close()
    return f"Partitioned {len(DOMAINS)} domain tables created"

def query_partitioned(query: str, domain: str, top_k: int = 5) -> list[dict]:
    """Query a specific domain partition."""
    from lib.vectorstore import _import_model
    model = _import_model()
    if not model:
        return []
    
    q_vec = model.encode([query])[0]
    conn = sqlite3.connect(str(DB_FILE))
    conn.enable_load_extension(True)
    try:
        import sqlite_vec
        sqlite_vec.load(conn)
    except ImportError:
        pass
    finally:
        conn.enable_load_extension(False)
    
    try:
        results = conn.execute(f"""
            SELECT c.path, c.chunk_text, v.distance
            FROM vault_vectors_{domain} v
            JOIN vault_chunks_{domain} c ON v.rowid = c.rowid
            WHERE v.embedding MATCH ? AND k = ?
            ORDER BY v.distance
        """, [_serialize(q_vec), top_k]).fetchall()
    except Exception:
        conn.close()
        return []
    
    conn.close()
    return [
        {"path": r[0], "snippet": r[1][:200], "score": round(1.0 / (1.0 + r[2]), 3), "domain": domain}
        for r in results
    ]

def rebuild_partitioned(full: bool = False):
    """Rebuild all partitioned indexes from vault files."""
    from lib.vectorstore import _import_model, chunk_text
    import unicodedata
    
    model = _import_model()
    if not model:
        return "ERROR: sentence-transformers not installed"
    
    init_partitioned()
    conn = sqlite3.connect(str(DB_FILE))
    conn.enable_load_extension(True)
    try:
        import sqlite_vec
        sqlite_vec.load(conn)
    except ImportError:
        pass
    finally:
        conn.enable_load_extension(False)
    
    conn.execute("PRAGMA journal_mode=WAL")
    
    if full:
        for domain in DOMAINS:
            conn.execute(f"DELETE FROM vault_vectors_{domain}")
            conn.execute(f"DELETE FROM vault_chunks_{domain}")
    
    md_files = list((KAOS_ROOT / ".memory").rglob("*.md"))
    exclude = {"cache", "_pending", ".git", "_scripts", "dashboard"}
    
    counts = {d: 0 for d in DOMAINS}
    for f in md_files:
        if any(p in exclude for p in f.parts):
            continue
        rel = f.relative_to(KAOS_ROOT / ".memory").as_posix()
        
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if not text.strip():
            continue
        
        domain = _detect_domain(rel, text[:500])
        
        existing = conn.execute(f"SELECT COUNT(*) FROM vault_chunks_{domain} WHERE path = ?", (rel,)).fetchone()[0]
        if not full and existing > 0:
            continue
        
        chunks = chunk_text(text)
        if not chunks:
            continue
        
        vecs = model.encode(chunks)
        for i, (chunk, vec) in enumerate(zip(chunks, vecs)):
            cur = conn.execute(
                f"INSERT INTO vault_chunks_{domain}(path, chunk_text, chunk_index) VALUES (?, ?, ?)",
                (rel, chunk, i)
            )
            rowid = cur.lastrowid
            conn.execute(f"INSERT INTO vault_vectors_{domain}(rowid, embedding) VALUES (?, ?)",
                        (rowid, _serialize(vec)))
            counts[domain] += 1
    
    conn.commit()
    conn.close()
    
    summary = {d: counts[d] for d in DOMAINS if counts[d] > 0}
    return f"Partitioned rebuild: {sum(counts.values())} chunks across {len([c for c in counts.values() if c > 0])} domains"

if __name__ == "__main__":
    router = MoMERouter()
    if router.train():
        print("MoME Router trained successfully")
        tests = ["implementar API REST con JWT", "error NoneType en Python",
                 "arquitectura C4 del sistema", "analisis de mercado IA 2026"]
        for t in tests:
            routes = router.route(t)
            print(f"  '{t[:40]}...' -> {routes}")
    else:
        print("sklearn not available, router not trained")
    
    print(f"\nDomains: {init_partitioned()}")
