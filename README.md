# MelobudsNext

Ferramenta em Python para controlar o fone de ouvido **QCY Melobuds Pro** via Bluetooth Low Energy (BLE) — sem depender do app oficial.

O protocolo foi mapeado por engenharia reversa, capturando o tráfego BLE com o app **nRF Connect** enquanto o app oficial era usado.

> ⚠️ Projeto não-oficial, feito por engenharia reversa. Sem vínculo com a QCY. Use por sua conta e risco.

## Status atual

| Comando | Status |
|---|---|
| Game Mode (ligar/desligar) | ✅ Confirmado |
| ANC (Desligado / Cancelamento de Ruído / Transparência) | ✅ Confirmado |
| Bateria | ❓ Hipótese (cmd `0x16`) |
| Versão de firmware | ❓ Hipótese (cmd `0x19`) |
| Tabela de equalização | ❓ Hipótese (cmd `0x22`, pacote grande) |
| Comandos `0x10`, `0x14`, `0x1D`, `0x1F`, `0x2C` | ❓ Não identificados |

## Requisitos

- Python 3.10+
- Bluetooth habilitado no computador
- Windows ou Linux (bleak suporta ambos; ainda não testado no Linux neste projeto)

## Instalação

```bash
git clone https://github.com/Leandro-74/MelobudsNext.git
cd MelobudsNext
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

Na primeira execução, o programa busca dispositivos BLE por 5 segundos e lista os encontrados para você escolher. O endereço é salvo em `~/.melobudsnext/config.json` e reaproveitado nas próximas execuções.

```
=== MelobudsNext - Controle do QCY Melobuds Pro ===

1. Ativar/Desativar Game Mode
2. Alterar modo ANC
3. Reconfigurar fone (buscar dispositivo)
4. Sair
```

## Estrutura do projeto

```
MelobudsNext/
├── main.py
├── pyproject.toml
├── requirements.txt
├── README.md
└── melobudsnext/
    ├── config.py       # persistencia do endereco MAC
    ├── device.py         # conexao BLE (bleak) e notificacoes
    ├── commands.py        # montagem/parsing de pacotes do protocolo
    └── cli.py              # menu numerado (assincrono)
```

## Como funciona por baixo dos panos

Os comandos seguem o formato `FF | Length | Cmd | ParamLen | Params...`, enviados via `write_gatt_char` na characteristic de escrita (`00001001-...`) do serviço `0000a001-...`. As respostas do fone chegam por notificação na characteristic `00001002-...`, no mesmo formato.

## Próximos passos

- Validar as hipóteses de comando (bateria, firmware, EQ) capturando novos logs com o nRF Connect enquanto cada função é usada isoladamente no app oficial
- Decodificar o pacote grande (`0x22`, ~145 bytes) — provável tabela de equalização
- Testar no Linux
- Empacotamento (.exe / Arch), no mesmo estilo do projeto irmão [HuskyNext](https://github.com/Leandro-74/huskynext)

## Contribuindo

Se você também tem um QCY Melobuds Pro, capturas de log validando (ou refutando) as hipóteses acima são muito bem-vindas via issue/PR.

## Licença

<!-- Defina a licença do projeto, ex: MIT -->
