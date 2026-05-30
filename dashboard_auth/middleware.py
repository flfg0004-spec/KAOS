"""
Dashboard Auth Middleware — API Key validation for Hermes Gateway dashboard.

Protege los endpoints del dashboard con validación de API Key.
La clave se obtiene de la variable de entorno API_SERVER_KEY o del header X-API-Key.
"""

import os
import hmac
from functools import wraps
from typing import Optional, Callable

# ─── Config ──────────────────────────────────────────────────────────────────

API_KEY = os.environ.get("API_SERVER_KEY", "")
API_KEY_HEADER = "X-API-Key"
API_KEY_PARAM = "api_key"

# ─── Helpers ─────────────────────────────────────────────────────────────────


def _verify_key(key: str) -> bool:
    """Comparación segura contra API_KEY usando HMAC constant-time."""
    if not API_KEY or not key:
        return False
    return hmac.compare_digest(API_KEY, key)


def require_api_key(handler: Callable) -> Callable:
    """Decorador que valida API Key en request antes de ejecutar el handler."""

    @wraps(handler)
    def _wrapper(request, *args, **kwargs):
        # Intentar obtener key de header
        key = request.headers.get(API_KEY_HEADER, "")
        if not key:
            # Fallback: query param
            from urllib.parse import parse_qs
            from urllib.parse import urlparse

            parsed = urlparse(request.path)
            params = parse_qs(parsed.query)
            key = params.get(API_KEY_PARAM, [""])[0]

        if not _verify_key(key):
            return _unauthorized(request)

        return handler(request, *args, **kwargs)

    return _wrapper


def _unauthorized(request) -> tuple:
    """Retorna respuesta 401."""
    body = '{"error": "Unauthorized", "message": "API Key inválida o ausente"}'
    try:
        request.send_response(401)
        request.send_header("Content-Type", "application/json")
        request.send_header("WWW-Authenticate", f'Bearer realm="dashboard", charset="UTF-8"')
        request.end_headers()
        request.wfile.write(body.encode("utf-8"))
    except Exception:
        pass
    return (401, body)


# ─── Class-based Middleware ──────────────────────────────────────────────────


class AuthMiddleware:
    """Middleware para pipeline de requests del dashboard.

    Uso:
        from dashboard_auth import AuthMiddleware
        auth = AuthMiddleware()
        if not auth.authenticate(request):
            return auth.deny(request)
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or API_KEY

    def authenticate(self, request) -> bool:
        """Verifica si el request está autenticado."""
        key = request.headers.get(API_KEY_HEADER, "").strip()
        if not key:
            parts = request.path.split("?")
            if len(parts) > 1:
                for param in parts[1].split("&"):
                    if param.startswith(f"{API_KEY_PARAM}="):
                        key = param.split("=", 1)[1]
                        break
        return bool(key) and _verify_key(key)

    def deny(self, request) -> tuple:
        """Retorna 401."""
        return _unauthorized(request)
