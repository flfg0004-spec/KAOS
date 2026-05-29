"""Run A-Pilot AgentOS server.

Uso: python agno_kaos/run_pilot.py [--port 8022]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn
from agno.os import AgentOS

from agno_kaos import get_ports
from agno_kaos.agents.apilot import create_pilot
from agno_kaos.app import app as base_app

PORTS = get_ports()
port = int(sys.argv[2]) if len(sys.argv) > 2 else PORTS.get("pilot", 8022)

pilot = create_pilot()
os = AgentOS(
    agents=[pilot],
    enable_mcp_server=True,
    base_app=base_app,
    on_route_conflict="preserve_base_app",
    tracing=True,
)
app = os.get_app()

print(f"  Landing:     http://127.0.0.1:{port}/")
print(f"  Swagger UI:  http://127.0.0.1:{port}/docs")
print(f"  Health:      http://127.0.0.1:{port}/health")
uvicorn.run(app, host="127.0.0.1", port=port)
