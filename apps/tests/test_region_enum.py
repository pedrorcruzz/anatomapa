"""Tests for the public Region enum: model sync and usage through heatmap."""

import re
import unittest

import anatomapa as am
from anatomapa import Region


class TestRegionEnumSync(unittest.TestCase):
    """Ensures Region never drifts out of sync with regions.json/list_regions."""

    def setUp(self):
        regions = am.list_regions()
        self.canonical = {r["id"] for r in regions}
        self.bilateral = {r["id"] for r in regions if r["bilateral"]}
        self.values = {m.value for m in Region}

    def test_every_canonical_id_has_member(self):
        for rid in self.canonical:
            self.assertIn(rid, self.values, f"id canônico {rid!r} sem membro em Region")

    def test_every_bilateral_has_left_and_right(self):
        for rid in self.bilateral:
            self.assertIn(f"{rid}_left", self.values)
            self.assertIn(f"{rid}_right", self.values)

    def test_every_member_value_maps_to_model(self):
        valid = set(self.canonical)
        for rid in self.bilateral:
            valid.add(f"{rid}_left")
            valid.add(f"{rid}_right")
        for member in Region:
            self.assertIn(
                member.value, valid, f"membro {member.name} não corresponde a id do modelo"
            )

    def test_member_count_matches_model(self):
        expected = len(self.canonical) + 2 * len(self.bilateral)
        self.assertEqual(len(list(Region)), expected)


class TestRegionEnumUsage(unittest.TestCase):
    """Uso do enum como chave de heatmap e comportamento de string."""

    def _fills(self, svg: str) -> dict[str, str]:
        """Own colour of each hand, unwrapping the blending gradient."""
        fills = {}
        for rid in ("hand-left", "hand-right"):
            match = re.search(r'id="%s"[^>]*fill="([^"]+)"' % rid, svg)
            if not match:
                continue
            fill = match.group(1)
            # No gradiente de mescla, a cor propria e o stop central (0.3)
            if fill.startswith("url(#"):
                grad = re.search(
                    r'id="grad-%s".*?offset="0.3" stop-color="(#[0-9a-f]{6})"' % rid,
                    svg,
                    re.S,
                )
                fill = grad.group(1)
            fills[rid] = fill
        return fills

    def test_member_is_str(self):
        self.assertIsInstance(Region.TRUNK, str)
        self.assertEqual(Region.TRUNK, "trunk")

    def test_heatmap_accepts_members(self):
        svg = str(am.heatmap({Region.TRUNK: 50, Region.HAND_LEFT: 100}))
        self.assertIn("<svg", svg)

    def test_enum_matches_string_output(self):
        by_enum = str(am.heatmap({Region.TRUNK: 50, Region.HAND_LEFT: 100}))
        by_string = str(am.heatmap({"trunk": 50, "hand_left": 100}))
        self.assertEqual(by_enum, by_string)

    def test_canonical_bilateral_colors_both_sides(self):
        fills = self._fills(str(am.heatmap({Region.HAND: 100})))
        self.assertIsNotNone(fills.get("hand-left"))
        self.assertEqual(fills.get("hand-left"), fills.get("hand-right"))

    def test_lateralized_members_differ_per_side(self):
        fills = self._fills(str(am.heatmap({Region.HAND_LEFT: 100, Region.HAND_RIGHT: 1})))
        self.assertNotEqual(fills.get("hand-left"), fills.get("hand-right"))

    def test_construct_from_invalid_value_raises(self):
        with self.assertRaises(ValueError):
            Region("not_a_region")

    def test_exported_in_public_api(self):
        self.assertIn("Region", am.__all__)
        self.assertIs(am.Region, Region)


if __name__ == "__main__":
    unittest.main()
