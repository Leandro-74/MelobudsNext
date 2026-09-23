# src/tui_app.py

from __future__ import annotations

from typing import Awaitable, Callable, List, Optional, Tuple

import asyncio

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option
from textual.binding import Binding

from . import commands
from . import config
from . import device
from . import console
from . import keys
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
        permitir_vazio: bool = False,
    ) -> None:
        super().__init__()
        self._titulo_painel = titulo_painel
        self._placeholder = placeholder
        self._on_submit = on_submit
        self._permitir_vazio = permitir_vazio

    def compose(self) -> ComposeResult:
        with Vertical():
            with Vertical(classes="painel") as painel:
                painel.border_title = self._titulo_painel
                yield Input(placeholder=self._placeholder)
            yield Static(_formatar_barra([("enter", "Confirmar")]), id="barra")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        valor = event.value.strip()
        self.app.pop_screen()
        if valor or self._permitir_vazio:
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
        while len(self.screen_stack) > 1:
            self.pop_screen()
        await self.push_screen(self._menu_principal())

    async def _sair(self) -> None:
        self.exit()

    async def _abrir_anc(self) -> None:
        dev = self.dev
        assert dev is not None

        async def desligar() -> None:
            await dev.send_command(commands.anc_off())
            await dev.sync_state()
            await self._abrir_anc()

        async def cena(cena_id: int, nome_cena: str) -> None:
            async def escolher_nivel(nivel: int) -> None:
                comando = commands.anc_cena(cena_id, nivel)
                await dev.send_command(comando)
                await dev.sync_state()
                await self._abrir_anc()

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
            await self._abrir_anc()

        async def transparencia() -> None:
            async def vocal() -> None:
                await dev.send_command(commands.aprimoramento_vocal())
                await dev.sync_state()
                await self._abrir_anc()

            async def nivel(n: int) -> None:
                await dev.send_command(commands.transparencia(n))
                await dev.sync_state()
                await self._abrir_anc()

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

    async def _abrir_touch(self) -> None:
        dev = self.dev
        assert dev is not None

        async def escolher_funcao(key: int) -> None:
            async def aplicar_funcao(indice: int) -> None:
                mapping = dict(dev.state.touch or {})   # copia: nunca mutar o state
                mapping[key] = keys.FUNC_ORDER[indice]
                await dev.gravar_touch(mapping)
                dev.state.touch = dict(mapping)
                await self._abrir_touch()
            await self.push_screen(
                MenuScreen(
                    "Função do Toque",
                    [],
                    [(keys.FUNC_NAMES[f], (lambda i=i: aplicar_funcao(i)))
                     for i, f in enumerate(keys.FUNC_ORDER)],
                )
            )

        async def desativar() -> None:
            await dev.gravar_touch({k: keys.FUNC_NONE for k in keys.KEY_ORDER})
            dev.state.touch = {k: keys.FUNC_NONE for k in keys.KEY_ORDER}
            await self._abrir_touch()

        async def restaurar() -> None:
            if not dev.state.touch_inicial:
                return
            await dev.gravar_touch(dev.state.touch_inicial)
            dev.state.touch = dict(dev.state.touch_inicial)
            await self._abrir_touch()

        mapping = dev.state.touch or {}
        opcoes = [
            (f"{keys.KEY_NAMES[k]}: {keys.FUNC_NAMES[mapping.get(k, keys.FUNC_NONE)]}",
             (lambda k=k: escolher_funcao(k)))
            for k in keys.KEY_ORDER
        ]
        opcoes += [
            ("Desativar touch (tudo Nenhuma)", desativar),
            ("Restaurar mapeamento inicial", restaurar),
        ]
        await self.push_screen(MenuScreen("Personalizar Touch", [], opcoes))

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

    async def abrir_tone_volume(self) -> None:
        dev = self.dev
        async def definir(categoria: int) -> None:
            comando = commands.tone_volume(categoria)
            await dev.send_command(comando)
            dev.state.aplicar(comando)
            await asyncio.sleep(0.5)
            await dev.send_command(commands.request_data(commands.CMD_TONE_VOLUME))
            await asyncio.sleep(0.8)
            await self._voltar_ao_menu()
        
        await self.push_screen(
            MenuScreen(
                "Volume de Notificação",
                [f"Atual: {dev.state.tone_volume_label()}"],
                [
                    ("Volume mais baixo", lambda: definir(1)),
                    ("Volume médio", lambda: definir(2)),
                    ("Volume mais alto", lambda: definir(3)),
                    ("Volume máximo", lambda: definir(4)),
                ],
            )
        )
    
    async def _abrir_ajustes(self) -> None:
        dev = self.dev
        assert dev is not None

        async def game_mode(ligar: bool) -> None:
            comando = commands.game_mode(ligar)
            await dev.send_command(comando)
            dev.state.aplicar(comando)
            await self._abrir_ajustes()

        async def sleep_mode(ligar: bool) -> None:
            comando = commands.sleep_mode(ligar)
            await dev.send_command(comando)
            dev.state.aplicar(comando)
            await self._abrir_ajustes()

        async def ldac(ligar: bool) -> None:
            await dev.send_command(commands.ldac(ligar))
            await dev.reconectar()
            await self._abrir_ajustes()

        async def balance(valor: int) -> None:
            comando = commands.sound_balance(valor)
            await dev.send_command(comando)
            dev.state.aplicar(comando)
            await self._abrir_ajustes()

        async def tone_volume(categoria: int) -> None:
            comando = commands.tone_volume(categoria)
            await dev.send_command(comando)
            dev.state.aplicar(comando)
            await asyncio.sleep(0.5)
            await dev.send_command(commands.request_data(commands.CMD_TONE_VOLUME))
            await asyncio.sleep(0.8)
            await self._voltar_ao_menu()

        async def enviar_wear(ligar: bool, anc: bool) -> None:
            raw = dev.state.wear_raw or (0x00, 0x01, 0x00, 0x00)
            comando = commands.wearing_detection(
                ligar, anc, music_index=raw[1], tone=raw[3]
            )
            await dev.send_command(comando)
            dev.state.aplicar(comando)
            await asyncio.sleep(0.5)
            await dev.send_command(commands.request_data(commands.CMD_WEARING))
            await asyncio.sleep(0.8)

        async def abrir_wear_anc() -> None:
            async def trocar(ligar: bool) -> None:
                await enviar_wear(dev.state.wear if dev.state.wear is not None else True, ligar)
                await self._voltar_ao_menu()
            await self.push_screen(
                MenuScreen(
                    "Desligar ANC ao Remover",
                    [f"Atual: {dev.state.wear_anc_label()}"],
                    [("Ligar", lambda: trocar(True)), ("Desligar", lambda: trocar(False))],
                )
            )

        async def abrir_wear() -> None:
            async def trocar(ligar: bool) -> None:
                await enviar_wear(ligar, dev.state.wear_anc or False)
                await self._voltar_ao_menu()
            opcoes = [("Ligar", lambda: trocar(True)), ("Desligar", lambda: trocar(False))]
            if dev.state.wear:
                opcoes.append(
                    (f"Desligar ANC ao remover: {dev.state.wear_anc_label()}", abrir_wear_anc)
                )
            await self.push_screen(
                MenuScreen("Detecção de Uso", [f"Atual: {dev.state.wear_label()}"], opcoes)
            )

        async def reconfigurar() -> None:
            async def confirmar() -> None:
                await dev.disconnect()
                config.clear_config()

                async def finalizar(mac: str, us: str, uw: str, un: str) -> None:
                    config.save_device(mac, us, uw, un)
                    novo = MelobudsDevice(
                        address=mac, uuid_service=us, uuid_write=uw, uuid_notify=un
                    )
                    try:
                        await novo.connect()
                    except Exception as e:
                        self.exit(message=f"Falha ao conectar: {e}")
                        return
                    self.dev = novo
                    await self._voltar_ao_menu()

                async def uuids_um_a_um(mac: str) -> None:
                    async def servico(us: str) -> None:
                        async def escrita(uw: str) -> None:
                            async def notificacao(un: str) -> None:
                                await finalizar(mac, us or device.DEFAULT_UUID_SERVICE,
                                                uw or device.DEFAULT_UUID_WRITE,
                                                un or device.DEFAULT_UUID_NOTIFY)
                            await self.push_screen(FormScreen(
                                "UUID de notificação", device.DEFAULT_UUID_NOTIFY,
                                notificacao, permitir_vazio=True))
                        await self.push_screen(FormScreen(
                            "UUID de escrita", device.DEFAULT_UUID_WRITE,
                            escrita, permitir_vazio=True))
                    await self.push_screen(FormScreen(
                        "UUID do serviço", device.DEFAULT_UUID_SERVICE,
                        servico, permitir_vazio=True))

                async def mac_ok(mac: str) -> None:
                    async def sim() -> None:
                        await finalizar(mac, device.DEFAULT_UUID_SERVICE,
                                        device.DEFAULT_UUID_WRITE, device.DEFAULT_UUID_NOTIFY)
                    async def nao() -> None:
                        await uuids_um_a_um(mac)
                    await self.push_screen(MenuScreen(
                        "UUIDs", ["Usar os UUIDs padrão já confirmados?"],
                        [("Sim", sim), ("Não", nao)]))

                await self.push_screen(FormScreen(
                    "Reconfigurar fone", "MAC: AA:BB:CC:DD:EE:FF", mac_ok))

            await self.push_screen(MenuScreen(
                "Reconfigurar fone",
                ["A conexão será encerrada e a config apagada."],
                [("Continuar", confirmar)],
            ))

        async def abrir_game_mode() -> None:
            await self.push_screen(MenuScreen(
                "Modo de Jogo", [f"Atual: {dev.state.game_mode_label()}"],
                [("Ativar", lambda: game_mode(True)), ("Desativar", lambda: game_mode(False))]))

        async def abrir_sleep_mode() -> None:
            await self.push_screen(MenuScreen(
                "Modo de Sono", [f"Atual: {dev.state.sleep_mode_label()}"],
                [("Ativar", lambda: sleep_mode(True)), ("Desativar", lambda: sleep_mode(False))]))

        async def abrir_ldac() -> None:
            await self.push_screen(MenuScreen(
                "LDAC", [f"Atual: {dev.state.ldac_label()}", "Obs: o fone reinicia para aplicar"],
                [("Ativar", lambda: ldac(True)), ("Desativar", lambda: ldac(False))]))

        async def abrir_balance() -> None:
            await self.push_screen(MenuScreen(
                "Equilíbrio do Canal", [f"Atual: {dev.state.balance_label()}"],
                [("Todo esquerda", lambda: balance(0)),
                 ("Centro (padrão)", lambda: balance(50)),
                 ("Todo direita", lambda: balance(100))]))

        async def abrir_tone_volume() -> None:
            await self.push_screen(MenuScreen(
                "Volume de Notificação", [f"Atual: {dev.state.tone_volume_label()}"],
                [("Volume mais baixo", lambda: tone_volume(1)),
                 ("Volume médio", lambda: tone_volume(2)),
                 ("Volume mais alto", lambda: tone_volume(3)),
                 ("Volume máximo", lambda: tone_volume(4))]))

        await self.push_screen(
            MenuScreen(
                "Ajustes do Fone",
                [],
                [
                    ("Equilíbrio do canal", abrir_balance),
                    ("Reconfigurar fone (MAC/UUIDs)", reconfigurar),
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