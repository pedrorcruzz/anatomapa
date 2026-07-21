from __future__ import annotations

from typing import Any


def from_dict(data: dict[str, float | int]) -> list[tuple[str, float]]:
    """Converte um dicionário {rótulo: valor} em lista de pares (rótulo, valor).

    Parameters
    ----------
    data:
        Mapeamento do rótulo da região para valor numérico.

    Returns
    -------
    list[tuple[str, float]]
        Lista estável de pares (rótulo, valor) (ordem de inserção do dict).
    """
    return [(str(k), float(v)) for k, v in data.items()]


def from_records(
    records: Any,
    region_col: str,
    value_col: str,
) -> list[tuple[str, float]]:
    """Converte uma sequência de objetos tipo registro em pares (rótulo, valor).

    Funciona com qualquer objeto que suporte iteração e acesso por item ou
    atributo, incluindo dicts, namedtuples, dataclasses e DataFrames do pandas
    (duck typing, pandas nunca é importado).

    Parameters
    ----------
    records:
        Iterável de objetos tipo registro.
    region_col:
        Nome do campo que contém o rótulo da região.
    value_col:
        Nome do campo que contém o valor numérico.

    Returns
    -------
    list[tuple[str, float]]
        Lista de pares (rótulo, valor) na ordem de entrada.
    """
    result: list[tuple[str, float]] = []
    for row in records:
        if isinstance(row, dict):
            label = str(row[region_col])
            value = float(row[value_col])
        else:
            # Suporta namedtuple, dataclass e pandas Row via __getattr__
            try:
                label = str(getattr(row, region_col))
                value = float(getattr(row, value_col))
            except AttributeError:
                label = str(row[region_col])
                value = float(row[value_col])
        result.append((label, value))
    return result
