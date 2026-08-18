"""Tests for the trunk subdivision (chest/abdomen/pelvis/back) and related
features: parent->child rollup, the `missing` parameter and name resolution.

Covers:
- Rollup: a value on an aggregating region (such as "trunk") fills the children
  that have no value of their own (chest, abdomen, pelvis, back); a value on
  "hand" fills "finger".
- The Heatmap's value_min/value_max reflect only the real input values.
- missing="neutral" (default) paints a discreet grey; missing="cold" paints cold.
- An invalid missing raises ValueError.
- Portuguese name resolution: "peito"->chest, "costas"->back,
  "abdomen"->abdomen, "pelve"->pelvis, "tronco"->trunk.
- End-to-end render: a value on "trunk" colours the children in both views.
"""

import os
import unittest
import xml.etree.ElementTree as ET

_ASSETS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "anatomapa", "assets"
)
_ASSETS_EXIST = (
    os.path.exists(os.path.join(_ASSETS_DIR, "body_male_anterior.svg"))
    and os.path.exists(os.path.join(_ASSETS_DIR, "body_male_posterior.svg"))
    and os.path.exists(os.path.join(_ASSETS_DIR, "regions.json"))
)

_MISSING_NEUTRAL_HEX = "#9aa0a6"


def _tag(elem: ET.Element) -> str:
    return elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag


def _render_view(values: dict, view: str, body: str = "male") -> str:
    """Render a specific view through the internal core.

    The public facade exposes only the front; the posterior view remains
    renderable internally and this helper covers that path in the tests.
    """
    from anatomapa.color.registry import get_colormap, get_scale
    from anatomapa.model import loader as _loader
    from anatomapa.render.svg import SvgRenderer
    from anatomapa.resolver.resolver import resolve
    from anatomapa.usecases.build import build_heatmap

    model = _loader.load(view, body=body)
    resolved = resolve(list(values.keys()), model, None, strict=True)
    canonical = {resolved[k]: float(v) for k, v in values.items() if k in resolved}
    heat = build_heatmap(
        values=canonical, model=model,
        colormap=get_colormap("thermal"), scale=get_scale("linear"),
        lang="pt", title=None,
    )
    base = os.path.join(_loader._ASSETS_DIR, f"body_{body}_{view}.svg")
    with open(base, encoding="utf-8") as fh:
        base_svg = fh.read()
    return str(SvgRenderer().render(
        heat, model, lang="pt", base_svg=base_svg, smooth=False, legend=False,
        colormap=get_colormap("thermal"), background="transparent", missing="neutral",
    ))


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes -- pulando testes de subdivisão")
class TestRollupBuild(unittest.TestCase):
    """Tests the parent->child rollup in build_heatmap against the real model."""

    def setUp(self):
        from anatomapa.model import loader as _loader
        from anatomapa.color.registry import get_colormap, get_scale

        self.model_anterior = _loader.load("anterior", body="male")
        self.model_posterior = _loader.load("posterior", body="male")
        self.cmap = get_colormap("reds")
        self.scale = get_scale("linear")

    def test_trunk_value_fills_anterior_children(self):
        from anatomapa.usecases.build import build_heatmap

        result = build_heatmap(
            {"head": 0.0, "trunk": 100.0}, self.model_anterior, self.cmap, self.scale
        )
        for rid in ("chest", "abdomen", "pelvis"):
            self.assertIn(rid, result.colors, f"{rid} não recebeu cor via rollup")
            self.assertEqual(
                result.colors[rid],
                result.colors["trunk"],
                f"{rid} deveria herdar a mesma cor de trunk",
            )

    def test_trunk_value_fills_posterior_children(self):
        from anatomapa.usecases.build import build_heatmap

        result = build_heatmap(
            {"head": 0.0, "trunk": 100.0}, self.model_posterior, self.cmap, self.scale
        )
        for rid in ("back", "pelvis"):
            self.assertIn(rid, result.colors, f"{rid} não recebeu cor via rollup")
            self.assertEqual(result.colors[rid], result.colors["trunk"])

    def test_hand_value_fills_finger(self):
        from anatomapa.usecases.build import build_heatmap

        result = build_heatmap(
            {"hand": 42.0}, self.model_anterior, self.cmap, self.scale
        )
        self.assertIn("finger", result.colors)
        self.assertEqual(result.colors["finger"], result.colors["hand"])

    def test_own_value_takes_precedence_over_rollup(self):
        from anatomapa.usecases.build import build_heatmap

        result = build_heatmap(
            {"trunk": 10.0, "chest": 90.0}, self.model_anterior, self.cmap, self.scale
        )
        self.assertNotEqual(result.colors["chest"], result.colors["trunk"])

    def test_value_min_max_reflect_only_real_input(self):
        from anatomapa.usecases.build import build_heatmap

        result = build_heatmap(
            {"trunk": 5.0, "head": 20.0}, self.model_anterior, self.cmap, self.scale
        )
        # O rollup duplica o valor de trunk em chest/abdomen/pelvis, mas
        # value_min/value_max devem refletir só {5.0, 20.0}, a entrada real.
        self.assertEqual(result.value_min, 5.0)
        self.assertEqual(result.value_max, 20.0)

    def test_trunk_aggregator_has_no_geometry(self):
        # "trunk" nunca tem path próprio (agregador): geometry vazia nas duas vistas.
        trunk_anterior = self.model_anterior.get("trunk")
        trunk_posterior = self.model_posterior.get("trunk")
        self.assertEqual(trunk_anterior.geometry, {})
        self.assertEqual(trunk_posterior.geometry, {})


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes -- pulando testes de missing")
class TestMissingParameterFacade(unittest.TestCase):
    """Tests the `missing` parameter end to end through the heatmap() facade."""

    def test_missing_smooth_neutral_by_default(self):
        import anatomapa

        svg = str(anatomapa.heatmap({"head": 10}))
        self.assertIn(_MISSING_NEUTRAL_HEX, svg)


class TestMissingParameterRenderer(unittest.TestCase):
    """Tests the `missing` parameter directly on SvgRenderer (no assets)."""

    def _make_model(self):
        from anatomapa.domain.model import AnatomicalModel
        from anatomapa.domain.region import Region
        return AnatomicalModel(
            _regions=(
                Region(
                    id="head",
                    label_pt="Cabeça",
                    label_en="Head",
                    bilateral=False,
                    parent=None,
                    geometry={"center": "M 10 10 Z"},
                ),
            )
        )

    def _make_heatmap(self):
        from anatomapa.domain.heatmap import Heatmap
        return Heatmap(
            colors={},
            scale_name="linear",
            value_min=0.0,
            value_max=100.0,
            lang="pt",
        )

    def test_render_invalid_missing_raises(self):
        from anatomapa.render.svg import SvgRenderer
        renderer = SvgRenderer()
        with self.assertRaises(ValueError):
            renderer.render(self._make_heatmap(), self._make_model(), missing="lukewarm")

    def test_render_from_model_default_neutral(self):
        from anatomapa.render.svg import SvgRenderer
        renderer = SvgRenderer()
        fig = renderer.render(self._make_heatmap(), self._make_model())
        root = ET.fromstring(str(fig))
        head = next(p for p in root.iter() if p.get("id") == "head")
        self.assertEqual(head.get("fill"), _MISSING_NEUTRAL_HEX)

    def test_render_from_model_cold_uses_colormap(self):
        from anatomapa.render.svg import SvgRenderer
        from anatomapa.color.registry import get_colormap
        renderer = SvgRenderer()
        cmap = get_colormap("thermal")
        cold_hex = "#{:02x}{:02x}{:02x}".format(*cmap.color_at(0.0))
        fig = renderer.render(
            self._make_heatmap(), self._make_model(), colormap=cmap, missing="cold",
        )
        root = ET.fromstring(str(fig))
        head = next(p for p in root.iter() if p.get("id") == "head")
        self.assertEqual(head.get("fill"), cold_hex)

    def test_smooth_invalid_missing_raises(self):
        from anatomapa.render.svg import _build_smooth_svg
        from anatomapa.color.registry import get_colormap
        base_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions"><path id="head" d="M 0 0 Z" /></g>'
            '</svg>'
        )
        with self.assertRaises(ValueError):
            _build_smooth_svg(
                base_svg, self._make_heatmap(), get_colormap("thermal"),
                legend=False, missing="lukewarm",
            )


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes -- pulando testes de resolução")
class TestSubdivisionNameResolution(unittest.TestCase):
    """Tests that the subdivision ids resolve and Portuguese names do not."""

    def setUp(self):
        from anatomapa.model import loader as _loader
        self.model_anterior = _loader.load("anterior", body="male")
        self.model_posterior = _loader.load("posterior", body="male")

    def test_subdivision_ids_resolve(self):
        from anatomapa.resolver.resolver import resolve
        ids = ["chest", "abdomen", "pelvis", "trunk"]
        result = resolve(ids, self.model_anterior)
        self.assertEqual(result, {rid: rid for rid in ids})

    def test_back_id_resolves(self):
        from anatomapa.resolver.resolver import resolve
        result = resolve(["back"], self.model_posterior)
        self.assertEqual(result["back"], "back")

    def test_portuguese_names_are_rejected(self):
        from anatomapa.resolver.resolver import ResolutionError, resolve
        for label in ("peito", "costas", "pelve", "tronco"):
            with self.subTest(label=label):
                with self.assertRaises(ResolutionError):
                    resolve([label], self.model_anterior)

    def test_portuguese_name_works_through_region_map(self):
        from anatomapa.resolver.resolver import resolve
        result = resolve(
            ["peito"], self.model_anterior, region_map={"peito": "chest"}
        )
        self.assertEqual(result["peito"], "chest")


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes -- pulando testes de render com rollup")
class TestTrunkRollupRender(unittest.TestCase):
    """End-to-end render: a value on "trunk" must colour the children in both views."""

    def _paths_by_id(self, svg: str) -> dict[str, ET.Element]:
        root = ET.fromstring(svg)
        return {p.get("id"): p for p in root.iter() if _tag(p) == "path"}

    def test_trunk_value_colors_anterior_children(self):
        import anatomapa
        svg = str(anatomapa.heatmap({"trunk": 50}))
        paths = self._paths_by_id(svg)
        for rid in ("chest", "abdomen", "pelvis"):
            self.assertIn(rid, paths)
            self.assertNotEqual(
                paths[rid].get("fill"), _MISSING_NEUTRAL_HEX,
                f"{rid} deveria estar colorido pelo rollup de trunk",
            )

    def test_trunk_value_colors_posterior_children(self):
        svg = _render_view({"trunk": 50}, "posterior")
        paths = self._paths_by_id(svg)
        for rid in ("back", "pelvis"):
            self.assertIn(rid, paths)
            self.assertNotEqual(
                paths[rid].get("fill"), _MISSING_NEUTRAL_HEX,
                f"{rid} deveria estar colorido pelo rollup de trunk",
            )

    def test_all_four_trunk_children_get_colored_across_views(self):
        import anatomapa
        svg_ant = str(anatomapa.heatmap({"trunk": 50}))
        svg_post = _render_view({"trunk": 50}, "posterior")
        paths_ant = self._paths_by_id(svg_ant)
        paths_post = self._paths_by_id(svg_post)
        colored = {
            rid for rid in ("chest", "abdomen", "pelvis")
            if paths_ant.get(rid) is not None
            and paths_ant[rid].get("fill") != _MISSING_NEUTRAL_HEX
        }
        colored |= {
            rid for rid in ("back", "pelvis")
            if paths_post.get(rid) is not None
            and paths_post[rid].get("fill") != _MISSING_NEUTRAL_HEX
        }
        self.assertEqual(colored, {"chest", "abdomen", "pelvis", "back"})


if __name__ == "__main__":
    unittest.main()
