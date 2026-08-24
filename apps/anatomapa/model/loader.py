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
    """Return (canonical_id, side) where side is 'left', 'right' or 'center'."""
    for suffix in _BILATERAL_SUFFIXES:
        if element_id.endswith(suffix):
            return element_id[: -len(suffix)], suffix.lstrip("-")
    return element_id, "center"


def _parse_svg(path: str) -> dict[str, dict[str, str]]:
    """Parse the SVG file and extract region geometry grouped by canonical id.

    Returns
    -------
    dict[str, dict[str, str]]
        Mapping from canonical id to {side: path_d}, where side is
        'center', 'left' or 'right'.
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
    """Load and cache an AnatomicalModel for the given view and body.

    Parameters
    ----------
    view:
        Body view: "anterior" or "posterior".
    assets_dir:
        Directory holding the SVG files and regions.json. Defaults to assets/.
    body:
        Body type: "male" or "female".

    Returns
    -------
    AnatomicalModel
        Immutable model with the region geometry extracted from the SVG.

    Raises
    ------
    ValueError
        If body or view is unknown.
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
            bilateral=item.get("bilateral", False),
            parent=item.get("parent"),
            geometry=geom,
            area=item.get("area"),
            views=tuple(item.get("views", [])),
        )
        regions.append(region)

    return AnatomicalModel(_regions=tuple(regions))
