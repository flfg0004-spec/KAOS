<#
.SYNOPSIS
    Verifica que el stub de dashboard_auth esté correctamente instalado.
.DESCRIPTION
    Comprueba que los módulos dashboard_auth/__init__.py y middleware.py
    existen en el site-packages de Hermes y que importan correctamente.
.NOTES
    No requiere permisos de administrador.
#>

$ErrorActionPreference = "Stop"
$venvPython = "$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts\python.exe"

Write-Host "=== Verificación Dashboard Fix v0.15.2 ===" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Python venv
Write-Host "[1/5] Python venv..." -NoNewline
if (Test-Path $venvPython) {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " NO ENCONTRADO" -ForegroundColor Red
    Write-Host "  Buscando en PATH..." -NoNewline
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $py) { $py = (Get-Command py -ErrorAction SilentlyContinue).Source }
    if ($py) { Write-Host "$py" -ForegroundColor Yellow } else { Write-Host " NO HAY PYTHON" -ForegroundColor Red; exit 1 }
    $venvPython = $py
}

# 2. Verificar directorio dashboard_auth
Write-Host "[2/5] Directorio dashboard_auth..." -NoNewline
$sitePkg = & $venvPython -c "import site; print(site.getsitepackages()[0])" 2>$null
$dashAuthDir = Join-Path $sitePkg "hermes_cli\dashboard_auth"
if (Test-Path $dashAuthDir) {
    Write-Host " OK" -ForegroundColor Green
    Write-Host "  Ruta: $dashAuthDir"
} else {
    Write-Host " NO ENCONTRADO" -ForegroundColor Red
    Write-Host "  Buscando en ubicación alternativa..." -NoNewline
    $alt = "$env:LOCALAPPDATA\hermes\hermes-agent\venv\Lib\site-packages\hermes_cli\dashboard_auth"
    if (Test-Path $alt) { Write-Host " OK ($alt)" -ForegroundColor Green; $dashAuthDir = $alt }
    else { Write-Host " NO" -ForegroundColor Red; exit 1 }
}

# 3. Verificar archivos del stub
Write-Host "[3/5] Archivos del stub..." -NoNewline
$files = @("__init__.py", "middleware.py")
$missing = @()
foreach ($f in $files) {
    if (-not (Test-Path (Join-Path $dashAuthDir $f))) { $missing += $f }
}
if ($missing.Count -eq 0) {
    Write-Host " OK" -ForegroundColor Green
    Write-Host "  Archivos: $($files -join ', ')"
} else {
    Write-Host " FALTAN: $($missing -join ', ')" -ForegroundColor Red
    exit 1
}

# 4. Probar import
Write-Host "[4/5] Import test..." -NoNewline
try {
    $result = & $venvPython -c "
from hermes_cli.dashboard_auth import list_providers, ProviderInfo
from hermes_cli.dashboard_auth.middleware import gated_auth_middleware
print('OK')
print(f'  list_providers(): {list_providers()}')
print(f'  ProviderInfo: {ProviderInfo}')
print(f'  gated_auth_middleware: {gated_auth_middleware}')
" 2>&1
    Write-Host " OK" -ForegroundColor Green
    $result | ForEach-Object { Write-Host "  $_" }
} catch {
    Write-Host " FAIL" -ForegroundColor Red
    Write-Host "  Error: $_"
    exit 1
}

# 5. Resumen
Write-Host ""
Write-Host "[5/5] Resumen" -ForegroundColor Cyan
Write-Host "  Dashboard stub:  INSTALADO" -ForegroundColor Green
Write-Host "  Versión Hermes:  v0.15.2"
Write-Host "  Fix:             dashboard_auth module (stub local)"
Write-Host "  Próximo paso:    .\kaos hermes dashboard --port 9119"
Write-Host ""
Write-Host "=== VERIFICACIÓN COMPLETADA ===" -ForegroundColor Cyan
