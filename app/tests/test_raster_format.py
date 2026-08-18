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
    """Fake image exposing the minimum surface png_to_jpeg uses."""

    def __init__(self, size=(4, 4)):
        self.size = size

    def convert(self, mode):
        return self

    def split(self):
        return (self, self, self, self)

    def paste(self, im, mask=None):
        self._pasted = True

    def save(self, fp, format=None, quality=None):
        fp.write(b"JPEG-DATA:" + (format or "").encode() + str(quality).encode())


def _install_fakes():
    saved = {name: sys.modules.get(name) for name in ("cairosvg", "PIL", "PIL.Image")}

    cairo = types.ModuleType("cairosvg")
    cairo.svg2png = lambda bytestring=None, scale=1.0: b"PNG:" + bytestring[:4] + bytes([int(scale)])
    sys.modules["cairosvg"] = cairo

    pil = types.ModuleType("PIL")
    image = types.ModuleType("PIL.Image")
    image.open = lambda fp: _FakeImg()
    image.new = lambda mode, size, color: _FakeImg(size)
    pil.Image = image
    sys.modules["PIL"] = pil
    sys.modules["PIL.Image"] = image
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


if __name__ == "__main__":
    unittest.main()
