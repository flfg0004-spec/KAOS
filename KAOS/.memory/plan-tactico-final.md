# Plan Táctico Integral — Hermes Workspace + Swarm Workers Híbridos

**Versión**: 1.0 (Final)
**Fecha**: 2026-05-26
**Responsable**: Kratos (implementación), Metis (estrategia), Kosmos (arquitectura)
**Perfil**: desarrollo (score compuesto objetivo ≥ 70)

---

## 1. Resumen Ejecutivo

Implementar Hermes Workspace Swarm Mode como capa visual/orquestación de KAOS, adjuntando al hermes.exe existente (v0.14.0, 593 commits behind). WorkerManager híbrido con NativeWorker (subprocess + ThreadPool, default) y TmuxWorker (WSL2 + tmux 3.6, opt-in). Pipeline LangGraph actual corre en paralelo sin modificaciones. Workspace en :3001.

---

## 2. Roadmap Semanal

### S1: Fundación — Hermes Update + Gateway Setup

| Día | Actividad | Comandos |
|-----|-----------|----------|
| 1 | Backup kanban.db | `Copy-Item "$env:LOCALAPPDATA\hermes\kanban.db" ".backup\kanban.db"` |
| 1 | hermes update | `& "$env:LOCALAPPDATA\hermes\hermes.exe" update` |
| 1 | Verificar versión | `& "$env:LOCALAPPDATA\hermes\hermes.exe" --version` |
| 2 | Smoke test Telegram | `& "$env:LOCALAPPDATA\hermes\hermes.exe" send --to telegram "S1 smoke test"` |
| 2 | Gateway en :3001 | `& "$env:LOCALAPPDATA\hermes\hermes.exe" gateway --port 3001` |
| 3 | Verificar health | `curl http://localhost:3001/health` |
| 3 | Crear workspace | `& "$env:LOCALAPPDATA\hermes\hermes.exe" workspace create --name kaos-swarm` |
| 4 | Verificar integridad pipeline | `py -3 .memory\_scripts\lib\pipeline.py --smoke` |
| 5 | Documentar puerto y acceso | Escribir docs/hermes-workspace.md |

**Smoke test S1:**
```powershell
& "$env:LOCALAPPDATA\hermes\hermes.exe" update
& "$env:LOCALAPPDATA\hermes\hermes.exe" --version
& "$env:LOCALAPPDATA\hermes\hermes.exe" gateway --port 3001
curl http://localhost:3001/health
```

### S2: NativeWorker Core

Archivos a crear:
```
.memory/_scripts/swarm/
├── __init__.py
├── launcher.py
├── worker_manager.py
├── config.yaml
├── backends/
│   ├── __init__.py
│   └── native.py
└── roles/
    ├── __init__.py
    ├── base.py
    ├── researcher.py
    ├── architect.py
    ├── strategist.py
    └── curator.py
```

### S3: TmuxWorker + CLI

```
.memory/_scripts/swarm/backends/
└── tmux.py
```

### S4: Integración Workspace + Swarm + QA

---

## 3. Arquitectura Workers

```
WorkerManager (interfaz abstracta + factory)
├── NativeWorker (subprocess.Popen + JSON-RPC pipe + ThreadPool)  ← DEFAULT
└── TmuxWorker (WSL2 + tmux sessions + WSL pipe)                  ← OPT-IN

Roles:
├── researcher → aletheia_node()
├── architect  → kosmos_node()
├── strategist → metis_node()
└── curator    → mnemosyne_node()
```

---

## 4. Configuración

```yaml
backend:
  default: native
  native:
    max_workers: 2
    python: python
    pipe_timeout: 30
  tmux:
    wsl_distro: Ubuntu
    tmux_version: "3.6"
    session_prefix: "kaos-worker-"
```

---

## 5. Riesgos Clave

| # | Riesgo | Prob | Impacto | Mitigación |
|---|--------|:----:|:-------:|------------|
| R1 | hermes update rompe kanban.db | Media | Alto | Backup previo |
| R2 | Puerto 3001 ocupado | Baja | Medio | Usar :3002 |
| R3 | Workers híbridos divergentes | Media | Alto | Interfaz común + tests |
| R4 | WSL2 no disponible para TmuxWorker | Baja | Medio | Graceful fallback a Native |

---

## 6. Archivos

**12 nuevos + 1 modificación**

Ver sección 8 del documento completo para lista detallada.
