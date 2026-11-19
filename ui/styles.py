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
        'bg': '#f4f5f9', 'sidebar': '#ebedf4', 'card': '#ffffff', 'field': '#f4f5f9',
        'primary': '#6d4aff', 'primary_dark': '#5a39e0', 'primary_soft': '#e9e4ff',
        'text': '#171a24', 'muted': '#6a7184', 'border': '#dcdfea', 'hover': '#e4e7f1',
        'selection': '#6d4aff', 'selection_text': '#ffffff', 'danger': '#d6455d',
    },
    'escuro': {
        'bg': '#0d0e12', 'sidebar': '#14151b', 'card': '#181a21', 'field': '#101117',
        'primary': '#7c5cff', 'primary_dark': '#6747f0', 'primary_soft': '#2a2352',
        'text': '#eceef4', 'muted': '#8d93a5', 'border': '#272a35', 'hover': '#20232d',
        'selection': '#7c5cff', 'selection_text': '#ffffff', 'danger': '#ef6b80',
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

DEFAULT_THEME = 'escuro'
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
    style.configure('Step.TLabel', font=(FAMILY, base - 2, 'bold'),
                    background=COLORS['bg'], foreground=COLORS['primary'])
    style.configure('CardTitle.TLabel', font=(FAMILY, base + 2, 'bold'),
                    background=COLORS['card'], foreground=COLORS['text'])

    style.configure('TSeparator', background=COLORS['border'])
    style.configure('TEntry', fieldbackground=COLORS['field'], foreground=COLORS['text'],
                    insertcolor=COLORS['text'], padding=9, bordercolor=COLORS['border'],
                    lightcolor=COLORS['border'], darkcolor=COLORS['border'], relief='flat')
    style.map('TEntry', bordercolor=[('focus', COLORS['primary'])],
              lightcolor=[('focus', COLORS['primary'])], darkcolor=[('focus', COLORS['primary'])])
    style.configure('TCombobox', fieldbackground=COLORS['field'], background=COLORS['field'],
                    foreground=COLORS['text'], arrowcolor=COLORS['muted'], arrowsize=14,
                    bordercolor=COLORS['border'], lightcolor=COLORS['field'],
                    darkcolor=COLORS['field'], padding=(8, 6))
    style.map('TCombobox',
              fieldbackground=[('readonly', COLORS['field'])],
              background=[('active', COLORS['hover']), ('readonly', COLORS['field'])],
              foreground=[('readonly', COLORS['text'])],
              selectbackground=[('readonly', COLORS['field'])],
              selectforeground=[('readonly', COLORS['text'])],
              bordercolor=[('focus', COLORS['primary'])],
              arrowcolor=[('active', COLORS['text'])])
    style.configure('TCheckbutton', background=COLORS['card'], foreground=COLORS['text'],
                    indicatorbackground=COLORS['field'], font=(FAMILY, base))
    style.map('TCheckbutton', background=[('active', COLORS['card'])],
              indicatorbackground=[('selected', COLORS['primary'])])

    style.configure('Sidebar.TFrame', background=COLORS['sidebar'])
    style.configure('Sidebar.TLabel', background=COLORS['sidebar'], foreground=COLORS['text'])
    style.configure('SidebarTitle.TLabel', font=(FAMILY, base + 6, 'bold'),
                    background=COLORS['sidebar'], foreground=COLORS['text'])
    style.configure('SidebarMuted.TLabel', background=COLORS['sidebar'], foreground=COLORS['muted'],
                    font=(FAMILY, base - 1))
    style.configure('Stat.TLabel', font=(FAMILY, base + 8, 'bold'),
                    background=COLORS['sidebar'], foreground=COLORS['primary'])
    style.configure('Border.TFrame', background=COLORS['border'])
    style.configure('Hint.TLabel', background=COLORS['bg'], foreground=COLORS['muted'],
                    font=(FAMILY, base - 1))

    style.configure('Sidebar.TCheckbutton', background=COLORS['sidebar'], foreground=COLORS['text'],
                    indicatorbackground=COLORS['field'], font=(FAMILY, base))
    style.map('Sidebar.TCheckbutton', background=[('active', COLORS['sidebar'])],
              indicatorbackground=[('selected', COLORS['primary'])])
    style.configure('App.TCheckbutton', background=COLORS['bg'], foreground=COLORS['text'],
                    indicatorbackground=COLORS['field'], font=(FAMILY, base))
    style.map('App.TCheckbutton', background=[('active', COLORS['bg'])],
              indicatorbackground=[('selected', COLORS['primary'])])

    style.configure('Accent.TButton', font=(FAMILY, base, 'bold'),
                    background=COLORS['primary'], foreground='white',
                    padding=(16, 9), borderwidth=0, focuscolor=COLORS['primary'])
    style.map('Accent.TButton',
              background=[('active', COLORS['primary_dark']), ('disabled', COLORS['border'])],
              foreground=[('disabled', COLORS['muted'])])

    style.configure('Secondary.TButton', font=(FAMILY, base),
                    background=COLORS['card'], foreground=COLORS['text'],
                    bordercolor=COLORS['border'], lightcolor=COLORS['card'],
                    darkcolor=COLORS['card'], padding=(12, 8), borderwidth=1,
                    focuscolor=COLORS['card'])
    style.map('Secondary.TButton', background=[('active', COLORS['hover'])],
              foreground=[('disabled', COLORS['muted'])])

    # Botões de navegação da barra lateral: planos, só destacam ao passar o mouse.
    style.configure('Nav.TButton', font=(FAMILY, base), anchor='w',
                    background=COLORS['sidebar'], foreground=COLORS['text'],
                    padding=(12, 9), borderwidth=0, focuscolor=COLORS['sidebar'])
    style.map('Nav.TButton', background=[('active', COLORS['hover'])],
              foreground=[('disabled', COLORS['muted'])])
    style.configure('NavPrimary.TButton', font=(FAMILY, base, 'bold'), anchor='w',
                    background=COLORS['primary'], foreground='white',
                    padding=(12, 10), borderwidth=0, focuscolor=COLORS['primary'])
    style.map('NavPrimary.TButton', background=[('active', COLORS['primary_dark'])])

    style.configure('Treeview', font=(FAMILY, base), rowheight=base * 2 + 14,
                    bordercolor=COLORS['border'], lightcolor=COLORS['card'], darkcolor=COLORS['card'],
                    background=COLORS['card'], fieldbackground=COLORS['card'],
                    foreground=COLORS['text'], borderwidth=0)
    style.map('Treeview', background=[('selected', COLORS['selection'])],
              foreground=[('selected', COLORS['selection_text'])])
    style.configure('Treeview.Heading', font=(FAMILY, base - 1, 'bold'), relief='flat',
                    background=COLORS['sidebar'], foreground=COLORS['muted'], padding=(8, 6))
    style.map('Treeview.Heading', background=[('active', COLORS['hover'])])

    for sb in ('TScrollbar', 'Vertical.TScrollbar'):
        style.configure(sb, background=COLORS['border'], troughcolor=COLORS['card'],
                        bordercolor=COLORS['card'], lightcolor=COLORS['border'],
                        darkcolor=COLORS['border'], arrowcolor=COLORS['muted'],
                        gripcount=0, arrowsize=12, relief='flat')
        style.map(sb, background=[('active', COLORS['muted'])])

    # Caixinhas de marcar: no tema clam as cores do quadradinho têm nomes próprios.
    for nome, fundo in (('TCheckbutton', COLORS['card']), ('Sidebar.TCheckbutton', COLORS['sidebar']),
                        ('App.TCheckbutton', COLORS['bg'])):
        style.configure(nome, indicatorforeground='white', indicatormargin=(0, 0, 8, 0),
                        upperbordercolor=COLORS['muted'], lowerbordercolor=COLORS['muted'],
                        focuscolor=fundo, padding=(0, 2))
        style.map(nome, indicatorbackground=[('selected', COLORS['primary']), ('', COLORS['field'])],
                  upperbordercolor=[('selected', COLORS['primary'])],
                  lowerbordercolor=[('selected', COLORS['primary'])])
    style.configure('TProgressbar', background=COLORS['primary'],
                    troughcolor=COLORS['border'], borderwidth=0, thickness=6)


def style_drop_zone(zone, hover=False) -> None:
    """A área de soltar é Tk clássico (moldura + rótulos), então não segue estilo nomeado."""
    fundo = COLORS['primary_soft'] if hover else COLORS['card']
    zone.configure(bg=fundo, highlightbackground=COLORS['primary'] if hover else COLORS['border'],
                   highlightcolor=COLORS['primary'])
    fontes = {'icon': (FAMILY, BASE_SIZE + 14), 'title': (FAMILY, BASE_SIZE + 2, 'bold'),
              'sub': (FAMILY, BASE_SIZE)}
    cores = {'icon': COLORS['primary'], 'title': COLORS['text'], 'sub': COLORS['muted']}
    for filho in zone.winfo_children():
        papel = getattr(filho, 'role', 'sub')
        if papel == 'img':
            filho.configure(bg=fundo)
            continue
        filho.configure(bg=fundo, fg=cores[papel], font=fontes[papel])


def style_plain(widget, bg, fg, delta=0, weight='normal') -> None:
    """Rótulos Tk clássicos soltos (logo, dica da busca, aviso de lista vazia)."""
    widget.configure(bg=COLORS[bg], fg=COLORS[fg], font=(FAMILY, BASE_SIZE + delta, weight))


def style_menu(menu) -> None:
    """Idem para o menu de contexto, que também é Tk clássico."""
    menu.configure(bg=COLORS['card'], fg=COLORS['text'], font=(FAMILY, BASE_SIZE),
                   activebackground=COLORS['selection'],
                   activeforeground=COLORS['selection_text'], borderwidth=0)
