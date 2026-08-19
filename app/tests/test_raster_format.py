"""Tests for the `format` parameter and the raster output (png/jpg/jpeg).

Raster formats depend on the optional extra (`cairosvg`/`Pillow`), which is not
installed in the zero-dep CI. To cover the success path without the real
dependency, fake modules are injected into `sys.modules`; what is under test is
the library's own dispatch logic, not cairosvg/Pillow.
"""

import io
import os
import sys
import tempfile
import types
import unittest

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "anatomapa", "assets")
_ASSETS_EXIST = os.path.exists(os.path.join(_ASSETS_DIR, "body_male_anterior.svg"))


class _FakeImg:
    """Fake image exposing the surface the raster pipeline touches.

    Enough to exercise the library's own compositing logic: blur, alpha mask,
    cold glow and layer order. The pixel maths is Pillow's business.
    """

    def __init__(self, size=(4, 4)):
        self.size = size

    def convert(self, mode):
        return self

    def split(self):
        return (self, self, self, self)

    def paste(self, im, mask=None):
        self._pasted = True

    def filter(self, kernel):
        return self

    def getchannel(self, band):
        return self

    def putalpha(self, band):
        self._alpha = band

    def alpha_composite(self, other):
        self._composited = True

    def save(self, fp, format=None, quality=None):
        if (format or "").upper() == "PNG":
            fp.write(b"PNG:fake")
            return
        fp.write(b"JPEG-DATA:" + (format or "").encode() + str(quality).encode())


def _install_fakes():
    names = ("cairosvg", "PIL", "PIL.Image", "PIL.ImageChops", "PIL.ImageFilter")
    saved = {name: sys.modules.get(name) for name in names}

    cairo = types.ModuleType("cairosvg")
    cairo.svg2png = lambda bytestring=None, scale=1.0: b"PNG:" + bytestring[:4] + bytes([int(scale)])
    sys.modules["cairosvg"] = cairo

    pil = types.ModuleType("PIL")
    image = types.ModuleType("PIL.Image")
    image.open = lambda fp: _FakeImg()
    image.new = lambda mode, size, color: _FakeImg(size)
    chops = types.ModuleType("PIL.ImageChops")
    chops.invert = lambda im: im
    chops.multiply = lambda a, b: a

    filters = types.ModuleType("PIL.ImageFilter")
    filters.GaussianBlur = lambda radius: ("blur", radius)

    pil.Image = image
    pil.ImageChops = chops
    pil.ImageFilter = filters
    sys.modules["PIL"] = pil
    sys.modules["PIL.Image"] = image
    sys.modules["PIL.ImageChops"] = chops
    sys.modules["PIL.ImageFilter"] = filters
    return saved


def _restore(saved):
    for name, mod in saved.items():
        if mod is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = mod


class TestRasterWithFakes(unittest.TestCase):
    def setUp(self):
        self._saved = _install_fakes()

    def tearDown(self):
        _restore(self._saved)

    def test_svg_to_png(self):
        from anatomapa.render.raster import svg_to_png
        out = svg_to_png("<svg/>", scale=2.0)
        self.assertTrue(out.startswith(b"PNG:"))

    def test_png_to_jpeg(self):
        from anatomapa.render.raster import png_to_jpeg
        out = png_to_jpeg(b"PNGDATA", quality=80)
        self.assertTrue(out.startswith(b"JPEG-DATA:JPEG"))

    def test_figure_to_png(self):
        from anatomapa.render.base import Figure
        self.assertTrue(Figure("<svg/>").to_png().startswith(b"PNG:"))

    def test_figure_to_jpeg(self):
        from anatomapa.render.base import Figure
        self.assertTrue(Figure("<svg/>").to_jpeg().startswith(b"JPEG-DATA:"))

    def test_save_png_writes_bytes(self):
        from anatomapa.render.base import Figure
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.png")
            Figure("<svg/>", format="png").save(path)
            with open(path, "rb") as fh:
                self.assertTrue(fh.read().startswith(b"PNG:"))

    def test_save_jpeg_by_extension(self):
        from anatomapa.render.base import Figure
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.jpg")
            Figure("<svg/>").save(path)
            with open(path, "rb") as fh:
                self.assertTrue(fh.read().startswith(b"JPEG-DATA:"))

    def test_explicit_format_overrides_extension(self):
        from anatomapa.render.base import Figure
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.txt")
            Figure("<svg/>").save(path, format="png")
            with open(path, "rb") as fh:
                self.assertTrue(fh.read().startswith(b"PNG:"))

    @unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
    def test_heatmap_format_png_saves_raster(self):
        import anatomapa
        fig = anatomapa.heatmap({"head": 10}, format="png")
        self.assertEqual(fig._format, "png")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "map.png")
            fig.save(path)
            with open(path, "rb") as fh:
                self.assertTrue(fh.read().startswith(b"PNG:"))


class TestRasterVariant(unittest.TestCase):
    """An SVG figure must rasterise through its filter-free variant.

    Raster converters ignore SVG filters, so rasterising the smooth SVG would
    paint the body blank.
    """

    def test_without_a_variant_the_own_svg_is_used(self):
        from anatomapa.render.base import Figure
        self.assertEqual(Figure("<svg>a</svg>")._svg_for_raster(), "<svg>a</svg>")

    def test_variant_replaces_the_svg_for_raster_only(self):
        from anatomapa.render.base import Figure
        figure = Figure("<svg>smooth</svg>", raster_svg=lambda: "<svg>flat</svg>")
        self.assertEqual(figure.to_svg(), "<svg>smooth</svg>")
        self.assertEqual(figure._svg_for_raster(), "<svg>flat</svg>")

    def test_variant_is_built_once_and_reused(self):
        from anatomapa.render.base import Figure
        calls = []

        def build():
            calls.append(1)
            return "<svg>flat</svg>"

        figure = Figure("<svg>smooth</svg>", raster_svg=build)
        figure._svg_for_raster()
        figure._svg_for_raster()
        self.assertEqual(len(calls), 1)

    @unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
    def test_svg_figure_carries_a_filter_free_variant(self):
        import anatomapa
        figure = anatomapa.heatmap({"head": 10, "foot": 90})
        self.assertIn("filter=", figure.to_svg())
        self.assertNotIn("filter=", figure._svg_for_raster())

    @unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
    def test_png_figure_is_already_flat_and_needs_no_variant(self):
        import anatomapa
        figure = anatomapa.heatmap({"head": 10, "foot": 90}, format="png")
        self.assertNotIn("filter=", figure.to_svg())
        self.assertEqual(figure._svg_for_raster(), figure.to_svg())

    @unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
    def test_each_split_figure_gets_its_own_variant(self):
        import anatomapa
        front, back = anatomapa.heatmap(
            {"head": 10, "foot": 90}, view="both", split=True
        )
        self.assertNotIn("filter=", front._svg_for_raster())
        self.assertNotIn("filter=", back._svg_for_raster())
        self.assertNotEqual(front._svg_for_raster(), back._svg_for_raster())


class TestRasterMissingDependency(unittest.TestCase):
    """Without the extra installed, raster formats fail with an install hint."""

    def setUp(self):
        self._saved = {n: sys.modules.get(n) for n in ("cairosvg", "PIL", "PIL.Image")}
        # None em sys.modules faz o import levantar ImportError.
        sys.modules["cairosvg"] = None
        sys.modules["PIL"] = None
        sys.modules["PIL.Image"] = None

    def tearDown(self):
        _restore(self._saved)

    def test_svg_to_png_raises_hint(self):
        from anatomapa.render.raster import svg_to_png
        with self.assertRaises(ImportError) as ctx:
            svg_to_png("<svg/>")
        self.assertIn("anatomapa[raster]", str(ctx.exception))

    def test_png_to_jpeg_raises_hint(self):
        from anatomapa.render.raster import png_to_jpeg
        with self.assertRaises(ImportError) as ctx:
            png_to_jpeg(b"x")
        self.assertIn("anatomapa[raster]", str(ctx.exception))


class TestSaveSvgDefault(unittest.TestCase):
    def test_save_svg_default(self):
        from anatomapa.render.base import Figure
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.svg")
            Figure("<svg>ok</svg>").save(path)
            with open(path, encoding="utf-8") as fh:
                self.assertIn("<svg>ok</svg>", fh.read())

    def test_unknown_extension_falls_back_to_format(self):
        from anatomapa.render.base import Figure
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.dat")
            Figure("<svg>x</svg>").save(path)
            with open(path, encoding="utf-8") as fh:
                self.assertIn("<svg>x</svg>", fh.read())



@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestRasterBlend(unittest.TestCase):
    """The raster output must rebuild the thermal blend the SVG filter makes.

    Converters ignore SVG filters, so a plain conversion loses the blur and
    turns every hairline gap of the source drawing into a white band. The
    pipeline therefore splits the figure into layers, blurs the colour one and
    puts the crisp outline back on top.
    """

    def setUp(self):
        self._saved = _install_fakes()
        self._svgs = []
        import cairosvg

        original = cairosvg.svg2png

        def spy(bytestring=None, scale=1.0):
            self._svgs.append(bytestring.decode("utf-8"))
            return original(bytestring=bytestring, scale=scale)

        cairosvg.svg2png = spy

    def tearDown(self):
        _restore(self._saved)

    def _render(self):
        import anatomapa

        anatomapa.heatmap({"head": 10}, format="png").to_png()
        return self._svgs

    def test_splits_the_figure_into_layers(self):
        camadas = self._render()
        self.assertEqual(len(camadas), 4, "cor, nítida, fundo e máscara")

    def test_colour_layer_has_regions_without_the_outline(self):
        cor = self._render()[0]
        self.assertIn('id="regions"', cor)
        self.assertNotIn('id="body-outline"', cor)

    def test_crisp_layer_has_the_outline_without_the_regions(self):
        nitida = self._render()[1]
        self.assertIn('id="body-outline"', nitida)
        self.assertNotIn('id="regions"', nitida)

    def test_mask_layer_is_the_silhouette_alone(self):
        mascara = self._render()[3]
        self.assertIn('fill="white"', mascara)
        self.assertIn('fill="black"', mascara)
        self.assertNotIn('id="regions"', mascara)

    def test_bodyless_svg_skips_the_blend(self):
        from anatomapa.render.raster import svg_to_png

        out = svg_to_png("<svg/>", scale=2.0)
        self.assertTrue(out.startswith(b"PNG:"))
        self.assertEqual(len(self._svgs), 1, "uma conversão só, sem camadas")

    def test_broken_svg_falls_back_instead_of_raising(self):
        from anatomapa.render.raster import svg_to_png

        self.assertTrue(svg_to_png("<svg", scale=1.0).startswith(b"PNG:"))


if __name__ == "__main__":
    unittest.main()
