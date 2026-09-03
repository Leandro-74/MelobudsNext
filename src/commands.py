# Montagem e parsing dos pacotes no protocolo do Melobuds Pro
# HEADER (0xFF) | Length | Cmd | ParamLen | Params...
# Lenght = 2 + len(Params) (Leva em consideração Cmd + ParamLen + Params...)

HEADER = 0xFF

# Monta o report no protocolo correto
def build_packet(cmd: int, params: list[int]) -> bytes:
    param_len = len(params)
    length = 2 + param_len
    return bytes([HEADER, length, cmd, param_len, *params])

# Decodifica devolução de reports do fone, devolve None se não bater com o padrão esperado
def parse_response(data: bytes) -> dict | None:
    if len(data) < 4 or data[0] != HEADER:
        return None
    length = data[1]
    cmd = data[2]
    param_len = data[3]
    params = list(data[4:4 + param_len])
    return {"cmd": f"0x{cmd:02X}", "length": length, "param_len": param_len, "params": params}

# Comandos
CMD_GAME_MODE = 0x09
CMD_ANC = 0x17
ANC_OFF = anc_mode(0x00, 0x00, 0x00)
ANC_ON = anc_mode(0x01, 0x01, 0x00)
ANC_TRANSPARENCY = anc_mode(0x03, 0x02, 0x00)

# Liga/Desliga o Game Mode
def game_mode(enable: bool) -> bytes:
    val = 0x01 if enable else 0x02
    return build_packet(CMD_GAME_MODE, [val])

# Altera o modo ANC (Desligado/ANC ON/Transparência)
def anc_mode(mode: int, sub_scene: int = 0x00, noise_value: int = 0x00) -> bytes:
    return build_packet(CMD_ANC, [mode, sub_scene, noise_value])

# Comandos observados no log do nRF Connect, mas NAO confirmados ainda
# (significado inferido pelo contexto - precisam ser testados um a um,
# ativando cada funcao no app oficial enquanto o nRF Connect grava)
CMD_BATTERY = 0x16        # hipotese: nivel de bateria (valor 0x32 = 50 = 50%?)
CMD_FIRMWARE_VERSION = 0x19  # hipotese: string ASCII de versao (ex: "WQ00")
CMD_EQ_TABLE = 0x22        # hipotese: tabela de equalizacao (pacote grande, ~145 bytes)
CMD_UNKNOWN_10 = 0x10
CMD_UNKNOWN_14 = 0x14
CMD_UNKNOWN_1D = 0x1D
CMD_UNKNOWN_1F = 0x1F
CMD_UNKNOWN_2C = 0x2C
