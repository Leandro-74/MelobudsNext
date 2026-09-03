# melobudsnext/config.py
"""
Carrega e salva a configuracao (endereco MAC + UUIDs de comunicacao)
em um arquivo JSON na pasta do usuario.
"""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".melobudsnext"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict | None:
    """Carrega a configuracao salva, ou None se nao existir/estiver vazia."""
    if not CONFIG_FILE.exists():
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if data else None
    except (json.JSONDecodeError, OSError):
        return None


def save_device(address: str, uuid_service: str, uuid_write: str, uuid_notify: str) -> None:
    """Salva o endereco MAC e os UUIDs de comunicacao do fone."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "address": address,
        "uuid_service": uuid_service,
        "uuid_write": uuid_write,
        "uuid_notify": uuid_notify,
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def clear_config() -> None:
    """Remove a configuracao salva."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
