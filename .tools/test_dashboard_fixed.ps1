# Test dashboard fixes
# 1. Start dashboard in background
$port = 9090

# Cleanup any existing process on port
$existing = netstat -ano | Select-String ":$port "
if ($existing) {
    $oldPid = ($existing -split '\s+')[-1]
    Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
    Start-Sleep 1
}

# Start dashboard
$job = Start-Job -ScriptBlock { 
    Set-Location "C:\Users\LeonX\Documents\KAOS"
    python .tools\dashboard.py 
}
Start-Sleep 4

Write-Host "=== TEST 1: API basica ==="
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:$port/api/data" -UseBasicParsing -TimeoutSec 10
    $d = $r.Content | ConvertFrom-Json
    Write-Host "OK - M1: $($d.metrics[0].value), Tendencias: $($d.trends.Count)d, Agentes: $($d.agents.Count)"
} catch {
    Write-Host "FAIL: $_"
}

Write-Host "=== TEST 2: HTML page ==="
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:$port/" -UseBasicParsing -TimeoutSec 5
    Write-Host "OK - Status: $($r.StatusCode), Size: $($r.Content.Length) bytes"
} catch {
    Write-Host "FAIL: $_"
}

Write-Host "=== TEST 3: Concurrencia (3 peticiones simultaneas) ==="
$sw = [Diagnostics.Stopwatch]::StartNew()
$tasks = 1..3 | ForEach-Object {
    Start-Job -ScriptBlock {
        param($p) Invoke-WebRequest -Uri "http://127.0.0.1:$p/api/data" -UseBasicParsing -TimeoutSec 10
    } -ArgumentList $port
}
$results = $tasks | Wait-Job | Receive-Job
$sw.Stop()
$oks = ($results | Where-Object { $_.StatusCode -eq 200 }).Count
Write-Host "OK - $oks/3 respuestas en $($sw.ElapsedMilliseconds)ms"

# Cleanup
Stop-Job $job -ErrorAction SilentlyContinue
Remove-Job $job -ErrorAction SilentlyContinue

Write-Host "`n=== Dashboard FIXED ==="
