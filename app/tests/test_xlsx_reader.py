"""Testes do reader XLSX sem dependências externas.

O helper build_xlsx_bytes() monta um arquivo .xlsx mínimo e válido em memória
usando apenas zipfile e strings XML, espelhando o formato Open XML (OOXML).
"""

import io
import os
import tempfile
import unittest
import zipfile

from anatomapa.readers.xlsx_reader import (
    _col_letter_to_index,
    _cell_col_index,
    _cell_row_index,
    _resolve_col_index,
    _parse_worksheet,
    from_xlsx,
)


# ---------------------------------------------------------------------------
# Helper: gera um .xlsx mínimo em bytes
# ---------------------------------------------------------------------------

_CONTENT_TYPES = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/sharedStrings.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>
"""

_ROOT_RELS = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="xl/workbook.xml"/>
</Relationships>
"""

_WORKBOOK = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Dados" sheetId="1" r:id="rId1"/>
    <sheet name="Extra" sheetId="2" r:id="rId2"/>
  </sheets>
</workbook>
"""

_WORKBOOK_RELS = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings"
    Target="sharedStrings.xml"/>
</Relationships>
"""


def _shared_strings_xml(strings: list[str]) -> str:
    """Gera o XML da tabela de strings compartilhadas."""
    items = "".join(f"<si><t>{s}</t></si>" for s in strings)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        f' count="{len(strings)}" uniqueCount="{len(strings)}">'
        f"{items}</sst>"
    )


def _worksheet_xml(rows: list[list[tuple[str, str]]]) -> str:
    """Gera o XML de uma planilha a partir de linhas de células.

    Parameters
    ----------
    rows:
        Lista de linhas; cada linha é uma lista de tuplas (ref, valor) onde
        ref é a referência Excel ("A1") e valor é o texto XML da célula,
        incluindo o atributo t= quando aplicável.
    """
    row_elems = []
    for r_idx, cells in enumerate(rows, start=1):
        cell_elems = "".join(
            f'<c r="{ref}" {attrs}><v>{val}</v></c>'
            for ref, val, attrs in cells
        )
        row_elems.append(f'<row r="{r_idx}">{cell_elems}</row>')
    sheet_data = "".join(row_elems)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{sheet_data}</sheetData>"
        "</worksheet>"
    )


def build_xlsx_bytes(
    sheet1_rows: list[list[tuple[str, str, str]]],
    sheet2_rows: list[list[tuple[str, str, str]]] | None = None,
    shared_strings: list[str] | None = None,
) -> bytes:
    """Constrói um arquivo .xlsx mínimo e válido em memória.

    Parameters
    ----------
    sheet1_rows:
        Linhas da aba "Dados". Cada célula é (ref, valor, attrs).
        Para string: attrs='t="s"', valor=índice na tabela de strings.
        Para número: attrs='', valor=número em string.
    sheet2_rows:
        Linhas da aba "Extra" (opcional; padrão vazio).
    shared_strings:
        Tabela de strings compartilhadas (padrão vazia).

    Returns
    -------
    bytes
        Conteúdo binário do arquivo .xlsx.
    """
    if shared_strings is None:
        shared_strings = []
    if sheet2_rows is None:
        sheet2_rows = []

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _ROOT_RELS)
        zf.writestr("xl/workbook.xml", _WORKBOOK)
        zf.writestr("xl/_rels/workbook.xml.rels", _WORKBOOK_RELS)
        zf.writestr("xl/sharedStrings.xml", _shared_strings_xml(shared_strings))
        zf.writestr("xl/worksheets/sheet1.xml", _worksheet_xml(sheet1_rows))
        zf.writestr("xl/worksheets/sheet2.xml", _worksheet_xml(sheet2_rows))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Dados de exemplo reutilizáveis
# ---------------------------------------------------------------------------

# Strings compartilhadas: índice 0=região, 1=valor, 2=head, 3=arm, 4=leg, 5=trunk
_STRINGS = ["região", "valor", "head", "arm", "leg", "trunk"]

# Planilha com cabeçalho + 4 linhas de dado (strings na col A, número na col B)
# Linha 1 (cabeçalho): região(s=0), valor(s=1)
# Linha 2: head(s=2), 10
# Linha 3: arm(s=3), 5
# Linha 4: leg(s=4), 3.5
# Linha 5: trunk(s=5), 8
_ROWS_WITH_HEADER = [
    [("A1", "0", 't="s"'), ("B1", "1", 't="s"')],
    [("A2", "2", 't="s"'), ("B2", "10", "")],
    [("A3", "3", 't="s"'), ("B3", "5", "")],
    [("A4", "4", 't="s"'), ("B4", "3.5", "")],
    [("A5", "5", 't="s"'), ("B5", "8", "")],
]

# Planilha sem cabeçalho: 3 linhas diretas
_ROWS_NO_HEADER = [
    [("A1", "2", 't="s"'), ("B1", "20", "")],
    [("A2", "3", 't="s"'), ("B2", "7", "")],
    [("A3", "4", 't="s"'), ("B3", "1.5", "")],
]


# ---------------------------------------------------------------------------
# Testes dos utilitários internos
# ---------------------------------------------------------------------------

class TestColLetterToIndex(unittest.TestCase):
    def test_a(self):
        self.assertEqual(_col_letter_to_index("A"), 0)

    def test_d(self):
        self.assertEqual(_col_letter_to_index("D"), 3)

    def test_z(self):
        self.assertEqual(_col_letter_to_index("Z"), 25)

    def test_aa(self):
        self.assertEqual(_col_letter_to_index("AA"), 26)

    def test_ab(self):
        self.assertEqual(_col_letter_to_index("AB"), 27)

    def test_case_insensitive(self):
        self.assertEqual(_col_letter_to_index("d"), _col_letter_to_index("D"))


class TestCellRefParsing(unittest.TestCase):
    def test_col_index_d5(self):
        self.assertEqual(_cell_col_index("D5"), 3)

    def test_col_index_a1(self):
        self.assertEqual(_cell_col_index("A1"), 0)

    def test_row_index_d5(self):
        self.assertEqual(_cell_row_index("D5"), 4)

    def test_row_index_a1(self):
        self.assertEqual(_cell_row_index("A1"), 0)

    def test_invalid_col_ref(self):
        with self.assertRaises(ValueError):
            _cell_col_index("123")

    def test_invalid_row_ref(self):
        with self.assertRaises(ValueError):
            _cell_row_index("ABC")


class TestResolveColIndex(unittest.TestCase):
    def test_int_passthrough(self):
        self.assertEqual(_resolve_col_index(2, None), 2)

    def test_letter_no_header(self):
        self.assertEqual(_resolve_col_index("C", None), 2)

    def test_letter_with_header_not_in_headers(self):
        # Letra de coluna quando não está nos cabeçalhos
        self.assertEqual(_resolve_col_index("B", ["region", "value"]), 1)

    def test_name_in_header(self):
        headers = ["region", "count", "value"]
        self.assertEqual(_resolve_col_index("value", headers), 2)

    def test_name_priority_over_letter(self):
        # "A" é letra de coluna, mas se existir como nome de cabeçalho, prevalece
        headers = ["A", "B"]
        self.assertEqual(_resolve_col_index("A", headers), 0)

    def test_name_not_in_header_falls_back_to_letter(self):
        # "C" não está nos cabeçalhos mas é uma letra de coluna válida
        self.assertEqual(_resolve_col_index("C", ["region", "value"]), 2)

    def test_string_with_spaces_without_header_raises(self):
        # String com espaços não é letra de coluna nem pode ser resolvida sem cabeçalho
        with self.assertRaises(ValueError):
            _resolve_col_index("nome invalido", None)


# ---------------------------------------------------------------------------
# Testes do from_xlsx: leitura básica
# ---------------------------------------------------------------------------

class TestFromXlsxBasic(unittest.TestCase):
    def setUp(self):
        self.xlsx_bytes = build_xlsx_bytes(
            sheet1_rows=_ROWS_WITH_HEADER,
            shared_strings=_STRINGS,
        )

    def test_basic_by_column_index(self):
        result = from_xlsx(self.xlsx_bytes, region_col=0, value_col=1)
        self.assertEqual(result["head"], 10.0)
        self.assertEqual(result["arm"], 5.0)
        self.assertEqual(result["leg"], 3.5)
        self.assertEqual(result["trunk"], 8.0)

    def test_returns_dict_of_floats(self):
        result = from_xlsx(self.xlsx_bytes)
        for v in result.values():
            self.assertIsInstance(v, float)

    def test_preserves_order_of_appearance(self):
        result = from_xlsx(self.xlsx_bytes)
        self.assertEqual(list(result.keys()), ["head", "arm", "leg", "trunk"])

    def test_first_sheet_used_by_default(self):
        result = from_xlsx(self.xlsx_bytes)
        self.assertIn("head", result)

    def test_from_bytes(self):
        result = from_xlsx(self.xlsx_bytes)
        self.assertEqual(len(result), 4)

    def test_from_file_path(self):
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            f.write(self.xlsx_bytes)
            path = f.name
        try:
            result = from_xlsx(path)
            self.assertEqual(result["head"], 10.0)
        finally:
            os.unlink(path)

    def test_from_file_object(self):
        buf = io.BytesIO(self.xlsx_bytes)
        result = from_xlsx(buf)
        self.assertEqual(result["head"], 10.0)


# ---------------------------------------------------------------------------
# Testes: seleção de aba por nome
# ---------------------------------------------------------------------------

class TestFromXlsxSheetSelection(unittest.TestCase):
    def setUp(self):
        # Aba "Extra" tem dados diferentes
        extra_rows = [
            [("A1", "0", 't="s"'), ("B1", "1", 't="s"')],
            [("A2", "2", 't="s"'), ("B2", "99", "")],
        ]
        self.xlsx_bytes = build_xlsx_bytes(
            sheet1_rows=_ROWS_WITH_HEADER,
            sheet2_rows=extra_rows,
            shared_strings=_STRINGS,
        )

    def test_select_first_sheet_by_name(self):
        result = from_xlsx(self.xlsx_bytes, sheet="Dados")
        self.assertEqual(result["head"], 10.0)

    def test_select_second_sheet_by_name(self):
        result = from_xlsx(self.xlsx_bytes, sheet="Extra")
        self.assertEqual(result["head"], 99.0)

    def test_nonexistent_sheet_raises(self):
        with self.assertRaises(ValueError) as ctx:
            from_xlsx(self.xlsx_bytes, sheet="Inexistente")
        self.assertIn("Inexistente", str(ctx.exception))
        self.assertIn("Dados", str(ctx.exception))
        self.assertIn("Extra", str(ctx.exception))


# ---------------------------------------------------------------------------
# Testes: seleção de coluna por letra e por nome de cabeçalho
# ---------------------------------------------------------------------------

class TestFromXlsxColumnSpec(unittest.TestCase):
    def setUp(self):
        self.xlsx_bytes = build_xlsx_bytes(
            sheet1_rows=_ROWS_WITH_HEADER,
            shared_strings=_STRINGS,
        )

    def test_column_by_letter_a(self):
        result = from_xlsx(self.xlsx_bytes, region_col="A", value_col="B")
        self.assertEqual(result["head"], 10.0)

    def test_column_by_header_name(self):
        # Os cabeçalhos são "região" (idx 0 na tabela de strings) e "valor" (idx 1)
        result = from_xlsx(self.xlsx_bytes, region_col="região", value_col="valor")
        self.assertEqual(result["arm"], 5.0)

    def test_nonexistent_column_name_raises(self):
        # Underscores não são letra de coluna; deve falhar quando não encontrado no cabeçalho
        with self.assertRaises(ValueError):
            from_xlsx(self.xlsx_bytes, region_col="coluna_inexistente")


# ---------------------------------------------------------------------------
# Testes: header=False
# ---------------------------------------------------------------------------

class TestFromXlsxNoHeader(unittest.TestCase):
    def setUp(self):
        self.xlsx_bytes = build_xlsx_bytes(
            sheet1_rows=_ROWS_NO_HEADER,
            shared_strings=_STRINGS,
        )

    def test_no_header_reads_all_rows(self):
        result = from_xlsx(self.xlsx_bytes, header=False)
        self.assertEqual(result["head"], 20.0)
        self.assertEqual(result["arm"], 7.0)
        self.assertEqual(result["leg"], 1.5)

    def test_no_header_column_by_index(self):
        result = from_xlsx(self.xlsx_bytes, region_col=0, value_col=1, header=False)
        self.assertIn("head", result)

    def test_no_header_column_by_letter(self):
        result = from_xlsx(self.xlsx_bytes, region_col="A", value_col="B", header=False)
        self.assertEqual(result["head"], 20.0)


# ---------------------------------------------------------------------------
# Testes: aggregate="count"
# ---------------------------------------------------------------------------

class TestFromXlsxAggregateCount(unittest.TestCase):
    def setUp(self):
        # Dados crus: head aparece 3 vezes, arm 1 vez; coluna B não importa para count
        strings = ["head", "arm"]
        raw_rows = [
            [("A1", "0", 't="s"'), ("B1", "1", "")],
            [("A2", "0", 't="s"'), ("B2", "2", "")],
            [("A3", "1", 't="s"'), ("B3", "3", "")],
            [("A4", "0", 't="s"'), ("B4", "4", "")],
        ]
        self.xlsx_bytes = build_xlsx_bytes(
            sheet1_rows=raw_rows,
            shared_strings=strings,
        )

    def test_count_basic(self):
        result = from_xlsx(self.xlsx_bytes, header=False, aggregate="count")
        self.assertEqual(result["head"], 3.0)
        self.assertEqual(result["arm"], 1.0)

    def test_count_returns_float(self):
        result = from_xlsx(self.xlsx_bytes, header=False, aggregate="count")
        for v in result.values():
            self.assertIsInstance(v, float)

    def test_count_preserves_appearance_order(self):
        result = from_xlsx(self.xlsx_bytes, header=False, aggregate="count")
        self.assertEqual(list(result.keys()), ["head", "arm"])


# ---------------------------------------------------------------------------
# Testes: aggregate="sum"
# ---------------------------------------------------------------------------

class TestFromXlsxAggregateSum(unittest.TestCase):
    def setUp(self):
        strings = ["head", "arm"]
        raw_rows = [
            [("A1", "0", 't="s"'), ("B1", "3", "")],
            [("A2", "0", 't="s"'), ("B2", "7", "")],
            [("A3", "1", 't="s"'), ("B3", "5", "")],
        ]
        self.xlsx_bytes = build_xlsx_bytes(
            sheet1_rows=raw_rows,
            shared_strings=strings,
        )

    def test_sum_basic(self):
        result = from_xlsx(self.xlsx_bytes, header=False, aggregate="sum")
        self.assertEqual(result["head"], 10.0)
        self.assertEqual(result["arm"], 5.0)

    def test_sum_returns_float(self):
        result = from_xlsx(self.xlsx_bytes, header=False, aggregate="sum")
        for v in result.values():
            self.assertIsInstance(v, float)

    def test_sum_preserves_appearance_order(self):
        result = from_xlsx(self.xlsx_bytes, header=False, aggregate="sum")
        self.assertEqual(list(result.keys()), ["head", "arm"])


# ---------------------------------------------------------------------------
# Testes: condições de erro
# ---------------------------------------------------------------------------

class TestFromXlsxErrors(unittest.TestCase):
    def _make_xlsx_with_bad_value(self) -> bytes:
        """Planilha com valor não numérico na coluna de valor."""
        strings = ["região", "valor", "head", "nao_numero"]
        rows = [
            [("A1", "0", 't="s"'), ("B1", "1", 't="s"')],
            [("A2", "2", 't="s"'), ("B2", "3", 't="s"')],  # "nao_numero" como valor
        ]
        return build_xlsx_bytes(sheet1_rows=rows, shared_strings=strings)

    def test_nonexistent_sheet(self):
        xlsx = build_xlsx_bytes(
            sheet1_rows=_ROWS_WITH_HEADER,
            shared_strings=_STRINGS,
        )
        with self.assertRaises(ValueError) as ctx:
            from_xlsx(xlsx, sheet="NaoExiste")
        self.assertIn("NaoExiste", str(ctx.exception))

    def test_nonexistent_column_by_name(self):
        xlsx = build_xlsx_bytes(
            sheet1_rows=_ROWS_WITH_HEADER,
            shared_strings=_STRINGS,
        )
        with self.assertRaises(ValueError):
            from_xlsx(xlsx, region_col="coluna_fantasma")

    def test_non_numeric_value_raises(self):
        xlsx = self._make_xlsx_with_bad_value()
        with self.assertRaises(ValueError) as ctx:
            from_xlsx(xlsx, region_col=0, value_col=1)
        self.assertIn("não numérico", str(ctx.exception))

    def test_non_numeric_value_in_sum_raises(self):
        xlsx = self._make_xlsx_with_bad_value()
        with self.assertRaises(ValueError) as ctx:
            from_xlsx(xlsx, region_col=0, value_col=1, aggregate="sum")
        self.assertIn("não numérico", str(ctx.exception))

    def test_empty_sheet_returns_empty_dict(self):
        xlsx = build_xlsx_bytes(sheet1_rows=[], shared_strings=[])
        result = from_xlsx(xlsx, header=False)
        self.assertEqual(result, {})


# ---------------------------------------------------------------------------
# Testes: casos de borda de parsing interno
# ---------------------------------------------------------------------------

class TestFromXlsxEdgeCases(unittest.TestCase):
    def _build_xlsx_without_shared_strings(self) -> bytes:
        """Planilha com apenas valores numéricos; sem sharedStrings.xml."""
        # Sem strings compartilhadas: células têm valor numérico direto
        sheet_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<sheetData>"
            '<row r="1"><c r="A1"><v>1</v></c><c r="B1"><v>42</v></c></row>'
            '<row r="2"><c r="A2"><v>2</v></c><c r="B2"><v>7</v></c></row>'
            "</sheetData>"
            "</worksheet>"
        )
        # Workbook e rels com uma única aba
        workbook = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
            ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            "<sheets>"
            '<sheet name="Plan1" sheetId="1" r:id="rId1"/>'
            "</sheets>"
            "</workbook>"
        )
        wb_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"'
            ' Target="worksheets/sheet1.xml"/>'
            "</Relationships>"
        )
        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            "</Types>"
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("[Content_Types].xml", content_types)
            zf.writestr("_rels/.rels", _ROOT_RELS)
            zf.writestr("xl/workbook.xml", workbook)
            zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
            zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
            # Sem xl/sharedStrings.xml intencional
        return buf.getvalue()

    def test_no_shared_strings_file(self):
        # Cobre linha 102: retorno early quando sharedStrings.xml não existe
        xlsx = self._build_xlsx_without_shared_strings()
        result = from_xlsx(xlsx, header=False)
        self.assertEqual(result["1"], 42.0)
        self.assertEqual(result["2"], 7.0)

    def test_skip_empty_region_in_no_aggregate(self):
        # Linha com região vazia deve ser ignorada (cobre linhas 398)
        strings = ["head", ""]
        rows = [
            [("A1", "0", 't="s"'), ("B1", "10", "")],
            [("A2", "1", 't="s"'), ("B2", "5", "")],   # região vazia (string "")
            [("A3", "0", 't="s"'), ("B3", "3", "")],
        ]
        xlsx = build_xlsx_bytes(sheet1_rows=rows, shared_strings=strings)
        result = from_xlsx(xlsx, header=False)
        self.assertNotIn("", result)
        self.assertEqual(result["head"], 3.0)

    def test_skip_empty_value_in_no_aggregate(self):
        # Linha com valor vazio deve ser ignorada (cobre linha 401)
        strings = ["head", "arm"]
        rows = [
            [("A1", "0", 't="s"')],               # linha só com coluna A; col B ausente
            [("A2", "1", 't="s"'), ("B2", "5", "")],
        ]
        xlsx = build_xlsx_bytes(sheet1_rows=rows, shared_strings=strings)
        result = from_xlsx(xlsx, header=False)
        self.assertNotIn("head", result)
        self.assertEqual(result["arm"], 5.0)

    def test_skip_empty_region_in_count(self):
        # Linha com região vazia no modo count deve ser ignorada (cobre linha 370)
        strings = ["head", ""]
        rows = [
            [("A1", "0", 't="s"')],
            [("A2", "1", 't="s"')],   # região vazia
            [("A3", "0", 't="s"')],
        ]
        xlsx = build_xlsx_bytes(sheet1_rows=rows, shared_strings=strings)
        result = from_xlsx(xlsx, header=False, aggregate="count")
        self.assertNotIn("", result)
        self.assertEqual(result["head"], 2.0)

    def test_skip_empty_region_in_sum(self):
        # Linha com região vazia no modo sum deve ser ignorada (cobre linha 379)
        strings = ["head", ""]
        rows = [
            [("A1", "0", 't="s"'), ("B1", "5", "")],
            [("A2", "1", 't="s"'), ("B2", "99", "")],   # região vazia
            [("A3", "0", 't="s"'), ("B3", "3", "")],
        ]
        xlsx = build_xlsx_bytes(sheet1_rows=rows, shared_strings=strings)
        result = from_xlsx(xlsx, header=False, aggregate="sum")
        self.assertNotIn("", result)
        self.assertEqual(result["head"], 8.0)

    def test_skip_empty_value_in_sum(self):
        # Linha com valor vazio no modo sum deve ser ignorada (cobre linha 382)
        strings = ["head", "arm"]
        rows = [
            [("A1", "0", 't="s"'), ("B1", "5", "")],
            [("A2", "1", 't="s"')],   # sem coluna B (valor vazio)
            [("A3", "0", 't="s"'), ("B3", "3", "")],
        ]
        xlsx = build_xlsx_bytes(sheet1_rows=rows, shared_strings=strings)
        result = from_xlsx(xlsx, header=False, aggregate="sum")
        self.assertNotIn("arm", result)
        self.assertEqual(result["head"], 8.0)

    def test_short_row_padded_correctly(self):
        # Linha com menos colunas que o índice de value_col (cobre linha 363)
        strings = ["head", "arm"]
        rows = [
            # col A (idx 0) tem região, col C (idx 2) tem valor; col B ausente
            [("A1", "0", 't="s"'), ("C1", "10", "")],
            [("A2", "1", 't="s"'), ("C2", "5", "")],
        ]
        xlsx = build_xlsx_bytes(sheet1_rows=rows, shared_strings=strings)
        result = from_xlsx(xlsx, region_col=0, value_col=2, header=False)
        self.assertEqual(result["head"], 10.0)
        self.assertEqual(result["arm"], 5.0)

    def test_parse_worksheet_no_sheet_data(self):
        # Cobre linha 183: sheetData ausente no XML da planilha
        xml_no_sheet_data = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "</worksheet>"
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("xl/worksheets/sheet1.xml", xml_no_sheet_data)
        buf.seek(0)
        with zipfile.ZipFile(buf, "r") as zf:
            rows = _parse_worksheet(zf, "xl/worksheets/sheet1.xml", [])
        self.assertEqual(rows, [])

    def test_parse_worksheet_row_without_cells(self):
        # Cobre linha 189: <row> sem elementos <c> filhos
        xml_empty_row = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<sheetData>"
            '<row r="1"></row>'
            '<row r="2"><c r="A2"><v>5</v></c></row>'
            "</sheetData>"
            "</worksheet>"
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("xl/worksheets/sheet1.xml", xml_empty_row)
        buf.seek(0)
        with zipfile.ZipFile(buf, "r") as zf:
            rows = _parse_worksheet(zf, "xl/worksheets/sheet1.xml", [])
        # Só a linha 2 é retornada; a linha 1 vazia é ignorada
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "5")

    def test_parse_worksheet_cell_without_ref(self):
        # Cobre linha 198: célula <c> sem atributo r
        xml_no_ref = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<sheetData>"
            '<row r="1">'
            '<c r="A1"><v>10</v></c>'
            '<c><v>99</v></c>'    # sem atributo r: deve ser ignorada
            "</row>"
            "</sheetData>"
            "</worksheet>"
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("xl/worksheets/sheet1.xml", xml_no_ref)
        buf.seek(0)
        with zipfile.ZipFile(buf, "r") as zf:
            rows = _parse_worksheet(zf, "xl/worksheets/sheet1.xml", [])
        # Apenas a célula A1 é lida; a sem ref é ignorada
        self.assertEqual(rows[0][0], "10")
        self.assertEqual(len(rows[0]), 1)

    def test_count_skips_whitespace_only_region(self):
        # Cobre linha 370: região com apenas espaços (não filtrada pelo parser, mas ignorada no count)
        # Usamos célula com valor numérico diretamente como região (só espaços)
        xml_ws_region = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<sheetData>"
            '<row r="1"><c r="A1"><v>   </v></c></row>'
            '<row r="2"><c r="A2"><v>head</v></c></row>'
            "</sheetData>"
            "</worksheet>"
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("xl/worksheets/sheet1.xml", xml_ws_region)
        buf.seek(0)
        with zipfile.ZipFile(buf, "r") as zf:
            rows = _parse_worksheet(zf, "xl/worksheets/sheet1.xml", [])
        # Monta um xlsx falso a partir dessas linhas para testar o from_xlsx
        # Alternativa: testa aggregate="count" diretamente passando os dados
        from anatomapa.readers.xlsx_reader import from_xlsx as _from_xlsx
        # A linha com "   " passa pelo _parse_worksheet mas deve ser ignorada no count
        strings_ws = ["   ", "head"]
        rows_ws = [
            [("A1", "0", 't="s"'), ("B1", "1", "")],   # região "   "
            [("A2", "1", 't="s"'), ("B2", "2", "")],   # região "head"
        ]
        xlsx_ws = build_xlsx_bytes(sheet1_rows=rows_ws, shared_strings=strings_ws)
        result = _from_xlsx(xlsx_ws, header=False, aggregate="count")
        self.assertNotIn("   ", result)
        self.assertIn("head", result)

    def test_no_sheet_list_raises(self):
        # Workbook sem elemento <sheets> (cobre linha 328 via sheet_list vazio)
        workbook_empty = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
            ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            "</workbook>"
        )
        wb_rels_empty = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            "</Relationships>"
        )
        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            "</Types>"
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("[Content_Types].xml", content_types)
            zf.writestr("_rels/.rels", _ROOT_RELS)
            zf.writestr("xl/workbook.xml", workbook_empty)
            zf.writestr("xl/_rels/workbook.xml.rels", wb_rels_empty)
            zf.writestr("xl/sharedStrings.xml", _shared_strings_xml([]))
        with self.assertRaises(ValueError) as ctx:
            from_xlsx(buf.getvalue())
        self.assertIn("Nenhuma aba", str(ctx.exception))


# ---------------------------------------------------------------------------
# Testes: exposição via fachada
# ---------------------------------------------------------------------------

class TestFacadeExposesFromXlsx(unittest.TestCase):
    def test_from_xlsx_importable_from_facade(self):
        import anatomapa
        self.assertTrue(callable(anatomapa.from_xlsx))

    def test_from_xlsx_in_all(self):
        import anatomapa
        self.assertIn("from_xlsx", anatomapa.__all__)

    def test_facade_returns_correct_result(self):
        xlsx = build_xlsx_bytes(
            sheet1_rows=_ROWS_WITH_HEADER,
            shared_strings=_STRINGS,
        )
        import anatomapa
        result = anatomapa.from_xlsx(xlsx)
        self.assertEqual(result["head"], 10.0)


if __name__ == "__main__":
    unittest.main()
