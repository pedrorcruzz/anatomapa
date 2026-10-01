"""Tests for title placement and legend tick labels.

The title is drawn after the legend, which has already widened the viewBox to
the right, so it must be centred on the body alone. The tick labels must stay
distinct: rounding to integers collapses them on a narrow range.
"""

import os
import unittest
import xml.etree.ElementTree as ET

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "anatomapa", "assets")
_ASSETS_EXIST = os.path.exists(os.path.join(_ASSETS_DIR, "regions.json"))


def _title_x(svg: str) -> float:
    root = ET.fromstring(svg)
    title = next(e for e in root.iter() if e.get("id") == "figure-title")
    return float(title.get("x"))


def _viewbox(svg: str) -> tuple[float, float, float, float]:
    root = ET.fromstring(svg)
    return tuple(float(v) for v in root.get("viewBox").split())


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestTitleCentring(unittest.TestCase):
    """The title sits over the body, never pulled towards the legend."""

    def test_single_view_title_is_centred_on_the_body(self):
        import anatomapa
        from anatomapa.render.svg import _LEGEND_WIDTH_RATIO

        svg = str(anatomapa.heatmap({"hand": 1}, title="Ferimentos"))
        vx, _, vw, _ = _viewbox(svg)
        body_w = vw / (1.0 + _LEGEND_WIDTH_RATIO)
        self.assertAlmostEqual(_title_x(svg), vx + body_w / 2.0, places=1)

    def test_title_is_left_of_the_full_viewbox_centre(self):
        import anatomapa

        svg = str(anatomapa.heatmap({"hand": 1}, title="Ferimentos"))
        vx, _, vw, _ = _viewbox(svg)
        self.assertLess(
            _title_x(svg),
            vx + vw / 2.0,
            "o título não pode ser centrado no viewBox alargado pela legenda",
        )

    def test_both_views_title_is_centred_on_the_two_panels(self):
        import anatomapa
        from anatomapa.render.svg import _LEGEND_WIDTH_RATIO

        svg = str(anatomapa.heatmap({"hand": 1}, view="both", title="Frente e costas"))
        vx, _, vw, _ = _viewbox(svg)
        body_w = vw / (1.0 + _LEGEND_WIDTH_RATIO)
        self.assertAlmostEqual(_title_x(svg), vx + body_w / 2.0, places=1)

    def test_without_legend_the_whole_viewbox_is_the_body(self):
        from anatomapa.render.svg import _body_width

        root = ET.fromstring('<svg viewBox="0 0 540 960"><g id="regions"/></svg>')
        self.assertEqual(_body_width(root, 540.0), 540.0)


class TestTickLabels(unittest.TestCase):
    """Tick labels grow decimals only when integers would repeat."""

    def test_wide_range_keeps_integers(self):
        from anatomapa.render.svg import _compute_ticks, _format_ticks

        labels = _format_ticks(_compute_ticks(850.0, 13666.0))
        self.assertEqual(labels, ["850", "4054", "7258", "10462", "13666"])

    def test_narrow_range_gains_decimals(self):
        from anatomapa.render.svg import _compute_ticks, _format_ticks

        labels = _format_ticks(_compute_ticks(2.0, 5.0))
        self.assertEqual(len(set(labels)), len(labels))
        self.assertIn(".", labels[0])

    def test_single_value_gives_one_label(self):
        from anatomapa.render.svg import _compute_ticks, _format_ticks

        self.assertEqual(_format_ticks(_compute_ticks(3.0, 3.0)), ["3"])

    def test_very_tight_range_still_distinct(self):
        from anatomapa.render.svg import _format_ticks

        labels = _format_ticks([1.0, 1.002, 1.004, 1.006, 1.008])
        self.assertEqual(len(set(labels)), 5)

    def test_repeated_values_are_allowed_to_repeat(self):
        from anatomapa.render.svg import _format_ticks

        self.assertEqual(_format_ticks([2.0, 2.0]), ["2", "2"])

    @unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
    def test_rendered_legend_has_no_duplicate_tick(self):
        import anatomapa

        svg = str(anatomapa.heatmap({"hand": 2, "foot": 5}))
        root = ET.fromstring(svg)
        texts = [
            e.text
            for e in root.iter()
            if e.tag.endswith("text") and e.get("id") is None and e.text
        ]
        numeric = [t for t in texts if t.replace(".", "").replace("-", "").isdigit()]
        self.assertEqual(len(numeric), len(set(numeric)), numeric)


if __name__ == "__main__":
    unittest.main()
