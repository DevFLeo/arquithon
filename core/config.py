"""Persistência simples das preferências do usuário em `config.json`.

Um único arquivo, sem banco de dados: o app tem uma preferência (o critério
de organização escolhido), então um dicionário salvo em disco resolve sem
complexidade extra. Se um dia surgirem mais preferências, basta guardar
outras chaves no mesmo dicionário.
"""

import json

from core import paths


def load() -> dict:
    try:
        with open(paths.CONFIG_PATH, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save(data: dict) -> None:
    with open(paths.CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def get(key: str, default=None):
    return load().get(key, default)


def set(key: str, value) -> None:
    data = load()
    data[key] = value
    save(data)
