# src/commands.py

from dataclasses import dataclass
from typing import List

HEADER = 0xFF

@dataclass
# Um comando do protocolo: opcode + lista de parametros
class Command:
    opcode: int
    params: List[int]

    	
    # Serializa no framing FF
    def to_bytes(self) -> bytes:
        param_len = len(self.params)
        body_len = 2 + param_len
        return bytes([HEADER, body_len, self.opcode, param_len, *self.params])

    # Representacao legivel para logs ([0x17] params: 01 03 02)
    def __str__(self) -> str:
        params_hex = " ".join(f"{p:02X}" for p in self.params)
        return f"[0x{self.opcode:02X}] params: {params_hex}"

# Atalho de serializacao de um Command
def pack_packet(command: Command) -> bytes:
    return command.to_bytes()

# Decodifica uma notificacao em um ou mais Command (suporta pacotes compostos)
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

# Consulta de estado: 0xFE + opcode alvo
def request_data(cmd_id: int) -> Command:
    return Command(opcode=CMD_REQUEST_DATA, params=[cmd_id])

# Game Mode on/off (0x09)
def game_mode(enable: bool) -> Command:
    val = 0x01 if enable else 0x02
    return Command(opcode=CMD_GAME_MODE, params=[val])

# Sleep Mode on/off (0x10)
def sleep_mode(enable: bool) -> Command:
    val = 0x01 if enable else 0x02
    return Command(opcode=CMD_SLEEP_MODE, params=[val])

# LDAC on/off (0x23)
def ldac(enable: bool) -> Command:
    val = 0x01 if enable else 0x02
    return Command(opcode=CMD_LDAC, params=[val])

# Desliga o ANC (0x17 00 00 00)
def anc_off() -> Command:
    return Command(opcode=CMD_ANC, params=[0x00, 0x00, 0x00])

# Liga o ANC numa cena com nivel 1-3 (mode 0x01)
def anc_cena(cena: int, nivel: int = 1) -> Command:
    noise = (nivel-1) if cena in CENAS_COM_NIVEL else 0x00
    return Command(opcode=CMD_ANC, params=[0x01, cena, noise])

# Transparencia com intensidade 1-6 (mode 0x03)
def transparencia(nivel: int) -> Command:
    return Command(opcode=CMD_ANC, params=[0x03, SUB_TRANSPARENCIA, nivel])

# Transparencia com aprimoramento vocal (noise 0x00)
def aprimoramento_vocal() -> Command:
    return Command(opcode=CMD_ANC, params=[0x03, SUB_TRANSPARENCIA, 0x00])

# Renomeia o fone: params = nome em UTF-8 (0x18)
def rename_device(novo_nome: str) -> Command:
    return Command(opcode=CMD_RENAME, params=list(novo_nome.encode("utf-8")))

# Equilibrio do canal 0-100, sendo 50 o centro (0x16)
def sound_balance(valor: int) -> Command:
    valor = max(0, min(100, valor))
    return Command(opcode=CMD_SOUND_BALANCE, params=[valor])

# Deteccao de uso (0x2C): formato espelho do report, validado em testes
def wearing_detection(enable: bool, anc_enable: bool,
                      music_index: int = 0x01, tone: int = 0x00) -> Command:
    return Command(
        opcode=CMD_WEARING,
        params=[0x01 if enable else 0x00, music_index,
                0x01 if anc_enable else 0x00, tone],
    )

# Byte real de cada categoria, mapeado com o app como oraculo
TONE_BYTES = {1: 0x04, 2: 0x06, 3: 0x08, 4: 0x0A}
TONE_NAMES = {
    1: "Volume mais baixo",
    2: "Volume medio",
    3: "Volume mais alto",
    4: "Volume maximo",
}

# Categoria 1-4 do volume de notificacao -> byte real (0x1D)
def tone_volume(categoria: int) -> Command:
    if categoria not in TONE_BYTES:
        raise ValueError(f"categoria invalida: {categoria}")
    valor = TONE_BYTES[categoria]
    return Command(opcode=CMD_TONE_VOLUME, params=[valor, valor])

# Traduz o byte cru de volume para o nome da categoria
def tone_label(valor: int) -> str:
    for categoria, byte in TONE_BYTES.items():
        if byte == valor:
            return f"{categoria}. {TONE_NAMES[categoria]}"
    return f"desconhecido ({valor})"

# Opcodes validados por engenharia reversa
CMD_GAME_MODE = 0x09
CMD_SLEEP_MODE = 0x10
CMD_ANC = 0x17
CMD_REQUEST_DATA = 0xFE
CMD_BATTERY = 0x2F
CMD_VERSION = 0x30
CMD_RENAME = 0x18
CMD_SOUND_BALANCE = 0x16
CMD_TONE_VOLUME = 0x1D
CMD_LDAC = 0x23
CMD_WEARING = 0x2C

CENA_INTERIOR = 0x01
CENA_VIAGENS = 0x02
CENA_BARULHO = 0x03
CENA_VENTO = 0x04
CENA_ADAPTATIVO = 0x05
CENAS_COM_NIVEL = (CENA_INTERIOR, CENA_BARULHO, CENA_VIAGENS)

SUB_TRANSPARENCIA = 0x01

# Nomes amigaveis dos opcodes para os logs
EVENT_NAMES = {
    CMD_GAME_MODE: "Modo de Jogo",
    CMD_ANC: "Modo ANC",
    CMD_BATTERY: "Bateria",
    CMD_VERSION: "Versão",
    CMD_REQUEST_DATA: "Consulta",
    CMD_RENAME: "Renomear",
    CMD_SOUND_BALANCE: "Equilíbrio",
    CMD_TONE_VOLUME: "Volume de Notificação",
    CMD_SLEEP_MODE: "Modo de Sono",
    CMD_LDAC: "LDAC",
    CMD_WEARING: "Detecção de Uso",
    0x28: "ANC Wear/Result",
}

# Nome do opcode para logs, com fallback em hex
def get_event_name(opcode: int) -> str:
    return EVENT_NAMES.get(opcode, f"Desconhecido (0x{opcode:02X})")