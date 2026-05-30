"""kosmos/nodes.py — Pipeline node implementations for KosmosV2.

Contains the 8 node methods (discover → validate) and all helper functions
extracted from the original kosmos_node_v2.py monolith.

Each node function accepts ``self`` so it can be assigned as a method of
KosmosPipelineV2 and work correctly with instance state.
"""

import glob
import json
import logging
import os
import re
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Vault / project paths (adjusted for lib/kosmos/nodes.py location) ──
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent  # .memory/_scripts/
_MEMORY_DIR = _SCRIPTS_DIR.parent  # .memory/
_VAULT_ROOT = _MEMORY_DIR.parent  # KAOS/
_PIPELINE_DIR = _MEMORY_DIR / "_pipeline"
_RAW_DIR = _PIPELINE_DIR / "raw"
_SCHEMA_DIR = _MEMORY_DIR / "schema"
_CACHE_DIR = _MEMORY_DIR / "cache"


# ═══════════════════════════════════════════════════════════════════════
# Helper: filesystem scanning
# ═══════════════════════════════════════════════════════════════════════

def _depwire_scan(paths: List[str]) -> Dict[str, Any]:
    """Attempt to run depwire scan via MCP or subprocess.

    Gracefully degrades to a filesystem-level dependency scan using
    Python's ``ast`` and ``glob`` modules.

    Args:
        paths: List of directory paths to scan.

    Returns:
        Dict with keys: files, imports, structure, tool_available.
    """
    result: Dict[str, Any] = {
        "files": [],
        "imports": {},
        "graph": {"nodes": [], "edges": []},
        "tool_available": False,
        "note": "",
        "error": None,
    }

    # Try MCP depwire (tool only available inside OpenCode agent)
    try:
        import subprocess as _sp
        safe_paths = [shlex.quote(str(p)) for p in paths if Path(p).exists()]
        if not safe_paths:
            raise FileNotFoundError("No valid paths for depwire scan")
        proc = _sp.run(
            ["depwire", "--json", "scan"] + safe_paths,
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout)
            result.update(data)
            result["tool_available"] = True
            result["note"] = "depwire CLI scan"
            return result
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        logger.debug("depwire CLI not available: %s", exc)

    # Fallback: filesystem-level scan
    logger.info("depwire not available — using filesystem scan fallback")
    py_files: List[Path] = []
    for p in paths:
        base = Path(p)
        if base.is_dir():
            py_files.extend(base.rglob("*.py"))
            py_files.extend(base.rglob("*.js"))
            py_files.extend(base.rglob("*.ts"))
            py_files.extend(base.rglob("*.json"))
        elif base.is_file():
            py_files.append(base)

    # Limit to avoid huge scans
    py_files = py_files[:200]

    # Extract imports from Python files (simple regex, not ast for speed)
    import_re: Dict[str, int] = {}
    for f in py_files[:100]:  # limit to 100 files
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r'^(?:from|import)\s+(\S+)', text, re.MULTILINE):
                module = m.group(1).split(".")[0]
                import_re[module] = import_re.get(module, 0) + 1
        except (OSError, IOError):
            pass

    result["files"] = [str(f) for f in py_files]
    result["imports"] = import_re
    result["graph"]["nodes"] = [str(f) for f in py_files[:50]]
    result["note"] = f"filesystem scan: {len(py_files)} files, {len(import_re)} unique imports"
    return result


def _depwire_health_score(paths: List[str]) -> Dict[str, Any]:
    """Compute health score for a codebase.

    Args:
        paths: List of paths to evaluate.

    Returns:
        Dict with health_score, metrics, and tool_available flag.
    """
    result: Dict[str, Any] = {
        "health_score": 0.0,
        "metrics": {},
        "tool_available": False,
        "error": None,
    }

    # Try depwire CLI
    try:
        import subprocess as _sp
        safe_paths = [shlex.quote(str(p)) for p in paths if Path(p).exists()]
        if not safe_paths:
            raise FileNotFoundError("No valid paths for depwire health")
        proc = _sp.run(
            ["depwire", "--json", "health"] + safe_paths,
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout)
            result.update(data)
            result["tool_available"] = True
            return result
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        logger.debug("depwire health CLI not available: %s", exc)

    # Fallback: basic metrics
    logger.info("depwire health not available — computing heuristic metrics")
    total_files = 0
    total_lines = 0
    for p in paths:
        base = Path(p)
        if base.is_dir():
            for f in base.rglob("*.py"):
                total_files += 1
                try:
                    lines = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
                    total_lines += lines
                except (OSError, IOError):
                    pass

    # Heuristic health score based on file/line distribution
    if total_files == 0:
        health = 0.0
    elif total_files < 5:
        health = 30.0  # very small project
    elif total_files < 20:
        health = 60.0
    elif total_lines < 100:
        health = 40.0  # many files but tiny
    else:
        # Better health with more files (indicates modularity)
        avg_lines = total_lines / max(total_files, 1)
        if 10 <= avg_lines <= 200:
            health = 85.0  # good module size
        elif avg_lines > 500:
            health = 55.0  # files may be too large
        else:
            health = 70.0

    result["health_score"] = round(health, 1)
    result["metrics"] = {
        "total_files": total_files,
        "total_lines": total_lines,
        "avg_lines_per_file": round(total_lines / max(total_files, 1), 1),
    }
    result["note"] = "heuristic fallback (depwire not available)"
    return result


def _depwire_simulate_change(paths: List[str], change_desc: str = "") -> Dict[str, Any]:
    """Simulate the impact of a change on the codebase.

    Args:
        paths: Paths potentially affected.
        change_desc: Description of the proposed change.

    Returns:
        Dict with impact analysis.
    """
    result: Dict[str, Any] = {
        "impacted_files": [],
        "impact_score": 0.0,
        "suggestions": [],
        "tool_available": False,
        "error": None,
    }

    try:
        import subprocess as _sp
        safe_paths = [shlex.quote(str(p)) for p in paths if Path(p).exists()]
        if not safe_paths:
            raise FileNotFoundError("No valid paths for depwire simulate")
        proc = _sp.run(
            ["depwire", "--json", "simulate", shlex.quote(str(change_desc))] + safe_paths,
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout)
            result.update(data)
            result["tool_available"] = True
            return result
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        logger.debug("depwire simulate not available: %s", exc)

    # Fallback: list files that might be impacted
    impacted = []
    for p in paths:
        base = Path(p)
        if base.exists():
            impacted.append(str(base))
            if base.is_dir():
                impacted.extend([str(f) for f in base.rglob("*.py")][:20])

    result["impacted_files"] = impacted
    result["impact_score"] = min(100.0, len(impacted) * 2.0)
    result["suggestions"] = ["Fallback analysis: review impacted files manually"]
    result["note"] = "heuristic fallback (depwire not available)"
    return result


# ═══════════════════════════════════════════════════════════════════════
# Helper: Structurizr DSL generation
# ═══════════════════════════════════════════════════════════════════════

def _generate_structurizr_dsl(architecture: Dict[str, Any]) -> str:
    """Generate Structurizr DSL from an architecture description.

    Args:
        architecture: Dict with system_name, containers, relationships.

    Returns:
        Valid Structurizr DSL string.
    """
    system_name = architecture.get("system_name", "KAOS System")
    containers = architecture.get("containers", [])
    relationships = architecture.get("relationships", [])
    tags = architecture.get("tags", "")

    dsl = f'workspace "{system_name}" {{\n'
    dsl += f'    model {{\n'
    dsl += f'        {system_name} = softwareSystem "{system_name}" {{\n'
    dsl += f'            tags "{tags}"\n' if tags else ""

    # Context-level: add software systems and persons
    external_systems = architecture.get("external_systems", [])
    for ext in external_systems:
        name = ext.get("name", "ExternalSystem")
        desc = ext.get("description", "")
        dsl += f'            {name} = softwareSystem "{name}" "{desc}"\n'

    # Container-level
    for container in containers:
        name = container.get("name", "Container")
        tech = container.get("technology", "")
        desc = container.get("description", "")
        dsl += f'            {name} = container "{name}" "{desc}" "{tech}"\n'

    dsl += f'        }}\n'

    # Relationships between containers
    rel_map: Dict[Tuple[str, str], str] = {}
    for rel in relationships:
        src = rel.get("source", "")
        dst = rel.get("destination", "")
        label = rel.get("label", "uses")
        tech = rel.get("technology", "")
        key = (src, dst)
        if key not in rel_map:
            rel_map[key] = label
            dsl += f'        {src} -> {dst} "{label}"'
            if tech:
                dsl += f' <<{tech}>>'
            dsl += '\n'

    # External system relationships
    for ext in external_systems:
        ext_name = ext.get("name", "")
        ext_rels = ext.get("relationships", [])
        for rel in ext_rels:
            target = rel.get("target", "")
            label = rel.get("label", "uses")
            dsl += f'        {ext_name} -> {target} "{label}"\n'

    dsl += '    }\n'

    # Views
    dsl += '    views {\n'
    dsl += f'        systemcontext {system_name} {{\n'
    dsl += '            include *\n'
    dsl += '            autoLayout\n'
    dsl += '        }\n'
    if containers:
        dsl += f'        container {system_name} {{\n'
        dsl += '            include *\n'
        dsl += '            autoLayout\n'
        dsl += '        }\n'
    dsl += '    }\n'
    dsl += '}\n'

    return dsl


def _generate_mermaid_diagram(diagram_type: str, data: Dict[str, Any]) -> str:
    """Generate a Mermaid diagram from structured data.

    Args:
        diagram_type: One of 'graph', 'flowchart', 'classDiagram', 'c4context'.
        data: Dict with nodes, edges, title.

    Returns:
        Mermaid diagram string.
    """
    title = data.get("title", "Architecture Diagram")
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    if diagram_type == "c4context":
        lines = ["graph TB"]
        lines.append(f'    title[{title}]')
        # System
        system = data.get("system", "System")
        lines.append(f'    System[{system}]')
        # External actors
        for actor in data.get("actors", []):
            name = actor.get("name", "Actor")
            rel = actor.get("relationship", "uses")
            lines.append(f'    Actor_{name}[{name}]')
            lines.append(f'    Actor_{name} -->|{rel}| System')
        # Containers
        for container in data.get("containers", []):
            c_name = container.get("name", "Container")
            c_tech = container.get("technology", "")
            c_label = f'{c_name}\\n[{c_tech}]' if c_tech else c_name
            lines.append(f'    C_{c_name}[{c_label}]')
            lines.append(f'    System -->|contains| C_{c_name}')
        # Container relationships
        for edge in data.get("container_edges", []):
            src = edge.get("source", "")
            dst = edge.get("destination", "")
            label = edge.get("label", "uses")
            lines.append(f'    C_{src} -->|{label}| C_{dst}')
        return "\n".join(lines)

    if diagram_type in ("graph", "flowchart"):
        direction = data.get("direction", "TB")
        lines = [f"graph {direction}"]
        if title:
            lines.append(f'    title[{title}]')

        for node in nodes:
            nid = node.get("id", "")
            nlabel = node.get("label", nid)
            nstyle = node.get("style", "")
            line = f'    {nid}[{nlabel}]'
            if nstyle:
                line += f' :::{nstyle}'
            lines.append(line)

        for edge in edges:
            src = edge.get("source", "")
            dst = edge.get("destination", "")
            label = edge.get("label", "")
            if label:
                lines.append(f'    {src} -->|{label}| {dst}')
            else:
                lines.append(f'    {src} --> {dst}')

        return "\n".join(lines)

    if diagram_type == "classDiagram":
        lines = ["classDiagram"]
        lines.append(f'    title {title}')
        for cls in nodes:
            cid = cls.get("id", "Class")
            lines.append(f'    class {cid} {{')
            for attr in cls.get("attributes", []):
                lines.append(f'        +{attr}')
            for method in cls.get("methods", []):
                lines.append(f'        +{method}()')
            lines.append('    }')
        for edge in edges:
            src = edge.get("source", "")
            dst = edge.get("destination", "")
            rel = edge.get("relationship", "-->")
            lines.append(f'    {src} {rel} {dst}')
        return "\n".join(lines)

    return f'%% Unsupported diagram type: {diagram_type}'


# ═══════════════════════════════════════════════════════════════════════
# Helper: ADR template generation
# ═══════════════════════════════════════════════════════════════════════

def _generate_adr_template(state: Dict[str, Any]) -> str:
    """Generate a complete ADR document from pipeline state.

    Uses L0 memory for cross-references if available.

    Args:
        state: Pipeline state dict with topic, aletheia_output, discovery, etc.

    Returns:
        Complete ADR markdown text with frontmatter and sections.
    """
    topic = state.get("topic", "Untitled Architecture Decision")
    decision_id = state.get("adr_id", "ADR-XXX")
    slug = re.sub(r'[^a-z0-9]+', '-', topic.lower())[:40]
    discovery = state.get("discovery", {})
    analysis = state.get("analyze", {})
    health = analysis.get("health", {})
    quality_scores = state.get("quality", {}).get("scores", {})

    # Build frontmatter
    tags_list = state.get("tags", ["adr", "architecture"])
    tags_str = ", ".join(f'"{t}"' for t in tags_list)
    refs = state.get("adr_references", [])
    refs_str = ", ".join(f'"{r}"' for r in refs)

    lines = ["---"]
    lines.append(f"id: {decision_id}")
    lines.append(f'title: "{topic}"')
    lines.append("status: proposed")
    lines.append(f"date: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"tags: [{tags_str}]")
    lines.append("responsible: kosmos")
    lines.append("validator: kratos")
    if refs:
        lines.append(f"related_adrs: [{refs_str}]")
    lines.append("---")
    lines.append("")
    lines.append(f"# {decision_id}: {topic}")
    lines.append("")

    # Context section
    aletheia_output = state.get("aletheia_output", "") or ""
    context_problems = discovery.get("problems", [
        "El sistema actual carece de documentación arquitectónica formal",
        "Las decisiones no tienen trazabilidad entre agentes",
        "No existe un repositorio centralizado de ADRs",
    ])
    lines.append("## Contexto")
    lines.append("")
    lines.append("### Problemas identificados")
    lines.append("")
    for i, problem in enumerate(context_problems, 1):
        lines.append(f"{i}. {problem}")
    lines.append("")

    # Options section
    options = state.get("options", [
        {"name": "Sistema FTS5 (L0)", "pros": ["Sin dependencias externas", "Rápido (<100ms por consulta)", "Suficiente para búsqueda textual"], "cons": ["Sin búsqueda semántica", "Requiere migración a L1+L2 en Fase 2"]},
        {"name": "Vector Store (L1)", "pros": ["Búsqueda semántica", "Embeddings reutilizables"], "cons": ["Requiere infraestructura", "Mayor latencia"]},
        {"name": "Architecture KG (L2)", "pros": ["Máxima expresividad", "Relaciones semánticas"], "cons": ["Complejidad operativa", "Sobredimensionado para Fase 1"]},
    ])
    lines.append("## Opciones Consideradas")
    lines.append("")
    for option in options:
        name = option.get("name", "Opción")
        lines.append(f"### {name}")
        lines.append("")
        lines.append("**Pros:**")
        for pro in option.get("pros", []):
            lines.append(f"- {pro}")
        lines.append("**Contras:**")
        for con in option.get("cons", []):
            lines.append(f"- {con}")
        lines.append("")

    # Decision section
    decision = state.get("decision", "Implementar un enfoque incremental comenzando con L0 (FTS5) como base de memoria arquitectónica, con planes de migrar a L1+L2 en fases posteriores.")
    decision_rationale = state.get("decision_rationale", "Esta decisión se basa en la necesidad de tener memoria funcional desde el día 1, minimizando dependencias externas y complejidad operativa.")
    lines.append("## Decisión")
    lines.append("")
    lines.append(decision)
    lines.append("")
    lines.append(decision_rationale)
    lines.append("")

    # Consequences
    lines.append("## Consecuencias")
    lines.append("")
    lines.append("### Positivas")
    for pos in state.get("consequences_positive", [
        "Memoria arquitectónica disponible inmediatamente",
        "Sin nuevas dependencias externas",
        "Base consolidada para Fase 2 y 3",
    ]):
        lines.append(f"- {pos}")
    lines.append("")
    lines.append("### Negativas")
    for neg in state.get("consequences_negative", [
        "Búsqueda semántica limitada hasta implementar L1",
        "Requiere re-indexación periódica de ADRs",
    ]):
        lines.append(f"- {neg}")
    lines.append("")

    # Quality scores
    if quality_scores:
        lines.append("## Scores de Calidad")
        lines.append("")
        lines.append("| Dimensión | Score |")
        lines.append("|-----------|-------|")
        for dim, score in quality_scores.items():
            lines.append(f"| {dim.capitalize()} | {score}/100 |")
        lines.append("")

    # References
    lines.append("## Referencias")
    lines.append("")
    if refs:
        for ref in refs:
            lines.append(f"- [[{ref}]]")
    if health:
        health_score = health.get("health_score", 0)
        lines.append(f"- Health Score del código base: {health_score}/100")
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# Helper: RDF triple generation
# ═══════════════════════════════════════════════════════════════════════

def _generate_rdf_triples(adr_data: Dict[str, Any]) -> List[str]:
    """Generate RDF triples (as NT-like strings) for the Architecture KG.

    Args:
        adr_data: Dict with adr_id, title, status, tags, related_adrs, etc.

    Returns:
        List of triple strings in NTriples-like format.
    """
    adr_id = adr_data.get("adr_id", "ADR-XXX")
    title = adr_data.get("title", "Untitled")
    status = adr_data.get("status", "proposed")
    tags = adr_data.get("tags", [])
    related = adr_data.get("related_adrs", [])

    triples = []

    # Namespace
    ns = "kaos:adr"
    rdf_type = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
    rdfs_label = "<http://www.w3.org/2000/01/rdf-schema#label>"

    # ADR instance
    adr_uri = f"<kaos://adr/{adr_id}>"
    triples.append(f"{adr_uri} {rdf_type} <kaos://ontology/ArchitectureDecisionRecord> .")
    triples.append(f'{adr_uri} {rdfs_label} "{title}" .')
    triples.append(f'{adr_uri} <kaos://ontology/status> "{status}" .')

    # Tags
    for tag in tags:
        tag = tag.strip().lower().replace(" ", "_")
        triples.append(f'{adr_uri} <kaos://ontology/tag> "{tag}" .')

    # Relationships to other ADRs
    for rel in related:
        rel_uri = f"<kaos://adr/{rel}>"
        triples.append(f"{adr_uri} <kaos://ontology/relatesTo> {rel_uri} .")
        triples.append(f"{rel_uri} <kaos://ontology/relatedFrom> {adr_uri} .")

    # Timestamp
    now = datetime.now().isoformat()
    triples.append(f'{adr_uri} <kaos://ontology/createdAt> "{now}" .')

    return triples


# ═══════════════════════════════════════════════════════════════════════
# Helper: cross-reference validation
# ═══════════════════════════════════════════════════════════════════════

def _validate_cross_references(
    adr_text: str, memory: Any
) -> Dict[str, Any]:
    """Validate cross-references in an ADR against L0 memory.

    Args:
        adr_text: The ADR text to validate.
        memory: ArchitectureMemoryL0 instance.

    Returns:
        Dict with validation results.
    """
    results = {
        "adr_references_found": [],
        "adr_references_valid": [],
        "adr_references_invalid": [],
        "wikilinks_found": [],
        "suggestions": [],
    }

    # Extract ADR references
    adr_refs = re.findall(r'ADR-\d+', adr_text)
    results["adr_references_found"] = list(set(adr_refs))

    # Extract wikilinks
    wikilinks = re.findall(r'\[\[([^\]]+)\]\]', adr_text)
    results["wikilinks_found"] = wikilinks

    # Validate against L0 if available
    if memory is not None:
        for ref in results["adr_references_found"]:
            # Search in memory
            hits = memory.search(ref, limit=1)
            if hits:
                results["adr_references_valid"].append(ref)
            else:
                results["adr_references_invalid"].append(ref)

        for wl in wikilinks:
            hits = memory.search(wl, limit=1)
            if not hits:
                results["suggestions"].append(
                    f"Wikilink [[{wl}]] no encontrado en L0 — verificar"
                )

    if not results["adr_references_found"]:
        results["suggestions"].append(
            "No se encontraron referencias a ADRs existentes — considerar agregar"
        )

    return results


# ═══════════════════════════════════════════════════════════════════════
# Static helpers for diagram validation
# ═══════════════════════════════════════════════════════════════════════

def _validate_diagram(diagram_text: str, diagram_name: str) -> Dict[str, Any]:
    """Validate a Mermaid diagram for minimum quality requirements.

    Checks:
    1. Has a title
    2. Has a legend or label
    3. Has at least 4 nodes
    4. Has at least 2 connections/edges
    5. Uses valid Mermaid syntax (graph TB, flowchart, etc.)

    Args:
        diagram_text: The Mermaid diagram text.
        diagram_name: Name for logging.

    Returns:
        Dict con keys: passed (bool), node_count (int), edge_count (int),
        issues (list).
    """
    issues: List[str] = []
    lines = diagram_text.strip().split("\n")

    # Check 1: Has proper Mermaid header
    has_header = any(
        line.strip().startswith(prefix)
        for line in lines
        for prefix in ["graph ", "flowchart ", "classDiagram", "sequenceDiagram"]
    )
    if not has_header:
        issues.append("No valid Mermaid header (graph/flowchart/classDiagram)")

    # Check 2: Count nodes (lines with [...] or (...))
    node_count = 0
    edge_count = 0
    for line in lines:
        stripped = line.strip()
        if "-->" in stripped or "---" in stripped:
            edge_count += 1
        elif "[" in stripped and "]" in stripped:
            node_count += 1
        elif "(" in stripped and ")" in stripped:
            node_count += 1

    # Check 3: Has a title or legend
    has_title = any(
        "title" in line.lower() or "legend" in line.lower()
        for line in lines
    )
    if not has_title:
        issues.append("No title or legend found in diagram")

    # Check 4: Minimum nodes
    if node_count < 4:
        issues.append(f"Too few nodes ({node_count} < 4 required)")

    # Check 5: Minimum edges
    if edge_count < 2:
        issues.append(f"Too few edges ({edge_count} < 2 required)")

    passed = len(issues) == 0
    logger.debug("Diagram '%s': nodes=%d, edges=%d, valid=%s", diagram_name, node_count, edge_count, passed)

    return {
        "passed": passed,
        "node_count": node_count,
        "edge_count": edge_count,
        "has_header": has_header,
        "has_title": has_title,
        "issues": issues,
        "diagram_name": diagram_name,
    }


def _generate_fallback_diagram(diagram_type: str, topic: str) -> str:
    """Generate a simplified fallback diagram when validation fails.

    Args:
        diagram_type: Type of diagram ('c4-context' or 'container').
        topic: The architecture topic.

    Returns:
        Simplified Mermaid diagram string.
    """
    slug = re.sub(r'[^a-z0-9]+', '_', topic.lower())[:20]

    if diagram_type == "c4-context":
        return f"""graph TB
    title[{topic} - Simplified Context]
    System[{slug}_system]
    Actor_User[User]
    Actor_Dev[Developer]
    C_Agent[Agent Orchestrator]
    C_Memory[Memory Store]
    C_Pipeline[Pipeline Executor]
    C_LLM[LLM Engine]

    Actor_User -->|interacts| System
    Actor_Dev -->|configures| System
    System -->|contains| C_Agent
    System -->|contains| C_Memory
    System -->|contains| C_Pipeline
    System -->|contains| C_LLM
    C_Agent -->|uses| C_Pipeline
    C_Pipeline -->|stores| C_Memory
    C_Agent -->|decides| C_LLM
"""

    # Container fallback
    return f"""graph LR
    title[{topic} - Simplified Containers]
    A[Agent Orchestrator]
    B[Memory Store]
    C[Pipeline Executor]
    D[LLM Interface]

    A -->|routes| C
    C -->|persists| B
    A -->|queries| D
    D -->|reads| B
"""


# ═══════════════════════════════════════════════════════════════════════
# Node 1: Discover
# ═══════════════════════════════════════════════════════════════════════

def discover(self) -> Dict[str, Any]:
    """Nodo 1: Discover — escanea el código base.

    Ejecuta depwire_scan (o fallback) sobre paths relevantes.
    Retorna grafo de dependencias, estructura de archivos, e imports.

    Returns:
        Dict with keys: files, imports, graph, problems, paths_scanned.
    """
    logger.info("▶️ Nodo 1: Discover")
    result: Dict[str, Any] = {
        "files": [],
        "imports": {},
        "graph": {"nodes": [], "edges": []},
        "problems": [],
        "paths_scanned": [],
        "tool_available": False,
        "node_time": datetime.now().isoformat(),
    }

    try:
        # Determine paths to scan
        scan_paths = [_SCRIPTS_DIR, _MEMORY_DIR]
        result["paths_scanned"] = [str(p) for p in scan_paths]

        scan_result = _depwire_scan(scan_paths)
        result["files"] = scan_result.get("files", [])
        result["imports"] = scan_result.get("imports", {})
        result["graph"] = scan_result.get("graph", {"nodes": [], "edges": []})
        result["tool_available"] = scan_result.get("tool_available", False)
        result["note"] = scan_result.get("note", "")

        # Infer problems from imports analysis
        imports = result["imports"]
        total_files = len(result["files"])
        if total_files > 0 and imports:
            problems = []
            if "sqlite3" in imports:
                problems.append("Uso de SQLite directo — considerar migrar a ORM si escala")
            if "subprocess" in imports:
                problems.append("Múltiples llamadas subprocess — centralizar en executor")
            if "json" in imports and "yaml" in imports:
                problems.append("Dos formatos de serialización — estandarizar a uno")
            if total_files > 100:
                problems.append(f"Alto volumen de archivos ({total_files}) — posible sobre-división de módulos")
            result["problems"] = problems

        logger.info("   Discover: %d files, %d imports", len(result["files"]), len(result["imports"]))

    except Exception as exc:
        logger.warning("   Discover failed: %s", exc)
        self.errors["discover"] = str(exc)
        result["error"] = str(exc)

    self.node_results["discover"] = result
    self.state["discovery"] = result
    return result


# ═══════════════════════════════════════════════════════════════════════
# Node 2: Model
# ═══════════════════════════════════════════════════════════════════════

def model(self) -> Dict[str, Any]:
    """Nodo 2: Model — genera modelo C4 (Contexto + Contenedor).

    Produce Structurizr DSL válido a partir del estado del pipeline.

    Returns:
        Dict with keys: dsl, system_name, containers, relationships,
        external_systems.
    """
    logger.info("▶️ Nodo 2: Model")
    result: Dict[str, Any] = {
        "dsl": "",
        "system_name": "KAOS System",
        "containers": [],
        "relationships": [],
        "external_systems": [],
        "node_time": datetime.now().isoformat(),
    }

    try:
        topic = self.state.get("topic", "KAOS System")
        system_name = topic if len(topic) < 40 else "KAOS System"

        # Build containers from discovery data
        discovery = self.state.get("discovery", {})
        imports = discovery.get("imports", {})

        # Map top imports to containers
        top_modules = sorted(imports.items(), key=lambda x: -x[1])[:8]
        containers = []
        for module, count in top_modules:
            containers.append({
                "name": module.capitalize(),
                "technology": "Python",
                "description": f"Módulo {module} ({count} referencias)",
            })

        # Ensure minimum containers
        if len(containers) < 2:
            containers = [
                {"name": "AgentOrchestrator", "technology": "Python", "description": "Orquestador de agentes"},
                {"name": "MemoryStore", "technology": "SQLite/FTS5", "description": "Almacenamiento de memoria arquitectónica"},
                {"name": "PipelineExecutor", "technology": "Python", "description": "Ejecutor del pipeline de agentes"},
                {"name": "DecisionEngine", "technology": "LLM", "description": "Motor de decisiones basado en LLM"},
            ]

        result["containers"] = containers

        # Generate relationships
        relationships = []
        if len(containers) >= 2:
            for i in range(len(containers) - 1):
                relationships.append({
                    "source": containers[i]["name"],
                    "destination": containers[i + 1]["name"],
                    "label": "uses",
                    "technology": "function call",
                })
        result["relationships"] = relationships

        # External systems
        result["external_systems"] = [
            {
                "name": "OpenCode",
                "description": "Plataforma de agentes subagent",
                "relationships": [{"target": "AgentOrchestrator", "label": "hosts agents"}],
            },
            {
                "name": "SQLite",
                "description": "Base de datos embebida para FTS5",
                "relationships": [{"target": "MemoryStore", "label": "storage backend"}],
            },
        ]

        # Generate DSL
        arch_data = {
            "system_name": system_name,
            "containers": containers,
            "relationships": relationships,
            "external_systems": result["external_systems"],
            "tags": "kaos,architecture,agent-system",
        }
        dsl = _generate_structurizr_dsl(arch_data)
        result["dsl"] = dsl

        logger.info("   Model: %d containers, %d relationships", len(containers), len(relationships))

    except Exception as exc:
        logger.warning("   Model failed: %s", exc)
        self.errors["model"] = str(exc)
        result["error"] = str(exc)

    self.node_results["model"] = result
    self.state["model"] = result
    return result


# ═══════════════════════════════════════════════════════════════════════
# Node 3: Analyze
# ═══════════════════════════════════════════════════════════════════════

def analyze(self) -> Dict[str, Any]:
    """Nodo 3: Analyze — análisis de impacto y health score.

    Ejecuta depwire health + simulate (o fallback) sobre el código base.

    Returns:
        Dict with keys: health, impact, suggestions.
    """
    logger.info("▶️ Nodo 3: Analyze")
    result: Dict[str, Any] = {
        "health": {},
        "impact": {},
        "suggestions": [],
        "node_time": datetime.now().isoformat(),
    }

    try:
        # Health score
        scan_paths = [_SCRIPTS_DIR, _MEMORY_DIR]
        health = _depwire_health_score(scan_paths)
        result["health"] = health

        # Simulate change
        topic = self.state.get("topic", "")
        impact = _depwire_simulate_change(scan_paths, change_desc=topic)
        result["impact"] = impact

        # Generate suggestions based on health
        health_score = health.get("health_score", 0)
        suggestions = []
        if health_score < 40:
            suggestions.append("Código base requiere reestructuración significativa")
        elif health_score < 60:
            suggestions.append("Consolidar módulos pequeños en paquetes coherentes")
        elif health_score < 80:
            suggestions.append("Mejora incremental: revisar dependencias circulares")
        else:
            suggestions.append("Código base saludable — mantener prácticas actuales")

        # Add impact-based suggestions
        impacted_count = len(impact.get("impacted_files", []))
        if impacted_count > 20:
            suggestions.append(f"Cambio de alto impacto ({impacted_count} archivos) — considerar enfoque gradual")
        elif impacted_count > 10:
            suggestions.append(f"Impacto moderado ({impacted_count} archivos) — planificar migración")

        result["suggestions"] = suggestions
        logger.info("   Analyze: health=%s, suggestions=%d", health_score, len(suggestions))

    except Exception as exc:
        logger.warning("   Analyze failed: %s", exc)
        self.errors["analyze"] = str(exc)
        result["error"] = str(exc)

    self.node_results["analyze"] = result
    self.state["analyze"] = result
    return result


# ═══════════════════════════════════════════════════════════════════════
# Node 4: Quality
# ═══════════════════════════════════════════════════════════════════════

def quality(self) -> Dict[str, Any]:
    """Nodo 4: Quality — evaluación dimensional del output.

    Evalúa el output arquitectónico en 5 dimensiones usando
    DimensionalEvaluator (heuristic, no DeepEval).
    Si ``skip_eval=True``, retorna metadata sin ejecutar el evaluador
    (la evaluación corre externamente en agent_executor).

    Returns:
        Dict with keys: scores, weighted_score, passed, evidences.
    """
    logger.info("▶️ Nodo 4: Quality")
    result: Dict[str, Any] = {
        "scores": {},
        "weighted_score": 0.0,
        "passed": False,
        "evidences": {},
        "node_time": datetime.now().isoformat(),
    }

    # G2: Skip evaluation if externally managed
    if self.skip_eval:
        logger.info("   Quality: SKIP_EVAL enabled — pipeline eval skipped (external eval will run)")
        result["skip_eval"] = True
        result["profile_used"] = self.state.get("profile", "standard")
        self.node_results["quality"] = result
        self.state["quality"] = result
        return result

    try:
        from lib.kosmos_evaluator_v2 import DimensionalEvaluator

        # Build text from current state for evaluation
        eval_text_parts = []

        # Topic
        topic = self.state.get("topic", "")
        if topic:
            eval_text_parts.append(f"# {topic}\n\n")

        # Aletheia output
        aletheia_out = self.state.get("aletheia_output", "")
        if aletheia_out and len(aletheia_out) > 50:
            eval_text_parts.append(aletheia_out[:2000])

        # Discovery results
        discovery = self.state.get("discovery", {})
        if discovery.get("files"):
            eval_text_parts.append(f"Files scanned: {len(discovery['files'])}\n")
            eval_text_parts.append(f"Imports: {json.dumps(discovery.get('imports', {}), indent=2)[:500]}\n")

        # Model DSL
        model_data = self.state.get("model", {})
        if model_data.get("dsl"):
            eval_text_parts.append(f"Structurizr DSL:\n{model_data['dsl'][:500]}\n")

        eval_text = "\n".join(eval_text_parts)
        if len(eval_text) < 50:
            eval_text = f"# {topic or 'Architecture Analysis'}\n\nPending architectural analysis for topic."

        evaluator = DimensionalEvaluator(profile=self.state.get("profile", "standard"))
        eval_result = evaluator.evaluate(eval_text)

        result["scores"] = eval_result.scores
        result["weighted_score"] = eval_result.weighted_score
        result["passed"] = eval_result.passed
        result["evidences"] = eval_result.evidences
        result["profile_used"] = eval_result.profile_used

        logger.info(
            "   Quality: composite=%s, passed=%s",
            eval_result.weighted_score, eval_result.passed
        )

    except Exception as exc:
        logger.warning("   Quality failed: %s", exc)
        self.errors["quality"] = str(exc)
        result["error"] = str(exc)

    self.node_results["quality"] = result
    self.state["quality"] = result
    return result


# ═══════════════════════════════════════════════════════════════════════
# Node 5: Visualize
# ═══════════════════════════════════════════════════════════════════════

def visualize(self) -> Dict[str, Any]:
    """Nodo 5: Visualize — genera diagramas C4 obligatorios con validación.

    Produce SIEMPRE diagramas C4 (Contexto y Contenedor) en formato Mermaid.
    Valida que los diagramas tengan título, leyenda, y ≥4 nodos.
    Si la validación falla, intenta regenerar con fallback a diagrama simplificado.
    Guarda los diagramas en ``.memory/_pipeline/raw/diagrams/``.

    Returns:
        Dict with keys: mermaid_diagrams, diagram_paths, validation, node_time.
    """
    logger.info("▶️ Nodo 5: Visualize (C4 obligatorio)")
    result: Dict[str, Any] = {
        "mermaid_diagrams": [],
        "diagram_paths": [],
        "validation": {"passed": False, "checks": []},
        "fallback_used": False,
        "node_time": datetime.now().isoformat(),
    }

    try:
        topic = self.state.get("topic", "Architecture")
        slug = re.sub(r'[^a-z0-9]+', '-', topic.lower())[:40]
        discovery = self.state.get("discovery", {})
        model_data = self.state.get("model", {})
        containers = model_data.get("containers", [])
        external_systems = model_data.get("external_systems", [])

        # Ensure minimum containers for C4 validity
        if len(containers) < 3:
            containers = [
                {"name": "AgentOrchestrator", "technology": "Python", "description": "Orquestador de agentes"},
                {"name": "MemoryStore", "technology": "SQLite/FTS5", "description": "Almacenamiento de memoria arquitectónica"},
                {"name": "PipelineExecutor", "technology": "Python", "description": "Ejecutor del pipeline de agentes"},
                {"name": "DecisionEngine", "technology": "LLM", "description": "Motor de decisiones basado en LLM"},
            ]

        # ── Diagram 1: C4 Context ──
        c4_data = {
            "title": f"{topic} — C4 Context Diagram",
            "system": topic[:30],
            "actors": [
                {"name": "Developer", "relationship": "uses"},
                {"name": "Operator", "relationship": "configures"},
                {"name": "User", "relationship": "interacts with"},
            ],
            "containers": containers,
            "container_edges": model_data.get("relationships", []),
        }
        c4_diagram = _generate_mermaid_diagram("c4context", c4_data)

        # ── Diagram 2: C4 Container (dependency graph) ──
        imports = discovery.get("imports", {})
        top_imports = sorted(imports.items(), key=lambda x: -x[1])[:10]
        graph_nodes = []
        for module, count in top_imports:
            graph_nodes.append({"id": module, "label": f"{module} ({count})"})
        graph_edges = []
        if len(top_imports) >= 2:
            for i in range(len(top_imports) - 1):
                graph_edges.append({
                    "source": top_imports[i][0],
                    "destination": top_imports[i + 1][0],
                    "label": f"{top_imports[i+1][1]} refs",
                })

        dep_data = {
            "title": f"{topic} — C4 Container Diagram",
            "direction": "LR",
            "nodes": graph_nodes,
            "edges": graph_edges,
        }
        dep_diagram = _generate_mermaid_diagram("graph", dep_data)

        # ── Validate diagrams ──
        validation_checks = []
        diagrams_to_save = []

        for d_name, d_content in [("c4-context", c4_diagram), ("container", dep_diagram)]:
            checks = self._validate_diagram(d_content, d_name)
            validation_checks.append({f"{d_name}_validation": checks})
            if checks.get("passed", False):
                diagrams_to_save.append((d_name, d_content))
            else:
                logger.warning("   Diagram '%s' validation failed: %s", d_name, checks.get("issues", []))
                # Fallback: generate simplified diagram
                simplified = self._generate_fallback_diagram(d_name, topic)
                fallback_checks = self._validate_diagram(simplified, f"{d_name}-fallback")
                validation_checks.append({f"{d_name}_fallback_validation": fallback_checks})
                diagrams_to_save.append((f"{d_name}-fallback", simplified))
                result["fallback_used"] = True

        # ── Save diagrams ──
        diagrams_dir = _RAW_DIR / "diagrams"
        diagrams_dir.mkdir(parents=True, exist_ok=True)

        for d_name, d_content in diagrams_to_save:
            d_path = diagrams_dir / f"{slug}-{d_name}.mmd"
            d_path.write_text(d_content, encoding="utf-8")
            result["diagram_paths"].append(str(d_path))
            result["mermaid_diagrams"].append({
                "type": d_name,
                "path": str(d_path),
                "content": d_content,
            })

        # Compute overall validation
        all_passed = all(
            c.get(list(c.keys())[0], {}).get("passed", False)
            for c in validation_checks
        )
        result["validation"] = {
            "passed": all_passed,
            "checks": validation_checks,
            "total_diagrams": len(diagrams_to_save),
        }

        # Register diagrams in state for downstream nodes
        self.state["kosmos_diagrams"] = result["diagram_paths"]

        logger.info("   Visualize: %d diagrams saved (validation=%s, fallback=%s)",
                    len(result["diagram_paths"]), all_passed, result["fallback_used"])

    except Exception as exc:
        logger.warning("   Visualize failed: %s", exc)
        self.errors["visualize"] = str(exc)
        result["error"] = str(exc)

    self.node_results["visualize"] = result
    self.state["visualize"] = result
    return result


# ═══════════════════════════════════════════════════════════════════════
# Node 6: Document
# ═══════════════════════════════════════════════════════════════════════

def document(self) -> Dict[str, Any]:
    """Nodo 6: Document — redacta el ADR completo y lo indexa en L1.

    Genera un ADR con frontmatter YAML, contexto, opciones,
    decisión, consecuencias, scores, y referencias cruzadas.
    Usa L0 para buscar ADRs relacionados.
    Indexa automáticamente el ADR en L1 (txtai) tras generarlo.

    Returns:
        Dict with keys: adr_text, adr_id, filepath, references,
        l1_index_status.
    """
    logger.info("▶️ Nodo 6: Document")
    result: Dict[str, Any] = {
        "adr_text": "",
        "adr_id": "ADR-XXX",
        "filepath": "",
        "references": [],
        "l1_index_status": "",
        "node_time": datetime.now().isoformat(),
    }

    try:
        topic = self.state.get("topic", "Architecture Decision")
        slug = re.sub(r'[^a-z0-9]+', '-', topic.lower())[:40]

        # Assign ADR ID
        if self.memory is not None:
            stats = self.memory.get_stats()
            total = stats.get("total_adrs", 0)
            adr_number = total + 19  # offset for existing ADRs
        else:
            adr_number = 19
        adr_id = f"ADR-{adr_number:03d}"
        result["adr_id"] = adr_id

        # Gather references from L0
        refs: List[str] = []
        if self.memory is not None:
            related = self.memory.search(topic, limit=5)
            for r in related:
                ref_id = re.search(r'(ADR-\d+)', r.get("title", ""))
                if ref_id:
                    refs.append(ref_id.group(1))
        result["references"] = refs

        # Build state for template
        adr_state = {
            **self.state,
            "adr_id": adr_id,
            "adr_references": refs,
            "tags": self.state.get("tags", ["adr", "architecture", slug[:15]]),
        }

        # Generate ADR text
        adr_text = _generate_adr_template(adr_state)
        result["adr_text"] = adr_text

        # ── C3: Quality gate pre-validate ──
        # Evalúa el ADR ANTES de guardarlo. Si score < threshold, bloquea el guardado.
        if adr_text and len(adr_text) > 50:
            try:
                from lib.kosmos.llm import evaluate_adr_quality

                gate_result = evaluate_adr_quality(adr_text, self.state)
                result["quality_gate"] = gate_result

                if gate_result["passed"]:
                    logger.info(
                        "C3: Quality gate PASSED (score=%s)",
                        gate_result["score"],
                    )
                else:
                    logger.warning(
                        "C3: Quality gate FAILED (score=%s, gaps=%s)",
                        gate_result["score"],
                        gate_result["gaps"],
                    )
                    # Hard gate: score too low → DO NOT save
                    if not gate_result["should_save"]:
                        logger.warning(
                            "C3: ADR NOT saved — quality too low "
                            "(%s < %s threshold)",
                            gate_result["score"],
                            gate_result["min_score"] * 0.5,
                        )
                        result["quality_gate"]["adr_blocked"] = True
                        self.node_results["document"] = result
                        self.state["document"] = result
                        return result
            except Exception as exc:
                logger.warning("C3: Quality gate failed (non-blocking): %s", exc)

        # Save ADR file
        adr_path = _RAW_DIR / f"{slug}-adr.md"
        adr_path.write_text(adr_text, encoding="utf-8")
        result["filepath"] = str(adr_path)

        # ── Index ADR in L1 (txtai) for immediate semantic search ──
        l1_status = self.sync_with_txtai(adr_text, adr_id)
        result["l1_index_status"] = l1_status
        self.state["l1_index_status"] = l1_status

        logger.info("   Document: %s written to %s (L1: %s)", adr_id, adr_path.name, l1_status)

    except Exception as exc:
        logger.warning("   Document failed: %s", exc)
        self.errors["document"] = str(exc)
        result["error"] = str(exc)

    self.node_results["document"] = result
    self.state["adr"] = result
    return result


# ═══════════════════════════════════════════════════════════════════════
# Node 7: Govern
# ═══════════════════════════════════════════════════════════════════════

def govern(self) -> Dict[str, Any]:
    """Nodo 7: Govern — población del Architecture Knowledge Graph (Fase 3).

    Fase 1-2: Genera tripletas RDF NT-like del ADR.
    Fase 3 (actual): Usa arch_graph.py para poblar el KG real con:
      - Nodo ADR con metadata completa
      - Edges: references, implements, detects, depends_on
      - Consulta coverage post-inserción
    Mantiene compatibilidad hacia atrás con triples NT.

    Returns:
        Dict with keys: triples, triple_count, filepath, arch_graph_status,
        coverage, metrics.
    """
    logger.info("▶️ Nodo 7: Govern (Fase 3 — ArchKnowledgeGraph)")
    result: Dict[str, Any] = {
        "triples": [],
        "triple_count": 0,
        "filepath": "",
        "arch_graph_status": {},
        "coverage": {},
        "arch_graph_nodes_added": 0,
        "arch_graph_edges_added": 0,
        "node_time": datetime.now().isoformat(),
    }

    try:
        adr_data = self.state.get("adr", {})
        adr_text = adr_data.get("adr_text", "")
        adr_id = adr_data.get("adr_id", "ADR-XXX")
        topic = self.state.get("topic", "Untitled")

        # Extract tags from state
        tags = self.state.get("tags", ["adr"])
        if self.memory is not None:
            stats = self.memory.get_stats()
            top_tags = list(stats.get("por_tag", {}).keys())[:3]
            tags.extend(top_tags)

        # Extract related ADRs from text
        related = []
        if adr_text:
            related = list(set(re.findall(r'ADR-\d+', adr_text)))
            # Remove self-reference
            if adr_id in related:
                related.remove(adr_id)

        kg_data = {
            "adr_id": adr_id,
            "title": topic,
            "status": "proposed",
            "tags": tags,
            "related_adrs": related,
        }

        # ── Fase 3: Poblar ArchKnowledgeGraph ──
        arch_graph_metrics = self._populate_arch_graph(
            adr_id=adr_id,
            topic=topic,
            tags=tags,
            related=related,
            adr_text=adr_text or "",
        )
        result["arch_graph_nodes_added"] = arch_graph_metrics.get("nodes_added", 0)
        result["arch_graph_edges_added"] = arch_graph_metrics.get("edges_added", 0)
        result["arch_graph_status"] = arch_graph_metrics.get("status", {})
        result["coverage"] = arch_graph_metrics.get("coverage", {})

        # ── Fase 1-2: RDF triples (backward compatibility) ──
        triples = _generate_rdf_triples(kg_data)
        result["triples"] = triples
        result["triple_count"] = len(triples)

        # Save triples (backward compat)
        slug = re.sub(r'[^a-z0-9]+', '-', topic.lower())[:40]
        triples_dir = _CACHE_DIR / "kosmos" / "triples"
        triples_dir.mkdir(parents=True, exist_ok=True)
        triples_path = triples_dir / f"{slug}-triples.nt"
        triples_path.write_text("\n".join(triples), encoding="utf-8")
        result["filepath"] = str(triples_path)

        logger.info("   Govern: %d triples generated", len(triples))

    except Exception as exc:
        logger.warning("   Govern failed: %s", exc)
        self.errors["govern"] = str(exc)
        result["error"] = str(exc)

    self.node_results["govern"] = result
    self.state["govern"] = result
    return result


# ═══════════════════════════════════════════════════════════════════════
# Node 8: Validate
# ═══════════════════════════════════════════════════════════════════════

def validate(self) -> Dict[str, Any]:
    """Nodo 8: Validate — verificación cross-referencia + reflexión + contratos F2.

    Valida el ADR contra ADRs existentes en L0, ejecuta el
    ciclo de reflexión, y ejecuta todos los contratos de Fase 2
    (Kratos, Metis, Mnemosyne, Aletheia) si aplican.

    Returns:
        Dict with keys: validation, reflection, contracts, suggestions.
    """
    logger.info("▶️ Nodo 8: Validate (Fase 2)")
    result: Dict[str, Any] = {
        "validation": {},
        "reflection": {},
        "contracts": {},
        "suggestions": [],
        "node_time": datetime.now().isoformat(),
    }

    try:
        adr_data = self.state.get("adr", {})
        adr_text = adr_data.get("adr_text", "")
        adr_id = adr_data.get("adr_id", "ADR-XXX")

        # 1. Cross-reference validation against L0
        if self.memory is not None and adr_text:
            validation = _validate_cross_references(adr_text, self.memory)
            result["validation"] = validation

            # Check adherence
            try:
                from lib.kosmos_evaluator_v2 import check_adherence

                # Get existing ADRs from memory
                stats = self.memory.get_stats()
                total = stats.get("total_adrs", 0)
                existing = []
                if total > 0:
                    for i in range(1, min(total + 1, 30)):
                        adr = self.memory.get_adr(i)
                        if adr:
                            existing.append(adr)

                adherence = check_adherence(adr_text, existing)
                result["adherence"] = adherence

                if adherence.get("contradictions"):
                    result["suggestions"].extend([
                        f"Contradicción detectada: {c}" for c in adherence["contradictions"]
                    ])
                if adherence.get("warnings"):
                    result["suggestions"].extend(adherence["warnings"])

            except Exception as exc:
                logger.warning("   Adherence check failed: %s", exc)
        else:
            result["validation"] = {
                "adr_references_found": re.findall(r'ADR-\d+', adr_text) if adr_text else [],
                "note": "L0 memory not available — validation limited",
            }

        # 2. Reflection (G2: skip if externally managed)
        if adr_text and not self.skip_eval:
            try:
                from lib.kosmos_reflect import ReflectionEngine

                reflector = ReflectionEngine(memory=self.memory)
                reflection = reflector.evaluate_adr(adr_text)
                result["reflection"] = reflection.to_dict()

                # Add reflection-based suggestions
                if reflection.gaps:
                    for gap in reflection.gaps[:3]:
                        result["suggestions"].append(f"Gap de reflexión: {gap}")

            except Exception as exc:
                logger.warning("   Reflection failed: %s", exc)
                result["reflection"] = {"error": str(exc)}
        elif self.skip_eval:
            logger.info("   Validate: SKIP_EVAL enabled — reflection skipped (external eval will run)")
            result["reflection"] = {"skip_eval": True}

        # 3. Fase 2: Run contracts (only if we have an ADR)
        if adr_text:
            try:
                contracts_result = self.run_contracts()
                result["contracts"] = contracts_result

                # Add contract suggestions to main suggestions
                contract_summary = contracts_result.get("summary", {})
                if contract_summary.get("errors", 0) > 0:
                    result["suggestions"].append(
                        f"{contract_summary['errors']} contratos fallaron — revisar logs"
                    )
                if contract_summary.get("completed", 0) > 0:
                    result["suggestions"].append(
                        f"{contract_summary['completed']} contratos ejecutados correctamente"
                    )

                # G5: Process corrective actions from contracts
                corrective_actions = contracts_result.get("corrective_actions", [])
                if corrective_actions:
                    logger.info("G5: %d corrective actions from contracts", len(corrective_actions))
                    for action in corrective_actions:
                        if action.get("severity") == "alta":
                            result["suggestions"].append(
                                f"[G5] {action['message']}"
                            )
                    result["corrective_actions"] = corrective_actions

            except Exception as exc:
                logger.warning("   Contracts execution failed (non-blocking): %s", exc)
                result["contracts"] = {"error": str(exc), "status": "failed"}

        # 4. Aggregate final suggestions
        if not result["suggestions"]:
            result["suggestions"] = [
                "ADR generado correctamente — verificar manualmente antes de aceptar"
            ]

        logger.info("   Validate: %d suggestions, %d adr refs, contracts=%s",
                   len(result["suggestions"]),
                   len(result.get("validation", {}).get("adr_references_found", [])),
                   "executed" if result.get("contracts") else "none")

    except Exception as exc:
        logger.warning("   Validate failed: %s", exc)
        self.errors["validate"] = str(exc)
        result["error"] = str(exc)

    self.node_results["validate"] = result
    self.state["validate"] = result
    return result
