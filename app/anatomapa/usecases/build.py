from __future__ import annotations

from anatomapa.domain.colormap import ColorMap
from anatomapa.domain.heatmap import Heatmap
from anatomapa.domain.model import AnatomicalModel
from anatomapa.domain.region import Region
from anatomapa.domain.scale import Scale


def _nearest_ancestor_value(
    region: Region, model: AnatomicalModel, values: dict[str, float]
) -> float | None:
    """Walk the `parent` chain from `region` and return the value of the
    nearest ancestor present in `values`, or None when none has a value."""
    parent_id = region.parent
    while parent_id is not None:
        if parent_id in values:
            return values[parent_id]
        parent_region = model.get(parent_id)
        parent_id = parent_region.parent if parent_region else None
    return None


def _rollup_values(
    values: dict[str, float], model: AnatomicalModel
) -> dict[str, float]:
    """Expand values through parent->child inheritance (rollup).

    Every region with geometry (a path in this view's SVG) that received no
    value of its own inherits the value of the nearest ancestor in the
    `parent` chain that has one in `values`. Aggregating regions with no
    geometry (such as "trunk") get no colour of their own, but their value
    still drives their children.
    """
    expanded = dict(values)
    for region in model.regions():
        if region.id in values:
            continue
        if not region.geometry:
            continue
        inherited = _nearest_ancestor_value(region, model, values)
        if inherited is not None:
            expanded[region.id] = inherited
    return expanded


def build_heatmap(
    values: dict[str, float],
    model: AnatomicalModel,
    colormap: ColorMap,
    scale: Scale,
    lang: str = "pt",
    title: str | None = None,
) -> Heatmap:
    """Build a Heatmap by mapping region values to colours.

    Parameters
    ----------
    values:
        Mapping of canonical region id to numeric value.
    model:
        Anatomical model carrying the region metadata.
    colormap:
        ColorMap used for RGB interpolation.
    scale:
        Scaling strategy that normalises values into [0, 1].
    lang:
        Language of the labels.
    title:
        Optional figure title.

    Returns
    -------
    Heatmap
        Immutable result mapping region_id -> RGB. Regions with geometry but
        no value of their own inherit the nearest ancestor's value (parent->
        child rollup); value_min/value_max reflect only the real input values,
        without the rollup.
    """
    if not values:
        return Heatmap(
            colors={},
            scale_name=type(scale).__name__,
            value_min=0.0,
            value_max=0.0,
            lang=lang,
            title=title,
        )

    expanded_values = _rollup_values(values, model)

    # Ordem estável: ids canônicos do modelo
    ids = [rid for rid in model.ids() if rid in expanded_values]
    # Inclui ids com valores que não estão no modelo (serão ignorados na renderização)
    extra_ids = sorted(k for k in values if k not in model.ids())
    all_ids = ids + extra_ids

    raw_values_for_color = [expanded_values[rid] for rid in ids] + [
        values[rid] for rid in extra_ids
    ]
    normalized = scale.normalize(raw_values_for_color)

    colors: dict[str, tuple[int, int, int]] = {}
    for rid, t in zip(all_ids, normalized):
        colors[rid] = colormap.color_at(t)

    input_values = list(values.values())
    return Heatmap(
        colors=colors,
        scale_name=type(scale).__name__,
        value_min=min(input_values),
        value_max=max(input_values),
        lang=lang,
        title=title,
    )
