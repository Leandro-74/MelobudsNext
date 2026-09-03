# melobudsnext/device.py
"""
Comunicacao BLE com o fone, via bleak.
"""

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

from . import commands

UUID_SERVICE = "0000a001-0000-1000-8000-00805f9b34fb"
UUID_WRITE = "00001001-0000-1000-8000-00805f9b34fb"
UUID_NOTIFY = "00001002-0000-1000-8000-00805f9b34fb"


async def scan_devices(timeout: float = 5.0) -> list[BLEDevice]:
    """Escaneia dispositivos BLE nas proximidades por alguns segundos."""
    return await BleakScanner.discover(timeout=timeout)


class MelobudsDevice:
    def __init__(self, address: str):
        self.address = address
        self.client = BleakClient(address)
        self._connected = False

    async def connect(self) -> None:
        await self.client.connect()
        self._connected = True
        await self.client.start_notify(UUID_NOTIFY, self._notification_handler)

    async def disconnect(self) -> None:
        if self._connected:
            await self.client.stop_notify(UUID_NOTIFY)
            await self.client.disconnect()
            self._connected = False

    async def send_command(self, packet: bytes) -> None:
        if not self._connected:
            raise ConnectionError("Dispositivo nao conectado.")
        await self.client.write_gatt_char(UUID_WRITE, packet, response=False)

    def _notification_handler(self, sender, data: bytes) -> None:
        parsed = commands.parse_response(data)
        if parsed:
            print(f"  [Fone] {data.hex('-').upper()}  -> cmd={parsed['cmd']} params={parsed['params']}")
        else:
            print(f"  [Fone] {data.hex('-').upper()}  (pacote nao reconhecido - possivel tabela de EQ)")
