"""Janela principal: só monta a moldura e entrega o conteúdo ao MainFrame."""

import tkinter as tk

from ui import styles, window_state
from ui.main_frame import MainFrame


class ArquithonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Arquithon - Arquivista Digital')
        self.geometry('820x640')
        self.minsize(640, 480)

        styles.apply(self)  # já deixa a janela com a cor do tema escolhido
        MainFrame(self).pack(fill='both', expand=True)

        # Depois de montar a tela: a geometria salva tem a palavra final sobre
        # o tamanho que os widgets pediram.
        window_state.restore(self)
        window_state.watch(self)
