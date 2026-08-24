import unittest

from anatomapa.domain.colormap import ColorMap
from anatomapa.domain.model import AnatomicalModel
from anatomapa.domain.region import Region
from anatomapa.domain.scale import LinearScale, LogScale
from anatomapa.usecases.build import build_heatmap


def _make_model() -> AnatomicalModel:
    regions = (
        Region(
            id="head",
            label_pt="Cabeca",
            label_en="Head",
            bilateral=False,
            parent=None,
            geometry={"center": "M 0 0 Z"},
        ),
        Region(
            id="arm",
            label_pt="Braco",
            label_en="Arm",
            bilateral=True,
            parent=None,
            geometry={"left": "M 0 0 Z", "right": "M 1 1 Z"},
        ),
        Region(
            id="trunk",
            label_pt="Tronco",
            label_en="Trunk",
            bilateral=False,
            parent=None,
            geometry={"center": "M 0 0 Z"},
        ),
    )
    return AnatomicalModel(_regions=regions)


def _make_colormap() -> ColorMap:
    return ColorMap(
        stops=(
            (0.0, (0, 0, 0)),
            (1.0, (255, 255, 255)),
        )
    )


class TestBuildHeatmap(unittest.TestCase):
    def setUp(self):
        self.model = _make_model()
        self.cmap = _make_colormap()
        self.scale = LinearScale()

    def test_returns_heatmap(self):
        from anatomapa.domain.heatmap import Heatmap
        result = build_heatmap(
            {"head": 10.0, "arm": 5.0},
            self.model,
            self.cmap,
            self.scale,
        )
        self.assertIsInstance(result, Heatmap)

    def test_all_input_ids_have_colors(self):
        result = build_heatmap(
            {"head": 10.0, "arm": 5.0},
            self.model,
            self.cmap,
            self.scale,
        )
        self.assertIn("head", result.colors)
        self.assertIn("arm", result.colors)

    def test_highest_value_maps_to_max_color(self):
        result = build_heatmap(
            {"head": 0.0, "arm": 100.0},
            self.model,
            self.cmap,
            self.scale,
        )
        self.assertEqual(result.colors["head"], (0, 0, 0))
        self.assertEqual(result.colors["arm"], (255, 255, 255))

    def test_determinism(self):
        values = {"head": 10.0, "arm": 5.0, "trunk": 1.0}
        r1 = build_heatmap(values, self.model, self.cmap, self.scale)
        r2 = build_heatmap(values, self.model, self.cmap, self.scale)
        self.assertEqual(r1.colors, r2.colors)
        self.assertEqual(r1.value_min, r2.value_min)
        self.assertEqual(r1.value_max, r2.value_max)

    def test_stable_order_independent_of_input_order(self):
        values_a = {"head": 10.0, "arm": 5.0, "trunk": 1.0}
        values_b = {"trunk": 1.0, "head": 10.0, "arm": 5.0}
        r1 = build_heatmap(values_a, self.model, self.cmap, self.scale)
        r2 = build_heatmap(values_b, self.model, self.cmap, self.scale)
        self.assertEqual(r1.colors["head"], r2.colors["head"])
        self.assertEqual(r1.colors["arm"], r2.colors["arm"])
        self.assertEqual(r1.colors["trunk"], r2.colors["trunk"])

    def test_value_min_max_stored(self):
        result = build_heatmap(
            {"head": 3.0, "arm": 9.0},
            self.model,
            self.cmap,
            self.scale,
        )
        self.assertAlmostEqual(result.value_min, 3.0)
        self.assertAlmostEqual(result.value_max, 9.0)

    def test_empty_values_returns_empty_heatmap(self):
        result = build_heatmap({}, self.model, self.cmap, self.scale)
        self.assertEqual(result.colors, {})

    def test_log_scale_used(self):
        scale = LogScale()
        result = build_heatmap(
            {"head": 1.0, "arm": 100.0},
            self.model,
            self.cmap,
            scale,
        )
        self.assertIn("head", result.colors)
        self.assertIn("arm", result.colors)
        self.assertEqual(result.scale_name, "LogScale")

    def test_title_stored(self):
        result = build_heatmap(
            {"head": 1.0},
            self.model,
            self.cmap,
            self.scale,
            title="Test Title",
        )
        self.assertEqual(result.title, "Test Title")

    def test_lang_stored(self):
        result = build_heatmap(
            {"head": 1.0},
            self.model,
            self.cmap,
            self.scale,
            lang="en",
        )
        self.assertEqual(result.lang, "en")


if __name__ == "__main__":
    unittest.main()
