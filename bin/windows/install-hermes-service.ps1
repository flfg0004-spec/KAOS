<#
.SYNOPSIS
    Registra una tarea programada en Windows para iniciar Hermes Gateway al login.
.DESCRIPTION
    Crea la tarea "KAOS Hermes Gateway" en Task Scheduler con:
    - Trigger: al iniciar sesión del usuario
    - Acción: ejecutar start-hermes-service.ps1
    - Reinicio automático si falla (cada 5 min, hasta 3 intentos)
    - Ejecutar aunque no haya red
.NOTES
    Ejecutar como Administrador:右-click → "Run with PowerShell as Administrator"
#>

#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

# ─── Config ───────────────────────────────────────────────────────────────
$TaskName      = "KAOS Hermes Gateway"
$TaskDesc      = "Inicia Hermes Agent Gateway (puerto 8642) al iniciar sesión"
$ScriptDir     = Split-Path -Parent $PSCommandPath
$StartScript   = Join-Path $ScriptDir "start-hermes-service.ps1"
$LogDir        = Join-Path $env:USERPROFILE ".hermes" "logs"
$TaskLog       = Join-Path $LogDir "install-hermes-service.log"

# ─── Helper ───────────────────────────────────────────────────────────────
function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp [install-hermes-service] $Message" | Out-File -FilePath $TaskLog -Append -Encoding UTF8
}

Write-Log "=== Instalando tarea programada: $TaskName ==="

# ─── Verificar prerequisitos ──────────────────────────────────────────────

# 1. Script de inicio debe existir
if (-not (Test-Path $StartScript)) {
    Write-Log "ERROR: No se encuentra $StartScript"
    Write-Host "[ERROR] No se encuentra $StartScript" -ForegroundColor Red
    exit 1
}
Write-Log "Script de inicio: $StartScript"

# 2. PowerShell execution policy
$CurrentPolicy = Get-ExecutionPolicy -Scope CurrentUser
if ($CurrentPolicy -eq "Restricted") {
    Write-Log "AVISO: Execution Policy es Restricted. Cambiando a RemoteSigned para CurrentUser."
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
}
Write-Log "ExecutionPolicy: $(Get-ExecutionPolicy -Scope CurrentUser)"

# 3. Verificar que hermes existe en PATH
try {
    $HermesVersion = & hermes --version 2>&1
    Write-Log "Hermes detectado: $HermesVersion"
} catch {
    Write-Warning "hermes no está en PATH. La tarea se creará pero fallará al ejecutarse."
    Write-Log "ADVERTENCIA: hermes no está en PATH"
}

# 4. Crear log directory si no existe
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-Log "Creado directorio de logs: $LogDir"
}

# ─── Eliminar tarea existente si la hay ───────────────────────────────────
$Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($Existing) {
    Write-Log "Tarea existente encontrada. Eliminando..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Log "Tarea eliminada."
}

# ─── Crear tarea programada ───────────────────────────────────────────────

# Acción: ejecutar PowerShell con el script de inicio
$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StartScript`""

# Trigger: al iniciar sesión
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Settings: reiniciar si falla
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Days 1) `
    -Priority 7

# Condiciones: ejecutar sin red
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType S4U `
    -RunLevel Limited

# Registrar tarea
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Description $TaskDesc `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Force

    Write-Log "Tarea '$TaskName' registrada exitosamente."
    Write-Host "[OK] Tarea '$TaskName' registrada exitosamente." -ForegroundColor Green

    # Mostrar resumen
    $Task = Get-ScheduledTask -TaskName $TaskName
    Write-Host "`n=== Resumen de la Tarea ===" -ForegroundColor Cyan
    Write-Host "Nombre:    $($Task.TaskName)"
    Write-Host "Estado:    $($Task.State)"
    Write-Host "Acción:    powershell.exe -File $StartScript"
    Write-Host "Trigger:   Al iniciar sesión ($env:USERNAME)"
    Write-Host "Reinicio:  Cada 5 min, hasta 3 intentos"
    Write-Host "Red:       No requerida (gateway local)"
    Write-Host "Log:       $TaskLog"
    Write-Host "`nPara probar manualmente:"
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Yellow
    Write-Host "  O ejecuta: $StartScript`n" -ForegroundColor Yellow

} catch {
    Write-Log "ERROR al registrar tarea: $_"
    Write-Host "[ERROR] No se pudo registrar la tarea: $_" -ForegroundColor Red
    exit 1
}
