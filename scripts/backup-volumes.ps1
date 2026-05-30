# ==============================================================================
# backup-volumes.ps1 — Backup de volúmenes Docker del ecosistema KAOS
# ==============================================================================
# Crea respaldos comprimidos de los volúmenes Docker críticos.
# Los backups se guardan en .backup/docker-volumes/ con retención de 7 días.
# ==============================================================================
# USO:
#   .\scripts\backup-volumes.ps1               - Backup de todos los volúmenes
#   .\scripts\backup-volumes.ps1 -Restore       - Modo restore interactivo
# ==============================================================================

param(
    [switch]$Restore
)

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Resolve-Path (Join-Path $SCRIPT_DIR "..")
$BACKUP_DIR_WIN = Join-Path $PROJECT_ROOT ".backup/docker-volumes"
$BACKUP_DIR = "/mnt/c/Users/LeonX/Documents/KAOS/.backup/docker-volumes"
$DATE_STAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$RETENTION_DAYS = 7

$VOLUME_MAP = @(
    @{ Name = "kaos_langfuse-pg-data"; Label = "Langfuse DB" }
)

function Write-Step { Write-Host "`n>>> $args" -ForegroundColor Cyan }
function Write-Ok  { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Warn { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Err { Write-Host "[ERROR] $args" -ForegroundColor Red }

function Test-WSLDocker {
    try {
        $null = wsl.exe -d Ubuntu docker info --format '{{.Name}}' 2>&1
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

function Backup-DockerVolume {
    param([string]$VolumeName, [string]$Label)
    $backupFile = Join-Path $BACKUP_DIR_WIN "${VolumeName}-${DATE_STAMP}.tar.gz"
    Write-Step "Respaldando ${Label} (${VolumeName})"

    $volExists = wsl.exe -d Ubuntu docker volume inspect $VolumeName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Volumen '${VolumeName}' no existe, saltando..."
        return $false
    }

    $result = wsl.exe -d Ubuntu docker run --rm `
        -v "${VolumeName}:/source:ro" `
        -v "${BACKUP_DIR}:/backup" `
        alpine:latest `
        tar czf "/backup/${VolumeName}-${DATE_STAMP}.tar.gz" -C /source . 2>&1

    if ($LASTEXITCODE -eq 0 -and (Test-Path $backupFile)) {
        $size = [Math]::Round((Get-Item $backupFile).Length / 1MB, 2)
        Write-Ok "${Label} respaldado: ${backupFile} (${size} MB)"
        return $true
    } else {
        Write-Err "Fallo al respaldar ${Label}"
        return $false
    }
}

function Enforce-Retention {
    Write-Step "Aplicando retención (maximo ${RETENTION_DAYS} dias)"
    if (-not (Test-Path $BACKUP_DIR_WIN)) { Write-Ok "No hay directorio de backups"; return }
    $cutoff = (Get-Date).AddDays(-$RETENTION_DAYS)
    $oldFiles = Get-ChildItem -Path $BACKUP_DIR_WIN -Filter "*.tar.gz" | Where-Object { $_.LastWriteTime -lt $cutoff }
    if ($oldFiles.Count -eq 0) { Write-Ok "No hay backups antiguos que eliminar"; return }
    foreach ($file in $oldFiles) {
        Remove-Item -Path $file.FullName -Force
        Write-Host "  Eliminado: $($file.Name)" -ForegroundColor Gray
    }
    Write-Ok "Eliminados $($oldFiles.Count) backup(s) antiguo(s)"
}

# MAIN
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  KAOS Docker Volume Backup" -ForegroundColor Cyan
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

if (-not (Test-WSLDocker)) { exit 1 }
if (-not (Test-Path $BACKUP_DIR_WIN)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR_WIN -Force | Out-Null
    Write-Ok "Directorio de backups creado: ${BACKUP_DIR_WIN}"
}

foreach ($v in $VOLUME_MAP) {
    Backup-DockerVolume -VolumeName $v.Name -Label $v.Label
}

Enforce-Retention

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "  BACKUP COMPLETADO" -ForegroundColor Green
Write-Host "  Directorio: ${BACKUP_DIR_WIN}" -ForegroundColor Gray
Write-Host "=============================================" -ForegroundColor Cyan
