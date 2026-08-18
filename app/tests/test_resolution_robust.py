"""Tests for robust label resolution: sides, plurals, synonyms, region_map
precedence, batched errors, on_unknown, validate and per-side rendering."""
import os
import unittest
import warnings
import xml.etree.ElementTree as ET

import anatomapa as am
from anatomapa.domain.heatmap import Heatmap
from anatomapa.domain.model import AnatomicalModel
from anatomapa.domain.region import Region
from anatomapa.render.svg import SvgRenderer, _canonical_and_side, _color_for
from anatomapa.resolver.resolver import (
    ResolutionError,
    _extract_side,
    _plural_variants,
    analyze,
    resolve,
)

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "anatomapa", "assets")
_ASSETS_EXIST = os.path.exists(
    os.path.join(_ASSETS_DIR, "body_male_anterior.svg")
) and os.path.exists(os.path.join(_ASSETS_DIR, "regions.json"))


def _model() -> AnatomicalModel:
    return AnatomicalModel(
        _regions=(
            Region("head", "Cabeça", "Head", ("cabeca", "cranio"), False, None, {"center": "M0 0Z"}),
            Region("hand", "Mão", "Hand", ("mao", "palm"), True, None, {"left": "M0 0Z", "right": "M1 1Z"}),
            Region("foot", "Pé", "Foot", ("pe",), True, None, {"left": "M0 0Z", "right": "M1 1Z"}),
            Region("trunk", "Tronco", "Trunk", ("torso",), False, None, {"center": "M0 0Z"}),
        )
    )


def _fills_by_id(svg: str) -> dict[str, str]:
    root = ET.fromstring(svg)
    return {e.get("id"): e.get("fill") for e in root.iter() if e.get("id")}


class TestLateralResolve(unittest.TestCase):
    def setUp(self):
        self.model = _model()

    def test_bare_name_is_bilateral(self):
        self.assertEqual(resolve(["mão"], self.model)["mão"], "hand")

    def test_pt_right(self):
        self.assertEqual(resolve(["mão direita"], self.model)["mão direita"], "hand_right")

    def test_pt_left(self):
        self.assertEqual(resolve(["mão esquerda"], self.model)["mão esquerda"], "hand_left")

    def test_en_side_before(self):
        self.assertEqual(resolve(["right hand"], self.model)["right hand"], "hand_right")

    def test_en_side_after(self):
        self.assertEqual(resolve(["hand left"], self.model)["hand left"], "hand_left")

    def test_underscore_id(self):
        self.assertEqual(resolve(["hand_right"], self.model)["hand_right"], "hand_right")
        self.assertEqual(resolve(["right_hand"], self.model)["right_hand"], "hand_right")

    def test_abbrev_side(self):
        self.assertEqual(resolve(["pe dir"], self.model)["pe dir"], "foot_right")
        self.assertEqual(resolve(["pe esq"], self.model)["pe esq"], "foot_left")

    def test_central_with_side_is_error(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["cabeça direita"], self.model)
        self.assertIn("central", str(ctx.exception))

    def test_central_with_side_in_analyze(self):
        report = analyze(["cabeça esquerda"], self.model)
        self.assertIn("cabeça esquerda", report["unresolved"])
        self.assertIn("central", report["unresolved"]["cabeça esquerda"]["reason"])

    def test_extract_side_helper(self):
        self.assertEqual(_extract_side("mao_direita"), ("mao", "right"))
        self.assertEqual(_extract_side("left_hand"), ("hand", "left"))
        self.assertEqual(_extract_side("mao"), ("mao", None))


class TestPlurals(unittest.TestCase):
    def setUp(self):
        self.model = _model()

    def test_regular_plural(self):
        self.assertEqual(resolve(["maos"], self.model)["maos"], "hand")

    def test_plural_via_alias(self):
        self.assertEqual(resolve(["pes"], self.model)["pes"], "foot")

    def test_irregular_feet(self):
        self.assertEqual(resolve(["feet"], self.model)["feet"], "foot")

    def test_plural_variants_helper(self):
        self.assertIn("hand", _plural_variants("hands"))
        self.assertIn("foot", _plural_variants("feet"))
        self.assertIn("box", _plural_variants("boxes"))


class TestRegionMap(unittest.TestCase):
    def setUp(self):
        self.model = _model()

    def test_exact(self):
        r = resolve(["MinhaVar"], self.model, region_map={"MinhaVar": "hand"})
        self.assertEqual(r["MinhaVar"], "hand")

    def test_by_slug(self):
        # chave do region_map com acento/caixa diferente ainda casa por slug
        r = resolve(["braço x"], self.model, region_map={"braco_x": "hand"})
        self.assertEqual(r["braço x"], "hand")

    def test_to_lateral_id(self):
        r = resolve(["right_hand"], self.model, region_map={"right_hand": "hand_right"})
        self.assertEqual(r["right_hand"], "hand_right")

    def test_precedence_over_canonical(self):
        # region_map vence o match canônico
        r = resolve(["mao"], self.model, region_map={"mao": "foot"})
        self.assertEqual(r["mao"], "foot")


class TestBatchErrors(unittest.TestCase):
    def setUp(self):
        self.model = _model()

    def test_all_unresolved_listed(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["pedro", "xpto", "mao"], self.model)
        msg = str(ctx.exception)
        self.assertIn("pedro", msg)
        self.assertIn("xpto", msg)
        self.assertIn("2", msg)  # conta 2 não resolvidos

    def test_non_strict_returns_partial(self):
        r = resolve(["mao", "pedro"], self.model, strict=False)
        self.assertEqual(r, {"mao": "hand"})

    def test_analyze_reports_suggestions(self):
        report = analyze(["heaad"], self.model)
        self.assertIn("heaad", report["unresolved"])
        self.assertTrue(report["unresolved"]["heaad"]["suggestions"])


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestFacadeOnUnknown(unittest.TestCase):
    def test_default_error(self):
        with self.assertRaises(ResolutionError):
            am.heatmap({"mao": 1, "pedro": 2})

    def test_skip(self):
        fig = am.heatmap({"mao": 10, "pedro": 5}, on_unknown="skip")
        self.assertIn("<svg", str(fig))

    def test_warn(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            am.heatmap({"mao": 10, "pedro": 5}, on_unknown="warn")
        self.assertTrue(any("pedro" in str(x.message) for x in w))

    def test_invalid_on_unknown(self):
        with self.assertRaises(ValueError):
            am.heatmap({"mao": 1}, on_unknown="explode")


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestFacadeExtras(unittest.TestCase):
    def test_accepts_pairs(self):
        pares = am.from_dict({"mao": 10, "pe": 20})
        fig = am.heatmap(pares)
        self.assertIn("<svg", str(fig))

    def test_accepts_records_output(self):
        recs = [{"r": "mao", "v": 5}, {"r": "pe", "v": 9}]
        data = am.from_records(recs, region_col="r", value_col="v")
        fig = am.heatmap(data)
        self.assertIn("<svg", str(fig))

    def test_validate_dry_run(self):
        report = am.validate({"mao": 1, "pedro": 2, "mão direita": 3})
        self.assertEqual(report["resolved"]["mao"], "hand")
        self.assertEqual(report["resolved"]["mão direita"], "hand_right")
        self.assertIn("pedro", report["unresolved"])

    def test_plural_and_synonym_via_facade(self):
        report = am.validate({"maos": 1, "biceps": 1, "quadriceps": 1, "joelho": 1})
        self.assertEqual(report["resolved"]["maos"], "hand")
        self.assertEqual(report["resolved"]["biceps"], "arm")
        self.assertEqual(report["resolved"]["quadriceps"], "thigh")
        self.assertEqual(report["resolved"]["joelho"], "leg")


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestRenderPerSide(unittest.TestCase):
    def test_sides_get_distinct_colors(self):
        svg = str(am.heatmap({"mão direita": 100, "mão esquerda": 1, "tronco": 50}))
        fills = _fills_by_id(svg)
        self.assertIn("hand-left", fills)
        self.assertIn("hand-right", fills)
        self.assertNotEqual(fills["hand-left"], fills["hand-right"])

    def test_bilateral_paints_both_equal(self):
        svg = str(am.heatmap({"mão": 100, "tronco": 1}))
        fills = _fills_by_id(svg)
        self.assertEqual(fills["hand-left"], fills["hand-right"])

    def test_smooth_per_side(self):
        svg = str(am.heatmap({"mão direita": 100, "mão esquerda": 1}))
        fills = _fills_by_id(svg)
        self.assertNotEqual(fills.get("hand-left"), fills.get("hand-right"))


class TestRenderHelpers(unittest.TestCase):
    def test_canonical_and_side(self):
        self.assertEqual(_canonical_and_side("hand-left"), ("hand", "left"))
        self.assertEqual(_canonical_and_side("hand-right"), ("hand", "right"))
        self.assertEqual(_canonical_and_side("head"), ("head", None))

    def test_color_for_side(self):
        colors = {"hand_left": (255, 0, 0), "hand": (0, 0, 255)}
        self.assertEqual(_color_for("hand", "left", colors), (255, 0, 0))
        # lado sem chave cai no canônico
        self.assertEqual(_color_for("hand", "right", colors), (0, 0, 255))
        # sem nenhuma chave -> None
        self.assertIsNone(_color_for("foot", "left", colors))


class TestRenderFromModel(unittest.TestCase):
    def test_side_lookup_without_base_svg(self):
        model = _model()
        heat = Heatmap(
            colors={"hand_left": (255, 0, 0), "hand": (0, 0, 255)},
            scale_name="LinearScale",
            value_min=0.0,
            value_max=1.0,
            lang="pt",
        )
        svg = str(SvgRenderer().render(heat, model))
        fills = _fills_by_id(svg)
        self.assertEqual(fills["hand-left"], "#ff0000")   # chave lateral
        self.assertEqual(fills["hand-right"], "#0000ff")  # fallback canônico


if __name__ == "__main__":
    unittest.main()
