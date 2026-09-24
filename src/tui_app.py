# src/tui_app.py

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, List, Optional, Tuple

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option
from textual.binding import Binding

from . import commands
from . import config
from . import device
from . import keys
from . import console
from .device import MelobudsDevice

Callback = Callable[[], Awaitable[None]]

PRIMARY = "#8835e9"
DIM = "#521994"

BASE_CSS = f"""
Screen {{
    background: #0a0a0a;
    color: #e6e6e6;
}}

.painel {{
    border: round {PRIMARY};
    border-title-color: {PRIMARY};
    border-title-style: bold;
    padding: 0 1;
    background: #0a0a0a;
}}

#status {{
    height: auto;
    margin-bottom: 1;
}}

#status .linha {{
    color: #e6e6e6;
}}

#status .rotulo {{
    color: {DIM};
}}

OptionList {{
    background: #0a0a0a;
    border: none;
    scrollbar-size: 1 1;
}}

OptionList > .option-list--option {{
    color: #e6e6e6;
}}

OptionList > .option-list--option-highlighted {{
    background: {PRIMARY} 25%;
    color: {PRIMARY};
    text-style: bold;
}}

#barra {{
    height: 1;
    dock: bottom;
    background: #0a0a0a;
    color: {DIM};
    padding: 0 1;
}}

#barra .tecla {{
    color: {PRIMARY};
    text-style: bold;
}}

Input {{
    border: round {PRIMARY};
    background: #0a0a0a;
}}
"""


def _formatar_barra(dicas: List[Tuple[str, str]]) -> str:
    partes = []
    for tecla, label in dicas:
        partes.append(f"[b]{tecla}[/b] {label}")
    return "   ".join(partes) + "   [b]esc[/b] Voltar"

class MenuScreen(Screen):
    BINDINGS = [
        Binding("escape", "voltar", "Voltar", show=False),
        Binding("j", "cursor_down", "Baixo", show=False),
        Binding("k", "cursor_up", "Cima", show=False),
    ]
    CSS = BASE_CSS

    def __init__(
        self,
        titulo_painel: str,
        status_lines: List[str],
        options: List[Tuple[str, Callback]],
    ) -> None:
        super().__init__()
        self._titulo_painel = titulo_painel
        self._status_lines = status_lines
        self._options = options

    def compose(self) -> ComposeResult:
        with Vertical():
            if self._status_lines:
                with Vertical(id="status", classes="painel") as painel:
                    painel.border_title = "Estado"
                    for linha in self._status_lines:
                        yield Static(linha, classes="linha")
            with Vertical(classes="painel") as menu_painel:
                menu_painel.border_title = self._titulo_painel
                yield OptionList(
                    *[Option(f" {i + 1}. {label}", id=str(i)) for i, (label, _cb) in enumerate(self._options)]
                )
            yield Static(
                _formatar_barra([("j,k / ↑↓", "Navegar"), ("enter", "Selecionar")]),
                id="barra",
            )

    def on_mount(self) -> None:
        self.query_one(OptionList).focus()

    async def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        idx = int(event.option.id)
        _label, callback = self._options[idx]
        await callback()

    def action_cursor_down(self) -> None:
        self.query_one(OptionList).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one(OptionList).action_cursor_up()

    def action_voltar(self) -> None:
        self.app.pop_screen()


class FormScreen(Screen):
    BINDINGS = [Binding("escape", "voltar", "Cancelar", show=False)]
    CSS = BASE_CSS

    def __init__(
        self,
        titulo_painel: str,
        placeholder: str,
        on_submit: Callable[[str], Awaitable[None]],
        initial_value: str = "",
    ) -> None:
        super().__init__()
        self._titulo_painel = titulo_painel
        self._placeholder = placeholder
        self._on_submit = on_submit
        self._initial_value = initial_value

    def compose(self) -> ComposeResult:
        with Vertical():
            with Vertical(classes="painel") as painel:
                painel.border_title = self._titulo_painel
                yield Input(placeholder=self._placeholder, value=self._initial_value)
            yield Static(_formatar_barra([("enter", "Confirmar")]), id="barra")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        valor = event.value.strip()
        self.app.pop_screen()
        if valor:
            await self._on_submit(valor)

    def action_voltar(self) -> None:
        self.app.pop_screen()

class MelobudsTUI(App):
    console.ajustar_janela()
    TITLE = "MelobudsNext"
    CSS = BASE_CSS

    def __init__(self) -> None:
        super().__init__()
        self.dev: Optional[MelobudsDevice] = None

    async def on_mount(self) -> None:
        cfg = config.load_config()
        if cfg is None or "address" not in cfg:
            self.exit(message="Nenhum fone configurado ainda. Rode o CLI (main.py) uma vez para parear.")
            return
        self.dev = MelobudsDevice(
            address=cfg["address"],
            uuid_service=cfg.get("uuid_service", device.DEFAULT_UUID_SERVICE),
            uuid_write=cfg.get("uuid_write", device.DEFAULT_UUID_WRITE),
            uuid_notify=cfg.get("uuid_notify", device.DEFAULT_UUID_NOTIFY),
        )
        try:
            await self.dev.connect()
        except Exception as e:
            self.exit(message=f"Falha ao conectar: {e}")
            return
        await self.push_screen(self._menu_principal())

    async def on_unmount(self) -> None:
        if self.dev and self.dev.connected:
            await self.dev.disconnect()

    def _menu_principal(self) -> MenuScreen:
        dev = self.dev
        assert dev is not None
        return MenuScreen(
            f"{dev.state.nome or 'QCY Melobuds Pro'}",
            [dev.state.battery_line()],
            [
                ("Alterar modo ANC", self._abrir_anc),
                ("Consultar estados", self._abrir_estado),
                ("Renomear fone", self._abrir_renomear),
                ("Personalizar touch", self._abrir_touch),
                ("Ajustes do fone", self._abrir_ajustes),
                ("Sair", self._sair),
            ],
        )

    async def _voltar_ao_menu(self) -> None:
        self.pop_screen()
        await self.push_screen(self._menu_principal())

    def _resetar_para_menu_principal(self) -> None:
        while len(self.screen_stack) > 2:
            self.pop_screen()
        self.switch_screen(self._menu_principal())

    async def _sair(self) -> None:
        self.exit()

    async def _abrir_anc(self) -> None:
        dev = self.dev
        assert dev is not None

        async def desligar() -> None:
            await dev.send_command(commands.anc_off())
            await dev.sync_state()
            await self._voltar_ao_menu()

        async def cena(cena_id: int, nome_cena: str) -> None:
            async def escolher_nivel(nivel: int) -> None:
                comando = commands.anc_cena(cena_id, nivel)
                await dev.send_command(comando)
                await dev.sync_state()
                await self._voltar_ao_menu()

            await self.push_screen(
                MenuScreen(
                    f"{nome_cena} — nível",
                    [],
                    [(f"Intensidade {n}", (lambda n=n: escolher_nivel(n))) for n in (1, 2, 3)],
                )
            )

        async def cena_sem_nivel(cena_id: int) -> None:
            await dev.send_command(commands.anc_cena(cena_id))
            await dev.sync_state()
            await self._voltar_ao_menu()

        async def transparencia() -> None:
            async def vocal() -> None:
                await dev.send_command(commands.aprimoramento_vocal())
                await dev.sync_state()
                await self._voltar_ao_menu()

            async def nivel(n: int) -> None:
                await dev.send_command(commands.transparencia(n))
                await dev.sync_state()
                await self._voltar_ao_menu()

            opts = [("Aprimoramento vocal", vocal)]
            opts += [(f"Intensidade {n}", (lambda n=n: nivel(n))) for n in range(1, 7)]
            await self.push_screen(MenuScreen("Transparência", [], opts))

        await self.push_screen(
            MenuScreen(
                "ANC",
                [f"Atual: {dev.state.anc_label()}"],
                [
                    ("Desligado", desligar),
                    ("Interior", lambda: cena(commands.CENA_INTERIOR, "Interior")),
                    ("Viagens Diárias", lambda: cena(commands.CENA_VIAGENS, "Viagens Diárias")),
                    ("Barulho", lambda: cena(commands.CENA_BARULHO, "Barulho")),
                    ("Ruído Contra o Vento", lambda: cena_sem_nivel(commands.CENA_VENTO)),
                    ("Cancelamento Adaptativo", lambda: cena_sem_nivel(commands.CENA_ADAPTATIVO)),
                    ("Transparência", transparencia),
                ],
            )
        )

    async def _abrir_estado(self) -> None:
        dev = self.dev
        assert dev is not None

        async def atualizar() -> None:
            await dev.sync_state()
            self.pop_screen()
            await self._abrir_estado()

        s = dev.state
        linhas = [
            f"Bateria:         {s.battery_line()}",
            f"ANC:             {s.anc_label()}",
            f"Game Mode:       {s.game_mode_label()}",
            f"Modo de Sono:    {s.sleep_mode_label()}",
            f"LDAC:            {s.ldac_label()}",
            f"Detecção de Uso: {s.wear_label()}",
            f"Equilíbrio:      {s.balance_label()}",
            f"Versão:          {s.version or 'desconhecida'}",
        ]
        await self.push_screen(
            MenuScreen("Estado do Fone", linhas, [("Atualizar tudo agora", atualizar)])
        )

    async def _abrir_renomear(self) -> None:
        dev = self.dev
        assert dev is not None

        async def salvar(novo: str) -> None:
            if len(novo.encode("utf-8")) > 30:
                return
            comando = commands.rename_device(novo)
            await dev.send_command(comando)
            dev.state.aplicar(comando)
            await self._voltar_ao_menu()

        await self.push_screen(
            FormScreen(
                f"Renomear (atual: {dev.state.nome or 'desconhecido'})",
                "Novo nome...",
                salvar,
            )
        )

    async def _abrir_touch(self) -> None:
        dev = self.dev
        assert dev is not None

        async def escolher_funcao(key: int) -> None:
            async def aplicar(func: int) -> None:
                mapping = dict(dev.state.touch or {})
                mapping[key] = func
                await dev.gravar_touch(mapping)
                dev.state.touch = dict(mapping)
                self.pop_screen()
                self.pop_screen()
                await self._abrir_touch()

            opts = [(keys.FUNC_NAMES[f], (lambda f=f: aplicar(f))) for f in keys.FUNC_ORDER]
            await self.push_screen(MenuScreen(f"Função — {keys.KEY_NAMES[key]}", [], opts))

        async def desativar_tudo() -> None:
            vazio = {k: keys.FUNC_NONE for k in keys.KEY_ORDER}
            await dev.gravar_touch(vazio)
            dev.state.touch = dict(vazio)
            self.pop_screen()
            await self._abrir_touch()

        async def restaurar() -> None:
            if dev.state.touch_inicial:
                await dev.gravar_touch(dev.state.touch_inicial)
                dev.state.touch = dict(dev.state.touch_inicial)
            self.pop_screen()
            await self._abrir_touch()

        mapping = dict(dev.state.touch or {})
        opts = [
            (
                f"{keys.KEY_NAMES[key]}: {keys.FUNC_NAMES[mapping.get(key, keys.FUNC_NONE)]}",
                (lambda key=key: escolher_funcao(key)),
            )
            for key in keys.KEY_ORDER
        ]
        opts.append(("Desativar touch (tudo Nenhuma)", desativar_tudo))
        if dev.state.touch_inicial:
            opts.append(("Restaurar mapeamento inicial", restaurar))

        await self.push_screen(MenuScreen("Personalizar Touch", [], opts))

    async def _abrir_ajustes(self) -> None:
        dev = self.dev
        assert dev is not None

        async def game_mode(ligar: bool) -> None:
            comando = commands.game_mode(ligar)
            await dev.send_command(comando)
            dev.state.aplicar(comando)
            await self._voltar_ao_menu()

        async def sleep_mode(ligar: bool) -> None:
            comando = commands.sleep_mode(ligar)
            await dev.send_command(comando)
            dev.state.aplicar(comando)
            await self._voltar_ao_menu()

        async def ldac(ligar: bool) -> None:
            await dev.send_command(commands.ldac(ligar))
            await dev.reconectar()
            await self._voltar_ao_menu()

        async def balance(valor: int) -> None:
            comando = commands.sound_balance(valor)
            await dev.send_command(comando)
            dev.state.aplicar(comando)
            await self._voltar_ao_menu()

        async def abrir_game_mode() -> None:
            await self.push_screen(
                MenuScreen(
                    "Modo de Jogo",
                    [f"Atual: {dev.state.game_mode_label()}"],
                    [("Ativar", lambda: game_mode(True)), ("Desativar", lambda: game_mode(False))],
                )
            )

        async def abrir_sleep_mode() -> None:
            await self.push_screen(
                MenuScreen(
                    "Modo de Sono",
                    [f"Atual: {dev.state.sleep_mode_label()}"],
                    [("Ativar", lambda: sleep_mode(True)), ("Desativar", lambda: sleep_mode(False))],
                )
            )

        async def abrir_ldac() -> None:
            await self.push_screen(
                MenuScreen(
                    "LDAC",
                    [f"Atual: {dev.state.ldac_label()}", "Obs: o fone reinicia para aplicar"],
                    [("Ativar", lambda: ldac(True)), ("Desativar", lambda: ldac(False))],
                )
            )

        async def balance_personalizado(texto: str) -> None:
            if not texto.isdigit() or not 0 <= int(texto) <= 100:
                return
            await balance(int(texto))

        async def abrir_balance_personalizado() -> None:
            await self.push_screen(
                FormScreen(
                    "Valor personalizado (0-100)",
                    "0 = esquerda, 50 = centro, 100 = direita...",
                    balance_personalizado,
                )
            )

        async def abrir_balance() -> None:
            await self.push_screen(
                MenuScreen(
                    "Equilíbrio do Canal",
                    [f"Atual: {dev.state.balance_label()}"],
                    [
                        ("Todo esquerda", lambda: balance(0)),
                        ("Centro (padrão)", lambda: balance(50)),
                        ("Todo direita", lambda: balance(100)),
                        ("Valor personalizado", abrir_balance_personalizado),
                    ],
                )
            )

        async def abrir_tone_volume() -> None:
            async def escolher(categoria: int) -> None:
                comando = commands.tone_volume(categoria)
                await dev.send_command(comando)
                dev.state.aplicar(comando)
                await asyncio.sleep(0.5)
                await dev.send_command(commands.request_data(commands.CMD_TONE_VOLUME))
                await asyncio.sleep(0.7)
                await self._voltar_ao_menu()

            await self.push_screen(
                MenuScreen(
                    "Volume de Notificação",
                    [f"Atual: {dev.state.tone_volume_label()}"],
                    [
                        ("Volume mais baixo", lambda: escolher(1)),
                        ("Volume médio", lambda: escolher(2)),
                        ("Volume mais alto", lambda: escolher(3)),
                        ("Volume máximo", lambda: escolher(4)),
                    ],
                )
            )

        async def enviar_wear(enable: bool, anc: bool) -> None:
            raw = dev.state.wear_raw or (0x00, 0x01, 0x00, 0x00)
            comando = commands.wearing_detection(enable, anc, music_index=raw[1], tone=raw[3])
            await dev.send_command(comando)
            dev.state.aplicar(comando)
            await asyncio.sleep(0.5)
            await dev.send_command(commands.request_data(commands.CMD_WEARING))
            await asyncio.sleep(0.8)

        async def abrir_wear() -> None:
            async def ligar(estado: bool) -> None:
                await enviar_wear(enable=estado, anc=(dev.state.wear_anc or False))
                self.pop_screen()
                await abrir_wear()

            async def abrir_wear_anc() -> None:
                async def escolher_anc(ligar_anc: bool) -> None:
                    estado_atual = dev.state.wear if dev.state.wear is not None else True
                    await enviar_wear(enable=estado_atual, anc=ligar_anc)
                    self.pop_screen()
                    self.pop_screen()
                    await abrir_wear()

                await self.push_screen(
                    MenuScreen(
                        "Desligar ANC ao Remover",
                        [f"Atual: {dev.state.wear_anc_label()}"],
                        [("Ligar", lambda: escolher_anc(True)), ("Desligar", lambda: escolher_anc(False))],
                    )
                )

            opcoes = [("Ligar", lambda: ligar(True)), ("Desligar", lambda: ligar(False))]
            if dev.state.wear:
                opcoes.append((f"Desligar ANC ao remover: {dev.state.wear_anc_label()}", abrir_wear_anc))

            await self.push_screen(
                MenuScreen("Detecção de Uso", [f"Atual: {dev.state.wear_label()}"], opcoes)
            )

        async def pedir_mac(mac: str) -> None:
            await self.push_screen(
                MenuScreen(
                    "UUIDs padrão?",
                    [f"MAC: {mac}"],
                    [
                        ("Usar UUIDs padrão já confirmados", lambda: escolher_uuid(mac, True)),
                        ("Definir UUIDs manualmente", lambda: escolher_uuid(mac, False)),
                    ],
                )
            )

        async def escolher_uuid(mac: str, usar_padrao: bool) -> None:
            if usar_padrao:
                await finalizar_reconfig(
                    mac, device.DEFAULT_UUID_SERVICE, device.DEFAULT_UUID_WRITE, device.DEFAULT_UUID_NOTIFY
                )
            else:
                await self.push_screen(
                    FormScreen(
                        "UUID do serviço",
                        "uuid do serviço...",
                        (lambda v: pedir_uuid_write(mac, v)),
                        initial_value=device.DEFAULT_UUID_SERVICE,
                    )
                )

        async def pedir_uuid_write(mac: str, uuid_service: str) -> None:
            await self.push_screen(
                FormScreen(
                    "UUID de escrita",
                    "uuid de escrita...",
                    (lambda v: pedir_uuid_notify(mac, uuid_service, v)),
                    initial_value=device.DEFAULT_UUID_WRITE,
                )
            )

        async def pedir_uuid_notify(mac: str, uuid_service: str, uuid_write: str) -> None:
            await self.push_screen(
                FormScreen(
                    "UUID de notificação",
                    "uuid de notificação...",
                    (lambda v: finalizar_reconfig(mac, uuid_service, uuid_write, v)),
                    initial_value=device.DEFAULT_UUID_NOTIFY,
                )
            )

        async def finalizar_reconfig(mac: str, uuid_service: str, uuid_write: str, uuid_notify: str) -> None:
            config.save_device(mac, uuid_service, uuid_write, uuid_notify)
            if dev.connected:
                await dev.disconnect()
            novo_dev = MelobudsDevice(
                address=mac, uuid_service=uuid_service, uuid_write=uuid_write, uuid_notify=uuid_notify
            )
            try:
                await novo_dev.connect()
            except Exception as e:
                await self.push_screen(
                    MenuScreen("Falha ao reconectar", [str(e)], [("Voltar ao menu", self._voltar_ao_menu)])
                )
                return
            self.dev = novo_dev
            self._resetar_para_menu_principal()

        async def abrir_reconfigurar() -> None:
            await self.push_screen(
                FormScreen(
                    "Endereço MAC do fone",
                    "MAC do fone (já pareado no sistema)...",
                    pedir_mac,
                    initial_value=dev.address or "",
                )
            )

        await self.push_screen(
            MenuScreen(
                "Ajustes do Fone",
                [],
                [
                    ("Equilíbrio do canal", abrir_balance),
                    ("Reconfigurar fone (MAC/UUIDs)", abrir_reconfigurar),
                    ("Volume de Notificação", abrir_tone_volume),
                    ("Modo de Jogo", abrir_game_mode),
                    ("Modo de Sono", abrir_sleep_mode),
                    ("LDAC", abrir_ldac),
                    ("Detecção de Uso", abrir_wear),
                ],
            )
        )


def main() -> None:
    MelobudsTUI().run()


if __name__ == "__main__":
    main()