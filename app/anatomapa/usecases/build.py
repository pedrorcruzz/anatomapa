from __future__ import annotations

from anatomapa.domain.colormap import ColorMap
from anatomapa.domain.heatmap import Heatmap
from anatomapa.domain.model import AnatomicalModel
from anatomapa.domain.region import Region
from anatomapa.domain.scale import Scale


def _nearest_ancestor_value(
    region: Region, model: AnatomicalModel, values: dict[str, float]
) -> float | None:
    """Percorre a cadeia `parent` a partir de `region` e devolve o valor do
    ancestral mais próximo presente em `values`, ou None se nenhum tiver valor."""
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
    """Expande valores por herança pai->filhos (rollup).

    Toda região com geometria (tem path no SVG desta vista) que não recebeu
    valor próprio herda o valor do ancestral mais próximo, na cadeia `parent`,
    que tiver valor em `values`. Regiões agregadoras sem geometria (ex.:
    "trunk") não recebem cor própria, mas seu valor guia os filhos.
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
    """Constrói um Heatmap mapeando valores de regiões para cores.

    Parameters
    ----------
    values:
        Mapeamento do id canônico da região para valor numérico.
    model:
        Modelo anatômico com metadados das regiões.
    colormap:
        ColorMap usado para interpolação RGB.
    scale:
        Estratégia de escala para normalizar valores para [0, 1].
    lang:
        Idioma dos rótulos.
    title:
        Título opcional da figura.

    Returns
    -------
    Heatmap
        Resultado imutável com mapeamento region_id -> RGB. Regiões com
        geometria sem valor próprio herdam o valor do ancestral mais próximo
        (rollup pai->filhos); value_min/value_max refletem só os valores reais
        de entrada, sem o rollup.
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
