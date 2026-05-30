# Start Aether Dashboard Server
Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList ".memory\_scripts\aether_serve.py --port 9090"
Start-Sleep -Seconds 5
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:9090/" -TimeoutSec 3 -UseBasicParsing
    Write-Output "Dashboard running at http://localhost:9090 (Status: $($r.StatusCode))"
    Start-Process "http://localhost:9090"
} catch {
    Write-Output "Server may need more time. Try: http://localhost:9090"
}
