"""Tela principal do Arquithon 3.0 fiel ao layout-regra:
- Sidebar com busca (Ctrl K), seção PASTAS e card Espaço organizado
- Topo com 'Organizar arquivos' e botão âmbar '↩ Desfazer última ação'
- Drop Zone tracejada com 'Organizar meus Downloads' e 'Escolher arquivos' empilhados à direita
- Pílulas 'Separar por [Tipo | Data | Nome | Tamanho]' e '[Copiar (seguro) | Mover]'
- Linha 'Destino uploads / ...' e barra verde de conclusão
- Detecção O(1) de projetos de código inteiros em codigo/projetos
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core import fs_utils, organizer, paths, search
from ui import dnd, result_dialog, settings_dialog, styles

SEARCH_DEBOUNCE_MS = 180

MODE_SHORT_LABELS = [
    ('extensao', 'Tipo'),
    ('data', 'Data'),
    ('nome', 'Nome'),
    ('tamanho', 'Tamanho'),
]

MODE_PREVIEW_EXAMPLES = {
    'extensao': 'uploads / documentos / ... / relatorio_2026.pdf',
    'data': 'uploads / 2026 / 11 - Novembro / relatorio_2026.pdf',
    'nome': 'uploads / alfabetico / R / relatorio_2026.pdf',
    'tamanho': 'uploads / tamanho / medios (1 a 50MB) / relatorio_2026.pdf',
}


class MainFrame(ttk.Frame):
    def __init__(self, app):
        super().__init__(app, style='App.TFrame', padding=0)
        self.item_paths = {}
        self.last_operations = []
        self.organizing = False
        self._search_index = None
        self._search_after_id = None
        self._drop_hover = False
        self._active_category_filter = None
        self._last_batch_count = 0
        self._total_bytes_cache = 0

        self._mode_key = organizer.load_org_mode()
        self.mode_var = tk.StringVar(value=organizer.ORG_MODE_LABEL_BY_KEY[self._mode_key])
        self.move_var = tk.BooleanVar(value=organizer.load_move_default())
        self._mode_buttons = {}
        self._copy_move_buttons = {}

        self._build_layout()
        self._update_rule_preview()
        self._show_categorized_view()

        dnd.enable_file_drop(app, self._on_files_dropped)

        app.bind('<Control-o>', lambda e: self._select_files())
        app.bind('<Control-f>', lambda e: self._focus_search())
        app.bind('<Control-k>', lambda e: self._focus_search())
        app.bind('<Control-z>', lambda e: self._undo_last_organize())
        app.bind('<Control-t>', lambda e: self._toggle_theme_quick())
        app.bind('<F5>', lambda e: self._refresh_all())

    # --- Layout Principal em 2 Colunas (Sidebar + Workspace) ---
    def _build_layout(self):
        self.columnconfigure(0, weight=0, minsize=230)
        self.columnconfigure(1, weight=0, minsize=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self, style='Sidebar.TFrame', padding=(16, 18, 16, 16))
        self.sidebar.grid(row=0, column=0, sticky='nsew')

        divider = tk.Frame(self, width=1, bg=styles.COLORS['border'], bd=0, highlightthickness=0)
        divider.grid(row=0, column=1, sticky='ns')
        self._divider = divider

        self.workspace = ttk.Frame(self, style='App.TFrame', padding=(24, 18, 24, 16))
        self.workspace.grid(row=0, column=2, sticky='nsew')

        self._build_sidebar()
        self._build_workspace()

    def _build_sidebar(self):
        # 1. Título "Arquithon 3.0"
        brand_row = ttk.Frame(self.sidebar, style='Sidebar.TFrame')
        brand_row.pack(fill='x', pady=(0, 14))
        ttk.Label(brand_row, text='Arquithon', style='SidebarTitle.TLabel').pack(side='left')
        ttk.Label(brand_row, text=' 3.0', style='SidebarVersion.TLabel').pack(side='left')

        # 2. Barra de Busca com Badge "Ctrl K"
        search_frame = tk.Frame(
            self.sidebar,
            bg=styles.COLORS['field'],
            highlightbackground=styles.COLORS['border'],
            highlightthickness=1,
            padx=8,
            pady=4,
        )
        search_frame.pack(fill='x', pady=(0, 18))
        self._search_frame = search_frame

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side='left', fill='x', expand=True)
        self.search_entry.bind('<Return>', lambda e: self._run_search())
        self.search_entry.bind('<KeyRelease>', self._on_search_key_release)
        self.search_entry.bind('<Escape>', lambda e: self._clear_search())

        ctrl_k = tk.Label(
            search_frame,
            text='Ctrl K',
            bg=styles.COLORS['card'],
            fg=styles.COLORS['muted'],
            font=(styles.FAMILY, 8),
            padx=5,
            pady=1,
        )
        ctrl_k.pack(side='right', padx=(4, 0))
        self._ctrl_k_badge = ctrl_k

        self.search_content_var = tk.BooleanVar(value=search.load_search_content_pref())

        # 3. Seção PASTAS
        ttk.Label(self.sidebar, text='PASTAS', style='SidebarSection.TLabel').pack(anchor='w', pady=(0, 6))
        self.nav_container = ttk.Frame(self.sidebar, style='Sidebar.TFrame')
        self.nav_container.pack(fill='x')

        spacer = ttk.Frame(self.sidebar, style='Sidebar.TFrame')
        spacer.pack(fill='both', expand=True)

        # 4. Card Inferior: "Espaço organizado  5,7 MB" + Barra Azul + "6 arquivos salvos"
        storage_card = tk.Frame(
            self.sidebar,
            bg=styles.COLORS['field'],
            highlightbackground=styles.COLORS['border'],
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        storage_card.pack(fill='x', pady=(12, 0))
        self._storage_card = storage_card

        top_stat = tk.Frame(storage_card, bg=styles.COLORS['field'])
        top_stat.pack(fill='x')
        self._top_stat = top_stat

        lbl_esp = tk.Label(
            top_stat,
            text='Espaço organizado',
            bg=styles.COLORS['field'],
            fg=styles.COLORS['muted'],
            font=(styles.FAMILY, 9),
        )
        lbl_esp.pack(side='left')
        self._lbl_esp = lbl_esp

        self.kpi_size_var = tk.StringVar(value='0 B')
        lbl_size = tk.Label(
            top_stat,
            textvariable=self.kpi_size_var,
            bg=styles.COLORS['field'],
            fg=styles.COLORS['text'],
            font=(styles.FAMILY, 9, 'bold'),
        )
        lbl_size.pack(side='right')
        self._lbl_size = lbl_size

        self.storage_bar = ttk.Progressbar(storage_card, mode='determinate', maximum=100, value=35)
        self.storage_bar.pack(fill='x', pady=(8, 6))

        self.kpi_files_var = tk.StringVar(value='0 arquivos salvos')
        lbl_count = tk.Label(
            storage_card,
            textvariable=self.kpi_files_var,
            bg=styles.COLORS['field'],
            fg=styles.COLORS['muted'],
            font=(styles.FAMILY, 8),
            anchor='w',
        )
        lbl_count.pack(fill='x')
        self._lbl_count = lbl_count

    def _build_workspace(self):
        # 1. Topo: "Organizar arquivos" à esquerda + "↩ Desfazer última ação" (Âmbar) à direita
        header_row = ttk.Frame(self.workspace, style='App.TFrame')
        header_row.pack(fill='x', pady=(0, 12))

        ttk.Label(header_row, text='Organizar arquivos', style='Title.TLabel').pack(side='left')

        self.undo_btn = ttk.Button(
            header_row,
            text='↩  Desfazer última ação',
            style='Undo.TButton',
            command=self._undo_last_organize,
            state='disabled',
        )
        self.undo_btn.pack(side='right')

        # 2. Hero Drop Zone Tracejada com 2 Botões Empilhados à Direita
        self.drop_zone = tk.Canvas(
            self.workspace,
            height=104,
            highlightthickness=0,
            bd=0,
        )
        self.drop_zone.pack(fill='x', pady=(0, 12))
        self.drop_zone.redraw_drop_zone = self._redraw_drop_canvas

        # Container dos 2 botões empilhados dentro da Drop Zone à direita
        self.drop_btns_frame = tk.Frame(self.drop_zone, bg=styles.COLORS['field'])
        self.btn_downloads = ttk.Button(
            self.drop_btns_frame,
            text='Organizar meus Downloads',
            style='Accent.TButton',
            command=self._organize_downloads_preset,
        )
        self.btn_downloads.pack(fill='x', pady=(0, 6))

        self.btn_choose = ttk.Button(
            self.drop_btns_frame,
            text='Escolher arquivos',
            style='Secondary.TButton',
            command=self._select_files,
        )
        self.btn_choose.pack(fill='x')

        self.drop_zone.bind('<Configure>', lambda e: self._redraw_drop_canvas(self._drop_hover))
        self.drop_zone.bind('<Button-1>', lambda e: self._select_files())
        self.drop_zone.bind('<Enter>', lambda e: self._set_drop_hover(True))
        self.drop_zone.bind('<Leave>', lambda e: self._set_drop_hover(False))

        # 3. Linha "Separar por [Tipo | Data | Nome | Tamanho]" e "[Copiar (seguro) | Mover]"
        controls_row = ttk.Frame(self.workspace, style='App.TFrame')
        controls_row.pack(fill='x', pady=(0, 10))

        left_ctrl = ttk.Frame(controls_row, style='App.TFrame')
        left_ctrl.pack(side='left')
        ttk.Label(left_ctrl, text='Separar por', style='Subtitle.TLabel').pack(side='left', padx=(0, 8))

        mode_box = tk.Frame(
            left_ctrl,
            bg=styles.COLORS['field'],
            highlightbackground=styles.COLORS['border'],
            highlightthickness=1,
            padx=2,
            pady=2,
        )
        mode_box.pack(side='left')
        self._mode_box = mode_box

        for key, short_label in MODE_SHORT_LABELS:
            btn = ttk.Button(
                mode_box,
                text=short_label,
                style='PillActive.TButton' if key == self._mode_key else 'Pill.TButton',
                command=lambda k=key: self._select_mode_pill(k),
            )
            btn.pack(side='left', padx=1)
            self._mode_buttons[key] = btn

        copy_box = tk.Frame(
            controls_row,
            bg=styles.COLORS['field'],
            highlightbackground=styles.COLORS['border'],
            highlightthickness=1,
            padx=2,
            pady=2,
        )
        copy_box.pack(side='right')
        self._copy_box = copy_box

        is_move = self.move_var.get()
        btn_copy = ttk.Button(
            copy_box,
            text='Copiar (seguro)',
            style='Pill.TButton' if is_move else 'PillActive.TButton',
            command=lambda: self._set_move_mode(False),
        )
        btn_copy.pack(side='left', padx=1)
        btn_move = ttk.Button(
            copy_box,
            text='Mover',
            style='PillActive.TButton' if is_move else 'Pill.TButton',
            command=lambda: self._set_move_mode(True),
        )
        btn_move.pack(side='left', padx=1)
        self._copy_move_buttons = {'copy': btn_copy, 'move': btn_move}

        # 4. Linha "Destino  uploads / documentos / ... / relatorio_2026.pdf"
        dest_row = ttk.Frame(self.workspace, style='App.TFrame')
        dest_row.pack(fill='x', pady=(0, 10))
        ttk.Label(dest_row, text='Destino ', style='Bold.TLabel').pack(side='left')
        self.preview_path_var = tk.StringVar()
        ttk.Label(dest_row, textvariable=self.preview_path_var, style='Subtitle.TLabel').pack(side='left')

        # 5. Barra Verde de Conclusão ("✓ Concluído · 6/6 arquivos copiados [━━━━━] 5,7 MB")
        self.done_canvas = tk.Canvas(self.workspace, height=36, highlightthickness=0, bd=0)
        self.done_canvas.pack(fill='x', pady=(0, 12))
        self.done_canvas.bind('<Configure>', lambda e: self._redraw_green_banner())

        # Barra de progresso ativa durante processamento
        self.progress_frame = ttk.Frame(self.workspace, style='App.TFrame')
        self.progress_label_var = tk.StringVar(value='')
        ttk.Label(
            self.progress_frame, textvariable=self.progress_label_var, style='Subtitle.TLabel'
        ).pack(anchor='w', pady=(0, 3))
        self.progress = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress.pack(fill='x', pady=(0, 10))

        # 6. Cabeçalho da Lista: "ARQUIVOS ORGANIZADOS (6)" | "PASTA"
        list_header = ttk.Frame(self.workspace, style='App.TFrame')
        list_header.pack(fill='x', pady=(0, 6))
        self.list_title = ttk.Label(list_header, text='ARQUIVOS ORGANIZADOS (0)', style='Section.TLabel')
        self.list_title.pack(side='left')
        ttk.Label(list_header, text='PASTA', style='Section.TLabel').pack(side='right', padx=(0, 18))

        # 7. Lista de Arquivos
        tree_frame = ttk.Frame(self.workspace, style='Card.TFrame')
        tree_frame.pack(fill='both', expand=True)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=('tamanho', 'destino'),
            show='tree',
        )
        self.tree.column('#0', width=380, minwidth=220, stretch=True, anchor='w')
        self.tree.column('tamanho', width=95, minwidth=80, stretch=False, anchor='e')
        self.tree.column('destino', width=180, minwidth=130, stretch=False, anchor='e')

        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.context_menu = tk.Menu(self.tree, tearoff=0)
        styles.style_menu(self.context_menu)
        self.tree.bind('<Button-3>', self._show_context_menu)
        self.tree.bind('<Double-1>', lambda e: self._open_selected())
        self.tree.bind('<Button-1>', self._on_tree_click)

    def _redraw_drop_canvas(self, hover: bool = False):
        c = styles.COLORS
        w = max(self.drop_zone.winfo_width(), 520)
        h = max(self.drop_zone.winfo_height(), 104)
        border = c['primary'] if hover else c['dash_border']

        self.drop_zone.configure(bg=c['bg'])
        self.drop_zone.delete('bg_rect')
        self.drop_zone.delete('txt')

        self.drop_zone.create_rectangle(
            2, 2, w - 2, h - 2,
            fill=c['field'],
            outline=border,
            width=1.5,
            dash=(6, 4),
            tags='bg_rect',
        )

        self.drop_zone.create_text(
            22, h // 2 - 11,
            anchor='w',
            text='Arraste arquivos ou pastas para cá',
            fill=c['text'],
            font=(styles.FAMILY, styles.BASE_SIZE + 2, 'bold'),
            tags='txt',
        )
        self.drop_zone.create_text(
            22, h // 2 + 12,
            anchor='w',
            text='ou escolha uma das opções ao lado',
            fill=c['muted'],
            font=(styles.FAMILY, styles.BASE_SIZE),
            tags='txt',
        )

        self.drop_btns_frame.configure(bg=c['field'])
        self.drop_zone.create_window(
            w - 18, h // 2,
            anchor='e',
            window=self.drop_btns_frame,
            width=205,
        )

    def _redraw_green_banner(self):
        c = styles.COLORS
        w = max(self.done_canvas.winfo_width(), 520)
        h = 36
        self.done_canvas.configure(bg=c['bg'])
        self.done_canvas.delete('all')

        self.done_canvas.create_rectangle(
            1, 1, w - 1, h - 1,
            fill=c['green_bg'],
            outline=c['green_border'],
            width=1,
        )

        qtd = self._last_batch_count
        verbo = 'movidos' if self.move_var.get() else 'copiados'
        msg = f'✓   Concluído · {qtd}/{qtd} arquivos {verbo}'
        self.done_canvas.create_text(
            14, h // 2,
            anchor='w',
            text=msg,
            fill=c['green_fg'],
            font=(styles.FAMILY, styles.BASE_SIZE, 'bold'),
        )

        mb_str = organizer.format_file_size(self._total_bytes_cache).replace('.', ',')
        self.done_canvas.create_text(
            w - 14, h // 2,
            anchor='e',
            text=mb_str,
            fill=c['green_fg'],
            font=(styles.FAMILY, styles.BASE_SIZE, 'bold'),
        )

        bar_x1 = 265
        bar_x2 = max(bar_x1 + 40, w - 78)
        bar_y = h // 2
        self.done_canvas.create_line(
            bar_x1, bar_y, bar_x2, bar_y,
            fill=c['green_track'],
            width=6,
        )
        if qtd > 0:
            self.done_canvas.create_line(
                bar_x1, bar_y, bar_x2, bar_y,
                fill=c['green_bar'],
                width=6,
            )

    def _update_rule_preview(self):
        exemplo = MODE_PREVIEW_EXAMPLES.get(self._mode_key, MODE_PREVIEW_EXAMPLES['extensao'])
        self.preview_path_var.set(exemplo)

    def _set_move_mode(self, move: bool):
        self.move_var.set(move)
        self._copy_move_buttons['copy'].configure(style='Pill.TButton' if move else 'PillActive.TButton')
        self._copy_move_buttons['move'].configure(style='PillActive.TButton' if move else 'Pill.TButton')
        self._redraw_green_banner()

    def _select_mode_pill(self, mode_key: str):
        self._mode_key = mode_key
        self.mode_var.set(organizer.ORG_MODE_LABEL_BY_KEY[mode_key])
        organizer.save_org_mode(mode_key)
        for k, btn in self._mode_buttons.items():
            btn.configure(style='PillActive.TButton' if k == mode_key else 'Pill.TButton')
        self._update_rule_preview()

    def _toggle_theme_quick(self):
        styles.toggle_theme()
        self._apply_appearance()

    def _open_settings(self):
        if settings_dialog.show(self.winfo_toplevel()):
            self._apply_appearance()

    def _apply_appearance(self):
        styles.apply(self.winfo_toplevel())
        self._redraw_drop_canvas(self._drop_hover)
        self._redraw_green_banner()
        styles.style_menu(self.context_menu)

    def _set_drop_hover(self, hover: bool):
        self._drop_hover = hover
        self._redraw_drop_canvas(hover=hover)

    # --- Cache de índice ---
    def _invalidate_index(self):
        self._search_index = None

    def _get_index(self):
        if self._search_index is None:
            self._search_index = search.build_index()
        return self._search_index

    def _refresh_all(self):
        self._invalidate_index()
        if self.search_var.get().strip():
            self._run_search()
        else:
            self._show_categorized_view()

    # --- Organização ---
    def _open_root_folder(self):
        self._safe_open(fs_utils.open_in_explorer, paths.UPLOAD_FOLDER)

    def _organize_downloads_preset(self):
        downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        if not os.path.isdir(downloads_dir):
            messagebox.showinfo('Downloads', 'Não foi possível localizar a pasta Downloads padrão.')
            return

        itens = fs_utils.collect_files([downloads_dir])
        if not itens:
            messagebox.showinfo('Downloads', 'Sua pasta Downloads não possui arquivos para organizar.')
            return

        modo_nome = dict(MODE_SHORT_LABELS).get(self._mode_key, 'Tipo')
        acao_nome = 'Mover' if self.move_var.get() else 'Copiar (seguro)'
        if not messagebox.askyesno(
            'Organizar meus Downloads',
            f'{len(itens)} item(ns) encontrados em Downloads.\n\n'
            f'Separar por: {modo_nome}  ·  Modo: {acao_nome}\n\n'
            'Organizar agora?',
        ):
            return

        self._organize_paths(itens)

    def _select_files(self):
        selected = filedialog.askopenfilenames(title='Selecione os arquivos para organizar')
        if not selected:
            return
        self._organize_paths(list(selected))

    def _select_folder(self):
        folder = filedialog.askdirectory(title='Selecione uma pasta ou projeto para organizar')
        if not folder:
            return
        self._organize_entries([folder])

    def _on_files_dropped(self, dropped):
        if self.organizing:
            return
        self.winfo_toplevel().focus_force()
        self._organize_entries(dropped)

    def _organize_entries(self, entries):
        if any(self._is_inside_app(entry) for entry in entries):
            messagebox.showwarning(
                'Organização',
                'Não é possível organizar arquivos de dentro da própria pasta do Arquithon.',
            )
            return

        arquivos = fs_utils.collect_files(entries)
        if not arquivos:
            messagebox.showinfo('Organização', 'Nenhum arquivo encontrado para organizar.')
            return
        self._organize_paths(arquivos)

    @staticmethod
    def _is_inside_app(path):
        alvo = os.path.normcase(os.path.normpath(path))
        base = os.path.normcase(os.path.normpath(paths.BASE_DIR))
        return alvo == base or alvo.startswith(base + os.sep)

    def _focus_search(self):
        self.search_entry.focus_set()
        self.search_entry.select_range(0, 'end')

    def _organize_paths(self, selected):
        self.organizing = True
        try:
            mode_key = self._mode_key
            move = self.move_var.get()

            if move and not messagebox.askyesno(
                'Mover arquivos',
                f'Isso vai remover {len(selected)} item(ns) do local de origem.\n\nContinuar?',
            ):
                return

            self.progress_frame.pack(fill='x', before=self.tree.master)
            self.progress.configure(maximum=len(selected), value=0)

            def on_progress(feito, total):
                pct = int((feito / max(total, 1)) * 100)
                self.progress.configure(value=feito)
                self.progress_label_var.set(f'Organizando {feito} de {total} ({pct}%)')
                self.update_idletasks()

            try:
                resultado = organizer.organize_files(
                    selected, mode=mode_key, move=move, on_progress=on_progress
                )
            finally:
                self.progress_frame.pack_forget()

            if not resultado.successful:
                messagebox.showwarning('Organização', 'Nenhum arquivo pôde ser organizado.')
                return

            self._invalidate_index()
            self.last_operations = resultado.operations
            self._last_batch_count = resultado.successful
            self.undo_btn.configure(state='normal')
            self._show_categorized_view()

            escolha = result_dialog.show(self.winfo_toplevel(), resultado, move)
            if escolha == 'reverter':
                self._undo_last_organize()
            elif escolha == 'abrir':
                self._open_root_folder()
        finally:
            self.organizing = False

    def _undo_last_organize(self):
        if not self.last_operations:
            return
        restaurados, falhas = organizer.undo_operations(self.last_operations)
        self.last_operations = []
        self.undo_btn.configure(state='disabled')
        self._invalidate_index()

        msg = f'{restaurados} item(ns) restaurados.'
        if falhas:
            msg += f'\n{falhas} não puderam ser desfeitos.'
        messagebox.showinfo('Desfazer última ação', msg)
        self._show_categorized_view()

    # --- Busca ao Vivo ---
    def _on_search_key_release(self, event=None):
        if event and event.keysym in ('Return', 'Escape', 'Up', 'Down', 'Left', 'Right'):
            return
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(SEARCH_DEBOUNCE_MS, self._run_search)

    def _run_search(self):
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
            self._search_after_id = None

        query = self.search_var.get().strip()
        if not query:
            self._show_categorized_view()
            return
        index = self._get_index()
        results = search.search(index, query, include_content=self.search_content_var.get())
        self._show_search_results(results, query)

    def _clear_search(self):
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
            self._search_after_id = None
        self.search_var.set('')
        self._show_categorized_view()

    # --- Sidebar e Lista de Arquivos ---
    def _filter_by_top_category(self, top_cat):
        self._active_category_filter = top_cat
        if self.search_var.get().strip():
            self.search_var.set('')
        self._show_categorized_view()

    def _rebuild_sidebar_categories(self, organized: dict, total_files: int):
        for w in self.nav_container.winfo_children():
            w.destroy()

        counts = {}
        for rel_path, arquivos in organized.items():
            top = rel_path.split(os.sep)[0]
            counts[top] = counts.get(top, 0) + len(arquivos)

        all_btn = ttk.Button(
            self.nav_container,
            text=f'Todos os arquivos   {total_files}',
            style='NavActive.TButton' if self._active_category_filter is None else 'Nav.TButton',
            command=lambda: self._filter_by_top_category(None),
        )
        all_btn.pack(fill='x', pady=1)

        sidebar_labels = {
            'documentos': 'Documentos',
            'imagens': 'Imagens',
            'codigo': 'Código-fonte',
            'planilhas': 'Planilhas',
        }

        for top_cat, qtd in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            label = sidebar_labels.get(top_cat, organizer._capitalizar_primeira_letra(top_cat))
            is_sel = self._active_category_filter == top_cat
            btn = ttk.Button(
                self.nav_container,
                text=f'{label}   {qtd}',
                style='NavActive.TButton' if is_sel else 'Nav.TButton',
                command=lambda c=top_cat: self._filter_by_top_category(c),
            )
            btn.pack(fill='x', pady=1)

    @staticmethod
    def _file_prefix(filename: str, is_project: bool = False) -> str:
        if is_project:
            return f'<>   {filename}  (projeto intacto)'
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if ext in ('py', 'js', 'ts', 'tsx', 'jsx', 'html', 'css', 'json', 'sql', 'java', 'c', 'cpp', 'cs', 'go', 'rs'):
            return f'<>   {filename}'
        if ext in ('xlsx', 'xls', 'csv', 'ods'):
            return f'⊞   {filename}'
        if ext in ('png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico'):
            return f'▣   {filename}'
        return f'▯   {filename}'

    def _show_categorized_view(self):
        self.tree.delete(*self.tree.get_children())
        self.item_paths.clear()

        organized = organizer.scan_organized_files()
        total_all_files = sum(len(a) for a in organized.values())
        self._rebuild_sidebar_categories(organized, total_all_files)

        if not organized:
            self.list_title.configure(text='ARQUIVOS ORGANIZADOS (0)')
            self.kpi_size_var.set('0 B')
            self.kpi_files_var.set('0 arquivos salvos')
            self._total_bytes_cache = 0
            self._last_batch_count = 0
            self._redraw_green_banner()
            self.tree.insert(
                '', 'end',
                text='Arraste arquivos ou clique em Organizar meus Downloads acima',
                values=('', ''),
            )
            return

        total_bytes = 0
        shown_files = 0

        for rel_path, arquivos in organized.items():
            top_cat = rel_path.split(os.sep)[0]
            dest_clean = rel_path.replace(os.sep, ' / ')
            is_proj_cat = os.path.normpath(rel_path) == os.path.normpath(os.path.join('codigo', 'projetos'))

            for nome in arquivos:
                abs_path = os.path.join(paths.UPLOAD_FOLDER, rel_path, nome)
                try:
                    st = os.stat(abs_path)
                    f_size = st.st_size
                except OSError:
                    f_size = 0
                total_bytes += f_size

                if self._active_category_filter and top_cat != self._active_category_filter:
                    continue

                shown_files += 1
                item_kind = 'pasta' if is_proj_cat and os.path.isdir(abs_path) else 'arquivo'
                tam_str = organizer.format_file_size(f_size).replace('.', ',')
                file_iid = self.tree.insert(
                    '', 'end',
                    text=self._file_prefix(nome, is_project=(item_kind == 'pasta')),
                    values=(tam_str, f'{dest_clean}   ↗'),
                )
                self.item_paths[file_iid] = (item_kind, abs_path)

        self._total_bytes_cache = total_bytes
        if self._last_batch_count == 0:
            self._last_batch_count = total_all_files

        self.list_title.configure(text=f'ARQUIVOS ORGANIZADOS ({shown_files})')
        self.kpi_size_var.set(organizer.format_file_size(total_bytes).replace('.', ','))
        self.kpi_files_var.set(f'{total_all_files} arquivos salvos')
        self._redraw_green_banner()

    def _show_search_results(self, results, query):
        self.list_title.configure(text=f'ARQUIVOS ORGANIZADOS ({len(results)})')
        self.tree.delete(*self.tree.get_children())
        self.item_paths.clear()

        if not results:
            self.tree.insert('', 'end', text='Nenhum arquivo encontrado.', values=('', ''))
            return

        for item in results:
            dest_clean = os.path.dirname(item.rel_path).replace(os.sep, ' / ') or item.category
            tamanho = organizer.format_file_size(item.size).replace('.', ',')
            iid = self.tree.insert(
                '', 'end',
                text=self._file_prefix(item.name),
                values=(tamanho, f'{dest_clean}   ↗'),
            )
            self.item_paths[iid] = ('arquivo', item.path)

    def _on_tree_click(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        info = self.item_paths.get(iid)
        if not info or info[0] != 'pasta':
            return
        if self.tree.identify_element(event.x, event.y) == 'Treeitem.indicator':
            return
        self.tree.item(iid, open=not self.tree.item(iid, 'open'))

    def _show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        info = self.item_paths.get(iid)
        if not info:
            return
        self.tree.selection_set(iid)

        self.context_menu.delete(0, 'end')
        self.context_menu.add_command(label='Abrir no Explorer', command=self._open_selected)
        self.context_menu.add_command(label='Copiar caminho', command=self._copy_selected_path)
        if info[0] == 'arquivo':
            self.context_menu.add_separator()
            self.context_menu.add_command(label='Excluir arquivo', command=self._delete_selected_file)
        self.context_menu.post(event.x_root, event.y_root)

    def _copy_selected_path(self):
        selection = self.tree.selection()
        if not selection:
            return
        info = self.item_paths.get(selection[0])
        if not info:
            return
        caminho = info[1]
        self.clipboard_clear()
        self.clipboard_append(caminho)

    def _open_selected(self):
        selection = self.tree.selection()
        if not selection:
            return
        info = self.item_paths.get(selection[0])
        if not info:
            return
        tipo, caminho = info
        action = fs_utils.open_in_explorer if tipo == 'pasta' else fs_utils.open_and_select_file
        self._safe_open(action, caminho)

    def _delete_selected_file(self):
        selection = self.tree.selection()
        if not selection:
            return
        info = self.item_paths.get(selection[0])
        if not info or info[0] != 'arquivo':
            return
        caminho = info[1]
        nome = os.path.basename(caminho)

        if not messagebox.askyesno(
            'Excluir arquivo',
            f'Excluir "{nome}" permanentemente?\n\nEsta ação não pode ser desfeita pelo Arquithon.',
            icon='warning',
        ):
            return

        try:
            organizer.delete_file(caminho)
        except OSError:
            messagebox.showerror('Erro', f'Não foi possível excluir:\n{caminho}')
            return

        self._invalidate_index()
        if self.search_var.get().strip():
            self._run_search()
        else:
            self._show_categorized_view()

    @staticmethod
    def _safe_open(action, path):
        try:
            action(path)
        except OSError:
            messagebox.showerror('Erro', f'Não foi possível abrir:\n{path}')
