# ==============================================================================
# KAOS Ecosystem Orchestrator (manage-ecosystem.ps1)
# Controls and verifies the status of Open WebUI, Langfuse, MCPO, and utility containers.
# ==============================================================================

$SCRIPTPATH = Join-Path $PSScriptRoot "wsl-docker-manager.ps1"
$KEEPALIVE_FILE = Join-Path $PSScriptRoot ".ecosystem-keepalive.pid"

function Test-Endpoint {
    param (
        [string]$Url,
        [string]$Name
    )
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] $Name está activo y respondiendo en $Url" -ForegroundColor Green
            return $true
        } else {
            Write-Host "[WAIT] $Name devolvió estado $($response.StatusCode) en $Url" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "[WAIT] $Name no responde aún en $Url" -ForegroundColor DarkGray
        return $false
    }
}

function Start-Ecosystem {
    Write-Host "`n=== Iniciando Infraestructura WSL2 y Docker ===" -ForegroundColor Cyan
    & $SCRIPTPATH start
    
    Write-Host "`n=== Levantando pilas de Docker Compose ===" -ForegroundColor Cyan
    
    # 1. Levantar Open WebUI + MCPO
    Write-Host "Iniciando Open WebUI & MCPO Bridge (Puerto 3000 / 9090)..." -ForegroundColor White
    wsl.exe -d Ubuntu docker compose -f docker-compose.owui.yml up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Fallo al iniciar Open WebUI."
    }
    
    # 2. Levantar Langfuse Stack (Postgres, Clickhouse, Otel Collector, Langfuse en puerto 3001)
    Write-Host "Iniciando Langfuse, Clickhouse, Otel Collector (Puerto 3001)..." -ForegroundColor White
    wsl.exe -d Ubuntu docker compose -f docker-compose.langfuse.yml up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Fallo al iniciar Langfuse Stack."
    }

    # 3. Levantar únicamente SearXNG y Crawl4AI para evitar colisión en puerto 3000 con el Langfuse viejo
    Write-Host "Iniciando SearXNG & Crawl4AI (Puertos 8888 / 11235)..." -ForegroundColor White
    wsl.exe -d Ubuntu docker compose -f .tools/docker-compose.yml up -d searxng crawl4ai
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Fallo al iniciar SearXNG o Crawl4AI."
    }
    
    # Verificación activa con polling
    Write-Host "`n=== Verificando disponibilidad de los servicios principales ===" -ForegroundColor Cyan
    $attempts = 0
    $maxAttempts = 10
    $allReady = $false
    
    while ($attempts -lt $maxAttempts -and -not $allReady) {
        Write-Host "Comprobando servicios (Intento $($attempts + 1)/$maxAttempts)..." -ForegroundColor Gray
        Start-Sleep -Seconds 6
        
        $owui = Test-Endpoint "http://127.0.0.1:3000" "Open WebUI"
        $lf = Test-Endpoint "http://127.0.0.1:3001" "Langfuse"
        $mcpo = Test-Endpoint "http://127.0.0.1:9090/docs" "MCPO Bridge"
        
        $allReady = $owui -and $lf -and $mcpo
        $attempts++
    }
    
    if ($allReady) {
        Write-Host "`n[ÉXITO] Todo el ecosistema KAOS está arriba y listo para usar." -ForegroundColor Green
        Write-Host "  - Open WebUI: http://localhost:3000" -ForegroundColor Gray
        Write-Host "  - Langfuse:   http://localhost:3001" -ForegroundColor Gray
        Write-Host "  - MCPO Bridge: http://localhost:9090" -ForegroundColor Gray
    } else {
        Write-Host "`n[ALERTA] Algunos servicios están tardando más en responder. Las imágenes pueden estarse descargando de los registros de Docker." -ForegroundColor Yellow
        Write-Host "Puedes verificar el progreso de las descargas y contenedores ejecutando: .\manage-ecosystem.ps1 status" -ForegroundColor Gray
    }

    # Iniciar keepalive para mantener WSL2 activo en background
    $keepAlive = Start-Process -NoNewWindow -PassThru -FilePath wsl.exe -ArgumentList "-d Ubuntu -u root sleep infinity"
    $keepAlive.Id | Out-File -FilePath $KEEPALIVE_FILE -Encoding ascii -Force
    Write-Host "[OK] Keepalive WSL2 activo (PID: $($keepAlive.Id)) - VM se mantendrá encendida" -ForegroundColor Green
}

function Stop-Ecosystem {
    Write-Host "`n=== Deteniendo todas las pilas de Docker Compose ===" -ForegroundColor Cyan
    
    # Matar keepalive primero
    if (Test-Path -LiteralPath $KEEPALIVE_FILE) {
        $pid = Get-Content -LiteralPath $KEEPALIVE_FILE -Raw
        $pid = $pid.Trim()
        if ($pid -match '^\d+$') {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host "[OK] Keepalive WSL2 detenido (PID: $pid)" -ForegroundColor Green
        }
        Remove-Item -LiteralPath $KEEPALIVE_FILE -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "Apagando Open WebUI & MCPO..." -ForegroundColor White
    wsl.exe -d Ubuntu docker compose -f docker-compose.owui.yml down
    
    Write-Host "Apagando Langfuse Stack..." -ForegroundColor White
    wsl.exe -d Ubuntu docker compose -f docker-compose.langfuse.yml down
    
    Write-Host "Apagando SearXNG & Crawl4AI..." -ForegroundColor White
    wsl.exe -d Ubuntu docker compose -f .tools/docker-compose.yml down
    
    Write-Host "`n=== Apagando WSL2 y liberando memoria RAM ===" -ForegroundColor Cyan
    & $SCRIPTPATH stop
}

function Show-EcosystemStatus {
    & $SCRIPTPATH status
    
    Write-Host "`n=== Verificación de Endpoints Locales ===" -ForegroundColor Cyan
    $null = Test-Endpoint "http://127.0.0.1:3000" "Open WebUI (Chat / Dashboard)"
    $null = Test-Endpoint "http://127.0.0.1:3001" "Langfuse (Observabilidad)"
    $null = Test-Endpoint "http://127.0.0.1:9090/docs" "MCPO Bridge"
    $null = Test-Endpoint "http://127.0.0.1:8888" "SearXNG Metasearch"
    $null = Test-Endpoint "http://127.0.0.1:11235/health" "Crawl4AI API"
}

# Enrutamiento de parámetros
if ($args.Count -eq 0) {
    Write-Host "`n=== Uso de KAOS Ecosystem Orchestrator ===" -ForegroundColor Cyan
    Write-Host "  .\manage-ecosystem.ps1 start   - Inicia todo el ecosistema (WSL, Docker, Open WebUI, Langfuse, etc.)"
    Write-Host "  .\manage-ecosystem.ps1 stop    - Apaga limpia y ordenadamente todo el ecosistema y libera RAM"
    Write-Host "  .\manage-ecosystem.ps1 status  - Comprueba la salud y los puertos de cada herramienta"
    Write-Host ""
    exit 0
}

switch ($args[0]) {
    "start"  { Start-Ecosystem }
    "stop"   { Stop-Ecosystem }
    "status" { Show-EcosystemStatus }
    default {
        Write-Host "Comando no válido. Opciones: start, stop, status" -ForegroundColor Red
    }
}
