from __future__ import annotations

import io
import json


def from_json(
    source: str | io.TextIOBase,
    region_key: str = "region",
    value_key: str = "value",
    encoding: str = "utf-8",
) -> list[tuple[str, float]]:
    """Parseia um arquivo ou string JSON em pares (rótulo, valor).

    Aceita dois formatos:
    - Objeto: {"region_id": valor, ...}
    - Array: [{"region": "...", "value": ...}, ...]

    Parameters
    ----------
    source:
        Caminho do arquivo, string JSON ou objeto de texto tipo arquivo.
    region_key:
        Chave do rótulo da região no formato array de objetos.
    value_key:
        Chave do valor numérico no formato array de objetos.
    encoding:
        Codificação quando source é um caminho de arquivo.

    Returns
    -------
    list[tuple[str, float]]
        Lista de pares (rótulo, valor).
    """
    if isinstance(source, str):
        stripped = source.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            data = json.loads(stripped)
        else:
            with open(source, encoding=encoding) as fh:
                data = json.load(fh)
    else:
        data = json.load(source)

    if isinstance(data, dict):
        return [(str(k), float(v)) for k, v in data.items()]

    if isinstance(data, list):
        return [(str(item[region_key]), float(item[value_key])) for item in data]

    raise ValueError(f"Unsupported JSON structure: {type(data)}")
