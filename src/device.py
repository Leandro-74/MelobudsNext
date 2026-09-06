# melobudsnext/device.py

# Estabelece conexão e realiza a comunicação

from bleak import BleakClient
from typing import Optional

from . import commands
from .commands import Command

# Valores confirmados por engenharia reversa (captura no nRF Connect).
# Usados como padrao, mas configuraveis por instancia caso um outro
# fone/firmware use UUIDs diferentes.
DEFAULT_ADDRESS = "C4:AC:60:07:68:09"
DEFAULT_UUID_SERVICE = "0000a001-0000-1000-8000-00805f9b34fb"
DEFAULT_UUID_WRITE = "00001001-0000-1000-8000-00805f9b34fb"
DEFAULT_UUID_NOTIFY = "00001002-0000-1000-8000-00805f9b34fb"


class MelobudsDevice:
    def __init__(
        self,
        address: str,
        uuid_service: str = DEFAULT_UUID_SERVICE,
        uuid_write: str = DEFAULT_UUID_WRITE,
        uuid_notify: str = DEFAULT_UUID_NOTIFY,
    ):
        self.address = address
        self.uuid_service = uuid_service
        self.uuid_write = uuid_write
        self.uuid_notify = uuid_notify

        self.client = BleakClient(address)
        self._connected = False

        self._char_write: Optional[object] = None
        self._char_notify: Optional[object] = None

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        await self.client.connect()

        service = self.client.services.get_service(self.uuid_service)
        if service is None:
            await self.client.disconnect()
            raise ConnectionError(
                f"Serviço {self.uuid_service} não encontrado."
                "Verifique o UUID de serviço configurado."
            )

        self._char_write = service.get_characteristic(self.uuid_write)
        self._char_notify = service.get_characteristic(self.uuid_notify)

        if self._char_write is None or self._char_notify is None:
            await self.client.disconnect()
            raise ConnectionError(
                f"characteristics não encontradas em {self.uuid_service}."
                "Verifique os UUIDs configurados."
            )

        self._connected = True

        await self.client.start_notify(
            self._char_notify,
            self._notification_handler
        )

    async def disconnect(self) -> None:
        if self._connected:
            try:
                await self.client.stop_notify(self._char_notify)
            except Exception:
                pass
            await self.client.disconnect()
            self._connected = False

    async def send_command(self, command: Command) -> None:
        if not self._connected:
            raise ConnectionError("Dispositivo não conectado.")
        
        packet = command.to_bytes()
        await self.client.write_gatt_char(
            self._char_write,
            packet,
            response=False
        )
    
    def _notification_handler(self, sender, data: bytes) -> None:
        parsed_commands = commands.parse_packet(data)

        if not parsed_commands:
            print(f" [Fone] {data.hex('-').upper()} (não reconhecido)")
            return

        for cmd in parsed_commands:
            event_name = commands.get_event_name(cmd.opcode)
            print(f" [Fone] {event_name}: {cmd}")

