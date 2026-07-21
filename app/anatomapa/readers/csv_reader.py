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
    """Parseia um arquivo ou string CSV em pares (rótulo, valor).

    Parameters
    ----------
    source:
        Caminho do arquivo como string ou objeto de texto tipo arquivo.
    region_col:
        Nome da coluna CSV que contém o rótulo da região.
    value_col:
        Nome da coluna CSV que contém o valor numérico.
    delimiter:
        Delimitador de campo (padrão: vírgula).
    encoding:
        Codificação quando source é um caminho de arquivo.

    Returns
    -------
    list[tuple[str, float]]
        Lista de pares (rótulo, valor) na ordem das linhas.
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
