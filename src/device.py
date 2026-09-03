# melobudsnext/device.py
"""
Comunicacao BLE com o fone, via bleak.

A conexao usa diretamente o endereco MAC (ja pareado no Windows) em vez
de escanear via BLE - um fone ja pareado e em uso normalmente para de
anunciar (advertise), entao um scan nao o encontraria de forma
confiavel. BleakClient.connect() com o endereco conhecido reaproveita
o pareamento (bond) que o Windows ja tem, sem parear de novo.

IMPORTANTE: os UUIDs de escrita/notificacao (0x1001/0x1002) se repetem
em mais de um servico do fone (ex: 00007033-... e 0000a001-...). Por
isso a busca das characteristics precisa ser escopada ao servico certo
primeiro (client.services.get_service(...).get_characteristic(...)) -
passar so a string do UUID direto pro bleak gera erro de ambiguidade
("Multiple Characteristics with this UUID").
"""

from bleak import BleakClient

from . import commands

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
        # Characteristics resolvidas na conexao (escopadas ao servico certo)
        self._char_write = None
        self._char_notify = None

    async def connect(self) -> None:
        # Conecta direto pelo MAC - usa o pareamento ja existente no
        # Windows, nao inicia um novo pareamento.
        await self.client.connect()

        service = self.client.services.get_service(self.uuid_service)
        if service is None:
            await self.client.disconnect()
            raise ConnectionError(
                f"Servico {self.uuid_service} nao encontrado neste dispositivo. "
                "Confira o UUID de servico configurado."
            )

        self._char_write = service.get_characteristic(self.uuid_write)
        self._char_notify = service.get_characteristic(self.uuid_notify)

        if self._char_write is None or self._char_notify is None:
            await self.client.disconnect()
            raise ConnectionError(
                "Characteristics de escrita/notificacao nao encontradas dentro do servico "
                f"{self.uuid_service}. Confira os UUIDs configurados."
            )

        self._connected = True
        await self.client.start_notify(self._char_notify, self._notification_handler)

    async def disconnect(self) -> None:
        if self._connected:
            await self.client.stop_notify(self._char_notify)
            await self.client.disconnect()
            self._connected = False

    async def send_command(self, packet: bytes) -> None:
        if not self._connected:
            raise ConnectionError("Dispositivo nao conectado.")
        await self.client.write_gatt_char(self._char_write, packet, response=False)

    def _notification_handler(self, sender, data: bytes) -> None:
        parsed = commands.parse_response(data)
        if parsed:
            print(f"  [Fone] {data.hex('-').upper()}  -> cmd={parsed['cmd']} params={parsed['params']}")
        else:
            print(f"  [Fone] {data.hex('-').upper()}  (pacote nao reconhecido - possivel tabela de EQ)")
