"""
KAOS Schedule — Orquestador de sesiones programadas
Ejecuta smoke/functional/audit según calendario.
Almacena última ejecución en .vault/quality/last-run.json
"""
import json
import subprocess
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
LAST_RUN = BASE / ".vault" / "quality" / "last-run.json"
SESSION_RUNNER = BASE / ".tools" / "session_runner.py"
VERIFICATION_CHAIN = BASE / ".tools" / "verification_chain.py"
DISTILL_ENGINE = BASE / ".tools" / "distill.py"
PYTHON = "py" if sys.platform == "win32" else "python3"


def load_last_run():
    if LAST_RUN.exists():
        with open(LAST_RUN) as f:
            return json.load(f)
    return {}


def save_last_run(data):
    LAST_RUN.parent.mkdir(parents=True, exist_ok=True)
    with open(LAST_RUN, "w") as f:
        json.dump(data, f, indent=2)


def should_run(today_str, last_run, key, interval_days, weekday=None):
    """Check if enough days passed and (optionally) if today is the right weekday."""
    last = last_run.get(key)
    if not last:
        return True
    last_date = datetime.fromisoformat(last).date()
    delta = (date.fromisoformat(today_str) - last_date).days
    if delta < interval_days:
        return False
    if weekday is not None and date.today().weekday() != weekday:
        return False
    return True


def run_session(session_type, profile="desarrollo"):
    cmd = [PYTHON, str(SESSION_RUNNER), session_type, profile]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout


def run_verification(profile="desarrollo"):
    cmd = [PYTHON, str(VERIFICATION_CHAIN), profile]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout

def run_distill():
    cmd = [PYTHON, str(DISTILL_ENGINE), "all"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout


def update_log(entry):
    log_path = BASE / ".memory" / "wiki" / "log.md"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n## [{date.today().isoformat()}] schedule | {entry}\n")


def main():
    today_str = date.today().isoformat()
    last_run = load_last_run()
    executed = []

    # Diario: distill + functional session (cada 24h)
    if should_run(today_str, last_run, "distill", 1):
        success, output = run_distill()
        executed.append(("distill", success))
        if success:
            last_run["distill"] = datetime.now().isoformat()
            update_log("distill automático completado")

    if should_run(today_str, last_run, "functional", 1):
        success, output = run_session("functional", "desarrollo")
        executed.append(("functional", success))
        if success:
            last_run["functional"] = datetime.now().isoformat()
            update_log("functional session completada (automática)")

    # Semanal: verification chain + audit (lunes = 0)
    if should_run(today_str, last_run, "verification", 7, weekday=0):
        success, output = run_verification("desarrollo")
        executed.append(("verification", success))
        if success:
            last_run["verification"] = datetime.now().isoformat()
            update_log("verificación cruzada semanal completada")

    if should_run(today_str, last_run, "audit", 7, weekday=0):
        success, output = run_session("audit", "auditoria")
        executed.append(("audit", success))
        if success:
            last_run["audit"] = datetime.now().isoformat()
            update_log("auditoría semanal completada")

    # Mensual: audit con perfil auditoria (1ro de cada mes)
    if date.today().day == 1:
        if should_run(today_str, last_run, "monthly_audit", 28):
            success, output = run_session("audit", "auditoria")
            executed.append(("monthly_audit", success))
            if success:
                last_run["monthly_audit"] = datetime.now().isoformat()
                update_log("auditoría mensual completada (perfil auditoría)")

    save_last_run(last_run)

    if not executed:
        print("No sessions due today.")
        return

    for session_type, success in executed:
        status = "✅" if success else "❌"
        print(f"{status} {session_type}")


if __name__ == "__main__":
    main()
