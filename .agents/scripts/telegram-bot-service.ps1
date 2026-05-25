# KAOS Telegram Bot Service — long polling ingestion
# Usage: .\telegram-bot-service.ps1 start|stop|status

$PID_FILE = "$env:USERPROFILE\.gemini\antigravity-cli\telegram-bot.pid"
$LOG_FILE = "$env:USERPROFILE\Documents\KAOS\.memory\cache\telegram-bot.log"

function Start-Service {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] Starting telegram bot..."
    $jobName = "KAOS-telegram-bot"
    $existing = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($existing) { $existing | Remove-Job -Force }
    Start-Job -Name $jobName -ScriptBlock {
        param($kaosDir)
        Set-Location $kaosDir
        py -3 -m telegram_bot.bot 2>&1 | Out-File -FilePath $args[0] -Encoding utf8
    } -ArgumentList $LOG_FILE | Out-Null
    Write-Output "telegram bot started as job '$jobName'"
}

function Stop-Service {
    $jobName = "KAOS-telegram-bot"
    $job = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($job) { Stop-Job $job; Remove-Job $job; Write-Output "stopped" }
    else { Write-Output "not running" }
}

function Status-Service {
    $job = Get-Job -Name "KAOS-telegram-bot" -ErrorAction SilentlyContinue
    if ($job -and $job.State -eq 'Running') { Write-Output "RUNNING" }
    else { Write-Output "STOPPED" }
}

switch ($args[0]) {
    "start" { Start-Service }
    "stop"  { Stop-Service }
    "restart" { Stop-Service; Start-Service }
    default { Status-Service }
}
