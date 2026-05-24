"""Docker health check for KAOS services."""

import json
import subprocess
from datetime import datetime

SERVICES = {
    "searxng": {"port": 8888, "url": "http://127.0.0.1:8888"},
    "crawl4ai": {"port": 11235, "url": "http://127.0.0.1:11235"},
}


def check_all() -> dict:
    """Check all Docker services. Returns {service: {status, error}}."""
    results = {}
    try:
        raw = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10,
        )
        if raw.returncode != 0:
            return {s: {"status": "error", "error": raw.stderr.strip()} for s in SERVICES}

        running = {}
        for line in raw.stdout.strip().split("\n"):
            if "\t" in line:
                name, status = line.split("\t", 1)
                running[name] = status

        for name, info in SERVICES.items():
            container_name = f"kaos-{name}"
            if container_name in running:
                results[name] = {"status": "running", "container": container_name,
                                 "docker_status": running[container_name]}
            else:
                results[name] = {"status": "stopped", "container": container_name}

    except FileNotFoundError:
        return {s: {"status": "error", "error": "Docker not found"} for s in SERVICES}
    except subprocess.TimeoutExpired:
        return {s: {"status": "error", "error": "Docker timeout"} for s in SERVICES}
    except Exception as e:
        return {s: {"status": "error", "error": str(e)} for s in SERVICES}

    return results


def report() -> str:
    """Generate health report string."""
    checks = check_all()
    lines = [f"# Docker Health — {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    all_ok = True
    for name, info in checks.items():
        status = info.get("status", "unknown")
        icon = "✅" if status == "running" else "❌"
        lines.append(f"{icon} {name}: {status}")
        if info.get("docker_status"):
            lines[-1] += f" ({info['docker_status']})"
        if info.get("error"):
            lines[-1] += f" — {info['error']}"
            all_ok = False

    lines.append("")
    lines.append(f"**All services: {'OK' if all_ok else 'ISSUES FOUND'}**")
    return "\n".join(lines)
