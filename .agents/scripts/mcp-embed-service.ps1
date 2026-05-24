# KAOS mcp_embed Service — keeps embedding model loaded persistently
# Run as a background job or Windows Scheduled Task
# Usage: powershell -File .agents/scripts/mcp-embed-service.ps1

$KAOS = "$env:USERPROFILE\Documents\KAOS"
$SCRIPT = "$KAOS\.memory\_scripts\mcp_embed.py"
$LOG = "$KAOS\.memory\cache\mcp-embed-service.log"
$PID_FILE = "$KAOS\.memory\cache\mcp-embed-service.pid"

function Start-Service {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] Starting mcp_embed server..."
    $proc = Start-Process -FilePath "py" -ArgumentList "-3", $SCRIPT -NoNewWindow -PassThru -RedirectStandardInput "NUL"
    $proc.Id | Out-File -FilePath $PID_FILE -Encoding ascii
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] PID: $($proc.Id)"
}

function Stop-Service {
    if (Test-Path $PID_FILE) {
        $pid = Get-Content $PID_FILE
        if ($pid -match '^\d+$') {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Output "[$(Get-Date -Format 'HH:mm:ss')] Stopped PID $pid"
        }
        Remove-Item $PID_FILE -Force -ErrorAction SilentlyContinue
    }
}

function Status-Service {
    if (Test-Path $PID_FILE) {
        $pid = Get-Content $PID_FILE
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Output "mcp_embed RUNNING (PID: $pid)"
        } else {
            Write-Output "mcp_embed STOPPED (stale PID file)"
        }
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
