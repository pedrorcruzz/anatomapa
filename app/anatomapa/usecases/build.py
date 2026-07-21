from __future__ import annotations

from anatomapa.domain.colormap import ColorMap
from anatomapa.domain.heatmap import Heatmap
from anatomapa.domain.model import AnatomicalModel
from anatomapa.domain.scale import Scale


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
        Resultado imutável com mapeamento region_id -> RGB.
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

    # Ordem estável: ids canônicos do modelo
    ids = [rid for rid in model.ids() if rid in values]
    # Inclui ids com valores que não estão no modelo (serão ignorados na renderização)
    extra_ids = sorted(k for k in values if k not in model.ids())
    all_ids = ids + extra_ids

    raw_values = [values[rid] for rid in all_ids]
    normalized = scale.normalize(raw_values)

    colors: dict[str, tuple[int, int, int]] = {}
    for rid, t in zip(all_ids, normalized):
        colors[rid] = colormap.color_at(t)

    return Heatmap(
        colors=colors,
        scale_name=type(scale).__name__,
        value_min=min(raw_values),
        value_max=max(raw_values),
        lang=lang,
        title=title,
    )
