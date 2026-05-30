"""Syntax check all modified files."""
import os, sys

BASE = r"C:\Users\LeonX\Documents\KAOS"
files = [
    r".memory\_scripts\tests\test_aether_kimi.py",
    r".memory\_scripts\tests\test_aether_config.py",
    r".memory\_scripts\tests\test_aether_router.py",
    r".memory\_scripts\tests\conftest.py",
    r".memory\_scripts\lib\aether\circuit.py",
]
errors = []
for rel in files:
    path = os.path.join(BASE, rel)
    try:
        compile(open(path, encoding="utf-8").read(), path, "exec")
        print(f"OK: {rel}")
    except SyntaxError as e:
        print(f"FAIL: {rel}: {e}")
        errors.append(rel)

if errors:
    print(f"\n{len(errors)} file(s) with syntax errors!")
    sys.exit(1)
else:
    print(f"\nAll {len(files)} files OK!")
