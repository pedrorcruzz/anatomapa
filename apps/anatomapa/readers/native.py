from __future__ import annotations

from typing import Any


def from_dict(data: dict[str, float | int]) -> list[tuple[str, float]]:
    """Converts a {label: value} dict into a list of (label, value) pairs.

    Parameters
    ----------
    data:
        Mapping from region label to numeric value.

    Returns
    -------
    list[tuple[str, float]]
        Stable list of (label, value) pairs (dict insertion order).
    """
    return [(str(k), float(v)) for k, v in data.items()]


def from_records(
    records: Any,
    region_col: str,
    value_col: str,
) -> list[tuple[str, float]]:
    """Converts a sequence of record-like objects into (label, value) pairs.

    Works with any object that supports iteration and item or attribute
    access, including dicts, namedtuples, dataclasses, and pandas
    DataFrames (duck typing, pandas is never imported).

    Parameters
    ----------
    records:
        Iterable of record-like objects.
    region_col:
        Name of the field that contains the region label.
    value_col:
        Name of the field that contains the numeric value.

    Returns
    -------
    list[tuple[str, float]]
        List of (label, value) pairs in input order.
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
