# KAOS kitty-bridge Service — keeps GPT-5.5 accessible via local bridge
# Usage:
#   .\kitty-bridge-service.ps1 start
#   .\kitty-bridge-service.ps1 stop
#   .\kitty-bridge-service.ps1 status

$PID_FILE = "$env:USERPROFILE\.gemini\antigravity-cli\kitty-bridge.pid"
$LOG_FILE = "$env:USERPROFILE\Documents\KAOS\.memory\cache\kitty-bridge.log"

function Start-Service {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] Starting kitty-bridge..."

    # Check if already running
    if (Test-Path $PID_FILE) {
        $pid = Get-Content $PID_FILE
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Output "kitty-bridge already running (PID: $pid)"
            return
        }
    }

    $jobName = "KAOS-kitty-bridge"
    $existing = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($existing) { $existing | Remove-Job -Force }

    Start-Job -Name $jobName -ScriptBlock {
        param($logFile)
        $env:PYTHONUNBUFFERED = "1"
        kitty bridge --port 8080 --profile plus 2>&1 | Out-File -FilePath $logFile -Encoding utf8
    } -ArgumentList $LOG_FILE | Out-Null

    Write-Output "kitty-bridge started as background job '$jobName'"
    Write-Output "Log: $LOG_FILE"
}

function Stop-Service {
    $jobName = "KAOS-kitty-bridge"
    $job = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($job) {
        Stop-Job $job
        Remove-Job $job
        Write-Output "kitty-bridge stopped"
    } else {
        Write-Output "kitty-bridge not running"
    }
}

function Status-Service {
    $jobName = "KAOS-kitty-bridge"
    $job = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($job -and $job.State -eq 'Running') {
        Write-Output "kitty-bridge RUNNING (Job: $jobName)"
    } elseif ($job) {
        Write-Output "kitty-bridge STOPPED (state: $($job.State))"
    } else {
        Write-Output "kitty-bridge STOPPED"
    }
}

switch ($args[0]) {
    "start"  { Start-Service }
    "stop"   { Stop-Service }
    "restart" { Stop-Service; Start-Service }
    default { Status-Service }
}
