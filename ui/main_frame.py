"""Tela única do app: organizar arquivos, buscar os já organizados, navegar."""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core import fs_utils, importer, organizer, paths, search
from ui import dnd, icon, result_dialog, settings_dialog, styles


MAX_UNDO = 5  # quantas organizações seguidas dá para desfazer, uma de cada vez


class MainFrame(ttk.Frame):
    def __init__(self, app):
        super().__init__(app, style='App.TFrame')
        self.item_paths = {}  # iid da árvore -> ('pasta' | 'arquivo', caminho absoluto)
        self.undo_stack = []  # levas de Operation, da mais antiga à mais recente (até MAX_UNDO)
        self.organizing = False  # um drop pode chegar com um diálogo aberto; um de cada vez
        self._plain = []  # (widget, fundo, cor, delta, peso): rótulos Tk clássicos a recolorir

        self._build_sidebar()
        main = ttk.Frame(self, style='App.TFrame', padding=(24, 20, 24, 16))
        main.pack(side='left', fill='both', expand=True)
        self._build_drop_area(main)
        self._build_search_bar(main)
        self._build_results_tree(main)

        self._show_categorized_view()

        # Sem suporte a arrastar e soltar (outro sistema, ou API indisponível),
        # a área de soltar some em vez de ficar prometendo o que não funciona.
        if not dnd.enable_file_drop(app, self._on_files_dropped):
            self.drop_zone.pack_forget()

        app.bind('<Control-o>', lambda e: self._select_files())
        app.bind('<Control-f>', lambda e: self._focus_search())

    # --- Montagem da interface ---
    def _build_sidebar(self):
        side = ttk.Frame(self, style='Sidebar.TFrame', padding=(16, 20))
        side.pack(side='left', fill='y')
        ttk.Frame(self, style='Border.TFrame', width=1).pack(side='left', fill='y')

        marca = ttk.Frame(side, style='Sidebar.TFrame')
        marca.pack(fill='x', pady=(0, 22))
        self._logo_img = icon.photo(self, 40)  # guardar referência: o Tk não segura a imagem
        ttk.Label(marca, image=self._logo_img, style='Sidebar.TLabel').pack(side='left', padx=(0, 10))
        textos = ttk.Frame(marca, style='Sidebar.TFrame')
        textos.pack(side='left')
        ttk.Label(textos, text='Arquithon', style='SidebarTitle.TLabel').pack(anchor='w')
        ttk.Label(textos, text='Arquivista digital · v2.1', style='SidebarMuted.TLabel').pack(anchor='w')

        ttk.Button(side, text='+   Escolher arquivos', style='NavPrimary.TButton',
                   command=self._select_files).pack(fill='x')
        ttk.Button(side, text='Escolher uma pasta', style='Nav.TButton',
                   command=self._select_folder).pack(fill='x', pady=(8, 0))
        ttk.Button(side, text='Abrir no Explorer', style='Nav.TButton',
                   command=self._open_root_folder).pack(fill='x')
        self.undo_btn = ttk.Button(side, text='Desfazer (nada a desfazer)', style='Nav.TButton',
                                    command=self._undo_last_organize, state='disabled')
        self.undo_btn.pack(fill='x')

        ttk.Separator(side).pack(fill='x', pady=18)
        ttk.Label(side, text='COMO ORGANIZAR', style='SidebarMuted.TLabel').pack(anchor='w', pady=(0, 6))
        self.mode_var = tk.StringVar(value=organizer.ORG_MODE_LABEL_BY_KEY[organizer.load_org_mode()])
        mode_combo = ttk.Combobox(
            side, textvariable=self.mode_var, state='readonly', width=24,
            values=[label for _, label in organizer.ORG_MODES],
        )
        mode_combo.pack(fill='x')
        mode_combo.bind('<<ComboboxSelected>>', self._on_mode_change)

        self.move_var = tk.BooleanVar(value=organizer.load_move_default())
        ttk.Checkbutton(side, text='Mover em vez de copiar', style='Sidebar.TCheckbutton',
                        variable=self.move_var).pack(anchor='w', pady=(10, 0))
        ttk.Label(side, text='Copiar é o modo seguro: o original\nfica onde está.',
                  style='SidebarMuted.TLabel', justify='left').pack(anchor='w', pady=(2, 0))

        # Rodapé: números rápidos e configurações (empacotados de baixo para cima).
        ttk.Button(side, text='Configurações', style='Nav.TButton',
                   command=self._open_settings).pack(side='bottom', fill='x')
        ttk.Button(side, text='⇄   Receber de outro Arquithon', style='Secondary.TButton',
                   command=self._import_repository).pack(side='bottom', fill='x', pady=(0, 8))
        ttk.Separator(side).pack(side='bottom', fill='x', pady=(0, 14))
        self.stats_lbl = ttk.Label(side, text='', style='SidebarMuted.TLabel', justify='left')
        self.stats_lbl.pack(side='bottom', anchor='w', pady=(0, 10))
        self.stats_num = ttk.Label(side, text='0', style='Stat.TLabel')
        self.stats_num.pack(side='bottom', anchor='w')
        self.progress = ttk.Progressbar(side, mode='determinate')

    def _build_drop_area(self, parent):
        self._section(parent, 'PASSO 1', 'Organizar arquivos')
        self.drop_zone = tk.Frame(parent, highlightthickness=1, cursor='hand2', pady=22)
        self.drop_zone.pack(fill='x', pady=(8, 24))
        self._drop_img = icon.photo(self, 48)
        img = tk.Label(self.drop_zone, image=self._drop_img, cursor='hand2')
        img.role = 'img'
        img.pack(pady=(0, 8))
        for papel, texto in (('title', 'Arraste arquivos ou pastas para cá'),
                             ('sub', 'ou clique aqui para escolher no computador')):
            rotulo = tk.Label(self.drop_zone, text=texto, cursor='hand2')
            rotulo.role = papel
            rotulo.pack()
        styles.style_drop_zone(self.drop_zone)
        for w in (self.drop_zone, *self.drop_zone.winfo_children()):
            w.bind('<Button-1>', lambda e: self._select_files())
            w.bind('<Enter>', lambda e: styles.style_drop_zone(self.drop_zone, hover=True))
            w.bind('<Leave>', lambda e: styles.style_drop_zone(self.drop_zone))

    def _section(self, parent, passo, titulo):
        ttk.Label(parent, text=passo, style='Step.TLabel').pack(anchor='w')
        ttk.Label(parent, text=titulo, style='Section.TLabel').pack(anchor='w', pady=(2, 0))

    def _build_search_bar(self, parent):
        self._section(parent, 'PASSO 2', 'Encontrar um arquivo')
        row = ttk.Frame(parent, style='App.TFrame')
        row.pack(fill='x', pady=(6, 0))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(row, textvariable=self.search_var)
        self.search_entry.pack(side='left', fill='x', expand=True)
        self.search_entry.bind('<Return>', lambda e: self._run_search())
        self.search_entry.bind('<Escape>', lambda e: self._clear_search())

        # Dica dentro do campo vazio (o Entry do Tk não tem placeholder próprio).
        self.search_hint = tk.Label(self.search_entry, text='Digite parte do nome do arquivo…   (Ctrl+F)')
        self._plain_add(self.search_hint, 'field', 'muted')
        self.search_hint.bind('<Button-1>', lambda e: self._focus_search())
        self.search_var.trace_add('write', lambda *a: self._sync_hint())
        self.search_entry.bind('<FocusIn>', lambda e: self._sync_hint(), add='+')
        self.search_entry.bind('<FocusOut>', lambda e: self._sync_hint(), add='+')
        self.after_idle(self._sync_hint)
        ttk.Button(row, text='🔍 Buscar', style='Accent.TButton',
                   command=self._run_search).pack(side='left', padx=(10, 0))
        ttk.Button(row, text='Limpar', style='Secondary.TButton',
                   command=self._clear_search).pack(side='left', padx=(8, 0))

        self.search_content_var = tk.BooleanVar(value=search.load_search_content_pref())
        ttk.Checkbutton(parent, text='Procurar também dentro de arquivos de texto',
                        style='App.TCheckbutton', variable=self.search_content_var,
                        command=self._on_search_content_change).pack(anchor='w', pady=(8, 14))

    def _build_results_tree(self, parent):
        list_header = ttk.Frame(parent, style='App.TFrame')
        list_header.pack(fill='x')
        self.list_title = ttk.Label(list_header, text='', style='Section.TLabel')
        self.list_title.pack(side='left')
        ttk.Label(list_header, text='Duplo clique abre · botão direito para mais opções',
                  style='Hint.TLabel').pack(side='right')

        tree_frame = ttk.Frame(parent, style='App.TFrame')
        tree_frame.pack(fill='both', expand=True, pady=(8, 0))

        self.tree = ttk.Treeview(tree_frame, columns=('categoria', 'tamanho', 'data'), show='tree headings')
        self.tree.heading('#0', text='Nome', anchor='w')
        self.tree.heading('categoria', text='Pasta', anchor='w')
        self.tree.column('categoria', anchor='w')
        self.tree.heading('tamanho', text='Tamanho', anchor='e')
        self.tree.heading('data', text='Modificado', anchor='e')
        self.tree.column('#0', width=300, stretch=True)
        self.tree.column('categoria', width=150, stretch=False)
        self.tree.column('tamanho', width=90, stretch=False, anchor='e')
        self.tree.column('data', width=90, stretch=False, anchor='e')
        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        self._empty_img = icon.photo(self, 40)
        self.empty_lbl = tk.Label(tree_frame, text='', justify='center', image=self._empty_img,
                                  compound='top', pady=8)
        self._plain_add(self.empty_lbl, 'card', 'muted', 1)
        self._style_tree_tags()

        self.context_menu = tk.Menu(self.tree, tearoff=0)
        styles.style_menu(self.context_menu)
        self.tree.bind('<Button-3>', self._show_context_menu)
        self.tree.bind('<Double-1>', lambda e: self._open_selected())
        self.tree.bind('<Button-1>', self._on_tree_click)

    # --- Configurações ---
    def _open_settings(self):
        if settings_dialog.show(self.winfo_toplevel()):
            self._apply_appearance()

    def _apply_appearance(self):
        """Redesenha a tela com o tema e o tamanho de fonte escolhidos.

        Os widgets ttk seguem os estilos nomeados sozinhos; só os dois que não
        são ttk (a área de soltar e o menu de contexto) precisam ser avisados.
        """
        styles.apply(self.winfo_toplevel())
        styles.style_drop_zone(self.drop_zone)
        styles.style_menu(self.context_menu)
        for args in self._plain:
            styles.style_plain(*args)
        self._style_tree_tags()

    def _plain_add(self, widget, bg, fg, delta=0, weight='normal'):
        self._plain.append((widget, bg, fg, delta, weight))
        styles.style_plain(widget, bg, fg, delta, weight)

    def _style_tree_tags(self):
        self.tree.tag_configure('pasta', font=(styles.FAMILY, styles.BASE_SIZE, 'bold'))
        self.tree.tag_configure('meta', foreground=styles.COLORS['muted'])

    def _sync_hint(self):
        vazio = not self.search_var.get()
        if vazio and self.focus_get() is not self.search_entry:
            self.search_hint.place(x=10, rely=0.5, anchor='w')
        else:
            self.search_hint.place_forget()

    def _show_empty(self, texto):
        self.empty_lbl.configure(text=texto)
        self.empty_lbl.place(relx=0.5, rely=0.4, anchor='center')

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
        self._organize_entries([folder])

    def _on_files_dropped(self, dropped):
        """Recebe o que o usuário soltou na janela (arquivos e/ou pastas).

        O Windows entrega o drop mesmo com um diálogo nosso aberto, que é o
        único caminho por onde duas organizações começariam ao mesmo tempo:
        nesse caso o drop é ignorado, e o usuário arrasta de novo depois.
        """
        if self.organizing:
            return
        self.winfo_toplevel().focus_force()
        self._organize_entries(dropped)

    def _organize_entries(self, entries):
        """Organiza uma leva de caminhos, abrindo as pastas recursivamente."""
        if any(self._is_inside_app(entry) for entry in entries):
            messagebox.showwarning('Organização',
                                   'Não é possível organizar arquivos de dentro da própria pasta do Arquithon.')
            return

        arquivos = fs_utils.collect_files(entries)
        if not arquivos:
            messagebox.showinfo('Organização', 'Nenhum arquivo encontrado para organizar.')
            return
        self._organize_paths(arquivos)

    @staticmethod
    def _is_inside_app(path):
        """O Arquithon não organiza a si mesmo: evita copiar uploads/ dentro de uploads/."""
        alvo = os.path.normcase(os.path.normpath(path))
        base = os.path.normcase(os.path.normpath(paths.BASE_DIR))
        return alvo == base or alvo.startswith(base + os.sep)

    def _focus_search(self):
        self.search_entry.focus_set()
        self.search_entry.select_range(0, 'end')

    def _organize_paths(self, selected):
        self.organizing = True
        try:
            mode_key = organizer.ORG_MODE_KEY_BY_LABEL[self.mode_var.get()]
            move = self.move_var.get()

            if move and not messagebox.askyesno(
                'Mover arquivos',
                f'Isso vai remover {len(selected)} arquivo(s) do local de origem.\n\nContinuar?',
            ):
                return

            self.progress.pack(fill='x', pady=(0, 10), before=self.stats_num)
            self.progress.configure(maximum=len(selected), value=0)

            def on_progress(feito, total):
                self.progress.configure(value=feito)
                self.update_idletasks()

            try:
                resultado = organizer.organize_files(selected, mode=mode_key, move=move, on_progress=on_progress)
            finally:
                self.progress.pack_forget()

            if not resultado.successful:
                messagebox.showwarning('Organização', 'Nenhum arquivo pôde ser organizado.')
                return

            self.undo_stack.append(resultado.operations)
            del self.undo_stack[:-MAX_UNDO]
            self._refresh_undo_btn()
            self._show_categorized_view()

            escolha = result_dialog.show(self.winfo_toplevel(), resultado, move)
            if escolha == 'reverter':
                self._undo_last_organize()
            elif escolha == 'abrir':
                self._open_root_folder()
        finally:
            self.organizing = False

    def _import_repository(self):
        """Copia para cá tudo o que outro Arquithon já organizou."""
        if self.organizing:
            return
        pasta = filedialog.askdirectory(
            title='Escolha a pasta do outro Arquithon (onde fica o .exe ou a pasta uploads)')
        if not pasta:
            return
        try:
            origem = importer.resolve_source(pasta)
        except importer.ImportError_ as erro:
            messagebox.showwarning('Receber de outro Arquithon', str(erro))
            return
        total = len(importer.list_files(origem))
        if not total:
            messagebox.showinfo('Receber de outro Arquithon', 'Essa pasta não tem nenhum arquivo para receber.')
            return
        if not messagebox.askyesno(
            'Receber de outro Arquithon',
            f'Copiar {total} arquivo(s) de:\n{origem}\n\nOs originais não serão alterados.\n'
            'Arquivos idênticos aos que você já tem serão ignorados.'):
            return

        self.organizing = True
        self.progress.pack(fill='x', pady=(0, 10), before=self.stats_num)
        self.progress.configure(maximum=total, value=0)

        def on_progress(feito, _total):
            self.progress.configure(value=feito)
            self.update_idletasks()

        try:
            resultado = importer.import_repository(pasta, on_progress=on_progress)
        except importer.ImportError_ as erro:
            messagebox.showwarning('Receber de outro Arquithon', str(erro))
            return
        finally:
            self.progress.pack_forget()
            self.organizing = False

        if resultado.operations:
            self.undo_stack.append(resultado.operations)
            del self.undo_stack[:-MAX_UNDO]
            self._refresh_undo_btn()
        self._clear_search()

        msg = f'{resultado.copied} arquivo(s) recebido(s).'
        if resultado.duplicates:
            msg += f'\n{resultado.duplicates} já existiam aqui e foram ignorados.'
        if resultado.failed:
            msg += f'\n{resultado.failed} não puderam ser copiados.'
        if resultado.operations:
            msg += '\n\nSe não era isso, use "Desfazer última".'
        messagebox.showinfo('Receber de outro Arquithon', msg)

    def _refresh_undo_btn(self):
        n = len(self.undo_stack)
        if n:
            self.undo_btn.configure(state='normal', text=f'↶  Desfazer última  ({n} disponível{"is" if n > 1 else ""})')
        else:
            self.undo_btn.configure(state='disabled', text='Desfazer (nada a desfazer)')

    def _undo_last_organize(self):
        if not self.undo_stack:
            return
        restaurados, falhas = organizer.undo_operations(self.undo_stack.pop())
        self._refresh_undo_btn()

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
        total = sum(len(f) for f in organized.values())
        self.stats_num.configure(text=str(total))
        self.stats_lbl.configure(text=f'arquivo(s) organizado(s)\nem {len(organized)} pasta(s)')
        if not organized:
            self._show_empty('Nenhum arquivo organizado ainda.\nArraste arquivos para a caixa lá em cima para começar.')
            return
        self.empty_lbl.place_forget()

        for rel_path, arquivos in organized.items():
            cat_iid = self.tree.insert('', 'end', text=organizer.format_category_label(rel_path),
                                       values=('', f'{len(arquivos)} item(ns)', ''), open=True, tags=('pasta',))
            self.item_paths[cat_iid] = ('pasta', os.path.join(paths.UPLOAD_FOLDER, rel_path))
            for nome in arquivos:
                caminho = os.path.join(paths.UPLOAD_FOLDER, rel_path, nome)
                try:
                    tamanho = organizer.format_file_size(os.path.getsize(caminho))
                    data = organizer.format_modified_date(os.path.getmtime(caminho))
                except OSError:
                    tamanho = data = ''
                file_iid = self.tree.insert(cat_iid, 'end', text=f'📄 {nome}', values=('', tamanho, data))
                self.item_paths[file_iid] = ('arquivo', caminho)

    def _show_search_results(self, results, query):
        self.list_title.configure(text=f'Resultados para "{query}" ({len(results)})')
        self.tree.delete(*self.tree.get_children())
        self.item_paths.clear()

        if not results:
            self._show_empty(f'Nada encontrado para "{query}".\nTente outra palavra ou clique em Limpar.')
            return
        self.empty_lbl.place_forget()

        for item in results:
            categoria = organizer.format_category_label(os.path.dirname(item.rel_path) or item.category)
            iid = self.tree.insert('', 'end', text=f'📄 {item.name}', values=(
                categoria, organizer.format_file_size(item.size), organizer.format_modified_date(item.modified)))
            self.item_paths[iid] = ('arquivo', item.path)

    def _on_tree_click(self, event):
        """Clicar em qualquer parte da linha de uma categoria expande/recolhe ela.

        Por padrão o Treeview só reage à setinha de expandir; isso obriga a
        mirar num alvo de poucos pixels. Deixa o clique na setinha com o
        comportamento padrão (para não abrir e fechar de novo) e trata o
        resto da linha aqui, sem interferir na seleção normal do clique.
        """
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
