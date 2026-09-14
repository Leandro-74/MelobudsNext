# src/config.py

import json
from pathlib import Path
from typing import Optional, Dict

CONFIG_DIR = Path.home() / ".melobudsnext"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Le o JSON salvo; None se nao existir ou estiver corrompido
def load_config() -> Optional[Dict[str, str]]:
    if not CONFIG_FILE.exists():
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if data else None
    except (ValueError, OSError):
        return None

# Persiste MAC e UUIDs para as proximas execucoes
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

# Apaga a config salva (fluxo de reconfigurar)
def clear_config() -> None:
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
