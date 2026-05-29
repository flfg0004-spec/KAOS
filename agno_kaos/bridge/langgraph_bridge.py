"""AgnoAgentNode: wrappea agentes agno como nodos LangGraph.

Reemplaza los nodos originales de lib/agent_executor.py por agentes
agno cuando AGNO_ENABLED=true en el orquestador de KAOS.

Uso en orchestrator.py:
    from agno_kaos.bridge.langgraph_bridge import AgnoAgentNode, agno_factory

    if AGNO_ENABLED:
        builder.add_node("aletheia", AgnoAgentNode("aletheia"))
"""

from agno_kaos import load_config


class AgnoAgentNode:
    """Wrappea un agente agno como nodo LangGraph.

    Args:
        agent_name: Nombre del agente ("aletheia", "kosmos", "metis", "kratos").
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._agent = None

    def _get_agent(self):
        if self._agent is not None:
            return self._agent
        cfg = load_config()
        with_mcp = cfg.get("agentos", {}).get("enable_mcp_server", True)

        if self.agent_name == "aletheia":
            from agno_kaos.agents.a_aletheia import create_aletheia

            self._agent = create_aletheia(with_mcp=with_mcp)
        elif self.agent_name == "kosmos":
            from agno_kaos.agents.a_kosmos import create_kosmos
            self._agent = create_kosmos(with_mcp=with_mcp)
        elif self.agent_name == "metis":
            from agno_kaos.agents.a_metis import create_metis
            self._agent = create_metis(with_mcp=with_mcp)
        elif self.agent_name == "kratos":
            from agno_kaos.agents.a_kratos import create_kratos
            self._agent = create_kratos(with_mcp=with_mcp)
        else:
            raise ValueError(f"Unknown agent: {self.agent_name}")
        return self._agent

    async def __call__(self, state: dict) -> dict:
        topic = state.get("topic", "")
        profile = state.get("profile", "standard")
        context = state.get("plan", {})

        prompt = f"Topic: {topic}\nProfile: {profile}"
        if context:
            prompt += f"\nContext: {context}"
        prompt += f"\n\nAct as {self.agent_name}. Respond in markdown."

        agent = self._get_agent()
        try:
            import asyncio

            response = await asyncio.wait_for(agent.arun(prompt), timeout=60)
            content = response.content if hasattr(response, "content") else str(response)
        except asyncio.TimeoutError:
            content = f"[TIMEOUT] {self.agent_name} did not respond in 60s"
        except Exception as e:
            content = f"[ERROR] {self.agent_name}: {e}"

        slug_map = {"aletheia": "aletheia", "kosmos": "kosmos", "metis": "metis", "kratos": "kratos"}
        slug = slug_map.get(self.agent_name, self.agent_name)
        return {f"{slug}_output": content, f"{slug}_prompt": prompt}


def agno_factory(state: dict) -> dict:
    """Factory que selecciona el nodo agno según el agente."""
    agent_name = state.get("_agent_name", "aletheia")
    node = AgnoAgentNode(agent_name)
    return node(state)
