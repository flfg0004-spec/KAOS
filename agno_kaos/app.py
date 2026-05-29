"""FastAPI base_app compartido para todos los modos de AgentOS.

Provee landing page, health endpoint, dashboard y rutas custom sin colisionar con MCP.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="A(gnO)-KAOS", version="3.0.0")

app.mount("/static", StaticFiles(directory="agno_kaos/static"), name="static")
from agno_kaos.ecosystem import router as ecosystem_router
app.include_router(ecosystem_router)


@app.get("/")
async def landing():
    return JSONResponse({
        "service": "A(gnO)-KAOS AgentOS",
        "version": "3.0.0",
        "agents": ["A-Pilot", "A-Aletheia", "A-Kosmos", "A-Metis", "A-Kratos"],
        "docs": "/docs",
        "mcp": "/mcp",
        "status": "/health",
        "dashboard": "/dashboard",
    })


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "agents": 5, "version": "3.0.0"})


@app.get("/dashboard")
async def dashboard():
    from fastapi.responses import HTMLResponse
    from pathlib import Path
    html = Path("agno_kaos/static/dashboard.html").read_text(encoding="utf-8")
    return HTMLResponse(html)
