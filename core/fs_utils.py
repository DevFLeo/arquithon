"""Integração com o explorador de arquivos do sistema operacional.

As funções aqui levantam `OSError` quando algo falha; quem chama (a camada de
UI) decide como avisar o usuário. Isso mantém este módulo livre de Tkinter e
testável sem abrir janela nenhuma.
"""

import os
import subprocess


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
    """Expande uma lista de caminhos em arquivos; pastas viram seu conteúdo.

    Serve tanto para o botão "Selecionar Pasta" quanto para o arrastar e
    soltar, onde o usuário pode largar arquivos e pastas na mesma leva. O que
    não existir mais (um atalho quebrado, por exemplo) é ignorado em silêncio,
    já que quem chama só quer a lista do que dá para organizar.
    """
    arquivos = []
    for entry in entries:
        if os.path.isdir(entry):
            for root, _dirs, files in os.walk(entry):
                arquivos.extend(os.path.join(root, nome) for nome in sorted(files))
        elif os.path.isfile(entry):
            arquivos.append(entry)
    return arquivos
