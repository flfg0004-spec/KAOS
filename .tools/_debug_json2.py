import json
text = open('.opencode/opencode.json', encoding='utf-8').read()
print(f"File size: {len(text)} chars")
try:
    json.loads(text)
    print("VALID JSON")
except json.JSONDecodeError as e:
    print(f"Error: {e}")
    # Try to find the issue around the error position
    start = max(0, e.pos - 50)
    end = min(len(text), e.pos + 50)
    print(f"Context: ...{text[start:end]}...")
