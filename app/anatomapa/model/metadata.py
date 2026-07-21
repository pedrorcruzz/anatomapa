from __future__ import annotations

import json
import os

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")


def load_metadata(assets_dir: str | None = None) -> list[dict]:
    """Carrega os metadados das regiões a partir do regions.json.

    Parameters
    ----------
    assets_dir:
        Diretório contendo o regions.json. Padrão: diretório assets do pacote.

    Returns
    -------
    list[dict]
        Lista de dicionários de metadados conforme armazenado no regions.json.
    """
    base = assets_dir or _ASSETS_DIR
    path = os.path.join(base, "regions.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data["regions"]
