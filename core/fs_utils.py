"""Integração com o explorador de arquivos e detecção de projetos de código em O(1).

As funções aqui levantam `OSError` quando algo falha; quem chama (a camada de
UI) decide como avisar o usuário. Isso mantém este módulo livre de Tkinter e
testável sem abrir janela nenhuma.
"""

import os
import subprocess

# Marcadores de manifesto/repositório que identificam imediatamente a raiz de um
# projeto de código em tempo O(1) via hash-set lookup.
PROJECT_MARKERS = frozenset({
    '.git', '.svn', '.hg', '.idea', '.vscode',
    'package.json', 'tsconfig.json', 'pyproject.toml', 'requirements.txt',
    'setup.py', 'setup.cfg', 'pipfile', 'poetry.lock', 'manage.py',
    'cargo.toml', 'go.mod', 'pom.xml', 'build.gradle', 'makefile',
    'cmakelists.txt', 'dockerfile', 'docker-compose.yml', 'composer.json',
    'gemfile', 'vite.config.ts', 'vite.config.js', 'next.config.js',
})

PROJECT_MARKER_SUFFIXES = ('.sln', '.csproj', '.fsproj', '.vbproj', '.xcodeproj', '.spec')

# Extensões de código-fonte que caracterizam um diretório de desenvolvimento.
CODE_EXTENSIONS = frozenset({
    'py', 'ipynb', 'js', 'ts', 'jsx', 'tsx', 'html', 'htm', 'css', 'scss',
    'java', 'c', 'cpp', 'h', 'hpp', 'cs', 'go', 'rs', 'php', 'rb', 'swift',
    'kt', 'kts', 'dart', 'lua', 'r', 'sql', 'sh', 'bat', 'ps1', 'vue', 'svelte',
})

# Subpastas típicas da estrutura de um projeto de software.
SOURCE_DIR_NAMES = frozenset({
    'src', 'core', 'ui', 'app', 'lib', 'pkg', 'cmd', 'components',
    'controllers', 'models', 'views', 'services', 'utils', 'tests', 'test',
})

# Pastas pesadas ignoradas durante a inspeção rasa para garantir tempo constante.
IGNORED_HEAVY_DIRS = frozenset({
    'node_modules', '.git', '.venv', 'venv', 'env', '__pycache__',
    'dist', 'build', 'target', '.next', '.nuxt', 'vendor',
})

MAX_SHALLOW_SCAN = 64


def is_code_project(folder_path: str) -> bool:
    """Detecta em tempo constante O(1) (Bounded Shallow Scan com Early-Exit) se
    uma pasta é um projeto de código que deve ser mantido inteiro sem desmontar.

    Algoritmo em 2 níveis sobre uma única chamada `os.scandir`:
    1. Tier 1 (O(1) Hash-Set Signature): verifica se há qualquer arquivo de
       manifesto (package.json, requirements.txt, pyproject.toml, .git, .sln...).
       Retorna True no primeiro acerto (short-circuit).
    2. Tier 2 (Densidade Rasa de Código): conta arquivos de código na raiz
       (limitado às primeiras 64 entradas) e verifica subpastas estruturais
       (src/, core/, ui/, app/, tests/). Se houver >= 2 arquivos de código, ou
       1 arquivo de código + subpasta estrutural, ou código dentro de src/core,
       classifica como projeto sem jamais percorrer árvores pesadas como node_modules.
    """
    if not os.path.isdir(folder_path):
        return False

    code_files_count = 0
    candidate_subdirs = []

    try:
        with os.scandir(folder_path) as it:
            for idx, entry in enumerate(it):
                name_lower = entry.name.lower()

                # Tier 1: Manifesto ou pasta de controle de versão -> Early Exit O(1)
                if name_lower in PROJECT_MARKERS or name_lower.endswith(PROJECT_MARKER_SUFFIXES):
                    return True

                try:
                    is_dir = entry.is_dir(follow_symlinks=False)
                except OSError:
                    is_dir = False

                if is_dir:
                    if name_lower in SOURCE_DIR_NAMES:
                        candidate_subdirs.append(entry.path)
                        if code_files_count >= 1:
                            return True
                else:
                    if '.' in name_lower:
                        ext = name_lower.rsplit('.', 1)[1]
                        if ext in CODE_EXTENSIONS:
                            code_files_count += 1
                            if code_files_count >= 2 or candidate_subdirs:
                                return True

                if idx >= MAX_SHALLOW_SCAN:
                    break
    except OSError:
        return False

    # Se não havia código solto na raiz, mas existe pasta estrutural (ex.: src/),
    # faz um único peek raso limitado na primeira subpasta estrutural.
    for subdir in candidate_subdirs[:2]:
        try:
            with os.scandir(subdir) as sub_it:
                for sub_idx, sub_entry in enumerate(sub_it):
                    sub_name = sub_entry.name.lower()
                    if '.' in sub_name and sub_name.rsplit('.', 1)[1] in CODE_EXTENSIONS:
                        return True
                    if sub_idx >= 24:
                        break
        except OSError:
            continue

    return False


def open_in_explorer(path: str) -> None:
    """Abre uma pasta no explorador de arquivos, criando-a se preciso."""
    os.makedirs(path, exist_ok=True)
    if os.name == 'nt':
        os.startfile(path)  # noqa: S606 - caminho controlado pela própria aplicação
    else:
        subprocess.Popen(['xdg-open', path])


def open_and_select_file(path: str) -> None:
    """Abre a pasta do arquivo já com ele selecionado (Windows Explorer)."""
    if os.name == 'nt':
        subprocess.run(['explorer', '/select,', os.path.normpath(path)])
    else:
        subprocess.Popen(['xdg-open', os.path.dirname(path)])


def collect_files(entries) -> list:
    """Expande uma lista de caminhos em itens organizáveis.

    - Pastas comuns são expandidas recursivamente em seus arquivos.
    - Pastas identificadas como Projeto de Código (`is_code_project`) são
      preservadas inteiras como um único item de diretório na lista, evitando
      desmontar a estrutura interna do projeto.
    """
    itens = []
    for entry in entries:
        if os.path.isdir(entry):
            if is_code_project(entry):
                itens.append(os.path.normpath(entry))
                continue

            for root, dirs, files in os.walk(entry):
                # Verifica se alguma subpasta dentro da pasta selecionada é um
                # projeto de código; se for, preserva a subpasta inteira e poda
                # o os.walk (`dirs[:]`) para não entrar nela!
                keep_dirs = []
                for d in sorted(dirs):
                    if d.lower() in IGNORED_HEAVY_DIRS:
                        continue
                    sub_path = os.path.join(root, d)
                    if is_code_project(sub_path):
                        itens.append(os.path.normpath(sub_path))
                    else:
                        keep_dirs.append(d)
                dirs[:] = keep_dirs
                itens.extend(os.path.join(root, nome) for nome in sorted(files))
        elif os.path.isfile(entry):
            itens.append(entry)
    return itens
