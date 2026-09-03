# src/device.py
import asyncio
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
from . import commands

# UUIDs extraidos
UUID_SERVICE = "0000a001-0000-1000-8000-00805f9b34fb"
UUID_WRITE = "00001001-0000-1000-8000-00805f9b34fb"
UUID_NOTIFY = "00001002-0000-1000-8000-00805f9b34fb"

class MelobudsDevice:
    def __init__(self, address: str):
        self.address = address
        self.client = BleakClient(address)
        self._connected = False

    # Faz a conexão com o fone
    async def connect(self):
        await self.client.connect()
        self._connected = True
        # Assina as notificacoes para ouvir o fone
        await self.client.start_notify(UUID_NOTIFY, self._notification_handler)

    # Encerra a conexão
    async def disconnect(self):
        if self._connected:
            await self.client.stop_notify(UUID_NOTIFY)
            await self.client.disconnect()
            self._connected = False

    # Envia um report
    async def send_command(self, packet: bytes):
        if not self._connected:
            raise ConnectionError("Dispositivo nao conectado.")
        await self.client.write_gatt_char(UUID_WRITE, packet, response=False)

    # TESTE: printa uma notificação do fone, será feito parse para bateria/status
    def _notification_handler(self, sender, data):
        print(f"  [Resposta Fone] {data.hex('-').upper()}")

    @property
    def is_connected(self) -> bool:
        return self.client.is_connected

    async def connect(self):
        try:
            await self.client.connect()
            self._connected = True
            await self.client.start_notify(UUID_NOTIFY, self._notification_handler)
        except BleakError as e:
            self._connected = False
            raise ConnectionError(f"Falha BLE: {e}") from e

    async def disconnect(self):
        if self._connected:
            try:
                await self.client.stop_notify(UUID_NOTIFY)
                await self.client.disconnect()
            except Exception:
                pass # Ignora erros ao desconectar
            self._connected = False