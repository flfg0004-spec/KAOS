# ============================================
# start-hermes-native.ps1
# Inicia Hermes Agent nativamente (sin Docker)
# ============================================
# Uso: .\bin\windows\start-hermes-native.ps1
# Detener: .\bin\windows\stop-hermes-native.ps1

$LOG_DIR = "$env:TEMP"
$GATEWAY_LOG = "$LOG_DIR\hermes-gateway.log"
$DASHBOARD_LOG = "$LOG_DIR\hermes-dashboard.log"
$WORKSPACE_LOG = "$LOG_DIR\hermes-workspace.log"
$KAOS_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Hermes Agent Native - Startup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Leer API_KEY del .env de Hermes
$hermesEnv = "$env:USERPROFILE\.hermes\.env"
$apiKeyLine = Select-String -Path $hermesEnv -Pattern "^API_SERVER_KEY=" -SimpleMatch | Select-Object -Last 1
$apiKey = if ($apiKeyLine) { ($apiKeyLine.Line -split "=", 2)[1] } else { "" }

if (-not $apiKey) {
    Write-Host "[WARN] API_SERVER_KEY no encontrada en .hermes/.env" -ForegroundColor Yellow
    Write-Host "       El gateway se iniciara sin autenticacion" -ForegroundColor Yellow
}

# 2. Verificar que API_SERVER esté configurado
$apiEnabled = (Select-String -Path $hermesEnv -Pattern "API_SERVER_ENABLED=true" -SimpleMatch -Quiet)
if (-not $apiEnabled) {
    Write-Host "[WARN] API_SERVER_ENABLED no esta en .hermes/.env" -ForegroundColor Yellow
    Write-Host "       Agregando..." -ForegroundColor Yellow
    Add-Content $hermesEnv "`nAPI_SERVER_ENABLED=true`nAPI_SERVER_HOST=127.0.0.1`nGATEWAY_ALLOW_ALL_USERS=false"
}

# 3. Iniciar Gateway
Write-Host "[1/3] Iniciando Hermes Gateway (:8642)..." -ForegroundColor Yellow
$proc = Get-Process -Name "hermes" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "gateway" }
if (-not $proc) {
    $wsh = New-Object -ComObject WScript.Shell
    $wsh.Run("cmd.exe /c hermes gateway run > $GATEWAY_LOG 2>&1", 0, $false)
    Start-Sleep 3
    Write-Host "      Gateway iniciado" -ForegroundColor Green
} else {
    Write-Host "      Gateway ya estaba corriendo" -ForegroundColor Green
}

# 4. Iniciar Dashboard
Write-Host "[2/3] Iniciando Hermes Dashboard (:9119)..." -ForegroundColor Yellow
try {
    $dashCheck = Invoke-WebRequest -Uri "http://127.0.0.1:9119/api/status" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "      Dashboard ya estaba corriendo" -ForegroundColor Green
} catch {
    $wsh = New-Object -ComObject WScript.Shell
    $wsh.Run("cmd.exe /c hermes dashboard --port 9119 --no-open --skip-build > $DASHBOARD_LOG 2>&1", 0, $false)
    Start-Sleep 5
    Write-Host "      Dashboard iniciado" -ForegroundColor Green
}

# 5. Iniciar Workspace UI (con API_KEY para autenticacion)
Write-Host "[3/3] Iniciando Workspace UI (:3002)..." -ForegroundColor Yellow
try {
    $wsCheck = Invoke-WebRequest -Uri "http://127.0.0.1:3002/api/healthcheck" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "      Workspace UI ya estaba corriendo" -ForegroundColor Green
} catch {
    $wsh = New-Object -ComObject WScript.Shell
    $wsEnv = "set NODE_OPTIONS=--max-old-space-size=2048"
    if ($apiKey) { $wsEnv += " && set HERMES_API_TOKEN=$apiKey" }
    $wsh.Run("cmd.exe /c cd /d $KAOS_ROOT\.workspace && $wsEnv && npx vite dev --port 3002 > $WORKSPACE_LOG 2>&1", 0, $false)
    Start-Sleep 8
    Write-Host "      Workspace UI iniciado" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Hermes nativo listo" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nEndpoints:"
Write-Host "  Gateway:        http://localhost:8642"
if ($apiKey) { Write-Host "  API Key:        $apiKey" -ForegroundColor DarkGray }
Write-Host "  Dashboard:      http://localhost:9119"
Write-Host "  Workspace UI:   http://localhost:3002"
Write-Host ""
