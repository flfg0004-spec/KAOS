"""A(gnO)-KAOS — Ecosistema de agentes agno para KAOS.

Usa OpenCode GO (OpenAI-compatible) como proveedor LLM por defecto.
"""

import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

logger = logging.getLogger("agno_kaos")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

OPENCODE_GO_KEY = os.environ.get("OPENCODE_GO_KEY", "")
OPENCODE_GO_ENDPOINT = os.environ.get("OPENCODE_GO_ENDPOINT", "https://opencode.ai/zen/go/v1")
AGNO_INTERNAL_TOKEN = os.environ.get("AGNO_INTERNAL_TOKEN", "")
AGNO_DB_PATH = (Path(__file__).parent / "agno.db").resolve()

from agno.models.openai import OpenAIChat


def default_model(model_id: str = "deepseek-v4-flash") -> OpenAIChat:
    return OpenAIChat(
        id=model_id,
        api_key=OPENCODE_GO_KEY,
        base_url=OPENCODE_GO_ENDPOINT,
        role_map=dict(system="system", user="user", assistant="assistant", tool="tool"),
    )


def load_config() -> dict:
    cfg_path = Path(__file__).parent / "config.yaml"
    if not cfg_path.exists():
        return {}
    with open(cfg_path) as f:
        return yaml.safe_load(f) or {}


def get_ports() -> dict:
    cfg = load_config()
    return cfg.get("ports", {"escadron": 8030, "pilot": 8022})


def _resolve_db_path(cfg_path: str | None, default: Path) -> Path:
    if not cfg_path:
        return default.resolve()
    p = Path(cfg_path)
    if p.is_absolute():
        return p
    return (_PROJECT_ROOT / p).resolve()


def get_db():
    """Devuelve la DB configurada: Postgres si disponible, SQLite fallback."""
    cfg = load_config()
    pg_url = cfg.get("database", {}).get("postgres_url", "")
    sqlite_fallback = _resolve_db_path(
        cfg.get("database", {}).get("sqlite_fallback"),
        AGNO_DB_PATH,
    )
    strict = cfg.get("database", {}).get("strict_postgres", False)

    if pg_url:
        try:
            from agno.db.postgres import PostgresDb
            return PostgresDb(db_url=pg_url)
        except ImportError:
            if strict:
                raise RuntimeError(
                    "Postgres configurado como strict pero psycopg2 no está instalado. "
                    "pip install psycopg2-binary o strict_postgres: false"
                )
            logger.warning("Postgres no disponible (psycopg2 no instalado), usando SQLite fallback")
        except (ConnectionError, OSError) as e:
            if strict:
                raise RuntimeError(f"Postgres strict mode: no se pudo conectar — {e}")
            logger.warning("Postgres no disponible (%s), usando SQLite fallback", e)

    from agno.db.sqlite import SqliteDb
    return SqliteDb(db_file=str(sqlite_fallback))


def _load_public_key() -> str | None:
    """Lee la clave pública JWT desde el archivo configurado en config.yaml."""
    cfg = load_config()
    path = cfg.get("security", {}).get("jwt_public_key_path", "")
    if not path:
        return AGNO_INTERNAL_TOKEN or None
    p = Path(path)
    if not p.is_absolute():
        p = (_PROJECT_ROOT / p).resolve()
    if p.exists():
        return p.read_text().strip()
    return AGNO_INTERNAL_TOKEN or None


def get_auth_config():
    """Devuelve config de autorización si está habilitada."""
    cfg = load_config()
    if not cfg.get("agentos", {}).get("authorization", False):
        return None
    from agno.os.config import AuthorizationConfig

    algorithm = cfg.get("security", {}).get("jwt_algorithm", "HS256")
    key = _load_public_key()
    keys = [key] if key else [AGNO_INTERNAL_TOKEN or "dev-token"]

    return AuthorizationConfig(
        verification_keys=keys,
        algorithm=algorithm,
        user_isolation=False,
    )
