# melobudsnext/cli.py

# Interface de linha de comando (menu numerado) do MelobudsNext.

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

# Pede MAC e UUIDs, aproveitando pareamento do sistema
def _configurar_dispositivo() -> dict:
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

# Interativo para Ativar/Desativar o Game Mode
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

# Interativo para alterar modo ANC
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

# Estabelece conexão usando o address e os UUIDs coletados
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

# roda a interface e faz encaminhamento das funções
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

# Wrapper sincrono - usado como entry_point (console_scripts nao aceita corrotina direto)
def main() -> None:
    asyncio.run(run())
