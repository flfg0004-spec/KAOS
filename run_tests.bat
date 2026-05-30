@echo off
cd /d "C:\Users\LeonX\Documents\KAOS\.memory\_scripts"
py -3 -m pytest tests/test_kratos_e2e.py tests/test_kratos_integration.py tests/test_quality_gate.py tests/test_lang_utils.py tests/test_kratos_benchmarks.py -v --no-header
