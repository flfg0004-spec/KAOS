# KAOS Post-Tool Hook: Activity Logging & Telemetry
# Recibe JSON de Antigravity vía stdin conteniendo los resultados de la ejecución del tool

$inputPayload = $Input | Out-String

if (-not $inputPayload) {
    exit 0
}

try {
    $payload = ConvertFrom-Json $inputPayload
    $toolName = $payload.toolName
    $exitCode = $payload.exitCode
    
    # Simular auditoría posterior
    $logMsg = "[POST-TOOL] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Tool: $toolName | Result: Success"
    
    $logDir = "c:\Users\LeonX\Documents\KAOS\.agents\logs"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    $logMsg | Out-File -FilePath "$logDir\audit_trail.log" -Append -Encoding utf8
    exit 0
} catch {
    $errLog = "[ERROR-POST] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Fallo al registrar post-tool: $_"
    $errLog | Out-File -FilePath "c:\Users\LeonX\Documents\KAOS\.agents\logs\audit_trail.log" -Append -Encoding utf8
    exit 0
}
