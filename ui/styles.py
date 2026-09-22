"""Paleta de cores, tamanhos de fonte e estilos ttk usados em toda a interface.

Cor e tamanho de texto saem daqui e de mais lugar nenhum: a tela é montada só
com estilos nomeados, então trocar de tema ou de tamanho de fonte é recalcular
esses estilos e mandar o Tk redesenhar — sem refazer a janela nem perder o que
o usuário já tinha na tela.

As preferências ficam no mesmo `config.json` das outras.
"""

from tkinter import ttk

from core import config

FAMILY = 'Segoe UI'

PALETTES = {
    'claro': {
        'bg': '#f2f4f9', 'card': '#ffffff', 'field': '#ffffff',
        'primary': '#2f6fed', 'primary_dark': '#1d4fbe',
        'text': '#1f2937', 'muted': '#6b7280', 'border': '#dfe3ee',
        'selection': '#2f6fed', 'selection_text': '#ffffff',
    },
    'escuro': {
        'bg': '#161a23', 'card': '#212736', 'field': '#2b3243',
        'primary': '#4b82f0', 'primary_dark': '#3a6ad4',
        'text': '#e8eaf0', 'muted': '#9aa3b2', 'border': '#39414f',
        'selection': '#4b82f0', 'selection_text': '#ffffff',
    },
}

THEMES = [('claro', 'Claro'), ('escuro', 'Escuro')]
FONT_SIZES = [('pequena', 9), ('media', 10), ('grande', 12)]
FONT_SIZE_LABELS = [('pequena', 'Pequena'), ('media', 'Média'), ('grande', 'Grande')]

THEME_LABEL_BY_KEY = dict(THEMES)
THEME_KEY_BY_LABEL = {label: key for key, label in THEMES}
FONT_SIZE_PX = dict(FONT_SIZES)
FONT_SIZE_LABEL_BY_KEY = dict(FONT_SIZE_LABELS)
FONT_SIZE_KEY_BY_LABEL = {label: key for key, label in FONT_SIZE_LABELS}

DEFAULT_THEME = 'claro'
DEFAULT_FONT_SIZE = 'media'

# Paleta e tamanho em vigor. Widgets que não são ttk (o rótulo da área de
# soltar, o menu de contexto) não seguem estilo nomeado e leem daqui, então
# isso é estado do módulo, atualizado a cada `apply`.
COLORS = dict(PALETTES[DEFAULT_THEME])
BASE_SIZE = FONT_SIZE_PX[DEFAULT_FONT_SIZE]


# --- Preferências ---
def load_theme() -> str:
    """Tema salvo; cai no claro se o config.json trouxer coisa desconhecida."""
    tema = config.get('theme')
    return tema if tema in PALETTES else DEFAULT_THEME


def save_theme(key: str) -> None:
    config.set('theme', key)


def load_font_size() -> str:
    """Tamanho de fonte salvo, também tolerante a valor inválido no arquivo."""
    tamanho = config.get('font_size')
    return tamanho if tamanho in FONT_SIZE_PX else DEFAULT_FONT_SIZE


def save_font_size(key: str) -> None:
    config.set('font_size', key)


# --- Estilos ---
def apply(root) -> None:
    """(Re)calcula todos os estilos a partir das preferências salvas."""
    global BASE_SIZE
    COLORS.clear()
    COLORS.update(PALETTES[load_theme()])
    BASE_SIZE = FONT_SIZE_PX[load_font_size()]
    base = BASE_SIZE

    style = ttk.Style(root)
    style.theme_use('clam')
    root.configure(bg=COLORS['bg'])

    # A lista suspensa do Combobox é um widget Tk clássico por dentro: só a
    # option database alcança as cores dela.
    root.option_add('*TCombobox*Listbox.background', COLORS['field'])
    root.option_add('*TCombobox*Listbox.foreground', COLORS['text'])
    root.option_add('*TCombobox*Listbox.selectBackground', COLORS['selection'])
    root.option_add('*TCombobox*Listbox.selectForeground', COLORS['selection_text'])

    style.configure('.', font=(FAMILY, base), background=COLORS['bg'], foreground=COLORS['text'])
    style.configure('App.TFrame', background=COLORS['bg'])
    style.configure('Card.TFrame', background=COLORS['card'])
    style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['text'])
    style.configure('Card.TLabel', background=COLORS['card'], foreground=COLORS['text'])
    style.configure('Title.TLabel', font=(FAMILY, base + 10, 'bold'),
                    background=COLORS['bg'], foreground=COLORS['text'])
    style.configure('Subtitle.TLabel', font=(FAMILY, base),
                    background=COLORS['bg'], foreground=COLORS['muted'])
    style.configure('CardSubtitle.TLabel', font=(FAMILY, base),
                    background=COLORS['card'], foreground=COLORS['muted'])
    style.configure('Section.TLabel', font=(FAMILY, base + 1, 'bold'),
                    background=COLORS['bg'], foreground=COLORS['text'])
    style.configure('CardTitle.TLabel', font=(FAMILY, base + 2, 'bold'),
                    background=COLORS['card'], foreground=COLORS['text'])

    style.configure('TSeparator', background=COLORS['border'])
    style.configure('TEntry', fieldbackground=COLORS['field'], foreground=COLORS['text'],
                    insertcolor=COLORS['text'], padding=8,
                    bordercolor=COLORS['border'], relief='flat')
    style.configure('TCombobox', fieldbackground=COLORS['field'], foreground=COLORS['text'],
                    background=COLORS['card'], arrowcolor=COLORS['text'], padding=6)
    style.map('TCombobox', fieldbackground=[('readonly', COLORS['field'])],
              foreground=[('readonly', COLORS['text'])])
    style.configure('TCheckbutton', background=COLORS['card'], foreground=COLORS['text'],
                    indicatorcolor=COLORS['field'], font=(FAMILY, base))
    style.map('TCheckbutton', background=[('active', COLORS['card'])],
              indicatorcolor=[('selected', COLORS['primary'])])

    style.configure('Accent.TButton', font=(FAMILY, base, 'bold'),
                    background=COLORS['primary'], foreground='white',
                    padding=(14, 8), borderwidth=0)
    style.map('Accent.TButton',
              background=[('active', COLORS['primary_dark']), ('disabled', COLORS['border'])])

    style.configure('Secondary.TButton', font=(FAMILY, base),
                    background=COLORS['card'], foreground=COLORS['primary'],
                    bordercolor=COLORS['border'], padding=(12, 7), borderwidth=1)
    style.map('Secondary.TButton', background=[('active', COLORS['bg'])],
              foreground=[('disabled', COLORS['muted'])])

    style.configure('Treeview', font=(FAMILY, base), rowheight=base * 2 + 6,
                    background=COLORS['card'], fieldbackground=COLORS['card'],
                    foreground=COLORS['text'], borderwidth=0)
    style.map('Treeview', background=[('selected', COLORS['selection'])],
              foreground=[('selected', COLORS['selection_text'])])
    style.configure('Treeview.Heading', font=(FAMILY, base, 'bold'),
                    background=COLORS['bg'], foreground=COLORS['text'])

    style.configure('TScrollbar', background=COLORS['card'], troughcolor=COLORS['bg'],
                    bordercolor=COLORS['border'], arrowcolor=COLORS['text'])
    style.configure('TProgressbar', background=COLORS['primary'],
                    troughcolor=COLORS['bg'], borderwidth=0, thickness=8)


def style_drop_zone(label) -> None:
    """A área de soltar é um tk.Label, então não segue estilo nomeado."""
    label.configure(bg=COLORS['card'], fg=COLORS['muted'],
                    highlightbackground=COLORS['border'], font=(FAMILY, BASE_SIZE))


def style_menu(menu) -> None:
    """Idem para o menu de contexto, que também é Tk clássico."""
    menu.configure(bg=COLORS['card'], fg=COLORS['text'], font=(FAMILY, BASE_SIZE),
                   activebackground=COLORS['selection'],
                   activeforeground=COLORS['selection_text'], borderwidth=0)
