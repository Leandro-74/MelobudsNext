# melobudsnext/device.py

# Estabelece conexão e realiza a comunicação

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

    # Inicia conexão
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
                f"{self.uuid_service}. Confira os UUIDs configurados."
            )

        self._connected = True
        await self.client.start_notify(self._char_notify, self._notification_handler)

    # Encerra conexão
    async def disconnect(self) -> None:
        if self._connected:
            await self.client.stop_notify(self._char_notify)
            await self.client.disconnect()
            self._connected = False

    # Envia um report
    async def send_command(self, packet: bytes) -> None:
        if not self._connected:
            raise ConnectionError("Dispositivo nao conectado.")
        await self.client.write_gatt_char(self._char_write, packet, response=False)

    # Recebe notificações do fone
    def _notification_handler(self, sender, data: bytes) -> None:
        parsed = commands.parse_response(data)
        if parsed:
            print(f"  [Fone] {data.hex('-').upper()}  -> cmd={parsed['cmd']} params={parsed['params']}")
        else:
            print(f"  [Fone] {data.hex('-').upper()}  (pacote nao reconhecido - possivel tabela de EQ)")
