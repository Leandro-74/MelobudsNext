# src/state.py

from dataclasses import dataclass, field
from typing import Optional, Tuple

from . import commands
from .commands import Command

@dataclass
class BatteryInfo:
    level: Optional[int] = None
    charging: bool = False

    def display(self) -> str:
        if self.level is None or self.level == 0:
            return "-/-"
        return f"{self.level}%+" if self.charging else f"{self.level}%"

@dataclass
class DeviceState:
    left: BatteryInfo = field(default_factory=BatteryInfo)
    right: BatteryInfo = field(default_factory=BatteryInfo)
    case: BatteryInfo = field(default_factory=BatteryInfo)
    anc: Optional[Tuple[int, int, int]] = None
    game_mode: Optional[bool] = None
    sleep_mode: Optional[bool] = None
    version: Optional[str] = None
    nome: Optional[str] = None
    touch: Optional[dict] = None
    touch_inicial: Optional[dict] = None
    balance: Optional[int] = None
    tone_volume: Optional[int] = None

    def battery_line(self) -> str:
        return f"L: {self.left.display()} | R: {self.right.display()}"

    def anc_label(self) -> str:
        if self.anc is None:
            return "desconhecido"
        mode, sub, noise = self.anc
        if mode == 0x00 or (mode, sub, noise) == (0x02, 0x00, 0x00):
            return "Desligado"
        if mode == 0x01:
            nomes = {
                commands.CENA_INTERIOR: "Interior",
                commands.CENA_VIAGENS: "Viagens Diarias",
                commands.CENA_BARULHO: "Barulho",
                commands.CENA_VENTO: "Contra o vento",
                commands.CENA_ADAPTATIVO: "Adaptativo",
            }
            nome = nomes.get(sub, f"cena 0x{sub:02X}")
            if sub in (commands.CENA_VENTO, commands.CENA_ADAPTATIVO):
                return nome
            return f"{nome} (nivel {noise + 1})"
        if mode == 0x03:
            if noise == 0x00:
                return "Transparencia (aprimoramento vocal)"
            return f"Transparencia (intensidade {noise})"
        return f"desconhecido (0x{mode:02X}, 0x{sub:02X}, 0x{noise:02X})"

    def game_mode_label(self) -> str:
        if self.game_mode is None:
            return "desconhecido"
        return "ativado" if self.game_mode else "desativado"
    
    def sleep_mode_label(self) -> str:
        if self.sleep_mode is None:
            return "desconhecido"
        return "ativado" if self.sleep_mode else "desativado"

    def balance_label(self) -> str:
        if self.balance is None:
            return "desconhecido"
        v = self.balance
        if v == 50:
            return "centro (50)"
        lado = "esquerda" if v < 50 else "direita"
        return f"inclinado p/ {lado} ({v})"

    def tone_volume_label(self) -> str:
        if self.tone_volume is None:
            return "desconhecido"
        return commands.tone_label(self.tone_volume)

    def aplicar(self, cmd: Command) -> None:
        if cmd.opcode == commands.CMD_ANC and len(cmd.params) >= 3:
            self.anc = (cmd.params[0], cmd.params[1], cmd.params[2])
        elif cmd.opcode == commands.CMD_GAME_MODE and len(cmd.params) >= 1:
            self.game_mode = (cmd.params[0] == 0x01)
        elif cmd.opcode == commands.CMD_SLEEP_MODE and len(cmd.params) >= 1:
            self.sleep_mode = (cmd.params[0] == 0x01)
        elif cmd.opcode == commands.CMD_RENAME:
            raw = bytes(cmd.params).rstrip(b"\x00")
            if raw:
                self.nome = raw.decode("utf-8", errors="replace")
        elif cmd.opcode == commands.CMD_SOUND_BALANCE and cmd.params:
            self.balance = cmd.params[0]
        elif cmd.opcode == commands.CMD_TONE_VOLUME and cmd.params:
            self.tone_volume = cmd.params[0]

    def aplicar_bateria(self, dados: bytes) -> None:
        if len(dados) >= 2:
            self.left = _parse_battery_byte(dados[0])
            self.right = _parse_battery_byte(dados[1])
        if len(dados) >= 3:
            self.case = _parse_battery_byte(dados[2])

    def aplicar_versao(self, dados: bytes) -> None:
        if len(dados) >= 3:
            self.version = ".".join(str(b) for b in dados[:3])

def _parse_battery_byte(b: int) -> BatteryInfo:
    return BatteryInfo(level=b & 0x7F, charging=(b & 0x80) != 0)