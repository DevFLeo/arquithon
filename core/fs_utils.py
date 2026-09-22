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
