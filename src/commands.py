# melobudsnext/commands.py
"""
Montagem e parsing de pacotes no protocolo do QCY Melobuds Pro.

Formato observado (via Wireshark/nRF Connect):
  HEADER (0xFF) | Length | Cmd | ParamLen | Params...

  Length = 2 + len(Params)  (conta Cmd + ParamLen + os proprios params)
"""

HEADER = 0xFF


def build_packet(cmd: int, params: list[int]) -> bytes:
    """Monta um pacote no formato FF | Len | Cmd | ParamLen | Params."""
    param_len = len(params)
    length = 2 + param_len
    return bytes([HEADER, length, cmd, param_len, *params])


def parse_response(data: bytes) -> dict | None:
    """
    Decodifica uma notificacao recebida do fone no mesmo formato.
    Devolve None se os bytes nao baterem com o padrao esperado
    (ex: o pacote grande de EQ, que parece ter uma estrutura diferente).
    """
    if len(data) < 4 or data[0] != HEADER:
        return None
    length = data[1]
    cmd = data[2]
    param_len = data[3]
    params = list(data[4:4 + param_len])
    return {"cmd": f"0x{cmd:02X}", "length": length, "param_len": param_len, "params": params}


# ---------------------------------------------------------------------
# Comandos CONFIRMADOS (testados de verdade em teste.py, o fone respondeu)
# ---------------------------------------------------------------------

CMD_GAME_MODE = 0x09
CMD_ANC = 0x17


def game_mode(enable: bool) -> bytes:
    """Liga (True) ou desliga (False) o Game Mode."""
    val = 0x01 if enable else 0x02
    return build_packet(CMD_GAME_MODE, [val])


def anc_mode(mode: int, sub_scene: int = 0x00, noise_value: int = 0x00) -> bytes:
    """
    mode: 0x00=Off, 0x01=ANC, 0x02=ANC Ambiente, 0x03=Transparencia
    sub_scene/noise_value: variam por mode nos testes ja feitos, ainda
    nao sabemos a regra exata - por enquanto use os atalhos abaixo,
    que sao os valores confirmados em teste.py.
    """
    return build_packet(CMD_ANC, [mode, sub_scene, noise_value])


# Atalhos com os parametros exatos que ja foram testados e confirmados
ANC_OFF = anc_mode(0x00, 0x00, 0x00)
ANC_ON = anc_mode(0x01, 0x01, 0x00)
ANC_TRANSPARENCY = anc_mode(0x03, 0x02, 0x00)


# ---------------------------------------------------------------------
# Comandos observados no log do nRF Connect, mas NAO confirmados ainda
# (significado inferido pelo contexto - precisam ser testados um a um,
# ativando cada funcao no app oficial enquanto o nRF Connect grava)
# ---------------------------------------------------------------------

CMD_BATTERY = 0x16        # hipotese: nivel de bateria (valor 0x32 = 50 = 50%?)
CMD_FIRMWARE_VERSION = 0x19  # hipotese: string ASCII de versao (ex: "WQ00")
CMD_EQ_TABLE = 0x22        # hipotese: tabela de equalizacao (pacote grande, ~145 bytes)
CMD_UNKNOWN_10 = 0x10
CMD_UNKNOWN_14 = 0x14
CMD_UNKNOWN_1D = 0x1D
CMD_UNKNOWN_1F = 0x1F
CMD_UNKNOWN_2C = 0x2C
