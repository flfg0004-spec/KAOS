"""FastAPI base_app compartido para todos los modos de AgentOS.

Provee landing page, health endpoint, dashboard y rutas custom sin colisionar con MCP.
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

_HERE = Path(__file__).resolve().parent

app = FastAPI(title="A(gnO)-KAOS", version="3.0.0")

_static_dir = _HERE / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

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
    html_path = _HERE / "static" / "dashboard.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)
