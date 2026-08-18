"""Tests for the view parameter: anterior, posterior and both."""
import inspect
import os
import re
import typing
import unittest
import xml.etree.ElementTree as ET

import anatomapa as am
from anatomapa.regions import Region

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "anatomapa", "assets")
_ASSETS_EXIST = all(
    os.path.exists(os.path.join(_ASSETS_DIR, name))
    for name in (
        "body_male_anterior.svg",
        "body_male_posterior.svg",
        "body_female_posterior.svg",
        "regions.json",
    )
)


def _ids(svg: str) -> set[str]:
    root = ET.fromstring(svg)
    return {e.get("id") for e in root.iter() if e.get("id")}


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestViewParameter(unittest.TestCase):
    def test_default_is_anterior(self):
        self.assertEqual(str(am.heatmap({"hand": 1})), str(am.heatmap({"hand": 1}, view="anterior")))

    def test_invalid_view_raises(self):
        with self.assertRaises(ValueError) as ctx:
            am.heatmap({"hand": 1}, view="lateral")
        self.assertIn("view", str(ctx.exception))

    def test_anterior_has_front_trunk_regions(self):
        ids = _ids(str(am.heatmap({"chest": 5, "abdomen": 3, "pelvis": 1})))
        self.assertIn("chest", ids)
        self.assertIn("abdomen", ids)
        self.assertNotIn("back", ids)
        self.assertNotIn("buttocks", ids)

    def test_posterior_has_back_trunk_regions(self):
        ids = _ids(str(am.heatmap({"back": 5, "buttocks": 1}, view="posterior")))
        self.assertIn("back", ids)
        self.assertIn("buttocks", ids)
        self.assertNotIn("chest", ids)
        self.assertNotIn("abdomen", ids)

    def test_posterior_accepts_shared_regions(self):
        svg = str(am.heatmap({Region.HAND: 10, Region.FOOT: 20}, view="posterior"))
        self.assertIn("<svg", svg)

    def test_posterior_differs_from_anterior(self):
        self.assertNotEqual(
            str(am.heatmap({"hand": 10})),
            str(am.heatmap({"hand": 10}, view="posterior")),
        )

    def test_female_posterior_renders(self):
        svg = str(am.heatmap({"back": 4}, view="posterior", body="female"))
        self.assertIn("back", _ids(svg))


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestBothViews(unittest.TestCase):
    def setUp(self):
        self.svg = str(am.heatmap({"trunk": 100, "hand": 50}, view="both"))

    def test_has_one_group_per_view(self):
        ids = _ids(self.svg)
        self.assertIn("anterior-view", ids)
        self.assertIn("posterior-view", ids)

    def test_ids_are_namespaced_per_panel(self):
        ids = _ids(self.svg)
        self.assertIn("anterior-hand-left", ids)
        self.assertIn("posterior-hand-left", ids)

    def test_front_and_back_trunk_regions_both_present(self):
        ids = _ids(self.svg)
        self.assertIn("anterior-chest", ids)
        self.assertIn("posterior-back", ids)
        self.assertIn("posterior-buttocks", ids)

    def test_single_legend_and_background(self):
        self.assertEqual(self.svg.count('id="legend-bar"'), 1)
        dark = str(am.heatmap({"hand": 1}, view="both", background="dark"))
        self.assertEqual(dark.count('id="figure-background"'), 1)

    def test_background_covers_the_legend_strip(self):
        root = ET.fromstring(str(am.heatmap({"hand": 1}, view="both", background="dark")))
        rect = next(e for e in root.iter() if e.get("id") == "figure-background")
        total_w = float(root.get("viewBox").split()[2])
        self.assertGreaterEqual(float(rect.get("width")), total_w)

    def test_viewbox_is_wider_than_one_panel(self):
        one = ET.fromstring(str(am.heatmap({"hand": 1}))).get("viewBox")
        both = ET.fromstring(self.svg).get("viewBox")
        self.assertGreater(float(both.split()[2]), float(one.split()[2]))

    def test_panels_are_offset(self):
        root = ET.fromstring(self.svg)
        groups = {
            e.get("id"): e.get("transform")
            for e in root.iter()
            if e.get("id") in ("anterior-view", "posterior-view")
        }
        self.assertIn("translate(0", groups["anterior-view"])
        offset = float(re.search(r"translate\(([\d.]+)", groups["posterior-view"]).group(1))
        self.assertGreater(offset, 0.0)

    def test_deterministic(self):
        self.assertEqual(
            str(am.heatmap({"trunk": 100, "hand": 50}, view="both")),
            str(am.heatmap({"trunk": 100, "hand": 50}, view="both")),
        )

    def test_title_appears_once(self):
        svg = str(am.heatmap({"hand": 1}, view="both", title="Frente e costas"))
        self.assertEqual(svg.count("<title>"), 1)
        self.assertIn("Frente e costas", svg)


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestSplitParameter(unittest.TestCase):
    """Tests for split=True: view="both" as two independent figures."""

    def test_split_returns_two_figures(self):
        anterior, posterior = am.heatmap(
            {"hand": 5, "buttocks": 2}, view="both", split=True
        )
        self.assertIn("hand-left", _ids(str(anterior)))
        self.assertIn("buttocks", _ids(str(posterior)))
        self.assertNotIn("buttocks", _ids(str(anterior)))

    def test_split_figures_have_own_legend_and_no_prefix(self):
        anterior, posterior = am.heatmap({"hand": 5}, view="both", split=True)
        for svg in (str(anterior), str(posterior)):
            self.assertIn("legend-bar", svg)
            self.assertNotIn("anterior-hand-left", svg)
            self.assertNotIn("posterior-hand-left", svg)

    def test_split_matches_single_view_render(self):
        # Cada figura do par é idêntica à vista renderizada sozinha
        anterior, posterior = am.heatmap({"hand": 5}, view="both", split=True)
        self.assertEqual(str(anterior), str(am.heatmap({"hand": 5}, view="anterior")))
        self.assertEqual(str(posterior), str(am.heatmap({"hand": 5}, view="posterior")))

    def test_split_keeps_format(self):
        anterior, _ = am.heatmap({"hand": 5}, view="both", split=True, format="png")
        self.assertNotIn("feGaussianBlur", str(anterior))

    def test_split_requires_both(self):
        with self.assertRaises(ValueError):
            am.heatmap({"hand": 5}, view="anterior", split=True)
        with self.assertRaises(ValueError):
            am.heatmap({"hand": 5}, view="posterior", split=True)


@unittest.skipUnless(
    hasattr(typing, "get_overloads"), "typing.get_overloads exige Python 3.11+"
)
class TestHeatmapOverloads(unittest.TestCase):
    """Tests for the typed overloads that make the return type of heatmap precise."""

    def test_declares_the_three_overloads(self):
        overloads = typing.get_overloads(am.heatmap)
        self.assertEqual(len(overloads), 3)

    def test_each_overload_accepts_the_full_signature(self):
        params = list(inspect.signature(am.heatmap).parameters)
        for over in typing.get_overloads(am.heatmap):
            self.assertEqual(list(inspect.signature(over).parameters), params)

    def test_split_literal_drives_the_return_type(self):
        hints = [
            typing.get_type_hints(over)
            for over in typing.get_overloads(am.heatmap)
        ]
        by_split = {str(h["split"]): str(h["return"]) for h in hints}
        self.assertIn("Figure]", by_split["typing.Literal[True]"])
        self.assertNotIn("tuple", by_split["typing.Literal[False]"])


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestListRegionsPerView(unittest.TestCase):
    def test_lists_every_region_by_default(self):
        ids = {r["id"] for r in am.list_regions()}
        self.assertIn("chest", ids)
        self.assertIn("back", ids)
        self.assertIn("buttocks", ids)

    def test_anterior_hides_back_regions(self):
        ids = {r["id"] for r in am.list_regions(view="anterior")}
        self.assertIn("chest", ids)
        self.assertNotIn("back", ids)
        self.assertNotIn("buttocks", ids)

    def test_posterior_hides_front_regions(self):
        ids = {r["id"] for r in am.list_regions(view="posterior")}
        self.assertIn("back", ids)
        self.assertIn("buttocks", ids)
        self.assertNotIn("chest", ids)
        self.assertNotIn("pelvis", ids)

    def test_aggregator_appears_in_both_views(self):
        for view in ("anterior", "posterior"):
            ids = {r["id"] for r in am.list_regions(view=view)}
            self.assertIn("trunk", ids, f"trunk deveria valer na vista {view}")

    def test_views_field_is_exposed(self):
        by_id = {r["id"]: r for r in am.list_regions()}
        self.assertEqual(by_id["chest"]["views"], ["anterior"])
        self.assertEqual(by_id["back"]["views"], ["posterior"])
        self.assertEqual(by_id["trunk"]["views"], [])
        self.assertIn("anterior", by_id["hand"]["views"])
        self.assertIn("posterior", by_id["hand"]["views"])

    def test_invalid_view_raises(self):
        with self.assertRaises(ValueError):
            am.list_regions(view="both")


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestRasterUsesFlatFill(unittest.TestCase):
    """Raster output must avoid SVG filters, which converters do not implement."""

    def test_svg_keeps_the_gradient(self):
        svg = str(am.heatmap({"hand": 5}))
        self.assertIn("filter=", svg)
        self.assertIn("mask=", svg)

    def test_raster_drops_filter_and_mask(self):
        for fmt in ("png", "jpg", "jpeg"):
            with self.subTest(format=fmt):
                flat = am.heatmap({"hand": 5}, format=fmt).to_svg()
                self.assertNotIn("filter=", flat)
                self.assertNotIn("mask=", flat)

    def test_raster_keeps_legend_and_colors(self):
        flat = am.heatmap({"hand": 5, "foot": 100}, format="png").to_svg()
        self.assertIn("legend-bar", flat)
        self.assertIn("hand-left", flat)

    def test_raster_both_views_still_composes(self):
        flat = am.heatmap({"trunk": 10}, view="both", format="png").to_svg()
        self.assertNotIn("filter=", flat)
        self.assertIn("anterior-view", flat)
        self.assertIn("posterior-view", flat)


class TestButtocksRegion(unittest.TestCase):
    def test_enum_member_exists(self):
        self.assertEqual(Region.BUTTOCKS, "buttocks")

    def test_enum_member_is_usable(self):
        self.assertIn(Region.BUTTOCKS, list(Region))


if __name__ == "__main__":
    unittest.main()
