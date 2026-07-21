from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from functools import lru_cache

from anatomapa.domain.model import AnatomicalModel
from anatomapa.domain.region import Region
from anatomapa.model.metadata import load_metadata

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
_SVG_NS = "http://www.w3.org/2000/svg"

_BILATERAL_SUFFIXES = ("-left", "-right")
_VALID_BODIES = ("male", "female")
_VALID_VIEWS = ("anterior", "posterior")


def _strip_suffix(element_id: str) -> tuple[str, str]:
    """Retorna (canonical_id, side) onde side é 'left', 'right' ou 'center'."""
    for suffix in _BILATERAL_SUFFIXES:
        if element_id.endswith(suffix):
            return element_id[: -len(suffix)], suffix.lstrip("-")
    return element_id, "center"


def _parse_svg(path: str) -> dict[str, dict[str, str]]:
    """Parseia o arquivo SVG e extrai a geometria das regiões agrupada por id canônico.

    Returns
    -------
    dict[str, dict[str, str]]
        Mapeamento do id canônico para {side: path_d}, onde side é
        'center', 'left' ou 'right'.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    def find_regions_group(root: ET.Element) -> ET.Element | None:
        for g in root.iter():
            tag = g.tag.split("}")[-1] if "}" in g.tag else g.tag
            if tag == "g" and g.get("id") == "regions":
                return g
        return None

    regions_group = find_regions_group(root)
    if regions_group is None:
        raise ValueError(f"No <g id='regions'> found in {path}")

    geometry: dict[str, dict[str, str]] = {}
    for elem in regions_group:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag != "path":
            continue
        elem_id = elem.get("id", "")
        if not elem_id:
            continue
        path_d = elem.get("d", "")
        canonical_id, side = _strip_suffix(elem_id)
        if canonical_id not in geometry:
            geometry[canonical_id] = {}
        geometry[canonical_id][side] = path_d

    return geometry


@lru_cache(maxsize=8)
def load(
    view: str,
    assets_dir: str | None = None,
    body: str = "male",
) -> AnatomicalModel:
    """Carrega e armazena em cache um AnatomicalModel para a vista e corpo informados.

    Parameters
    ----------
    view:
        Vista do corpo: "anterior" ou "posterior".
    assets_dir:
        Diretório contendo os arquivos SVG e regions.json. Padrão: assets/.
    body:
        Tipo de corpo: "male" ou "female".

    Returns
    -------
    AnatomicalModel
        Modelo imutável com a geometria das regiões extraída do SVG.

    Raises
    ------
    ValueError
        Se body ou view forem desconhecidos.
    """
    if body not in _VALID_BODIES:
        raise ValueError(
            f"Unknown body {body!r}. Available: {list(_VALID_BODIES)}"
        )
    if view not in _VALID_VIEWS:
        raise ValueError(
            f"Unknown view {view!r}. Available: {list(_VALID_VIEWS)}"
        )

    base = assets_dir or _ASSETS_DIR
    svg_path = os.path.join(base, f"body_{body}_{view}.svg")
    geometry = _parse_svg(svg_path)
    metadata_list = load_metadata(base)

    regions: list[Region] = []
    # Ordem estável: ids canônicos conforme o JSON de metadados
    for item in metadata_list:
        rid = item["id"]
        geom = geometry.get(rid, {})
        region = Region(
            id=rid,
            label_pt=item["label_pt"],
            label_en=item["label_en"],
            aliases=tuple(item.get("aliases", [])),
            bilateral=item.get("bilateral", False),
            parent=item.get("parent"),
            geometry=geom,
            area=item.get("area"),
        )
        regions.append(region)

    return AnatomicalModel(_regions=tuple(regions))
