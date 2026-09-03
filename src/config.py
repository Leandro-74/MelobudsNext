import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".melobudsnext"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Lê o arquivo de config, caso não existir ou corrompido, devolve {}
def _read() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

# Escrve no arquivo as configs salvas
def _write(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# Carrega a config salva, ou None caso vazia
def load_config() -> dict | None:
    data = _read()
    return data if data else None

# Salva as infos do fone pareado
def save_device(address: str, name: str) -> None:
    data = _read()
    data.update({
        "address": address,
        "name": name,
    })
    _write(data)

# Apaga as infos de um fone pareado para forçar um novo escaneamento
def clear_device() -> None:
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()