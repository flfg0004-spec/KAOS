"""Crystallize engine: intelligent duplicate fusion with AI.

Multi-level dedup pipeline:
  1. MD5 hash exact match
  2. Levenshtein title similarity > 0.90
  3. Jaccard content similarity > 0.85
  4. Embedding similarity > 0.90 (via txtai MCP)
  5. Link prediction co-citation

Crystallize (AI merge):
  - DSOL (Gemini Flash) analyzes candidate pairs
  - Produces merged note with supersedes edge
  - Original notes moved to _archive/ with redirect stub
"""

import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

import lib.llm as llm

BASE = (Path(__file__).resolve().parent.parent.parent)
ARCHIVE = BASE / "_archive"
WIKI_CONCEPTS = BASE / "wiki" / "concepts"
WIKI_ENTITIES = BASE / "wiki" / "entities"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _levenshtein_ratio(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    a, b = a.lower(), b.lower()
    n, m = len(a), len(b)
    dp = list(range(n + 1))
    for j in range(1, m + 1):
        prev = dp[0]
        dp[0] = j
        for i in range(1, n + 1):
            temp = dp[i]
            if a[i - 1] == b[j - 1]:
                dp[i] = prev
            else:
                dp[i] = 1 + min(dp[i], dp[i - 1], prev)
            prev = temp
    return 1.0 - (dp[n] / max(n, m))


def _jaccard_similarity(a: str, b: str) -> float:
    set_a = set(re.findall(r"\w+", a.lower()))
    set_b = set(re.findall(r"\w+", b.lower()))
    if not set_a and not set_b:
        return 1.0
    return len(set_a & set_b) / len(set_a | set_b)


def _embedding_similarity(texts: list[str]) -> list[tuple[str, str, float]]:
    """Compute pairwise embedding similarities via txtai MCP."""
    import os as _os
    import subprocess
    import sys as _sys
    if _os.environ.get("KAOS_TESTING") == "1":
        return []
    mcp_txtai = BASE / "_scripts" / "mcp_txtai.py"
    req = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "deduplicate", "arguments": {"path": str(WIKI_CONCEPTS), "threshold": 0.0}}
    })
    try:
        r = subprocess.run(
            [_sys.executable, str(mcp_txtai)],
            input=req, capture_output=True, text=True, timeout=30
        )
        if r.returncode == 0 and r.stdout.strip():
            resp = json.loads(r.stdout.strip())
            content = resp.get("result", {}).get("content", [])
            if content:
                pairs = json.loads(content[0]["text"])
                return [(p["file_a"], p["file_b"], p["similarity"]) for p in pairs]
    except Exception:
        pass
    return []


def _get_all_concept_files() -> list[Path]:
    files = []
    for d in [WIKI_CONCEPTS, WIKI_ENTITIES]:
        if d.exists():
            files.extend(sorted(d.glob("*.md")))
    return files


def _cocitation_similarity(files: list[Path]) -> list[tuple[str, str, float]]:
    """Co-citation: two notes are similar if they are linked from the same sources."""
    backlink_map = {}
    for f in files:
        content = _read(f)
        links = re.findall(r"\[\[([^\]]+?)\]\]", content)
        for link in links:
            target = link.split("|")[0].split("#")[0].strip()
            if target:
                backlink_map.setdefault(target, set()).add(f.stem)
    pairs = []
    targets = list(backlink_map.keys())
    for i in range(len(targets)):
        for j in range(i + 1, len(targets)):
            shared = len(backlink_map[targets[i]] & backlink_map[targets[j]])
            total = len(backlink_map[targets[i]] | backlink_map[targets[j]])
            if total > 0:
                score = shared / total
                if score > 0.3:
                    pairs.append((targets[i], targets[j], round(score, 3)))
    return sorted(pairs, key=lambda x: -x[2])


def find_candidates(min_embedding: float = 0.90, min_jaccard: float = 0.85,
                    min_title: float = 0.90) -> list[dict]:
    """Multi-level dedup. Returns candidates sorted by confidence."""
    files = _get_all_concept_files()
    if len(files) < 2:
        return []

    candidates = []
    seen_pairs = set()

    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            fa, fb = files[i], files[j]
            pair_key = tuple(sorted([fa.stem, fb.stem]))
            if pair_key in seen_pairs:
                continue

            ca, cb = _read(fa), _read(fb)
            if not ca.strip() or not cb.strip():
                continue

            # Level 1: MD5 hash exact
            if _md5(ca) == _md5(cb):
                candidates.append({"file_a": str(fa), "file_b": str(fb),
                                   "method": "hash_exact", "confidence": 1.0})
                seen_pairs.add(pair_key)
                continue

            # Level 2: Title similarity
            title_sim = _levenshtein_ratio(fa.stem, fb.stem)
            if title_sim >= min_title:
                candidates.append({"file_a": str(fa), "file_b": str(fb),
                                   "method": "title_fuzzy", "confidence": round(title_sim, 3)})
                seen_pairs.add(pair_key)
                continue

            # Level 3: Jaccard content
            jaccard = _jaccard_similarity(ca, cb)
            if jaccard >= min_jaccard:
                candidates.append({"file_a": str(fa), "file_b": str(fb),
                                   "method": "jaccard_content", "confidence": round(jaccard, 3)})
                seen_pairs.add(pair_key)

    # Level 4-5: Embedding + co-citation (global, via MCP)
    embed_pairs = _embedding_similarity([])
    for a, b, sim in embed_pairs:
        pair_key = tuple(sorted([Path(a).stem, Path(b).stem]))
        if pair_key not in seen_pairs and sim >= min_embedding:
            candidates.append({"file_a": str(BASE / a), "file_b": str(BASE / b),
                               "method": "embedding", "confidence": round(sim, 3)})
            seen_pairs.add(pair_key)

    cocit_pairs = _cocitation_similarity(files)
    for a, b, sim in cocit_pairs:
        pair_key = tuple(sorted([a, b]))
        if pair_key not in seen_pairs:
            fa = WIKI_CONCEPTS / f"{a}.md"
            fb = WIKI_CONCEPTS / f"{b}.md"
            if fa.exists() and fb.exists():
                candidates.append({"file_a": str(fa), "file_b": str(fb),
                                   "method": "cocitation", "confidence": round(sim, 3)})
                seen_pairs.add(pair_key)

    return sorted(candidates, key=lambda x: -x["confidence"])


def _backup_file(path: Path) -> Path | None:
    """Create a .bak copy before modifying. Returns backup path or None."""
    try:
        bak = path.with_suffix(path.suffix + ".bak")
        import shutil as _sh
        _sh.copy2(str(path), str(bak))
        return bak
    except Exception:
        return None


def _rollback(backup: Path, original: Path):
    """Restore a file from backup."""
    if backup and backup.exists():
        import shutil as _sh
        _sh.copy2(str(backup), str(original))
        backup.unlink(missing_ok=True)


def crystallize(file_a: str, file_b: str, dry_run: bool = True) -> dict:
    """AI fusion of two related notes into one consolidated note."""
    pa, pb = Path(file_a), Path(file_b)
    if not pa.exists() or not pb.exists():
        return {"error": "One or both files not found"}
    if not pa.is_file() or not pb.is_file():
        return {"error": "One or both paths are not files"}

    ca, cb = _read(pa), _read(pb)
    if not ca.strip() or not cb.strip():
        return {"error": "One or both files are empty"}

    title_a = pa.stem.replace("-", " ").title()
    title_b = pb.stem.replace("-", " ").title()
    merged_title = title_a if len(title_a) <= len(title_b) else title_b

    prompt = (
        "Eres un curador de conocimiento. Fusiona las siguientes 2 notas en UNA sola nota consolidada.\n\n"
        "REGLAS:\n"
        "1. Preserva TODA la información de ambas notas\n"
        "2. Si hay contradicciones, márcalas con > **Contradicción:** ...\n"
        "3. Elimina redundancias obvias\n"
        "4. Organiza por temas, no por fuente\n"
        "5. Responde SOLO con el contenido markdown de la nota fusionada\n\n"
        f"--- NOTA A: {title_a} ---\n{ca[:3000]}\n\n"
        f"--- NOTA B: {title_b} ---\n{cb[:3000]}"
    )

    try:
        merged = llm.llm_call(
            prompt=prompt,
            system=("Eres un curador experto. Fusionas notas de conocimiento "
                    "preservando toda la información y marcando contradicciones."),
            model="go-gemini-flash",
            temperature=0.1,
            max_tokens=4096,
        )
    except Exception as e:
        return {"error": f"LLM fusion failed: {e}"}

    if not merged or not merged.strip():
        return {"error": "LLM returned empty fusion result"}

    merged_content = (
        "---\n"
        f"title: \"{merged_title}\"\n"
        f"supersedes: [{pa.stem}, {pb.stem}]\n"
        f"merged_at: \"{datetime.now().strftime('%Y-%m-%d %H:%M')}\"\n"
        "---\n\n"
        f"{merged.strip()}\n\n"
        "---\n"
        f"*Nota fusionada desde: [[{pa.stem}]] y [[{pb.stem}]]*"
    )

    merged_path = WIKI_CONCEPTS / f"{pa.stem}-{pb.stem}.md"

    if not dry_run:
        backups = {}
        for orig in [pa, pb]:
            backups[orig] = _backup_file(orig)
        try:
            _write(merged_path, merged_content)
            for orig in [pa, pb]:
                archive_path = ARCHIVE / "concepts" / orig.name
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(orig), str(archive_path))
                stub = f"→ [[{merged_path.stem}]]\n\n*Nota fusionada. Contenido original en `_archive/concepts/{orig.name}`.*"
                _write(orig, stub)
        except Exception as e:
            for orig, bak in backups.items():
                if bak:
                    _rollback(bak, orig)
            if merged_path.exists():
                merged_path.unlink(missing_ok=True)
            return {"error": f"Fusion failed, rolled back: {e}"}

    return {
        "merged_path": str(merged_path),
        "title": merged_title,
        "supersedes": [pa.stem, pb.stem],
        "content_preview": merged[:300],
        "modified": not dry_run,
    }


def run_dedup(dry_run: bool = True, min_confidence: float = 0.90) -> list[dict]:
    """Full dedup pipeline: find candidates + crystallize high-confidence pairs."""
    candidates = find_candidates(min_embedding=0.90)
    if not candidates:
        return []
    results = []
    for c in candidates:
        if c["confidence"] >= min_confidence and c["method"] not in ("cocitation",):
            result = crystallize(c["file_a"], c["file_b"], dry_run=dry_run)
            results.append(result)
            if not dry_run and "error" not in result:
                break
    return results
