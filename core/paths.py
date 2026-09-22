"""Caminhos usados pelo app.

Tudo fica sempre ao lado do executável (build congelado) ou ao lado do
projeto (rodando via `python app.py`), nunca em pastas de sistema — assim o
usuário pode mover o app inteiro para qualquer lugar sem perder nada.
"""

import os
import sys

IS_FROZEN = getattr(sys, 'frozen', False)

if IS_FROZEN:
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
