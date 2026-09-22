"""Janela principal: só monta a moldura e entrega o conteúdo ao MainFrame."""

import tkinter as tk

from ui import styles
from ui.main_frame import MainFrame


class ArquithonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Arquithon - Arquivista Digital')
        self.geometry('820x640')
        self.minsize(640, 480)
        self.configure(bg=styles.COLORS['bg'])

        styles.apply(self)
        MainFrame(self).pack(fill='both', expand=True)
