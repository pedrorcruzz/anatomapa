"""Tests for the public heatmap() facade.

Tests that depend on assets (SVG + regions.json) are skipped when assets
are absent.
"""

import os
import unittest

_ASSETS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "anatomapa", "assets"
)
_ASSETS_EXIST = (
    os.path.exists(os.path.join(_ASSETS_DIR, "body_male_anterior.svg"))
    and os.path.exists(os.path.join(_ASSETS_DIR, "regions.json"))
)


@unittest.skipUnless(_ASSETS_EXIST, "Assets not yet created -- skipping facade tests")
class TestHeatmapFacade(unittest.TestCase):
    def test_returns_figure(self):
        import anatomapa
        from anatomapa.render.base import Figure
        fig = anatomapa.heatmap({"head": 10, "trunk": 5})
        self.assertIsInstance(fig, Figure)

    def test_str_returns_svg_string(self):
        import anatomapa
        fig = anatomapa.heatmap({"head": 10, "trunk": 5})
        svg = str(fig)
        self.assertIn("<svg", svg)

    def test_to_svg_returns_string(self):
        import anatomapa
        fig = anatomapa.heatmap({"head": 10, "trunk": 5})
        self.assertIsInstance(fig.to_svg(), str)

    def test_repr_svg_for_jupyter(self):
        import anatomapa
        fig = anatomapa.heatmap({"head": 10})
        self.assertIn("<svg", fig._repr_svg_())

    def test_colors_applied_to_svg(self):
        import anatomapa
        fig = anatomapa.heatmap({"head": 100, "trunk": 0})
        svg = str(fig)
        # SVG deve conter atributo fill com cor hexadecimal
        self.assertIn("fill", svg)
        self.assertIn("#", svg)

    def test_format_default_is_svg(self):
        import anatomapa
        fig = anatomapa.heatmap({"head": 5})
        self.assertEqual(fig._format, "svg")

    def test_title_embedded(self):
        import anatomapa
        fig = anatomapa.heatmap({"head": 5}, title="Meu Mapa")
        svg = str(fig)
        self.assertIn("Meu Mapa", svg)

    def test_list_regions_returns_list(self):
        import anatomapa
        regions = anatomapa.list_regions()
        self.assertIsInstance(regions, list)
        self.assertGreater(len(regions), 0)

    def test_list_regions_has_required_fields(self):
        import anatomapa
        regions = anatomapa.list_regions()
        for r in regions:
            self.assertIn("id", r)
            self.assertIn("label", r)
            self.assertIn("bilateral", r)

    def test_invalid_format_raises(self):
        import anatomapa
        with self.assertRaises(ValueError):
            anatomapa.heatmap({"head": 1}, format="gif")

    def test_unknown_region_raises_resolution_error(self):
        import anatomapa
        from anatomapa.resolver.resolver import ResolutionError
        with self.assertRaises(ResolutionError):
            anatomapa.heatmap({"regiao_inexistente_xyz": 5})

    def test_determinism(self):
        import anatomapa
        values = {"head": 10, "trunk": 5}
        fig1 = anatomapa.heatmap(values)
        fig2 = anatomapa.heatmap(values)
        self.assertEqual(str(fig1), str(fig2))


@unittest.skipUnless(_ASSETS_EXIST, "Assets not yet created -- skipping facade tests")
class TestRegionMapAcceptsEnumValues(unittest.TestCase):
    """Tests for region_map with Region members as values, as the manuals use."""

    def test_heatmap_accepts_enum_values_in_region_map(self):
        import anatomapa
        from anatomapa.regions import Region
        fig = anatomapa.heatmap({"CABEÇA": 10}, region_map={"CABEÇA": Region.HEAD})
        self.assertIn("head", str(fig))

    def test_validate_accepts_enum_values_in_region_map(self):
        import anatomapa
        from anatomapa.regions import Region
        report = anatomapa.validate({"MÃO": 3}, region_map={"MÃO": Region.HAND})
        self.assertFalse(report["unresolved"])
        self.assertEqual(report["resolved"]["MÃO"], "hand")


class TestTypedMarker(unittest.TestCase):
    """Tests for the PEP 561 marker, without which type checkers ignore the lib."""

    def test_py_typed_file_exists(self):
        import anatomapa
        package_dir = os.path.dirname(anatomapa.__file__)
        self.assertTrue(os.path.exists(os.path.join(package_dir, "py.typed")))

    def test_py_typed_is_declared_as_package_data(self):
        pyproject = os.path.join(
            os.path.dirname(__file__), "..", "..", "pyproject.toml"
        )
        if not os.path.exists(pyproject):
            self.skipTest("pyproject.toml ausente (instalação sem fontes)")
        with open(pyproject, encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn('"py.typed"', content)


if __name__ == "__main__":
    unittest.main()
