"""Validate Xiaomi MiMo API connectivity with correct auth headers."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

import httpx

XIAOMI_API_KEY = os.environ.get("XIAOMI_API_KEY", "")
XIAOMI_ENDPOINT = os.environ.get("XIAOMI_API_ENDPOINT", "https://token-plan-sgp.xiaomimimo.com/v1")

if not XIAOMI_API_KEY:
    print("❌ XIAOMI_API_KEY not set in .env")
    sys.exit(1)

print(f"Endpoint: {XIAOMI_ENDPOINT}")
print(f"Key: {XIAOMI_API_KEY[:10]}...{XIAOMI_API_KEY[-4:]}")

models_to_test = ["mimo-v2.5-pro", "mimo-v2-pro", "mimo-v2.5"]

for model in models_to_test:
    print(f"\n--- Testing model: {model} ---")
    try:
        response = httpx.post(
            f"{XIAOMI_ENDPOINT}/chat/completions",
            headers={
                "api-key": XIAOMI_API_KEY,
                "Content-Type": "application/json",
                "User-Agent": "claude-code/1.0",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Say 'ok' in one word"}],
                "max_tokens": 5,
            },
            timeout=30,
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Response: {data.get('choices', [{}])[0].get('message', {}).get('content', '')}")
        else:
            print(f"  ❌ Error: {response.text[:300]}")
    except Exception as e:
        print(f"  ❌ Exception: {e}")

print("\n--- Testing via LLM client (get_xiaomi_client) ---")
try:
    from lib.llm import get_xiaomi_client

    client = get_xiaomi_client()
    resp = client.chat.completions.create(
        model="mimo-v2.5-pro",
        messages=[{"role": "user", "content": "Say 'ok' in one word"}],
        max_tokens=5,
    )
    print(f"  ✅ Response: {resp.choices[0].message.content}")
except Exception as e:
    print(f"  ❌ Exception: {e}")
