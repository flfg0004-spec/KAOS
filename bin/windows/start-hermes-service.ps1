<#
.SYNOPSIS
    Inicia el gateway de Hermes Agent en puerto 8642.
.DESCRIPTION
    Ejecuta `hermes gateway --port 8642` usando el entorno virtual de Hermes.
    Usado por install-hermes-service.ps1 como acción de tarea programada.
.NOTES
    Logs se escriben a ~/.hermes/logs/gateway-service.log
#>

$ErrorActionPreference = "Stop"

# ─── Config ───────────────────────────────────────────────────────────────
$HermesHome = Join-Path $env:USERPROFILE ".hermes"
$LogDir     = Join-Path $HermesHome "logs"
$LogFile    = Join-Path $LogDir "gateway-service.log"
$Port       = 8642

# ─── Logging ──────────────────────────────────────────────────────────────
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp [start-hermes-service] $Message" | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

Write-Log "=== Iniciando Hermes Gateway (puerto $Port) ==="

# ─── Verificar que hermes esté en PATH ───────────────────────────────────
try {
    $HermesVersion = & hermes --version 2>&1
    Write-Log "Hermes version: $HermesVersion"
} catch {
    Write-Log "ERROR: hermes no encontrado en PATH"
    exit 1
}

# ─── Verificar que el puerto no esté ocupado ─────────────────────────────
$ExistingProcess = netstat -ano | Select-String ":$Port\s"
if ($ExistingProcess) {
    Write-Log "AVISO: Puerto $Port ya está en uso. Intentando arranque de todas formas."
}

# ─── Iniciar gateway ─────────────────────────────────────────────────────
try {
    $env:HERMES_NONINTERACTIVE = "1"
    $process = Start-Process -FilePath "hermes" `
        -ArgumentList "gateway", "--port", "$Port" `
        -NoNewWindow `
        -PassThru `
        -RedirectStandardOutput $LogFile `
        -RedirectStandardError $LogFile

    Write-Log "Gateway iniciado (PID: $($process.Id))"
    Write-Log "Dashboard: http://localhost:9119"
    Write-Log "Gateway:   http://localhost:$Port"

    # Esperar proceso (la tarea programada corre en foreground)
    $process.WaitForExit()
    $exitCode = $process.ExitCode
    Write-Log "Gateway terminado con código $exitCode"
    exit $exitCode
} catch {
    Write-Log "ERROR al iniciar gateway: $_"
    exit 1
}
