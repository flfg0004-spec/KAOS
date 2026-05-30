param(
    [switch]$Help
)

if ($Help) {
    Write-Host @"

KAOS Docker Status Checker
============================
Uso: .\status-kaos.ps1

Muestra el estado de todos los servicios Docker de KAOS.

"@ -ForegroundColor Cyan
    return
}

$kaosRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$composeFile = Join-Path $kaosRoot "docker-compose.yml"

$dockerless = [Environment]::GetEnvironmentVariable("DOCKERLESS_MODE", "User") -eq "true"
if ($env:DOCKERLESS_MODE -eq "true") { $dockerless = $true }

if ($dockerless) {
    Write-Host "DOCKERLESS_MODE is active — skipping Docker" -ForegroundColor Yellow
    return
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   KAOS Service Status" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Check WSL2
Write-Host "[WSL2]" -ForegroundColor Yellow
$hasWsl = $null -ne (Get-Command wsl.exe -ErrorAction SilentlyContinue)
$hasDockerExe = $null -ne (Get-Command docker.exe -ErrorAction SilentlyContinue)

if ($hasWsl) {
    $wslOk = & wsl.exe -d Ubuntu -u root -- echo "ok" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Estado:     Activo" -ForegroundColor Green
    } else {
        Write-Host "  Estado:     Inactivo" -ForegroundColor Red
    }
} elseif ($hasDockerExe) {
    Write-Host "  Entorno:    Windows nativo (sin WSL)" -ForegroundColor Yellow
} else {
    Write-Host "  Estado:     No disponible" -ForegroundColor Red
}

# 2. Check Docker
Write-Host "`n[Docker]" -ForegroundColor Yellow
if ($hasWsl) {
    $dockerStatus = & wsl.exe -d Ubuntu -u root -- systemctl is-active docker 2>&1
    if ($dockerStatus -eq "active") {
        Write-Host "  Daemon:     Activo" -ForegroundColor Green
    } else {
        Write-Host "  Daemon:     Inactivo" -ForegroundColor Red
    }
} elseif ($hasDockerExe) {
    $dockerVersion = & docker.exe version --format "{{.Server.Version}}" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Daemon:     Activo (v$dockerVersion)" -ForegroundColor Green
    } else {
        Write-Host "  Daemon:     Inactivo" -ForegroundColor Red
    }
}

# 3. Containers via compose ps
Write-Host "`n[Contenedores KAOS]" -ForegroundColor Yellow
if ($hasWsl) {
    $psOutput = & wsl.exe -d Ubuntu -- docker compose -f (wslpath -m $composeFile) ps --all 2>&1
} elseif ($hasDockerExe) {
    $psOutput = & docker.exe compose -f $composeFile ps --all 2>&1
}
if ($LASTEXITCODE -eq 0 -and $psOutput) {
    Write-Host $psOutput -ForegroundColor Gray
} else {
    Write-Host "  No containers or unable to list" -ForegroundColor DarkGray
}

# 4. Endpoints — only check if profile is active
Write-Host "`n[Endpoints]" -ForegroundColor Yellow

# Determine which containers are actually running to filter endpoint checks
$activeNames = @()
if ($hasWsl) {
    $rawContainers = & wsl.exe -d Ubuntu -- docker compose -f (wslpath -m $composeFile) ps --status running --format "{{.Names}}" 2>&1
} elseif ($hasDockerExe) {
    $rawContainers = & docker.exe compose -f $composeFile ps --status running --format "{{.Names}}" 2>&1
}
if ($LASTEXITCODE -eq 0 -and $rawContainers) {
    $activeNames = $rawContainers -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
}

$endpoints = @(
    @{ Name = "SearXNG";  Url = "http://127.0.0.1:8888";        Container = "kaos-searxng" }
    @{ Name = "Crawl4AI"; Url = "http://127.0.0.1:11235/health"; Container = "kaos-crawl4ai" }
    @{ Name = "Langfuse"; Url = "http://127.0.0.1:3000";        Container = "kaos-langfuse" }
)

foreach ($ep in $endpoints) {
    $isActive = $activeNames -contains $ep.Container
    if (-not $isActive) {
        Write-Host "  --  $($ep.Name) -> inactive" -ForegroundColor DarkGray
        continue
    }
    try {
        $response = Invoke-WebRequest -Uri $ep.Url -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  OK  $($ep.Name) -> $($ep.Url)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  OFF $($ep.Name) -> $($ep.Url)" -ForegroundColor Red
    }
}

# 5. Resource usage
Write-Host "`n[Recursos]" -ForegroundColor Yellow
if ($hasWsl) {
    $diskUsage = & wsl.exe -d Ubuntu -- docker system df --format "table {{.Type}}\t{{.Size}}\t{{.Reclaimable}}" 2>&1
} elseif ($hasDockerExe) {
    $diskUsage = & docker.exe system df --format "table {{.Type}}\t{{.Size}}\t{{.Reclaimable}}" 2>&1
}
if ($LASTEXITCODE -eq 0 -and $diskUsage) {
    Write-Host $diskUsage -ForegroundColor Gray
}

Write-Host "`n========================================`n" -ForegroundColor Cyan
