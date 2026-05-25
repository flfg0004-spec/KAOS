"""KAOS Dashboard Alerts — envía alertas vía Telegram cuando las métricas están fuera de rango.

Uso:
    py .tools/alert_daemon.py          # Corre como daemon, verifica cada 5 min
    py .tools/alert_daemon.py --once   # Una sola verificación
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".memory" / "_scripts"))

KAOS_ROOT = Path(__file__).resolve().parent.parent
TIMESERIES_DIR = KAOS_ROOT / ".vault" / "quality" / "timeseries"
CACHE_DIR = KAOS_ROOT / ".memory" / "cache"
MEMORY_DIR = KAOS_ROOT / ".memory"
ALERT_STATE = KAOS_ROOT / ".vault" / "quality" / "alert-state.json"

CHECK_INTERVAL = 300  # 5 minutos


def _load_json(path):
    if path and path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _load_state():
    return _load_json(ALERT_STATE)


def _save_state(state):
    ALERT_STATE.parent.mkdir(parents=True, exist_ok=True)
    ALERT_STATE.write_text(json.dumps(state, indent=2))


def check_and_alert(once=False):
    state = _load_state()
    now = datetime.now()
    alerts_sent = 0

    # Verificar calidad
    scores_file = TIMESERIES_DIR / "verification-scores.json"
    scores = _load_json(scores_file).get("scores", [])
    if scores:
        last = scores[-1]
        composite = last.get("composite", 100)
        agent = last.get("agent", "unknown")
        score_key = f"quality_{agent}"

        if composite < 60 and state.get(score_key) != "alerted":
            _send_alert(f"🔴 CALIDAD CRÍTICA: {agent} score {composite:.1f}/100")
            state[score_key] = "alerted"
            alerts_sent += 1
        elif composite >= 80 and state.get(score_key) == "alerted":
            state[score_key] = "resolved"

    # Verificar costo
    token_data = _load_json(CACHE_DIR / "token-usage.json")
    cost = token_data.get("total_cost_usd", 0)
    cost_key = "cost_weekly"

    if cost > 10 and state.get(cost_key) != "alerted":
        _send_alert(f"💰 COSTO ALTO: ${cost:.2f} esta semana (límite: $10)")
        state[cost_key] = "alerted"
        alerts_sent += 1
    elif cost <= 5 and state.get(cost_key) == "alerted":
        state[cost_key] = "resolved"

    # Verificar broken wikilinks
    lint_path = MEMORY_DIR / "schema" / "lint-report.md"
    if lint_path.exists():
        import re
        content = lint_path.read_text(encoding="utf-8")
        m = re.search(r"Total issues:\s*(\d+)", content)
        issues = int(m.group(1)) if m else 0
        lint_key = "lint_issues"

        if issues > 3 and state.get(lint_key) != "alerted":
            _send_alert(f"🔗 BROKEN WIKILINKS: {issues} issues en lint report")
            state[lint_key] = "alerted"
            alerts_sent += 1
        elif issues == 0 and state.get(lint_key) == "alerted":
            state[lint_key] = "resolved"

    _save_state(state)

    if alerts_sent > 0:
        print(f"[{now.strftime('%H:%M')}] {alerts_sent} alerta(s) enviada(s)")
    elif not once:
        print(f"[{now.strftime('%H:%M')}] Sin alertas")

    return alerts_sent


def _send_alert(message):
    """Envía alerta vía Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print(f"[ALERT] (mock) {message}")
        return

    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        print(f"[TELEGRAM] Alerta enviada: {message[:60]}...")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar alerta: {e}")


def main():
    once = "--once" in sys.argv
    if once:
        check_and_alert(once=True)
        return

    print(f"KAOS Alert Daemon — verificando cada {CHECK_INTERVAL}s")
    while True:
        try:
            check_and_alert()
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
