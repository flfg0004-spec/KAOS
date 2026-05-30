@echo off
REM ============================================
REM KAOS CLI — Wrapper para bin\windows\kaos.ps1
REM ============================================

powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0bin\windows\kaos.ps1" %*
