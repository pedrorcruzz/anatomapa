"""Tests for SvgRenderer covering both render modes and edge cases."""

import os
import tempfile
import unittest
import xml.etree.ElementTree as ET

from anatomapa.domain.colormap import ColorMap
from anatomapa.domain.heatmap import Heatmap
from anatomapa.domain.model import AnatomicalModel
from anatomapa.domain.region import Region
from anatomapa.render.base import Figure
from anatomapa.render.svg import SvgRenderer

_ASSETS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "anatomapa", "assets"
)
_ASSETS_EXIST = (
    os.path.exists(os.path.join(_ASSETS_DIR, "body_male_anterior.svg"))
    and os.path.exists(os.path.join(_ASSETS_DIR, "regions.json"))
)

_PLACEHOLDER = "#e0e0e0"


def _make_model_central() -> AnatomicalModel:
    return AnatomicalModel(
        _regions=(
            Region(
                id="head",
                label_pt="Cabeca",
                label_en="Head",
                aliases=(),
                bilateral=False,
                parent=None,
                geometry={"center": "M 10 10 Z"},
            ),
        )
    )


def _make_model_bilateral() -> AnatomicalModel:
    return AnatomicalModel(
        _regions=(
            Region(
                id="arm",
                label_pt="Braco",
                label_en="Arm",
                aliases=(),
                bilateral=True,
                parent=None,
                geometry={"left": "M 0 0 Z", "right": "M 100 0 Z"},
            ),
        )
    )


def _make_model_mixed() -> AnatomicalModel:
    return AnatomicalModel(
        _regions=(
            Region(
                id="head",
                label_pt="Cabeca",
                label_en="Head",
                aliases=(),
                bilateral=False,
                parent=None,
                geometry={"center": "M 10 10 Z"},
            ),
            Region(
                id="arm",
                label_pt="Braco",
                label_en="Arm",
                aliases=(),
                bilateral=True,
                parent=None,
                geometry={"left": "M 0 0 Z", "right": "M 100 0 Z"},
            ),
            Region(
                id="trunk",
                label_pt="Tronco",
                label_en="Trunk",
                aliases=(),
                bilateral=False,
                parent=None,
                geometry={"center": "M 20 20 Z"},
            ),
        )
    )


def _make_model_no_geometry() -> AnatomicalModel:
    return AnatomicalModel(
        _regions=(
            Region(
                id="ghost",
                label_pt="Fantasma",
                label_en="Ghost",
                aliases=(),
                bilateral=False,
                parent=None,
                geometry={},
            ),
        )
    )


def _make_heatmap(colors: dict, title: str | None = None) -> Heatmap:
    return Heatmap(
        colors=colors,
        scale_name="linear",
        value_min=0.0,
        value_max=100.0,
        lang="pt",
        title=title,
    )


def _minimal_base_svg(region_id: str, path_d: str = "M 0 0 Z") -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
        '<g id="regions">'
        f'<path id="{region_id}" d="{path_d}" />'
        "</g>"
        "</svg>"
    )


def _tag(elem: ET.Element) -> str:
    tag = elem.tag
    return tag.split("}")[-1] if "}" in tag else tag


class TestSvgRendererFromModel(unittest.TestCase):
    """Testa _render_from_model (base_svg=None)."""

    def setUp(self):
        self.renderer = SvgRenderer()

    def test_returns_figure(self):
        model = _make_model_central()
        hm = _make_heatmap({"head": (255, 0, 0)})
        result = self.renderer.render(hm, model)
        self.assertIsInstance(result, Figure)

    def test_svg_tag_present(self):
        model = _make_model_central()
        hm = _make_heatmap({"head": (255, 0, 0)})
        svg = str(self.renderer.render(hm, model))
        self.assertIn("<svg", svg)

    def test_viewbox_set(self):
        model = _make_model_central()
        hm = _make_heatmap({"head": (255, 0, 0)})
        svg = str(self.renderer.render(hm, model))
        root = ET.fromstring(svg)
        self.assertIn("viewBox", root.attrib)

    def test_central_region_renders_as_single_path(self):
        model = _make_model_central()
        hm = _make_heatmap({"head": (255, 0, 0)})
        svg = str(self.renderer.render(hm, model))
        root = ET.fromstring(svg)
        paths = [e for e in root.iter() if _tag(e) == "path"]
        ids = {p.get("id") for p in paths}
        self.assertIn("head", ids)
        self.assertNotIn("head-left", ids)

    def test_bilateral_region_renders_two_paths(self):
        model = _make_model_bilateral()
        hm = _make_heatmap({"arm": (100, 200, 50)})
        svg = str(self.renderer.render(hm, model))
        root = ET.fromstring(svg)
        paths = [e for e in root.iter() if _tag(e) == "path"]
        ids = {p.get("id") for p in paths}
        self.assertIn("arm-left", ids)
        self.assertIn("arm-right", ids)

    def test_region_with_color_gets_correct_fill(self):
        model = _make_model_central()
        hm = _make_heatmap({"head": (255, 0, 0)})
        svg = str(self.renderer.render(hm, model))
        root = ET.fromstring(svg)
        paths = {e.get("id"): e for e in root.iter() if _tag(e) == "path"}
        self.assertEqual(paths["head"].get("fill"), "#ff0000")

    def test_region_without_value_gets_placeholder(self):
        model = _make_model_central()
        hm = _make_heatmap({})
        svg = str(self.renderer.render(hm, model))
        root = ET.fromstring(svg)
        paths = {e.get("id"): e for e in root.iter() if _tag(e) == "path"}
        self.assertEqual(paths["head"].get("fill"), _PLACEHOLDER)

    def test_title_included_when_present(self):
        model = _make_model_central()
        hm = _make_heatmap({"head": (0, 0, 0)}, title="Meu Mapa")
        svg = str(self.renderer.render(hm, model))
        self.assertIn("Meu Mapa", svg)
        root = ET.fromstring(svg)
        titles = [e for e in root.iter() if _tag(e) == "title"]
        self.assertEqual(len(titles), 1)
        self.assertEqual(titles[0].text, "Meu Mapa")

    def test_no_title_element_when_absent(self):
        model = _make_model_central()
        hm = _make_heatmap({"head": (0, 0, 0)}, title=None)
        svg = str(self.renderer.render(hm, model))
        root = ET.fromstring(svg)
        titles = [e for e in root.iter() if _tag(e) == "title"]
        self.assertEqual(len(titles), 0)

    def test_region_without_geometry_skipped(self):
        model = _make_model_no_geometry()
        hm = _make_heatmap({})
        svg = str(self.renderer.render(hm, model))
        root = ET.fromstring(svg)
        paths = [e for e in root.iter() if _tag(e) == "path"]
        self.assertEqual(len(paths), 0)

    def test_bilateral_region_missing_one_side_skipped(self):
        model = AnatomicalModel(
            _regions=(
                Region(
                    id="arm",
                    label_pt="Braco",
                    label_en="Arm",
                    aliases=(),
                    bilateral=True,
                    parent=None,
                    # Apenas left, sem right presente
                    geometry={"left": "M 0 0 Z"},
                ),
            )
        )
        hm = _make_heatmap({"arm": (100, 100, 100)})
        svg = str(self.renderer.render(hm, model))
        root = ET.fromstring(svg)
        paths = {e.get("id") for e in root.iter() if _tag(e) == "path"}
        self.assertIn("arm-left", paths)
        self.assertNotIn("arm-right", paths)

    def test_lang_pt_renders_without_error(self):
        model = _make_model_central()
        hm = _make_heatmap({"head": (0, 128, 0)})
        svg = str(self.renderer.render(hm, model, lang="pt"))
        self.assertIn("<svg", svg)

    def test_lang_en_renders_without_error(self):
        model = _make_model_central()
        hm = _make_heatmap({"head": (0, 128, 0)})
        svg = str(self.renderer.render(hm, model, lang="en"))
        self.assertIn("<svg", svg)

    def test_deterministic_output(self):
        model = _make_model_mixed()
        hm = _make_heatmap({"head": (255, 0, 0), "arm": (0, 255, 0)})
        svg1 = str(self.renderer.render(hm, model))
        svg2 = str(self.renderer.render(hm, model))
        self.assertEqual(svg1, svg2)

    def test_regions_group_id_set(self):
        model = _make_model_central()
        hm = _make_heatmap({})
        svg = str(self.renderer.render(hm, model))
        root = ET.fromstring(svg)
        groups = [e for e in root.iter() if _tag(e) == "g"]
        group_ids = {g.get("id") for g in groups}
        self.assertIn("regions", group_ids)


class TestSvgRendererOntoSvg(unittest.TestCase):
    """Testa _render_onto_svg (base_svg fornecido)."""

    def setUp(self):
        self.renderer = SvgRenderer()
        self.model = _make_model_central()

    def test_returns_figure(self):
        base = _minimal_base_svg("head")
        hm = _make_heatmap({"head": (0, 0, 255)})
        result = self.renderer.render(hm, self.model, base_svg=base)
        self.assertIsInstance(result, Figure)

    def test_fill_applied_to_known_region(self):
        base = _minimal_base_svg("head")
        hm = _make_heatmap({"head": (0, 0, 255)})
        svg = str(self.renderer.render(hm, self.model, base_svg=base))
        root = ET.fromstring(svg)
        paths = {e.get("id"): e for e in root.iter() if _tag(e) == "path"}
        self.assertEqual(paths["head"].get("fill"), "#0000ff")

    def test_unknown_region_gets_placeholder(self):
        base = _minimal_base_svg("unknown_region")
        hm = _make_heatmap({"head": (0, 0, 255)})
        svg = str(self.renderer.render(hm, self.model, base_svg=base))
        root = ET.fromstring(svg)
        paths = {e.get("id"): e for e in root.iter() if _tag(e) == "path"}
        self.assertEqual(paths["unknown_region"].get("fill"), _PLACEHOLDER)

    def test_bilateral_suffix_stripped_for_color_lookup(self):
        base = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions">'
            '<path id="arm-left" d="M 0 0 Z" />'
            '<path id="arm-right" d="M 100 0 Z" />'
            "</g>"
            "</svg>"
        )
        hm = _make_heatmap({"arm": (200, 100, 50)})
        svg = str(self.renderer.render(hm, self.model, base_svg=base))
        root = ET.fromstring(svg)
        paths = {e.get("id"): e for e in root.iter() if _tag(e) == "path"}
        self.assertEqual(paths["arm-left"].get("fill"), "#c86432")
        self.assertEqual(paths["arm-right"].get("fill"), "#c86432")

    def test_style_attribute_removed(self):
        base = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions">'
            '<path id="head" d="M 0 0 Z" style="fill:red" />'
            "</g>"
            "</svg>"
        )
        hm = _make_heatmap({"head": (0, 255, 0)})
        svg = str(self.renderer.render(hm, self.model, base_svg=base))
        root = ET.fromstring(svg)
        paths = {e.get("id"): e for e in root.iter() if _tag(e) == "path"}
        self.assertNotIn("style", paths["head"].attrib)

    def test_path_without_id_skipped(self):
        base = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions">'
            '<path d="M 0 0 Z" />'
            "</g>"
            "</svg>"
        )
        hm = _make_heatmap({})
        svg = str(self.renderer.render(hm, self.model, base_svg=base))
        self.assertIn("<svg", svg)

    def test_non_path_elements_skipped(self):
        base = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions">'
            '<rect id="box" width="10" height="10" />'
            "</g>"
            "</svg>"
        )
        hm = _make_heatmap({})
        svg = str(self.renderer.render(hm, self.model, base_svg=base))
        self.assertIn("<svg", svg)

    def test_no_regions_group_returns_original_svg(self):
        base = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="other"><path id="head" d="M 0 0 Z" /></g>'
            "</svg>"
        )
        hm = _make_heatmap({"head": (0, 0, 0)})
        svg = str(self.renderer.render(hm, self.model, base_svg=base))
        # Sem grupo regions, retorna SVG original sem fill aplicado
        self.assertIn("<svg", svg)

    def test_well_formed_xml_output(self):
        base = _minimal_base_svg("head")
        hm = _make_heatmap({"head": (10, 20, 30)})
        svg = str(self.renderer.render(hm, self.model, base_svg=base))
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            self.fail(f"Output is not well-formed XML: {e}")


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes -- skip testes com assets reais")
class TestSvgRendererWithRealAssets(unittest.TestCase):
    """Testa o renderer com o SVG base real do projeto."""

    def setUp(self):
        self.renderer = SvgRenderer()
        from anatomapa.model.loader import load
        self.model = load("anterior", body="male")
        anterior_path = os.path.join(_ASSETS_DIR, "body_male_anterior.svg")
        with open(anterior_path, encoding="utf-8") as fh:
            self.base_svg = fh.read()

    def test_render_onto_real_svg_returns_figure(self):
        hm = _make_heatmap({"head": (255, 50, 50)})
        result = self.renderer.render(hm, self.model, base_svg=self.base_svg)
        self.assertIsInstance(result, Figure)

    def test_render_onto_real_svg_is_valid_xml(self):
        hm = _make_heatmap({"head": (255, 50, 50)})
        svg = str(self.renderer.render(hm, self.model, base_svg=self.base_svg))
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            self.fail(f"SVG com assets reais inválido: {e}")

    def test_render_from_model_with_real_model(self):
        hm = _make_heatmap({"head": (200, 100, 0)})
        svg = str(self.renderer.render(hm, self.model))
        self.assertIn("<svg", svg)

    def test_lang_en_with_real_model(self):
        hm = Heatmap(
            colors={"head": (200, 100, 0)},
            scale_name="linear",
            value_min=0.0,
            value_max=100.0,
            lang="en",
        )
        svg = str(self.renderer.render(hm, self.model, lang="en"))
        self.assertIn("<svg", svg)


class TestBuildSmoothSvgUnit(unittest.TestCase):
    """Testa _build_smooth_svg diretamente (sem assets externos)."""

    def _make_colormap(self) -> "ColorMap":
        from anatomapa.color.registry import get_colormap
        return get_colormap("thermal")

    def _make_hm(self, colors: dict) -> "Heatmap":
        return Heatmap(
            colors=colors,
            scale_name="linear",
            value_min=0.0,
            value_max=100.0,
            lang="pt",
            title=None,
        )

    def _svg_with_outline(self, region_id: str = "head", fill: str = "#ff0000") -> str:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<path id="body-outline" d="M 0 0 L 400 0 L 400 900 L 0 900 Z" />'
            '<g id="regions">'
            f'<path id="{region_id}" d="M 10 10 Z" />'
            "</g>"
            "</svg>"
        )

    def _svg_without_outline(self) -> str:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions">'
            '<path id="head" d="M 10 10 Z" />'
            "</g>"
            "</svg>"
        )

    def test_smooth_with_outline_is_valid_xml(self):
        from anatomapa.render.svg import _build_smooth_svg
        cmap = self._make_colormap()
        hm = self._make_hm({"head": (255, 0, 0)})
        svg = _build_smooth_svg(self._svg_with_outline(), hm, cmap, legend=False)
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            self.fail(f"SVG inválido: {e}")

    def test_smooth_without_outline_uses_rect_fallback(self):
        # Sem body-outline, a camada interna deve ser um rect (fallback)
        from anatomapa.render.svg import _build_smooth_svg
        cmap = self._make_colormap()
        hm = self._make_hm({"head": (255, 0, 0)})
        svg = _build_smooth_svg(self._svg_without_outline(), hm, cmap, legend=False)
        root = ET.fromstring(svg)
        rects = [e for e in root.iter() if _tag(e) == "rect"]
        self.assertGreater(len(rects), 0, "Fallback rect ausente quando sem body-outline")

    def test_smooth_without_outline_valid_xml(self):
        from anatomapa.render.svg import _build_smooth_svg
        cmap = self._make_colormap()
        hm = self._make_hm({})
        svg = _build_smooth_svg(self._svg_without_outline(), hm, cmap, legend=False)
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            self.fail(f"SVG sem outline inválido: {e}")

    def test_smooth_with_outline_no_curtain_no_evenodd(self):
        # Sem curtain (evenodd): body-outline como curtain criaria linhas escuras
        # nos sub-paths musculares. As linhas musculares agora são deliberadas
        # (grupo muscle-lines), não efeito colateral de curtain.
        from anatomapa.render.svg import _build_smooth_svg
        cmap = self._make_colormap()
        hm = self._make_hm({"head": (200, 100, 50)})
        svg = _build_smooth_svg(self._svg_with_outline(), hm, cmap, legend=False)
        self.assertNotIn("evenodd", svg)
        root = ET.fromstring(svg)
        # Linhas musculares devem estar no grupo muscle-lines, não espalhadas
        muscle_groups = [e for e in root.iter() if _tag(e) == "g" and e.get("id") == "muscle-lines"]
        self.assertGreater(len(muscle_groups), 0, "Grupo muscle-lines ausente")

    def test_smooth_muscle_lines_in_output(self):
        # Linhas musculares (fill=none, stroke escuro) devem estar presentes no
        # grupo muscle-lines para definição anatômica por cima do degradê.
        from anatomapa.render.svg import _build_smooth_svg
        cmap = self._make_colormap()
        hm = self._make_hm({})
        svg = _build_smooth_svg(self._svg_with_outline(), hm, cmap, legend=False)
        root = ET.fromstring(svg)
        muscle_groups = [e for e in root.iter() if _tag(e) == "g" and e.get("id") == "muscle-lines"]
        self.assertGreater(len(muscle_groups), 0, "Grupo muscle-lines ausente")
        lines = [p for g in muscle_groups for p in g if _tag(p) == "path"]
        self.assertGreater(len(lines), 0, "Nenhuma linha muscular encontrada")
        for line in lines:
            self.assertEqual(line.get("fill"), "none")
            self.assertIsNotNone(line.get("stroke"))

    def test_smooth_bilateral_suffix_stripped(self):
        from anatomapa.render.svg import _build_smooth_svg
        cmap = self._make_colormap()
        hm = self._make_hm({"arm": (200, 100, 50)})
        base = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<path id="body-outline" d="M 0 0 Z" />'
            '<g id="regions">'
            '<path id="arm-left" d="M 0 0 Z" />'
            '<path id="arm-right" d="M 100 0 Z" />'
            "</g>"
            "</svg>"
        )
        svg = _build_smooth_svg(base, hm, cmap, legend=False)
        root = ET.fromstring(svg)
        paths = {e.get("id"): e for e in root.iter() if _tag(e) == "path"}
        arm_color = "#{:02x}{:02x}{:02x}".format(200, 100, 50)
        self.assertEqual(paths["arm-left"].get("fill"), arm_color)
        self.assertEqual(paths["arm-right"].get("fill"), arm_color)

    def test_smooth_with_title(self):
        from anatomapa.render.svg import _build_smooth_svg
        cmap = self._make_colormap()
        hm = Heatmap(
            colors={},
            scale_name="linear",
            value_min=0.0,
            value_max=10.0,
            lang="pt",
            title="Mapa Teste",
        )
        svg = _build_smooth_svg(self._svg_with_outline(), hm, cmap, legend=False)
        self.assertIn("Mapa Teste", svg)

    def test_smooth_with_legend(self):
        from anatomapa.render.svg import _build_smooth_svg
        cmap = self._make_colormap()
        hm = self._make_hm({"head": (255, 0, 0)})
        svg = _build_smooth_svg(self._svg_with_outline(), hm, cmap, legend=True)
        self.assertIn("linearGradient", svg)


class TestFigureSave(unittest.TestCase):
    """Testa Figure.save() (render/base.py linhas 42-43)."""

    def test_save_writes_file(self):
        from anatomapa.render.base import Figure
        fig = Figure("<svg>test</svg>")
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            path = tmp.name
        try:
            fig.save(path)
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            self.assertEqual(content, "<svg>test</svg>")
        finally:
            os.unlink(path)

    def test_save_creates_valid_content(self):
        from anatomapa.render.base import Figure
        model = _make_model_central()
        hm = _make_heatmap({"head": (255, 0, 0)})
        fig = SvgRenderer().render(hm, model)
        with tempfile.NamedTemporaryFile(
            suffix=".svg", delete=False, mode="w"
        ) as tmp:
            path = tmp.name
        try:
            fig.save(path)
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            ET.fromstring(content)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
