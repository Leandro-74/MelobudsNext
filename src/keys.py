# src/keys.py

UUID_KEYS = "0000000d-0000-1000-8000-00805f9b34fb"

KEY_LEFT_1, KEY_RIGHT_1 = 0x01, 0x02
KEY_LEFT_2, KEY_RIGHT_2 = 0x03, 0x04
KEY_LEFT_3, KEY_RIGHT_3 = 0x05, 0x06
KEY_LEFT_4, KEY_RIGHT_4 = 0x07, 0x08

KEY_ORDER = [KEY_LEFT_1, KEY_RIGHT_1, KEY_LEFT_2, KEY_RIGHT_2,
             KEY_LEFT_3, KEY_RIGHT_3, KEY_LEFT_4, KEY_RIGHT_4]

KEY_NAMES = {
    KEY_LEFT_1: "Esq. 1 toque",    KEY_RIGHT_1: "Dir. 1 toque",
    KEY_LEFT_2: "Esq. 2 toques",   KEY_RIGHT_2: "Dir. 2 toques",
    KEY_LEFT_3: "Esq. 3 toques",   KEY_RIGHT_3: "Dir. 3 toques",
    KEY_LEFT_4: "Esq. 4 toques",   KEY_RIGHT_4: "Dir. 4 toques",
}

FUNC_NONE, FUNC_PLAY_PAUSE = 0x00, 0x01
FUNC_PREV, FUNC_NEXT = 0x02, 0x03
FUNC_ASSISTANT, FUNC_VOL_UP = 0x04, 0x05
FUNC_VOL_DOWN, FUNC_GAME_MODE = 0x06, 0x07
FUNC_ANSWER, FUNC_REJECT = 0x08, 0x09
FUNC_HOLD, FUNC_ANC_MODE = 0x0A, 0x0B

FUNC_ORDER = [FUNC_NONE, FUNC_PLAY_PAUSE, FUNC_PREV, FUNC_NEXT,
              FUNC_ASSISTANT, FUNC_VOL_UP, FUNC_VOL_DOWN, FUNC_GAME_MODE,
              FUNC_ANSWER, FUNC_REJECT, FUNC_HOLD, FUNC_ANC_MODE]

FUNC_NAMES = {
    FUNC_NONE: "Nenhuma (desativado)", FUNC_PLAY_PAUSE: "Play/Pause",
    FUNC_PREV: "Faixa anterior",       FUNC_NEXT: "Proxima faixa",
    FUNC_ASSISTANT: "Assistente de voz", FUNC_VOL_UP: "Volume +",
    FUNC_VOL_DOWN: "Volume -",         FUNC_GAME_MODE: "Alternar Game Mode",
    FUNC_ANSWER: "Atender chamada",    FUNC_REJECT: "Recusar chamada",
    FUNC_HOLD: "Chamada em espera",    FUNC_ANC_MODE: "Modo ANC",
}


def parse_pairs(data: bytes) -> dict:
    mapping = {}
    for i in range(0, len(data) - 1, 2):
        key, fun = data[i], data[i + 1]
        if key != 0x00:
            mapping[key] = fun
    return mapping


def build_bytes(mapping: dict) -> bytes:
    pares = []
    for key in KEY_ORDER:
        pares += [key, mapping.get(key, FUNC_NONE)]
    pares += [0x00, 0x00, 0x00, 0x00]
    return bytes(pares)