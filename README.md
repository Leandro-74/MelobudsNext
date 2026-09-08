<p align="center">
  <img src="assets/logo.png" alt="Logo do MelobudsNext" width="120">
</p>

<h1 align="center">MelobudsNext</h1>

<p align="center">
  Ferramenta em Python para controlar o fone <b>QCY Melobuds Pro</b> via
  Bluetooth Low Energy (BLE) — sem depender do app oficial.
</p>

> ⚠️ Projeto não oficial, construído por engenharia reversa. Sem vínculo com a
> QCY. Use por sua conta e risco.

## Funcionalidades

| Funcionalidade | Status |
| --- | --- |
| Game Mode (ligar/desligar) | ✅ Validado |
| ANC completo: Desligado, cenas Interior / Viagens Diárias / Barulho (níveis 1–3), Ruído Contra o Vento e Cancelamento Adaptativo | ✅ Validado |
| Modo Transparência: intensidades 1–6 + Aprimoramento Vocal | ✅ Validado |
| Bateria por lado no menu principal | ✅ Validado |
| Versão do firmware | ✅ Validado |
| Renomear o fone | ✅ Validado |
| Personalizar touch | ✅ Validado |
| Estado ao vivo: mudanças pelo touch ou pelo app oficial refletem na ferramenta | ✅ Validado |
| Volume, detecção in-ear, auto-desligar, opcodes desconhecidos | 🚧 A explorar |

## Protocolo validado (firmware 2.0.6)

Canal principal — escrita em `00001001-...`, notificações em `00001002-...`:

```
[0xFF] [body_len] [cmd] [param_len] [params...]     body_len = 2 + param_len
```

| Dado | Mecanismo |
| --- | --- |
| Game Mode | `0x09` + `01` (on) / `02` (off) |
| ANC | `0x17` + `[mode, sub, noise]` (cenas abaixo) |
| Renomear | `0x18` + nome UTF-8; leitura via `0xFE 0x18` (campo de 32 bytes, padding NUL) |
| Consulta de estado | `0xFE` + cmd (responde para `0x17`, `0x09` e `0x18`) |
| Bateria | Leitura direta da char `00000008`: `[L, R, estojo]`; bit 7 = carregando, bits 0–6 = nível |
| Versão | Leitura direta da char `00000007` |
| Touch | Leitura/escrita direta da char `0000000D`: 10 pares `[key, func]` = 20 bytes |

**Cenas ANC (`0x17`):** desligado = `00 00 00` (o fone *reporta* `02 00 00`);
mode `01` → sub `01` Interior, `02` Viagens, `03` Barulho (noise `00–02` =
níveis 1–3), sub `04` Vento e `05` Adaptativo (sem níveis); mode `03`
Transparência → sub `01`, noise `00` = Aprimoramento Vocal, `01–06` =
intensidades.

**Touch:** teclas `01–08` (Esq/Dir × 1–4 toques); funções `00–0B`, sendo
`0x0B` = Modo ANC **neste firmware** (a documentação padrão da QCY diz
"rediscar"). Desativar o touch = todas as funções `0x00`.

### Particularidades deste firmware (divergências do protocolo QCY padrão)

- `0x0C` (ANC simples) não existe; apenas `0x17`.
- `0xFE` não responde para bateria/versão — essas vêm de leitura direta.
- O fone fica mudo em repouso: só fala quando o estado muda.
- Bateria do estojo sempre reporta `0`.

## Requisitos

- Python 3.10+
- Bluetooth habilitado no computador
- Windows (testado); Linux suportado pelo bleak, ainda não testado aqui
- Fone pareado no sistema operacional e **não conectado** a outro dispositivo

## Instalação

```bash
git clone https://github.com/Leandro-74/MelobudsNext.git
cd MelobudsNext
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

Na primeira execução, informe o endereço MAC do fone (ele fica salvo para as
próximas). O menu principal já nasce com o nome do fone e a bateria por lado:

```
╔══════════════════════════════════════════════╗
║ MelobudsNext - Melobuds Pro de Leandro       ║
║ L: 94% | R: 78%                              ║
╠══════════════════════════════════════════════╣
║ 1. Ativar/Desativar Game Mode                ║
║ 2. Alterar modo ANC                          ║
║ 3. Consultar estados                         ║
║ 4. Renomear fone                             ║
║ 5. Personalizar touch                        ║
║ 6. Reconfigurar fone (MAC/UUIDs)             ║
║ 7. Sair                                      ║
╠══════════════════════════════════════════════╣
║ Escolha uma opcao:                           ║
╚══════════════════════════════════════════════╝
```

## Estrutura do projeto

```
MelobudsNext/
├── main.py            # ponto de entrada
├── requirements.txt
├── pyproject.toml
└── src/
    ├── commands.py    # protocolo: framing, opcodes e fábricas de comandos
    ├── keys.py        # protocolo de touch (char 0000000D)
    ├── state.py       # estado ao vivo do fone (nada persistido)
    ├── device.py      # conexão BLE (bleak), sincronização e leituras diretas
    ├── menu.py        # desenho das caixas e conteúdo dos menus
    ├── cli.py         # fluxo da interface e ações
    └── config.py      # persistência apenas de MAC/UUIDs
```

## Método de engenharia reversa

Nenhuma funcionalidade entra no código sem validação empírica: scripts de
laboratório enviam/leem pacotes crus, o **app oficial serve de oráculo** 
para conferir significados, e só então o mecanismo é integrado à ferramenta.
Divergências entre documentação de terceiros e bytes observados são sempre
resolvidas a favor dos bytes.

## Próximos passos

- Volume (`0x08`), detecção in-ear (`0x06`/`0x2C`), power manager (`0x14`)
- Explorar opcodes ainda não identificados (`0x10`, `0x1D`, `0x1F`, `0x2C`...)
- Testes automatizados de parse/montagem de pacotes
- Testar no Linux e empacotar (.exe / Arch)

## Contribuindo

Tem um QCY Melobuds Pro (ou outro modelo QCY) e quer validar/comparar o
protocolo no seu firmware? Capturas, saídas de laboratório e PRs são muito
bem-vindos via issue/PR.