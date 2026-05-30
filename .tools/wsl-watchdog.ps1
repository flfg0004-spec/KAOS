# ==============================================================================
# KAOS WSL Idle Watchdog (wsl-watchdog.ps1)
# Monitorea inactividad de Docker y apaga WSL2 si no hay contenedores activos
# por un período prolongado. Complementa vmIdleTimeout de .wslconfig.
# ==============================================================================

param(
    [int]$IdleTimeoutMinutes = 30,
    [int]$PollIntervalSeconds = 60,
    [string]$DistroName = "Ubuntu"
)

$PID_FILE = Join-Path $PSScriptRoot "..\.ecosystem-keepalive.pid"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] $Message"
    Write-Host $logLine
    $logLine | Out-File -FilePath (Join-Path $PSScriptRoot "..\watchdog.log") -Encoding ascii -Append
}

Write-Log "KAOS WSL Watchdog iniciado — Timeout: ${IdleTimeoutMinutes}min, Poll: ${PollIntervalSeconds}s"
$Pid | Out-File -FilePath $PID_FILE -Encoding ascii -Force

$idleStart = $null

while ($true) {
    $containers = wsl.exe -d $DistroName docker ps -q 2>$null
    $hasContainers = (-not [string]::IsNullOrWhiteSpace($containers))

    if (-not $hasContainers) {
        if (-not $idleStart) {
            $idleStart = Get-Date
            Write-Log "Sin contenedores activos — inicio contador de inactividad"
        } else {
            $idleMinutes = [Math]::Round(((Get-Date) - $idleStart).TotalMinutes, 1)
            if ($idleMinutes -ge $IdleTimeoutMinutes) {
                Write-Log "Inactividad detectada por ${idleMinutes}min ($IdleTimeoutMinutes max). Apagando WSL..."

                wsl.exe -d $DistroName -u root systemctl stop docker 2>$null
                wsl.exe --terminate $DistroName
                wsl.exe --shutdown

                Write-Log "WSL2 apagado — RAM liberada. Watchdog terminado."
                Remove-Item -LiteralPath $PID_FILE -Force -ErrorAction SilentlyContinue
                exit 0
            }
        }
    } else {
        if ($idleStart) {
            $idleMinutes = [Math]::Round(((Get-Date) - $idleStart).TotalMinutes, 1)
            Write-Log "Actividad detectada tras ${idleMinutes}min de inactividad — contador reiniciado"
            $idleStart = $null
        }
    }

    Start-Sleep -Seconds $PollIntervalSeconds
}
