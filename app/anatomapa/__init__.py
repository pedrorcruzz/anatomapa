"""anatomapa - Python library to generate anatomical heatmaps of the human body surface."""

from __future__ import annotations

import os
import warnings

from anatomapa.color.registry import get_colormap, get_scale
from anatomapa.domain.heatmap import Heatmap
from anatomapa.model import loader as _loader
from anatomapa.readers.csv_reader import from_csv
from anatomapa.readers.json_reader import from_json
from anatomapa.readers.native import from_dict, from_records
from anatomapa.readers.xlsx_reader import from_xlsx
from anatomapa.regions import Region
from anatomapa.render.base import Figure
from anatomapa.render.svg import SvgRenderer
from anatomapa.resolver.resolver import ResolutionError, analyze, resolve
from anatomapa.usecases.build import build_heatmap as _build_heatmap

__version__ = "0.1.1"
__all__ = [
    "heatmap",
    "validate",
    "from_csv",
    "from_json",
    "from_dict",
    "from_records",
    "from_xlsx",
    "list_regions",
    "resolve",
    "Region",
    "Figure",
    "Heatmap",
    "ResolutionError",
]

_VALID_ON_UNKNOWN = ("error", "skip", "warn")
_VALID_FORMATS = ("svg", "png", "jpg", "jpeg")
_VIEW = "anterior"


def _as_dict(values) -> dict:
    """Aceita dict ou iterável de pares (região, valor) e devolve sempre um dict."""
    if isinstance(values, dict):
        return values
    return dict(values)

_renderer = SvgRenderer()


def heatmap(
    values,
    body: str = "male",
    lang: str = "pt",
    format: str = "svg",
    title: str | None = None,
    background: str = "transparent",
    on_unknown: str = "error",
    region_map: dict[str, str] | None = None,
) -> Figure:
    """Generate an anatomical heatmap figure.

    Parameters
    ----------
    values:
        Mapping of region label -> value. Labels may be given in Portuguese or
        English, with accents, plural forms and side ("mão direita", "left hand").
        An iterable of (region, value) pairs is also accepted, such as the output
        of the from_csv/from_json/from_records readers.
    body:
        Body type: "male" or "female".
    lang:
        Language of the region labels drawn on the figure: "pt" or "en".
    format:
        Output format: "svg" (default), "png", "jpg" or "jpeg". PNG and JPEG are
        rasterised when the figure is saved and require the optional "raster"
        extra (pip install anatomapa[raster]).
    title:
        Optional title embedded in the SVG and in the legend.
    background:
        Figure background: "dark", "light" or "transparent" (default, no background
        rectangle). Legend text colors adapt to the chosen background.
    on_unknown:
        Policy for unrecognised labels: "error" (default, raises ResolutionError
        listing them all), "skip" (silently ignores) or "warn" (ignores with a
        warning).
    region_map:
        User mapping: custom label -> region id. Accepts canonical ids ("hand")
        and lateralised ids ("hand_left", "hand_right").

    Returns
    -------
    Figure
        A Figure object supporting .save(), .to_svg() and str().

    Raises
    ------
    ResolutionError
        If a label in values cannot be resolved to a known region id.
    ValueError
        If body, format or background is unknown.
    """
    if on_unknown not in _VALID_ON_UNKNOWN:
        raise ValueError(
            f"on_unknown inválido: {on_unknown!r}. Use um de {list(_VALID_ON_UNKNOWN)}."
        )

    fmt = format.lower()
    if fmt not in _VALID_FORMATS:
        raise ValueError(
            f"format inválido: {format!r}. Use um de {list(_VALID_FORMATS)}."
        )

    values = _as_dict(values)
    model = _loader.load(_VIEW, None, body)

    label_list = list(values.keys())
    resolved = resolve(label_list, model, region_map, strict=(on_unknown == "error"))

    if on_unknown == "warn":
        dropped = [lab for lab in label_list if lab not in resolved]
        if dropped:
            warnings.warn(
                f"Rótulos não reconhecidos foram ignorados: {dropped}",
                stacklevel=2,
            )

    # Apenas rótulos resolvidos entram; regiões repetidas mantêm o último valor
    canonical_values: dict[str, float] = {}
    for label, val in values.items():
        region_key = resolved.get(label)
        if region_key is not None:
            canonical_values[region_key] = float(val)

    colormap = get_colormap("thermal")
    scale_obj = get_scale("linear")

    heat = _build_heatmap(
        values=canonical_values,
        model=model,
        colormap=colormap,
        scale=scale_obj,
        lang=lang,
        title=title,
    )

    # Carrega o SVG base para o modo onto-svg
    base = _loader._ASSETS_DIR
    svg_path = os.path.join(base, f"body_{body}_{_VIEW}.svg")
    with open(svg_path, encoding="utf-8") as fh:
        base_svg = fh.read()

    figure = _renderer.render(
        heat,
        model,
        lang=lang,
        base_svg=base_svg,
        smooth=True,
        legend=True,
        colormap=colormap,
        background=background,
        missing="neutral",
    )
    return Figure(figure.to_svg(), format=fmt)


def validate(
    values,
    body: str = "male",
    region_map: dict[str, str] | None = None,
) -> dict[str, dict]:
    """Dry-run check of which labels would be recognised, WITHOUT rendering.

    Useful to validate a spreadsheet before generating the map: shows what each
    label maps to and which ones were not recognised (with suggestions).

    Parameters
    ----------
    values:
        dict {label: value} or iterable of (region, value) pairs; the values are
        ignored here, only the keys/labels matter.
    body:
        Body type used to load the valid regions.
    region_map:
        User mapping (same format as heatmap).

    Returns
    -------
    dict
        {"resolved": {label: region_key}, "unresolved": {label: {"reason", "suggestions"}}}.
    """
    values = _as_dict(values)
    model = _loader.load(_VIEW, None, body)
    return analyze(list(values.keys()), model, region_map)


def list_regions(
    lang: str = "pt",
    body: str = "male",
) -> list[dict[str, str | bool | None]]:
    """List all anatomical regions for the front (anterior) view.

    Parameters
    ----------
    lang:
        Language of the label field: "pt" or "en".
    body:
        Body type: "male" or "female".

    Returns
    -------
    list[dict]
        Ordered list of dicts with keys: id, label, bilateral, parent.
    """
    model = _loader.load(_VIEW, None, body)
    result = []
    for region in model.regions():
        label = region.label_pt if lang == "pt" else region.label_en
        result.append({
            "id": region.id,
            "label": label,
            "bilateral": region.bilateral,
            "parent": region.parent,
        })
    return result
