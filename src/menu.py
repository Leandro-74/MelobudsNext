# src/menu.py
LARGURA = 46
ESC = "\x1b"

def _linha(texto: str = "") -> str:
    return "║" + (" " + texto).ljust(LARGURA) + "║"

def _topo() -> str:
    return "╔" + "═" * LARGURA + "╗"

def _sep() -> str:
    return "╠" + "═" * LARGURA + "╣"

def _fundo() -> str:
    return "╚" + "═" * LARGURA + "╝"

def linhas_principal(status: str) -> list:
    return [
        "MelobudsNext - QCY Melobuds Pro",
        status,
        _sep(),
        "1. Ativar/Desativar Game Mode",
        "2. Alterar modo ANC",
        "3. Consultar estados",
        "4. Reconfigurar fone (MAC/UUIDs)",
        "5. Sair",
    ]

def linhas_game_mode() -> list:
    return [
        "MelobudsNext - Game Mode",
        _sep(),
        "1. Ativar",
        "2. Desativar",
    ]

def linhas_anc() -> list:
    return [
        "MelobudsNext - ANC",
        _sep(),
        "1. Desligado",
        "2. Interior",
        "3. Viagens Diárias",
        "4. Barulho",
        "5. Ruído Contra o Vento",
        "6. Cancelamento Adaptativo",
        "7. Transparência",
    ]

def linhas_nivel() -> list:
    return [
        "MelobudsNext - Nível do ANC",
        _sep(),
        "1. Intensidade 1",
        "2. Intensidade 2",
        "3. Intensidade 3",
    ]

def linhas_transparencia() -> list:
    return [
        "MelobudsNext - Modo Transparência",
        _sep(),
        "1. Aprimoramento Vocal",
        "2. Intensidade 1",
        "3. Intensidade 2",
        "4. Intensidade 3",
        "5. Intensidade 4",
        "6. Intensidade 5",
        "7. Intensidade 6",
    ]

def linhas_estado(bateria: str, anc: str, game_mode: str, versao: str) -> list:
    return [
        "MelobudsNext - Estado do Fone",
        _sep(),
        f"Bateria:   {bateria}",
        f"ANC:       {anc}",
        f"Game Mode: {game_mode}",
        f"Versao:    {versao}",
        _sep(),
        "1. Atualizar tudo agora (leituras + 0xFE)",
        "Enter/outro: voltar ao menu",
    ]

def abrir_caixa(linhas: list, prompt: str) -> None:
    print(_topo())
    for l in linhas:
        print(l if l.startswith("╠") else _linha(l))
    print(_sep())
    texto = " " + prompt
    print("║" + texto + " " * max(1, LARGURA - len(texto)) + "║")
    print(_fundo())
    col = 2 + len(texto)
    print(f"{ESC}[2A{ESC}[{col}G", end="", flush=True)

def fechar_caixa() -> None:
    print(f"{ESC}[1B", end="", flush=True)

def perguntar(linhas: list, prompt: str) -> str:
    abrir_caixa(linhas, prompt)
    valor = input()
    fechar_caixa()
    return valor.strip()