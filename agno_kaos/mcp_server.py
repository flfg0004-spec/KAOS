"""agno-mcp-server: Gateway MCP bidireccional A(gnO)-KAOS.

- Expone agentes agno como tools MCP para que KAOS los consuma
- Los agents agno consumen MCP servers de KAOS (vault, txtai, etc.)
- Rate limiting integrado (30 rpm por defecto)
"""

import asyncio
import logging
from pathlib import Path

from agno_kaos.mcp_utils import RateLimiter, load_mcp_config
from agno_kaos.agents.a_aletheia import create_aletheia
from agno_kaos.agents.a_kosmos import create_kosmos
from agno_kaos.agents.a_kratos import create_kratos
from agno_kaos.agents.a_metis import create_metis
from agno_kaos.agents.apilot import create_pilot

logger = logging.getLogger("agno_kaos.mcp_server")

# Rate limiter config from config.yaml
_rl_rpm = 30
try:
    from agno_kaos import load_config
    _rl_rpm = load_config().get("rate_limiting", {}).get("rpm", 30)
except Exception:
    pass
_rate_limiter = RateLimiter(rpm=_rl_rpm)

try:
    from mcp.server import Server as MCPServer
    from mcp.server.stdio import stdio_server
    from mcp.types import CallToolRequest, CallToolResult, ListToolsResult, TextContent, Tool

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

_agents = {}


def get_agents():
    global _agents
    if not _agents:
        _agents["a_aletheia"] = create_aletheia(with_mcp=False)
        _agents["a_kosmos"] = create_kosmos(with_mcp=False)
        _agents["a_metis"] = create_metis(with_mcp=False)
        _agents["a_kratos"] = create_kratos(with_mcp=False)
        _agents["a_pilot"] = create_pilot()
    return _agents


TOOL_DEFS = [
    Tool(
        name="a_aletheia_research",
        description="Investigación profunda sobre un tema usando el agente A-Aletheia (acceso a exa-search, searxng, crawl4ai, vault)",
        inputSchema={
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Tema a investigar"},
                "depth": {"type": "string", "description": "standard|deep", "default": "standard"},
            },
            "required": ["topic"],
        },
    ),
    Tool(
        name="a_kosmos_analyze",
        description="Analiza la arquitectura de un codebase usando A-Kosmos (acceso a depwire, structurizr)",
        inputSchema={
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Ruta del código o sistema a analizar"},
                "focus": {"type": "string", "description": "dependencies|structure|quality", "default": "structure"},
            },
            "required": ["target"],
        },
    ),
    Tool(
        name="a_metis_strategize",
        description="Análisis estratégico usando A-Metis (acceso a strategy-mcp, paperjsx)",
        inputSchema={
            "type": "object",
            "properties": {
                "objective": {"type": "string", "description": "Objetivo estratégico"},
                "context": {"type": "string", "description": "Contexto adicional"},
            },
            "required": ["objective"],
        },
    ),
    Tool(
        name="a_kratos_code",
        description="Generación o revisión de código usando A-Kratos (acceso a git, vault)",
        inputSchema={
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Tarea de código a realizar"},
                "language": {"type": "string", "description": "Lenguaje de programación", "default": "python"},
            },
            "required": ["task"],
        },
    ),
    Tool(
        name="a_pilot_ask",
        description="Pregunta general a A-Pilot (asistente principal del ecosistema)",
        inputSchema={
            "type": "object",
            "properties": {"question": {"type": "string", "description": "Pregunta"}},
            "required": ["question"],
        },
    ),
]


async def handle_list_tools() -> ListToolsResult:
    return ListToolsResult(tools=TOOL_DEFS)


def _prompt_for_tool(name: str, args: dict) -> str:
    prompts = {
        "a_aletheia_research": lambda: f"Investiga a fondo: {args.get('topic', '')}",
        "a_kosmos_analyze": lambda: (
            f"Analiza la arquitectura de: {args.get('target', '')}\nEnfoque: {args.get('focus', 'structure')}"
        ),
        "a_metis_strategize": lambda: f"Objective: {args.get('objective', '')}\nContext: {args.get('context', '')}",
        "a_kratos_code": lambda: f"Task: {args.get('task', '')}\nLanguage: {args.get('language', 'python')}",
        "a_pilot_ask": lambda: args.get("question", ""),
    }
    return prompts.get(name, lambda: "")()


async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
    name = request.params.name
    args = request.params.arguments or {}

    if not _rate_limiter.acquire():
        logger.warning("Rate limit exceeded for tool: %s", name)
        return CallToolResult(
            isError=True, content=[TextContent(type="text", text="Rate limit exceeded. Try again later.")]
        )

    agents = get_agents()

    agent_map = {
        "a_aletheia_research": "a_aletheia",
        "a_kosmos_analyze": "a_kosmos",
        "a_metis_strategize": "a_metis",
        "a_kratos_code": "a_kratos",
        "a_pilot_ask": "a_pilot",
    }

    agent_key = agent_map.get(name)
    if not agent_key:
        return CallToolResult(isError=True, content=[TextContent(type="text", text=f"Unknown tool: {name}")])

    agent = agents.get(agent_key)
    if not agent:
        return CallToolResult(
            isError=True, content=[TextContent(type="text", text=f"Agent {agent_key} not initialized")]
        )

    try:
        prompt = _prompt_for_tool(name, args)
        response = await agent.arun(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        return CallToolResult(content=[TextContent(type="text", text=str(content))])
    except Exception as e:
        return CallToolResult(isError=True, content=[TextContent(type="text", text=f"Error: {e}")])


async def main():
    if not MCP_AVAILABLE:
        print("MCP SDK no instalado. pip install mcp")
        return

    server = MCPServer("agno-kaos-gateway")

    @server.list_tools()
    async def list_tools():
        return await handle_list_tools()

    @server.call_tool()
    async def call_tool(request: CallToolRequest):
        return await handle_call_tool(request)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
