"""Optional snapshot test for SVG render output.

Skipped when assets are absent.
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


@unittest.skipUnless(_ASSETS_EXIST, "Assets not yet created -- skipping snapshot tests")
class TestSvgRenderSnapshot(unittest.TestCase):
    def _render(self, values, **kwargs):
        import anatomapa
        return str(anatomapa.heatmap(values, **kwargs))

    def test_svg_is_well_formed_xml(self):
        import xml.etree.ElementTree as ET
        svg = self._render({"head": 5, "trunk": 10})
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            self.fail(f"Rendered SVG is not well-formed XML: {e}")

    def test_svg_has_viewbox(self):
        svg = self._render({"head": 5})
        self.assertIn("viewBox", svg)

    def test_bilateral_regions_painted_both_sides(self):
        svg = self._render({"arm": 50})
        self.assertIn("arm-left", svg)
        self.assertIn("arm-right", svg)

    def test_fill_attribute_present_on_paths(self):
        import xml.etree.ElementTree as ET
        svg = self._render({"head": 10})
        root = ET.fromstring(svg)
        paths_with_fill = [
            elem for elem in root.iter()
            if (elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag) == "path"
            and elem.get("fill")
        ]
        self.assertGreater(len(paths_with_fill), 0)

    def test_deterministic_output(self):
        values = {"head": 10, "trunk": 5, "arm": 7}
        svg1 = self._render(values)
        svg2 = self._render(values)
        self.assertEqual(svg1, svg2)

    def test_lang_does_not_break_render(self):
        svg_pt = self._render({"head": 5}, lang="pt")
        svg_en = self._render({"head": 5}, lang="en")
        self.assertIn("<svg", svg_pt)
        self.assertIn("<svg", svg_en)


if __name__ == "__main__":
    unittest.main()
