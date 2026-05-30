<#
.SYNOPSIS
    Instrucciones para instalar Hermes Gateway como servicio Windows.
.NOTES
    Ejecutar como ADMINISTRADOR: Botón derecho → "Run with PowerShell as Administrator"
#>

Write-Host "=== Instalación de Hermes Gateway como Servicio Windows ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "PASOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Abre PowerShell COMO ADMINISTRADOR:"
Write-Host "   Win + X → Windows PowerShell (Admin)"
Write-Host ""
Write-Host "2. Ejecuta:"
Write-Host "   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
Write-Host ""
Write-Host "3. Ejecuta:"
Write-Host "   $env:KAOS_ROOT\bin\windows\install-hermes-service.ps1"
Write-Host "   (reemplaza `$env:KAOS_ROOT con C:\Users\LeonX\Documents\KAOS)"
Write-Host ""
Write-Host "4. Verifica:"
Write-Host "   Get-ScheduledTask -TaskName 'KAOS Hermes Gateway' | Select-Object TaskName, State"
Write-Host ""
Write-Host "5. Para iniciar manualmente:"
Write-Host "   Start-ScheduledTask -TaskName 'KAOS Hermes Gateway'"
Write-Host ""
Write-Host "O directamente sin servicio:"
Write-Host "   .\bin\windows\start-hermes-service.ps1"
Write-Host "   .\kaos hermes gateway"
Write-Host ""

if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "⚠️  Sesión ACTUAL NO es Administrador" -ForegroundColor Red
    Write-Host "   El script no puede continuar. Sigue los pasos de arriba." -ForegroundColor Yellow
} else {
    Write-Host "✅  Sesión actual ES Administrador. Ejecutando instalación..." -ForegroundColor Green
    & "$PSScriptRoot\install-hermes-service.ps1"
}
