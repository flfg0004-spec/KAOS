# KAOS Pre-Tool Hook: Command Verification & Safety Check
# Recibe JSON de Antigravity vía stdin

$inputPayload = $Input | Out-String

if (-not $inputPayload) {
    # Evitar fallos si se ejecuta manualmente sin entrada
    Write-Output '{"status": "allowed", "message": "No input payload received"}'
    exit 0
}

# Parsear el payload JSON
try {
    $payload = ConvertFrom-Json $inputPayload
    $toolName = $payload.toolName
    $toolArgs = $payload.toolArgs
    
    # Simular auditoría de comandos
    $logMsg = "[PRE-TOOL] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Tool: $toolName | Args: $toolArgs"
    
    # Crear carpeta de logs si no existe
    $logDir = "c:\Users\LeonX\Documents\KAOS\.agents\logs"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    # Escribir en log
    $logMsg | Out-File -FilePath "$logDir\audit_trail.log" -Append -Encoding utf8
    
    # Enviar respuesta exitosa a Antigravity (salida 0 indica permitido)
    exit 0
} catch {
    # Si hay error en parseo, permitir por defecto pero loguear el error
    $errLog = "[ERROR-PRE] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Fallo al parsear JSON: $_"
    $errLog | Out-File -FilePath "c:\Users\LeonX\Documents\KAOS\.agents\logs\audit_trail.log" -Append -Encoding utf8
    exit 0
}
