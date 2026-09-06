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

# Liga/Desliga o Game Mode
def game_mode(enable: bool) -> bytes:
    val = 0x01 if enable else 0x02
    return Command(opcode=CMD_GAME_MODE, params=[val])

# Altera o modo ANC (Desligado/ANC ON/Transparência)
def anc_mode(mode: int, sub_scene: int = 0x00, noise_value: int = 0x00) -> bytes:
    return Command(opcode=CMD_ANC, params=[mode, sub_scene, noise_value])

# Comandos
CMD_GAME_MODE = 0x09
CMD_ANC = 0x17
ANC_OFF = anc_mode(0x00, 0x00, 0x00)
ANC_ON = anc_mode(0x01, 0x01, 0x00)
ANC_TRANSPARENCY = anc_mode(0x03, 0x02, 0x00)