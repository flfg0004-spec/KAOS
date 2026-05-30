"""Knowledge Tour Generator — topological sort of VaultGraph for guided learning paths.

Produces markdown guides with Start Here → Core Concepts → Advanced Topics
based on the dependency structure of the vault's wikilink graph.
"""

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

GUIDES_DIR = Path(__file__).resolve().parent.parent.parent / "wiki" / "guides"


def _ensure_guides_dir():
    GUIDES_DIR.mkdir(parents=True, exist_ok=True)


def topological_layers(graph) -> list[list[str]]:
    """Return nodes grouped by topological depth (Kahn's algorithm)."""

    in_degree = dict(graph.in_degree())
    queue = [n for n, d in in_degree.items() if d == 0]
    layers = []

    while queue:
        layers.append(sorted(queue))
        next_queue = []
        for node in queue:
            for successor in graph.successors(node):
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    next_queue.append(successor)
        queue = next_queue

    remaining = {n for n, d in in_degree.items() if d > 0}
    if remaining:
        logger.warning("Cycle detected among %d nodes — forcing remaining into last layer", len(remaining))
        layers.append(sorted(remaining))

    return layers


def detect_cycles(graph) -> list[list[str]]:
    """Return all cycles in the directed graph."""
    import networkx as nx

    try:
        cycles = list(nx.simple_cycles(graph))
        return cycles
    except Exception as e:
        logger.warning("Cycle detection failed: %s", e)
        return []


def assign_learning_levels(page_map: dict, graph) -> dict[str, int]:
    """Assign learning level 0..N to each node based on topological depth."""
    layers = topological_layers(graph)
    levels: dict[str, int] = {}
    for depth, layer in enumerate(layers):
        for node in layer:
            levels[node] = depth
    return levels


def _learning_level_label(level: int, max_level: int) -> tuple[str, str]:
    """Return (badge, section_title) for a given learning level."""
    if max_level <= 2:
        if level == 0:
            return ("START", "Start Here")
        elif level == 1:
            return ("CORE", "Core Concepts")
        else:
            return ("ADVANCED", "Advanced Topics")
    if level == 0:
        return ("START", "Start Here")
    elif level == max_level:
        return ("ADVANCED", "Advanced Topics")
    elif level <= max_level // 2:
        return ("CORE", "Core Concepts")
    else:
        return ("ADV", "Advanced Topics")


def generate_tour(page_map: dict, graph, output_path: str | Path | None = None, title: str = "Knowledge Tour") -> str:
    """Generate a full markdown knowledge tour from the vault graph."""

    layers = topological_layers(graph)
    levels = assign_learning_levels(page_map, graph)
    cycles = detect_cycles(graph)
    max_level = max(levels.values()) if levels else 0

    slug = title.lower().replace(" ", "-")[:40]
    output_path = GUIDES_DIR / f"knowledge-tour-{slug}.md" if output_path is None else Path(output_path)

    lines = []
    lines.append("---")
    lines.append("type: guide")
    lines.append(f"title: {title}")
    lines.append(f"generated: '{datetime.now().strftime('%Y-%m-%d %H:%M')}'")
    lines.append(f"nodes: {graph.number_of_nodes()}")
    lines.append(f"edges: {graph.number_of_edges()}")
    lines.append(f"levels: {len(layers)}")
    lines.append(f"cycles: {len(cycles)}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"*Auto-generated knowledge tour — {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")
    lines.append("## Table of Contents")
    lines.append("")

    toc_entries = []
    for depth, layer in enumerate(layers):
        badge, section = _learning_level_label(depth, max_level)
        anchor = section.lower().replace(" ", "-")
        entry = f"- **[{badge}] [{section}](#{anchor})** — {len(layer)} nodes"
        lines.append(entry)
        toc_entries.append((section, anchor, layer))
    lines.append("")

    if cycles:
        lines.append("## ⚠️ Cycles Detected")
        lines.append("")
        lines.append(f"The graph contains **{len(cycles)} cycle(s)**, which were broken artificially for the tour.")
        lines.append("")
        for i, cycle in enumerate(cycles[:5]):
            lines.append(f"{i + 1}. {' → '.join(cycle)}")
        if len(cycles) > 5:
            lines.append(f"... and {len(cycles) - 5} more")
        lines.append("")

    lines.append("## Dependency Graph")
    lines.append("")
    lines.append("```mermaid")
    lines.append("graph LR")
    for node in graph.nodes():
        label = node.replace("_", " ").replace("-", " ")[:30]
        level = levels.get(node, 0)
        badge, _ = _learning_level_label(level, max_level)
        css_class = badge.lower()
        lines.append(f'    {node}["{label}"]:::{css_class}')
    for u, v in graph.edges():
        lines.append(f"    {u} --> {v}")
    lines.append("")
    lines.append("classDef start fill:#e1f5fe,stroke:#4fc3f7;")
    lines.append("classDef core fill:#e8f5e9,stroke:#81c784;")
    lines.append("classDef adv fill:#fff3e0,stroke:#ffb74d;")
    lines.append("classDef advanced fill:#fce4ec,stroke:#e57373;")
    lines.append("```")
    lines.append("")

    for depth, layer in enumerate(layers):
        badge, section = _learning_level_label(depth, max_level)
        anchor = section.lower().replace(" ", "-")
        lines.append(f"## {section}")
        lines.append("")
        lines.append("| # | Node | Links Out | Links In | Level |")
        lines.append("|---|------|-----------|----------|-------|")

        for i, node in enumerate(layer, 1):
            out_deg = graph.out_degree(node)
            in_deg = graph.in_degree(node)
            level = levels.get(node, depth)
            lines.append(f"| {i} | {node} | {out_deg} | {in_deg} | {level} |")

        lines.append("")

    lines.append("---")
    lines.append("*Generated by Knowledge Tour Generator*")

    md = "\n".join(lines)
    _ensure_guides_dir()
    output_path.write_text(md, encoding="utf-8")
    logger.info("Knowledge tour written to %s (%d nodes, %d levels)", output_path, graph.number_of_nodes(), len(layers))
    return md
