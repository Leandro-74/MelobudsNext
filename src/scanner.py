import asyncio
from bleak import BleakScanner

# Escaneia dispositivos bluetooth e filtra por palavras-chave comuns
async def scan_for_qcy_devices(timeout: float = 7.0) -> list[dict]:
    print(f"Escaneando dispositivos Bluetooth por {timeout} segundos...")
    print("(Certifique-se de que o fone está fora da caixa e NAO conectado ao celular)\n")
    
    devices = await BleakScanner.discover(timeout=timeout)
    
    candidates = []
    keywords = ["QCY", "MELOBUDS", "TWS", "AIRDOTS", "HT05", "HT07", "ARCADIA"]
    
    for d in devices:
        name = d.name or ""
        # Filtra por nomes conhecidos
        if any(kw in name.upper() for kw in keywords):
            candidates.append({"name": name or "Dispositivo QCY", "address": d.address})
            
    # Se não achar nada com as keywords, retorna todos para o usuário escolher manualmente
    if not candidates and devices:
        print("Nenhum dispositivo com nome 'QCY/Melobuds' identificado automaticamente.")
        print("Listando todos os devices Bluetooth próximos:\n")
        for d in devices:
            name = d.name or "Unknown"
            candidates.append({"name": name, "address": d.address})
            
    return candidates