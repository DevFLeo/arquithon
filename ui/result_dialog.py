"""Diálogo de fim de organização: mostra o que foi para onde, com opção de reverter.

Antes esse momento era só um "12 arquivo(s) organizados com sucesso!" — o
usuário sabia quantos, mas não onde. Como a organização mexe em arquivo de
verdade, a hora de conferir (e de voltar atrás) é essa, com a lista na frente,
e não depois de ir procurar na árvore.
"""

import os
import tkinter as tk
from tkinter import ttk

from core import organizer, paths
from ui import styles

LINHAS_VISIVEIS = 8


def show(parent, resultado, move: bool) -> str:
    """Abre a lista do que foi organizado e devolve 'ok', 'reverter' ou 'abrir'."""
    dialog = _ResultDialog(parent, resultado, move)
    parent.wait_window(dialog)
    return dialog.escolha


class _ResultDialog(tk.Toplevel):
    def __init__(self, parent, resultado, move):
        super().__init__(parent)
        self.escolha = 'ok'  # fechar pelo X ou pelo Esc é o mesmo que confirmar
        self.title('Organização concluída')
        self.configure(bg=styles.COLORS['bg'])
        self.transient(parent)
        self.resizable(True, True)

        corpo = ttk.Frame(self, style='App.TFrame', padding=18)
        corpo.pack(fill='both', expand=True)

        ttk.Label(corpo, text=self._resumo(resultado, move),
                  style='Section.TLabel').pack(anchor='w')
        ttk.Label(corpo, text='Cada arquivo e a pasta onde ele foi parar:',
                  style='Subtitle.TLabel').pack(anchor='w', pady=(2, 8))

        self._build_lista(corpo, resultado.operations)
        self._build_botoes(corpo)

        self.bind('<Return>', lambda e: self._escolher('ok'))
        self.bind('<Escape>', lambda e: self._escolher('ok'))
        self.protocol('WM_DELETE_WINDOW', lambda: self._escolher('ok'))

        self._centralizar(parent)
        self.grab_set()
        self.ok_btn.focus_set()

    # --- Montagem ---
    @staticmethod
    def _resumo(resultado, move) -> str:
        verbo = 'movidos' if move else 'organizados'
        resumo = f'{resultado.successful} arquivo(s) {verbo} com sucesso!'
        if resultado.failed:
            acao = 'movidos' if move else 'copiados'
            resumo += f'  ({resultado.failed} não puderam ser {acao})'
        return resumo

    def _build_lista(self, corpo, operations):
        moldura = ttk.Frame(corpo, style='App.TFrame')
        moldura.pack(fill='both', expand=True)

        altura = min(max(len(operations), 3), LINHAS_VISIVEIS)
        self.tree = ttk.Treeview(moldura, columns=('arquivo', 'destino'), show='headings', height=altura)
        self.tree.heading('arquivo', text='Arquivo')
        self.tree.heading('destino', text='Foi para')
        self.tree.column('arquivo', width=260, anchor='w')
        self.tree.column('destino', width=340, anchor='w')

        vsb = ttk.Scrollbar(moldura, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        for op in operations:
            self.tree.insert('', 'end', values=_descrever(op))

    def _build_botoes(self, corpo):
        linha = ttk.Frame(corpo, style='App.TFrame')
        linha.pack(fill='x', pady=(14, 0))

        self.ok_btn = ttk.Button(linha, text='OK', style='Accent.TButton',
                                 command=lambda: self._escolher('ok'))
        self.ok_btn.pack(side='right')
        ttk.Button(linha, text='📂 Abrir pasta', style='Secondary.TButton',
                   command=lambda: self._escolher('abrir')).pack(side='right', padx=(0, 10))
        ttk.Button(linha, text='↩️ Reverter', style='Secondary.TButton',
                   command=lambda: self._escolher('reverter')).pack(side='right', padx=(0, 10))

    def _centralizar(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 3
        self.geometry(f'+{max(x, 0)}+{max(y, 0)}')

    def _escolher(self, escolha):
        self.escolha = escolha
        self.grab_release()
        self.destroy()


def _descrever(op) -> tuple:
    """Uma linha da lista: nome de origem e a categoria de destino."""
    nome = os.path.basename(op.source)
    rel = os.path.relpath(op.destination, paths.UPLOAD_FOLDER)
    destino = organizer.format_category_label(os.path.dirname(rel))

    # Se já existia um arquivo com esse nome, o organizador salvou como
    # "nome (2).ext" — quem está conferindo precisa saber disso.
    salvo_como = os.path.basename(op.destination)
    if salvo_como != nome:
        destino += f'  ·  salvo como "{salvo_como}"'
    return nome, destino
