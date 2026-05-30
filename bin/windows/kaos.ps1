# ============================================
# KAOS CLI - Unified Control Center
# ============================================
param([string]$Command, [Parameter(ValueFromRemainingArguments)]$Args)

$KAOS_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

$SERVICES = @(
    @{ Name = "Hermes Gateway";  Key = "hermes";  Url = "http://127.0.0.1:8642/health" }
    @{ Name = "Hermes Dashboard"; Key = "hermesdash"; Url = "http://127.0.0.1:9119/api/status" }
    @{ Name = "Hermes Workspace"; Key = "hermesws"; Url = "http://127.0.0.1:3002/api/healthcheck" }
)

$OPEN_TARGETS = @(
    @{ Name = "Hermes Gateway";  Key = "hermes";  Url = "http://localhost:8642" }
    @{ Name = "Hermes Dashboard"; Key = "hermesdash"; Url = "http://localhost:9119" }
    @{ Name = "Hermes Workspace"; Key = "hermesws"; Url = "http://localhost:3002" }
    @{ Name = "Langfuse Cloud";  Key = "langfuse";  Url = "https://cloud.langfuse.com" }
    @{ Name = "OpenCode";  Key = "opencode";  Url = "https://opencode.ai" }
)

$DOC_TARGETS = @(
    @{ Name = "Entity Hermes Agent";  Key = "hermes-entity";  Path = ".memory\wiki\entities\hermes-agent.md" }
    @{ Name = "Hermes Config";  Key = "hermes-config";  Path = "$env:USERPROFILE\.hermes\config.yaml" }
    @{ Name = "KAOS .env";  Key = "env";  Path = ".env" }
    @{ Name = "MnemoBEAM";  Key = "mnemobeam";  Path = ".memory\_scripts\lib\mnemobeam.py" }
    @{ Name = "KAOS CLI";  Key = "kaos-cli";  Path = "bin\windows\kaos.ps1" }
)

$AGENTS = @(
    @{ Name = "aletheia"; Color = "Cyan"; Description = "Research agent" }
    @{ Name = "mnemosyne"; Color = "Gray"; Description = "Memory curator" }
    @{ Name = "kosmos"; Color = "Magenta"; Description = "Architecture agent" }
    @{ Name = "metis"; Color = "Yellow"; Description = "Strategy agent" }
    @{ Name = "kronos"; Color = "DarkYellow"; Description = "Pipeline orchestrator" }
    @{ Name = "kratos"; Color = "Red"; Description = "Code agent" }
)

function Write-OK    { Write-Host "  OK "  -ForegroundColor Green  -NoNewline; Write-Host $args }
function Write-Warn  { Write-Host "  WARN " -ForegroundColor Yellow -NoNewline; Write-Host $args }
function Write-Err   { Write-Host "  ERR "  -ForegroundColor Red   -NoNewline; Write-Host $args }
function Write-Info  { Write-Host "    "    -ForegroundColor Gray  -NoNewline; Write-Host $args }
function Write-Step  { Write-Host "  -> "   -ForegroundColor Cyan  -NoNewline; Write-Host $args }
function Write-Head  { Write-Host "`n$args" -ForegroundColor White }
function Test-Endpoint($url, $timeout = 3) {
    try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec $timeout -ErrorAction Stop; return $r.StatusCode -eq 200 }
    catch { return $false }
}

function Show-Help {
    Write-Host @"

KAOS CLI - Native Control Center
==================================

Uso: .\kaos <comando> [argumentos]

COMANDOS:
  status                            Estado del ecosistema nativo
  hermes [start|stop|status|...]   Gestion de Hermes nativo
  open <target>                    Abrir web UI en navegador
  agent [list|<name>]              Gestion de agentes
  quality [smoke|audit|trend]      Metricas de calidad
  vault <cmd>                      Operaciones del vault
  doctor                           Diagnostico del sistema
  env                              Variables de entorno
  help [cmd]                       Ayuda detallada

TARGETS:  hermes, hermesws, hermesdash, langfuse, opencode
AGENTES:  aletheia, mnemosyne, kosmos, metis, kronos, kratos

WSL/Docker ELIMINADOS. Todo corre nativo en Windows.
  - Crawl4AI: pip install crawl4ai (nativo)
  - busqueda: pip install duckduckgo-search (nativo)
  - Langfuse: cloud.langfuse.com (SaaS)
  - Hermes: hermes gateway run (nativo)

"@ -ForegroundColor Cyan
}

function Show-HelpCmd($cmd) {
    switch ($cmd) {
        "status" { Write-Host "status`n  Muestra el estado de servicios nativos (Hermes, agents, vault)." -ForegroundColor Gray }
        "hermes" { Write-Host "hermes [start|stop|status|gateway|dashboard|workspace|model]`n  Gestion de Hermes nativo." -ForegroundColor Gray }
        "open" { Write-Host "open <target>`n  Abre URL en navegador: $($OPEN_TARGETS.Key -join ', ')" -ForegroundColor Gray }
        default { Show-Help }
    }
}

function Cmd-Status {
    Write-Head "-- Servicios Nativos --"
    Write-Step "Hermes Gateway (:8642)..."
    if (Test-Endpoint "http://127.0.0.1:8642/health" 3) { Write-OK "Hermes Gateway" } else { Write-Err "Hermes Gateway (detenido)" }
    Write-Step "Hermes Dashboard (:9119)..."
    if (Test-Endpoint "http://127.0.0.1:9119/api/status" 3) { Write-OK "Hermes Dashboard" } else { Write-Warn "Hermes Dashboard (bug upstream v0.15.2 - gateway funciona)" }
    Write-Step "Hermes Workspace (:3002)..."
    if (Test-Endpoint "http://127.0.0.1:3002/api/healthcheck" 3) { Write-OK "Hermes Workspace" } else { Write-Err "Hermes Workspace (detenido)" }

    Write-Head "-- Agentes --"
    foreach ($a in $AGENTS) { Write-Host "  $($a.Name)" -NoNewline -ForegroundColor $a.Color; Write-Host " - $($a.Description)" -ForegroundColor Gray }

    Write-Head "-- Vault --"
    $vaultPy = Join-Path $KAOS_ROOT ".memory\_scripts\lib\mnemobeam.py"
    if (Test-Path $vaultPy) {
        $result = & py -3 $vaultPy score 2>&1
        $result | ForEach-Object { Write-Info $_ }
    }

    Write-Head "-- Recursos --"
    $scriptsDir = Join-Path $KAOS_ROOT ".memory\_scripts"
    $scriptsCount = (Get-ChildItem -Path $scriptsDir -Recurse -Filter "*.py" -ErrorAction SilentlyContinue).Count
    Write-Info "Scripts Python: $scriptsCount"
    $wikiDir = Join-Path $KAOS_ROOT ".memory\wiki"
    if (Test-Path $wikiDir) { $wikiCount = (Get-ChildItem -Path $wikiDir -Recurse -Filter "*.md" -ErrorAction SilentlyContinue).Count; Write-Info "Documentos vault: $wikiCount" }
}

function Cmd-Hermes {
    $sub = if ($Args.Count -gt 0) { $Args[0].ToLower() } else { "status" }
    switch ($sub) {
        "start" { & "$PSScriptRoot\start-hermes-native.ps1" }
        "stop" { & "$PSScriptRoot\stop-hermes-native.ps1" }
        "status" {
            Write-Head "-- Hermes Nativo --"
            if (Test-Endpoint "http://127.0.0.1:8642/health" 3) { Write-OK "Gateway (:8642)" } else { Write-Err "Gateway (:8642)" }
            if (Test-Endpoint "http://127.0.0.1:9119/api/status" 3) { Write-OK "Dashboard (:9119)" } else { Write-Err "Dashboard (:9119)" }
            if (Test-Endpoint "http://127.0.0.1:3002/api/healthcheck" 3) { Write-OK "Workspace UI (:3002)" } else { Write-Err "Workspace UI (:3002)" }
        }
        "gateway" {
            Write-Step "Iniciando Hermes Gateway..."
            $envFile = "$env:USERPROFILE\.hermes\.env"
            $envPrefix = ""
            if (Test-Path $envFile) {
                $matches = Select-String -Path $envFile -Pattern "^(OPENCODE_GO_KEY|XIAOMI_API_KEY|API_SERVER_KEY)="
                foreach ($m in $matches) { $envPrefix += "set $($m.Line) && " }
            }
            $wsh = New-Object -ComObject WScript.Shell
            $wsh.Run("cmd.exe /c $envPrefix hermes gateway run > $env:TEMP\hermes-gateway.log 2>&1", 0, $false)
            Start-Sleep 8
            if (Test-Endpoint "http://127.0.0.1:8642/health" 5) { Write-OK "Gateway en :8642" } else { Write-Err "Gateway no responde" }
        }
        "dashboard" {
            Write-Step "Iniciando Hermes Dashboard..."
            $envFile = "$env:USERPROFILE\.hermes\.env"
            $envPrefix = ""
            if (Test-Path $envFile) {
                $matches = Select-String -Path $envFile -Pattern "^(OPENCODE_GO_KEY|XIAOMI_API_KEY|API_SERVER_KEY)="
                foreach ($m in $matches) { $envPrefix += "set $($m.Line) && " }
            }
            $wsh = New-Object -ComObject WScript.Shell
            $wsh.Run("cmd.exe /c $envPrefix hermes dashboard --port 9119 --no-open --skip-build > $env:TEMP\hermes-dashboard.log 2>&1", 0, $false)
            Start-Sleep 8
            if (Test-Endpoint "http://127.0.0.1:9119/api/status" 5) { Write-OK "Dashboard en :9119" } else { Write-Err "Dashboard no responde" }
        }
        "workspace" {
            Write-Step "Iniciando Workspace UI..."
            $wsh = New-Object -ComObject WScript.Shell
            $wsh.Run("cmd.exe /c cd /d $KAOS_ROOT\.workspace && set NODE_OPTIONS=--max-old-space-size=2048 && npx vite dev --port 3002 > $env:TEMP\hermes-workspace.log 2>&1", 0, $false)
            Start-Sleep 8
            if (Test-Endpoint "http://127.0.0.1:3002/api/healthcheck" 5) { Write-OK "Workspace UI en :3002" } else { Write-Err "Workspace UI no responde" }
        }
        "model" {
            $model = if ($Args.Count -gt 1) { $Args[1] } else { "" }
            if (-not $model) {
                Write-Host "Modelos disponibles:" -ForegroundColor Yellow
                Write-Host "  MiMo:    mimo-v2-omni, mimo-v2-pro, mimo-v2.5, mimo-v2.5-pro"
                Write-Host "Uso: .\kaos hermes model <nombre>" -ForegroundColor Gray
                return
            }
            Write-Step "Configurando modelo: $model..."
            hermes model --provider mimo --model $model 2>&1 | Out-Null
            Write-OK "Modelo cambiado a $model"
        }
        default { Write-Host "Subcomandos: start, stop, status, gateway, dashboard, workspace, model" -ForegroundColor Yellow }
    }
}

function Cmd-Open {
    if ($Args.Count -eq 0) { Write-Host "Targets: $($OPEN_TARGETS.Key -join ', ')" -ForegroundColor Yellow; return }
    $key = $Args[0].ToLower()
    $target = $OPEN_TARGETS | Where-Object { $_.Key -eq $key }
    if (-not $target) { Write-Err "Target desconocido: $key"; return }
    Write-Step "Abriendo $($target.Name)..."
    Start-Process $target.Url
    Write-OK "$($target.Url)"
}

function Cmd-Doc {
    $sub = ""
    if ($Args -and $Args.Count -gt 0) { $sub = $Args[0].ToLower() }
    if (-not $sub) {
        Write-Host "Documentos disponibles:" -ForegroundColor Yellow
        foreach ($d in $DOC_TARGETS) { Write-Info "$($d.Key) -> $($d.Name)" }
        return
    }
    $target = $DOC_TARGETS | Where-Object { $_.Key -eq $sub }
    if (-not $target) { Write-Err "Documento desconocido: $sub"; return }
    $fullPath = if ($target.Path.StartsWith("$env:USERPROFILE")) { $target.Path } else { Join-Path $KAOS_ROOT $target.Path }
    if (-not (Test-Path $fullPath)) { Write-Err "Archivo no encontrado: $fullPath"; return }
    Start-Process $fullPath
    Write-OK "Abriendo $($target.Name)"
}

function Cmd-Agent {
    if ($Args.Count -eq 0 -or $Args[0] -eq "list") {
        Write-Head "Agentes disponibles"
        foreach ($a in $AGENTS) { Write-Host "  $($a.Name)" -NoNewline -ForegroundColor $a.Color; Write-Host " - $($a.Description)" -ForegroundColor Gray }
        return
    }
    $agentName = $Args[0].ToLower()
    $agent = $AGENTS | Where-Object { $_.Name -eq $agentName }
    if (-not $agent) { Write-Err "Agente desconocido: $agentName"; return }
    Write-Step "Invocando @$agentName..."
    Write-Info "Usa @$agentName en una conversacion de OpenCode"
    Start-Process "https://opencode.ai"
}

function Cmd-Quality {
    $vaultPy = Join-Path $KAOS_ROOT ".memory\_scripts\vault.py"
    if (-not (Test-Path $vaultPy)) { Write-Err "vault.py no encontrado"; return }
    $sub = if ($Args.Count -gt 0) { $Args[0] } else { "smoke" }
    switch ($sub) {
        "smoke" { & py -3 $vaultPy health --auto 2>&1; & py -3 $vaultPy lint run 2>&1 }
        "audit" { & py -3 $vaultPy curation report 2>&1 }
        "trend" { & py -3 $vaultPy quality trend 2>&1 }
        default { Write-Warn "Subcomando: smoke, audit, trend" }
    }
}

function Cmd-Vault { & py -3 (Join-Path $KAOS_ROOT ".memory\_scripts\vault.py") @Args 2>&1 }

function Cmd-Doctor {
    Write-Head "KAOS System Doctor"
    Write-Host "------------------------" -ForegroundColor DarkGray
    Write-Step "Python..."
    $pyVersion = & py --version 2>&1
    Write-OK $pyVersion
    Write-Step "Hermes Agent..."
    try { $v = & hermes --version 2>&1 | Select-Object -First 1; Write-OK $v } catch { Write-Err "hermes no instalado" }
    Write-Step "Servicios Hermes..."
    if (Test-Endpoint "http://127.0.0.1:8642/health" 3) { Write-OK "Gateway (:8642)" } else { Write-Err "Gateway (:8642) detenido" }
    if (Test-Endpoint "http://127.0.0.1:9119/api/status" 3) { Write-OK "Dashboard (:9119)" } else { Write-Warn "Dashboard (:9119) detenido" }
    if (Test-Endpoint "http://127.0.0.1:3002/api/healthcheck" 3) { Write-OK "Workspace (:3002)" } else { Write-Warn "Workspace (:3002) detenido" }
    Write-Step "Librerias Python..."
    $libs = @("crawl4ai", "duckduckgo-search", "blockdiag", "httpx")
    foreach ($lib in $libs) { $r = & pip show $lib 2>&1 | Select-String "Version"; if ($r) { Write-OK "$lib $($r -replace 'Version: ','')" } else { Write-Err "$lib no instalado" } }
    Write-Step "Agentes OpenCode..."
    if (Test-Path (Join-Path $KAOS_ROOT ".opencode")) { Write-OK "$($AGENTS.Count) agentes configurados"; foreach ($a in $AGENTS) { Write-Info "$($a.Name) - $($a.Description)" } }
    Write-Step "Scripts Python..."
    $scriptsDir = Join-Path $KAOS_ROOT ".memory\_scripts"
    if (Test-Path $scriptsDir) { Write-OK "$((Get-ChildItem -Path $scriptsDir -Recurse -Filter '*.py').Count) scripts disponibles" }
    Write-Host "------------------------" -ForegroundColor DarkGray
}

function Cmd-Env {
    $envFile = Join-Path $KAOS_ROOT ".env"
    if (-not (Test-Path $envFile)) { Write-Err ".env no encontrado"; return }
    Write-Head "Variables de entorno"
    foreach ($line in (Get-Content $envFile)) {
        if ($line -match "^\s*#") { Write-Host "  $line" -ForegroundColor DarkGray; continue }
        if ($line -match "^\s*$") { continue }
        if ($line -match "^(.*?)=(.*)") {
            $val = $matches[2]
            if ($val -and $val.Length -gt 20) { $val = $val.Substring(0, 20) + "..." }
            Write-Host "  $($matches[1]) = $val" -ForegroundColor Gray
        }
    }
}

if (-not $Command) { Show-Help; exit 0 }
$cmd = $Command.ToLower()
$cmdMap = @{ "status" = "Cmd-Status"; "hermes" = "Cmd-Hermes"; "open" = "Cmd-Open"; "doc" = "Cmd-Doc"; "agent" = "Cmd-Agent"; "quality" = "Cmd-Quality"; "vault" = "Cmd-Vault"; "doctor" = "Cmd-Doctor"; "env" = "Cmd-Env"; "help" = "Show-HelpCmd" }
if ($cmdMap.ContainsKey($cmd)) { & $cmdMap[$cmd] @Args }
else { Write-Err "Comando desconocido: $cmd"; Show-Help }
