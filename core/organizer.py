"""Organização de arquivos: para onde cada arquivo vai, e como chegar lá.

O critério de organização é plugável: cada modo é só uma função que recebe
(nome, caminho) e devolve a subpasta de destino. Adicionar um novo critério é
escrever uma função e registrá-la em `ORG_MODE_FUNCS` — o resto do app
(interface, persistência da preferência) não precisa mudar.
"""

import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime

from core import config, paths

# Extensão -> subpasta de destino no modo "por tipo de arquivo". O que não
# estiver aqui vai para "outros/<extensao>", então nenhum arquivo fica sem
# categoria.
EXTENSION_MAP = {
    # Imagens
    'png': 'imagens/png', 'jpg': 'imagens/jpg_jpeg', 'jpeg': 'imagens/jpg_jpeg',
    'gif': 'imagens/gif', 'webp': 'imagens/webp', 'bmp': 'imagens/bmp',
    'tiff': 'imagens/tiff', 'tif': 'imagens/tiff', 'ico': 'imagens/icones',
    'heic': 'imagens/heic', 'svg': 'imagens/vetoriais', 'eps': 'imagens/vetoriais',

    # Documentos de texto e PDF
    'docx': 'documentos/word', 'doc': 'documentos/word', 'odt': 'documentos/word', 'rtf': 'documentos/word',
    'txt': 'documentos/texto', 'md': 'documentos/texto',
    'pdf': 'documentos/pdf',

    # Planilhas
    'xlsx': 'documentos/planilhas', 'xls': 'documentos/planilhas',
    'ods': 'documentos/planilhas', 'csv': 'documentos/planilhas',

    # Apresentações
    'pptx': 'documentos/apresentacoes', 'ppt': 'documentos/apresentacoes', 'odp': 'documentos/apresentacoes',

    # E-books
    'epub': 'documentos/ebooks', 'mobi': 'documentos/ebooks', 'azw3': 'documentos/ebooks',

    # Áudio
    'mp3': 'multimedia/audio', 'wav': 'multimedia/audio', 'flac': 'multimedia/audio',
    'aac': 'multimedia/audio', 'ogg': 'multimedia/audio', 'm4a': 'multimedia/audio', 'wma': 'multimedia/audio',

    # Vídeo
    'mp4': 'multimedia/video', 'avi': 'multimedia/video', 'mkv': 'multimedia/video',
    'mov': 'multimedia/video', 'wmv': 'multimedia/video', 'flv': 'multimedia/video',
    'webm': 'multimedia/video', 'm4v': 'multimedia/video',

    # Compactados
    'zip': 'compactados', 'rar': 'compactados', '7z': 'compactados',
    'tar': 'compactados', 'gz': 'compactados', 'bz2': 'compactados', 'xz': 'compactados',

    # Código / desenvolvimento
    'py': 'codigo/python', 'ipynb': 'codigo/python',
    'js': 'codigo/web', 'ts': 'codigo/web', 'html': 'codigo/web', 'htm': 'codigo/web', 'css': 'codigo/web',
    'json': 'codigo/dados', 'xml': 'codigo/dados', 'yaml': 'codigo/dados', 'yml': 'codigo/dados', 'sql': 'codigo/dados',
    'java': 'codigo/outros', 'c': 'codigo/outros', 'cpp': 'codigo/outros', 'h': 'codigo/outros',
    'cs': 'codigo/outros', 'php': 'codigo/outros', 'sh': 'codigo/outros', 'bat': 'codigo/outros', 'ps1': 'codigo/outros',

    # Design / CAD
    'psd': 'design/imagem', 'ai': 'design/imagem', 'xd': 'design/imagem',
    'fig': 'design/imagem', 'sketch': 'design/imagem',
    'dwg': 'design/cad', 'dxf': 'design/cad', 'skp': 'design/cad',

    # Executáveis e instaladores
    'exe': 'executaveis', 'msi': 'executaveis', 'apk': 'executaveis', 'dmg': 'executaveis',

    # Fontes
    'ttf': 'fontes', 'otf': 'fontes', 'woff': 'fontes', 'woff2': 'fontes',
}

# Ícone por categoria de topo, só para exibição na árvore.
CATEGORY_ICONS = {
    'imagens': '🖼️', 'documentos': '📄', 'multimedia': '🎬', 'compactados': '🗜️',
    'codigo': '💻', 'design': '🎨', 'executaveis': '⚙️', 'fontes': '🔤',
    'outros': '📦', 'alfabetico': '🔤', 'tamanho': '📏',
}

MESES = [
    'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
]


def _dest_by_extension(filename: str, path: str) -> str:
    if '.' not in filename:
        return 'outros/sem_extensao'
    ext = filename.rsplit('.', 1)[1].lower()
    return EXTENSION_MAP.get(ext, f'outros/{ext}')


def _dest_by_date(filename: str, path: str) -> str:
    dt = datetime.fromtimestamp(os.path.getmtime(path))
    return f'{dt.year}/{dt.month:02d} - {MESES[dt.month - 1]}'


def _dest_by_name(filename: str, path: str) -> str:
    primeira = filename[0].upper() if filename else '#'
    if primeira.isalpha():
        return f'alfabetico/{primeira}'
    if primeira.isdigit():
        return 'alfabetico/0-9'
    return 'alfabetico/outros'


def _dest_by_size(filename: str, path: str) -> str:
    tamanho_mb = os.path.getsize(path) / (1024 * 1024)
    if tamanho_mb < 1:
        return 'tamanho/pequenos (menos de 1MB)'
    if tamanho_mb < 50:
        return 'tamanho/medios (1 a 50MB)'
    return 'tamanho/grandes (mais de 50MB)'


# Critérios de organização disponíveis na interface, em ordem de exibição.
ORG_MODES = [
    ('extensao', 'Tipo de arquivo (extensão)'),
    ('data', 'Data de modificação (ano / mês)'),
    ('nome', 'Nome do arquivo (A-Z)'),
    ('tamanho', 'Tamanho do arquivo'),
]
ORG_MODE_FUNCS = {
    'extensao': _dest_by_extension,
    'data': _dest_by_date,
    'nome': _dest_by_name,
    'tamanho': _dest_by_size,
}
ORG_MODE_LABEL_BY_KEY = {key: label for key, label in ORG_MODES}
ORG_MODE_KEY_BY_LABEL = {label: key for key, label in ORG_MODES}
DEFAULT_ORG_MODE = ORG_MODES[0][0]


def load_org_mode() -> str:
    """Recupera o último critério de organização escolhido pelo usuário."""
    mode = config.get('org_mode')
    return mode if mode in ORG_MODE_FUNCS else DEFAULT_ORG_MODE


def save_org_mode(mode: str) -> None:
    config.set('org_mode', mode)


def format_category_label(rel_path: str) -> str:
    partes = rel_path.split(os.sep)
    icone = '📅' if partes[0].isdigit() else CATEGORY_ICONS.get(partes[0], '📁')
    texto = ' › '.join(p if p.isdigit() else p.capitalize() for p in partes)
    return f'{icone} {texto}'


def format_file_size(size_bytes: int) -> str:
    """Formata um tamanho em bytes como '3.4 MB', '512 KB' etc."""
    size = float(size_bytes)
    for unidade in ('B', 'KB', 'MB'):
        if size < 1024:
            return f'{size:.0f} {unidade}' if unidade == 'B' else f'{size:.1f} {unidade}'
        size /= 1024
    return f'{size:.1f} GB'


def format_modified_date(timestamp: float) -> str:
    """Formata a data de modificação de um arquivo como 'dd/mm/aaaa'."""
    return datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y')


def delete_file(path: str) -> None:
    """Remove definitivamente um arquivo já organizado. Levanta OSError se falhar.

    Sem lixeira: quem chama (a UI) precisa confirmar com o usuário antes,
    deixando claro que não há como desfazer pelo próprio Arquithon.
    """
    os.remove(path)


def scan_organized_files() -> dict:
    """Mapeia cada subpasta já organizada para a lista de arquivos nela."""
    if not os.path.isdir(paths.UPLOAD_FOLDER):
        return {}
    organized = {}
    for root, dirs, files in os.walk(paths.UPLOAD_FOLDER):
        if not files:
            continue
        rel_path = os.path.relpath(root, paths.UPLOAD_FOLDER)
        if rel_path == '.':
            continue
        organized[rel_path] = sorted(files)
    return dict(sorted(organized.items()))


def _unique_destination(dest_dir: str, filename: str) -> str:
    """Evita sobrescrever um arquivo já organizado com o mesmo nome.

    Duas fontes diferentes podem ter um arquivo chamado igual (ex.: duas
    fotos "foto.jpg" em pastas distintas). Sem isso, a segunda cópia apagaria
    a primeira sem aviso nenhum.
    """
    candidate = os.path.join(dest_dir, filename)
    if not os.path.exists(candidate):
        return candidate

    base, ext = os.path.splitext(filename)
    n = 2
    while True:
        candidate = os.path.join(dest_dir, f'{base} ({n}){ext}')
        if not os.path.exists(candidate):
            return candidate
        n += 1


@dataclass
class Operation:
    """Uma cópia ou mudança de arquivo já concluída, para permitir desfazer."""
    source: str
    destination: str
    moved: bool


@dataclass
class OrganizeResult:
    successful: int
    failed: int
    operations: list[Operation] = field(default_factory=list)


def organize_files(file_paths, mode: str = DEFAULT_ORG_MODE, move: bool = False,
                    on_progress=None) -> OrganizeResult:
    """Copia (ou move) os arquivos para as subpastas certas.

    `on_progress`, se dado, é chamado como `on_progress(feito, total)` após
    cada arquivo processado — usado pela UI para atualizar uma barra de
    progresso sem precisar rodar isso em outra thread.
    """
    func = ORG_MODE_FUNCS.get(mode, _dest_by_extension)
    file_paths = list(file_paths)
    total = len(file_paths)
    successful, failed = 0, 0
    operations = []
    for i, path in enumerate(file_paths, start=1):
        try:
            filename = os.path.basename(path)
            destino_relativo = func(filename, path)
            destino_absoluto = os.path.join(paths.UPLOAD_FOLDER, *destino_relativo.split('/'))
            os.makedirs(destino_absoluto, exist_ok=True)
            destino_arquivo = _unique_destination(destino_absoluto, filename)
            if move:
                shutil.move(path, destino_arquivo)
            else:
                shutil.copy2(path, destino_arquivo)
            operations.append(Operation(source=path, destination=destino_arquivo, moved=move))
            successful += 1
        except OSError:
            failed += 1
        finally:
            if on_progress:
                on_progress(i, total)
    return OrganizeResult(successful, failed, operations)


def _prune_empty_dirs(start_dir: str) -> None:
    """Remove `start_dir` e seus pais vazios, sem nunca sair de dentro de uploads/."""
    current = os.path.normpath(start_dir)
    boundary = os.path.normpath(paths.UPLOAD_FOLDER)
    while current != boundary and current.startswith(boundary + os.sep):
        try:
            os.rmdir(current)
        except OSError:
            break
        current = os.path.dirname(current)


def undo_operations(operations: list[Operation]) -> tuple[int, int]:
    """Desfaz operações de organização, da mais recente para a mais antiga.

    Arquivo copiado: a cópia é apagada, o original nunca foi tocado.
    Arquivo movido: volta para o caminho de origem.
    Retorna (desfeitos, falhas).
    """
    restored, failed = 0, 0
    for op in reversed(operations):
        try:
            if op.moved:
                os.makedirs(os.path.dirname(op.source), exist_ok=True)
                shutil.move(op.destination, op.source)
            else:
                os.remove(op.destination)
        except OSError:
            failed += 1
        else:
            restored += 1
            _prune_empty_dirs(os.path.dirname(op.destination))
    return restored, failed
