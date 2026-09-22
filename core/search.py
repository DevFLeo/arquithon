"""Motor de busca/indexação dos arquivos já organizados.

Varre `uploads/` e monta um índice em memória com nome, categoria, tamanho,
data e, para arquivos de texto, um trecho do conteúdo — tudo com a biblioteca
padrão, sem leitores de PDF/DOCX externos. Formatos binários continuam
pesquisáveis por nome; o conteúdo só é indexado para extensões de texto puro.

O índice é reconstruído a cada busca em vez de mantido incrementalmente: para
o volume de arquivos de um arquivista pessoal isso é rápido o bastante, e
evita toda a complexidade (e os bugs) de invalidar um cache toda vez que um
arquivo é adicionado, movido ou apagado por fora do app.
"""

import os
from dataclasses import dataclass, field

from core import config, paths

# Extensões cujo conteúdo vale a pena ler como texto simples.
TEXT_EXTENSIONS = {
    'txt', 'md', 'csv', 'json', 'xml', 'yaml', 'yml', 'html', 'htm', 'css',
    'js', 'ts', 'py', 'java', 'c', 'cpp', 'h', 'cs', 'php', 'sh', 'bat',
    'ps1', 'sql', 'ini', 'log',
}
SNIPPET_CHARS = 2000  # quanto do arquivo é lido para a busca por conteúdo


@dataclass
class IndexedFile:
    name: str
    path: str        # caminho absoluto no disco
    rel_path: str     # caminho relativo dentro de uploads/
    category: str     # pasta de categoria (topo da árvore)
    extension: str
    size: int
    modified: float
    snippet: str = field(default='', repr=False)  # trecho do conteúdo, se for texto


def _read_snippet(path: str) -> str:
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            return f.read(SNIPPET_CHARS)
    except OSError:
        return ''


def build_index() -> list[IndexedFile]:
    """Varre uploads/ e devolve um índice com todos os arquivos organizados."""
    if not os.path.isdir(paths.UPLOAD_FOLDER):
        return []

    index = []
    for root, _dirs, files in os.walk(paths.UPLOAD_FOLDER):
        for filename in files:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, paths.UPLOAD_FOLDER)
            extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            try:
                stat = os.stat(full_path)
            except OSError:
                continue

            index.append(IndexedFile(
                name=filename,
                path=full_path,
                rel_path=rel_path,
                category=rel_path.split(os.sep)[0],
                extension=extension,
                size=stat.st_size,
                modified=stat.st_mtime,
                snippet=_read_snippet(full_path) if extension in TEXT_EXTENSIONS else '',
            ))
    return index


def _searchable_folder(item: IndexedFile) -> str:
    """A pasta do arquivo dentro de uploads/, em texto buscável.

    A barra vira espaço para "imagens png" casar tanto com quem digita
    "imagens" quanto com "png" — e para o separador do sistema não mudar o
    resultado da busca.
    """
    return os.path.dirname(item.rel_path).lower().replace(os.sep, ' ').replace('/', ' ')


def search(index: list[IndexedFile], query: str, include_content: bool = True) -> list[IndexedFile]:
    """Filtra o índice pelo nome do arquivo, pela pasta e, opcionalmente, pelo conteúdo.

    A ordem da saída é a ordem da confiança: quem casou pelo nome vem antes de
    quem casou só pela pasta, e o conteúdo vem por último. Sem isso, procurar
    por "contrato" deixaria o arquivo chamado contrato.pdf atrás de uma
    categoria inteira que por acaso tem essa palavra no caminho.
    """
    query = query.strip().lower().replace(os.sep, ' ').replace('/', ' ')
    if not query:
        return list(index)

    por_nome, por_pasta, por_conteudo = [], [], []
    for item in index:
        if query in item.name.lower():
            por_nome.append(item)
        elif query in _searchable_folder(item):
            por_pasta.append(item)
        elif include_content and item.snippet and query in item.snippet.lower():
            por_conteudo.append(item)
    return por_nome + por_pasta + por_conteudo


def load_search_content_pref() -> bool:
    """Recupera a última preferência de 'buscar também no conteúdo'."""
    return bool(config.get('search_content', True))


def save_search_content_pref(value: bool) -> None:
    config.set('search_content', value)
