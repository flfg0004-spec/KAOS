"""Dashboard Auth — middleware de autenticación API Key para Hermes Dashboard."""

from .middleware import AuthMiddleware, require_api_key

__all__ = ["AuthMiddleware", "require_api_key"]
