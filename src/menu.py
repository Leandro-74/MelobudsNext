# src/menu.py

from typing import Optional
import shutil

from . import keys
from . import state

# Largura interna das caixas e prefixo dos escapes ANSI
LARGURA = 56
ESC = "\x1b"

def _pad_horizontal() -> int:
    try:
        cols = shutil.get_terminal_size().columns
    except Exception:
        cols = LARGURA + 2
    return max(0, (cols - (LARGURA + 2)) // 2)

def _pad_vertical(total_linhas: int) -> int:
    try:
        rows = shutil.get_terminal_size().lines
    except Exception:
        return 0
    return max(0, (rows - total_linhas) // 2)

# Linha de conteudo com bordas e preenchimento a direita
def _linha(texto: str = "") -> str:
    return "║" + (" " + texto).ljust(LARGURA) + "║"

# Bordas horizontais da caixa (topo, separador e base)
def _topo() -> str:
    return "╔" + "═" * LARGURA + "╗"

def _sep() -> str:
    return "╠" + "═" * LARGURA + "╣"

def _fundo() -> str:
    return "╚" + "═" * LARGURA + "╝"

# Conteudo do menu principal (titulo, bateria e opcoes)
def linhas_principal(status: str, nome_fone: Optional[str] = None) -> list:
    return [
        f"MelobudsNext - {nome_fone or 'QCY Melobuds Pro'}",
        status,
        _sep(),
        "1. Alterar modo ANC",
        "2. Consultar estados",
        "3. Renomear fone",
        "4. Personalizar touch",
        "5. Ajustes do fone",
        "6. Sair",
    ]

# Tela de rename com o nome atual
def linhas_rename(nome_atual: str) -> list:
    return [
        "MelobudsNext - Renomear Fone",
        _sep(),
        f"Nome atual: {nome_atual}",
        "",
        "Digite o novo nome e pressione Enter.",
        "Deixe vazio para cancelar.",
    ]

# Tela do toggle de Game Mode
def linhas_game_mode(atual: str) -> list:
    return [
        "MelobudsNext - Modo de Jogo",
        _sep(),
        f"Atual: {atual}",
        _sep(),
        "1. Ativar",
        "2. Desativar",
    ]

# Tela do toggle de Sleep Mode
def linhas_sleep_mode(atual: str) -> list:
    return [
        "MelobudsNext - Modo de Sono",
        _sep(),
        f"Atual: {atual}",
        _sep(),
        "1. Ativar",
        "2. Desativar",
    ]

# Tela do toggle de LDAC
def linhas_ldac(atual: str) -> list:
    return [
        "MelobudsNext - LDAC",
        _sep(),
        f"Atual: {atual}",
        _sep(),
        "1. Ativar",
        "2. Desativar",
    ]

# Tela das cenas de ANC
def linhas_anc(atual: str) -> list:
    return [
        "MelobudsNext - ANC",
        f"Atual: {atual}",
        _sep(),
        "1. Desligado",
        "2. Interior",
        "3. Viagens Diárias",
        "4. Barulho",
        "5. Ruído Contra o Vento",
        "6. Cancelamento Adaptativo",
        "7. Transparência",
    ]

# Tela de intensidade do ANC
def linhas_nivel() -> list:
    return [
        "MelobudsNext - Nível do ANC",
        _sep(),
        "1. Intensidade 1",
        "2. Intensidade 2",
        "3. Intensidade 3",
    ]

# Tela do modo transparencia
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

# Painel de consulta com todos os rotulos do estado
def linhas_estado(state) -> list:
    return [
        "MelobudsNext - Estado do Fone",
        _sep(),
        f"Bateria:         {state.battery_line()}",
        f"ANC:             {state.anc_label()}",
        f"Game Mode:       {state.game_mode_label()}",
        f"Modo de Sono:    {state.sleep_mode_label()}",
        f"LDAC:            {state.ldac_label()}",
        f"Detecção de Uso: {state.wear_label()}",
        f"Equilibrio:      {state.balance_label()}",
        f"Versao:          {state.version or 'desconhecida'}",
        _sep(),
        "1. Atualizar tudo agora (leituras + 0xFE)",
        "   Enter/outro: voltar ao menu",
    ]

# Tabela atual do touch + acoes de desativar/restaurar
def linhas_touch(mapping: dict) -> list:
    linhas = ["MelobudsNext - Personalizar Touch", _sep()]
    for i, key in enumerate(keys.KEY_ORDER, start=1):
        fun = mapping.get(key, keys.FUNC_NONE)
        linhas.append(f"{i}. {keys.KEY_NAMES[key]}: {keys.FUNC_NAMES[fun]}")
    linhas += [
        _sep(),
        "9. Desativar touch (tudo Nenhuma)",
        "10. Restaurar mapeamento inicial",
        "   Enter/outro: voltar",
    ]
    return linhas

# Lista das funcoes atributiveis a uma tecla
def linhas_funcoes() -> list:
    linhas = ["MelobudsNext - Função do Toque", _sep()]
    for i, fun in enumerate(keys.FUNC_ORDER, start=1):
        linhas.append(f"{i}. {keys.FUNC_NAMES[fun]}")
    return linhas

# Submenu dos ajustes com os valores atuais
def linhas_ajustes(state) -> list:
    return [
        "MelobudsNext - Ajustes do Fone",
        _sep(),
        f"1. Equilibrio do canal: {state.balance_label()}",
        "2. Reconfigurar fone (MAC/UUIDs)",
        "3. Volume de Notificação",
        "4. Modo de Jogo",
        "5. Modo de Sono",
        "6. LDAC",
        "7. Detecção de Uso",
        _sep(),
        "Enter/outro: voltar",
    ]

# Tela do toggle de Detecção de Uso
def linhas_wear(state) -> list:
    linhas = [
        "MelobudsNext - Detecção de Uso",
        _sep(),
        f"Atual: {state.wear_label()}",
        _sep(),
        "1. Ligar",
        "2. Desligar",
    ]
    if state.wear:
        linhas.append(f"3. Desligar ANC ao remover: {state.wear_anc_label()}")
    return linhas

# Tela do toggle de Desligar ANC ao Remover o fone
def linhas_wear_anc(atual: str) -> list:
    return [
        "MelobudsNext - Desligar ANC ao Remover",
        _sep(),
        f"Atual: {atual}",
        _sep(),
        "1. Ligar",
        "2. Desligar",
        _sep(),
        "Enter/outro: voltar",
    ]

# Tela do equilibrio do canal
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

# Tela do volume de notificacao
def linhas_tone_vol(atual: str) -> list:
    return [
        "MelobudsNext - Volume de Notificação",
        f"Atual: {atual}",
        _sep(),
        "1. Volume mais baixo",
        "2. Volume médio",
        "3. Volume mais alto",
        "4. Volume máximo",
        _sep(),
        "Enter/outro: voltar",
    ]

# Desenha a caixa completa e devolve o cursor para dentro dela, apos o prompt
def abrir_caixa(linhas: list, prompt: str) -> None:
    pad = _pad_horizontal()
    total = len(linhas) + 4
    print("\n" * _pad_vertical(total), end="")

    def out(s: str) -> None:
        print(" " * pad + s)

    out(_topo())
    for l in linhas:
        out(l if l.startswith("╠") else _linha(l))
    out(_sep())
    texto = " " + prompt
    out("║" + texto + " " * max(1, LARGURA - len(texto)) + "║")
    out(_fundo())
    col = pad + 2 + len(texto)
    print(f"{ESC}[2A{ESC}[{col}G", end="", flush=True)

# Pula a base ja desenhada para o proximo print nao a sobrescrever
def fechar_caixa() -> None:
    print(f"{ESC}[1B", end="", flush=True)

# Versao sincrona da pergunta em caixa (setup inicial)
def perguntar(linhas: list, prompt: str) -> str:
    abrir_caixa(linhas, prompt)
    valor = input()
    fechar_caixa()
    return valor.strip()