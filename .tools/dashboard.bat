@echo off
title KAOS Dashboard
cd /d "%~dp0.."

echo ====================================
echo  KAOS Dashboard - Servicio Windows
echo ====================================
echo.

:LIBERAR_PUERTO
set PORT=9090
echo [1/3] Verificando puerto %PORT%...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" 2^>nul') do (
    echo  Puerta %PORT% ocupada por PID: %%a
    echo  Liberando...
    taskkill /f /pid %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)

:INICIAR
echo [2/3] Iniciando dashboard en http://127.0.0.1:%PORT%
echo [3/3] Presiona Ctrl+C para detener
echo.

:REENICIAR
python .tools\dashboard.py
echo.
echo [WARNING] Dashboard se detuvo inesperadamente.
echo [INFO] Reiniciando en 5 segundos...
timeout /t 5 /nobreak >nul
goto LIBERAR_PUERTO
