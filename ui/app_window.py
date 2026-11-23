"""Janela principal: só monta a moldura e entrega o conteúdo ao MainFrame (v3.0)."""

import tkinter as tk

from ui import icon, styles, window_state
from ui.main_frame import MainFrame


class ArquithonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Arquithon 3.0 - Arquivista Digital')
        self.geometry('1020x720')
        self.minsize(820, 560)
        self._icons = [icon.photo(self, s) for s in (16, 32, 64)]
        self.iconphoto(True, *self._icons)

        styles.apply(self)  # já deixa a janela com a cor do tema escolhido
        MainFrame(self).pack(fill='both', expand=True)

        # Depois de montar a tela: a geometria salva tem a palavra final sobre
        # o tamanho que os widgets pediram.
        window_state.restore(self)
        window_state.watch(self)
