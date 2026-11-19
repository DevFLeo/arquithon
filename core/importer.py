"""Receber o repositório (a pasta uploads/) de outro Arquithon.

Copia tudo o que outro Arquithon já organizou para o nosso uploads/,
mantendo as mesmas subpastas. Nada na origem é alterado. Arquivo idêntico
que já existe aqui é pulado; arquivo diferente com o mesmo nome ganha um
sufixo " (2)", como na organização normal. Cada cópia vira uma Operation,
então o "Desfazer" do app também desfaz o recebimento.
"""

import filecmp
import os
import shutil
from dataclasses import dataclass, field

from core import paths
from core.organizer import Operation, _unique_destination


class ImportError_(ValueError):
    """Pasta escolhida não serve como origem (mensagem pronta para o usuário)."""


@dataclass
class ImportResult:
    copied: int = 0
    duplicates: int = 0
    failed: int = 0
    operations: list = field(default_factory=list)


def _norm(path):
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def resolve_source(folder: str) -> str:
    """Aceita a pasta do outro Arquithon (que contém uploads/) ou o próprio uploads/."""
    if not os.path.isdir(folder):
        raise ImportError_('A pasta escolhida não existe.')
    candidata = os.path.join(folder, 'uploads')
    origem = candidata if os.path.isdir(candidata) else folder

    nossa = _norm(paths.UPLOAD_FOLDER)
    alvo = _norm(origem)
    if alvo == nossa or alvo.startswith(nossa + os.sep) or nossa.startswith(alvo + os.sep):
        raise ImportError_('Essa é a pasta deste próprio Arquithon. Escolha a pasta de outro.')
    return origem


def list_files(source_root: str) -> list:
    """Caminhos relativos de todos os arquivos dentro da origem."""
    arquivos = []
    for root, _dirs, files in os.walk(source_root):
        for nome in files:
            arquivos.append(os.path.relpath(os.path.join(root, nome), source_root))
    return sorted(arquivos)


def import_repository(folder: str, on_progress=None) -> ImportResult:
    origem = resolve_source(folder)
    relativos = list_files(origem)
    resultado = ImportResult()
    total = len(relativos)

    for i, rel in enumerate(relativos, 1):
        src = os.path.join(origem, rel)
        dest_dir = os.path.join(paths.UPLOAD_FOLDER, os.path.dirname(rel))
        existente = os.path.join(dest_dir, os.path.basename(rel))
        try:
            if os.path.isfile(existente) and filecmp.cmp(src, existente, shallow=False):
                resultado.duplicates += 1
            else:
                os.makedirs(dest_dir, exist_ok=True)
                dest = _unique_destination(dest_dir, os.path.basename(rel))
                shutil.copy2(src, dest)
                resultado.operations.append(Operation(source=src, destination=dest, moved=False))
                resultado.copied += 1
        except OSError:
            resultado.failed += 1
        if on_progress:
            on_progress(i, total)
    return resultado
