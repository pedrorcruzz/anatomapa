import unittest

from anatomapa.domain.colormap import ColorMap


class TestColorMap(unittest.TestCase):
    def setUp(self):
        self.cmap = ColorMap(
            stops=(
                (0.0, (0, 0, 0)),
                (0.5, (128, 128, 128)),
                (1.0, (255, 255, 255)),
            )
        )

    def test_color_at_zero(self):
        self.assertEqual(self.cmap.color_at(0.0), (0, 0, 0))

    def test_color_at_one(self):
        self.assertEqual(self.cmap.color_at(1.0), (255, 255, 255))

    def test_color_at_midpoint(self):
        r, g, b = self.cmap.color_at(0.5)
        self.assertEqual((r, g, b), (128, 128, 128))

    def test_interpolation_between_stops(self):
        r, g, b = self.cmap.color_at(0.25)
        self.assertAlmostEqual(r, 64, delta=1)
        self.assertAlmostEqual(g, 64, delta=1)
        self.assertAlmostEqual(b, 64, delta=1)

    def test_clamp_below_zero(self):
        self.assertEqual(self.cmap.color_at(-1.0), (0, 0, 0))

    def test_clamp_above_one(self):
        self.assertEqual(self.cmap.color_at(2.0), (255, 255, 255))

    def test_single_stop(self):
        cmap = ColorMap(stops=((0.0, (100, 150, 200)),))
        self.assertEqual(cmap.color_at(0.5), (100, 150, 200))

    def test_result_within_rgb_range(self):
        for t in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]:
            r, g, b = self.cmap.color_at(t)
            self.assertGreaterEqual(r, 0)
            self.assertLessEqual(r, 255)
            self.assertGreaterEqual(g, 0)
            self.assertLessEqual(g, 255)
            self.assertGreaterEqual(b, 0)
            self.assertLessEqual(b, 255)

    def test_determinism(self):
        results = [self.cmap.color_at(0.3) for _ in range(5)]
        self.assertTrue(all(r == results[0] for r in results))

    def test_reds_colormap(self):
        from anatomapa.color.registry import get_colormap
        reds = get_colormap("reds")
        low = reds.color_at(0.0)
        high = reds.color_at(1.0)
        # Extremo baixo deve ser mais claro (maior R, G, B) que o extremo alto
        self.assertGreater(low[1], high[1])

    def test_viridis_colormap(self):
        from anatomapa.color.registry import get_colormap
        viridis = get_colormap("viridis")
        c0 = viridis.color_at(0.0)
        c1 = viridis.color_at(1.0)
        self.assertNotEqual(c0, c1)


if __name__ == "__main__":
    unittest.main()
