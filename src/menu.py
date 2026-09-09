# src/menu.py

from typing import Optional

from . import keys
from . import state

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

def linhas_principal(status: str, nome_fone: Optional[str] = None) -> list:
    return [
        f"MelobudsNext - {nome_fone or 'QCY Melobuds Pro'}",
        status,
        _sep(),
        "1. Ativar/Desativar Game Mode",
        "2. Alterar modo ANC",
        "3. Consultar estados",
        "4. Renomear fone",
        "5. Personalizar touch",
        "6. Ajustes do fone",
        "7. Reconfigurar fone (MAC/UUIDs)",
        "8. Sair",
    ]

def linhas_rename(nome_atual: str) -> list:
    return [
        "MelobudsNext - Renomear Fone",
        _sep(),
        f"Nome atual: {nome_atual}",
        "",
        "Digite o novo nome e pressione Enter.",
        "Deixe vazio para cancelar.",
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

def linhas_estado(state) -> list:
    return [
        "MelobudsNext - Estado do Fone",
        _sep(),
        f"Bateria:    {state.battery_line()}",
        f"ANC:        {state.anc_label()}",
        f"Game Mode:  {state.game_mode_label()}",
        f"Versao:     {state.version or 'desconhecida'}",
        f"Equilibrio: {state.balance_label()}",
        _sep(),
        "1. Atualizar tudo agora (leituras + 0xFE)",
        "Enter/outro: voltar ao menu",
    ]

def linhas_touch(mapping: dict) -> list:
    linhas = ["MelobudsNext - Personalizar Touch", _sep()]
    for i, key in enumerate(keys.KEY_ORDER, start=1):
        fun = mapping.get(key, keys.FUNC_NONE)
        linhas.append(f"{i}. {keys.KEY_NAMES[key]}: {keys.FUNC_NAMES[fun]}")
    linhas += [
        _sep(),
        "9. Desativar touch (tudo Nenhuma)",
        "10. Restaurar mapeamento inicial",
        "Enter/outro: voltar",
    ]
    return linhas

def linhas_funcoes() -> list:
    linhas = ["MelobudsNext - Função do Toque", _sep()]
    for i, fun in enumerate(keys.FUNC_ORDER, start=1):
        linhas.append(f"{i}. {keys.FUNC_NAMES[fun]}")
    return linhas

def linhas_ajustes(state) -> list:
    return [
        "MelobudsNext - Ajustes do Fone",
        _sep(),
        f"1. Equilibrio do canal: {state.balance_label()}",
        _sep(),
        "Enter/outro: voltar",
    ]

def linhas_balance(atual: str) -> list:
    return [
        "MelobudsNext - Equilibrio do Canal",
        _sep(),
        f"Atual: {atual}",
        "0 = todo esquerda | 50 = centro | 100 = todo direita",
        _sep(),
        "1. Todo esquerda",
        "2. Centro (padrao)",
        "3. Todo direita",
        "4. Valor personalizado",
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