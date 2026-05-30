Write-Host "=== F2 VERIFICATION ===" -ForegroundColor Cyan

Write-Host "`n1. schedule_gaps:"
py -3 -c "compile(open('.memory/_scripts/scripts/schedule_gaps.py', encoding='utf-8').read(), 'schedule_gaps.py', 'exec'); Write-Host '  ✅ Syntax OK'"

Write-Host "`n2. schedule_tagger:"
py -3 -c "compile(open('.memory/_scripts/scripts/schedule_tagger.py', encoding='utf-8').read(), 'schedule_tagger.py', 'exec'); Write-Host '  ✅ Syntax OK'"

Write-Host "`n3. configure_indexes:"
py -3 -c "compile(open('.memory/_scripts/scripts/configure_indexes.py', encoding='utf-8').read(), 'configure_indexes.py', 'exec'); Write-Host '  ✅ Syntax OK'"

Write-Host "`n4. Smart Connections config:"
if (Test-Path '.obsidian/plugins/smart-connections/data.json') { Write-Host '  ✅ data.json' } else { Write-Host '  ⚠️ Not found (run --setup)' }

Write-Host "`n5. txtai config:"
if (Test-Path '.memory/cache/txtai-config.yml') { Write-Host '  ✅ txtai-config.yml' } else { Write-Host '  ⚠️ Not found (run --setup)' }

Write-Host "`n6. Pre-commit hook:"
py -3 -c "compile(open('.memory/_scripts/hooks/pre-commit-library.py', encoding='utf-8').read(), 'pre-commit-library.py', 'exec'); Write-Host '  ✅ Syntax OK'"

Write-Host "`n7. install_hooks:"
py -3 -c "compile(open('.memory/_scripts/scripts/install_hooks.py', encoding='utf-8').read(), 'install_hooks.py', 'exec'); Write-Host '  ✅ Syntax OK'"

Write-Host "`n=== F2 VERIFICATION COMPLETE ===" -ForegroundColor Cyan