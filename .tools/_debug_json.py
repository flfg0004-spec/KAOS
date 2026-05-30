import json
try:
    json.load(open('.opencode/opencode.json'))
    print("VALID")
except json.JSONDecodeError as e:
    print(f"Error line {e.lineno} col {e.colno}: {e.msg}")
    with open('.opencode/opencode.json') as f:
        lines = f.readlines()
    start = max(0, e.lineno - 5)
    end = min(len(lines), e.lineno + 3)
    for i in range(start, end):
        marker = ">>>" if i == e.lineno - 1 else "   "
        print(f"{marker} {i+1}:{lines[i].rstrip()}")
