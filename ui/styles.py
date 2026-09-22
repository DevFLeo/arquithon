"""Paleta de cores e estilos ttk usados em toda a interface."""

from tkinter import ttk

COLORS = {
    'bg': '#f2f4f9',
    'card': '#ffffff',
    'primary': '#2f6fed',
    'primary_dark': '#1d4fbe',
    'text': '#1f2937',
    'muted': '#6b7280',
    'border': '#dfe3ee',
}


def apply(root) -> None:
    style = ttk.Style(root)
    style.theme_use('clam')

    style.configure('.', font=('Segoe UI', 10), background=COLORS['bg'])
    style.configure('App.TFrame', background=COLORS['bg'])
    style.configure('Card.TFrame', background=COLORS['card'])
    style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['text'])
    style.configure('Card.TLabel', background=COLORS['card'], foreground=COLORS['text'])
    style.configure('Title.TLabel', font=('Segoe UI', 20, 'bold'),
                     background=COLORS['bg'], foreground=COLORS['text'])
    style.configure('Subtitle.TLabel', font=('Segoe UI', 10),
                     background=COLORS['bg'], foreground=COLORS['muted'])
    style.configure('Section.TLabel', font=('Segoe UI', 11, 'bold'),
                     background=COLORS['bg'], foreground=COLORS['text'])

    style.configure('TEntry', fieldbackground='white', padding=8,
                     bordercolor=COLORS['border'], relief='flat')
    style.configure('TCombobox', fieldbackground='white', padding=6)
    style.configure('TCheckbutton', background=COLORS['card'], foreground=COLORS['text'])

    style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'),
                     background=COLORS['primary'], foreground='white',
                     padding=(14, 8), borderwidth=0)
    style.map('Accent.TButton',
               background=[('active', COLORS['primary_dark']), ('disabled', COLORS['border'])])

    style.configure('Secondary.TButton', font=('Segoe UI', 10),
                     background=COLORS['card'], foreground=COLORS['primary'],
                     padding=(12, 7), borderwidth=1)
    style.map('Secondary.TButton', background=[('active', COLORS['bg'])])

    style.configure('Treeview', font=('Segoe UI', 10), rowheight=26,
                     background='white', fieldbackground='white', borderwidth=0)
    style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))

    style.configure('TProgressbar', background=COLORS['primary'],
                     troughcolor=COLORS['bg'], borderwidth=0, thickness=8)
