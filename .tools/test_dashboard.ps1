# Start KAOS Dashboard in background, test API, then stop
$dashboard = Start-Process -NoNewWindow -PassThru python ".tools/dashboard.py"
Start-Sleep 3

try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:9090/api/data" -UseBasicParsing -TimeoutSec 5
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "=== KAOS Dashboard Test ==="
    Write-Host "M1 Score Compuesto: $($data.metrics[0].value)"
    Write-Host "M2 Cache Hit Rate: $($data.metrics[1].value)"
    Write-Host "M3 Pipeline: $($data.metrics[2].value)"
    Write-Host "M4 Broken Wikilinks: $($data.metrics[3].value)"
    Write-Host "M5 Costo: $($data.metrics[4].value)"
    Write-Host "M6 Throughput: $($data.metrics[5].value)"
    Write-Host "M7 Fragmentacion: $($data.metrics[6].value)"
    Write-Host "Alertas: $($data.alerts.Count)"
    Write-Host "Tendencias: $($data.trends.Count) dias"
    Write-Host "Agentes: $($data.agents.Count)"
    Write-Host "Dashboard OK"
}
catch {
    Write-Host "ERROR: $_"
    Write-Host "Dashboard FAIL"
}
finally {
    Stop-Process -Id $dashboard.Id -Force -ErrorAction SilentlyContinue
}
