import asyncio
import sys
from . import config
from . import device
from . import commands
from . import pairing

MENU = """
=== Melobuds Next - Controle BLE para QCY ===

1. Ler Bateria e Status
2. Game Mode (Ligar/Desligar)
3. ANC (Modos de Ruído)
4. Reconfigurar Fone (Pareamento)
5. Sair

"""

# Tenta conexão, caso falhe, avisa
async def _ensure_connected(dev: device.MelobudsDevice) -> bool:
    if dev.is_connected:
        return True
        
    print("Conectando ao fone...")
    try:
        await dev.connect()
        await asyncio.sleep(1.5) 
        return True
    except Exception as e:
        print(f"\n⚠️ Falha ao conectar: {e}")
        print("Dica: O fone pode estar dormindo ou conectado ao celular.")
        print("Tire-o da caixa e desconecte o Bluetooth do celular, depois tente novamente.")
        return False

# Lê infos mandadas pelo fone
async def _acao_ler_status(dev: device.MelobudsDevice):
    if not await _ensure_connected(dev):
        return
    print("Solicitando status da bateria e conectividade...")
    # O fone geralmente envia notificações de bateria (Cmd 0x16) ao conectar.
    # Vamos apenas aguardar para que o _notification_handler do device.py as imprima.
    await asyncio.sleep(2.5)
    print("(Se nenhuma bateria apareceu acima, o fone pode não suportar leitura direta via GATT)")

# Função responsável pelo controle do Game Mode
async def _acao_game_mode(dev: device.MelobudsDevice):
    if not await _ensure_connected(dev):
        return
        
    print("\n=== Game Mode ===")
    print("1. Ligar")
    print("2. Desligar")
    escolha = input("Escolha: ").strip()
    
    if escolha == "1":
        await dev.send_command(commands.game_mode(True))
        print("✅ Game Mode LIGADO.")
    elif escolha == "2":
        await dev.send_command(commands.game_mode(False))
        print("✅ Game Mode DESLIGADO.")
    else:
        print("Opção inválida.")

# Função responsável pelo controle do ANC
async def _acao_anc(dev: device.MelobudsDevice):
    if not await _ensure_connected(dev):
        return
        
    print("\n=== ANC (Cancelamento de Ruído) ===")
    print("1. Desligado")
    print("2. ANC (Ativo)")
    print("3. Transparência")
    escolha = input("Escolha: ").strip()
    
    if escolha == "1":
        await dev.send_command(commands.anc_off())
        print("✅ ANC Desligado.")
    elif escolha == "2":
        await dev.send_command(commands.anc_on())
        print("✅ ANC Ativado.")
    elif escolha == "3":
        await dev.send_command(commands.anc_transparency())
        print("✅ Modo Transparência Ativado.")
    else:
        print("Opção inválida.")

# Roda a interface
async def run():
    cfg = config.load_config()
    if cfg is None:
        print("Nenhuma configuracao encontrada. Vamos parear seu fone.")
        try:
            cfg = await pairing.run_wizard()
        except KeyboardInterrupt:
            print("\nOperacao cancelada.")
            sys.exit(0)

    dev = device.MelobudsDevice(cfg["address"])
    print(f"\nFone configurado: {cfg.get('name', 'Melobuds')} ({cfg['address']})")

    while True:
        print(MENU)
        escolha = input("Escolha uma opção: ").strip()

        try:
            if escolha == "1":
                await _acao_ler_status(dev)
            elif escolha == "2":
                await _acao_game_mode(dev)
            elif escolha == "3":
                await _acao_anc(dev)
            elif escolha == "4":
                await dev.disconnect()
                config.clear_device()
                try:
                    cfg = await pairing.run_wizard()
                    dev = device.MelobudsDevice(cfg["address"])
                except KeyboardInterrupt:
                    print("\nOperacao cancelada.")
            elif escolha == "5":
                print("Desconectando e saindo...")
                await dev.disconnect()
                break
            else:
                print("Opção inválida.")
        except Exception as e:
            print(f"\n❌ Erro durante a operacao: {e}")
            print("Tente reconectar ou verifique se o fone está ligado.")
            
        input("\nPressione Enter para continuar...")