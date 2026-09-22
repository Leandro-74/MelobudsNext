import ctypes
import ctypes.wintypes
import time
import os

# Descobre a janela VISIVEL do terminal (WT ou conhost) pelo titulo do console
def _hwnd_da_janela() -> int:
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    titulo = "MelobudsNext"
    kernel32.SetConsoleTitleW(titulo)
    time.sleep(0.25)                   # o WT atualiza o titulo em async
    hwnd = user32.FindWindowW(None, titulo)
    return hwnd or kernel32.GetConsoleWindow()   # fallback: conhost classico

# Redimensiona em pixels (pela grade atual) e centraliza a janela do console
def ajustar_janela(cols: int = 70, lines: int = 21) -> None:
    if os.name != "nt":
        return
    try:
        grid = os.get_terminal_size()
    except Exception:
        return
    try:
        user32 = ctypes.windll.user32
        hwnd = _hwnd_da_janela()
        if not hwnd:
            return
        if user32.IsZoomed(hwnd):
            user32.ShowWindow(hwnd, 9)     # SW_RESTORE
            time.sleep(0.15)
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        cell_w = w / max(1, grid.columns)  # px por caractere, medido na janela real
        cell_h = h / max(1, grid.lines)
        novo_w = int(cols * cell_w)
        novo_h = int(lines * cell_h)
        x = (user32.GetSystemMetrics(0) - novo_w) // 2
        y = (user32.GetSystemMetrics(1) - novo_h) // 2
        user32.MoveWindow(hwnd, x, y, novo_w, novo_h, True)
    except Exception:
        pass