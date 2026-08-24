from __future__ import annotations

from anatomapa.domain.colormap import ColorMap
from anatomapa.domain.heatmap import Heatmap
from anatomapa.domain.model import AnatomicalModel
from anatomapa.domain.region import Region
from anatomapa.domain.scale import Scale

_SIDES = ("left", "right")


def _source_key(
    region: Region,
    side: str | None,
    model: AnatomicalModel,
    values: dict[str, float],
) -> str | None:
    """Find which input key colours one region on one side.

    Walks the `parent` chain from the region upwards and stops at the first
    ancestor that carries a value. On each step the lateralised key wins over
    the plain one, so `{"leg": 3, "leg_left": 9}` paints the left leg with 9 and
    the right one with 3. A deeper region always wins over a shallower ancestor,
    so in `{"leg_left": 10, "foot": 2}` the left foot is 2.

    Parameters
    ----------
    region:
        Region being painted.
    side:
        "left", "right", or None for a central region.
    model:
        Model used to walk the parent chain.
    values:
        Input values keyed by region id or lateralised region id.

    Returns
    -------
    str | None
        The winning key of `values`, or None when nothing applies.
    """
    node: Region | None = region
    while node is not None:
        if side is not None:
            lateralised = f"{node.id}_{side}"
            if lateralised in values:
                return lateralised
        if node.id in values:
            return node.id
        node = model.get(node.parent) if node.parent else None
    return None


def _paint_plan(
    model: AnatomicalModel, values: dict[str, float]
) -> dict[str, str]:
    """Map each drawable path of this view to the input key that colours it.

    The key follows what the renderer looks up: `chest_left` for the path
    `chest-left`, and the plain id for a central region. When both sides of a
    region end up with the same value the plain id is emitted once instead of
    two identical lateralised entries, so a symmetric heatmap keeps reading as
    `colors["chest"]`.
    """
    plan: dict[str, str] = {}
    for region in model.regions():
        per_side: dict[str, str] = {}
        for side in region.geometry:
            lookup_side = None if side == "center" else side
            source = _source_key(region, lookup_side, model, values)
            if source is not None:
                per_side[side] = source
        if not per_side:
            continue
        # Simétrica quando todo lado desenhado recebeu o MESMO valor; a forma
        # do resultado depende do que é pintado, não de como foi escrito
        sides = set(region.geometry)
        painted = {values[source] for source in per_side.values()}
        symmetric = sides == set(per_side) and len(painted) == 1
        if symmetric:
            plan[region.id] = next(iter(per_side.values()))
            continue
        for side, source in per_side.items():
            plan[region.id if side == "center" else f"{region.id}_{side}"] = source
    return plan


def _scale_sources(
    model: AnatomicalModel, values: dict[str, float]
) -> set[str]:
    """Input keys that end up colouring something, in any view.

    Drives the legend range. A region that only aggregates (`trunk`) has no
    drawing of its own, so its value counts only while some descendant is
    actually inheriting it. Regions drawn on the other view count too, so both
    panels of `view="both"` share one scale.
    """
    sources: set[str] = set()
    for region in model.regions():
        if not region.views:
            continue
        sides = _SIDES if region.bilateral else (None,)
        for side in sides:
            source = _source_key(region, side, model, values)
            if source is not None:
                sources.add(source)
    return sources


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
        Mapping of region id, or lateralised region id, to numeric value.
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
        Immutable result mapping paint key -> RGB. Regions with no value of
        their own inherit the nearest ancestor that has one, side by side;
        value_min/value_max cover only the values that actually paint.
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

    plan = _paint_plan(model, values)
    sources = _scale_sources(model, values) | set(plan.values())
    if not sources:
        return Heatmap(
            colors={},
            scale_name=type(scale).__name__,
            value_min=0.0,
            value_max=0.0,
            lang=lang,
            title=title,
        )

    # Normaliza os valores distintos: a escala é função só do valor e do
    # intervalo, então basta uma consulta por valor
    distinct = sorted({values[key] for key in sources})
    normalized = scale.normalize(distinct)
    by_value = dict(zip(distinct, normalized))

    # Ordem estável: ids canônicos do modelo, cada um com os lados em ordem
    colors: dict[str, tuple[int, int, int]] = {}
    for key in sorted(plan, key=_paint_order(model)):
        colors[key] = colormap.color_at(by_value[values[plan[key]]])

    return Heatmap(
        colors=colors,
        scale_name=type(scale).__name__,
        value_min=distinct[0],
        value_max=distinct[-1],
        lang=lang,
        title=title,
    )


def _paint_order(model: AnatomicalModel):
    """Sort key that keeps the colour dict in the model's own region order."""
    rank = {rid: index for index, rid in enumerate(model.ids())}

    def key(paint_key: str) -> tuple[int, str]:
        base, separator, side = paint_key.rpartition("_")
        if separator and side in _SIDES and base in rank:
            return (rank[base], side)
        return (rank.get(paint_key, len(rank)), "")

    return key
