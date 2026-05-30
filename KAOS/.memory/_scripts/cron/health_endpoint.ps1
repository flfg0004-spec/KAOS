# ─── Health Endpoint Check — KAOS ─────────────────────────────────────
# Verifica:
#   1. Hermes gateway en :8642/health
#   2. API Server en :8642/v1
#   3. Latencia de respuesta
#   4. Estado de los 3 cron jobs
# Output: health-report.json en cache/
# ──────────────────────────────────────────────────────────────────────

param(
    [string]$HermesBaseUrl   = "http://localhost:8642",
    [string]$ReportPath      = "$PSScriptRoot\..\..\cache\health-report.json"
)

$Report = @{
    timestamp        = (Get-Date -Format "o")
    hermes_gateway   = $null
    api_server       = $null
    cron_jobs        = $null
    summary          = "unknown"
}

# ─── Helper ───────────────────────────────────────────────────────────
function Test-Endpoint {
    param([string]$Url, [string]$Label)
    $result = @{ endpoint = $Url; status = "unknown"; latency_ms = $null; error = $null }
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 10 -UseBasicParsing
        $sw.Stop()
        $result.latency_ms = [math]::Round($sw.Elapsed.TotalMilliseconds, 1)
        if ($response.StatusCode -eq 200) {
            $result.status = "ok"
        } else {
            $result.status = "degraded"
            $result.error = "HTTP $($response.StatusCode)"
        }
    } catch {
        $result.status = "down"
        $result.error   = $_.Exception.Message
    }
    return $result
}

# ─── 1. Hermes Gateway :8642/health ───────────────────────────────────
Write-Host "[health] Checking Hermes gateway..." -ForegroundColor Cyan
$Report.hermes_gateway = Test-Endpoint -Url "${HermesBaseUrl}/health" -Label "Hermes Gateway"

# ─── 2. API Server :8642/v1 ────────────────────────────────────────────
Write-Host "[health] Checking API Server..." -ForegroundColor Cyan
$Report.api_server = Test-Endpoint -Url "${HermesBaseUrl}/v1" -Label "API Server"

# ─── 3. Cron Jobs Health ──────────────────────────────────────────────
Write-Host "[health] Checking cron job status..." -ForegroundColor Cyan
$cronJobs = @(
    @{ name = "health-check";    schedule = "*/15 * * * *"; action = "health" },
    @{ name = "kanban-vacuum";   schedule = "0 3 * * *";    action = "kanban vacuum" },
    @{ name = "env-integrity";   schedule = "0 */6 * * *";  action = "run check_env" }
)

$Report.cron_jobs = $cronJobs | ForEach-Object {
    $job = $_
    $jobResult = @{
        name     = $job.name
        schedule = $job.schedule
        action   = $job.action
        # En un entorno real se consultaría el estado del scheduler.
        # Por ahora se marca como "configured".
        status   = "configured"
    }
    return $jobResult
}

# ─── 4. Summary ────────────────────────────────────────────────────────
$allOk = ($Report.hermes_gateway.status -eq "ok" -or $Report.hermes_gateway.status -eq "unknown")
$allOk = $allOk -and ($Report.api_server.status -eq "ok" -or $Report.api_server.status -eq "unknown")
if ($allOk) { $Report.summary = "healthy" } else { $Report.summary = "degraded" }

# ─── 5. Write Report ──────────────────────────────────────────────────
$json = $Report | ConvertTo-Json -Depth 5
$ReportDir = Split-Path $ReportPath -Parent
if (-not (Test-Path $ReportDir)) {
    New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
}
$json | Out-File -FilePath $ReportPath -Encoding utf8

Write-Host "[health] Report written to $ReportPath" -ForegroundColor Green
Write-Host "[health] Summary: $($Report.summary)" -ForegroundColor $(if ($Report.summary -eq "healthy") { "Green" } else { "Yellow" })
Write-Host "  Gateway : $($Report.hermes_gateway.status) ($($Report.hermes_gateway.latency_ms)ms)"
Write-Host "  API     : $($Report.api_server.status) ($($Report.api_server.latency_ms)ms)"

return $Report
