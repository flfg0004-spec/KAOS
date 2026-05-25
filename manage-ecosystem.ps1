# ==============================================================================
# KAOS Ecosystem Orchestrator (manage-ecosystem.ps1)
# Controls and verifies the status of Open WebUI, Langfuse, MCPO, and utility containers.
# Version: 2.0 — Pre-flight YAML validation, per-stack polling, WSL2 health check
# ==============================================================================

$SCRIPTPATH = Join-Path $PSScriptRoot "wsl-docker-manager.ps1"
$KEEPALIVE_FILE = Join-Path $PSScriptRoot ".ecosystem-keepalive.pid"

# ==============================================================================
# HELPERS
# ==============================================================================

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

function Test-WSL2VM {
    <#
    .SYNOPSIS
        Verifica que la VM de WSL2 (Ubuntu) responda correctamente.
    .DESCRIPTION
        Corre 'true' dentro de la distro Ubuntu como root. Si WSL no responde,
        retorna $false con un mensaje descriptivo.
    #>
    try {
        $null = wsl.exe -d Ubuntu -u root true 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] VM WSL2 (Ubuntu) responde correctamente" -ForegroundColor Green
            return $true
        } else {
            Write-Host "[ERROR] VM WSL2 (Ubuntu) devolvió código de salida $LASTEXITCODE" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "[ERROR] Excepción al contactar VM WSL2 (Ubuntu): $_" -ForegroundColor Red
        return $false
    }
}

function Test-DockerComposeConfig {
    <#
    .SYNOPSIS
        Valida la sintaxis YAML de un archivo docker-compose.yml usando
        'docker compose config' antes de intentar levantarlo.
    .DESCRIPTION
        Si la validación falla, muestra el error de stderr con detalle.
        Retorna $true si el YAML es válido, $false si no.
    #>
    param (
        [string]$ComposeFile,
        [string]$StackName
    )

    Write-Host "  Validando sintaxis YAML de $StackName ($ComposeFile)..." -ForegroundColor DarkGray

    $result = wsl.exe -d Ubuntu docker compose -f $ComposeFile config 2>&1
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        $errorRaw = ($result | Out-String).Trim()
        # Extraer solo las líneas de error (diagnóstico útil)
        $errorLines = $errorRaw -split "`n" | Where-Object { $_ -match "(error|Error|failed|not found|invalid|WARNING|parsing)" }
        if ($errorLines.Count -eq 0) { $errorLines = @($errorRaw) }

        Write-Host "  [ERROR] Sintaxis YAML inválida en $displayFile" -ForegroundColor Red
        Write-Host "  " -NoNewline
        Write-Host $($errorLines -join "`n  ") -ForegroundColor DarkRed
        return $false
    }

    Write-Host "  [OK] Sintaxis YAML válida en $displayFile" -ForegroundColor Green
    return $true
}

function Invoke-DockerComposeUp {
    <#
    .SYNOPSIS
        Ejecuta 'docker compose up -d' para un stack, capturando stderr
        para diagnóstico detallado en caso de fallo.
    .RETURNS
        $true si el comando se ejecutó con éxito (exit code 0), $false si no.
    #>
    param (
        [string]$ComposeFile,
        [string]$StackName,
        [string[]]$Services = @()
    )

    Write-Host "  Iniciando $StackName..." -ForegroundColor White

    if ($Services.Count -gt 0) {
        $servicesArg = $Services -join ' '
        $result = wsl.exe -d Ubuntu docker compose -f $ComposeFile up -d $servicesArg 2>&1
    } else {
        $result = wsl.exe -d Ubuntu docker compose -f $ComposeFile up -d 2>&1
    }

    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        $errorDetail = ($result | Out-String).Trim()
        $errorShort = ($errorDetail -split "`n") | Where-Object { $_ -match "(error|Error|failed|denied|not found|timeout|refusing)" }
        if ($errorShort.Count -eq 0) { $errorShort = @($errorDetail.Substring(0, [Math]::Min(300, $errorDetail.Length))) }

        Write-Host "  [ERROR] Fallo al iniciar $StackName (exit code: $exitCode)" -ForegroundColor Red
        Write-Host "  Razón:" -ForegroundColor Yellow
        foreach ($line in $errorShort) {
            Write-Host "    $line" -ForegroundColor DarkRed
        }
        Write-Host "  Posibles soluciones:" -ForegroundColor Yellow
        Write-Host "    1. Verifica que Docker esté corriendo: .\wsl-docker-manager.ps1 status" -ForegroundColor Gray
        Write-Host "    2. Revisa la sintaxis de $(Split-Path $ComposeFile -Leaf)" -ForegroundColor Gray
        Write-Host "    3. Ejecuta manualmente para ver el error completo:" -ForegroundColor Gray
        Write-Host "       wsl.exe -d Ubuntu docker compose -f $ComposeFile up -d" -ForegroundColor DarkGray
        return $false
    }

    Write-Host "  [OK] $StackName iniciado correctamente" -ForegroundColor Green
    return $true
}

# ==============================================================================
# MAIN COMMANDS
# ==============================================================================

function Start-Ecosystem {
    # --------------------------------------------------
    # 1. WSL2 VM Health Check (pre-flight)
    # --------------------------------------------------
    Write-Host "`n=== Verificando VM WSL2 ===" -ForegroundColor Cyan
    if (-not (Test-WSL2VM)) {
        Write-Host "`n[FATAL] La VM de WSL2 (Ubuntu) no responde. Abortando." -ForegroundColor Red
        Write-Host "  Causas posibles:" -ForegroundColor Yellow
        Write-Host "  1. WSL no está instalado → ejecuta: wsl --install -d Ubuntu (como Admin)" -ForegroundColor Gray
        Write-Host "  2. La distro Ubuntu no existe → ejecuta: wsl -l -v" -ForegroundColor Gray
        Write-Host "  3. WSL está en estado inconsistente → ejecuta: wsl --shutdown && wsl -d Ubuntu" -ForegroundColor Gray
        exit 1
    }

    # --------------------------------------------------
    # 2. Iniciar infraestructura WSL/Docker
    # --------------------------------------------------
    Write-Host "`n=== Iniciando Infraestructura WSL2 y Docker ===" -ForegroundColor Cyan
    & $SCRIPTPATH start

    # --------------------------------------------------
    # 3. Levantar pilas de Docker Compose con validación previa
    # --------------------------------------------------
    Write-Host "`n=== Levantando pilas de Docker Compose ===" -ForegroundColor Cyan

    # Definir los stacks a levantar
    $stacks = @(
        @{
            Name     = "Open WebUI & MCPO Bridge"
            File     = "docker-compose.owui.yml"
            Services = @()   # todos los servicios
            Ports    = @(3000, 9090)
        }
        @{
            Name     = "Langfuse Stack (Postgres, Clickhouse, Otel, Langfuse)"
            File     = "docker-compose.langfuse.yml"
            Services = @()
            Ports    = @(3001)
        }
        @{
            Name     = "SearXNG & Crawl4AI"
            File     = ".tools/docker-compose.yml"
            Services = @("searxng", "crawl4ai")
            Ports    = @(8888, 11235)
        }
    )

    $stackOk = @{}  # Nombre del stack -> $true/$false

    foreach ($stack in $stacks) {
        $stackName = $stack.Name
        $composeFile = $stack.File

        Write-Host "`n--- Stack: $stackName ---" -ForegroundColor Cyan

        # Pre-flight YAML validation (T2.1)
        if (-not (Test-DockerComposeConfig -ComposeFile $composeFile -StackName $stackName)) {
            Write-Host "  [SKIP] $stackName NO se levantará (YAML inválido)." -ForegroundColor Yellow
            $stackOk[$stackName] = $false
            continue
        }

        # Levantar el stack (T2.4: captura stderr detallado)
        $success = Invoke-DockerComposeUp -ComposeFile $composeFile -StackName $stackName -Services $stack.Services
        $stackOk[$stackName] = $success
    }

    # --------------------------------------------------
    # 4. Polling inteligente por stack (T2.2 + T2.3)
    # --------------------------------------------------
    Write-Host "`n=== Verificando disponibilidad de los servicios principales ===" -ForegroundColor Cyan

    # Construir lista de endpoints a verificar, solo para stacks que se iniciaron bien
    $endpointChecks = @()

    if ($stackOk["Open WebUI & MCPO Bridge"]) {
        $endpointChecks += @(
            @{ Url = "http://127.0.0.1:3000";    Name = "Open WebUI" }
            @{ Url = "http://127.0.0.1:9090/docs"; Name = "MCPO Bridge" }
        )
    }
    if ($stackOk["Langfuse Stack (Postgres, Clickhouse, Otel, Langfuse)"]) {
        $endpointChecks += @{ Url = "http://127.0.0.1:3001"; Name = "Langfuse" }
    }

    if ($endpointChecks.Count -eq 0) {
        Write-Host "`n[ALERTA] Ningún stack se inició correctamente. No hay servicios que verificar." -ForegroundColor Yellow
        Write-Host "  Revisa los errores anteriores y corrige los problemas antes de reintentar." -ForegroundColor Gray
        return
    }

    # Polling extendido: 30 intentos × 6s = 180s (T2.2)
    $attempts = 0
    $maxAttempts = 30
    $allReady = $false

    while ($attempts -lt $maxAttempts -and -not $allReady) {
        Write-Host "  Comprobando servicios (Intento $($attempts + 1)/$maxAttempts)..." -ForegroundColor Gray
        Start-Sleep -Seconds 6

        $pending = @()
        foreach ($check in $endpointChecks) {
            $ready = Test-Endpoint -Url $check.Url -Name $check.Name
            if (-not $ready) {
                $pending += $check.Name
            }
        }

        $allReady = ($pending.Count -eq 0)
        $attempts++
    }

    if ($allReady) {
        Write-Host "`n[ÉXITO] Todo el ecosistema KAOS está arriba y listo para usar." -ForegroundColor Green
        Write-Host "  - Open WebUI:    http://localhost:3000" -ForegroundColor Gray
        Write-Host "  - Langfuse:      http://localhost:3001" -ForegroundColor Gray
        Write-Host "  - MCPO Bridge:   http://localhost:9090" -ForegroundColor Gray
        Write-Host "  - SearXNG:       http://localhost:8888" -ForegroundColor Gray
        Write-Host "  - Crawl4AI:      http://localhost:11235" -ForegroundColor Gray
    } else {
        Write-Host "`n[ALERTA] Pasaron $maxAttempts intentos sin que todos los servicios respondan." -ForegroundColor Yellow
        if ($pending.Count -gt 0) {
            Write-Host "  Pendientes: $($pending -join ', ')" -ForegroundColor Yellow
            Write-Host "  Posibles causas:" -ForegroundColor Gray
            Write-Host "  1. Las imágenes Docker aún se están descargando (slow connection)" -ForegroundColor Gray
            Write-Host "  2. Los contenedores requieren más tiempo (verifica con: docker ps)" -ForegroundColor Gray
            Write-Host "  3. Error en la configuración del contenedor (revisa logs)" -ForegroundColor Gray
            Write-Host "  Para ver el progreso: .\manage-ecosystem.ps1 status" -ForegroundColor Gray
        }
    }

    # --------------------------------------------------
    # 5. Iniciar keepalive para mantener WSL2 activo
    # --------------------------------------------------
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

    $stacks = @(
        @{ Name = "Open WebUI & MCPO";       File = "docker-compose.owui.yml" }
        @{ Name = "Langfuse Stack";          File = "docker-compose.langfuse.yml" }
        @{ Name = "SearXNG & Crawl4AI";      File = ".tools/docker-compose.yml" }
    )

    foreach ($stack in $stacks) {
        Write-Host "  Apagando $($stack.Name)..." -ForegroundColor White
        $result = wsl.exe -d Ubuntu docker compose -f $($stack.File) down 2>&1
        if ($LASTEXITCODE -ne 0) {
            $errMsg = ($result | Out-String).Trim()
            Write-Host "  [WARN] $($stack.Name) reportó problemas al detenerse:" -ForegroundColor Yellow
            Write-Host "    $errMsg" -ForegroundColor DarkGray
        } else {
            Write-Host "  [OK] $($stack.Name) detenido" -ForegroundColor Green
        }
    }

    Write-Host "`n=== Apagando WSL2 y liberando memoria RAM ===" -ForegroundColor Cyan
    & $SCRIPTPATH stop
}

function Show-EcosystemStatus {
    & $SCRIPTPATH status

    Write-Host "`n=== Verificación de Endpoints Locales ===" -ForegroundColor Cyan
    $null = Test-Endpoint "http://127.0.0.1:3000"           "Open WebUI (Chat / Dashboard)"
    $null = Test-Endpoint "http://127.0.0.1:3001"           "Langfuse (Observabilidad)"
    $null = Test-Endpoint "http://127.0.0.1:9090/docs"      "MCPO Bridge"
    $null = Test-Endpoint "http://127.0.0.1:8888"           "SearXNG Metasearch"
    $null = Test-Endpoint "http://127.0.0.1:11235/health"   "Crawl4AI API"
}

# ==============================================================================
# ENRUTAMIENTO
# ==============================================================================
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
