"""anatomapa - Python library to generate anatomical heatmaps of the human body surface."""

from __future__ import annotations

import os
import warnings
from collections.abc import Mapping
from dataclasses import replace
from typing import Literal, overload

from anatomapa.color.registry import get_colormap, get_scale
from anatomapa.domain.heatmap import Heatmap
from anatomapa.model import loader as _loader
from anatomapa.readers.csv_reader import from_csv
from anatomapa.readers.json_reader import from_json
from anatomapa.readers.native import from_dict, from_records
from anatomapa.readers.xlsx_reader import from_xlsx
from anatomapa.regions import Region
from anatomapa.render.base import Figure
from anatomapa.render.svg import SvgRenderer, compose_views as _compose_views
from anatomapa.resolver.resolver import ResolutionError, analyze, resolve
from anatomapa.usecases.build import build_heatmap as _build_heatmap

__version__ = "0.3.6"
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
_VALID_VIEWS = ("anterior", "posterior", "both")
_VIEW = "anterior"


def _views_of(view: str) -> tuple[str, ...]:
    """Views to draw: "both" expands into the two, front first and back second."""
    return ("anterior", "posterior") if view == "both" else (view,)


def _as_dict(values) -> dict:
    """Accept a dict or an iterable of (region, value) pairs, always returning a dict."""
    if isinstance(values, dict):
        return values
    return dict(values)

_renderer = SvgRenderer()


@overload
def heatmap(
    values,
    view: str = ...,
    body: str = ...,
    lang: str = ...,
    format: str = ...,
    title: str | None = ...,
    background: str = ...,
    on_unknown: str = ...,
    region_map: Mapping[str, str] | None = ...,
    split: Literal[False] = False,
) -> Figure: ...


@overload
def heatmap(
    values,
    view: str = ...,
    body: str = ...,
    lang: str = ...,
    format: str = ...,
    title: str | None = ...,
    background: str = ...,
    on_unknown: str = ...,
    region_map: Mapping[str, str] | None = ...,
    split: Literal[True] = ...,
) -> tuple[Figure, Figure]: ...


# Fallback para quem passa uma variável bool, cujo valor o checker não conhece
@overload
def heatmap(
    values,
    view: str = ...,
    body: str = ...,
    lang: str = ...,
    format: str = ...,
    title: str | None = ...,
    background: str = ...,
    on_unknown: str = ...,
    region_map: Mapping[str, str] | None = ...,
    split: bool = ...,
) -> Figure | tuple[Figure, Figure]: ...


def heatmap(
    values,
    view: str = "anterior",
    body: str = "male",
    lang: str = "pt",
    format: str = "svg",
    title: str | None = None,
    background: str = "transparent",
    on_unknown: str = "error",
    region_map: Mapping[str, str] | None = None,
    split: bool = False,
) -> Figure | tuple[Figure, Figure]:
    """Generate an anatomical heatmap figure.

    Parameters
    ----------
    values:
        Mapping of region label -> value. A label must be a region id written
        exactly as defined ("hand", "hand_left"), a Region enum member, or a
        key of region_map. Names are never guessed, so a spreadsheet label such
        as "MÃO" has to be mapped through region_map. An iterable of
        (region, value) pairs is also accepted, such as the output of the
        from_csv/from_json/from_records readers.
    view:
        Body view: "anterior" (front, default), "posterior" (back) or "both",
        which draws the two side by side in a single figure sharing one colour
        scale and one legend. Trunk regions differ per view: the front exposes
        chest, abdomen and pelvis; the back exposes back and buttocks. A value
        on "trunk" fills whichever of them belongs to the view being drawn.
    body:
        Body type: "male" or "female".
    lang:
        Language of the region labels drawn on the figure: "pt" or "en".
    format:
        Output format: "svg" (default), "png", "jpg" or "jpeg". PNG and JPEG are
        rasterised when the figure is saved and require the optional "raster"
        extra (pip install anatomapa[raster]). Raster output uses per-region
        gradients that blend into the neighbouring regions, so the thermal
        look is preserved without SVG filters, which raster converters do not
        implement; the colours and the legend are the same. Saving an "svg"
        figure to a .png/.jpg path rasterises that very variant, so this
        parameter only picks the default format when the path has no extension.
    title:
        Optional figure title. When given, it is drawn in a band above the
        drawing and embedded as the SVG <title> element. Omitted by default,
        and then nothing is drawn and the layout stays unchanged.
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
    split:
        Only for view="both". When False (default) the two views share one
        figure, side by side with a single legend. When True, returns a tuple
        (anterior, posterior) of two independent figures, each with its own
        legend, sharing the same colour scale.

    Returns
    -------
    Figure or tuple[Figure, Figure]
        A Figure supporting .save(), .to_svg() and str(); with view="both"
        and split=True, the pair (anterior, posterior) of such figures.

    Raises
    ------
    ResolutionError
        If a label in values cannot be resolved to a known region id.
    ValueError
        If view, body, format or background is unknown, or if split=True is
        used with a view other than "both".
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

    if view not in _VALID_VIEWS:
        raise ValueError(
            f"view inválida: {view!r}. Use uma de {list(_VALID_VIEWS)}."
        )

    if split and view != "both":
        raise ValueError('split=True só vale para view="both".')

    values = _as_dict(values)
    views = _views_of(view)
    model = _loader.load(views[0], None, body)

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
    base = _loader._ASSETS_DIR

    # O degradê térmico é feito com filtro SVG, que os conversores raster não
    # implementam: rasterizar essa versão devolveria o corpo branco. Para
    # PNG/JPG a figura sai em degradê chapado, com as mesmas cores.
    smooth = fmt == "svg"

    def _render_one(
        view_name: str,
        with_legend: bool,
        panel_background: str,
        panel_title: str | None,
        panel_smooth: bool,
    ):
        """Render a single view. Each view loads its own model, as the regions differ."""
        view_model = _loader.load(view_name, None, body)
        heat = _build_heatmap(
            values=canonical_values,
            model=view_model,
            colormap=colormap,
            scale=scale_obj,
            lang=lang,
            title=panel_title,
        )
        svg_path = os.path.join(base, f"body_{body}_{view_name}.svg")
        with open(svg_path, encoding="utf-8") as fh:
            base_svg = fh.read()
        figure = _renderer.render(
            heat,
            view_model,
            lang=lang,
            base_svg=base_svg,
            smooth=panel_smooth,
            legend=with_legend,
            colormap=colormap,
            background=panel_background,
            missing="neutral",
        )
        return heat, figure.to_svg()

    def _render_all(panel_smooth: bool) -> str | tuple[str, str]:
        """Render every SVG of this call: one string, or the pair when split."""
        if len(views) == 1:
            return _render_one(views[0], True, background, title, panel_smooth)[1]

        # "both" com split: duas figuras independentes, cada uma com a própria
        # legenda; a escala é a mesma porque os valores são os mesmos
        if split:
            return tuple(
                _render_one(view_name, True, background, title, panel_smooth)[1]
                for view_name in views
            )

        # "both": painéis sem legenda, fundo nem título próprios, compostos lado
        # a lado com uma legenda só
        panels = []
        shared_heat = None
        for view_name in views:
            heat, svg = _render_one(view_name, False, "transparent", None, panel_smooth)
            shared_heat = shared_heat or replace(heat, title=title)
            panels.append((f"{view_name}-", svg))
        return _compose_views(
            panels,
            shared_heat,
            colormap,
            legend=True,
            lang=lang,
            background=background,
        )

    # A versão chapada só é montada se alguém pedir raster, e uma vez só
    flat_cache: list = []

    def _flat_all():
        if not flat_cache:
            flat_cache.append(_render_all(False))
        return flat_cache[0]

    rendered = _render_all(smooth)

    if split:
        return tuple(
            Figure(
                rendered[index],
                format=fmt,
                raster_svg=(lambda i=index: _flat_all()[i]) if smooth else None,
            )
            for index in range(2)
        )

    return Figure(
        rendered,
        format=fmt,
        raster_svg=_flat_all if smooth else None,
    )


def validate(
    values,
    body: str = "male",
    region_map: Mapping[str, str] | None = None,
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
    view: str | None = None,
) -> list[dict]:
    """List the anatomical regions that can be used as input.

    Parameters
    ----------
    lang:
        Language of the label field: "pt" or "en".
    body:
        Body type: "male" or "female".
    view:
        Restrict the listing to the regions drawn in one view: "anterior" or
        "posterior". None (default) lists every region of both views.

    Returns
    -------
    list[dict]
        Ordered list of dicts with keys: id, label, bilateral, parent, views.
        The "views" field tells where the region is drawn; an empty tuple marks
        an aggregating region such as "trunk", which has no drawing of its own
        but fills its children through the rollup.
    """
    if view is not None and view not in ("anterior", "posterior"):
        raise ValueError(
            "view inválida: use 'anterior', 'posterior' ou None."
        )
    model = _loader.load(view or _VIEW, None, body)
    result = []
    for region in model.regions():
        # Agregadoras (views vazio) valem em qualquer vista via rollup
        if view is not None and region.views and view not in region.views:
            continue
        label = region.label_pt if lang == "pt" else region.label_en
        result.append({
            "id": region.id,
            "label": label,
            "bilateral": region.bilateral,
            "parent": region.parent,
            "views": list(region.views),
        })
    return result
