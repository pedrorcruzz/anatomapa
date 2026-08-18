"""Tests for the drawn figure title.

The title is opt-in: without it the layout must stay byte-for-byte the same as
before, and with it a band is added above the drawing.
"""

import os
import unittest
import xml.etree.ElementTree as ET

import anatomapa
from anatomapa.render.svg import _append_title, _viewbox_of

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "anatomapa", "assets")
_ASSETS_EXIST = os.path.exists(os.path.join(_ASSETS_DIR, "body_male_anterior.svg"))

_VALUES = {"head": 10.0, "hand": 40.0, "foot": 90.0}


def _title_text(svg: str) -> str | None:
    """Text of the drawn title element, or None when it was not drawn."""
    root = ET.fromstring(svg)
    for elem in root.iter():
        if elem.get("id") == "figure-title":
            return elem.text
    return None


def _viewbox(svg: str) -> tuple[float, float, float, float]:
    """viewBox of a rendered SVG string, as (min-x, min-y, width, height)."""
    return _viewbox_of(ET.fromstring(svg))


class TestTitleIsOptional(unittest.TestCase):
    def test_viewbox_of_falls_back_when_malformed(self):
        root = ET.Element("svg")
        root.set("viewBox", "0 0 10")
        self.assertEqual(_viewbox_of(root), (0.0, 0.0, 400.0, 900.0))

    def test_viewbox_of_falls_back_when_not_numeric(self):
        root = ET.Element("svg")
        root.set("viewBox", "a b c d")
        self.assertEqual(_viewbox_of(root), (0.0, 0.0, 400.0, 900.0))

    def test_append_title_does_nothing_without_title(self):
        root = ET.Element("svg")
        root.set("viewBox", "0 0 100 200")
        _append_title(root, None, "dark")
        self.assertEqual(root.get("viewBox"), "0 0 100 200")
        self.assertEqual(len(root), 0)

    def test_append_title_ignores_empty_string(self):
        root = ET.Element("svg")
        root.set("viewBox", "0 0 100 200")
        _append_title(root, "", "dark")
        self.assertEqual(root.get("viewBox"), "0 0 100 200")


class TestTitleBand(unittest.TestCase):
    def _rendered(self, background: str = "dark") -> ET.Element:
        root = ET.Element("svg")
        root.set("viewBox", "0 0 100 200")
        rect = ET.SubElement(root, "rect")
        rect.set("id", "figure-background")
        rect.set("y", "0")
        rect.set("height", "200")
        _append_title(root, "Mapa", background)
        return root

    def test_viewbox_grows_upwards_only(self):
        root = self._rendered()
        vx, vy, vw, vh = _viewbox_of(root)
        self.assertEqual((vx, vw), (0.0, 100.0))
        self.assertLess(vy, 0.0)
        # A altura cresce exatamente o quanto o topo subiu
        self.assertAlmostEqual(vh, 200.0 - vy, places=2)

    def test_background_rect_follows_the_new_viewbox(self):
        root = self._rendered()
        _, vy, _, vh = _viewbox_of(root)
        rect = [e for e in root if e.get("id") == "figure-background"][0]
        self.assertAlmostEqual(float(rect.get("y")), vy, places=2)
        self.assertAlmostEqual(float(rect.get("height")), vh, places=2)

    def test_text_is_centred_and_inside_the_band(self):
        root = self._rendered()
        _, vy, vw, _ = _viewbox_of(root)
        text = [e for e in root if e.get("id") == "figure-title"][0]
        self.assertEqual(text.text, "Mapa")
        self.assertEqual(text.get("text-anchor"), "middle")
        self.assertAlmostEqual(float(text.get("x")), vw / 2.0, places=2)
        self.assertGreater(float(text.get("y")), vy)
        self.assertLess(float(text.get("y")), 0.0)

    def test_colour_adapts_to_the_background(self):
        dark = [e for e in self._rendered("dark") if e.get("id") == "figure-title"][0]
        light = [e for e in self._rendered("light") if e.get("id") == "figure-title"][0]
        self.assertNotEqual(dark.get("fill"), light.get("fill"))

    def test_long_title_shrinks_to_fit_the_width(self):
        short = ET.Element("svg")
        short.set("viewBox", "0 0 100 200")
        _append_title(short, "Curto", "dark")

        long_root = ET.Element("svg")
        long_root.set("viewBox", "0 0 100 200")
        _append_title(long_root, "T" * 200, "dark")

        short_size = float([e for e in short if e.get("id") == "figure-title"][0].get("font-size"))
        long_size = float([e for e in long_root if e.get("id") == "figure-title"][0].get("font-size"))
        self.assertLess(long_size, short_size)
        # A faixa não encolhe junto: as duas figuras crescem o mesmo tanto
        self.assertEqual(short.get("viewBox"), long_root.get("viewBox"))


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestTitleEndToEnd(unittest.TestCase):
    def test_no_title_keeps_the_layout_untouched(self):
        svg = anatomapa.heatmap(_VALUES).to_svg()
        self.assertIsNone(_title_text(svg))

    def test_title_is_drawn_in_a_single_view(self):
        svg = anatomapa.heatmap(_VALUES, title="Picadas").to_svg()
        self.assertEqual(_title_text(svg), "Picadas")

    def test_title_is_drawn_in_both_views(self):
        svg = anatomapa.heatmap(_VALUES, view="both", title="Picadas").to_svg()
        self.assertEqual(_title_text(svg), "Picadas")

    def test_title_is_drawn_in_each_split_figure(self):
        front, back = anatomapa.heatmap(
            _VALUES, view="both", split=True, title="Picadas"
        )
        self.assertEqual(_title_text(front.to_svg()), "Picadas")
        self.assertEqual(_title_text(back.to_svg()), "Picadas")

    def test_title_only_grows_the_figure_upwards(self):
        plain = _viewbox(anatomapa.heatmap(_VALUES).to_svg())
        titled = _viewbox(anatomapa.heatmap(_VALUES, title="Picadas").to_svg())
        self.assertEqual(plain[0], titled[0])
        self.assertEqual(plain[2], titled[2])
        self.assertLess(titled[1], plain[1])
        self.assertGreater(titled[3], plain[3])

    def test_title_is_also_svg_metadata(self):
        svg = anatomapa.heatmap(_VALUES, title="Picadas").to_svg()
        root = ET.fromstring(svg)
        titles = [e for e in root if e.tag.split("}")[-1] == "title"]
        self.assertEqual([e.text for e in titles], ["Picadas"])

    def test_title_is_drawn_in_the_raster_variant_too(self):
        figure = anatomapa.heatmap(_VALUES, title="Picadas")
        self.assertEqual(_title_text(figure._svg_for_raster()), "Picadas")


if __name__ == "__main__":
    unittest.main()
