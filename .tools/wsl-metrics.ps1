# ==============================================================================
# KAOS WSL Metrics Pipeline (wsl-metrics.ps1)
# Recolecta métricas de WSL2, Docker, y recursos del host en intervalos.
# Output: .vault/quality/timeseries/wsl-metrics.json
# Integración: alert_daemon.py consume este archivo para alertas.
# ==============================================================================

param(
    [int]$IntervalSeconds = 300,
    [int]$MaxEntries = 288,
    [string]$DistroName = "Ubuntu"
)

$METRICS_FILE = Join-Path $PSScriptRoot "..\.vault\quality\timeseries\wsl-metrics.json"
$MAX_ENTRIES = $MaxEntries

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message"
}

function Collect-Metrics {
    $timestamp = (Get-Date).ToString("o")
    $metrics = @{ timestamp = $timestamp }

    # RAM dentro de WSL
    try {
        $freeOutput = wsl.exe -d $DistroName free -b 2>$null
        if ($freeOutput) {
            $memLine = $freeOutput | Select-String -Pattern "^Mem:"
            if ($memLine) {
                $parts = -split $memLine
                $metrics["wsl_mem_total"] = [long]$parts[1]
                $metrics["wsl_mem_used"] = [long]$parts[2]
                $metrics["wsl_mem_free"] = [long]$parts[3]
                $metrics["wsl_mem_available"] = [long]$parts[6]
            }
            $swapLine = $freeOutput | Select-String -Pattern "^Swap:"
            if ($swapLine) {
                $parts = -split $swapLine
                $metrics["wsl_swap_total"] = [long]$parts[1]
                $metrics["wsl_swap_used"] = [long]$parts[2]
            }
        }
    } catch {
        $metrics["wsl_mem_error"] = $_.Exception.Message
    }

    # CPU load
    try {
        $loadOutput = wsl.exe -d $DistroName cat /proc/loadavg 2>$null
        if ($loadOutput) {
            $loads = -split $loadOutput
            $metrics["wsl_load_1min"] = [double]$loads[0]
            $metrics["wsl_load_5min"] = [double]$loads[1]
            $metrics["wsl_load_15min"] = [double]$loads[2]
        }
    } catch {}

    # Docker containers
    try {
        $containerOutput = wsl.exe -d $DistroName docker ps -q 2>$null
        $containers = $containerOutput.ToString().Trim()
        $metrics["docker_containers_active"] = if ([string]::IsNullOrWhiteSpace($containers)) { 0 } else { (-split $containers).Count }
    } catch {
        $metrics["docker_containers_active"] = -1
    }

    # wslhost.exe RAM en Windows
    try {
        $wslProcess = Get-Process -Name wslhost -ErrorAction SilentlyContinue
        if ($wslProcess) {
            $metrics["wslhost_ram_mb"] = [Math]::Round(($wslProcess | Measure-Object -Property WorkingSet64 -Sum).Sum / 1MB, 2)
        } else {
            $metrics["wslhost_ram_mb"] = 0
        }
    } catch {}

    # VHDX size
    try {
        $vhdFolder = "$env:LOCALAPPDATA\WSL"
        if (Test-Path $vhdFolder) {
            $vhdxFiles = Get-ChildItem -Path $vhdFolder -Filter "*.vhdx" -Recurse -ErrorAction SilentlyContinue
            $metrics["vhdx_count"] = $vhdxFiles.Count
            $metrics["vhdx_total_mb"] = [Math]::Round(($vhdxFiles | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
        }
    } catch {}

    # Uptime WSL
    try {
        $uptime = wsl.exe -d $DistroName uptime -s 2>$null
        if ($uptime) {
            $metrics["wsl_boot_time"] = $uptime.ToString().Trim()
        }
    } catch {}

    return $metrics
}

function Append-Metrics($newEntry) {
    $data = @{ entries = @() }
    if (Test-Path $METRICS_FILE) {
        try {
            $data = Get-Content $METRICS_FILE -Raw | ConvertFrom-Json
            if (-not $data.entries) { $data.entries = @() }
        } catch {
            $data = @{ entries = @() }
        }
    }
    $data.entries += $newEntry
    if ($data.entries.Count -gt $MAX_ENTRIES) {
        $data.entries = $data.entries[-$MAX_ENTRIES..-1]
    }
    $dir = Split-Path $METRICS_FILE -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $data | ConvertTo-Json -Depth 5 | Out-File $METRICS_FILE -Encoding utf8
}

Write-Log "KAOS WSL Metrics Pipeline iniciado — Intervalo: ${IntervalSeconds}s, Max entries: $MAX_ENTRIES"
Write-Log "Output: $METRICS_FILE"

while ($true) {
    $metrics = Collect-Metrics
    Append-Metrics $metrics
    Write-Log "Métricas recolectadas: RAM=$(if ($metrics.wsl_mem_used) { '{0:N0}' -f ($metrics.wsl_mem_used/1MB) + 'MB' } else { 'N/A' }), Containers=$($metrics.docker_containers_active), wslhost=$($metrics.wslhost_ram_mb)MB"
    Start-Sleep -Seconds $IntervalSeconds
}
