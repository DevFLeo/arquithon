"""Memória da janela: reabre o app do tamanho e no lugar em que foi fechado.

Quem usa o Arquithon todo dia acaba deixando a janela de um jeito só — num
canto da tela, num monitor específico, maximizada. Guardar isso no mesmo
`config.json` das outras preferências é o bastante; não há estado de sessão
nenhum além de posição, tamanho e maximização.

A geometria salva é sempre a da janela *não* maximizada: é ela que volta
quando o usuário restaura a janela, então guardar a medida da tela cheia no
lugar dela deixaria a janela restaurada gigante.
"""

import tkinter as tk

from core import config

KEY = 'window'
SAVE_DELAY_MS = 600  # espera o usuário parar de arrastar/redimensionar antes de salvar
MARGEM_VISIVEL = 80  # quanto da janela precisa sobrar na tela para a posição valer


def load_enabled() -> bool:
    """Se o app deve reabrir com a janela do jeito que estava."""
    return bool(config.get('remember_window', True))


def save_enabled(value: bool) -> None:
    config.set('remember_window', value)


def restore(window: tk.Tk) -> None:
    """Aplica a geometria salva, se ela ainda couber nos monitores de hoje."""
    if not load_enabled():
        return
    dados = config.get(KEY) or {}
    largura, altura = dados.get('w'), dados.get('h')
    x, y = dados.get('x'), dados.get('y')

    if all(isinstance(v, int) for v in (largura, altura, x, y)) and _cabe_na_tela(window, x, y, largura, altura):
        window.geometry(f'{largura}x{altura}+{x}+{y}')
    if dados.get('maximizada'):
        window.state('zoomed')


def watch(window: tk.Tk) -> None:
    """Passa a lembrar posição, tamanho e maximização daqui em diante."""
    estado = {'geometria': None, 'agendado': None}

    def anotar(event=None):
        if event is not None and event.widget is not window:
            return  # Configure de widget filho sobe até aqui; não é mudança de janela
        if window.state() == 'normal':
            estado['geometria'] = (window.winfo_width(), window.winfo_height(),
                                   window.winfo_x(), window.winfo_y())
        if estado['agendado']:
            window.after_cancel(estado['agendado'])
        estado['agendado'] = window.after(SAVE_DELAY_MS, salvar)

    def salvar():
        estado['agendado'] = None
        if not estado['geometria'] or not load_enabled():
            return
        largura, altura, x, y = estado['geometria']
        config.set(KEY, {'w': largura, 'h': altura, 'x': x, 'y': y,
                         'maximizada': window.state() == 'zoomed'})

    def fechar():
        if estado['agendado']:
            window.after_cancel(estado['agendado'])
            estado['agendado'] = None
        salvar()
        window.destroy()

    anotar()  # registra a geometria inicial, caso a janela nunca seja mexida
    window.bind('<Configure>', anotar, add='+')
    window.protocol('WM_DELETE_WINDOW', fechar)


def _cabe_na_tela(window, x, y, largura, altura) -> bool:
    """Descarta posição de um monitor que não existe mais.

    Sem isso, quem fechou o app numa segunda tela e depois desligou ela
    reabriria a janela fora do alcance do mouse, sem jeito fácil de trazer de
    volta.
    """
    esquerda, topo, direita, baixo = _area_das_telas(window)
    return (x + largura > esquerda + MARGEM_VISIVEL
            and x < direita - MARGEM_VISIVEL
            and y + altura > topo + MARGEM_VISIVEL
            and y < baixo - MARGEM_VISIVEL)


def _area_das_telas(window) -> tuple:
    """Retângulo que cobre todos os monitores; no Windows, a tela virtual inteira."""
    try:
        import ctypes
        metric = ctypes.windll.user32.GetSystemMetrics
        x, y, largura, altura = metric(76), metric(77), metric(78), metric(79)  # SM_*VIRTUALSCREEN
        if largura and altura:
            return x, y, x + largura, y + altura
    except (AttributeError, OSError):
        pass
    return 0, 0, window.winfo_screenwidth(), window.winfo_screenheight()
