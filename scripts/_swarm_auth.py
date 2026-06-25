"""
scripts/_swarm_auth.py — Carga ANTHROPIC_API_KEY desde .env si no está en el entorno.

Importar en todos los swarm scripts con:
    from scripts._swarm_auth import ensure_api_key
    ensure_api_key()
"""
from __future__ import annotations
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def ensure_api_key() -> None:
    """Set ANTHROPIC_API_KEY from .env if not already in environment."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return

    # Try .env in project root
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key == "ANTHROPIC_API_KEY" and val:
                os.environ["ANTHROPIC_API_KEY"] = val
                return

    raise EnvironmentError(
        "ANTHROPIC_API_KEY not found.\n"
        "Options:\n"
        "  1. Set it in PowerShell: $env:ANTHROPIC_API_KEY = 'sk-ant-...'\n"
        "  2. Create a .env file in the project root:\n"
        "     ANTHROPIC_API_KEY=sk-ant-...\n"
        "  3. Export it in your shell profile."
    )
