"""
KAOS Distill Engine v2 — Destilación automática raw/ → wiki/
Usa DeepSeek v4 Flash (via DSOL) para extracción semántica en vez de regex.
"""

import json
import re
import sys
from datetime import datetime, date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / ".memory" / "_scripts" / "lib"))

RAW_DIR = BASE / ".memory" / "raw"
CONCEPTS_DIR = BASE / ".memory" / "wiki" / "concepts"
SOURCES_DIR = BASE / ".memory" / "wiki" / "sources"
ENTITIES_DIR = BASE / ".memory" / "wiki" / "entities"
INDEX_PATH = BASE / ".memory" / "wiki" / "index.md"
LOG_PATH = BASE / ".memory" / "wiki" / "log.md"

import hashlib

DSOL_CACHE_FILE = BASE / ".memory" / "cache" / "dsol-cache.json"

# Try to import DSOL
try:
    from dsol import build_prompt, configure_thinking, get_output_config, allocate
    try:
        from dsol import call_structured as dsol_call_structured
    except ImportError:
        dsol_call_structured = None
    HAS_DSOL = True
except ImportError:
    HAS_DSOL = False
    dsol_call_structured = None

# Try to import synapse (optional)
try:
    from synapse import cross_link
    HAS_SYNAPSE = True
except ImportError:
    HAS_SYNAPSE = False


def _dsol_cache_key(content: str) -> str:
    return hashlib.sha256(content[:1000].encode("utf-8")).hexdigest()[:16]


def _dsol_cache_get(key: str) -> dict | None:
    if DSOL_CACHE_FILE.exists():
        try:
            cache = json.loads(DSOL_CACHE_FILE.read_text(encoding="utf-8"))
            return cache.get(key)
        except Exception:
            pass
    return None


def _dsol_cache_set(key: str, result: dict):
    DSOL_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache = {}
    if DSOL_CACHE_FILE.exists():
        try:
            cache = json.loads(DSOL_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    cache[key] = result
    DSOL_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _call_dsol(task: str, content: str, use_json: bool = True) -> dict | str:
    """Call DeepSeek via DSOL for structured extraction. Uses cache."""
    if not HAS_DSOL or dsol_call_structured is None:
        return {"error": "DSOL not available", "fallback": True}

    # Check cache
    cache_key = _dsol_cache_key(content)
    cached = _dsol_cache_get(cache_key)
    if cached and cached.get("task") == task:
        return cached["result"]

    result = dsol_call_structured(task, content, model="flash", use_json=use_json)

    if isinstance(result, dict) and "error" in result:
        return result

    # Cache successful results
    _dsol_cache_set(cache_key, {"task": task, "result": result})

    if use_json and isinstance(result, dict):
        return result

    return result


def extract_entities_llm(content: str) -> list[dict]:
    """NER con DSOL — extrae entidades. Valida resultado, fallback a regex si es necesario."""
    if HAS_DSOL:
        result = _call_dsol("extract_entities", content, use_json=True)
        if isinstance(result, dict) and "entities" in result:
            entities = result["entities"]
            if isinstance(entities, list) and len(entities) > 0:
                return entities
        if isinstance(result, dict) and result.get("fallback"):
            pass  # DSOL falló silenciosamente
    return extract_entities_fallback(content)


def extract_concepts_llm(content: str) -> list[dict]:
    """Extracción semántica de conceptos con DSOL. Valida resultado."""
    if HAS_DSOL:
        result = _call_dsol("extract_concepts", content, use_json=True)
        if isinstance(result, dict) and "concepts" in result:
            concepts = result["concepts"]
            if isinstance(concepts, list) and len(concepts) > 0:
                return concepts
    return extract_concepts_fallback(content)


def extract_entities_fallback(content: str) -> list[dict]:
    """Fallback basado en regex (mantiene compatibilidad)."""
    entities = []
    for entity_file in ENTITIES_DIR.glob("*.md"):
        entity_name = entity_file.stem
        if entity_name.lower() in content.lower():
            entities.append({"name": entity_name, "confidence": "media"})
    return entities


def extract_concepts_fallback(content: str) -> list[dict]:
    """Fallback original basado en bold text."""
    stop_words = {"resumen ejecutivo", "introducción", "conclusiones", "fuentes",
                  "metodología", "hallazgos", "análisis", "recomendaciones",
                  "estado", "contexto", "resultados", "discusión",
                  "auditoría de configuración actual", "dominio", "fecha",
                  "investigador", "resumen", "investigación", "prioridad"}
    concepts = []
    body_start = content.find("\n---\n", content.find("---") + 4)
    body = content[body_start + 5:] if body_start > 0 else content
    for line in body.split("\n"):
        for match in re.findall(r"\*\*([^*]+)\*\*", line):
            clean = match.strip().strip(".:,")
            if (len(clean) > 3 and len(clean) < 50 and
                clean.lower() not in stop_words and
                not clean[0].isdigit()):
                concepts.append({"name": clean, "confidence": "low"})
    seen = set()
    unique = []
    for c in concepts:
        key = c["name"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique[:6]


def extract_sources(content: str) -> list[dict]:
    """Extrae fuentes del contenido (URLs)."""
    urls = re.findall(r"(https?://[^\s\)\)]+)", content)
    seen = set()
    sources = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            slug = url.split("/")[-1].split("?")[0][:40]
            sources.append({"url": url, "slug": slug})
    return sources


def clean_slug(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")[:60]


def classify_research(content: str) -> str:
    """Clasifica el tipo de investigación para perfil de pipeline."""
    keywords = {
        "deep": ["investigación profunda", "deep research", "multi-query", "exhaustivo",
                 "sistemático", "comprehensive", "recursivo", "iterativo"],
        "flash": ["quick", "rápido", "brief", "fact-check", "verificación", "simple"],
        "massive": ["lista de", "todos los", "catálogo", "inventario", "completo"],
    }
    content_lower = content.lower()
    for profile, kws in keywords.items():
        for kw in kws:
            if kw in content_lower:
                return profile
    return "standard"


def create_concept_page(slug: str, title: str, snippet: str, raw_ref: str) -> Path | None:
    """Crea página en wiki/concepts/."""
    CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)
    clean = clean_slug(slug)
    path = CONCEPTS_DIR / f"{clean}.md"
    if path.exists():
        return None
    page = (f"---\ntype: concept\nsource: {raw_ref}\nauto-distilled: true\n"
            f"distill-engine: v2\n---\n\n# {title}\n\n"
            f"*Destilado automáticamente desde {raw_ref}*\n\n"
            f"{snippet[:500]}\n\n## Fuente\n- [{raw_ref}](../raw/{raw_ref})\n")
    path.write_text(page, encoding="utf-8")
    return path


def create_source_page(slug: str, url: str, raw_ref: str) -> Path | None:
    """Crea página en wiki/sources/."""
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    clean = clean_slug(slug)
    path = SOURCES_DIR / f"{clean}.md"
    if path.exists():
        return None
    page = (f"---\ntype: source\ncategory: web\nurl: {url}\nsource: {raw_ref}\n"
            f"confidence: media\n---\n\nFuente referenciada en [{raw_ref}](../raw/{raw_ref}).\n")
    path.write_text(page, encoding="utf-8")
    return path


def append_to_index(entry_type: str, name: str, description: str) -> None:
    if not INDEX_PATH.exists():
        return
    content = INDEX_PATH.read_text(encoding="utf-8")
    section_map = {"concept": "## Conceptos\n\n", "source": "## Fuentes\n\n"}
    marker = section_map.get(entry_type)
    clean_name = clean_slug(name)
    if marker and marker in content:
        new_entry = f"- [{clean_name}]({entry_type}s/{clean_name}.md) - {description}\n"
        if new_entry not in content:
            content = content.replace(marker, marker + new_entry)
            INDEX_PATH.write_text(content, encoding="utf-8")


def append_to_log(raw_name: str, created_files: list) -> None:
    if not LOG_PATH.exists():
        return
    files_str = ", ".join([str(f.relative_to(BASE)) for f in created_files if f])
    entry = f"\n## [{date.today().isoformat()}] distill-v2 | raw → wiki\n- raw/{raw_name}.md → {files_str}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(entry)


def distill_file(raw_path: Path) -> list[Path]:
    """Procesa un archivo raw/ y crea páginas wiki/ usando LLM o fallback."""
    content = raw_path.read_text(encoding="utf-8")
    slug = raw_path.stem
    raw_ref = raw_path.name

    # Extract title
    title = ""
    for line in content.split("\n"):
        if line.startswith("# ") and not line.startswith("## "):
            title = line[2:].strip()
            break
    if not title:
        title = slug.replace("-", " ").title()

    created = []

    # Try LLM extraction first, fallback to regex
    concepts = extract_concepts_llm(content)
    entities = extract_entities_llm(content)

    # Create concept pages
    for concept in concepts[:5]:
        name = concept.get("name", str(concept)) if isinstance(concept, dict) else str(concept)
        concept_slug = name.lower().replace(" ", "-").replace(":", "")[:50]
        snippet = ""
        for line in content.split("\n"):
            if name.lower() in line.lower():
                snippet = line[:200]
                break
        path = create_concept_page(concept_slug, name, snippet, raw_ref)
        if path:
            created.append(path)
            append_to_index("concept", concept_slug, name[:60])

    # Create source pages
    sources = extract_sources(content)
    for source in sources[:5]:
        source_slug = f"{slug}-{source['slug']}"[:50]
        path = create_source_page(source_slug, source["url"], raw_ref)
        if path:
            created.append(path)
            append_to_index("source", source_slug, source["url"][:60])

    # Run synapse if available (cross-link each created page)
    if HAS_SYNAPSE and created:
        for c in concepts[:3]:
            name = c.get("name", str(c)) if isinstance(c, dict) else str(c)
            concept_slug = clean_slug(name)
            try:
                cross_link(concept_slug)
            except Exception:
                pass

    if created:
        append_to_log(slug, created)
        print(f"  ✅ {raw_ref}: {len(created)} páginas creadas")
    else:
        print(f"  ⏭️  {raw_ref}: ya destilado")

    return created


def list_raw_files():
    """Lista archivos .md en raw/ que no tienen página wiki/ asociada."""
    files = list(RAW_DIR.glob("*.md"))
    return [f for f in files if not has_wiki_page(f)]


def has_wiki_page(raw_path: Path) -> bool:
    """Verifica si ya hay conceptos de esta investigación."""
    slug = raw_path.stem
    manual_concepts = {"add-only-extraction", "compile-then-query", "memory-blocks",
                       "per-agent-mcp-restriction", "pipeline-conocimiento-raw-wiki",
                       "estado-memoria-sesion", "llm-wiki", "hallazgos-clave",
                       "recomendacion-para-kaos"}
    for concept_file in CONCEPTS_DIR.glob("*.md"):
        name = concept_file.stem
        if name in manual_concepts:
            content = concept_file.read_text(encoding="utf-8")
            if slug in content:
                return True
    return False


def distill_all():
    """Destila todas las investigaciones raw/ sin página wiki/."""
    files = list_raw_files()
    if not files:
        print("No hay investigaciones pendientes de destilar.")
        return []
    print(f"Destilando {len(files)} investigaciones (v2)...")
    all_created = []
    for f in files:
        all_created.extend(distill_file(f))
    return all_created


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="KAOS Distill Engine v2")
    parser.add_argument("mode", nargs="?", default="all", choices=["all", "file"])
    parser.add_argument("--new-only", action="store_true", help="Solo destilar archivos sin wiki asociada")
    parser.add_argument("--slug", default="", help="Nombre del archivo raw/ (modo file)")
    args = parser.parse_args()
    mode = args.mode
    if mode == "all":
        if args.new_only:
            files = list_raw_files()
            if not files:
                print("No hay investigaciones pendientes de destilar.")
                sys.exit(0)
            print(f"Destilando {len(files)} investigaciones nuevas...")
            all_created = []
            for f in files:
                all_created.extend(distill_file(f))
        else:
            all_created = distill_all()
        # Auto-build embeddings after distill (synapse already ran per-file in distill_file)
        try:
            vault_py = Path(__file__).resolve().parent.parent / ".memory/_scripts/vault.py"
            import subprocess
            print("  Construyendo embeddings semánticos...")
            r = subprocess.run([sys.executable, str(vault_py), "embeddings", "build"], timeout=120, capture_output=True, text=True)
            if r.returncode == 0:
                print(f"  Embeddings construidos ✅ ({r.stdout.strip()[:100]})")
            else:
                print(f"  Embeddings: {r.stderr.strip()[:200]}")
        except subprocess.TimeoutExpired:
            print("  Embeddings: timeout (120s) — continuando")
        except Exception as e:
            print(f"  Embeddings: error {e}")
    elif mode == "file" and args.slug:
        path = RAW_DIR / args.slug
        if path.exists():
            distill_file(path)
        else:
            print(f"File not found: {path}")
    elif mode == "classify" and len(sys.argv) > 2:
        path = RAW_DIR / sys.argv[2]
        if path.exists():
            profile = classify_research(path.read_text(encoding="utf-8"))
            print(f"Classified as: {profile}")
    else:
        print(f"Usage: py distill.py [all|file <name.md>|classify <name.md>]")
