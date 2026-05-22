# KAOS Vault Maintenance — lint + index + health
try {
    Write-Output "[MAINT] Running vault lint..."
    $r1 = py -3 "$env:USERPROFILE\Documents\KAOS\.memory\_scripts\vault.py" lint
    if ($LASTEXITCODE -eq 0) { Write-Output "[MAINT] Lint OK" } else { Write-Output "[MAINT] Lint WARNING" }

    Write-Output "[MAINT] Regenerating index..."
    $r2 = py -3 "$env:USERPROFILE\Documents\KAOS\.memory\_scripts\vault.py" index
    if ($LASTEXITCODE -eq 0) { Write-Output "[MAINT] Index OK" } else { Write-Output "[MAINT] Index WARNING" }

    Write-Output "[MAINT] Running health check..."
    $r3 = py -3 "$env:USERPROFILE\Documents\KAOS\.memory\_scripts\vault.py" health --auto
    if ($LASTEXITCODE -eq 0) { Write-Output "[MAINT] Health OK" } else { Write-Output "[MAINT] Health WARNING" }

    Write-Output "[MAINT] Maintenance complete"
    exit 0
} catch {
    Write-Output "[MAINT] ERROR: $_"
    exit 1
}
