# Montagem e parsing dos pacotes no protocolo do Melobuds Pro
# HEADER (0xFF) | Length | Cmd | ParamLen | Params...
# Lenght = 2 + len(Params) (Leva em consideração Cmd + ParamLen + Params...)
from dataclasses import dataclass
from typing import List

HEADER = 0xFF

@dataclass
class Command:
    opcode: int
    params: List[int]

    def to_bytes(self) -> bytes:
        param_len = len(self.params)
        body_len = 2 + param_len
        return bytes([HEADER, body_len, self.opcode, param_len, *self.params])

    def __str__(self) -> str:
        params_hex = " ".join(f"{p:02X}" for p in self.params)
        return f"[0x{self.opcode:02X}] params: {params_hex}"
        
# Monta o report no protocolo correto
def pack_packet(command: Command) -> bytes:
    return command.to_bytes()

# Decodifica devolução de reports do fone, devolve None se não bater com o padrão esperado
def parse_packet(data: bytes) -> List[Command]:
    if len(data) < 4 or data[0] != HEADER:
        return []
    
    commands: List[Command] = []
    offset = 2

    while offset < len(data):
        if offset + 2 > len(data):
            break

        cmd_id = data[offset]
        param_len = data[offset+1]
        offset += 2

        if offset + param_len > len(data):
            break

        params = list(data[offset:offset+param_len])
        commands.append(Command(opcode=cmd_id, params=params))
        offset += param_len
    return commands

def request_data(cmd_id: int) -> Command:
    return Command(opcode=CMD_REQUEST_DATA, params=[cmd_id])

# Liga/Desliga o Game Mode
def game_mode(enable: bool) -> bytes:
    val = 0x01 if enable else 0x02
    return Command(opcode=CMD_GAME_MODE, params=[val])

# Desliga o ANC
def anc_off() -> Command:
    return Command(opcode=CMD_ANC, params=[0x00, 0x00, 0x00])

# Liga anc conforme cena selecionada
def anc_cena(cena: int, nivel: int = 1) -> Command:
    noise = (nivel-1) if cena in CENAS_COM_NIVEL else 0x00
    return Command(opcode=CMD_ANC, params=[0x01, cena, noise])

# Liga transparência conforme nível selecionado
def transparencia(nivel: int) -> Command:
    return Command(opcode=CMD_ANC, params=[0x03, SUB_TRANSPARENCIA, nivel])

def aprimoramento_vocal() -> Command:
    return Command(opcode=CMD_ANC, params=[0x03, SUB_TRANSPARENCIA, 0x00])

def rename_device(novo_nome: str) -> Command:
    return Command(opcode=CMD_RENAME, params=list(novo_nome.encode("utf-8")))

def sound_balance(valor: int) -> Command:
    valor = max(0, min(100, valor))
    return Command(opcode=CMD_SOUND_BALANCE, params=[valor])

# Comandos
CMD_GAME_MODE = 0x09
CMD_ANC = 0x17
CMD_REQUEST_DATA = 0xFE
CMD_BATTERY = 0x2F
CMD_VERSION = 0x30
CMD_RENAME = 0x18
CMD_SOUND_BALANCE = 0x16

# Cenas ANC (mode = 0x01)
CENA_INTERIOR = 0x01
CENA_VIAGENS = 0x02
CENA_BARULHO = 0x03
CENA_VENTO = 0x04
CENA_ADAPTATIVO = 0x05
CENAS_COM_NIVEL = (CENA_INTERIOR, CENA_BARULHO, CENA_VIAGENS)

# Transparencia (mode = 0x03)
SUB_TRANSPARENCIA = 0x01

EVENT_NAMES = {
    CMD_GAME_MODE: "Game Mode",
    CMD_ANC: "Modo ANC",
    CMD_BATTERY: "Bateria",
    CMD_VERSION: "Versao",
    CMD_REQUEST_DATA: "Consulta",
    CMD_RENAME: "Renomear",
    CMD_SOUND_BALANCE: "Equilibrio",
    0x28: "ANC Wear/Result",
}

def get_event_name(opcode: int) -> str:
    return EVENT_NAMES.get(opcode, f"Desconhecido (0x{opcode:02X})")