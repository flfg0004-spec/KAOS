"""Docker health check for KAOS services.

Respects DOCKERLESS_MODE and profile-based service activation.
Core services: SearXNG (8888), Crawl4AI (11235).
Optional: Langfuse (3000) only if ETHER_LANGFUSE_ENABLED flag is true.
"""

import os
import subprocess
from datetime import datetime

CORE_SERVICES = {
    "searxng": {"port": 8888, "url": "http://127.0.0.1:8888"},
    "crawl4ai": {"port": 11235, "url": "http://127.0.0.1:11235"},
}

OPTIONAL_SERVICES = {
    "langfuse": {"port": 3000, "url": "http://127.0.0.1:3000"},
    "sandbox": {"port": None, "check": "container"},
}


def _docker_available() -> bool:
    """Check if Docker is available and DOCKERLESS_MODE is not active."""
    if os.environ.get("DOCKERLESS_MODE", "").lower() == "true":
        return False
    try:
        subprocess.run(
            ["docker", "ps"],
            capture_output=True, timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _get_services() -> dict:
    """Build service dict based on environment flags."""
    services = dict(CORE_SERVICES)
    try:
        from lib.feature_flags import is_enabled
        langfuse_active = is_enabled("infra_langfuse")
    except ImportError:
        langfuse_active = os.environ.get("LANGFUSE_ENABLED", "").lower() in ("true", "1")
    if langfuse_active:
        services.update(OPTIONAL_SERVICES)
    return services


def check_all() -> dict:
    """Check all active Docker services. Returns {service: {status, error}}."""
    results = {}
    services = _get_services()

    if not _docker_available():
        return {s: {"status": "error", "error": "Docker not available or DOCKERLESS_MODE active"}
                for s in services}

    try:
        raw = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10,
        )
        if raw.returncode != 0:
            return {s: {"status": "error", "error": raw.stderr.strip()} for s in services}

        running = {}
        for line in raw.stdout.strip().split("\n"):
            if "\t" in line:
                name, status = line.split("\t", 1)
                running[name] = status

        for name, info in services.items():
            container_name = f"kaos-{name}"
            if container_name in running:
                results[name] = {
                    "status": "running",
                    "container": container_name,
                    "docker_status": running[container_name],
                }
            else:
                results[name] = {"status": "stopped", "container": container_name}

    except FileNotFoundError:
        return {s: {"status": "error", "error": "Docker not found"} for s in services}
    except subprocess.TimeoutExpired:
        return {s: {"status": "error", "error": "Docker timeout"} for s in services}
    except Exception as e:
        return {s: {"status": "error", "error": str(e)} for s in services}

    return results


def report() -> str:
    """Generate health report string."""
    checks = check_all()
    lines = [f"# Docker Health — {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    all_ok = True
    for name, info in checks.items():
        status = info.get("status", "unknown")
        icon = "+" if status == "running" else "-"
        lines.append(f"{icon} {name}: {status}")
        if info.get("docker_status"):
            lines[-1] += f" ({info['docker_status']})"
        if info.get("error"):
            lines[-1] += f" — {info['error']}"
            all_ok = False

    lines.append("")
    lines.append(f"**All services: {'OK' if all_ok else 'ISSUES FOUND'}**")
    return "\n".join(lines)
