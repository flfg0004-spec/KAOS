param(
    [switch]$Core,
    [switch]$Langfuse,
    [switch]$AgnoDb,
    [switch]$Sandbox,
    [switch]$Full,
    [switch]$Help,
    [switch]$Clean
)

if ($Help) {
    Write-Host @"

KAOS Docker Service Stopper
============================
Uso: .\stop-kaos.ps1 [opciones]

Opciones:
  -Core       Solo servicios core (SearXNG + Crawl4AI)
  -Langfuse   Solo Langfuse
  -AgnoDb     Solo Agno Postgres
  -Sandbox    Solo Sandbox
  -Full       Todos los servicios
  -Clean      Limpia contenedores y volúmenes huérfanos
  -Help       Muestra esta ayuda

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

$profiles = @()
if ($Full) {
    $profiles = @("core", "langfuse", "agno-db", "sandbox")
} elseif ($Core -or (-not $Langfuse -and -not $AgnoDb -and -not $Sandbox)) {
    $profiles = @("core")
} else {
    if ($Langfuse) { $profiles += "langfuse" }
    if ($AgnoDb) { $profiles += "agno-db" }
    if ($Sandbox) { $profiles += "sandbox" }
    if ($profiles.Count -eq 0) { $profiles = @("core") }
}

Write-Host "Stopping Docker services: $($profiles -join ', ')" -ForegroundColor Yellow
$profileArgs = $profiles | ForEach-Object { "--profile", $_ }

if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
    if ($Clean) {
        $result = & wsl.exe -d Ubuntu -- docker compose -f (wslpath -m $composeFile) down -v --remove-orphans @profileArgs 2>&1
    } else {
        $result = & wsl.exe -d Ubuntu -- docker compose -f (wslpath -m $composeFile) down @profileArgs 2>&1
    }
} elseif (Get-Command docker.exe -ErrorAction SilentlyContinue) {
    if ($Clean) {
        $result = & docker.exe compose -f $composeFile down -v --remove-orphans @profileArgs 2>&1
    } else {
        $result = & docker.exe compose -f $composeFile down @profileArgs 2>&1
    }
} else {
    Write-Error "Docker not found. Set DOCKERLESS_MODE=true to use native alternatives."
    exit 1
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker failed: $result"
    exit 1
}
Write-Host "✓ Docker services stopped: $($profiles -join ', ')" -ForegroundColor Green

if ($Clean) {
    Write-Host "`nCleaning orphan containers and volumes..." -ForegroundColor Yellow
    if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
        & wsl.exe -d Ubuntu -- docker container prune -f 2>&1 | Out-Null
        & wsl.exe -d Ubuntu -- docker volume prune -f 2>&1 | Out-Null
    } else {
        & docker.exe container prune -f 2>&1 | Out-Null
        & docker.exe volume prune -f 2>&1 | Out-Null
    }
    Write-Host "  Cleanup complete" -ForegroundColor Green
}
