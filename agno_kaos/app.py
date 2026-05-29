"""FastAPI base_app compartido para todos los modos de AgentOS.

Provee landing page, health endpoint y rutas custom sin colisionar con MCP.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="A(gnO)-KAOS", version="3.0.0")


@app.get("/")
async def landing():
    return JSONResponse(
        {
            "service": "A(gnO)-KAOS AgentOS",
            "version": "3.0.0",
            "agents": ["A-Pilot", "A-Aletheia", "A-Kosmos", "A-Metis", "A-Kratos"],
            "docs": "/docs",
            "mcp": "/mcp",
            "status": "/health",
        }
    )


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "agents": 5, "version": "3.0.0"})
