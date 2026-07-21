"""Testa que os ids de região nos SVGs estão sincronizados com regions.json.

Valida os 4 arquivos SVG (male/female × anterior/posterior).
Se os assets estiverem ausentes, os testes são ignorados.
"""

import json
import os
import unittest
import xml.etree.ElementTree as ET

_ASSETS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "anatomapa", "assets"
)
_REGIONS_JSON = os.path.join(_ASSETS_DIR, "regions.json")

_SVG_FILES = {
    "male_anterior": os.path.join(_ASSETS_DIR, "body_male_anterior.svg"),
    "male_posterior": os.path.join(_ASSETS_DIR, "body_male_posterior.svg"),
    "female_anterior": os.path.join(_ASSETS_DIR, "body_female_anterior.svg"),
    "female_posterior": os.path.join(_ASSETS_DIR, "body_female_posterior.svg"),
}

_ASSETS_EXIST = all(os.path.exists(p) for p in _SVG_FILES.values()) and os.path.exists(_REGIONS_JSON)

_BILATERAL_SUFFIXES = ("-left", "-right")


def _canonical_id(elem_id: str) -> str:
    for suffix in _BILATERAL_SUFFIXES:
        if elem_id.endswith(suffix):
            return elem_id[: -len(suffix)]
    return elem_id


def _extract_canonical_ids_from_svg(path: str) -> set[str]:
    tree = ET.parse(path)
    root = tree.getroot()

    def find_regions_group(root: ET.Element) -> ET.Element | None:
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag == "g" and elem.get("id") == "regions":
                return elem
        return None

    group = find_regions_group(root)
    if group is None:
        return set()

    ids = set()
    for elem in group:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "path":
            elem_id = elem.get("id", "")
            if elem_id:
                ids.add(_canonical_id(elem_id))
    return ids


def _load_json_ids() -> set[str]:
    with open(_REGIONS_JSON, encoding="utf-8") as fh:
        data = json.load(fh)
    return {item["id"] for item in data["regions"]}


@unittest.skipUnless(_ASSETS_EXIST, "Assets não encontrados -- pulando testes de sincronia")
class TestModelSync(unittest.TestCase):
    def _assert_svg_ids_match_json(self, svg_key: str) -> None:
        path = _SVG_FILES[svg_key]
        svg_ids = _extract_canonical_ids_from_svg(path)
        json_ids = _load_json_ids()
        self.assertEqual(
            svg_ids,
            json_ids,
            f"SVG {svg_key} diverge do regions.json.\n"
            f"Apenas no SVG: {svg_ids - json_ids}\n"
            f"Apenas no JSON: {json_ids - svg_ids}",
        )

    def test_male_anterior_svg_ids_match_json(self):
        self._assert_svg_ids_match_json("male_anterior")

    def test_male_posterior_svg_ids_match_json(self):
        self._assert_svg_ids_match_json("male_posterior")

    def test_female_anterior_svg_ids_match_json(self):
        self._assert_svg_ids_match_json("female_anterior")

    def test_female_posterior_svg_ids_match_json(self):
        self._assert_svg_ids_match_json("female_posterior")

    def test_json_has_required_fields(self):
        with open(_REGIONS_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
        required = {"id", "label_pt", "label_en", "bilateral"}
        for item in data["regions"]:
            missing = required - set(item.keys())
            self.assertEqual(
                missing,
                set(),
                f"Região {item.get('id', '?')} sem campos: {missing}",
            )

    def _assert_bilateral_have_both_sides(self, svg_key: str) -> None:
        with open(_REGIONS_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
        bilateral_ids = {item["id"] for item in data["regions"] if item.get("bilateral")}
        tree = ET.parse(_SVG_FILES[svg_key])
        root = tree.getroot()

        present_ids: set[str] = set()
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag == "path":
                elem_id = elem.get("id", "")
                present_ids.add(elem_id)

        for bid in bilateral_ids:
            self.assertIn(
                f"{bid}-left",
                present_ids,
                f"Região bilateral '{bid}' sem '{bid}-left' no SVG {svg_key}",
            )
            self.assertIn(
                f"{bid}-right",
                present_ids,
                f"Região bilateral '{bid}' sem '{bid}-right' no SVG {svg_key}",
            )

    def test_male_anterior_bilateral_have_both_sides(self):
        self._assert_bilateral_have_both_sides("male_anterior")

    def test_male_posterior_bilateral_have_both_sides(self):
        self._assert_bilateral_have_both_sides("male_posterior")

    def test_female_anterior_bilateral_have_both_sides(self):
        self._assert_bilateral_have_both_sides("female_anterior")

    def test_female_posterior_bilateral_have_both_sides(self):
        self._assert_bilateral_have_both_sides("female_posterior")

    def _assert_no_duplicate_ids(self, svg_key: str) -> None:
        tree = ET.parse(_SVG_FILES[svg_key])
        root = tree.getroot()
        all_ids = []
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag == "path":
                elem_id = elem.get("id", "")
                if elem_id:
                    all_ids.append(elem_id)
        self.assertEqual(
            len(all_ids),
            len(set(all_ids)),
            f"Ids duplicados no SVG {svg_key}: "
            f"{[i for i in all_ids if all_ids.count(i) > 1]}",
        )

    def test_no_duplicate_ids_male_anterior(self):
        self._assert_no_duplicate_ids("male_anterior")

    def test_no_duplicate_ids_male_posterior(self):
        self._assert_no_duplicate_ids("male_posterior")

    def test_no_duplicate_ids_female_anterior(self):
        self._assert_no_duplicate_ids("female_anterior")

    def test_no_duplicate_ids_female_posterior(self):
        self._assert_no_duplicate_ids("female_posterior")

    def _assert_silhouette_present(self, svg_key: str) -> None:
        tree = ET.parse(_SVG_FILES[svg_key])
        root = tree.getroot()
        found = False
        for elem in root.iter():
            if elem.get("id") == "body-outline":
                found = True
                break
        self.assertTrue(found, f"body-outline ausente no SVG {svg_key}")

    def test_silhouette_present_male_anterior(self):
        self._assert_silhouette_present("male_anterior")

    def test_silhouette_present_male_posterior(self):
        self._assert_silhouette_present("male_posterior")

    def test_silhouette_present_female_anterior(self):
        self._assert_silhouette_present("female_anterior")

    def test_silhouette_present_female_posterior(self):
        self._assert_silhouette_present("female_posterior")


if __name__ == "__main__":
    unittest.main()
