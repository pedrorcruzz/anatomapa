from __future__ import annotations

from collections import Counter


def aggregate_count(
    records: list[tuple[str, ...]],
    region_index: int = 0,
) -> dict[str, float]:
    """Conta ocorrências de cada rótulo de região em registros brutos de eventos.

    Parameters
    ----------
    records:
        Lista de tuplas onde uma posição contém o rótulo da região.
    region_index:
        Índice do rótulo da região dentro de cada tupla.

    Returns
    -------
    dict[str, float]
        Mapeamento do rótulo da região para a contagem de eventos.
    """
    counter: Counter[str] = Counter()
    for row in records:
        counter[str(row[region_index])] += 1
    return {k: float(v) for k, v in sorted(counter.items())}


def aggregate_sum(
    records: list[tuple[str, float | int, ...]],
    region_index: int = 0,
    value_index: int = 1,
) -> dict[str, float]:
    """Soma valores por rótulo de região em registros brutos de eventos.

    Parameters
    ----------
    records:
        Lista de tuplas com rótulo da região e valor numérico.
    region_index:
        Índice do rótulo da região dentro de cada tupla.
    value_index:
        Índice do valor numérico dentro de cada tupla.

    Returns
    -------
    dict[str, float]
        Mapeamento do rótulo da região para o valor somado.
    """
    totals: dict[str, float] = {}
    for row in records:
        label = str(row[region_index])
        value = float(row[value_index])  # type: ignore[arg-type]
        totals[label] = totals.get(label, 0.0) + value
    return dict(sorted(totals.items()))
