"""Testes para as novas funcionalidades: thermal, body, smooth e legend.

Cobre:
- Colormap "thermal" (extremos e meio)
- Parâmetro body (male/female) na facade e no loader
- Body inválido gera ValueError
- Modo smooth: SVG contém feGaussianBlur e mask
- Determinismo do modo smooth
- Legend: SVG contém linearGradient e rótulos min/max
- Sincronia viewBox com coordenadas da legenda
"""

import os
import unittest
import xml.etree.ElementTree as ET

_ASSETS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "anatomapa", "assets"
)
_ASSETS_EXIST = (
    os.path.exists(os.path.join(_ASSETS_DIR, "body_male_anterior.svg"))
    and os.path.exists(os.path.join(_ASSETS_DIR, "body_female_anterior.svg"))
    and os.path.exists(os.path.join(_ASSETS_DIR, "regions.json"))
)


def _tag(elem: ET.Element) -> str:
    return elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag


class TestThermalColormap(unittest.TestCase):
    """Testa o colormap 'thermal'."""

    def setUp(self):
        from anatomapa.color.registry import get_colormap
        self.cmap = get_colormap("thermal")

    def test_thermal_at_zero_is_dark_blue(self):
        r, g, b = self.cmap.color_at(0.0)
        # Azul-marinho: G e R devem ser baixos, B moderado
        self.assertLess(r, 30)
        self.assertLess(g, 30)
        self.assertGreater(b, 30)

    def test_thermal_at_one_is_orange(self):
        # Topo da escala agora é laranja (sem branco), fechando o degradê quente
        r, g, b = self.cmap.color_at(1.0)
        self.assertGreater(r, 240)
        self.assertLess(g, 190)
        self.assertLess(b, 80)

    def test_thermal_at_half_is_greenish(self):
        # t=0.5 mapeia para verde (0, 215, 120)
        r, g, b = self.cmap.color_at(0.5)
        self.assertGreater(g, 150)
        self.assertLess(r, 150)

    def test_thermal_at_09_is_reddish(self):
        # t=0.9 mapeia para laranja (255, 175, 0): quente, sem azul
        r, g, b = self.cmap.color_at(0.9)
        self.assertGreater(r, 200)
        self.assertLess(b, 100)

    def test_thermal_registered_by_name(self):
        from anatomapa.color.registry import list_colormaps
        self.assertIn("thermal", list_colormaps())

    def test_thermal_returns_rgb_tuple(self):
        result = self.cmap.color_at(0.3)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        for ch in result:
            self.assertIsInstance(ch, int)
            self.assertGreaterEqual(ch, 0)
            self.assertLessEqual(ch, 255)

    def test_thermal_at_015_is_blue(self):
        # t=0.15 fica no segmento inicial (frio, azul dominante): b alto, r baixo
        r, g, b = self.cmap.color_at(0.15)
        self.assertGreater(b, 200)
        self.assertLess(r, 50)
        self.assertLess(g, 60)

    def test_thermal_at_030_is_cyan(self):
        # t=0.30 fica no segmento azul->ciano: b alto, g já significativo, r baixo
        r, g, b = self.cmap.color_at(0.30)
        self.assertGreater(g, 100)
        self.assertGreater(b, 200)
        self.assertLess(r, 50)


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes -- pulando testes de body")
class TestBodyParameter(unittest.TestCase):
    """Testa o parâmetro body na facade e no loader."""

    def test_male_body_loads_correct_file(self):
        from anatomapa.model.loader import load
        model = load("anterior", body="male")
        self.assertGreater(len(model.ids()), 0)

    def test_female_body_loads_correct_file(self):
        from anatomapa.model.loader import load
        model = load("anterior", body="female")
        self.assertGreater(len(model.ids()), 0)

    def test_male_and_female_both_have_same_regions(self):
        from anatomapa.model.loader import load
        male = load("anterior", body="male")
        female = load("anterior", body="female")
        self.assertEqual(set(male.ids()), set(female.ids()))

    def test_invalid_body_raises_value_error(self):
        from anatomapa.model.loader import load
        with self.assertRaises(ValueError) as ctx:
            load("anterior", body="robot")
        self.assertIn("robot", str(ctx.exception))

    def test_invalid_body_error_mentions_valid_options(self):
        from anatomapa.model.loader import load
        with self.assertRaises(ValueError) as ctx:
            load("anterior", body="alien")
        msg = str(ctx.exception)
        self.assertTrue("male" in msg or "female" in msg)

    def test_invalid_view_raises_value_error(self):
        from anatomapa.model.loader import load
        with self.assertRaises(ValueError) as ctx:
            load("lateral", body="male")
        self.assertIn("lateral", str(ctx.exception))

    def test_facade_male_returns_figure(self):
        import anatomapa
        from anatomapa.render.base import Figure
        fig = anatomapa.heatmap({"head": 10}, body="male")
        self.assertIsInstance(fig, Figure)

    def test_facade_female_returns_figure(self):
        import anatomapa
        from anatomapa.render.base import Figure
        fig = anatomapa.heatmap({"head": 10}, body="female")
        self.assertIsInstance(fig, Figure)

    def test_facade_invalid_body_raises(self):
        import anatomapa
        with self.assertRaises(ValueError):
            anatomapa.heatmap({"head": 10}, body="android")

    def test_facade_male_svg_is_valid_xml(self):
        import anatomapa
        svg = str(anatomapa.heatmap({"head": 10, "trunk": 5}, body="male"))
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            self.fail(f"SVG male inválido: {e}")

    def test_facade_female_svg_is_valid_xml(self):
        import anatomapa
        svg = str(anatomapa.heatmap({"head": 10, "trunk": 5}, body="female"))
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            self.fail(f"SVG female inválido: {e}")

    def test_list_regions_female(self):
        import anatomapa
        regions = anatomapa.list_regions(body="female")
        self.assertGreater(len(regions), 0)

    def test_list_regions_male(self):
        import anatomapa
        regions = anatomapa.list_regions(body="male")
        self.assertGreater(len(regions), 0)

    def test_cache_key_includes_body(self):
        # male e female devem retornar modelos distintos (cache separado)
        from anatomapa.model.loader import load
        male = load("anterior", body="male")
        female = load("anterior", body="female")
        self.assertIsNot(male, female)


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes -- pulando testes de background")
class TestBackgroundFacade(unittest.TestCase):
    """Testa o parâmetro background via a facade heatmap(), fim a fim."""

    def test_dark_background_flat_mode(self):
        import anatomapa
        svg = str(anatomapa.heatmap({"head": 10}, background="dark"))
        root = ET.fromstring(svg)
        bg = next((e for e in root if e.get("id") == "figure-background"), None)
        self.assertIsNotNone(bg)
        self.assertEqual(bg.get("fill"), "#0a0a0a")

    def test_light_background_smooth_mode(self):
        import anatomapa
        svg = str(anatomapa.heatmap(
            {"head": 10, "trunk": 50}, smooth=True, cmap="thermal", background="light",
        ))
        root = ET.fromstring(svg)
        bg = next((e for e in root if e.get("id") == "figure-background"), None)
        self.assertIsNotNone(bg)
        self.assertEqual(bg.get("fill"), "#ffffff")

    def test_transparent_is_default_no_rect(self):
        import anatomapa
        svg = str(anatomapa.heatmap({"head": 10}))
        root = ET.fromstring(svg)
        bg = next((e for e in root if e.get("id") == "figure-background"), None)
        self.assertIsNone(bg)

    def test_invalid_background_raises(self):
        import anatomapa
        with self.assertRaises(ValueError):
            anatomapa.heatmap({"head": 10}, background="chartreuse")

    def test_background_and_legend_combined_valid_xml(self):
        import anatomapa
        svg = str(anatomapa.heatmap(
            {"head": 10, "trunk": 50}, smooth=True, cmap="thermal",
            background="dark", legend=True,
        ))
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            self.fail(f"SVG smooth+background+legend inválido: {e}")


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes -- pulando testes de smooth")
class TestSmoothMode(unittest.TestCase):
    """Testa o modo smooth (degradê contínuo)."""

    def _smooth_svg(self, values=None, body="male", **kwargs):
        import anatomapa
        if values is None:
            values = {"head": 100, "trunk": 50, "arm": 80}
        return str(anatomapa.heatmap(values, body=body, smooth=True, **kwargs))

    def test_smooth_svg_is_valid_xml(self):
        svg = self._smooth_svg()
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            self.fail(f"SVG smooth inválido: {e}")

    def test_smooth_contains_feGaussianBlur(self):
        svg = self._smooth_svg()
        self.assertIn("feGaussianBlur", svg)

    def test_smooth_has_blurred_group(self):
        # O grupo blurred (com filter) deve estar presente sem clipPath nem mask
        svg = self._smooth_svg()
        root = ET.fromstring(svg)
        blurred = [e for e in root.iter() if _tag(e) == "g" and "thermal-blur" in e.get("filter", "")]
        self.assertGreater(len(blurred), 0, "Grupo blurred ausente")
        # O grupo blurred nao deve ter clipPath nem mask (causam seams)
        for g in blurred:
            self.assertNotIn("clip-path", g.attrib, "clipPath no grupo blurred cria seams")
            self.assertNotIn("mask", g.attrib, "mask no grupo blurred cria seams")

    def test_smooth_contains_filter(self):
        svg = self._smooth_svg()
        root = ET.fromstring(svg)
        filters = [e for e in root.iter() if _tag(e) == "filter"]
        self.assertGreater(len(filters), 0)

    def test_smooth_is_deterministic(self):
        values = {"head": 100, "trunk": 50, "arm": 80}
        import anatomapa
        svg1 = str(anatomapa.heatmap(values, smooth=True))
        svg2 = str(anatomapa.heatmap(values, smooth=True))
        self.assertEqual(svg1, svg2)

    def test_smooth_has_sharp_outline_layer(self):
        # A camada NÍTIDA (contorno forte + linhas de detalhe) fica por cima do
        # degradê, fora da máscara/blur, para o modelo nunca distorcer.
        svg = self._smooth_svg()
        root = ET.fromstring(svg)
        outline = next((e for e in root if e.get("id") == "body-outline"), None)
        self.assertIsNotNone(outline, "Contorno nítido body-outline ausente")
        self.assertEqual(outline.get("fill"), "none")
        self.assertEqual(outline.get("fill-rule"), "evenodd")
        detail = next((e for e in root if e.get("id") == "body-outline-detail"), None)
        self.assertIsNotNone(detail, "Linhas de detalhe body-outline-detail ausentes")
        self.assertEqual(detail.get("fill"), "none")

    def test_smooth_female_is_valid_xml(self):
        svg = self._smooth_svg(body="female")
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            self.fail(f"SVG smooth female inválido: {e}")

    def test_smooth_with_thermal_cmap(self):
        svg = self._smooth_svg(cmap="thermal")
        self.assertIn("feGaussianBlur", svg)

    def test_smooth_with_title(self):
        svg = self._smooth_svg(title="Teste Smooth")
        self.assertIn("Teste Smooth", svg)

    def test_smooth_false_does_not_add_blur(self):
        import anatomapa
        svg = str(anatomapa.heatmap({"head": 10}, smooth=False))
        self.assertNotIn("feGaussianBlur", svg)

    def test_smooth_base_cold_present(self):
        # A base fria (união de todos os paths de região, sem id próprio) deve
        # estar presente como camada de fundo do degradê quando missing="cold"
        # (comportamento antigo, sem cor de missing neutra).
        from anatomapa.color.registry import get_colormap
        cmap = get_colormap("thermal")
        cold_hex = "#{:02x}{:02x}{:02x}".format(*cmap.color_at(0.0))
        svg = self._smooth_svg(cmap="thermal", missing="cold")
        root = ET.fromstring(svg)
        bases = [
            e
            for e in root.iter()
            if _tag(e) in ("rect", "path") and e.get("fill") == cold_hex
        ]
        self.assertGreaterEqual(len(bases), 1, "Base fria ausente no grupo blurred")

    def test_smooth_base_neutral_by_default(self):
        # Por padrão (missing="neutral"), a base do degradê usa o cinza
        # discreto de missing, não a cor fria do colormap.
        svg = self._smooth_svg(cmap="thermal")
        root = ET.fromstring(svg)
        bases = [
            e
            for e in root.iter()
            if _tag(e) in ("rect", "path") and e.get("fill") == "#9aa0a6"
        ]
        self.assertGreaterEqual(len(bases), 1, "Base neutra ausente no grupo blurred")

    def test_smooth_regions_without_value_have_no_own_path(self):
        # Regiões sem valor (ex.: trunk, quando só "head" tem dado) não recebem
        # path próprio dentro do grupo blurred: a base fria por baixo já cobre
        # a área, sem deixar buraco no degradê.
        import anatomapa
        # Passa apenas head; trunk e outros nao tem valor
        svg = str(anatomapa.heatmap({"head": 100}, body="male", smooth=True, cmap="thermal"))
        root = ET.fromstring(svg)
        blurred_group = None
        for e in root.iter():
            if _tag(e) == "g" and "thermal-blur" in e.get("filter", ""):
                blurred_group = e
                break
        self.assertIsNotNone(blurred_group, "Grupo blurred nao encontrado")
        trunk_paths = [p for p in blurred_group if p.get("id") == "trunk"]
        self.assertEqual(trunk_paths, [], "trunk sem valor não deveria ter path próprio")

    def test_smooth_regions_with_value_have_matching_stroke(self):
        # Regioes com valor tem stroke=fill para fechar os vãos na silhueta unida.
        # Usa dois valores distintos para que head (100) nao fique em t=0 (cor fria).
        import anatomapa
        from anatomapa.color.registry import get_colormap
        cmap = get_colormap("thermal")
        cold_hex = "#{:02x}{:02x}{:02x}".format(*cmap.color_at(0.0))
        svg = str(anatomapa.heatmap(
            {"head": 100, "trunk": 1}, body="male", smooth=True, cmap="thermal",
        ))
        root = ET.fromstring(svg)
        blurred_group = None
        for e in root.iter():
            if _tag(e) == "g" and "thermal-blur" in e.get("filter", ""):
                blurred_group = e
                break
        self.assertIsNotNone(blurred_group, "Grupo blurred nao encontrado")
        # Paths com id contendo "head" devem ter stroke == fill (fill+stroke identicos)
        head_paths = [
            p for p in blurred_group
            if _tag(p) == "path" and "head" in p.get("id", "")
        ]
        self.assertGreater(len(head_paths), 0, "Nenhum path de head encontrado")
        for p in head_paths:
            self.assertNotEqual(p.get("fill"), cold_hex, "Head deveria ter cor quente")
            self.assertEqual(
                p.get("fill"), p.get("stroke"),
                f"stroke deve igualar fill no path {p.get('id')}",
            )

    def test_smooth_blur_std_is_moderate(self):
        # Dois filtros usam feGaussianBlur: o blur base (thermal-blur, leve,
        # ~1% do vw) e o inner-glow frio (inner-glow-cold, mais largo, ~4% do
        # vw). Ambos devem ficar num intervalo moderado da largura do viewBox.
        svg = self._smooth_svg()
        root = ET.fromstring(svg)
        blurs = [e for e in root.iter() if _tag(e) == "feGaussianBlur"]
        self.assertEqual(len(blurs), 2)
        for blur in blurs:
            std = float(blur.get("stdDeviation", "0"))
            self.assertGreater(std, 1.0, "Desfoque insuficiente")
            self.assertLess(std, 100.0, "Desfoque excessivo")

    def test_smooth_with_legend_is_valid_xml(self):
        import anatomapa
        svg = str(anatomapa.heatmap(
            {"head": 100, "trunk": 50, "arm": 80},
            body="male", smooth=True, legend=True, cmap="thermal",
        ))
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            self.fail(f"SVG smooth+legend inválido: {e}")

    def test_smooth_has_body_mask_in_defs(self):
        # <mask id="body-mask"> deve estar em <defs> para recortar o blur na silhueta.
        svg = self._smooth_svg()
        root = ET.fromstring(svg)
        masks = [e for e in root.iter() if _tag(e) == "mask" and e.get("id") == "body-mask"]
        self.assertGreater(len(masks), 0, "body-mask ausente nos defs")

    def test_smooth_masked_group_wraps_blurred_group(self):
        # O grupo externo (com mask) deve conter o grupo blurred (com filter).
        svg = self._smooth_svg()
        root = ET.fromstring(svg)
        masked_groups = [e for e in root if _tag(e) == "g" and "body-mask" in e.get("mask", "")]
        self.assertGreater(len(masked_groups), 0, "Grupo com mask=body-mask ausente")
        for mg in masked_groups:
            blurred = [c for c in mg if _tag(c) == "g" and "thermal-blur" in c.get("filter", "")]
            self.assertGreater(len(blurred), 0, "Grupo blurred não está dentro do masked_group")

    def test_smooth_blurred_group_has_no_mask(self):
        # O grupo blurred interno NÃO deve ter mask (causaria bordas duras internas).
        # A mask fica apenas no grupo exterior.
        svg = self._smooth_svg()
        root = ET.fromstring(svg)
        blurred = [e for e in root.iter() if _tag(e) == "g" and "thermal-blur" in e.get("filter", "")]
        self.assertGreater(len(blurred), 0, "Grupo blurred ausente")
        for g in blurred:
            self.assertNotIn("mask", g.attrib, "mask no grupo blurred cria seams internos")

    def test_smooth_body_mask_contains_white_paths(self):
        # A máscara body-mask deve conter paths brancos para formar a silhueta sólida.
        svg = self._smooth_svg()
        root = ET.fromstring(svg)
        masks = [e for e in root.iter() if _tag(e) == "mask" and e.get("id") == "body-mask"]
        self.assertGreater(len(masks), 0)
        for mask in masks:
            white_paths = [c for c in mask.iter() if _tag(c) == "path" and c.get("fill") == "white"]
            self.assertGreater(len(white_paths), 0, "Máscara sem paths brancos")

    def test_smooth_female_has_body_mask(self):
        # body-mask deve aparecer também no corpo feminino.
        svg = self._smooth_svg(body="female")
        root = ET.fromstring(svg)
        masks = [e for e in root.iter() if _tag(e) == "mask" and e.get("id") == "body-mask"]
        self.assertGreater(len(masks), 0, "body-mask ausente no body=female")

    def test_smooth_detail_lines_have_no_fill(self):
        # As linhas de detalhe do contorno nítido têm fill="none" para não
        # cobrir o degradê por baixo.
        svg = self._smooth_svg()
        root = ET.fromstring(svg)
        detail = next((e for e in root if e.get("id") == "body-outline-detail"), None)
        self.assertIsNotNone(detail)
        self.assertEqual(detail.get("fill"), "none")

    def test_smooth_detail_lines_stroke_is_semitransparent(self):
        # O stroke das linhas de detalhe é semitransparente (rgba com alpha < 1),
        # já o contorno externo forte é sólido (preto opaco).
        svg = self._smooth_svg()
        self.assertIn("rgba", svg)
        root = ET.fromstring(svg)
        detail = next((e for e in root if e.get("id") == "body-outline-detail"), None)
        self.assertIsNotNone(detail)
        self.assertIn("rgba", detail.get("stroke", ""))
        outline = next((e for e in root if e.get("id") == "body-outline"), None)
        self.assertIsNotNone(outline)
        self.assertEqual(outline.get("stroke"), "#000000")


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes -- pulando testes de legend")
class TestLegend(unittest.TestCase):
    """Testa a legenda vertical de valores."""

    def _legend_svg(self, values=None, **kwargs):
        import anatomapa
        if values is None:
            values = {"head": 100, "trunk": 10}
        return str(anatomapa.heatmap(values, legend=True, **kwargs))

    def test_legend_contains_linear_gradient(self):
        svg = self._legend_svg()
        self.assertIn("linearGradient", svg)

    def test_legend_gradient_is_vertical(self):
        # Gradiente vertical: x1==x2 e y1!=y2 (ou y2=="100%")
        svg = self._legend_svg()
        root = ET.fromstring(svg)
        grads = [e for e in root.iter() if _tag(e) == "linearGradient"]
        legend_grad = next((g for g in grads if g.get("id") == "legend-gradient"), None)
        self.assertIsNotNone(legend_grad, "linearGradient com id legend-gradient ausente")
        self.assertEqual(legend_grad.get("x1"), "0%")
        self.assertEqual(legend_grad.get("x2"), "0%")
        self.assertEqual(legend_grad.get("y2"), "100%")

    def test_legend_label_pt(self):
        svg = self._legend_svg(lang="pt")
        self.assertIn("Valor", svg)

    def test_legend_label_en(self):
        svg = self._legend_svg(lang="en")
        self.assertIn("Value", svg)

    def test_legend_label_pt_not_en(self):
        # lang=pt não deve conter "Value" como rótulo da legenda
        svg = self._legend_svg(lang="pt")
        root = ET.fromstring(svg)
        legend_label = next(
            (e for e in root.iter() if _tag(e) == "text" and e.get("id") == "legend-label"),
            None,
        )
        self.assertIsNotNone(legend_label)
        self.assertEqual(legend_label.text, "Valor")

    def test_legend_label_en_text(self):
        svg = self._legend_svg(lang="en")
        root = ET.fromstring(svg)
        legend_label = next(
            (e for e in root.iter() if _tag(e) == "text" and e.get("id") == "legend-label"),
            None,
        )
        self.assertIsNotNone(legend_label)
        self.assertEqual(legend_label.text, "Value")

    def test_legend_contains_min_value(self):
        import anatomapa
        svg = str(anatomapa.heatmap({"head": 100, "trunk": 10}, legend=True))
        self.assertIn("10", svg)

    def test_legend_contains_max_value(self):
        import anatomapa
        svg = str(anatomapa.heatmap({"head": 100, "trunk": 10}, legend=True))
        self.assertIn("100", svg)

    def test_legend_contains_large_tick_value(self):
        # Verifica que o valor máximo 13666 aparece como tick
        import anatomapa
        values = {
            "head": 845, "arm": 1831, "forearm": 974, "hand": 5153,
            "finger": 8684, "trunk": 2602, "thigh": 1733, "leg": 1984,
            "foot": 13666, "toe": 6547,
        }
        svg = str(anatomapa.heatmap(values, legend=True, cmap="thermal", scale="log"))
        self.assertIn("13666", svg)

    def test_legend_has_tick_lines(self):
        # Legenda vertical deve ter elementos <line> para os ticks
        svg = self._legend_svg()
        root = ET.fromstring(svg)
        lines = [e for e in root.iter() if _tag(e) == "line"]
        self.assertGreater(len(lines), 0, "Nenhum elemento <line> de tick encontrado")

    def test_legend_is_valid_xml(self):
        svg = self._legend_svg()
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            self.fail(f"SVG com legenda inválido: {e}")

    def test_legend_contains_rect_for_bar(self):
        svg = self._legend_svg()
        root = ET.fromstring(svg)
        rects = [e for e in root.iter() if _tag(e) == "rect"]
        self.assertGreater(len(rects), 0)

    def test_legend_has_text_elements(self):
        svg = self._legend_svg()
        root = ET.fromstring(svg)
        texts = [e for e in root.iter() if _tag(e) == "text"]
        self.assertGreater(len(texts), 0)

    def test_legend_with_title(self):
        svg = self._legend_svg(title="Meu Título")
        self.assertIn("Meu Título", svg)

    def test_legend_false_no_gradient(self):
        import anatomapa
        svg = str(anatomapa.heatmap({"head": 10}, legend=False))
        self.assertNotIn("linearGradient", svg)

    def test_legend_gradient_has_stops(self):
        svg = self._legend_svg()
        root = ET.fromstring(svg)
        stops = [e for e in root.iter() if _tag(e) == "stop"]
        self.assertGreater(len(stops), 0)

    def test_legend_smooth_combined(self):
        svg = self._legend_svg(smooth=True, cmap="thermal")
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            self.fail(f"SVG smooth+legend inválido: {e}")
        self.assertIn("feGaussianBlur", svg)
        self.assertIn("linearGradient", svg)

    def test_legend_smooth_combined_deterministic(self):
        import anatomapa
        values = {"head": 100, "trunk": 10}
        svg1 = str(anatomapa.heatmap(values, smooth=True, legend=True, cmap="thermal"))
        svg2 = str(anatomapa.heatmap(values, smooth=True, legend=True, cmap="thermal"))
        self.assertEqual(svg1, svg2)

    def test_legend_thermal_cmap(self):
        svg = self._legend_svg(cmap="thermal")
        self.assertIn("linearGradient", svg)

    def test_legend_female_body(self):
        svg = self._legend_svg(body="female")
        self.assertIn("linearGradient", svg)

    def test_legend_viewbox_expanded(self):
        # viewBox de saída deve ter largura maior que o SVG original (legenda à direita)
        import anatomapa
        from anatomapa.render.svg import _parse_viewbox
        from anatomapa.model import loader as _loader
        import os
        base_dir = _loader._ASSETS_DIR
        svg_path = os.path.join(base_dir, "body_male_anterior.svg")
        with open(svg_path, encoding="utf-8") as fh:
            base_svg = fh.read()
        _, _, orig_w, _ = _parse_viewbox(base_svg)

        svg = self._legend_svg()
        root = ET.fromstring(svg)
        vb = root.get("viewBox", "")
        parts = vb.split()
        self.assertEqual(len(parts), 4, f"viewBox inválido: {vb}")
        out_w = float(parts[2])
        self.assertGreater(out_w, orig_w, "viewBox de saída não foi expandido para a legenda")

    def test_legend_smooth_viewbox_expanded(self):
        # Modo smooth com legend também expande o viewBox
        import anatomapa
        from anatomapa.render.svg import _parse_viewbox
        from anatomapa.model import loader as _loader
        import os
        base_dir = _loader._ASSETS_DIR
        svg_path = os.path.join(base_dir, "body_male_anterior.svg")
        with open(svg_path, encoding="utf-8") as fh:
            base_svg = fh.read()
        _, _, orig_w, _ = _parse_viewbox(base_svg)

        svg = self._legend_svg(smooth=True, cmap="thermal")
        root = ET.fromstring(svg)
        vb = root.get("viewBox", "")
        parts = vb.split()
        out_w = float(parts[2])
        self.assertGreater(out_w, orig_w, "viewBox smooth+legend não foi expandido")

    def test_format_value_integer(self):
        from anatomapa.render.svg import _format_value
        self.assertEqual(_format_value(10.0), "10")
        self.assertEqual(_format_value(0.0), "0")

    def test_format_value_float(self):
        from anatomapa.render.svg import _format_value
        self.assertEqual(_format_value(1.5), "1.50")
        self.assertEqual(_format_value(3.14159), "3.14")

    def test_compute_ticks_normal(self):
        from anatomapa.render.svg import _compute_ticks
        ticks = _compute_ticks(0.0, 100.0, 5)
        self.assertEqual(len(ticks), 5)
        self.assertAlmostEqual(ticks[0], 0.0)
        self.assertAlmostEqual(ticks[-1], 100.0)

    def test_compute_ticks_equal_min_max(self):
        # Quando min==max retorna lista com um único valor
        from anatomapa.render.svg import _compute_ticks
        ticks = _compute_ticks(42.0, 42.0)
        self.assertEqual(ticks, [42.0])


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes -- pulando testes de helper svg")
class TestSvgHelpers(unittest.TestCase):
    """Testa funções auxiliares do render/svg.py."""

    def test_parse_viewbox_valid(self):
        from anatomapa.render.svg import _parse_viewbox
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="10 20 300 600"></svg>'
        vx, vy, vw, vh = _parse_viewbox(svg)
        self.assertAlmostEqual(vx, 10.0)
        self.assertAlmostEqual(vy, 20.0)
        self.assertAlmostEqual(vw, 300.0)
        self.assertAlmostEqual(vh, 600.0)

    def test_parse_viewbox_missing(self):
        from anatomapa.render.svg import _parse_viewbox
        svg = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
        vx, vy, vw, vh = _parse_viewbox(svg)
        self.assertEqual(vw, 400.0)
        self.assertEqual(vh, 900.0)

    def test_parse_viewbox_invalid_xml(self):
        from anatomapa.render.svg import _parse_viewbox
        vx, vy, vw, vh = _parse_viewbox("não é xml")
        self.assertEqual(vw, 400.0)
        self.assertEqual(vh, 900.0)

    def test_parse_viewbox_wrong_parts(self):
        from anatomapa.render.svg import _parse_viewbox
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400"></svg>'
        vx, vy, vw, vh = _parse_viewbox(svg)
        self.assertEqual(vw, 400.0)

    def test_extract_body_outline_present(self):
        from anatomapa.render.svg import _extract_body_outline_d
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g id="silhouette"><path id="body-outline" d="M 0 0 Z" /></g>'
            '</svg>'
        )
        d = _extract_body_outline_d(svg)
        self.assertEqual(d, "M 0 0 Z")

    def test_extract_body_outline_absent(self):
        from anatomapa.render.svg import _extract_body_outline_d
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><g id="regions"></g></svg>'
        d = _extract_body_outline_d(svg)
        self.assertIsNone(d)

    def test_extract_body_outline_invalid_xml(self):
        from anatomapa.render.svg import _extract_body_outline_d
        d = _extract_body_outline_d("não é xml")
        self.assertIsNone(d)

    def test_parse_viewbox_non_numeric(self):
        from anatomapa.render.svg import _parse_viewbox
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="a b c d"></svg>'
        vx, vy, vw, vh = _parse_viewbox(svg)
        self.assertEqual(vw, 400.0)


class TestSvgRendererSmoothNoOutline(unittest.TestCase):
    """Testa smooth quando o SVG base não tem body-outline."""

    def test_smooth_without_outline_is_valid_xml(self):
        from anatomapa.render.svg import SvgRenderer, _build_smooth_svg
        from anatomapa.domain.heatmap import Heatmap
        from anatomapa.color.registry import get_colormap

        base_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions">'
            '<path id="head" d="M 10 10 Z" />'
            '</g>'
            '</svg>'
        )
        hm = Heatmap(
            colors={"head": (255, 0, 0)},
            scale_name="linear",
            value_min=0.0,
            value_max=100.0,
            lang="pt",
            title=None,
        )
        cmap = get_colormap("reds")
        svg = _build_smooth_svg(base_svg, hm, cmap, legend=False)
        ET.fromstring(svg)  # deve ser XML válido

    def test_smooth_blurred_group_no_clip_or_mask(self):
        from anatomapa.render.svg import _build_smooth_svg
        from anatomapa.domain.heatmap import Heatmap
        from anatomapa.color.registry import get_colormap

        base_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions"><path id="head" d="M 0 0 Z" /></g>'
            '</svg>'
        )
        hm = Heatmap(
            colors={"head": (200, 100, 50)},
            scale_name="linear",
            value_min=0.0,
            value_max=200.0,
            lang="pt",
        )
        cmap = get_colormap("thermal")
        svg = _build_smooth_svg(base_svg, hm, cmap, legend=False)
        root = ET.fromstring(svg)
        blurred = [e for e in root.iter() if _tag(e) == "g" and "thermal-blur" in e.get("filter", "")]
        self.assertGreater(len(blurred), 0)
        for g in blurred:
            self.assertNotIn("clip-path", g.attrib)
            self.assertNotIn("mask", g.attrib)

    def test_smooth_with_legend_no_outline(self):
        from anatomapa.render.svg import _build_smooth_svg
        from anatomapa.domain.heatmap import Heatmap
        from anatomapa.color.registry import get_colormap

        base_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions"><path id="head" d="M 0 0 Z" /></g>'
            '</svg>'
        )
        hm = Heatmap(
            colors={"head": (200, 100, 50)},
            scale_name="linear",
            value_min=5.0,
            value_max=200.0,
            lang="pt",
            title="Legenda Teste",
        )
        cmap = get_colormap("thermal")
        svg = _build_smooth_svg(base_svg, hm, cmap, legend=True)
        self.assertIn("linearGradient", svg)
        self.assertIn("Legenda Teste", svg)

    def test_smooth_regions_cold_color_when_no_value(self):
        from anatomapa.render.svg import _build_smooth_svg
        from anatomapa.domain.heatmap import Heatmap
        from anatomapa.color.registry import get_colormap

        base_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions">'
            '<path id="head" d="M 0 0 Z" />'
            '<path id="trunk" d="M 1 1 Z" />'
            '</g>'
            '</svg>'
        )
        # Apenas head tem valor; trunk deve receber a cor fria quando missing="cold"
        hm = Heatmap(
            colors={"head": (255, 0, 0)},
            scale_name="linear",
            value_min=0.0,
            value_max=100.0,
            lang="pt",
        )
        cmap = get_colormap("thermal")
        cold_color = "#{:02x}{:02x}{:02x}".format(*cmap.color_at(0.0))
        svg = _build_smooth_svg(base_svg, hm, cmap, legend=False, missing="cold")
        self.assertIn(cold_color, svg)

    def test_smooth_regions_neutral_color_when_no_value_by_default(self):
        from anatomapa.render.svg import _build_smooth_svg
        from anatomapa.domain.heatmap import Heatmap
        from anatomapa.color.registry import get_colormap

        base_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions">'
            '<path id="head" d="M 0 0 Z" />'
            '<path id="trunk" d="M 1 1 Z" />'
            '</g>'
            '</svg>'
        )
        # Apenas head tem valor; por padrão (missing="neutral"), trunk deve
        # receber o cinza discreto, não a cor fria do colormap.
        hm = Heatmap(
            colors={"head": (255, 0, 0)},
            scale_name="linear",
            value_min=0.0,
            value_max=100.0,
            lang="pt",
        )
        cmap = get_colormap("thermal")
        svg = _build_smooth_svg(base_svg, hm, cmap, legend=False)
        self.assertIn("#9aa0a6", svg)


class TestSvgRendererNewParams(unittest.TestCase):
    """Testa SvgRenderer.render() com novos parâmetros smooth/legend."""

    def _make_model(self):
        from anatomapa.domain.model import AnatomicalModel
        from anatomapa.domain.region import Region
        return AnatomicalModel(
            _regions=(
                Region(
                    id="head",
                    label_pt="Cabeça",
                    label_en="Head",
                    aliases=(),
                    bilateral=False,
                    parent=None,
                    geometry={"center": "M 10 10 Z"},
                ),
            )
        )

    def _make_heatmap(self):
        from anatomapa.domain.heatmap import Heatmap
        return Heatmap(
            colors={"head": (200, 50, 50)},
            scale_name="linear",
            value_min=0.0,
            value_max=100.0,
            lang="pt",
        )

    def test_render_with_legend_from_model(self):
        from anatomapa.render.svg import SvgRenderer
        from anatomapa.color.registry import get_colormap
        renderer = SvgRenderer()
        model = self._make_model()
        hm = self._make_heatmap()
        cmap = get_colormap("reds")
        fig = renderer.render(hm, model, legend=True, colormap=cmap)
        self.assertIn("linearGradient", str(fig))

    def test_render_legend_false_no_gradient_from_model(self):
        from anatomapa.render.svg import SvgRenderer
        from anatomapa.color.registry import get_colormap
        renderer = SvgRenderer()
        model = self._make_model()
        hm = self._make_heatmap()
        cmap = get_colormap("reds")
        fig = renderer.render(hm, model, legend=False, colormap=cmap)
        self.assertNotIn("linearGradient", str(fig))

    def test_render_onto_svg_with_legend(self):
        from anatomapa.render.svg import SvgRenderer
        from anatomapa.color.registry import get_colormap
        renderer = SvgRenderer()
        model = self._make_model()
        hm = self._make_heatmap()
        cmap = get_colormap("reds")
        base_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions"><path id="head" d="M 0 0 Z" /></g>'
            '</svg>'
        )
        fig = renderer.render(hm, model, base_svg=base_svg, legend=True, colormap=cmap)
        self.assertIn("linearGradient", str(fig))

    def test_render_smooth_requires_colormap_and_base_svg(self):
        # smooth=True sem colormap nem base_svg cai no ramo _render_from_model
        from anatomapa.render.svg import SvgRenderer
        renderer = SvgRenderer()
        model = self._make_model()
        hm = self._make_heatmap()
        # smooth=True mas sem base_svg: deve usar _render_from_model
        fig = renderer.render(hm, model, smooth=True)
        self.assertIn("<svg", str(fig))
        # Sem base_svg, não há feGaussianBlur
        self.assertNotIn("feGaussianBlur", str(fig))

    def test_render_smooth_with_base_svg_but_no_colormap(self):
        # smooth=True com base_svg mas sem colormap: usa _render_onto_svg
        from anatomapa.render.svg import SvgRenderer
        renderer = SvgRenderer()
        model = self._make_model()
        hm = self._make_heatmap()
        base_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions"><path id="head" d="M 0 0 Z" /></g>'
            '</svg>'
        )
        fig = renderer.render(hm, model, base_svg=base_svg, smooth=True, colormap=None)
        self.assertIn("<svg", str(fig))
        self.assertNotIn("feGaussianBlur", str(fig))

    def test_append_legend_with_existing_defs(self):
        # Testa _append_legend quando já há um bloco <defs> no SVG
        from anatomapa.render.svg import _build_smooth_svg
        from anatomapa.domain.heatmap import Heatmap
        from anatomapa.color.registry import get_colormap

        base_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<defs><style>.x{fill:red}</style></defs>'
            '<g id="regions"><path id="head" d="M 0 0 Z" /></g>'
            '</svg>'
        )
        hm = Heatmap(
            colors={"head": (200, 50, 50)},
            scale_name="linear",
            value_min=0.0,
            value_max=100.0,
            lang="pt",
        )
        cmap = get_colormap("thermal")
        svg = _build_smooth_svg(base_svg, hm, cmap, legend=True)
        # Deve ter linearGradient e ser XML válido
        self.assertIn("linearGradient", svg)
        ET.fromstring(svg)


class TestBackgroundParameter(unittest.TestCase):
    """Testa o parâmetro background no SvgRenderer (modo flat e smooth)."""

    def _make_model(self):
        from anatomapa.domain.model import AnatomicalModel
        from anatomapa.domain.region import Region
        return AnatomicalModel(
            _regions=(
                Region(
                    id="head",
                    label_pt="Cabeça",
                    label_en="Head",
                    aliases=(),
                    bilateral=False,
                    parent=None,
                    geometry={"center": "M 10 10 Z"},
                ),
            )
        )

    def _make_heatmap(self):
        from anatomapa.domain.heatmap import Heatmap
        return Heatmap(
            colors={"head": (200, 50, 50)},
            scale_name="linear",
            value_min=0.0,
            value_max=100.0,
            lang="pt",
        )

    def _base_svg(self):
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 900">'
            '<g id="regions"><path id="head" d="M 0 0 Z" /></g>'
            '</svg>'
        )

    def test_render_invalid_background_raises(self):
        from anatomapa.render.svg import SvgRenderer
        renderer = SvgRenderer()
        with self.assertRaises(ValueError):
            renderer.render(self._make_heatmap(), self._make_model(), background="purple")

    def test_onto_svg_dark_background_draws_rect(self):
        from anatomapa.render.svg import SvgRenderer
        renderer = SvgRenderer()
        fig = renderer.render(
            self._make_heatmap(), self._make_model(),
            base_svg=self._base_svg(), background="dark",
        )
        root = ET.fromstring(str(fig))
        bg = next((e for e in root if e.get("id") == "figure-background"), None)
        self.assertIsNotNone(bg)
        self.assertEqual(bg.get("fill"), "#0a0a0a")

    def test_onto_svg_transparent_background_no_rect(self):
        from anatomapa.render.svg import SvgRenderer
        renderer = SvgRenderer()
        fig = renderer.render(
            self._make_heatmap(), self._make_model(), base_svg=self._base_svg(),
        )
        root = ET.fromstring(str(fig))
        bg = next((e for e in root if e.get("id") == "figure-background"), None)
        self.assertIsNone(bg)

    def test_from_model_light_background_draws_white_rect(self):
        from anatomapa.render.svg import SvgRenderer
        renderer = SvgRenderer()
        fig = renderer.render(self._make_heatmap(), self._make_model(), background="light")
        root = ET.fromstring(str(fig))
        bg = next((e for e in root if e.get("id") == "figure-background"), None)
        self.assertIsNotNone(bg)
        self.assertEqual(bg.get("fill"), "#ffffff")

    def test_legend_text_dark_on_light_background(self):
        from anatomapa.render.svg import SvgRenderer
        from anatomapa.color.registry import get_colormap
        renderer = SvgRenderer()
        cmap = get_colormap("reds")
        fig = renderer.render(
            self._make_heatmap(), self._make_model(),
            legend=True, colormap=cmap, background="light",
        )
        root = ET.fromstring(str(fig))
        label = next((e for e in root.iter() if e.get("id") == "legend-label"), None)
        self.assertIsNotNone(label)
        self.assertEqual(label.get("fill"), "#1a1a1a")

    def test_legend_text_light_on_dark_background(self):
        from anatomapa.render.svg import SvgRenderer
        from anatomapa.color.registry import get_colormap
        renderer = SvgRenderer()
        cmap = get_colormap("reds")
        fig = renderer.render(
            self._make_heatmap(), self._make_model(),
            legend=True, colormap=cmap, background="dark",
        )
        root = ET.fromstring(str(fig))
        label = next((e for e in root.iter() if e.get("id") == "legend-label"), None)
        self.assertIsNotNone(label)
        self.assertEqual(label.get("fill"), "#f2f2f2")


if __name__ == "__main__":
    unittest.main()
