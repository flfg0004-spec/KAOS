import logging
import os
import socket
import subprocess
import time

logger = logging.getLogger("docker_lazy")

_COMPOSE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "docker-compose.yml",
)

_DOCKERLESS = None


def _is_dockerless() -> bool:
    global _DOCKERLESS
    if _DOCKERLESS is None:
        val = os.environ.get("DOCKERLESS_MODE", "false").lower()
        _DOCKERLESS = val in ("1", "true", "yes")
    return _DOCKERLESS


def _port_open(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (TimeoutError, ConnectionRefusedError, OSError):
        return False


def _docker_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def ensure_service(profile: str, service_name: str, port: int) -> bool:
    if _is_dockerless():
        logger.info("DOCKERLESS_MODE active — skipping Docker for %s", service_name)
        return False

    try:
        from lib.feature_flags import is_enabled
        if not is_enabled(f"ether_{service_name}_enabled"):
            logger.info(
                "Feature flag ether_%s_enabled=false — using native fallback",
                service_name,
            )
            return False
    except ImportError:
        pass

    if not _docker_available():
        logger.warning(
            "Docker not available — using native fallback for %s", service_name
        )
        return False

    if _port_open(port):
        return True

    logger.info("Starting Docker service %s (profile=%s)", service_name, profile)
    result = subprocess.run(
        ["docker", "compose", "-f", _COMPOSE_FILE, "--profile", profile, "up", "-d"],
        capture_output=True, text=True, timeout=60,
    )

    if result.returncode != 0:
        logger.error("Failed to start %s: %s", service_name, result.stderr)
        return False

    for _ in range(6):
        if _port_open(port):
            return True
        time.sleep(2)

    logger.warning("%s started but port %d not responding", service_name, port)
    return False


def stop_service(profile: str, service_name: str) -> bool:
    if _is_dockerless() or not _docker_available():
        return True

    result = subprocess.run(
        ["docker", "compose", "-f", _COMPOSE_FILE, "--profile", profile, "stop", service_name],
        capture_output=True, text=True, timeout=30,
    )
    return result.returncode == 0
