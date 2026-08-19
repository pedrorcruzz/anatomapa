"""Tests for strict resolution: only exact ids and the user's region_map."""
import unittest
import warnings

from anatomapa.domain.model import AnatomicalModel
from anatomapa.domain.region import Region
from anatomapa.resolver.resolver import ResolutionError, analyze, resolve


def setUpModule():
    """Silence the 0.4 meaning-change notice: these fixtures use the old ids on purpose."""
    warnings.filterwarnings(
        "ignore",
        message="'(leg|arm)' agora é o membro",
        category=DeprecationWarning,
    )



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
        Region(
            id="leg",
            label_pt="Perna",
            label_en="Leg",
            bilateral=True,
            parent=None,
            geometry={"left": "M 0 0 Z", "right": "M 1 1 Z"},
        ),
    )
    return AnatomicalModel(_regions=regions)


class TestResolveExactId(unittest.TestCase):
    def setUp(self):
        self.model = _make_model()

    def test_canonical_id(self):
        result = resolve(["head", "arm"], self.model)
        self.assertEqual(result["head"], "head")
        self.assertEqual(result["arm"], "arm")

    def test_lateralised_id(self):
        result = resolve(["arm_left", "arm_right"], self.model)
        self.assertEqual(result["arm_left"], "arm_left")
        self.assertEqual(result["arm_right"], "arm_right")

    def test_multiple_labels(self):
        result = resolve(["head", "leg", "trunk"], self.model)
        self.assertEqual(len(result), 3)

    def test_side_on_central_region_raises_with_reason(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["head_left"], self.model)
        self.assertIn("central", str(ctx.exception))

    def test_unknown_side_suffix_raises(self):
        with self.assertRaises(ResolutionError):
            resolve(["arm_middle"], self.model)


class TestResolveRejectsGuessing(unittest.TestCase):
    """Nothing is inferred: no accents, case, plurals, labels or side words."""

    def setUp(self):
        self.model = _make_model()

    def test_rejects_uppercase(self):
        with self.assertRaises(ResolutionError):
            resolve(["HEAD"], self.model)

    def test_rejects_surrounding_spaces(self):
        with self.assertRaises(ResolutionError):
            resolve(["  head  "], self.model)

    def test_rejects_accented_portuguese_name(self):
        with self.assertRaises(ResolutionError):
            resolve(["Cabeça"], self.model)

    def test_rejects_label_pt(self):
        with self.assertRaises(ResolutionError):
            resolve(["Tronco"], self.model)

    def test_rejects_label_en(self):
        with self.assertRaises(ResolutionError):
            resolve(["Trunk"], self.model)

    def test_rejects_plural(self):
        with self.assertRaises(ResolutionError):
            resolve(["arms"], self.model)

    def test_rejects_hyphen(self):
        with self.assertRaises(ResolutionError):
            resolve(["arm-left"], self.model)

    def test_rejects_side_spelled_out(self):
        with self.assertRaises(ResolutionError):
            resolve(["braco direito"], self.model)


class TestRegionMap(unittest.TestCase):
    def setUp(self):
        self.model = _make_model()

    def test_maps_custom_label(self):
        result = resolve(["meu_label"], self.model, region_map={"meu_label": "arm"})
        self.assertEqual(result["meu_label"], "arm")

    def test_maps_to_lateralised_id(self):
        result = resolve(
            ["Membro Sup Dir"], self.model, region_map={"Membro Sup Dir": "arm_right"}
        )
        self.assertEqual(result["Membro Sup Dir"], "arm_right")

    def test_maps_portuguese_spreadsheet_label(self):
        result = resolve(["CABEÇA"], self.model, region_map={"CABEÇA": "head"})
        self.assertEqual(result["CABEÇA"], "head")

    def test_key_must_match_exactly(self):
        with self.assertRaises(ResolutionError):
            resolve(["cabeça"], self.model, region_map={"CABEÇA": "head"})

    def test_invalid_target_raises(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["x"], self.model, region_map={"x": "nao_existe"})
        self.assertIn("region_map", str(ctx.exception))

    def test_target_with_side_on_central_region_raises(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["x"], self.model, region_map={"x": "head_left"})
        self.assertIn("central", str(ctx.exception))


class TestErrorsAndSuggestions(unittest.TestCase):
    def setUp(self):
        self.model = _make_model()

    def test_typo_gets_suggestion(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["heaad"], self.model)
        message = str(ctx.exception)
        self.assertIn("heaad", message)
        self.assertIn("head", message)

    def test_error_points_to_list_regions(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["xyzabc123"], self.model)
        self.assertIn("list_regions", str(ctx.exception))

    def test_batches_every_unresolved_label(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["nope1", "nope2"], self.model)
        message = str(ctx.exception)
        self.assertIn("nope1", message)
        self.assertIn("nope2", message)
        self.assertIn("2 rótulo(s)", message)

    def test_non_strict_omits_unresolved(self):
        result = resolve(["head", "nope"], self.model, strict=False)
        self.assertEqual(result, {"head": "head"})

    def test_analyze_does_not_raise(self):
        report = analyze(["head", "nope"], self.model)
        self.assertEqual(report["resolved"], {"head": "head"})
        self.assertIn("nope", report["unresolved"])
        self.assertIn("suggestions", report["unresolved"]["nope"])


if __name__ == "__main__":
    unittest.main()
