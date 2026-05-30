# ADR-020: Windows Service Strategy

## Estado
Aceptado

## Contexto
Hermes Agent v0.15.2 debe ejecutarse 24/7 en Windows nativo (sin Docker, sin WSL) para:
1. Gateway API (:8642) accesible para todos los agentes KAOS vía MCP
2. Dashboard UI (:9119) para monitoreo visual
3. Kanban dispatcher automático cada 60s
4. Cron jobs programados (health-check, kanban-vacuum, env-integrity)
5. Proveer mensajería asíncrona (Telegram, Discord, WhatsApp)

KAOS no puede depender de Docker en Windows (performance overhead, complejidad de red). 
Hermes Agent corre nativamente como proceso Python, y necesita un mecanismo de 
inicio automático y restart en caso de fallo.

## Alternativas Consideradas

### Alternativa A: Windows Service nativo (sc create)
- ✅ Integración con Services.msc, restart automático nativo
- ❌ Hermes no está diseñado como Windows Service — problemas con session 0 isolation
- ❌ No puede mostrar ventanas ni QR codes (WhatsApp auth)
- ❌ Dificultad para debugging y logs
- Veredicto: ❌ Descartado

### Alternativa B: NSSM (Non-Sucking Service Manager)
- ✅ Wrapper service maduro, restart configurable, log integration
- ✅ Maneja stdout/stderr a archivos
- ❌ Dependencia externa (no en PATH por defecto)
- ❌ No está en el ecosistema Hermes/KAOS
- ❌ Overhead de mantenimiento (binario separado)
- Veredicto: ❌ Descartado — demasiada dependencia externa para un requerimiento simple

### Alternativa C: Windows Task Scheduler (schtasks)
- ✅ Nativo de Windows, sin dependencias externas
- ✅ Trigger al login del usuario (no requiere red)
- ✅ Restart configurable (hasta 3 intentos, cada 5 min)
- ✅ Ejecuta en la sesión del usuario (QR codes visibles)
- ✅ Scripts PowerShell existentes pueden ser la acción
- ❌ No es un "servicio" real (aparece en Task Scheduler, no en Services.msc)
- ❌ Restart limitado a 3 intentos (NSSM ofrece restart infinito)
- Veredicto: ✅ SELECCIONADO

### Alternativa D: Startup folder + restart loop
- ✅ Simple: acceso directo en shell:startup
- ❌ Sin restart automático en caso de crash
- ❌ Sin logging estructurado
- ❌ Ventana de terminal visible
- Veredicto: ❌ Descartado

## Decisión
Usar **Windows Task Scheduler (schtasks)** como mecanismo de servicio, con:
- **Trigger**: Al iniciar sesión del usuario (AtLogOn)
- **Acción**: `powershell.exe -File bin/windows/start-hermes-service.ps1`
- **Restart**: Cada 5 minutos, hasta 3 intentos (RestartCount=3, RestartInterval=5min)
- **Red**: No requerida (gateway local)
- **ExecutionTimeLimit**: 1 día (permite ejecución continua)
- **RunLevel**: Limited (no requiere Admin para ejecución, solo para instalación)

## Scripts

### install-hermes-service.ps1 (Requiere Admin)
- Crea tarea "KAOS Hermes Gateway" en Task Scheduler
- Verifica prerequisitos (script de inicio, execution policy, hermes en PATH)
- Elimina tarea existente antes de recrear
- Configura: AtLogOn, restart 3×5min, sin red, priority 7

### install-hermes-service-ADMIN.ps1
- Wrapper que verifica si la sesión actual es Administrador
- Si no, muestra instrucciones para ejecutar como Admin
- Si sí, delega en install-hermes-service.ps1

### start-hermes-service.ps1
- Verifica que hermes está en PATH
- Inicia `hermes gateway run --port 8642` via Start-Process
- Redirige stdout/stderr a `~/.hermes/logs/gateway-service.log`
- Espera al proceso (WaitForExit) y reporta código de salida

### start-hermes-native.ps1 (Fallback sin Admin)
- Inicia gateway + dashboard + workspace UI manualmente
- Usa WScript.Shell para ocultar ventanas
- Verifica conectividad con Invoke-WebRequest antes de reportar

### verify-dashboard-fix.ps1
- Verifica que el stub dashboard_auth está instalado en site-packages
- Comprueba: __init__.py, middleware.py, import exitoso
- Reporta estado del fix para v0.15.2

## Arquitectura de Inicio

```
Login de Windows
       │
       ▼
Task Scheduler: "KAOS Hermes Gateway"
       │
       ▼
powershell.exe -File start-hermes-service.ps1
       │
       ├── Verifica hermes en PATH
       ├── Verifica puerto 8642 no ocupado
       ├── hermes gateway run --port 8642
       │       └── Gateway API (:8642)
       ├── (Opcional) hermes dashboard --port 9119
       │       └── Dashboard UI (:9119)  
       └── WaitForExit → si crash, Task Scheduler restart (3 intentos)
```

## Requisitos

### Para Instalación
- PowerShell como Administrador
- hermes en PATH (instalado vía pip en venv)
- ExecutionPolicy: RemoteSigned (mínimo)

### Para Ejecución
- Usuario loggeado en Windows
- hermes en PATH
- Puerto 8642 libre
- ~/.hermes/config.yaml (con profiles, kanban, etc.)

## Fallback

Si no hay permisos de Admin, se puede usar `start-hermes-native.ps1`:
```powershell
.\bin\windows\start-hermes-native.ps1
```
Este script inicia gateway y dashboard en ventanas ocultas vía WScript.Shell.
Requiere ejecución manual o acceso directo en shell:startup.

## Consecuencias

### Positivas
+ Sin dependencias externas (NSSM, Docker, WSL)
+ Scripts PowerShell fáciles de mantener y auditar
+ Restart automático en crash (3 intentos)
+ Logs centralizados en ~/.hermes/logs/
+ QR code visible para WhatsApp auth (sesión de usuario)

### Negativas
- No aparece en Services.msc (solo en Task Scheduler)
- Restart limitado a 3 intentos (NSSM ofrece restart infinito)
- Requiere Admin para instalación inicial
- La sesión del usuario debe estar activa (no funciona con cuenta deslogueada)

### Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Hermes crash loop | Baja | Alto | 3 restart intentos, luego alerta ntfy |
| Usuario cierra sesión | Media | Alto | Trigger AtLogOn reinicia al volver |
| Puerto 8642 ocupado | Baja | Medio | start-hermes-service.ps1 verifica con netstat |
| Task Scheduler no inicia | Baja | Alto | start-hermes-native.ps1 como fallback manual |

## ADRs Relacionados
- **ADR-011**: Hermes Integration Strategy (arquitectura general de Hermes en KAOS)

## Referencias
- `bin/windows/install-hermes-service.ps1`: Instalación schtasks
- `bin/windows/install-hermes-service-ADMIN.ps1`: Wrapper Admin
- `bin/windows/start-hermes-service.ps1`: Script de inicio principal
- `bin/windows/start-hermes-native.ps1`: Fallback manual
- `bin/windows/verify-dashboard-fix.ps1`: Verificación dashboard_auth
- `~/.hermes/config.yaml`: Configuración de Hermes
