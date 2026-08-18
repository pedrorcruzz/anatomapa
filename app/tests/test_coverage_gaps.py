"""Tests aimed at the remaining coverage gaps.

Target modules:
- domain/model.py (lines 20-23): regions(view=...), get() miss, ids()
- domain/colormap.py (line 43): span == 0 in color_at
- readers/csv_reader.py (lines 36-38, 41): file and multiline string reading
- readers/json_reader.py (lines 40-41, 51): file and invalid format
- color/registry.py (lines 89, 94): list_colormaps, list_scales
- model/loader.py (lines 45, 49, 55, 58): SVG paths without namespace, without
  a regions group
"""

import io
import os
import tempfile
import unittest

from anatomapa.domain.colormap import ColorMap
from anatomapa.domain.model import AnatomicalModel
from anatomapa.domain.region import Region

_ASSETS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "anatomapa", "assets"
)
_ASSETS_EXIST = (
    os.path.exists(os.path.join(_ASSETS_DIR, "body_male_anterior.svg"))
    and os.path.exists(os.path.join(_ASSETS_DIR, "regions.json"))
)


def _make_model() -> AnatomicalModel:
    return AnatomicalModel(
        _regions=(
            Region(
                id="head",
                label_pt="Cabeca",
                label_en="Head",
                aliases=(),
                bilateral=False,
                parent=None,
                geometry={"center": "M 0 0 Z"},
            ),
            Region(
                id="arm",
                label_pt="Braco",
                label_en="Arm",
                aliases=(),
                bilateral=True,
                parent=None,
                geometry={"left": "M 0 0 Z", "right": "M 1 1 Z"},
            ),
        )
    )


class TestAnatomicalModelMethods(unittest.TestCase):
    """Covers lines 20-23 of domain/model.py."""

    def setUp(self):
        self.model = _make_model()

    def test_regions_returns_all_when_no_view(self):
        regions = self.model.regions()
        self.assertEqual(len(regions), 2)

    def test_regions_with_view_param_returns_all(self):
        # view filtragem ainda não implementada: retorna tudo
        regions = self.model.regions(view="anterior")
        self.assertEqual(len(regions), 2)

    def test_regions_with_posterior_view(self):
        regions = self.model.regions(view="posterior")
        self.assertEqual(len(regions), 2)

    def test_get_existing_region(self):
        region = self.model.get("head")
        self.assertIsNotNone(region)
        self.assertEqual(region.id, "head")

    def test_get_missing_region_returns_none(self):
        result = self.model.get("nonexistent_xyz")
        self.assertIsNone(result)

    def test_ids_returns_tuple(self):
        ids = self.model.ids()
        self.assertIsInstance(ids, tuple)

    def test_ids_contains_all_canonical_ids(self):
        ids = self.model.ids()
        self.assertIn("head", ids)
        self.assertIn("arm", ids)

    def test_ids_stable_order(self):
        ids1 = self.model.ids()
        ids2 = self.model.ids()
        self.assertEqual(ids1, ids2)


class TestColorMapEdgeCases(unittest.TestCase):
    """Covers line 43 of domain/colormap.py: span == 0."""

    def test_span_zero_returns_lo_rgb(self):
        # Dois stops com mesmo t: span == 0
        cmap = ColorMap(
            stops=(
                (0.0, (10, 20, 30)),
                (0.0, (99, 99, 99)),
                (1.0, (255, 255, 255)),
            )
        )
        # Ao visitar o intervalo [0.0, 0.0], span será 0 e retorna lo_rgb
        result = cmap.color_at(0.0)
        self.assertEqual(result, (10, 20, 30))


class TestCsvReaderFilePath(unittest.TestCase):
    """Covers lines 36-38 and 41 of readers/csv_reader.py."""

    def test_reads_from_file_path(self):
        from anatomapa.readers.csv_reader import from_csv

        csv_content = "region,value\nhead,10\narm,5\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(csv_content)
            path = tmp.name
        try:
            result = from_csv(path, "region", "value")
            self.assertEqual(result, [("head", 10.0), ("arm", 5.0)])
        finally:
            os.unlink(path)

    def test_reads_from_file_path_custom_delimiter(self):
        from anatomapa.readers.csv_reader import from_csv

        csv_content = "region;value\nhead;10\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(csv_content)
            path = tmp.name
        try:
            result = from_csv(path, "region", "value", delimiter=";")
            self.assertEqual(result, [("head", 10.0)])
        finally:
            os.unlink(path)

    def test_multiline_string_treated_as_csv_content(self):
        from anatomapa.readers.csv_reader import from_csv

        # String com \n não é tratada como caminho de arquivo
        csv_data = "region,value\nhead,10\narm,5\n"
        result = from_csv(csv_data, "region", "value")
        self.assertEqual(result, [("head", 10.0), ("arm", 5.0)])

    def test_file_like_object_direct(self):
        from anatomapa.readers.csv_reader import from_csv

        csv_data = "region,value\ntrunk,7.5\n"
        fh = io.StringIO(csv_data)
        result = from_csv(fh, "region", "value")
        self.assertEqual(result, [("trunk", 7.5)])


class TestJsonReaderFilePath(unittest.TestCase):
    """Covers lines 40-41 and 51 of readers/json_reader.py."""

    def test_reads_from_file_path_object_format(self):
        from anatomapa.readers.json_reader import from_json

        json_content = '{"head": 10, "arm": 5}'
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(json_content)
            path = tmp.name
        try:
            result = from_json(path)
            self.assertIn(("head", 10.0), result)
            self.assertIn(("arm", 5.0), result)
        finally:
            os.unlink(path)

    def test_reads_from_file_path_array_format(self):
        from anatomapa.readers.json_reader import from_json

        json_content = '[{"region": "head", "value": 10}]'
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(json_content)
            path = tmp.name
        try:
            result = from_json(path, region_key="region", value_key="value")
            self.assertEqual(result, [("head", 10.0)])
        finally:
            os.unlink(path)

    def test_invalid_structure_raises_value_error(self):
        from anatomapa.readers.json_reader import from_json

        # JSON válido mas nem dict nem list: passa via file-like para chegar na linha 51
        json_io = io.StringIO("42")
        with self.assertRaises(ValueError):
            from_json(json_io)

    def test_invalid_structure_boolean_raises(self):
        from anatomapa.readers.json_reader import from_json

        json_io = io.StringIO("true")
        with self.assertRaises(ValueError):
            from_json(json_io)


class TestColorRegistry(unittest.TestCase):
    """Covers lines 89 and 94 of color/registry.py."""

    def test_list_colormaps_returns_sorted_list(self):
        from anatomapa.color.registry import list_colormaps

        result = list_colormaps()
        self.assertIsInstance(result, list)
        self.assertEqual(result, sorted(result))
        self.assertIn("reds", result)
        self.assertIn("viridis", result)

    def test_list_scales_returns_sorted_list(self):
        from anatomapa.color.registry import list_scales

        result = list_scales()
        self.assertIsInstance(result, list)
        self.assertEqual(result, sorted(result))
        self.assertIn("linear", result)
        self.assertIn("log", result)

    def test_get_unknown_colormap_raises(self):
        from anatomapa.color.registry import get_colormap

        with self.assertRaises(ValueError) as ctx:
            get_colormap("nonexistent_cmap")
        self.assertIn("nonexistent_cmap", str(ctx.exception))

    def test_get_unknown_scale_raises(self):
        from anatomapa.color.registry import get_scale

        with self.assertRaises(ValueError) as ctx:
            get_scale("nonexistent_scale")
        self.assertIn("nonexistent_scale", str(ctx.exception))


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes -- skipping testes de loader")
class TestModelLoaderEdgeCases(unittest.TestCase):
    """Covers lines 45, 49, 55, 58 of model/loader.py."""

    def test_load_male_anterior_returns_model(self):
        from anatomapa.model.loader import load

        model = load("anterior", body="male")
        self.assertIsInstance(model, AnatomicalModel)
        self.assertGreater(len(model.ids()), 0)

    def test_load_male_posterior_returns_model(self):
        from anatomapa.model.loader import load

        model = load("posterior", body="male")
        self.assertIsInstance(model, AnatomicalModel)
        self.assertGreater(len(model.ids()), 0)

    def test_load_female_anterior_returns_model(self):
        from anatomapa.model.loader import load

        model = load("anterior", body="female")
        self.assertIsInstance(model, AnatomicalModel)
        self.assertGreater(len(model.ids()), 0)

    def test_invalid_body_raises(self):
        from anatomapa.model.loader import load

        with self.assertRaises(ValueError) as ctx:
            load("anterior", body="robot")
        self.assertIn("robot", str(ctx.exception))

    def test_invalid_view_raises(self):
        from anatomapa.model.loader import load

        with self.assertRaises(ValueError) as ctx:
            load("lateral", body="male")
        self.assertIn("lateral", str(ctx.exception))

    def test_parse_svg_no_regions_group_raises(self):
        from anatomapa.model.loader import _parse_svg

        svg_without_regions = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="other"><path id="head" d="M 0 0 Z" /></g>'
            "</svg>"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".svg", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(svg_without_regions)
            path = tmp.name
        try:
            with self.assertRaises(ValueError) as ctx:
                _parse_svg(path)
            self.assertIn("regions", str(ctx.exception))
        finally:
            os.unlink(path)

    def test_parse_svg_path_without_id_skipped(self):
        from anatomapa.model.loader import _parse_svg

        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g id="regions">'
            '<path d="M 0 0 Z" />'
            '<path id="head" d="M 10 10 Z" />'
            "</g>"
            "</svg>"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".svg", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(svg)
            path = tmp.name
        try:
            result = _parse_svg(path)
            self.assertIn("head", result)
            # Path sem id não gera entrada
            self.assertNotIn("", result)
        finally:
            os.unlink(path)

    def test_parse_svg_non_path_element_skipped(self):
        from anatomapa.model.loader import _parse_svg

        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g id="regions">'
            '<rect id="box" width="10" height="10" />'
            '<path id="head" d="M 10 10 Z" />'
            "</g>"
            "</svg>"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".svg", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(svg)
            path = tmp.name
        try:
            result = _parse_svg(path)
            self.assertIn("head", result)
            self.assertNotIn("box", result)
        finally:
            os.unlink(path)

    def test_parse_svg_bilateral_region_both_sides(self):
        from anatomapa.model.loader import _parse_svg

        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g id="regions">'
            '<path id="arm-left" d="M 0 0 Z" />'
            '<path id="arm-right" d="M 100 0 Z" />'
            "</g>"
            "</svg>"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".svg", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(svg)
            path = tmp.name
        try:
            result = _parse_svg(path)
            self.assertIn("arm", result)
            self.assertIn("left", result["arm"])
            self.assertIn("right", result["arm"])
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
