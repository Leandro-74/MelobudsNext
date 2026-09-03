import asyncio
from . import scanner
from . import config
from . import device
from . import commands

# testa a conexão com um candidato, enviando um comando de teste
async def _try_candidate(address: str, name: str) -> bool:
    print(f"\nTentando conectar em: {name} ({address})...")
    try:
        dev = device.MelobudsDevice(address)
        await dev.connect()
        
        print("  Conectado! Enviando comando de teste (Game Mode ON)...")
        await dev.send_command(commands.game_mode(True))
        await asyncio.sleep(1.5)
        
        resposta = input("  O fone piscou o LED ou fez um som de confirmação? [s/n]: ").strip().lower()
        
        print("  Restaurando estado (Game Mode OFF)...")
        await dev.send_command(commands.game_mode(False))
        await dev.disconnect()
        
        return resposta.startswith("s")
    except Exception as e:
        print(f"  Falha ao conectar ou comunicar: {e}")
        print("  Dica: Verifique se o fone não está conectado ao seu celular no momento.")
        return False

# Fallback para caso de falha no pair automático
def _manual_entry() -> dict:
    print("\n--- Entrada Manual ---")
    print("Informe o MAC Address do fone.")
    print("No Windows: Configurações > Bluetooth e dispositivos.")
    print("No Linux: 'bluetoothctl devices' ou 'hcitool dev'.")
    
    while True:
        address = input("MAC Address (ex: C4:AC:60:07:68:09): ").strip()
        if len(address) >= 17: # Validação bem básica de formato
            break
        print("  Formato de MAC inválido. Tente novamente.")
        
    name = input("Nome do dispositivo (opcional, Enter para pular): ").strip() or "Manual Device"
    
    return {"address": address, "name": name}

# Executa o assistente e devolve o MAC em caso de pareamento concluído
async def run_wizard() -> dict:
    print("\n=== Assistente de Pareamento Melobuds Next ===")
    
    candidates = await scanner.scan_for_qcy_devices()
    chosen_device = None
    
    if not candidates:
        print("Nenhum dispositivo Bluetooth encontrado no escaneamento.")
    else:
        print(f"\nDispositivos encontrados ({len(candidates)}):")
        for i, d in enumerate(candidates, start=1):
            print(f"  {i}. {d['name']} [{d['address']}]")
            
        while True:
            escolha = input("\nEscolha o número do fone para testar (ou 'm' para manual, 's' para sair): ").strip().lower()
            if escolha == 's':
                raise KeyboardInterrupt("Pareamento cancelado pelo usuário.")
            if escolha == 'm':
                chosen_device = _manual_entry()
                break
            if escolha.isdigit() and 1 <= int(escolha) <= len(candidates):
                candidate = candidates[int(escolha) - 1]
                if await _try_candidate(candidate["address"], candidate["name"]):
                    chosen_device = candidate
                    print("  Confirmado!")
                    break
                print("  Ok, vamos tentar o próximo ou você pode escolher outro.")
            else:
                print("  Opção inválida.")
                
    # Se ainda não tem um device escolhido (ex: falhou em todos e não foi para o manual)
    if chosen_device is None:
        print("\nNenhum candidato automático funcionou.")
        chosen_device = _manual_entry()
        # Tenta o manual também
        if not await _try_candidate(chosen_device["address"], chosen_device["name"]):
            print("  Aviso: O teste falhou no device manual, mas salvaremos mesmo assim.")

    config.save_device(chosen_device["address"], chosen_device["name"])
    print(f"\nConfiguração salva com sucesso! Fone: {chosen_device['name']}")
    return chosen_device