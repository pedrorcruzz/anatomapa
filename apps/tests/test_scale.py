import unittest

from anatomapa.domain.scale import LinearScale, LogScale


class TestLinearScale(unittest.TestCase):
    def setUp(self):
        self.scale = LinearScale()

    def test_basic_normalization(self):
        result = self.scale.normalize([0.0, 5.0, 10.0])
        self.assertAlmostEqual(result[0], 0.0)
        self.assertAlmostEqual(result[1], 0.5)
        self.assertAlmostEqual(result[2], 1.0)

    def test_all_equal_returns_zeros(self):
        result = self.scale.normalize([7.0, 7.0, 7.0])
        self.assertEqual(result, [0.0, 0.0, 0.0])

    def test_single_value(self):
        result = self.scale.normalize([42.0])
        self.assertEqual(result, [0.0])

    def test_empty_input(self):
        result = self.scale.normalize([])
        self.assertEqual(result, [])

    def test_negative_values(self):
        result = self.scale.normalize([-10.0, 0.0, 10.0])
        self.assertAlmostEqual(result[0], 0.0)
        self.assertAlmostEqual(result[1], 0.5)
        self.assertAlmostEqual(result[2], 1.0)

    def test_determinism(self):
        values = [3.0, 1.0, 4.0, 1.0, 5.0]
        r1 = self.scale.normalize(values)
        r2 = self.scale.normalize(values)
        self.assertEqual(r1, r2)

    def test_result_length_matches_input(self):
        values = [1.0, 2.0, 3.0, 4.0]
        self.assertEqual(len(self.scale.normalize(values)), 4)


class TestLogScale(unittest.TestCase):
    def setUp(self):
        self.scale = LogScale()

    def test_extremes_map_to_0_and_1(self):
        result = self.scale.normalize([1.0, 10.0, 100.0])
        self.assertAlmostEqual(result[0], 0.0)
        self.assertAlmostEqual(result[-1], 1.0)

    def test_all_zeros_returns_zeros(self):
        result = self.scale.normalize([0.0, 0.0, 0.0])
        self.assertEqual(result, [0.0, 0.0, 0.0])

    def test_zeros_handled_safely(self):
        result = self.scale.normalize([0.0, 1.0, 10.0])
        self.assertAlmostEqual(result[0], 0.0)
        self.assertAlmostEqual(result[-1], 1.0)
        self.assertTrue(0.0 < result[1] < 1.0)

    def test_negative_values_handled_safely(self):
        result = self.scale.normalize([-5.0, 0.0, 5.0])
        self.assertAlmostEqual(result[0], 0.0)
        self.assertAlmostEqual(result[-1], 1.0)

    def test_empty_input(self):
        result = self.scale.normalize([])
        self.assertEqual(result, [])

    def test_single_value(self):
        result = self.scale.normalize([100.0])
        self.assertEqual(result, [0.0])

    def test_determinism(self):
        values = [1.0, 10.0, 100.0, 1000.0]
        r1 = self.scale.normalize(values)
        r2 = self.scale.normalize(values)
        self.assertEqual(r1, r2)

    def test_compression_vs_linear(self):
        # Log deve comprimir extremos: o ponto médio normalizado de [1, 10, 100]
        # deve estar bem acima de 0.5 (diferente da escala linear, que coloca 10 em ~0.1)
        import math
        result = self.scale.normalize([1.0, 10.0, 100.0])
        linear_mid = (10.0 - 1.0) / (100.0 - 1.0)
        # O valor do meio na escala log deve diferir da escala linear
        self.assertNotAlmostEqual(result[1], linear_mid, places=2)


if __name__ == "__main__":
    unittest.main()
