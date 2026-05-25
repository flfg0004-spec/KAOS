"""Auto-tagging pipeline with LLM + embedding fallback.

Taxonomía jerárquica de 5 categorías:
  - subject/   (disciplina o campo de estudio)
  - principle/ (principio, ley o regla fundamental)
  - practice/  (práctica, técnica o metodología)
  - tool/      (herramienta, framework o software)
  - reference/ (referencia a fuente, autor o paper)

Pipeline de 7 pasos:
  1. Normalize → 2. Check Blocked → 3. Resolve Alias
  4. Exact Match → 5. Fuzzy Match → 6. Semantic Match (DSOL)
  7. Create Tag
"""

import json
import re
from pathlib import Path

import lib.llm as llm

TAXONOMY_CATEGORIES = {"subject", "principle", "practice", "tool", "reference"}
BLOCKED_TAGS = {"todo", "wip", "update", "draft", "stub", "index", "log"}
ALIAS_MAP = {
    "ai": "subject/artificial-intelligence",
    "ml": "subject/machine-learning",
    "dl": "subject/deep-learning",
    "nlp": "subject/natural-language-processing",
    "llm": "subject/large-language-models",
    "pkm": "practice/personal-knowledge-management",
    "adr": "principle/architecture-decision-record",
    "mcp": "practice/model-context-protocol",
    "api": "practice/api-design",
    "ux": "practice/user-experience",
}
FUZZY_THRESHOLD = 0.6
BASE = (Path(__file__).resolve().parent.parent.parent)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _existing_tags() -> set[str]:
    """Collect all unique tags currently used across the vault."""
    tags = set()
    for f in (BASE / "wiki").rglob("*.md"):
        content = _read(f)
        m = re.search(r"^tags:\s*\[(.+?)\]", content, re.MULTILINE)
        if m:
            for t in m.group(1).split(","):
                tags.add(t.strip().strip('"').strip("'"))
    return tags


def _get_frontmatter(content: str) -> dict:
    fm = {}
    m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                key, _, val = line.partition(":")
                fm[key.strip()] = val.strip()
    return fm


def _update_frontmatter(content: str, tags: list[str]) -> str:
    tag_str = json.dumps(tags)
    if re.search(r"^tags:", content, re.MULTILINE):
        return re.sub(r"^tags:.*", f"tags: {tag_str}", content, flags=re.MULTILINE)
    if content.startswith("---"):
        end = content.index("---", 3)
        return content[:end] + f"tags: {tag_str}\n" + content[end:]
    return f"---\ntags: {tag_str}\n---\n\n{content}"


def _fuzzy_match(tag: str, existing: set[str]) -> str | None:
    """Token overlap fuzzy match with support for hyphenated tags."""
    tag_tokens = set(re.findall(r"\w+", tag.lower()))
    best, best_score = None, 0
    for ex in existing:
        raw_tokens = set(re.findall(r"\w+", ex.lower()))
        ex_tokens = set()
        for t in raw_tokens:
            ex_tokens.add(t)
            ex_tokens.update(t.split("-"))
        if not tag_tokens or not ex_tokens:
            continue
        score = len(tag_tokens & ex_tokens) / max(len(tag_tokens | ex_tokens), 1)
        if score > best_score and score >= FUZZY_THRESHOLD:
            best, best_score = ex, score
    return best


def _embedding_similarity(text: str, tag: str) -> float:
    """Compute cosine similarity between text and tag using fastembed."""
    import subprocess, sys, json as _json
    mcp_embed = BASE / "_scripts" / "mcp_embed.py"
    req = _json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "embed", "arguments": {"texts": [text[:1000], tag]}}
    })
    try:
        r = subprocess.run(
            [sys.executable, str(mcp_embed)],
            input=req, capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0 and r.stdout.strip():
            resp = _json.loads(r.stdout.strip())
            content = resp.get("result", {}).get("content", [])
            if content:
                vecs = _json.loads(content[0]["text"])
                import numpy as np
                a, b = np.array(vecs[0]), np.array(vecs[1])
                return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
    except Exception:
        pass
    return 0.0


def suggest_tags(content: str, title: str = "") -> list[str]:
    """Full 7-step tagging pipeline. Returns list of suggested tags."""
    import os as _os
    if _os.environ.get("KAOS_TESTING") == "1":
        return []

    if not content or not content.strip():
        return []

    existing = _existing_tags()
    content_text = title + " " + content[:3000]

    candidates = set()

    # Step 1-3: Aliases and exact matches from existing tags
    words = set(re.findall(r"\w+", content_text.lower()))
    for alias, tag in ALIAS_MAP.items():
        if alias in words:
            candidates.add(tag)

    # Step 4-5: Fuzzy match against existing tags
    for word in words:
        if len(word) > 3:
            match = _fuzzy_match(word, existing)
            if match:
                candidates.add(match)

    # Step 6: Semantic match via DSOL (Gemini Flash)
    if len(candidates) < 3:
        import concurrent.futures
        prompt = (
            "Eres un experto en taxonomía de conocimiento. "
            "Analiza el siguiente contenido y sugiere 1-3 tags de las categorías: "
            "subject/, principle/, practice/, tool/, reference/. "
            "Responde SOLO con un JSON array de strings.\n\n"
            f"Título: {title}\n\nContenido:\n{content[:2000]}"
        )
        def _llm_tag():
            return llm.llm_call(
                prompt=prompt,
                system="Eres un asistente de tagging. Respondes solo JSON.",
                model="go-gemini-flash",
                temperature=0.1,
                max_tokens=500,
            )
        try:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(_llm_tag)
                response = future.result(timeout=15)
                response = response.strip()
                if response.startswith("```"):
                    response = response.split("\n", 1)[-1].rsplit("```", 1)[0]
                llm_tags = json.loads(response)
                if isinstance(llm_tags, list):
                    for t in llm_tags:
                        has_category = any(f"{cat}/" in t for cat in TAXONOMY_CATEGORIES)
                        if has_category:
                            candidates.add(t)
        except Exception:
            pass

    # Step 6 fallback: embedding similarity against existing tags
    if len(candidates) < 2:
        import concurrent.futures
        def _embed_tag(tag):
            return tag, _embedding_similarity(content_text, tag)
        try:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                futures = {pool.submit(_embed_tag, tag): tag for tag in list(existing)[:30]}
                for future in concurrent.futures.as_completed(futures, timeout=10):
                    tag, sim = future.result()
                    if sim > 0.75:
                        candidates.add(tag)
                        if len(candidates) >= 5:
                            break
        except Exception:
            pass

    # Step 7: Filter blocked, normalize, sort
    result = []
    for tag in candidates:
        clean = tag.strip().lower().replace(" ", "-")
        if clean in BLOCKED_TAGS:
            continue
        has_category = any(f"{cat}/" in clean for cat in TAXONOMY_CATEGORIES)
        if not has_category:
            clean = f"subject/{clean}"
        result.append(clean)

    return sorted(set(result))[:8]


def tag_file(path: str, dry_run: bool = True) -> dict:
    """Tag a single file. Returns {'path': ..., 'tags': [...], 'modified': bool}."""
    fpath = Path(path) if Path(path).is_absolute() else BASE / path
    if not fpath.exists():
        return {"path": path, "error": "File not found"}
    if not fpath.is_file():
        return {"path": path, "error": "Not a file"}

    content = _read(fpath)
    if not content.strip():
        return {"path": path, "error": "Empty file"}
    if len(content) > 50000:
        return {"path": path, "error": "File too large (>50KB)"}

    fm = _get_frontmatter(content)
    existing_tags = json.loads(fm.get("tags", "[]")) if "tags" in fm else []

    title = fpath.stem.replace("-", " ").replace("_", " ").title()
    suggested = suggest_tags(content, title=title)

    new_tags = []
    for t in suggested:
        if t not in existing_tags:
            new_tags.append(t)

    if not new_tags:
        return {"path": path, "tags": existing_tags, "modified": False}

    if not dry_run:
        all_tags = existing_tags + new_tags
        updated = _update_frontmatter(content, all_tags)
        fpath.write_text(updated, encoding="utf-8")

    return {"path": path, "tags": existing_tags + new_tags, "added": new_tags, "modified": not dry_run}


def tag_all(dry_run: bool = True) -> list[dict]:
    """Tag all untagged files in wiki/concepts and wiki/entities."""
    results = []
    for base_dir in ["wiki/concepts", "wiki/entities"]:
        target = BASE / base_dir
        if not target.exists():
            continue
        for f in sorted(target.glob("*.md")):
            rel = f.relative_to(BASE).as_posix()
            fm = _get_frontmatter(_read(f))
            has_tags = "tags" in fm and fm["tags"].strip("[]").strip()
            if not has_tags:
                results.append(tag_file(str(f), dry_run=dry_run))
    return results
