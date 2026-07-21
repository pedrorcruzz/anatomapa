import unittest

from anatomapa.domain.model import AnatomicalModel
from anatomapa.domain.region import Region
from anatomapa.resolver.normalize import slugify
from anatomapa.resolver.resolver import ResolutionError, resolve


def _make_model() -> AnatomicalModel:
    regions = (
        Region(
            id="head",
            label_pt="Cabeca",
            label_en="Head",
            aliases=("cabeca", "cranio", "skull"),
            bilateral=False,
            parent=None,
            geometry={"center": "M 0 0 Z"},
        ),
        Region(
            id="arm",
            label_pt="Braco",
            label_en="Arm",
            aliases=("braco", "upper_arm"),
            bilateral=True,
            parent=None,
            geometry={"left": "M 0 0 Z", "right": "M 1 1 Z"},
        ),
        Region(
            id="trunk",
            label_pt="Tronco",
            label_en="Trunk",
            aliases=("torso", "thorax"),
            bilateral=False,
            parent=None,
            geometry={"center": "M 0 0 Z"},
        ),
        Region(
            id="leg",
            label_pt="Perna",
            label_en="Leg",
            aliases=("perna",),
            bilateral=True,
            parent=None,
            geometry={"left": "M 0 0 Z", "right": "M 1 1 Z"},
        ),
    )
    return AnatomicalModel(_regions=regions)


class TestSlugify(unittest.TestCase):
    def test_lowercase(self):
        self.assertEqual(slugify("HEAD"), "head")

    def test_strips_accents(self):
        self.assertEqual(slugify("Cabeça"), "cabeca")

    def test_hyphen_to_underscore(self):
        self.assertEqual(slugify("arm-left"), "arm_left")

    def test_space_to_underscore(self):
        self.assertEqual(slugify("upper arm"), "upper_arm")

    def test_trim_whitespace(self):
        self.assertEqual(slugify("  head  "), "head")

    def test_combined(self):
        self.assertEqual(slugify(" Braço Esquerdo "), "braco_esquerdo")


class TestResolve(unittest.TestCase):
    def setUp(self):
        self.model = _make_model()

    def test_exact_match(self):
        result = resolve(["head", "arm"], self.model)
        self.assertEqual(result["head"], "head")
        self.assertEqual(result["arm"], "arm")

    def test_match_with_accent(self):
        result = resolve(["Cabeça"], self.model)
        self.assertEqual(result["Cabeça"], "head")

    def test_match_with_hyphen(self):
        result = resolve(["upper-arm"], self.model)
        self.assertEqual(result["upper-arm"], "arm")

    def test_match_with_camelcase(self):
        # CamelCase não remove underscores mas slugify deixa comparação case-insensitive
        result = resolve(["HEAD"], self.model)
        self.assertEqual(result["HEAD"], "head")

    def test_match_with_trailing_space(self):
        result = resolve(["  head  "], self.model)
        self.assertEqual(result["  head  "], "head")

    def test_alias_pt(self):
        result = resolve(["cranio"], self.model)
        self.assertEqual(result["cranio"], "head")

    def test_alias_en(self):
        result = resolve(["skull"], self.model)
        self.assertEqual(result["skull"], "head")

    def test_label_pt_match(self):
        result = resolve(["Tronco"], self.model)
        self.assertEqual(result["Tronco"], "trunk")

    def test_label_en_match(self):
        result = resolve(["Trunk"], self.model)
        self.assertEqual(result["Trunk"], "trunk")

    def test_region_map_custom(self):
        result = resolve(["meu_label"], self.model, region_map={"meu_label": "arm"})
        self.assertEqual(result["meu_label"], "arm")

    def test_unknown_label_raises_with_suggestion(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["heaad"], self.model)
        self.assertIn("heaad", str(ctx.exception))

    def test_completely_unknown_label_raises(self):
        with self.assertRaises(ResolutionError):
            resolve(["xyzabc123"], self.model)

    def test_multiple_labels(self):
        result = resolve(["head", "Perna", "torso"], self.model)
        self.assertEqual(result["head"], "head")
        self.assertEqual(result["Perna"], "leg")
        self.assertEqual(result["torso"], "trunk")


if __name__ == "__main__":
    unittest.main()
