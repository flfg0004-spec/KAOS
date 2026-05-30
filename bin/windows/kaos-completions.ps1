# KAOS CLI - PowerShell Tab Completions
# Install: Add to $PROFILE: . "$env:KAOS_ROOT\bin\windows\kaos-completions.ps1"

$kaosCommands = @("status", "open", "agent", "quality", "vault", "hermes", "doctor", "env", "help")
$kaosTargets  = @("hermes", "hermesws", "hermesdash", "langfuse", "opencode")
$kaosAgents   = @("aletheia", "mnemosyne", "kosmos", "metis", "kronos", "kratos")
$kaosQuality  = @("smoke", "audit", "trend")
$kaosHermes   = @("start", "stop", "status", "gateway", "dashboard", "workspace", "model")

$kaosCompletion = {
    param($wordToComplete, $commandAst, $cursorPosition)
    $tokens = $commandAst.CommandElements | ForEach-Object { $_.Value }
    $cmdIndex = $tokens.IndexOf("kaos")
    if ($cmdIndex -lt 0) { $cmdIndex = $tokens.IndexOf(".\kaos") }
    if ($cmdIndex -lt 0) { return }
    $subCmdIndex = $cmdIndex + 1
    if ($tokens.Count -le $subCmdIndex) { return $kaosCommands | Where-Object { $_ -like "$wordToComplete*" } }
    $subCmd = $tokens[$subCmdIndex]
    $argIndex = $subCmdIndex + 1
    if ($tokens.Count -le $argIndex) {
        switch ($subCmd) {
            "open"    { return $kaosTargets  | Where-Object { $_ -like "$wordToComplete*" } }
            "agent"   { return $kaosAgents  | Where-Object { $_ -like "$wordToComplete*" } }
            "quality" { return $kaosQuality  | Where-Object { $_ -like "$wordToComplete*" } }
            "hermes"  { return $kaosHermes  | Where-Object { $_ -like "$wordToComplete*" } }
        }
    }
    if ($tokens.Count -le ($argIndex + 1)) { return }
    switch ($subCmd) {
        "model" { return @("mimo-v2-omni","mimo-v2-pro","mimo-v2.5","mimo-v2.5-pro") | Where-Object { $_ -like "$wordToComplete*" } }
    }
}
Register-ArgumentCompleter -Native -CommandName kaos -ScriptBlock $kaosCompletion
Register-ArgumentCompleter -Native -CommandName .\kaos -ScriptBlock $kaosCompletion
