# ==============================================================================
# rotate-keys.ps1 — Rotación de API Keys expuestas en el historial git
# ==============================================================================
# EJECUTAR SOLO DESPUÉS DE REGENERAR CADA KEY EN SU SERVICIO CORRESPONDIENTE
# ==============================================================================

# Colores
$RED = "Red"; $GREEN = "Green"; $YELLOW = "Yellow"; $CYAN = "Cyan"; $GRAY = "Gray"

Write-Host "`n============================================" -ForegroundColor $CYAN
Write-Host "  ROTACIÓN DE API KEYS — KAOS ECOSYSTEM" -ForegroundColor $CYAN
Write-Host "============================================" -ForegroundColor $CYAN

Write-Host "`n⚠️  ANTES DE COMENZAR:" -ForegroundColor $YELLOW
Write-Host "  1. Regenera cada key en su servicio correspondiente"
Write-Host "  2. Copia las NUEVAS keys aquí cuando te las solicite"
Write-Host "  3. Este script actualizará .env y purgará el historial git"
Write-Host ""

$confirm = Read-Host "¿Ya tienes las nuevas keys listas? (S/N)"
if ($confirm -notmatch "^[sS]") {
    Write-Host "`n[INFO] Abortando. Revisa las instrucciones en SECURITY.md y vuelve cuando tengas las keys nuevas." -ForegroundColor $YELLOW
    exit 0
}

# ==============================================================================
# PASO 1: Recolectar nuevas keys
# ==============================================================================
Write-Host "`n=== PASO 1: Ingresar nuevas API Keys ===" -ForegroundColor $CYAN

$newKeys = @{}

Write-Host "`n1. DEEPSEEK_API_KEY — Regenerar en https://platform.deepseek.com/api_keys" -ForegroundColor $GRAY
$newKeys["DEEPSEEK_API_KEY"] = Read-Host "  Nueva clave DeepSeek"

Write-Host "`n2. OPENCODE_GO_KEY — Regenerar en https://opencode.ai/keys" -ForegroundColor $GRAY
$newKeys["OPENCODE_GO_KEY"] = Read-Host "  Nueva clave OpenCode"

Write-Host "`n3. EXA_API_KEY — Regenerar en https://dashboard.exa.ai/api-keys" -ForegroundColor $GRAY
$newKeys["EXA_API_KEY"] = Read-Host "  Nueva clave Exa"

Write-Host "`n4. OBSIDIAN_API_KEY — Regenerar en la config de Obsidian Local REST API" -ForegroundColor $GRAY
$newKeys["OBSIDIAN_API_KEY"] = Read-Host "  Nueva clave Obsidian"

Write-Host "`n5. TELEGRAM_BOT_TOKEN — Regenerar con @BotFather en Telegram" -ForegroundColor $GRAY
$newKeys["TELEGRAM_BOT_TOKEN"] = Read-Host "  Nuevo token de Telegram"

# ==============================================================================
# PASO 2: Actualizar .env con las nuevas keys
# ==============================================================================
Write-Host "`n=== PASO 2: Actualizando .env ===" -ForegroundColor $CYAN
$envPath = Join-Path $PSScriptRoot "..\.env"

if (-not (Test-Path $envPath)) {
    Write-Host "[ERROR] No se encuentra .env en $envPath" -ForegroundColor $RED
    exit 1
}

$content = Get-Content $envPath -Raw

foreach ($key in $newKeys.Keys) {
    $oldValue = [regex]::Escape($key + "=*")
    $newLine = "$key=$($newKeys[$key])"
    
    # Reemplazar marcando como [ACTIVE] (ya no TO-ROTATE)
    $pattern = "$key=.*"
    $content = $content -replace "(?m)^# \[TO-ROTATE\].*\n$pattern", "$newLine`n# [ACTIVE] Regenerada el $(Get-Date -Format 'yyyy-MM-dd')"
}

$content | Set-Content $envPath -NoNewline -Force
Write-Host "[OK] .env actualizado con las nuevas claves" -ForegroundColor $GREEN

# ==============================================================================
# PASO 3: Purgar historial git (opcional, requiere confirmación)
# ==============================================================================
Write-Host "`n=== PASO 3: Purgar historial git de las keys viejas ===" -ForegroundColor $CYAN
Write-Host "⚠️  ADVERTENCIA: Esto reescribirá el historial git." -ForegroundColor $RED
Write-Host "   - Todos los colaboradores deberán hacer 'git pull --force'"
Write-Host "   - Las PRs abiertas pueden verse afectadas"
Write-Host "   - Haz un backup del repo antes de continuar" -ForegroundColor $YELLOW

$purgeConfirm = Read-Host "`n¿Deseas purgar el historial git AHORA? (S/N)"
if ($purgeConfirm -notmatch "^[sS]") {
    Write-Host "`n[INFO] Omisión de purga. Las keys nuevas están en .env pero las viejas siguen en el historial git." -ForegroundColor $YELLOW
    Write-Host "Para purgar manualmente más tarde, ejecuta:" -ForegroundColor $GRAY
    Write-Host "  cd $(Resolve-Path (Join-Path $PSScriptRoot '..'))" -ForegroundColor $GRAY
    Write-Host "  git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch .env' --prune-empty --tag-name-filter cat -- --all" -ForegroundColor $GRAY
    Write-Host "  git reflog expire --expire=now --all && git gc --prune=now --aggressive" -ForegroundColor $GRAY
    exit 0
}

# Ejecutar purga
Write-Host "`n[INFO] Ejecutando git filter-branch para eliminar .env del historial..." -ForegroundColor $YELLOW
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot

try {
    # 1. Filter branch para eliminar .env
    git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env" --prune-empty --tag-name-filter cat -- --all
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] git filter-branch falló. Revisa el mensaje arriba." -ForegroundColor $RED
        exit 1
    }
    Write-Host "[OK] Historial limpiado" -ForegroundColor $GREEN

    # 2. Expirar reflog y hacer gc agresivo
    Write-Host "[INFO] Limpiando referencias huérfanas..." -ForegroundColor $YELLOW
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive
    Write-Host "[OK] Repositorio compactado" -ForegroundColor $GREEN

    # 3. Forzar push (requiere permiso)
    Write-Host "`n⚠️  AHORA DEBES FORZAR EL PUSH:" -ForegroundColor $YELLOW
    Write-Host "  git push origin --force --all" -ForegroundColor $GRAY
    
    $pushConfirm = Read-Host "`n¿Deseas ejecutar git push --force ahora? (S/N)"
    if ($pushConfirm -match "^[sS]") {
        git push origin --force --all
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Push forzado completado" -ForegroundColor $GREEN
        } else {
            Write-Host "[ERROR] Push falló. Verifica permisos de escritura en el repositorio remoto." -ForegroundColor $RED
        }
    }
} finally {
    Pop-Location
}

Write-Host "`n============================================" -ForegroundColor $CYAN
Write-Host "  ROTACIÓN COMPLETADA" -ForegroundColor $GREEN
Write-Host "============================================" -ForegroundColor $CYAN
Write-Host "  - .env actualizado con nuevas claves"
Write-Host "  - Historial git purgado de las claves viejas"
Write-Host "  - NO olvides reiniciar los servicios que usan estas keys"
Write-Host "`nRecuerda también actualizar .env.template con los placeholders correctos si cambió algo.`n"
