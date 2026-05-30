with open('.opencode/opencode.json') as f:
    lines = f.readlines()
for i in range(569, 590):
    marker = " " if i < len(lines) else "X"
    line = lines[i].rstrip() if i < len(lines) else "EOF"
    print(f"{marker} {i+1}: {line}"[:120])
