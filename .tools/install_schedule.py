# KAOS Scheduled Tasks — Run as Administrator
# Open PowerShell as Administrator and run:  py -3 .tools\install_schedule.py

import subprocess, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RUNNER = str(BASE / ".tools/session_runner.py")

tasks = [
    {
        "name": "KAOS-Daily-Quality",
        "action": ["py", "-3", RUNNER, "functional", "desarrollo"],
        "trigger": "DAILY",
        "time": "08:00",
    },
    {
        "name": "KAOS-Daily-Distill",
        "action": ["py", "-3", str(BASE / ".tools/distill.py"), "all", "--new-only"],
        "trigger": "DAILY",
        "time": "06:00",
    },
    {
        "name": "KAOS-Weekly-Audit",
        "action": ["py", "-3", RUNNER, "audit", "desarrollo"],
        "trigger": "WEEKLY",
        "day": "MON",
        "time": "06:00",
    },
    {
        "name": "KAOS-Vault-Maintenance",
        "action": ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(BASE / ".agents/scripts/vault-maintenance.ps1")],
        "trigger": "WEEKLY",
        "day": "WED",
        "time": "22:00",
    },
    {
        "name": "KAOS-Vault-Health",
        "action": ["py", "-3", str(BASE / ".memory/_scripts/vault.py"), "health", "--auto"],
        "trigger": "WEEKLY",
        "day": "SUN",
        "time": "22:00",
    },
    {
        "name": "KAOS-Weekly-Report",
        "action": ["py", "-3", str(BASE / ".memory/_scripts/vault.py"), "report"],
        "trigger": "WEEKLY",
        "day": "FRI",
        "time": "18:00",
    },
    {
        "name": "KAOS-mcp-embed",
        "action": ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(BASE / ".agents/scripts/mcp-embed-service.ps1"), "start"],
        "trigger": "DAILY",
        "time": "05:00",
    },
    {
        "name": "KAOS-Dashboard-Update",
        "action": ["py", "-3", str(BASE / ".memory/_scripts/vault.py"), "dashboard"],
        "trigger": "DAILY",
        "time": "05:30",
    },
    {
        "name": "KAOS-GitHub-Push",
        "action": ["powershell.exe", "-Command", "cd", str(BASE), ";", "git", "push", "origin", "master"],
        "trigger": "DAILY",
        "time": "23:00",
    },
    {
        "name": "KAOS-Strategy-Review",
        "action": ["py", "-3", str(BASE / ".memory/_scripts/vault.py"), "consolidate"],
        "trigger": "WEEKLY",
        "day": "SUN",
        "time": "20:00",
    },
    {
        "name": "KAOS-Docker-Health",
        "action": ["py", "-3", str(BASE / ".memory/_scripts/vault.py"), "docker"],
        "trigger": "DAILY",
        "time": "09:00",
    },
    {
        "name": "KAOS-Obsidian-Sync",
        "action": ["py", "-3", str(BASE / ".tools/vault-sync.py"), "--quick"],
        "trigger": "DAILY",
        "time": "06:30",
    },
    {
        "name": "KAOS-GPT55-Bridge",
        "action": ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(BASE / ".agents/scripts/kitty-bridge-service.ps1"), "start"],
        "trigger": "DAILY",
        "time": "05:00",
    },
]

for t in tasks:
    action_cmd = t["action"]
    exe = action_cmd[0]
    args = " ".join(f'"{a}"' if " " in a else a for a in action_cmd[1:])
    action = f'New-ScheduledTaskAction -Execute "{exe}" -Argument \'{args}\''
    if t["trigger"] == "DAILY":
        trigger = f'New-ScheduledTaskTrigger -Daily -At {t["time"]}'
    else:
        trigger = f'New-ScheduledTaskTrigger -Weekly -DaysOfWeek {t["day"]} -At {t["time"]}'

    cmd = f'Register-ScheduledTask -TaskName "{t["name"]}" -Action ({action}) -Trigger ({trigger}) -RunLevel Highest -Force'
    print(f"Creating: {t['name']}...")
    r = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  ✅ {t['name']}")
    else:
        print(f"  ❌ {t['name']}: {r.stderr.strip()}")
