param([string]$Message, [string]$Title = "KAOS Alert", [int]$Priority = 3)
$body = @{ topic = "kaos"; message = $Message; title = $Title; priority = $Priority; tags = @("kaos") } | ConvertTo-Json
try { curl.exe -s -X POST -H "Content-Type: application/json" -d $body https://ntfy.sh 2>$null } catch {}
