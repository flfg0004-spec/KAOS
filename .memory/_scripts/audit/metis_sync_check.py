"""Metis Consistency Checker — verifica sincronización de MCP tools entre archivos.

Lee opencode.json y extrae la lista de MCP tools de Metis.
Compara contra las listas en metis.md, AGENTS.md,
KAOS/01-agentes/metis.md y .memory/wiki/entities/metis.md.

Da un score de consistencia (0-5 archivos sincronizados).
"""

import json
import re
import sys
from pathlib import Path

KAOS_ROOT = Path(__file__).resolve().parents[3]
OPCODE_CONFIG = KAOS_ROOT / ".opencode" / "opencode.json"
FILES_TO_CHECK = [
    ("opencode.json", KAOS_ROOT / ".opencode" / "opencode.json", "manifest"),
    ("metis.md (agent root)", KAOS_ROOT / ".opencode" / "agents" / "metis.md", "manifest"),
    ("AGENTS.md", KAOS_ROOT / ".opencode" / "agents" / "metis" / "AGENTS.md", "manifest"),
    ("KAOS/01-agentes/metis.md", KAOS_ROOT / "KAOS" / "01-agentes" / "metis.md", "manifest"),
    ("wiki/entities/metis.md", KAOS_ROOT / ".memory" / "wiki" / "entities" / "metis.md", "manifest"),
    ("SOUL.md", KAOS_ROOT / ".opencode" / "agents" / "metis" / "SOUL.md", "reference"),
    ("SKILL.md", KAOS_ROOT / ".opencode" / "skills" / "metis" / "SKILL.md", "reference"),
    ("ADR-016", KAOS_ROOT / "KAOS" / "04-esquema" / "ADR-016-arquitectura-metis.md", "reference"),
    ("eval-profile.yaml", KAOS_ROOT / ".memory" / "schema" / "eval-profile.yaml", "reference"),
    ("metis-kronos-boundary.md", KAOS_ROOT / ".memory" / "schema" / "metis-kronos-boundary.md", "reference"),
]

# Manifest files must have a complete tool listing matching opencode.json.
# Reference files only need to avoid containing contradictions (fake tools, wrong temps).

TOOL_MENTIONS_MAP = {
    "exa-search": ["exa-search", "exa search", "exa_search"],
    "sequential-thinking": ["sequential-thinking", "sequential thinking", "sequential_thinking"],
    "strategy-mcp": ["strategy-mcp", "strategy mcp", "strategy_mcp"],
    "strategy-extras": ["strategy-extras", "strategy extras", "strategy_extras"],
    "excalidraw": ["excalidraw"],
    "paperjsx": ["paperjsx"],
    "vault": ["vault", "vault mcp"],
    "dsol": ["dsol", "mcp-dsol", "mcp_dsol"],
    "speed": ["speed", "mcp-speed", "mcp_speed"],
    "agy-bridge": ["agy-bridge", "agy bridge", "agy_bridge"],
    "obsidian": ["obsidian", "mcp-obsidian-cli", "mcp_obsidian_cli"],
    "mcp-pandas": ["mcp-pandas", "mcp pandas", "mcp_pandas"],
    "skill": ["skill"],
}

FAKE_TOOLS = [
    "fabric-*", "canvas-*", "crewai-*", "autogpt-*", "langchain-*",
    "claude-*", "gpt-*", "llama-*", "palm-*", "gemini-*",
    "mock-*", "fake-*", "dummy-*",
]


def get_metis_tools_from_opencode() -> set[str]:
    """Extract Metis MCP server names from opencode.json.

    Tool keys follow two patterns:
      "excalidraw_*"                    -> server: "excalidraw"
      "agy-bridge_agy_ask_flash"       -> server: "agy-bridge"
    """
    config = json.loads(OPCODE_CONFIG.read_text(encoding="utf-8"))
    tools = config.get("agent", {}).get("metis", {}).get("tools", {})
    servers = set()
    for k in tools:
        if not tools[k]:
            continue
        if k.endswith("_*"):
            servers.add(k.replace("_*", ""))
        else:
            servers.add(k.split("_")[0])
    return servers


def extract_tools_from_text(text: str) -> set[str]:
    """Extract MCP tool references from markdown or YAML text.

    Matches patterns like:
    - `exa-search_*` or exa-search_*
    - mcp-servers: [list]
    - - **name**: description
    """
    tools = set()

    # Pattern 1: YAML list mcp-servers: [item1, item2, ...]
    mcp_servers_match = re.search(r"mcp-servers:\s*\[([^\]]+)\]", text)
    if mcp_servers_match:
        items = [x.strip().strip("'\"") for x in mcp_servers_match.group(1).split(",")]
        tools.update(items)

    # Pattern 2: YAML list with dash lines
    # mcp-servers:\n- item1\n- item2
    in_mcp_block = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("mcp-servers:"):
            if "[" not in stripped:
                in_mcp_block = True
            continue
        if in_mcp_block:
            if stripped.startswith("- "):
                item = stripped[2:].strip().strip("'\"")
                if item:
                    tools.add(item)
            elif stripped.startswith("#") or stripped == "" or ":" in stripped:
                continue
            else:
                in_mcp_block = False

    # Pattern 3: Tool_* references like `exa-search_*`
    tool_refs = re.findall(r"`([a-zA-Z][\w-]+)_\*`", text)
    tools.update(tool_refs)

    # Pattern 4: Tool names from markdown tool tables (AGENTS.md style)
    # | `tool-name` | ...
    table_tools = re.findall(r"\|\s*`([\w-]+)`\s*\|", text)
    # Filter out non-tools (like framework names, ids)
    known_tool_suffixes = {"search", "thinking", "mcp", "bridge", "excalidraw", "paperjsx"}
    for t in table_tools:
        if any(s in t.lower() for s in known_tool_suffixes) or "-" in t:
            tools.add(t)

    # Pattern 5: Markdown list items with bold tool names: - **Tool Name**:
    display_to_tool = {
        "exa search": "exa-search",
        "sequential thinking": "sequential-thinking",
        "excalidraw": "excalidraw",
        "paperjsx": "paperjsx",
        "strategy-mcp": "strategy-mcp",
        "strategy-extras": "strategy-extras",
        "dsol": "dsol",
        "speed": "speed",
        "vault mcp": "vault",
        "mcp-obsidian-cli": "mcp-obsidian-cli",
        "obsidian": "obsidian",
        "skill": "skill",
        "agy-bridge": "agy-bridge",
    }
    bold_list_items = re.findall(r"^\s*-\s+\*\*([^*]+)\*\*", text, re.MULTILINE)
    for item in bold_list_items:
        key = item.strip().lower()
        if key in display_to_tool:
            tools.add(display_to_tool[key])
        elif "-" in key or any(s in key for s in known_tool_suffixes):
            tools.add(key)

    return tools


def normalize(tools: set[str]) -> set[str]:
    """Normalize tool names for comparison."""
    mapping = {
        "exa": "exa-search",
        "exa-search": "exa-search",
        "sequential": "sequential-thinking",
        "sequential-thinking": "sequential-thinking",
        "obsidian": "obsidian",
        "mcp-obsidian-cli": "mcp-obsidian-cli",
        "vault": "vault",
        "strategy-mcp": "strategy-mcp",
        "strategy-extras": "strategy-extras",
        "dsol": "dsol",
        "speed": "speed",
        "paperjsx": "paperjsx",
        "excalidraw": "excalidraw",
        "agy-bridge": "agy-bridge",
        "skill": "skill",
        "brave-search": "brave-search",
        "server-github": "server-github",
        "ce-memory": "ce-memory",
    }
    normalized = set()
    for t in tools:
        t_clean = t.strip().lower().replace("_*", "").replace("_", "-")
        if t_clean in mapping:
            normalized.add(mapping[t_clean])
        elif t_clean:
            normalized.add(t_clean)
    return normalized


def check_file(label: str, path: Path, reference: set[str], file_type: str = "manifest") -> dict:
    """Check a single file against the reference set of tools."""
    if not path.exists():
        return {
            "label": label,
            "exists": False,
            "tools_found": set(),
            "missing": reference,
            "extra": set(),
            "synced": False,
        }

    # For opencode.json, use the reference directly (it was parsed from JSON)
    if "opencode.json" in label:
        tools_found = reference
        missing = reference - tools_found
        extra = tools_found - reference
        return {
            "label": label,
            "exists": True,
            "tools_found": tools_found,
            "missing": missing,
            "extra": extra,
            "synced": True,
        }

    text = path.read_text(encoding="utf-8")
    tools_found = normalize(extract_tools_from_text(text))

    if file_type == "reference":
        # Reference files only need to NOT contain fake/contradictory tool names
        # They don't need to list all tools
        fake_detected = {t for t in tools_found if any(f.replace("*", "") in t for f in FAKE_TOOLS)}
        has_contradiction = "0.3-0.4" in text and "temperatura" in text.lower()
        synced = len(fake_detected) == 0 and not has_contradiction
        missing = set()
        extra = fake_detected
        return {
            "label": label,
            "exists": True,
            "tools_found": tools_found,
            "missing": missing,
            "extra": extra,
            "synced": synced,
        }

    missing = reference - tools_found
    extra = tools_found - reference

    return {
        "label": label,
        "exists": True,
        "tools_found": tools_found,
        "missing": missing,
        "extra": extra,
        "synced": len(missing) == 0 and len(extra) <= 1,  # allow 1 extra (skill, etc.)
    }


def main() -> None:
    print("=" * 70)
    print("  Metis Consistency Checker — MCP Tool Sync Report")
    print("=" * 70)

    if not OPCODE_CONFIG.exists():
        print(f"\n  ERROR: opencode.json not found at {OPCODE_CONFIG}")
        sys.exit(1)

    reference = get_metis_tools_from_opencode()
    print("\n  Reference (from opencode.json):")
    for t in sorted(reference):
        print(f"    - {t}")
    print(f"  Total: {len(reference)} tools\n")

    results = []
    synced_count = 0

    sync_group = {"manifest": 0, "reference": 0}
    type_counts = {"manifest": 0, "reference": 0}

    for label, path, file_type in FILES_TO_CHECK:
        result = check_file(label, path, reference, file_type)
        results.append(result)
        type_counts[file_type] += 1

        status = "✗" if not result["synced"] else "✓"
        exists = "✓" if result["exists"] else "✗"
        print(f"  [{status}] {label}  (file exists: {exists})")

        if result["missing"]:
            print(f"       Missing: {', '.join(sorted(result['missing']))}")
        if result["extra"]:
            print(f"       Extra:   {', '.join(sorted(result['extra']))}")

        if result["synced"]:
            sync_group[file_type] += 1

    total = sum(type_counts.values())
    synced_count = sum(sync_group.values())

    print(f"\n  {'─' * 50}")
    print(f"  Consistency: {sync_group['manifest']}/{type_counts['manifest']} manifest | {sync_group['reference']}/{type_counts['reference']} reference")
    print(f"  Score: {synced_count}/{total} archivos sincronizados")

    if synced_count == total:
        print("  Status: ✅ COMPLETE — todos los archivos están sincronizados")
    elif synced_count >= total // 2:
        print(f"  Status: ⚠️  PARCIAL — {total - synced_count} archivo(s) necesitan sincronización")
    else:
        print(f"  Status: ❌ CRÍTICO — {total - synced_count} archivo(s) desincronizados")

    skill_path = KAOS_ROOT / ".opencode" / "skills" / "metis" / "SKILL.md"
    if skill_path.exists():
        skill_lines = len(skill_path.read_text(encoding="utf-8").split("\n"))
        print(f"\n  SKILL.md size: {skill_lines} líneas")
        if skill_lines > 750:
            print(f"  ⚠️  WARNING: SKILL.md ({skill_lines} líneas) excede 750 — considerar refactor (ADR-017)")
        elif skill_lines > 700:
            print(f"  ℹ️  SKILL.md se acerca al umbral de refactor (750). Actual: {skill_lines}")

    print("=" * 70)

    return synced_count


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result == len(FILES_TO_CHECK) else 1)
