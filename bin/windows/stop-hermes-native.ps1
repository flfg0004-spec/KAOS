# ============================================
# stop-hermes-native.ps1
# Detiene Hermes Agent nativo
# ============================================

Write-Host "Deteniendo Hermes nativo..." -ForegroundColor Yellow

# Matar procesos de vite (workspace UI)
Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "vite" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Matar procesos de Hermes gateway/dashboard
Get-Process -Name "hermes" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "Hermes nativo detenido" -ForegroundColor Green
