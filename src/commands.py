# src/commands.py

# Padrão de reports: FF | Len | Cmd | ParamLen | Params
HEADER = 0xFF

# Monta o report no padrão correto
def build_packet(cmd: int, params: list[int]) -> bytes:
    param_len = len(params)
    length = 2 + param_len 
    return bytes([HEADER, length, cmd, param_len, *params])

# Comandos conhecidos
CMD_GAME_MODE = 0x09
CMD_ANC = 0x17

# Função para ligar/desligar Game Mode
def game_mode(enable: bool) -> bytes:
    val = 0x01 if enable else 0x02
    return bytes([0xFF, 0x03, CMD_GAME_MODE, 0x01, val])

# Função para alterar modo ANC
def anc_mode(mode: int) -> bytes:
    return build_packet(CMD_ANC, [0x03, mode, 0x00, 0x00])