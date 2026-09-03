# melobudsnext/config.py]

# Carrega e salva configs (MAC address e UUIDs) em um JSON na /home

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".melobudsnext"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Carrega a config salva, ou retorna None se vazia ou não existir
def load_config() -> dict | None:
    if not CONFIG_FILE.exists():
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if data else None
    except (json.JSONDecodeError, OSError):
        return None

# Salva MAC address e UUIDs
def save_device(address: str, uuid_service: str, uuid_write: str, uuid_notify: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "address": address,
        "uuid_service": uuid_service,
        "uuid_write": uuid_write,
        "uuid_notify": uuid_notify,
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# Apaga config salva
def clear_config() -> None:
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
