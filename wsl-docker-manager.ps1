# ==============================================================================
# KAOS WSL Docker Manager (wsl-docker-manager.ps1)
# Script centralizado para el control del ciclo de vida de Docker nativo en WSL2
# ==============================================================================

# Configuración de variables globales
$DISTRO_NAME = "Ubuntu"
$DOCKER_DESKTOP_DISTROS = @("docker-desktop", "docker-desktop-data")
$DOCKER_SERVICE_NAME = "com.docker.service"

# Rutas estándar de Docker Desktop en Windows
$DOCKER_DESKTOP_DIRS = @(
    "$env:APPDATA\Docker",
    "$env:LOCALAPPDATA\Docker",
    "$env:ProgramFiles\Docker"
)

# Colores para mensajes de consola
function Write-Header ($text) {
    Write-Host "`n=== $text ===" -ForegroundColor Cyan
}

function Write-Success ($text) {
    Write-Host "[OK] $text" -ForegroundColor Green
}

function Write-Info ($text) {
    Write-Host "[INFO] $text" -ForegroundColor White
}

function Write-Warning ($text) {
    Write-Host "[WARN] $text" -ForegroundColor Yellow
}

function Write-ErrorMsg ($text) {
    Write-Host "[ERROR] $text" -ForegroundColor Red
}

# Obtener distribuciones WSL de forma limpia lidiando con la codificación UTF-16 de WSL
function Get-WSLDistros {
    $raw = wsl.exe -l 2>$null
    if ($null -eq $raw) { return @() }
    
    # Unir y remover caracteres nulos u otros remanentes de UTF-16
    $cleanText = ($raw -join "`n").Replace("`0", "").Replace("`r", "")
    $lines = $cleanText -split "`n"
    
    $distros = @()
    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        # Saltar cabeceras o líneas de descripción
        if ($trimmed -ne "" -and $trimmed -notlike "*Distribuciones*" -and $trimmed -notlike "*Windows Subsystem*") {
            # Extraer solo el nombre de la distribución (antes de cualquier espacio o paréntesis)
            $name = ($trimmed -split "\s+")[0]
            # Limpiar asteriscos indicadores de distribución predeterminada
            $name = $name.Replace("*", "").Trim()
            if ($name -ne "") {
                $distros += $name
            }
        }
    }
    return $distros
}

# 1. Verificar si WSL y la distribución Ubuntu están disponibles
function Assert-WSL {
    $distros = Get-WSLDistros
    if ($distros.Count -eq 0) {
        Write-ErrorMsg "No se detectaron distribuciones de WSL2 o WSL no responde."
        exit 1
    }
    
    $found = $false
    foreach ($d in $distros) {
        if ($d -eq $DISTRO_NAME) {
            $found = $true
            break
        }
    }
    
    if (-not $found) {
        Write-ErrorMsg "La distribución '$DISTRO_NAME' no está instalada en WSL."
        Write-Info "Distribuciones encontradas: $($distros -join ', ')"
        exit 1
    }
}

# 2. Comando: start (Iniciar Docker de forma integrada)
function Start-Docker {
    Write-Header "Iniciando Docker Nativo en WSL2 ($DISTRO_NAME)"
    Assert-WSL

    # Asegurar que la distribución esté levantada
    Write-Info "Arrancando la distribución '$DISTRO_NAME'..."
    wsl.exe -d $DISTRO_NAME -u root true
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "No se pudo iniciar la distribución WSL $DISTRO_NAME."
        return
    }

    # Verificar e iniciar el daemon de Docker por medio de systemd
    Write-Info "Verificando el estado del servicio Docker (systemd)..."
    $status = (wsl.exe -d $DISTRO_NAME -u root systemctl is-active docker 2>&1).ToString().Trim()
    if ($status -ne "active") {
        Write-Warning "El servicio Docker está inactivo. Iniciando..."
        wsl.exe -d $DISTRO_NAME -u root systemctl start docker
        Start-Sleep -Seconds 2
    }

    # Comprobación de conectividad final
    $dockerCheck = wsl.exe -d $DISTRO_NAME docker info --format '{{.Name}}' 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "¡Docker Engine nativo está activo y respondiendo correctamente!"
        Write-Info "Cliente Docker conectado a /var/run/docker.sock sin privilegios root."
    } else {
        Write-ErrorMsg "Docker no responde. Error: $dockerCheck"
    }
}

# 3. Comando: stop (Apagar Docker y liberar memoria)
function Stop-Docker {
    Write-Header "Deteniendo Infraestructura Docker en WSL2"
    Assert-WSL

    # Detener contenedores de forma ordenada
    Write-Info "Deteniendo todos los contenedores activos de forma limpia..."
    $runningContainers = wsl.exe -d $DISTRO_NAME docker ps -q 2>$null
    if ($runningContainers) {
        wsl.exe -d $DISTRO_NAME docker stop $runningContainers 2>$null
    }

    # Detener el servicio docker nativo
    Write-Info "Deteniendo servicio de Docker en WSL..."
    wsl.exe -d $DISTRO_NAME -u root systemctl stop docker 2>$null

    # Apagar la máquina virtual WSL
    Write-Info "Terminando la distribución $DISTRO_NAME..."
    wsl.exe --terminate $DISTRO_NAME
    
    # Liberar memoria física de WSL2 en el host de Windows
    Write-Info "Apagando WSL globalmente para recuperar RAM en Windows..."
    wsl.exe --shutdown

    Write-Success "Infraestructura Docker detenida con éxito. RAM liberada."
}

# 4. Comando: status (Ver estado de salud y recursos)
function Show-Status {
    Write-Header "Estado de la Infraestructura de Docker en WSL2"
    Assert-WSL

    # Estado de la distribución WSL
    $distros = Get-WSLDistros
    Write-Info "Distribuciones WSL registradas: $($distros -join ', ')"

    # Estado del Daemon de Docker
    $dockerActive = "inactive"
    try {
        $dockerActive = (wsl.exe -d $DISTRO_NAME -u root systemctl is-active docker 2>&1).ToString().Trim()
    } catch {}

    if ($dockerActive -eq "active") {
        Write-Success "Docker Daemon: ACTIVO (Running nativamente en systemd)"
        
        # Versión de Docker
        $ver = (wsl.exe -d $DISTRO_NAME docker --version).ToString().Trim()
        Write-Info "Versión: $ver"
        
        # Contenedores en ejecución
        Write-Info "Contenedores Activos:"
        wsl.exe -d $DISTRO_NAME docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    } else {
        Write-Warning "Docker Daemon: INACTIVO"
    }

    # 4a. Consumo de recursos de la máquina virtual (RAM / CPU / Discos)
    Write-Header "Métricas de Consumo de Recursos"

    # Consumo de memoria RAM dentro de WSL
    if ($dockerActive -eq "active") {
        $ramInfo = wsl.exe -d $DISTRO_NAME free -h | Select-String -Pattern "Mem:"
        if ($ramInfo) {
            $parts = -split $ramInfo
            Write-Info "RAM en WSL: Total: $($parts[1]) | Usada: $($parts[2]) | Libre: $($parts[3]) | Caché/Buff: $($parts[5])"
        }

        # Carga de CPU
        $loadInfo = wsl.exe -d $DISTRO_NAME cat /proc/loadavg
        if ($loadInfo) {
            $loads = -split $loadInfo
            Write-Info "Carga de CPU (WSL): 1 min: $($loads[0]) | 5 min: $($loads[1]) | 15 min: $($loads[2])"
        }
    }

    # Procesos wslhost en Windows
    $wslProcess = Get-Process -Name wslhost -ErrorAction SilentlyContinue
    if ($wslProcess) {
        $wslRam = [Math]::Round(($wslProcess | Measure-Object -Property WorkingSet64 -Sum).Sum / 1MB, 2)
        Write-Info "Memoria RAM física consumida por wslhost.exe en Windows: $wslRam MB"
    } else {
        Write-Info "Proceso wslhost.exe inactivo en Windows."
    }

    # Ruta y Tamaño del VHDX
    $vhdFolder = "$env:LOCALAPPDATA\WSL"
    if (Test-Path $vhdFolder) {
        $vhdxFiles = Get-ChildItem -Path $vhdFolder -Filter "*.vhdx" -Recurse -ErrorAction SilentlyContinue
        foreach ($file in $vhdxFiles) {
            $sizeGb = [Math]::Round($file.Length / 1GB, 2)
            $sizeMb = [Math]::Round($file.Length / 1MB, 2)
            $displaySize = if ($sizeGb -ge 1) { "$sizeGb GB" } else { "$sizeMb MB" }
            Write-Info "Disco Virtual (VHDX): $($file.Name) | Tamaño físico: $displaySize"
            Write-Info "Ruta del VHDX: $($file.FullName)"
        }
    }
}

# 5. Comando: clean (Optimización, Purga de Docker y Encogimiento del VHDX)
function Clean-Environment {
    Write-Header "Optimizando y Compactando el Almacenamiento Docker/WSL"
    Assert-WSL

    $dockerActive = (wsl.exe -d $DISTRO_NAME -u root systemctl is-active docker 2>&1).ToString().Trim()
    if ($dockerActive -ne "active") {
        Write-Warning "Se requiere que Docker esté activo para proceder con la limpieza de contenedores."
        Write-Info "Iniciando temporalmente..."
        wsl.exe -d $DISTRO_NAME -u root systemctl start docker
        Start-Sleep -Seconds 2
    }

    # Purga de Docker
    Write-Info "Ejecutando Docker System Prune (reclamando espacio de contenedores, volúmenes huérfanos e imágenes sin usar)..."
    wsl.exe -d $DISTRO_NAME docker system prune -af --volumes

    # fstrim (Súper importante para discos Sparse VHD en WSL2)
    Write-Info "Ejecutando fstrim en los puntos de montaje de WSL2 para devolver bloques vacíos a Windows..."
    wsl.exe -d $DISTRO_NAME -u root fstrim -av
    if ($LASTEXITCODE -eq 0) {
        Write-Success "¡fstrim completado! Windows ha recuperado el espacio de forma dinámica."
    } else {
        Write-Warning "Hubo un problema al ejecutar fstrim."
    }

    # Mostrar nuevo tamaño del disco
    $vhdFolder = "$env:LOCALAPPDATA\WSL"
    if (Test-Path $vhdFolder) {
        $vhdxFiles = Get-ChildItem -Path $vhdFolder -Filter "*.vhdx" -Recurse -ErrorAction SilentlyContinue
        foreach ($file in $vhdxFiles) {
            $sizeMb = [Math]::Round($file.Length / 1MB, 2)
            Write-Success "Nuevo tamaño de VHDX ($($file.Name)) en disco: $sizeMb MB"
        }
    }
}

# 6. Comando: decommission (Desmantelamiento y Decomisión Limpia de Docker Desktop)
function Decommission-DockerDesktop {
    Write-Header "Decomisión y Desmantelamiento Completo de Docker Desktop"
    
    # Confirmación de seguridad
    Write-Warning "Esta acción desactivará e inhabilitará completamente Docker Desktop en Windows."
    Write-Warning "Se eliminarán las carpetas de configuración de Docker Desktop en tu perfil de usuario."
    $confirm = Read-Host "¿Estás seguro de que deseas continuar? (S/N)"
    if ($confirm -notmatch "^[sSyY]") {
        Write-Info "Decomisión cancelada por el usuario."
        return
    }

    # Detener el servicio de Windows
    Write-Info "Deteniendo y eliminando el servicio de Windows '$DOCKER_SERVICE_NAME'..."
    $service = Get-Service -Name $DOCKER_SERVICE_NAME -ErrorAction SilentlyContinue
    if ($service) {
        if ($service.Status -eq "Running") {
            Stop-Service -Name $DOCKER_SERVICE_NAME -Force
        }
        # Eliminar el servicio del registro de Windows usando sc.exe
        & sc.exe delete $DOCKER_SERVICE_NAME | Out-Null
        Write-Success "Servicio '$DOCKER_SERVICE_NAME' detenido y eliminado con éxito."
    } else {
        Write-Info "El servicio '$DOCKER_SERVICE_NAME' no existe o ya fue removido."
    }

    # Desregistrar las distribuciones muertas de WSL
    $distros = Get-WSLDistros
    foreach ($distro in $DOCKER_DESKTOP_DISTROS) {
        $found = $false
        foreach ($d in $distros) {
            if ($d -eq $distro) { $found = $true; break }
        }
        if ($found) {
            Write-Info "Desregistrando y liberando espacio físico de la distro WSL '$distro'..."
            wsl.exe --unregister $distro
            Write-Success "Distro '$distro' desregistrada e hilos de disco liberados."
        } else {
            Write-Info "La distro WSL '$distro' no existe o ya fue desregistrada."
        }
    }

    # Eliminar directorios de datos de Docker Desktop
    foreach ($dir in $DOCKER_DESKTOP_DIRS) {
        if (Test-Path -LiteralPath $dir) {
            Write-Info "Eliminando remanente de archivos en: $dir"
            try {
                Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction Stop
                Write-Success "Directorio eliminado: $dir"
            } catch {
                Write-Warning "No se pudo eliminar de forma automática: $dir. Es posible que algún proceso lo esté bloqueando."
            }
        }
    }

    # Limpiar variables de entorno que apunten a Docker Desktop
    Write-Info "Limpiando variables de entorno obsoletas..."
    $envVars = @("DOCKER_HOST", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH")
    foreach ($var in $envVars) {
        if ([System.Environment]::GetEnvironmentVariable($var, "User")) {
            [System.Environment]::SetEnvironmentVariable($var, $null, "User")
            Write-Success "Variable de entorno de Usuario '$var' removida."
        }
        if ([System.Environment]::GetEnvironmentVariable($var, "Machine")) {
            [System.Environment]::SetEnvironmentVariable($var, $null, "Machine")
            Write-Success "Variable de entorno del Sistema '$var' removida."
        }
    }

    Write-Success "¡Desmantelamiento de Docker Desktop ejecutado con éxito!"
    Write-Info "La transición a Docker Engine Nativo sobre WSL2 está limpia de interferencias en el host Windows."
}

# Enrutamiento de argumentos
if ($args.Count -eq 0) {
    Write-Header "Uso de KAOS WSL Docker Manager"
    Write-Host "Ejecuta el script pasando una de las siguientes opciones:" -ForegroundColor Gray
    Write-Host "  .\wsl-docker-manager.ps1 start        - Inicia Docker Nativo en WSL2 de forma integrada"
    Write-Host "  .\wsl-docker-manager.ps1 stop         - Detiene de manera ordenada Docker y apaga WSL2"
    Write-Host "  .\wsl-docker-manager.ps1 status       - Muestra el estado del servicio Docker y métricas de RAM/CPU/VHDX"
    Write-Host "  .\wsl-docker-manager.ps1 clean        - Ejecuta prune y compacta espacio de almacenamiento (VHDX Sparse)"
    Write-Host "  .\wsl-docker-manager.ps1 decommission - Elimina residuos físicos y de sistema de Docker Desktop" -ForegroundColor Yellow
    Write-Host "`nEjemplo: .\wsl-docker-manager.ps1 status`n" -ForegroundColor DarkGray
    exit 0
}

switch ($args[0]) {
    "start"        { Start-Docker }
    "stop"         { Stop-Docker }
    "status"       { Show-Status }
    "clean"        { Clean-Environment }
    "decommission" { Decommission-DockerDesktop }
    default {
        Write-ErrorMsg "Comando no reconocido: '$($args[0])'."
        Write-Host "Opciones válidas: start, stop, status, clean, decommission" -ForegroundColor Gray
    }
}
