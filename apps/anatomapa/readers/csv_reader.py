from __future__ import annotations

import csv
import io


def from_csv(
    source: str | io.TextIOBase,
    region_col: str,
    value_col: str,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> list[tuple[str, float]]:
    """Parses a CSV file or string into (label, value) pairs.

    Parameters
    ----------
    source:
        File path as a string, or a text file-like object.
    region_col:
        Name of the CSV column that contains the region label.
    value_col:
        Name of the CSV column that contains the numeric value.
    delimiter:
        Field delimiter (default: comma).
    encoding:
        Encoding used when source is a file path.

    Returns
    -------
    list[tuple[str, float]]
        List of (label, value) pairs in row order.
    """
    if isinstance(source, str) and not source.startswith("\n") and "\n" not in source[:512]:
        # Trata a string como caminho de arquivo
        with open(source, newline="", encoding=encoding) as fh:
            reader = csv.DictReader(fh, delimiter=delimiter)
            return [(row[region_col], float(row[value_col])) for row in reader]

    if isinstance(source, str):
        fh = io.StringIO(source)
    else:
        fh = source

    reader = csv.DictReader(fh, delimiter=delimiter)
    return [(row[region_col], float(row[value_col])) for row in reader]
