"""ArchKnowledge Graph — lightweight knowledge graph for architectural decisions."""

import json
import logging
import time
from collections import deque
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("arch_graph")

GRAPH_DIR = Path(__file__).resolve().parent.parent.parent / "cache" / "arch-graph"
GRAPH_FILE = GRAPH_DIR / "graph.json"

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram

    GRAPH_QUERIES = Counter("arch_graph_queries_total", "Arch Graph queries", ["query_type"])
    GRAPH_LATENCY = Histogram(
        "arch_graph_query_seconds", "Arch Graph query latency", buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
    )
except ImportError:
    GRAPH_QUERIES = None
    GRAPH_LATENCY = None

_HAS_NETWORKX = False
try:
    import networkx as nx

    _HAS_NETWORKX = True
except ImportError:
    pass

NODE_TYPES = {"adr", "component", "decision", "smell", "pattern", "agent_output"}
EDGE_TYPES = {"implements", "violates", "depends_on", "supersedes", "references", "generates", "detects"}


def _ensure_graph_dir():
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)


def _load_graph() -> dict:
    _ensure_graph_dir()
    if GRAPH_FILE.exists():
        try:
            return json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"nodes": [], "edges": []}


def _save_graph(graph: dict):
    _ensure_graph_dir()
    GRAPH_FILE.write_text(json.dumps(graph, indent=2), encoding="utf-8")


def add_node(node_id: str, node_type: str, properties: dict = None) -> dict:
    if node_type not in NODE_TYPES:
        return {"status": "error", "message": f"Unknown node type: {node_type}"}
    graph = _load_graph()
    existing = [n for n in graph["nodes"] if n["id"] == node_id]
    if existing:
        existing[0]["properties"] = properties or {}
        existing[0]["updated_at"] = datetime.now().isoformat()
        _save_graph(graph)
        return {"status": "updated", "node_id": node_id}
    node = {
        "id": node_id,
        "type": node_type,
        "properties": properties or {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    graph["nodes"].append(node)
    _save_graph(graph)
    return {"status": "created", "node_id": node_id}


def add_edge(source_id: str, target_id: str, edge_type: str, properties: dict = None) -> dict:
    if edge_type not in EDGE_TYPES:
        return {"status": "error", "message": f"Unknown edge type: {edge_type}"}
    graph = _load_graph()
    edge = {
        "source": source_id,
        "target": target_id,
        "type": edge_type,
        "properties": properties or {},
        "created_at": datetime.now().isoformat(),
    }
    graph["edges"].append(edge)
    _save_graph(graph)
    return {"status": "created", "edge": f"{source_id} --[{edge_type}]--> {target_id}"}


def query(query_type: str, params: dict = None) -> dict:
    """Query the architecture knowledge graph with Prometheus metrics tracking."""
    start = time.time()
    result = _query(query_type, params or {})
    duration = time.time() - start
    if GRAPH_QUERIES:
        GRAPH_QUERIES.labels(query_type=query_type).inc()
    if GRAPH_LATENCY:
        GRAPH_LATENCY.observe(duration)
    return result


def _query(query_type: str, params: dict) -> dict:
    graph = _load_graph()
    if query_type == "node":
        nodes = [n for n in graph["nodes"] if n["id"] == params.get("id", "")]
        return {"results": nodes, "count": len(nodes)}
    elif query_type == "nodes_by_type":
        nodes = [n for n in graph["nodes"] if n["type"] == params.get("type", "")]
        return {"results": nodes, "count": len(nodes)}
    elif query_type == "edges_from":
        edges = [e for e in graph["edges"] if e["source"] == params.get("id", "")]
        return {"results": edges, "count": len(edges)}
    elif query_type == "edges_to":
        edges = [e for e in graph["edges"] if e["target"] == params.get("id", "")]
        return {"results": edges, "count": len(edges)}
    elif query_type == "path":
        if _HAS_NETWORKX:
            return _find_path_nx(graph, params.get("source", ""), params.get("target", ""))
        return _find_path_bfs(graph, params.get("source", ""), params.get("target", ""))
    elif query_type == "dependency_chain":
        return _find_dependency_chain(graph, params.get("component", ""))
    elif query_type == "adr_coverage":
        return _adr_coverage(graph)
    elif query_type == "recent":
        limit = params.get("limit", 10)
        all_items = [{"type": "node", **n} for n in graph["nodes"]]
        all_items += [{"type": "edge", **e} for e in graph["edges"]]
        all_items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return {"results": all_items[:limit], "count": min(len(all_items), limit)}
    return {"results": [], "count": 0, "error": f"Unknown query type: {query_type}"}


def _find_dependency_chain(graph: dict, component: str) -> dict:
    edges = graph["edges"]
    visited = set()
    chain = []

    def _traverse(node_id: str, depth: int = 0):
        if node_id in visited or depth > 10:
            return
        visited.add(node_id)
        for e in edges:
            if e["source"] == node_id and e["type"] == "depends_on":
                chain.append({"depth": depth, "from": node_id, "to": e["target"]})
                _traverse(e["target"], depth + 1)

    _traverse(component)
    return {"results": chain, "count": len(chain), "component": component}


def _adr_coverage(graph: dict) -> dict:
    adrs = [n["id"] for n in graph["nodes"] if n["type"] == "adr"]
    covered = set()
    for e in graph["edges"]:
        if e["type"] == "references" and e["source"] in adrs:
            covered.add(e["target"])
    components = [n for n in graph["nodes"] if n["type"] == "component"]
    uncovered = [c["id"] for c in components if c["id"] not in covered]
    return {
        "total_adrs": len(adrs),
        "total_components": len(components),
        "covered_components": len(covered),
        "coverage_pct": round(len(covered) / max(1, len(components)) * 100, 1),
        "uncovered_components": uncovered,
    }


def _find_path_nx(graph: dict, source: str, target: str) -> dict:
    try:
        import networkx as nx

        G = nx.DiGraph()
        for n in graph["nodes"]:
            G.add_node(n["id"])
        for e in graph["edges"]:
            G.add_edge(e["source"], e["target"])
        path = nx.shortest_path(G, source=source, target=target)
        return {"results": path, "count": len(path), "source": source, "target": target}
    except Exception as e:
        return {"results": [], "count": 0, "error": str(e)}


def _find_path_bfs(graph: dict, source: str, target: str) -> dict:
    edges = graph.get("edges", [])
    adj = {}
    for e in edges:
        s = e.get("source", "")
        t = e.get("target", "")
        if s not in adj:
            adj[s] = []
        adj[s].append(t)
    visited = {source}
    queue = deque([[source]])
    while queue:
        path = queue.popleft()
        node = path[-1]
        if node == target:
            return {"results": path, "count": len(path), "source": source, "target": target}
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    return {"results": [], "count": 0, "source": source, "target": target, "error": "No path found"}


def adr_to_graph(adr_data: dict) -> dict:
    adr_id = adr_data.get("id", f"adr-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    result = add_node(adr_id, "adr", adr_data)
    for comp in adr_data.get("affected_components", []):
        add_node(comp, "component")
        add_edge(adr_id, comp, "references")
    for dep in adr_data.get("supersedes", []):
        add_edge(adr_id, dep, "supersedes")
    return result


def status() -> dict:
    graph = _load_graph()
    type_counts = {}
    for n in graph["nodes"]:
        t = n["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    return {
        "total_nodes": len(graph["nodes"]),
        "total_edges": len(graph["edges"]),
        "node_types": type_counts,
        "networkx_available": _HAS_NETWORKX,
        "storage": str(GRAPH_FILE),
    }


class ArchKnowledgeGraph:
    """Wrapper class around arch_graph module functions.

    Proporciona una API orientada a objetos para KosmosV2,
    manteniendo compatibilidad hacia atrás con las funciones modulares.
    """

    def __init__(self, storage_path: str = "") -> None:
        """Initialize the knowledge graph.

        Si no se especifica storage_path, usa el default del módulo (GRAPH_FILE).

        Args:
            storage_path: Optional custom path for the graph JSON file.
        """
        if storage_path:
            self._storage_path: Path = Path(storage_path)
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self._storage_path: Path = GRAPH_FILE

    def add_node(self, node_id: str, node_type: str, properties: dict = None) -> dict:
        """Add a node to the knowledge graph. Delegates to module-level add_node().

        Args:
            node_id: Unique identifier for the node.
            node_type: Type of node (adr, component, decision, smell, pattern, agent_output).
            properties: Optional dict of properties.

        Returns:
            Dict with status and node_id.
        """
        return add_node(node_id, node_type, properties or {})

    def add_edge(self, source_id: str, target_id: str, edge_type: str, properties: dict = None) -> dict:
        """Add an edge to the knowledge graph. Delegates to module-level add_edge().

        Args:
            source_id: Source node ID.
            target_id: Target node ID.
            edge_type: Type of edge (implements, violates, depends_on, supersedes, references, generates, detects).
            properties: Optional dict of properties.

        Returns:
            Dict with status and edge description.
        """
        return add_edge(source_id, target_id, edge_type, properties or {})

    def query(self, query_type: str, params: dict = None) -> dict:
        """Query the knowledge graph. Delegates to module-level query().

        Args:
            query_type: Type of query (node, nodes_by_type, edges_from, edges_to,
                       path, dependency_chain, adr_coverage, recent).
            params: Optional dict of query parameters.

        Returns:
            Dict with results and count.
        """
        return query(query_type, params or {})

    def status(self) -> dict:
        """Get knowledge graph status. Delegates to module-level status().

        Returns:
            Dict with total_nodes, total_edges, node_types, storage path.
        """
        return status()

    def adr_to_graph(self, adr_data: dict) -> dict:
        """Import an ADR into the graph. Delegates to module-level adr_to_graph().

        Args:
            adr_data: Dict with id, affected_components, supersedes keys.

        Returns:
            Dict with status and node_id.
        """
        return adr_to_graph(adr_data)
