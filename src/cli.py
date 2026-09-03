# melobudsnext/cli.py
"""
Interface de linha de comando (menu numerado) do MelobudsNext.
"""

import asyncio

from . import config
from . import device
from . import commands

MENU = """
=== MelobudsNext - Controle do QCY Melobuds Pro ===

1. Ativar/Desativar Game Mode
2. Alterar modo ANC
3. Reconfigurar fone (MAC/UUIDs)
4. Sair
"""

ANC_MENU = """
=== Modo ANC ===

1. Desligado
2. Cancelamento de Ruido (ANC)
3. Transparencia
"""


def _configurar_dispositivo() -> dict:
    """
    Pede o MAC e os UUIDs de comunicacao diretamente - sem escanear via
    BLE. Isso e necessario porque um fone ja pareado e conectado (em uso
    normal) geralmente para de anunciar (advertise) via BLE, entao o
    scanner nao o encontraria mesmo estando disponivel. Conectar direto
    pelo MAC reaproveita o pareamento que o Windows ja tem, sem parear
    de novo.
    """
    print("\nO fone precisa ja estar pareado com o Windows (Configuracoes > Dispositivos > Bluetooth).")
    endereco = input(
        f"Endereco MAC do fone (Enter para usar {device.DEFAULT_ADDRESS}): "
    ).strip() or device.DEFAULT_ADDRESS

    usar_padrao = input("Usar os UUIDs padrao ja confirmados? [S/n]: ").strip().lower()
    if usar_padrao == "n":
        uuid_service = input(f"UUID do servico (Enter para {device.DEFAULT_UUID_SERVICE}): ").strip() or device.DEFAULT_UUID_SERVICE
        uuid_write = input(f"UUID de escrita (Enter para {device.DEFAULT_UUID_WRITE}): ").strip() or device.DEFAULT_UUID_WRITE
        uuid_notify = input(f"UUID de notificacao (Enter para {device.DEFAULT_UUID_NOTIFY}): ").strip() or device.DEFAULT_UUID_NOTIFY
    else:
        uuid_service = device.DEFAULT_UUID_SERVICE
        uuid_write = device.DEFAULT_UUID_WRITE
        uuid_notify = device.DEFAULT_UUID_NOTIFY

    config.save_device(endereco, uuid_service, uuid_write, uuid_notify)
    return {
        "address": endereco,
        "uuid_service": uuid_service,
        "uuid_write": uuid_write,
        "uuid_notify": uuid_notify,
    }


async def _acao_game_mode(dev: "device.MelobudsDevice") -> None:
    escolha = input("Ativar (1) ou Desativar (2) Game Mode? ").strip()
    if escolha == "1":
        await dev.send_command(commands.game_mode(True))
        print("Comando enviado: Game Mode ativado.")
    elif escolha == "2":
        await dev.send_command(commands.game_mode(False))
        print("Comando enviado: Game Mode desativado.")
    else:
        print("Opcao invalida.")


async def _acao_anc(dev: "device.MelobudsDevice") -> None:
    print(ANC_MENU)
    escolha = input("Escolha o modo: ").strip()
    mapa = {
        "1": ("Desligado", commands.ANC_OFF),
        "2": ("ANC", commands.ANC_ON),
        "3": ("Transparencia", commands.ANC_TRANSPARENCY),
    }
    opcao = mapa.get(escolha)
    if opcao is None:
        print("Opcao invalida.")
        return
    nome, pacote = opcao
    await dev.send_command(pacote)
    print(f"Comando enviado: modo ANC '{nome}'.")


async def _conectar(cfg: dict) -> "device.MelobudsDevice":
    dev = device.MelobudsDevice(
        cfg["address"],
        uuid_service=cfg.get("uuid_service", device.DEFAULT_UUID_SERVICE),
        uuid_write=cfg.get("uuid_write", device.DEFAULT_UUID_WRITE),
        uuid_notify=cfg.get("uuid_notify", device.DEFAULT_UUID_NOTIFY),
    )
    print(f"Conectando a {cfg['address']} (pareamento existente do Windows)...")
    await dev.connect()
    print("Conectado!\n")
    return dev


async def run() -> None:
    cfg = config.load_config()
    if cfg is None or "address" not in cfg:
        print("Nenhum fone configurado ainda.")
        cfg = _configurar_dispositivo()

    try:
        dev = await _conectar(cfg)
    except Exception as e:
        print(f"Falha ao conectar: {e}")
        print("Verifique se o fone esta ligado, proximo e pareado nas Configuracoes de Bluetooth do Windows.")
        return

    try:
        while True:
            print(MENU)
            escolha = input("Escolha uma opcao: ").strip()

            if escolha == "1":
                await _acao_game_mode(dev)
            elif escolha == "2":
                await _acao_anc(dev)
            elif escolha == "3":
                await dev.disconnect()
                config.clear_config()
                cfg = _configurar_dispositivo()
                dev = await _conectar(cfg)
            elif escolha == "4":
                print("Ate mais!")
                break
            else:
                print("Opcao invalida.")
    finally:
        await dev.disconnect()


def main() -> None:
    """Wrapper sincrono - usado como entry_point (console_scripts nao aceita corrotina direto)."""
    asyncio.run(run())
