"""Arrastar e soltar arquivos do Explorer direto na janela do Arquithon.

O Tkinter puro não recebe arquivos soltos pelo sistema: quem avisa que algo
foi largado em cima da janela é o próprio Windows, pela mensagem
WM_DROPFILES. Em vez de trazer uma dependência externa só para isso (o
tkinterdnd2 e a extensão Tcl que vem junto dele, que ainda precisaria ser
empacotada no .exe), a gente pede o serviço direto ao Windows com `ctypes`,
que já é biblioteca padrão — o app continua rodando com `python app.py` sem
instalar nada.

O caminho que a notícia faz é em dois passos, de propósito: o Windows chama a
nossa função de janela (WNDPROC) de dentro do laço de eventos do Tcl, onde
chamar qualquer coisa do Tk derruba o interpretador. Então o WNDPROC só
anota os caminhos numa fila, e um `after` do próprio Tk recolhe essa fila já
em terreno seguro e avisa a interface.

Fora do Windows, `enable_file_drop` só devolve False; a interface esconde a
área de soltar e o resto do app continua funcionando igual.
"""

import ctypes
import sys
from collections import deque
from ctypes import wintypes

WM_DROPFILES = 0x0233
GWL_WNDPROC = -4
DRAG_QUERY_COUNT = 0xFFFFFFFF  # índice especial: pede quantos arquivos vieram
POLL_MS = 100  # de quanto em quanto tempo o Tk olha a fila de coisas soltas

# O Windows guarda só o ponteiro do nosso WNDPROC. Se o coletor de lixo do
# Python levasse o objeto embora, a próxima mensagem cairia num ponteiro
# morto e derrubaria o app — por isso as referências ficam guardadas aqui.
_installed_procs = []


def enable_file_drop(widget, on_drop) -> bool:
    """Faz `widget` aceitar arquivos soltos, chamando `on_drop(caminhos)`.

    Devolve True se o sistema aceitou registrar a janela; False quando não dá
    para ativar (outro sistema operacional, ou API indisponível), para a
    interface poder se adaptar em vez de prometer algo que não funciona.
    """
    if sys.platform != 'win32':
        return False
    try:
        return _enable_windows_drop(widget, on_drop)
    except (AttributeError, OSError, ValueError):
        return False


def _enable_windows_drop(widget, on_drop) -> bool:
    user32 = ctypes.windll.user32
    shell32 = ctypes.windll.shell32

    lresult = ctypes.c_ssize_t
    wndproc_type = ctypes.WINFUNCTYPE(
        lresult, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
    )

    # SetWindowLongPtrW só existe em 64 bits; em 32 bits o ponteiro cabe no
    # SetWindowLongW mesmo.
    set_window_long = getattr(user32, 'SetWindowLongPtrW', None) or user32.SetWindowLongW
    set_window_long.argtypes = [wintypes.HWND, ctypes.c_int, wndproc_type]
    set_window_long.restype = lresult

    user32.CallWindowProcW.argtypes = [
        lresult, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
    ]
    user32.CallWindowProcW.restype = lresult

    shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
    shell32.DragQueryFileW.argtypes = [wintypes.HANDLE, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
    shell32.DragQueryFileW.restype = wintypes.UINT
    shell32.DragFinish.argtypes = [wintypes.HANDLE]

    hwnd = widget.winfo_id()
    pendentes = deque()
    previous_proc = None

    def on_message(msg_hwnd, msg, wparam, lparam):
        # Roda dentro do laço de eventos do Tcl: aqui só Python puro, nada de Tk.
        if msg == WM_DROPFILES:
            try:
                caminhos = _query_dropped_paths(shell32, wparam)
            finally:
                shell32.DragFinish(wparam)
            if caminhos:
                pendentes.append(caminhos)
            return 0
        return user32.CallWindowProcW(previous_proc, msg_hwnd, msg, wparam, lparam)

    proc = wndproc_type(on_message)
    previous_proc = set_window_long(hwnd, GWL_WNDPROC, proc)
    if not previous_proc:
        return False

    _installed_procs.append(proc)
    shell32.DragAcceptFiles(hwnd, True)

    # O id do `after` agendado fica aqui para poder ser cancelado no fechamento
    # (ver abaixo) -- sem isso, o último polling pendente dispara depois do
    # widget destruído e o Tcl imprime um erro "invalid command name" toda
    # vez que o app fecha.
    agendado = {'id': None}

    def cancelar(event=None):
        if agendado['id']:
            widget.after_cancel(agendado['id'])
            agendado['id'] = None

    widget.bind('<Destroy>', cancelar, add='+')
    _poll(widget, pendentes, on_drop, agendado)
    return True


def _poll(widget, pendentes, on_drop, agendado) -> None:
    """Entrega à interface, já no laço do Tk, o que o WNDPROC anotou."""
    while pendentes:
        on_drop(pendentes.popleft())
    agendado['id'] = widget.after(POLL_MS, _poll, widget, pendentes, on_drop, agendado)


def _query_dropped_paths(shell32, hdrop) -> list:
    """Lê do Windows a lista de caminhos que o usuário soltou na janela."""
    total = shell32.DragQueryFileW(hdrop, DRAG_QUERY_COUNT, None, 0)
    caminhos = []
    for i in range(total):
        tamanho = shell32.DragQueryFileW(hdrop, i, None, 0)
        buffer = ctypes.create_unicode_buffer(tamanho + 1)
        shell32.DragQueryFileW(hdrop, i, buffer, tamanho + 1)
        if buffer.value:
            caminhos.append(buffer.value)
    return caminhos
