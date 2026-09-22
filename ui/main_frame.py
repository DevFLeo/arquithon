"""Tela única do app: organizar arquivos, buscar os já organizados, navegar."""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core import fs_utils, organizer, paths, search


class MainFrame(ttk.Frame):
    def __init__(self, app):
        super().__init__(app, style='App.TFrame', padding=24)
        self.item_paths = {}  # iid da árvore -> ('pasta' | 'arquivo', caminho absoluto)
        self.last_operations = []  # última leva de Operation, para permitir desfazer

        self._build_header()
        self._build_organize_card()
        self._build_search_card()
        self._build_results_tree()

        self._show_categorized_view()

        app.bind('<Control-o>', lambda e: self._select_files())
        app.bind('<Control-f>', lambda e: self._focus_search())

    # --- Montagem da interface ---
    def _build_header(self):
        header = ttk.Frame(self, style='App.TFrame')
        header.pack(fill='x')
        ttk.Label(header, text='🗂️ Arquithon', style='Title.TLabel').pack(anchor='w')
        ttk.Label(header, text='Desenvolvido por Leonardo Frez', style='Subtitle.TLabel').pack(anchor='w')
        ttk.Separator(self).pack(fill='x', pady=14)

    def _build_organize_card(self):
        card = ttk.Frame(self, style='Card.TFrame', padding=18)
        card.pack(fill='x', pady=(0, 14))
        card.columnconfigure(2, weight=1)

        ttk.Label(card, text='Organizar novos arquivos', style='Card.TLabel',
                  font=('Segoe UI', 12, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 10))
        ttk.Label(card, text='Organizar por:', style='Card.TLabel').grid(row=1, column=0, sticky='w')

        self.mode_var = tk.StringVar(value=organizer.ORG_MODE_LABEL_BY_KEY[organizer.load_org_mode()])
        mode_combo = ttk.Combobox(
            card, textvariable=self.mode_var, state='readonly', width=30,
            values=[label for _, label in organizer.ORG_MODES],
        )
        mode_combo.grid(row=1, column=1, sticky='w', padx=(8, 0))
        mode_combo.bind('<<ComboboxSelected>>', self._on_mode_change)

        self.move_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, text='Mover em vez de copiar (remove da origem)',
                        variable=self.move_var).grid(row=1, column=2, sticky='w', padx=(14, 0))

        btn_row = ttk.Frame(card, style='Card.TFrame')
        btn_row.grid(row=2, column=0, columnspan=3, sticky='w', pady=(14, 0))
        ttk.Button(btn_row, text='📁 Selecionar e Organizar Arquivos', style='Accent.TButton',
                   command=self._select_files).pack(side='left')
        ttk.Button(btn_row, text='🗂️ Selecionar Pasta', style='Secondary.TButton',
                   command=self._select_folder).pack(side='left', padx=(10, 0))
        ttk.Button(btn_row, text='📂 Abrir Pasta de Arquivos', style='Secondary.TButton',
                   command=self._open_root_folder).pack(side='left', padx=(10, 0))
        self.undo_btn = ttk.Button(btn_row, text='↩️ Desfazer última organização', style='Secondary.TButton',
                                    command=self._undo_last_organize, state='disabled')
        self.undo_btn.pack(side='left', padx=(10, 0))

        self.progress = ttk.Progressbar(card, mode='determinate')
        self.progress.grid(row=3, column=0, columnspan=3, sticky='ew', pady=(12, 0))
        self.progress.grid_remove()

    def _build_search_card(self):
        card = ttk.Frame(self, style='Card.TFrame', padding=18)
        card.pack(fill='x', pady=(0, 18))

        ttk.Label(card, text='Buscar arquivos organizados', style='Card.TLabel',
                  font=('Segoe UI', 12, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(card, textvariable=self.search_var, width=42)
        self.search_entry.grid(row=1, column=0, sticky='w')
        self.search_entry.bind('<Return>', lambda e: self._run_search())

        self.search_content_var = tk.BooleanVar(value=search.load_search_content_pref())
        ttk.Checkbutton(card, text='Também no conteúdo de arquivos de texto',
                        variable=self.search_content_var,
                        command=self._on_search_content_change).grid(row=1, column=1, sticky='w', padx=(14, 0))

        btn_row = ttk.Frame(card, style='Card.TFrame')
        btn_row.grid(row=2, column=0, columnspan=2, sticky='w', pady=(12, 0))
        ttk.Button(btn_row, text='🔍 Buscar', style='Accent.TButton',
                   command=self._run_search).pack(side='left')
        ttk.Button(btn_row, text='Limpar busca', style='Secondary.TButton',
                   command=self._clear_search).pack(side='left', padx=(10, 0))

    def _build_results_tree(self):
        list_header = ttk.Frame(self, style='App.TFrame')
        list_header.pack(fill='x')
        self.list_title = ttk.Label(list_header, text='', style='Section.TLabel')
        self.list_title.pack(side='left')
        ttk.Label(list_header, text='(clique com o botão direito para abrir no Explorer ou excluir)',
                  style='Subtitle.TLabel').pack(side='left', padx=(10, 0))

        tree_frame = ttk.Frame(self, style='App.TFrame')
        tree_frame.pack(fill='both', expand=True, pady=(6, 0))

        self.tree = ttk.Treeview(tree_frame, show='tree')
        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.tree.bind('<Button-3>', self._show_context_menu)
        self.tree.bind('<Double-1>', lambda e: self._open_selected())

    # --- Organização ---
    def _on_mode_change(self, event=None):
        organizer.save_org_mode(organizer.ORG_MODE_KEY_BY_LABEL[self.mode_var.get()])

    def _open_root_folder(self):
        self._safe_open(fs_utils.open_in_explorer, paths.UPLOAD_FOLDER)

    def _select_files(self):
        selected = filedialog.askopenfilenames(title='Selecione os arquivos para organizar')
        if not selected:
            return
        self._organize_paths(list(selected))

    def _select_folder(self):
        folder = filedialog.askdirectory(title='Selecione uma pasta para organizar')
        if not folder:
            return

        folder_norm = os.path.normcase(os.path.normpath(folder))
        base_norm = os.path.normcase(os.path.normpath(paths.BASE_DIR))
        if folder_norm == base_norm or folder_norm.startswith(base_norm + os.sep):
            messagebox.showwarning('Organização', 'Não é possível organizar a própria pasta do Arquithon.')
            return

        arquivos = [os.path.join(root, nome) for root, _dirs, files in os.walk(folder) for nome in files]
        if not arquivos:
            messagebox.showinfo('Organização', 'A pasta selecionada não tem arquivos.')
            return
        self._organize_paths(arquivos)

    def _focus_search(self):
        self.search_entry.focus_set()
        self.search_entry.select_range(0, 'end')

    def _organize_paths(self, selected):
        mode_key = organizer.ORG_MODE_KEY_BY_LABEL[self.mode_var.get()]
        move = self.move_var.get()

        if move and not messagebox.askyesno(
            'Mover arquivos',
            f'Isso vai remover {len(selected)} arquivo(s) do local de origem.\n\nContinuar?',
        ):
            return

        self.progress.grid()
        self.progress.configure(maximum=len(selected), value=0)

        def on_progress(feito, total):
            self.progress.configure(value=feito)
            self.update_idletasks()

        try:
            resultado = organizer.organize_files(selected, mode=mode_key, move=move, on_progress=on_progress)
        finally:
            self.progress.grid_remove()

        if not resultado.successful:
            messagebox.showwarning('Organização', 'Nenhum arquivo pôde ser organizado.')
            return

        self.last_operations = resultado.operations
        self.undo_btn.configure(state='normal')

        verbo = 'movidos' if move else 'organizados'
        msg = f'{resultado.successful} arquivo(s) {verbo} com sucesso!'
        if resultado.failed:
            acao = 'movidos' if move else 'copiados'
            msg += f'\n{resultado.failed} arquivo(s) não puderam ser {acao}.'
        self._show_categorized_view()
        if messagebox.askyesno('Organização concluída', msg + '\n\nDeseja abrir a pasta agora?'):
            self._open_root_folder()

    def _undo_last_organize(self):
        if not self.last_operations:
            return
        restaurados, falhas = organizer.undo_operations(self.last_operations)
        self.last_operations = []
        self.undo_btn.configure(state='disabled')

        msg = f'{restaurados} arquivo(s) restaurados.'
        if falhas:
            msg += f'\n{falhas} arquivo(s) não puderam ser desfeitos.'
        messagebox.showinfo('Desfazer organização', msg)
        self._show_categorized_view()

    # --- Busca ---
    def _run_search(self):
        query = self.search_var.get().strip()
        if not query:
            self._clear_search()
            return
        index = search.build_index()
        results = search.search(index, query, include_content=self.search_content_var.get())
        self._show_search_results(results, query)

    def _clear_search(self):
        self.search_var.set('')
        self._show_categorized_view()

    def _on_search_content_change(self):
        search.save_search_content_pref(self.search_content_var.get())

    # --- Árvore de resultados ---
    def _show_categorized_view(self):
        self.list_title.configure(text='Seus arquivos organizados')
        self.tree.delete(*self.tree.get_children())
        self.item_paths.clear()

        organized = organizer.scan_organized_files()
        if not organized:
            self.tree.insert('', 'end', text='Nenhum arquivo foi organizado ainda. Comece a enviar!')
            return

        for rel_path, arquivos in organized.items():
            cat_iid = self.tree.insert('', 'end', text=organizer.format_category_label(rel_path), open=True)
            self.item_paths[cat_iid] = ('pasta', os.path.join(paths.UPLOAD_FOLDER, rel_path))
            for nome in arquivos:
                file_iid = self.tree.insert(cat_iid, 'end', text=f'📄 {nome}')
                self.item_paths[file_iid] = ('arquivo', os.path.join(paths.UPLOAD_FOLDER, rel_path, nome))

    def _show_search_results(self, results, query):
        self.list_title.configure(text=f'Resultados para "{query}" ({len(results)})')
        self.tree.delete(*self.tree.get_children())
        self.item_paths.clear()

        if not results:
            self.tree.insert('', 'end', text='Nenhum arquivo encontrado.')
            return

        for item in results:
            categoria = organizer.format_category_label(os.path.dirname(item.rel_path) or item.category)
            tamanho = organizer.format_file_size(item.size)
            data = organizer.format_modified_date(item.modified)
            iid = self.tree.insert('', 'end', text=f'📄 {item.name}  —  {categoria}  ·  {tamanho}  ·  {data}')
            self.item_paths[iid] = ('arquivo', item.path)

    def _show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        info = self.item_paths.get(iid)
        if not info:
            return
        self.tree.selection_set(iid)

        self.context_menu.delete(0, 'end')
        self.context_menu.add_command(label='📂 Abrir no Explorer', command=self._open_selected)
        if info[0] == 'arquivo':
            self.context_menu.add_command(label='🗑️ Excluir arquivo', command=self._delete_selected_file)
        self.context_menu.post(event.x_root, event.y_root)

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
