#src/cli.py

import asyncio
import os
from typing import Dict, Optional

from . import config
from . import device
from . import commands
from . import menu
from . import keys
from .device import MelobudsDevice

async def input_async(prompt: str = "") -> str:
    return await asyncio.to_thread(input, prompt)

async def perguntar_async(linhas: list, prompt: str) -> str:
    menu.abrir_caixa(linhas, prompt)
    valor = await input_async()
    menu.fechar_caixa()
    return valor.strip()

def _configurar_dispositivo() -> Dict[str, str]:
    limpar_tela()
    print("\n O fone precisa já estar pareado com o Windows (Configurações > Dispositivos > Bluetooth).")
    endereco = menu.perguntar(
        ["Endereço MAC do fone", f"Enter para usar {device.DEFAULT_ADDRESS}"],
        "MAC: ",
    ) or device.DEFAULT_ADDRESS
    limpar_tela()
    usar_padrao = menu.perguntar(
        ["Usar os UUIDs padrão já confirmados?"], "[S/n]: "
    ).lower()
    if usar_padrao == "n":
        uuid_service = input(f"UUID do serviço (Enter para {device.DEFAULT_UUID_SERVICE}): ").strip() or device.DEFAULT_UUID_SERVICE
        uuid_write = input(f"UUID de escrita (Enter para {device.DEFAULT_UUID_WRITE}): ").strip() or device.DEFAULT_UUID_WRITE
        uuid_notify = input(f"UUID de notificação (Enter para {device.DEFAULT_UUID_NOTIFY}): ").strip() or device.DEFAULT_UUID_NOTIFY
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
    escolha = await perguntar_async(menu.linhas_nivel(), "Escolha: ")
    if escolha.isdigit() and 1 <= int(escolha) <= quantidade:
        return int(escolha)
    return None

async def _acao_consultar(dev: MelobudsDevice) -> None:
    while True:
        limpar_tela()
        st = dev.state
        escolha = await perguntar_async(
            menu.linhas_estado(dev.state),
            "Escolha:",
        )
        if escolha == "1":
            await dev.sync_state()
        else:
            return

async def _acao_game_mode(dev: MelobudsDevice) -> None:
    limpar_tela()
    escolha = await perguntar_async(menu.linhas_game_mode(), "Escolha: ")

    if escolha == "1":
        await dev.send_command(commands.game_mode(True))
        print("Comando enviado: Game Mode ativado.")
    elif escolha == "2":
        await dev.send_command(commands.game_mode(False))
        print("Comando enviado: Game Mode desativado.")
    else:
        print("Opção inválida.")

async def _acao_sleep_mode(dev: MelobudsDevice) -> None:
    limpar_tela()
    escolha = await perguntar_async(menu.linhas_sleep_mode(), "Escolha: ")

    if escolha == "1":
        await dev.send_command(commands.sleep_mode(True))
        print("Comando enviado: Modo de Sono ativado.")
    elif escolha == "2":
        await dev.send_command(commands.sleep_mode(False))
        print("Comando enviado: Modo de Sono desativado.")
    else:
        print("Opção inválida.")

async def _acao_ldac(dev: MelobudsDevice) -> None:
    limpar_tela()
    escolha = await perguntar_async(menu.linhas_ldac(), "Escolha: ")

    if escolha == "1":
        await dev.send_command(commands.ldac(True))
    elif escolha == "2":
        await dev.send_command(commands.ldac(False))

async def _acao_anc(dev: "device.MelobudsDevice") -> None:
    limpar_tela()
    escolha = await perguntar_async(menu.linhas_anc(), "Escolha o modo: ")

    if escolha == "1":
        comando, nome = commands.anc_off(), "Desligado"
    elif escolha in ("2", "3", "4"):
        cenas = {
            "2": (commands.CENA_INTERIOR, "Interior"),
            "3": (commands.CENA_VIAGENS, "Viagens Diárias"),
            "4": (commands.CENA_BARULHO, "Barulho"),
        }
        cena, nome_cena = cenas[escolha]
        nivel = await _escolher_nivel(3)
        if nivel is None:
            print(" Opção Inválida.")
            return
        comando = commands.anc_cena(cena, nivel)
        nome = f"{nome_cena} (nível {nivel})"
    elif escolha in ("5", "6"):
        cenas = {
            "5": (commands.CENA_VENTO, "Ruído Contra o Vento"),
            "6": (commands.CENA_ADAPTATIVO, "Cancelamento Adaptativo"),
        }
        cena, nome = cenas[escolha]
        comando = commands.anc_cena(cena)
    elif escolha == "7":
        limpar_tela()
        sub = await perguntar_async(menu.linhas_transparencia(), "Escolha: ")
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
    await dev.sync_state()

async def _acao_renomear(dev: MelobudsDevice) -> None:
    limpar_tela()
    menu.abrir_caixa(
        menu.linhas_rename(dev.state.nome or "desconhecido"),
        "Novo nome: ",
    )
    novo = (await input_async()).strip()
    menu.fechar_caixa()

    if not novo:
        print("  Rename cancelado.")
        return
    if len(novo.encode("utf-8")) > 30:
        print("  Nome muito longo (maximo ~30 caracteres).")
        return

    comando = commands.rename_device(novo)
    await dev.send_command(comando)
    dev.state.aplicar(comando)
    print(f"  Comando enviado: novo nome '{novo}'.")

async def _acao_touch(dev: MelobudsDevice) -> None:
    while True:
        limpar_tela()
        mapping = dev.state.touch or {}
        escolha = await perguntar_async(menu.linhas_touch(mapping), "Escolha: ")

        if escolha.isdigit() and 1 <= int(escolha) <= 8:
            key = keys.KEY_ORDER[int(escolha) - 1]
            limpar_tela()
            f_escolha = await perguntar_async(menu.linhas_funcoes(), "Função: ")
            if f_escolha.isdigit() and 1 <= int(f_escolha) <= len(keys.FUNC_ORDER):
                mapping[key] = keys.FUNC_ORDER[int(f_escolha) - 1]
                await dev.gravar_touch(mapping)
                dev.state.touch = dict(mapping)
        elif escolha == "9":
            await dev.gravar_touch({k: keys.FUNC_NONE for k in keys.KEY_ORDER})
            dev.state.touch = {k: keys.FUNC_NONE for k in keys.KEY_ORDER}
        elif escolha == "10" and dev.state.touch_inicial:
            await dev.gravar_touch(dev.state.touch_inicial)
            dev.state.touch = dict(dev.state.touch_inicial)
        else:
            return

async def _acao_ajustes(dev: MelobudsDevice) -> None:
    while True:
        limpar_tela()
        escolha = await perguntar_async(menu.linhas_ajustes(dev.state), "Escolha: ")
        if escolha == "1":
            await _acao_balance(dev)
        elif escolha == "2":
            await dev.disconnect()
            config.clear_config()
            cfg = _configurar_dispositivo()
            dev = await _conectar(cfg)
        elif escolha == "3":
            await _acao_tone_volume(dev)
        elif escolha == "4":
            await _acao_game_mode(dev)
        elif escolha == "5":
            await _acao_sleep_mode(dev)
        elif escolha == "6":
            await _acao_ldac(dev)
        else:
            return


async def _acao_balance(dev: MelobudsDevice) -> None:
    limpar_tela()
    escolha = await perguntar_async(
        menu.linhas_balance(dev.state.balance_label()), "Escolha: "
    )
    if escolha == "1":
        valor = 0
    elif escolha == "2":
        valor = 50
    elif escolha == "3":
        valor = 100
    elif escolha == "4":
        raw = await perguntar_async(
            ["Valor de 0 (esquerda) a 100 (direita): "], "Valor: "
        )
        if not raw.isdigit() or not 0 <= int(raw) <= 100:
            print("  Valor invalido.")
            return
        valor = int(raw)
    else:
        return
    comando = commands.sound_balance(valor)
    await dev.send_command(comando)
    dev.state.aplicar(comando)
    print(f"  Equilibrio ajustado para {valor}.")

async def _acao_tone_volume(dev: MelobudsDevice) -> None:
    limpar_tela()
    escolha = await perguntar_async(
        menu.linhas_tone_vol(dev.state.tone_volume_label()), "Escolha: "
    )
    if escolha not in ("1", "2", "3", "4"):
        return
    comando = commands.tone_volume(int(escolha))
    await dev.send_command(comando)
    dev.state.aplicar(comando)
    await asyncio.sleep(0.5)
    await dev.send_command(
        commands.request_data(commands.CMD_TONE_VOLUME)
    )

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

async def run() -> None:
    cfg = config.load_config()
    if cfg is None or "address" not in cfg:
        print("Nenhum fone configurado ainda.")
        cfg = _configurar_dispositivo()

    try:
        dev = await _conectar(cfg)
    except Exception as e:
        print(f"Falha ao conectar: {e}")
        print("Verifique se o fone está ligado, próximo e pareado nas Configurações de Bluetooth do Windows.")
        return

    try:
        while True:
            limpar_tela()
            await dev.atualizar_bateria()
            escolha = await perguntar_async(
                menu.linhas_principal(dev.state.battery_line(), dev.state.nome),
                "Escolha uma opção: ",
            )

            if escolha == "1":
                await _acao_anc(dev)
            elif escolha == "2":
                await _acao_consultar(dev)
            elif escolha == "3":
                await _acao_renomear(dev)
            elif escolha == "4":
                await _acao_touch(dev)
            elif escolha == "5":
                await _acao_ajustes(dev)
            elif escolha == "6":
                print("Até mais!")
                break
            else:
                print("Opção inválida.")
    finally:
        await dev.disconnect()

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def main() -> None:
    asyncio.run(run())