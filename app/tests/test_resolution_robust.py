"""Tests for strict resolution end to end: lateralised ids, region_map,
batched errors, on_unknown, validate and per-side rendering."""
import os
import unittest
import warnings
import xml.etree.ElementTree as ET

import anatomapa as am
from anatomapa.domain.heatmap import Heatmap
from anatomapa.domain.model import AnatomicalModel
from anatomapa.domain.region import Region
from anatomapa.render.svg import SvgRenderer, _canonical_and_side, _color_for
from anatomapa.resolver.resolver import ResolutionError, analyze, resolve

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "anatomapa", "assets")
_ASSETS_EXIST = os.path.exists(
    os.path.join(_ASSETS_DIR, "body_male_anterior.svg")
) and os.path.exists(os.path.join(_ASSETS_DIR, "regions.json"))


def _model() -> AnatomicalModel:
    return AnatomicalModel(
        _regions=(
            Region("head", "Cabeça", "Head", False, None, {"center": "M0 0Z"}),
            Region("hand", "Mão", "Hand", True, None, {"left": "M0 0Z", "right": "M1 1Z"}),
            Region("foot", "Pé", "Foot", True, None, {"left": "M0 0Z", "right": "M1 1Z"}),
            Region("trunk", "Tronco", "Trunk", False, None, {"center": "M0 0Z"}),
        )
    )


def _fills_by_id(svg: str) -> dict[str, str]:
    root = ET.fromstring(svg)
    return {e.get("id"): e.get("fill") for e in root.iter() if e.get("id")}


class TestLateralResolve(unittest.TestCase):
    def setUp(self):
        self.model = _model()

    def test_bare_id_is_bilateral(self):
        self.assertEqual(resolve(["hand"], self.model)["hand"], "hand")

    def test_lateralised_ids(self):
        result = resolve(["hand_right", "foot_left"], self.model)
        self.assertEqual(result["hand_right"], "hand_right")
        self.assertEqual(result["foot_left"], "foot_left")

    def test_side_words_are_not_interpreted(self):
        for label in ("mão direita", "right hand", "hand left", "pe dir"):
            with self.subTest(label=label):
                with self.assertRaises(ResolutionError):
                    resolve([label], self.model)

    def test_reversed_side_order_is_not_interpreted(self):
        with self.assertRaises(ResolutionError):
            resolve(["right_hand"], self.model)

    def test_central_with_side_is_error(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["head_left"], self.model)
        self.assertIn("central", str(ctx.exception))

    def test_central_with_side_in_analyze(self):
        report = analyze(["head_right"], self.model)
        self.assertIn("head_right", report["unresolved"])
        self.assertIn("central", report["unresolved"]["head_right"]["reason"])


class TestRegionMap(unittest.TestCase):
    def setUp(self):
        self.model = _model()

    def test_exact_key(self):
        r = resolve(["MinhaVar"], self.model, region_map={"MinhaVar": "hand"})
        self.assertEqual(r["MinhaVar"], "hand")

    def test_key_is_not_normalised(self):
        with self.assertRaises(ResolutionError):
            resolve(["braço x"], self.model, region_map={"braco_x": "hand"})

    def test_to_lateral_id(self):
        r = resolve(["MSD"], self.model, region_map={"MSD": "hand_right"})
        self.assertEqual(r["MSD"], "hand_right")

    def test_precedence_over_canonical(self):
        r = resolve(["hand"], self.model, region_map={"hand": "foot"})
        self.assertEqual(r["hand"], "foot")

    def test_spreadsheet_labels(self):
        dados = {"MÃO": 1, "PÉ": 2, "CABEÇA": 3}
        mapa = {"MÃO": "hand", "PÉ": "foot", "CABEÇA": "head"}
        r = resolve(list(dados), self.model, region_map=mapa)
        self.assertEqual(r, {"MÃO": "hand", "PÉ": "foot", "CABEÇA": "head"})


class TestBatchErrors(unittest.TestCase):
    def setUp(self):
        self.model = _model()

    def test_all_unresolved_listed(self):
        with self.assertRaises(ResolutionError) as ctx:
            resolve(["pedro", "xpto", "hand"], self.model)
        msg = str(ctx.exception)
        self.assertIn("pedro", msg)
        self.assertIn("xpto", msg)
        self.assertIn("2", msg)

    def test_non_strict_returns_partial(self):
        r = resolve(["hand", "pedro"], self.model, strict=False)
        self.assertEqual(r, {"hand": "hand"})

    def test_analyze_reports_suggestions(self):
        report = analyze(["heaad"], self.model)
        self.assertIn("heaad", report["unresolved"])
        self.assertTrue(report["unresolved"]["heaad"]["suggestions"])


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestFacadeOnUnknown(unittest.TestCase):
    def test_default_error(self):
        with self.assertRaises(ResolutionError):
            am.heatmap({"hand": 1, "pedro": 2})

    def test_skip(self):
        fig = am.heatmap({"hand": 10, "pedro": 5}, on_unknown="skip")
        self.assertIn("<svg", str(fig))

    def test_warn(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            am.heatmap({"hand": 10, "pedro": 5}, on_unknown="warn")
        self.assertTrue(any("pedro" in str(x.message) for x in w))

    def test_invalid_on_unknown(self):
        with self.assertRaises(ValueError):
            am.heatmap({"hand": 1}, on_unknown="explode")


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestFacadeExtras(unittest.TestCase):
    def test_accepts_pairs(self):
        pares = am.from_dict({"hand": 10, "foot": 20})
        fig = am.heatmap(pares)
        self.assertIn("<svg", str(fig))

    def test_accepts_records_output(self):
        recs = [{"r": "hand", "v": 5}, {"r": "foot", "v": 9}]
        data = am.from_records(recs, region_col="r", value_col="v")
        fig = am.heatmap(data)
        self.assertIn("<svg", str(fig))

    def test_validate_dry_run(self):
        report = am.validate({"hand": 1, "pedro": 2, "hand_right": 3})
        self.assertEqual(report["resolved"]["hand"], "hand")
        self.assertEqual(report["resolved"]["hand_right"], "hand_right")
        self.assertIn("pedro", report["unresolved"])

    def test_validate_with_region_map(self):
        report = am.validate(
            {"MÃO": 1, "DEDO DA MÃO": 2},
            region_map={"MÃO": "hand", "DEDO DA MÃO": "finger"},
        )
        self.assertEqual(report["resolved"]["MÃO"], "hand")
        self.assertEqual(report["resolved"]["DEDO DA MÃO"], "finger")
        self.assertEqual(report["unresolved"], {})

    def test_portuguese_names_are_rejected_by_facade(self):
        report = am.validate({"maos": 1, "joelho": 1})
        self.assertEqual(report["resolved"], {})
        self.assertIn("maos", report["unresolved"])
        self.assertIn("joelho", report["unresolved"])


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestRenderPerSide(unittest.TestCase):
    def test_sides_get_distinct_colors(self):
        svg = str(am.heatmap({"hand_right": 100, "hand_left": 1, "trunk": 50}))
        fills = _fills_by_id(svg)
        self.assertIn("hand-left", fills)
        self.assertIn("hand-right", fills)
        self.assertNotEqual(fills["hand-left"], fills["hand-right"])

    def test_bilateral_paints_both_equal(self):
        svg = str(am.heatmap({"hand": 100, "trunk": 1}))
        fills = _fills_by_id(svg)
        self.assertEqual(fills["hand-left"], fills["hand-right"])

    def test_smooth_per_side(self):
        svg = str(am.heatmap({"hand_right": 100, "hand_left": 1}))
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
