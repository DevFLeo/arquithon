"""Paleta de cores e estilos ttk fiéis ao design oficial do Arquithon 3.0."""

from tkinter import ttk

from core import config

FAMILY = 'Segoe UI'

PALETTES = {
    'escuro': {
        'bg': '#0e131d',
        'sidebar': '#0c1018',
        'card': '#141a26',
        'field': '#131926',
        'primary': '#2563eb',
        'primary_dark': '#1d4ed8',
        'brand_accent': '#3b82f6',
        'text': '#e8eaf0',
        'muted': '#7c889e',
        'border': '#1e2738',
        'dash_border': '#2c3852',
        'selection': '#1c2436',
        'selection_text': '#ffffff',
        'nav_active_bg': '#1c2436',
        'undo_bg': '#231e17',
        'undo_border': '#785c22',
        'undo_fg': '#f5b942',
        'green_bg': '#10241d',
        'green_border': '#1c4734',
        'green_fg': '#4ade80',
        'green_track': '#19382b',
        'green_bar': '#22c55e',
    },
    'claro': {
        'bg': '#f2f4f9',
        'sidebar': '#e8ecf5',
        'card': '#ffffff',
        'field': '#ffffff',
        'primary': '#2563eb',
        'primary_dark': '#1d4ed8',
        'brand_accent': '#2563eb',
        'text': '#0f172a',
        'muted': '#64748b',
        'border': '#dfe3ee',
        'dash_border': '#94a3b8',
        'selection': '#2563eb',
        'selection_text': '#ffffff',
        'nav_active_bg': '#dce8ff',
        'undo_bg': '#fef3c7',
        'undo_border': '#d97706',
        'undo_fg': '#b45309',
        'green_bg': '#dcfce7',
        'green_border': '#86efac',
        'green_fg': '#15803d',
        'green_track': '#bbf7d0',
        'green_bar': '#16a34a',
    },
}

THEMES = [('escuro', 'Escuro'), ('claro', 'Claro')]
FONT_SIZES = [('pequena', 9), ('media', 10), ('grande', 12)]
FONT_SIZE_LABELS = [('pequena', 'Pequena'), ('media', 'Média'), ('grande', 'Grande')]

THEME_LABEL_BY_KEY = dict(THEMES)
THEME_KEY_BY_LABEL = {label: key for key, label in THEMES}
FONT_SIZE_PX = dict(FONT_SIZES)
FONT_SIZE_LABEL_BY_KEY = dict(FONT_SIZE_LABELS)
FONT_SIZE_KEY_BY_LABEL = {label: key for key, label in FONT_SIZE_LABELS}

DEFAULT_THEME = 'escuro'
DEFAULT_FONT_SIZE = 'media'

COLORS = dict(PALETTES[DEFAULT_THEME])
BASE_SIZE = FONT_SIZE_PX[DEFAULT_FONT_SIZE]


def load_theme() -> str:
    tema = config.get('theme')
    return tema if tema in PALETTES else DEFAULT_THEME


def save_theme(key: str) -> None:
    config.set('theme', key)


def toggle_theme() -> str:
    novo = 'claro' if load_theme() == 'escuro' else 'escuro'
    save_theme(novo)
    return novo


def load_font_size() -> str:
    tamanho = config.get('font_size')
    return tamanho if tamanho in FONT_SIZE_PX else DEFAULT_FONT_SIZE


def save_font_size(key: str) -> None:
    config.set('font_size', key)


def apply(root) -> None:
    global BASE_SIZE
    COLORS.clear()
    COLORS.update(PALETTES[load_theme()])
    BASE_SIZE = FONT_SIZE_PX[load_font_size()]
    base = BASE_SIZE

    style = ttk.Style(root)
    style.theme_use('clam')
    root.configure(bg=COLORS['bg'])

    root.option_add('*TCombobox*Listbox.background', COLORS['field'])
    root.option_add('*TCombobox*Listbox.foreground', COLORS['text'])
    root.option_add('*TCombobox*Listbox.selectBackground', COLORS['selection'])
    root.option_add('*TCombobox*Listbox.selectForeground', COLORS['selection_text'])

    style.configure('.', font=(FAMILY, base), background=COLORS['bg'], foreground=COLORS['text'])
    style.configure('App.TFrame', background=COLORS['bg'])
    style.configure('Sidebar.TFrame', background=COLORS['sidebar'])
    style.configure('Card.TFrame', background=COLORS['card'])
    style.configure('Field.TFrame', background=COLORS['field'])

    style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['text'])
    style.configure('SidebarTitle.TLabel', font=(FAMILY, base + 5, 'bold'),
                    background=COLORS['sidebar'], foreground=COLORS['text'])
    style.configure('SidebarVersion.TLabel', font=(FAMILY, base + 5, 'bold'),
                    background=COLORS['sidebar'], foreground=COLORS['brand_accent'])
    style.configure('SidebarSection.TLabel', font=(FAMILY, max(base - 2, 8), 'bold'),
                    background=COLORS['sidebar'], foreground=COLORS['muted'])

    style.configure('Title.TLabel', font=(FAMILY, base + 5, 'bold'),
                    background=COLORS['bg'], foreground=COLORS['text'])
    style.configure('Subtitle.TLabel', font=(FAMILY, base),
                    background=COLORS['bg'], foreground=COLORS['muted'])
    style.configure('Bold.TLabel', font=(FAMILY, base, 'bold'),
                    background=COLORS['bg'], foreground=COLORS['text'])
    style.configure('Section.TLabel', font=(FAMILY, max(base - 2, 8), 'bold'),
                    background=COLORS['bg'], foreground=COLORS['muted'])

    style.configure('Card.TLabel', background=COLORS['card'], foreground=COLORS['text'])
    style.configure('CardTitle.TLabel', font=(FAMILY, base + 1, 'bold'),
                    background=COLORS['card'], foreground=COLORS['text'])
    style.configure('CardSubtitle.TLabel', font=(FAMILY, max(base - 1, 8)),
                    background=COLORS['card'], foreground=COLORS['muted'])

    style.configure('TSeparator', background=COLORS['border'])
    style.configure('TEntry', fieldbackground=COLORS['field'], foreground=COLORS['text'],
                    insertcolor=COLORS['text'], padding=6,
                    bordercolor=COLORS['border'], relief='flat')

    # Botão Primário Azul ("Organizar meus Downloads")
    style.configure('Accent.TButton', font=(FAMILY, base, 'bold'),
                    background=COLORS['primary'], foreground='#ffffff',
                    padding=(14, 7), borderwidth=0)
    style.map('Accent.TButton',
              background=[('active', COLORS['primary_dark']), ('disabled', COLORS['border'])])

    # Botão Secundário Escuro ("Escolher arquivos")
    style.configure('Secondary.TButton', font=(FAMILY, base),
                    background=COLORS['card'], foreground=COLORS['text'],
                    bordercolor=COLORS['dash_border'], padding=(14, 7), borderwidth=1)
    style.map('Secondary.TButton',
              background=[('active', COLORS['field'])],
              foreground=[('disabled', COLORS['muted'])])

    # Botão Âmbar "↩ Desfazer última ação" do topo direito
    style.configure('Undo.TButton', font=(FAMILY, max(base - 1, 9), 'bold'),
                    background=COLORS['undo_bg'], foreground=COLORS['undo_fg'],
                    bordercolor=COLORS['undo_border'], padding=(12, 6), borderwidth=1)
    style.map('Undo.TButton',
              background=[('active', COLORS['undo_bg']), ('disabled', COLORS['card'])],
              foreground=[('disabled', COLORS['muted'])],
              bordercolor=[('disabled', COLORS['border'])])

    # Pílulas Segmentadas ("Tipo | Data | Nome | Tamanho" e "Copiar (seguro) | Mover")
    style.configure('PillActive.TButton', font=(FAMILY, max(base - 1, 9), 'bold'),
                    background=COLORS['primary'], foreground='#ffffff',
                    padding=(12, 5), borderwidth=0)
    style.map('PillActive.TButton', background=[('active', COLORS['primary_dark'])])

    style.configure('Pill.TButton', font=(FAMILY, max(base - 1, 9)),
                    background=COLORS['field'], foreground=COLORS['muted'],
                    padding=(12, 5), borderwidth=0)
    style.map('Pill.TButton',
              background=[('active', COLORS['card'])],
              foreground=[('active', COLORS['text'])])

    # Navegação da Sidebar ("Todos os arquivos", "Documentos", "Imagens", "Código-fonte", "Planilhas")
    style.configure('NavActive.TButton', font=(FAMILY, base, 'bold'),
                    background=COLORS['nav_active_bg'], foreground='#ffffff',
                    padding=(10, 7), borderwidth=0, anchor='w')
    style.map('NavActive.TButton', background=[('active', COLORS['nav_active_bg'])])

    style.configure('Nav.TButton', font=(FAMILY, base),
                    background=COLORS['sidebar'], foreground=COLORS['muted'],
                    padding=(10, 7), borderwidth=0, anchor='w')
    style.map('Nav.TButton',
              background=[('active', COLORS['nav_active_bg'])],
              foreground=[('active', COLORS['text'])])

    # Lista de Arquivos (Treeview limpa)
    style.configure('Treeview', font=(FAMILY, base), rowheight=base * 2 + 16,
                    background=COLORS['card'], fieldbackground=COLORS['card'],
                    foreground=COLORS['text'], borderwidth=0, relief='flat')
    style.map('Treeview', background=[('selected', COLORS['selection'])],
              foreground=[('selected', COLORS['selection_text'])])
    style.configure('Treeview.Heading', font=(FAMILY, max(base - 2, 8), 'bold'),
                    background=COLORS['bg'], foreground=COLORS['muted'],
                    borderwidth=0, padding=(8, 6))
    style.map('Treeview.Heading', background=[('active', COLORS['bg'])])

    style.configure('TScrollbar', background=COLORS['card'], troughcolor=COLORS['bg'],
                    bordercolor=COLORS['bg'], arrowcolor=COLORS['muted'], borderwidth=0)
    style.configure('TProgressbar', background=COLORS['primary'],
                    troughcolor=COLORS['border'], borderwidth=0, thickness=6)


def style_drop_zone(widget, hover: bool = False) -> None:
    if hasattr(widget, 'redraw_drop_zone'):
        widget.redraw_drop_zone(hover=hover)


def style_menu(menu) -> None:
    menu.configure(bg=COLORS['card'], fg=COLORS['text'], font=(FAMILY, BASE_SIZE),
                   activebackground=COLORS['selection'],
                   activeforeground=COLORS['selection_text'], borderwidth=0)
