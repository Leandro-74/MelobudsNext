# melobudsnext/cli.py

# Interface de linha de comando (menu numerado) do MelobudsNext.

import asyncio
import os
from typing import Dict, Optional

from . import config
from . import device
from . import commands
from . import menu
from .device import MelobudsDevice

async def input_async(prompt: str = "") -> str:
    return await asyncio.to_thread(input, prompt)


# Pede MAC e UUIDs, aproveitando pareamento do sistema
def _configurar_dispositivo() -> Dict[str, str]:
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

async def _escolher_nivel(quantidade: int) -> Optional[int]:
    limpar_tela()
    print(menu.ANC_INTENSE)
    escolha = (await input_async(" Escolha: ")).strip()
    if escolha.isdigit() and 1 <= int(escolha) <= 3:
        return int(escolha)
    return None

async def _acao_consultar(dev: MelobudsDevice) -> None:
    while True:
        limpar_tela()
        st = dev.state
        print(menu.painel_estado(
            bateria=st.battery_line(),
            anc=st.anc_label(),
            game_mode=st.game_mode_label(),
            versao=st.version or "desconhecida",
        ))
        escolha = (await input_async(" Escolha: ")).strip()
        if escolha == "1":
            await dev.sync_state()
        else:
            return

# Interativo para Ativar/Desativar o Game Mode
async def _acao_game_mode(dev: MelobudsDevice) -> None:
    escolha = (await input_async("Ativar (1) ou Desativar (2) Game Mode?: ")).strip()

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
    limpar_tela()
    print(menu.ANC_MENU)
    escolha = (await input_async("Escolha o modo: ")).strip()

    if escolha == "1":
        comando, nome = commands.anc_off(), "Desligado"
    elif escolha in ("2", "3", "4"):
        cenas = {
            "2": (commands.CENA_INTERIOR, "Interior"),
            "3": (commands.CENA_VIAGENS, "Viagens Diárias"),
            "4": (commands.CENA_BARULHO, "Barulho"),
        }
        cena, nome_cena = cenas[escolha]
        nivel = _escolher_nivel(3)
        if nivel is None:
            print(" Opção Inválida.")
            return
        comando = commands.anc_cena(cena, nivel)
        nome = f"{nome_cena} (nivel {nivel})"
    elif escolha in ("5", "6"):
        cenas = {
            "5": (commands.CENA_VENTO, "Ruído contra o vento"),
            "6": (commands.CENA_ADAPTATIVO, "Cancelamento Adaptativo"),
        }
        cena, nome = cenas[escolha]
        comando = commands.anc_cena(cena)
    elif escolha == "7":
        limpar_tela()
        print(menu.TRANSP_MENU)
        sub = (await input_async(" Escolha: ")).strip()
        if sub == "1":
            comando = commands.aprimoramento_vocal()
            nome = "Transparência (Aprimoramento Vocal)"
        elif sub.isdigit() and 2 <= int(sub) <= 7:
            nivel = int(sub)-1
            comando = commands.transparencia(nivel)
            nome = f"Transparência (intensidade {nivel})"
        else:
            print(" Opção Inválida.")
            return
    else:
        print(" Opção Inválida.")
        return

    await dev.send_command(comando)
    print(f"Comando enviado: modo ANC '{nome}'.")

# Estabelece conexão usando o address e os UUIDs coletados
async def _conectar(cfg: Dict[str, str]) -> MelobudsDevice:
    dev = MelobudsDevice(
        address=cfg["address"],
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
            limpar_tela()
            await dev.atualizar_bateria()
            print(menu.menu_principal(dev.state.battery_line()))
            escolha = input("Escolha uma opcao: ").strip()

            if escolha == "1":
                await _acao_game_mode(dev)
            elif escolha == "2":
                await _acao_anc(dev)
            elif escolha == "3":
                await _acao_consultar(dev)
            elif escolha == "4":
                await dev.disconnect()
                config.clear_config()
                cfg = _configurar_dispositivo()
                dev = await _conectar(cfg)
            elif escolha == "5":
                print("Ate mais!")
                break
            else:
                print("Opcao invalida.")
    finally:
        await dev.disconnect()

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')
# Wrapper sincrono - usado como entry_point (console_scripts nao aceita corrotina direto)
def main() -> None:
    asyncio.run(run())
