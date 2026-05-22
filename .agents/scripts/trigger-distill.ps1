# KAOS Post-Write Hook: Trigger distill on raw/ writes
param([string]$toolName, [string]$toolArgs)
if (-not $toolName) { exit 0 }
try {
    $writeTools = @("write", "edit", "write_file", "edit_file", "append_file")
    $matched = $false
    foreach ($t in $writeTools) {
        if ($toolName -match $t) { $matched = $true; break }
    }
    if ($matched -and $toolArgs -match "\.memory\\raw") {
        $distillCmd = "py -3 $env:USERPROFILE\Documents\KAOS\.tools\distill.py all --new-only"
        Invoke-Expression $distillCmd
    }
} catch { exit 0 }
