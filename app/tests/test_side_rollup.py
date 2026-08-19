"""Tests for side-aware inheritance down the region tree.

Covers the resolution rule: walking up from a region, the first ancestor with a
value wins, and on each step the lateralised key beats the plain one. Also
covers the legend range, which must ignore a value that ends up painting
nothing, and the deprecation warning for the ids whose meaning changed in 0.4.
"""

import os
import unittest
import warnings

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "anatomapa", "assets")
_ASSETS_EXIST = os.path.exists(os.path.join(_ASSETS_DIR, "regions.json"))


def _plan(values: dict, view: str = "anterior", body: str = "male") -> dict:
    """Paint key -> value actually applied, for one view."""
    from anatomapa.model import loader as _loader
    from anatomapa.usecases.build import _paint_plan

    model = _loader.load(view, body=body)
    floats = {k: float(v) for k, v in values.items()}
    return {key: floats[src] for key, src in _paint_plan(model, floats).items()}


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestSideAwareRollup(unittest.TestCase):
    """Inheritance across the tree, side by side."""

    def test_canonical_parent_paints_both_sides(self):
        plan = _plan({"leg": 6})
        for region in ("hip", "thigh", "knee", "lower_leg", "ankle", "foot", "toe"):
            self.assertEqual(
                plan.get(region), 6.0, f"{region} deveria herdar leg nos dois lados"
            )

    def test_lateralised_parent_paints_one_side_only(self):
        plan = _plan({"leg_left": 6})
        self.assertEqual(plan.get("thigh_left"), 6.0)
        self.assertNotIn("thigh_right", plan)
        self.assertNotIn("thigh", plan)

    def test_side_beats_general_on_the_same_step(self):
        plan = _plan({"leg": 3, "leg_left": 9})
        self.assertEqual(plan["thigh_left"], 9.0)
        self.assertEqual(plan["thigh_right"], 3.0)

    def test_deeper_region_beats_lateralised_ancestor(self):
        # foot é mais fundo que leg, então vence mesmo sem lado explícito. Como
        # vale para os dois pés, o resultado sai na chave simples
        plan = _plan({"leg_left": 10, "foot": 2})
        self.assertEqual(plan["foot"], 2.0)
        self.assertNotIn("foot_left", plan)
        self.assertEqual(plan["thigh_left"], 10.0)

    def test_child_value_overrides_parent(self):
        plan = _plan({"leg": 5, "foot_right": 10})
        self.assertEqual(plan["foot_right"], 10.0)
        self.assertEqual(plan["foot_left"], 5.0)
        self.assertEqual(plan["toe_right"], 10.0, "o dedo herda o pé, não a perna")

    def test_asymmetric_general_and_detailed(self):
        plan = _plan(
            {"leg_right": 8, "thigh_left": 2, "lower_leg_left": 9, "foot_left": 4}
        )
        for region in ("hip", "thigh", "knee", "lower_leg", "ankle", "foot", "toe"):
            self.assertEqual(plan.get(f"{region}_right"), 8.0, region)
        self.assertEqual(plan["thigh_left"], 2.0)
        self.assertEqual(plan["lower_leg_left"], 9.0)
        self.assertEqual(plan["foot_left"], 4.0)
        self.assertEqual(plan["toe_left"], 4.0)
        # quem detalha assume cobrir tudo: sem valor, não pinta
        self.assertNotIn("hip_left", plan)

    def test_symmetric_result_keeps_the_plain_key(self):
        # Dois lados com o mesmo valor não viram duas entradas lateralizadas
        plan = _plan({"chest_left": 4, "chest_right": 4})
        self.assertIn("upper_chest", plan)
        self.assertNotIn("upper_chest_left", plan)

    def test_input_order_does_not_matter(self):
        first = _plan({"leg": 3, "foot_left": 7})
        second = _plan({"foot_left": 7, "leg": 3})
        self.assertEqual(first, second)


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestLegendRange(unittest.TestCase):
    """value_min/value_max must cover only what really paints."""

    def _heatmap(self, values: dict, view: str = "anterior"):
        from anatomapa.color.registry import get_colormap, get_scale
        from anatomapa.model import loader as _loader
        from anatomapa.usecases.build import build_heatmap

        return build_heatmap(
            {k: float(v) for k, v in values.items()},
            _loader.load(view, body="male"),
            get_colormap("thermal"),
            get_scale("linear"),
        )

    def test_inert_aggregate_does_not_stretch_the_legend(self):
        result = self._heatmap(
            {
                "trunk": 999,
                "upper_chest": 1,
                "lower_chest": 2,
                "upper_abdomen": 3,
                "lower_abdomen": 4,
                "shoulder": 5,
                "genital": 6,
                "upper_back": 7,
                "lower_back": 8,
            }
        )
        self.assertEqual((result.value_min, result.value_max), (1.0, 8.0))

    def test_values_that_paint_nothing_give_an_empty_heatmap(self):
        # Nenhuma chave corresponde a região do modelo: nada pinta, nada na escala
        result = self._heatmap({"nao_existe": 7, "outra_invencao": 9})
        self.assertEqual(result.colors, {})
        self.assertEqual((result.value_min, result.value_max), (0.0, 0.0))

    def test_aggregate_that_paints_still_counts(self):
        result = self._heatmap({"trunk": 50, "upper_chest": 1})
        self.assertEqual((result.value_min, result.value_max), (1.0, 50.0))

    def test_other_view_regions_keep_the_scale_shared(self):
        # upper_back só desenha atrás, mas tem de entrar na escala da frente,
        # senão os dois painéis de view="both" saem com cores incomparáveis
        anterior = self._heatmap({"upper_chest": 1, "upper_back": 90}, "anterior")
        posterior = self._heatmap({"upper_chest": 1, "upper_back": 90}, "posterior")
        self.assertEqual(anterior.value_max, 90.0)
        self.assertEqual(anterior.value_min, posterior.value_min)
        self.assertEqual(anterior.value_max, posterior.value_max)


@unittest.skipUnless(_ASSETS_EXIST, "Assets ausentes")
class TestChangedMeaningWarning(unittest.TestCase):
    """`leg` and `arm` changed meaning in 0.4 and must say so out loud."""

    def _warnings(self, values: dict) -> list[str]:
        import anatomapa

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            anatomapa.heatmap(values)
        return [
            str(item.message)
            for item in caught
            if issubclass(item.category, DeprecationWarning)
        ]

    def test_leg_warns(self):
        messages = self._warnings({"leg": 5})
        self.assertEqual(len(messages), 1)
        self.assertIn("lower_leg", messages[0])

    def test_arm_warns(self):
        messages = self._warnings({"arm": 5})
        self.assertEqual(len(messages), 1)
        self.assertIn("upper_arm", messages[0])

    def test_lateralised_form_warns_too(self):
        self.assertEqual(len(self._warnings({"leg_left": 5})), 1)

    def test_warns_once_per_call(self):
        messages = self._warnings({"leg": 1, "leg_left": 2, "leg_right": 3})
        self.assertEqual(len(messages), 1)

    def test_new_ids_do_not_warn(self):
        self.assertEqual(self._warnings({"lower_leg": 5, "upper_arm": 2}), [])

    def test_unrelated_ids_do_not_warn(self):
        self.assertEqual(self._warnings({"upper_chest": 5, "hand": 2}), [])


if __name__ == "__main__":
    unittest.main()
