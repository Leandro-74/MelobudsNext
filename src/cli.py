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
3. Reconfigurar fone (buscar dispositivo)
4. Sair
"""

ANC_MENU = """
=== Modo ANC ===

1. Desligado
2. Cancelamento de Ruido (ANC)
3. Transparencia
"""


async def _escolher_dispositivo() -> str:
    print("Procurando fones por 5 segundos (deixe o fone no modo pareamento se for a primeira vez)...")
    encontrados = await device.scan_devices(timeout=5.0)

    if not encontrados:
        print("Nenhum dispositivo encontrado na busca.")
        endereco = input("Digite o endereco MAC manualmente (ex: C4:AC:60:07:68:09): ").strip()
        config.save_device(endereco)
        return endereco

    for i, d in enumerate(encontrados, start=1):
        print(f"{i}. {d.name or '(sem nome)'}  [{d.address}]")

    escolha = input("Escolha o numero do fone: ").strip()
    if not escolha.isdigit() or not (1 <= int(escolha) <= len(encontrados)):
        print("Opcao invalida, tentando de novo.")
        return await _escolher_dispositivo()

    escolhido = encontrados[int(escolha) - 1]
    config.save_device(escolhido.address, escolhido.name)
    return escolhido.address


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


async def _conectar(address: str) -> "device.MelobudsDevice":
    dev = device.MelobudsDevice(address)
    print(f"Conectando a {address}...")
    await dev.connect()
    print("Conectado!\n")
    return dev


async def run() -> None:
    cfg = config.load_config()
    if cfg is None or "address" not in cfg:
        print("Nenhum fone configurado ainda.")
        address = await _escolher_dispositivo()
    else:
        address = cfg["address"]

    try:
        dev = await _conectar(address)
    except Exception as e:
        print(f"Falha ao conectar: {e}")
        print("Verifique se o fone esta ligado, proximo e pareado com o computador.")
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
                address = await _escolher_dispositivo()
                dev = await _conectar(address)
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
