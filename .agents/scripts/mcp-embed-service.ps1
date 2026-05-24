# KAOS mcp_embed Service — keeps embedding model loaded persistently
# Usage:
#   .\mcp-embed-service.ps1 start
#   .\mcp-embed-service.ps1 stop
#   .\mcp-embed-service.ps1 status

$KAOS = "$env:USERPROFILE\Documents\KAOS"
$SCRIPT = "$KAOS\.memory\_scripts\mcp_embed.py"
$PID_FILE = "$KAOS\.memory\cache\mcp-embed-service.pid"

function Start-Service {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] Starting mcp_embed server..."
    $kaosDir = (Get-Item $KAOS).FullName
    $jobName = "KAOS-mcp-embed"
    $existing = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($existing) { $existing | Remove-Job -Force }
    Start-Job -Name $jobName -ScriptBlock {
        param($scriptPath, $kaosDir)
        Set-Location $kaosDir
        py -3 $scriptPath
    } -ArgumentList $SCRIPT, $kaosDir | Out-Null
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] mcp_embed started as background job '$jobName'"
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] Test: echo '{""jsonrpc"":""2.0"",""id"":1,""method"":""tools/list"",""params"":{}}' | py -3 $SCRIPT"
}

function Stop-Service {
    $jobName = "KAOS-mcp-embed"
    $job = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($job) {
        Stop-Job $job
        Remove-Job $job
        Write-Output "[$(Get-Date -Format 'HH:mm:ss')] mcp_embed stopped"
    } else {
        Write-Output "mcp_embed not running"
    }
}

function Status-Service {
    $jobName = "KAOS-mcp-embed"
    $job = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($job -and $job.State -eq 'Running') {
        Write-Output "mcp_embed RUNNING (Job: $jobName)"
    } elseif ($job) {
        Write-Output "mcp_embed STOPPED (state: $($job.State))"
    } else {
        Write-Output "mcp_embed STOPPED"
    }
}

switch ($args[0]) {
    "start"  { Start-Service }
    "stop"   { Stop-Service }
    "restart" { Stop-Service; Start-Service }
    default { Status-Service }
}
