from __future__ import annotations

from collections import Counter


def aggregate_count(
    records: list[tuple[str, ...]],
    region_index: int = 0,
) -> dict[str, float]:
    """Count occurrences of each region label in raw event records.

    Parameters
    ----------
    records:
        List of tuples where one position holds the region label.
    region_index:
        Index of the region label within each tuple.

    Returns
    -------
    dict[str, float]
        Mapping from region label to event count.
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
    """Sum values per region label in raw event records.

    Parameters
    ----------
    records:
        List of tuples holding the region label and a numeric value.
    region_index:
        Index of the region label within each tuple.
    value_index:
        Index of the numeric value within each tuple.

    Returns
    -------
    dict[str, float]
        Mapping from region label to the summed value.
    """
    totals: dict[str, float] = {}
    for row in records:
        label = str(row[region_index])
        value = float(row[value_index])  # type: ignore[arg-type]
        totals[label] = totals.get(label, 0.0) + value
    return dict(sorted(totals.items()))
