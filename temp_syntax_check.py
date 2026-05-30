import sys, os
files = [
    r"C:\Users\LeonX\Documents\KAOS\.memory\_scripts\tests\test_aether_kimi.py",
    r"C:\Users\LeonX\Documents\KAOS\.memory\_scripts\tests\test_aether_config.py",
    r"C:\Users\LeonX\Documents\KAOS\.memory\_scripts\tests\test_aether_router.py",
    r"C:\Users\LeonX\Documents\KAOS\.memory\_scripts\tests\conftest.py",
    r"C:\Users\LeonX\Documents\KAOS\.memory\_scripts\lib\aether\circuit.py",
]
for f in files:
    try:
        compile(open(f, encoding='utf-8').read(), f, 'exec')
        print(f"OK: {os.path.basename(f)}")
    except SyntaxError as e:
        print(f"FAIL: {os.path.basename(f)}: {e}")
