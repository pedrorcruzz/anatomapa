"""Excel (.xlsx) reader with no external dependencies.

Uses only zipfile and xml.etree.ElementTree from the stdlib to parse the
Open XML (OOXML) format that .xlsx implements internally.
"""

from __future__ import annotations

import io
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import OrderedDict
from typing import Union


# Namespaces do Open XML usados nos arquivos internos do .xlsx
_NS_SPREADSHEET = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_RELATIONSHIPS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

_NS = {
    "s": _NS_SPREADSHEET,
    "r": _NS_RELATIONSHIPS,
}

# A última coluna do Excel é XFD, então letra de coluna tem no máximo 3 caracteres.
# Sem esse limite, um nome de cabeçalho digitado errado viraria um índice gigante.
_MAX_COL_LETTERS = 3


def _col_letter_to_index(letter: str) -> int:
    """Convert a column letter (A, B, ..., Z, AA, AB, ...) to a zero-based index.

    Parameters
    ----------
    letter:
        Letter or sequence of letters naming the column (e.g. "A", "D", "AA").

    Returns
    -------
    int
        Zero-based column index.
    """
    letter = letter.upper().strip()
    index = 0
    for char in letter:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


def _cell_col_index(cell_ref: str) -> int:
    """Extract the zero-based column index from a cell reference such as 'D5'.

    Parameters
    ----------
    cell_ref:
        Cell reference in the standard Excel format (e.g. "A1", "D5", "AA10").

    Returns
    -------
    int
        Zero-based column index.
    """
    match = re.match(r"([A-Za-z]+)", cell_ref)
    if not match:
        raise ValueError(f"Referência de célula inválida: {cell_ref!r}")
    return _col_letter_to_index(match.group(1))


def _cell_row_index(cell_ref: str) -> int:
    """Extract the zero-based row index from a cell reference such as 'D5'.

    Parameters
    ----------
    cell_ref:
        Cell reference in the standard Excel format (e.g. "A1", "D5").

    Returns
    -------
    int
        Zero-based row index.
    """
    match = re.search(r"(\d+)$", cell_ref)
    if not match:
        raise ValueError(f"Referência de célula inválida: {cell_ref!r}")
    return int(match.group(1)) - 1


def _parse_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    """Read the shared strings table from the .xlsx file.

    In OOXML, string cells store only an index pointing into this table,
    which avoids repeating text throughout the file.

    Parameters
    ----------
    zf:
        Open .xlsx zip archive.

    Returns
    -------
    list[str]
        Strings indexed as in the sharedStrings.xml file.
    """
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    tree = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for si in tree.findall("s:si", _NS):
        # Cada <si> pode ter <t> direto ou múltiplos <r><t> (texto rico)
        parts: list[str] = []
        for t in si.iter(f"{{{_NS_SPREADSHEET}}}t"):
            parts.append(t.text or "")
        strings.append("".join(parts))
    return strings


def _parse_workbook_sheets(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    """Read the mapping from sheet name to worksheet file inside the zip.

    Combines xl/workbook.xml (names and rIds) with xl/_rels/workbook.xml.rels
    (rId -> file path) to produce (name, path) pairs.

    Parameters
    ----------
    zf:
        Open .xlsx zip archive.

    Returns
    -------
    list[tuple[str, str]]
        List of (sheet_name, path_in_zip) in workbook order.
    """
    wb_tree = ET.fromstring(zf.read("xl/workbook.xml"))
    rels_tree = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))

    # Mapeia rId -> caminho relativo a partir do arquivo de relacionamentos
    rid_to_path: dict[str, str] = {}
    for rel in rels_tree:
        rid = rel.get("Id", "")
        target = rel.get("Target", "")
        # Normaliza: garante prefixo "xl/" quando o target é relativo
        if not target.startswith("xl/"):
            target = "xl/" + target
        rid_to_path[rid] = target

    sheets: list[tuple[str, str]] = []
    sheets_elem = wb_tree.find("s:sheets", _NS)
    if sheets_elem is None:
        return sheets
    for sheet in sheets_elem.findall("s:sheet", _NS):
        name = sheet.get("name", "")
        rid = sheet.get(f"{{{_NS_RELATIONSHIPS}}}id", "")
        path = rid_to_path.get(rid, "")
        if name and path:
            sheets.append((name, path))
    return sheets


def _parse_worksheet(
    zf: zipfile.ZipFile,
    sheet_path: str,
    shared_strings: list[str],
) -> list[list[str]]:
    """Parse a worksheet and return its rows as lists of strings.

    Empty cells within a row are represented as empty strings. Rows that are
    entirely empty are omitted.

    Parameters
    ----------
    zf:
        Open .xlsx zip archive.
    sheet_path:
        Worksheet path inside the zip (e.g. "xl/worksheets/sheet1.xml").
    shared_strings:
        Shared strings table used to resolve string indices.

    Returns
    -------
    list[list[str]]
        Non-empty rows, each one a list of cell values as strings.
    """
    tree = ET.fromstring(zf.read(sheet_path))
    sheet_data = tree.find("s:sheetData", _NS)
    if sheet_data is None:
        return []

    rows: list[list[str]] = []
    for row_elem in sheet_data.findall("s:row", _NS):
        cells = row_elem.findall("s:c", _NS)
        if not cells:
            continue

        # Descobre a maior coluna presente para alocar a linha corretamente
        max_col = max(_cell_col_index(c.get("r", "A1")) for c in cells)
        row_data = [""] * (max_col + 1)

        for cell in cells:
            ref = cell.get("r", "")
            if not ref:
                continue
            col_idx = _cell_col_index(ref)
            cell_type = cell.get("t", "")
            v_elem = cell.find("s:v", _NS)
            value = ""
            if v_elem is not None and v_elem.text is not None:
                if cell_type == "s":
                    # Índice na tabela de strings compartilhadas
                    value = shared_strings[int(v_elem.text)]
                else:
                    value = v_elem.text
            row_data[col_idx] = value

        # Só inclui linhas que têm ao menos uma célula não vazia
        if any(v for v in row_data):
            rows.append(row_data)

    return rows


def _resolve_col_index(
    col: int | str,
    header_row: list[str] | None,
) -> int:
    """Convert a column specification into a zero-based integer index.

    Accepts three forms:
    - int: direct zero-based index.
    - str of up to three letters: spreadsheet column letter ("A", "D", "AA").
    - str matching a header cell: header name.

    A header name is tried first; only then is the string read as a column
    letter. Strings longer than three letters are never column letters, since
    Excel stops at "XFD", so they can only be header names.

    Parameters
    ----------
    col:
        Column specification: int index, letter ("D") or header name.
    header_row:
        Headers from the first row, used to resolve column names. None when
        header=False.

    Returns
    -------
    int
        Zero-based column index.

    Raises
    ------
    ValueError
        If the specification cannot be resolved.
    """
    if isinstance(col, int):
        return col

    is_col_letter = bool(re.fullmatch(r"[A-Za-z]{1,%d}" % _MAX_COL_LETTERS, col))

    if header_row is not None:
        # Com cabeçalho: tenta resolver pelo nome primeiro
        if col in header_row:
            return header_row.index(col)
        # Não encontrado como nome; aceita como letra de coluna se a forma bater
        if is_col_letter:
            return _col_letter_to_index(col)
        raise ValueError(
            f"Coluna {col!r} não encontrada nos cabeçalhos: {header_row}"
        )

    # Sem cabeçalho: aceita apenas letra de coluna ou int (já tratado acima)
    if is_col_letter:
        return _col_letter_to_index(col)

    raise ValueError(
        f"Especificação de coluna inválida sem cabeçalho: {col!r}"
    )


def from_xlsx(
    source: Union[str, os.PathLike, bytes, io.IOBase],
    sheet: str | None = None,
    region_col: int | str = 0,
    value_col: int | str = 1,
    header: bool = True,
    aggregate: str | None = None,
) -> dict[str, float]:
    """Parses an Excel (.xlsx) file and returns a mapping of region to value.

    The .xlsx file is read with no external dependencies: only the stdlib's
    zipfile and xml.etree.ElementTree are used.

    Parameters
    ----------
    source:
        File path as a string or a path-like object (pathlib.Path), file bytes,
        or a binary file-like object.
    sheet:
        Name of the sheet to read. None uses the first sheet in the workbook.
    region_col:
        Region column: zero-based integer index, spreadsheet letter ("D"),
        or header name (when header=True).
    value_col:
        Value column: same formats as region_col.
    header:
        True indicates the first row contains headers and should be skipped
        when collecting data. Also enables resolving columns by name.
    aggregate:
        None for one row per region (the last occurrence's value wins),
        "count" to count occurrences of each region,
        "sum" to sum the values per region.

    Returns
    -------
    dict[str, float]
        Mapping from region label to numeric value, in order of appearance.

    Raises
    ------
    ValueError
        If the requested sheet does not exist, the column is not found, or a
        value cannot be converted to a number.
    """
    # Abre o zip: aceita caminho, bytes ou objeto binário
    if isinstance(source, str):
        zf = zipfile.ZipFile(source, "r")
    elif isinstance(source, bytes):
        zf = zipfile.ZipFile(io.BytesIO(source), "r")
    else:
        zf = zipfile.ZipFile(source, "r")

    with zf:
        shared_strings = _parse_shared_strings(zf)
        sheet_list = _parse_workbook_sheets(zf)

        if not sheet_list:
            raise ValueError("Nenhuma aba encontrada no arquivo .xlsx.")

        available_names = [name for name, _ in sheet_list]

        if sheet is None:
            sheet_path = sheet_list[0][1]
        else:
            matched = [(n, p) for n, p in sheet_list if n == sheet]
            if not matched:
                raise ValueError(
                    f"Aba {sheet!r} não encontrada. "
                    f"Abas disponíveis: {available_names}"
                )
            sheet_path = matched[0][1]

        rows = _parse_worksheet(zf, sheet_path, shared_strings)

    if not rows:
        return {}

    # Separa o cabeçalho (se houver) das linhas de dados
    header_row: list[str] | None = None
    data_rows = rows
    if header:
        header_row = rows[0]
        data_rows = rows[1:]

    r_idx = _resolve_col_index(region_col, header_row)
    v_idx = _resolve_col_index(value_col, header_row)

    # Em "count" a coluna de valor nunca é lida, então não precisa existir
    required = [("region_col", region_col, r_idx)]
    if aggregate != "count":
        required.append(("value_col", value_col, v_idx))

    # Índice fora da largura da planilha só geraria dado vazio; erra explicitamente
    width = max(len(row) for row in rows)
    for name, spec, idx in required:
        if not 0 <= idx < width:
            raise ValueError(
                f"{name}={spec!r} aponta para a coluna de índice {idx}, "
                f"fora da planilha, que tem {width} coluna(s)."
            )

    # Valida que os índices existem nas linhas de dados
    max_needed = max(idx for _, _, idx in required)
    for i, row in enumerate(data_rows):
        if len(row) <= max_needed:
            # Linha pode ter células ausentes no final; complementa com vazio
            data_rows[i] = row + [""] * (max_needed + 1 - len(row))

    if aggregate == "count":
        counts: dict[str, float] = OrderedDict()
        for row in data_rows:
            region = row[r_idx].strip()
            if not region:
                continue
            counts[region] = counts.get(region, 0.0) + 1.0
        return dict(counts)

    if aggregate == "sum":
        totals: dict[str, float] = OrderedDict()
        for i, row in enumerate(data_rows):
            region = row[r_idx].strip()
            if not region:
                continue
            raw_value = row[v_idx].strip()
            if not raw_value:
                continue
            try:
                value = float(raw_value)
            except ValueError as exc:
                raise ValueError(
                    f"Valor não numérico na linha {i + (2 if header else 1)}, "
                    f"coluna de valor: {raw_value!r}"
                ) from exc
            totals[region] = totals.get(region, 0.0) + value
        return dict(totals)

    # Sem agregação: uma entrada por região (última ocorrência prevalece)
    result: dict[str, float] = OrderedDict()
    for i, row in enumerate(data_rows):
        region = row[r_idx].strip()
        if not region:
            continue
        raw_value = row[v_idx].strip()
        if not raw_value:
            continue
        try:
            value = float(raw_value)
        except ValueError as exc:
            raise ValueError(
                f"Valor não numérico na linha {i + (2 if header else 1)}, "
                f"coluna de valor: {raw_value!r}"
            ) from exc
        result[region] = value
    return dict(result)
