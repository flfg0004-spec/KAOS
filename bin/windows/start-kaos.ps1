param(
    [switch]$Core,
    [switch]$Langfuse,
    [switch]$AgnoDb,
    [switch]$Sandbox,
    [switch]$Full,
    [switch]$Help
)

if ($Help) {
    Write-Host @"

KAOS Docker Service Manager
============================
Uso: .\start-kaos.ps1 [opciones]

Opciones:
  -Core       Solo servicios core (SearXNG + Crawl4AI) [por defecto]
  -Langfuse   Incluye Langfuse (observabilidad)
  -AgnoDb     Incluye Agno Postgres (base de datos)
  -Sandbox    Incluye Sandbox (ejecución aislada)
  -Full       Todos los servicios
  -Help       Muestra esta ayuda

Ejemplos:
  .\start-kaos.ps1 -Full
  .\start-kaos.ps1 -Core -Langfuse

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

Write-Host "Starting Docker services: $($profiles -join ', ')" -ForegroundColor Cyan
$profileArgs = $profiles | ForEach-Object { "--profile", $_ }

if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
    $result = & wsl.exe -d Ubuntu -- docker compose -f (wslpath -m $composeFile) up -d @profileArgs 2>&1
} elseif (Get-Command docker.exe -ErrorAction SilentlyContinue) {
    $result = & docker.exe compose -f $composeFile up -d @profileArgs 2>&1
} else {
    Write-Error "Docker not found. Set DOCKERLESS_MODE=true to use native alternatives."
    exit 1
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker failed: $result"
    exit 1
}
Write-Host "✓ Docker services started: $($profiles -join ', ')" -ForegroundColor Green
