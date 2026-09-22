"""Tela de configurações: aparência e comportamento padrão do app.

Tudo aqui é preferência que sobrevive ao fechamento, então cada campo é lido
do `config.json` ao abrir e gravado ao salvar. O diálogo não mexe na
interface: devolve True quando algo mudou, e quem chamou decide o que
redesenhar — assim a janela principal continua dona da própria aparência.
"""

import tkinter as tk
from tkinter import ttk

from core import organizer
from ui import styles, window_state


def show(parent) -> bool:
    """Abre as configurações. Devolve True se o usuário salvou alguma mudança."""
    dialog = _SettingsDialog(parent)
    parent.wait_window(dialog)
    return dialog.salvou


class _SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.salvou = False
        self.title('Configurações')
        self.configure(bg=styles.COLORS['bg'])
        self.transient(parent)
        self.resizable(False, False)

        corpo = ttk.Frame(self, style='App.TFrame', padding=18)
        corpo.pack(fill='both', expand=True)

        ttk.Label(corpo, text='Configurações', style='Section.TLabel').pack(anchor='w')
        ttk.Label(corpo, text='Valem para as próximas vezes que você abrir o app.',
                  style='Subtitle.TLabel').pack(anchor='w', pady=(2, 12))

        card = ttk.Frame(corpo, style='Card.TFrame', padding=16)
        card.pack(fill='both', expand=True)
        card.columnconfigure(1, weight=1)

        self.font_var = tk.StringVar(value=styles.FONT_SIZE_LABEL_BY_KEY[styles.load_font_size()])
        self._linha_combo(card, 0, 'Tamanho da fonte:', self.font_var,
                          [label for _, label in styles.FONT_SIZE_LABELS])

        self.theme_var = tk.StringVar(value=styles.THEME_LABEL_BY_KEY[styles.load_theme()])
        self._linha_combo(card, 1, 'Tema:', self.theme_var,
                          [label for _, label in styles.THEMES])

        self.move_var = tk.BooleanVar(value=organizer.load_move_default())
        ttk.Checkbutton(card, variable=self.move_var,
                        text='Começar com "Mover em vez de copiar" marcado',
                        ).grid(row=2, column=0, columnspan=2, sticky='w', pady=(14, 0))

        self.window_var = tk.BooleanVar(value=window_state.load_enabled())
        ttk.Checkbutton(card, variable=self.window_var,
                        text='Reabrir a janela do tamanho e no lugar em que foi fechada',
                        ).grid(row=3, column=0, columnspan=2, sticky='w', pady=(8, 0))

        linha = ttk.Frame(corpo, style='App.TFrame')
        linha.pack(fill='x', pady=(16, 0))
        self.salvar_btn = ttk.Button(linha, text='Salvar', style='Accent.TButton', command=self._salvar)
        self.salvar_btn.pack(side='right')
        ttk.Button(linha, text='Cancelar', style='Secondary.TButton',
                   command=self.destroy).pack(side='right', padx=(0, 10))

        self.bind('<Return>', lambda e: self._salvar())
        self.bind('<Escape>', lambda e: self.destroy())

        self._centralizar(parent)
        self.grab_set()
        self.salvar_btn.focus_set()

    def _linha_combo(self, card, row, rotulo, variavel, valores):
        ttk.Label(card, text=rotulo, style='Card.TLabel').grid(row=row, column=0, sticky='w',
                                                               pady=(0, 8))
        combo = ttk.Combobox(card, textvariable=variavel, state='readonly',
                             width=18, values=valores)
        combo.grid(row=row, column=1, sticky='w', padx=(12, 0), pady=(0, 8))

    def _salvar(self):
        styles.save_font_size(styles.FONT_SIZE_KEY_BY_LABEL[self.font_var.get()])
        styles.save_theme(styles.THEME_KEY_BY_LABEL[self.theme_var.get()])
        organizer.save_move_default(self.move_var.get())
        window_state.save_enabled(self.window_var.get())
        self.salvou = True
        self.grab_release()
        self.destroy()

    def _centralizar(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 3
        self.geometry(f'+{max(x, 0)}+{max(y, 0)}')
