"""anatomapa - Biblioteca Python para geração de mapas de calor anatômicos da superfície corporal."""

from __future__ import annotations

import os

from anatomapa.color.registry import get_colormap, get_scale
from anatomapa.domain.heatmap import Heatmap
from anatomapa.model import loader as _loader
from anatomapa.readers.csv_reader import from_csv
from anatomapa.readers.json_reader import from_json
from anatomapa.readers.native import from_dict, from_records
from anatomapa.readers.xlsx_reader import from_xlsx
from anatomapa.render.base import Figure
from anatomapa.render.svg import SvgRenderer
from anatomapa.resolver.resolver import ResolutionError, resolve
from anatomapa.usecases.build import build_heatmap as _build_heatmap

__version__ = "0.1.0"
__all__ = [
    "heatmap",
    "from_csv",
    "from_json",
    "from_dict",
    "from_records",
    "from_xlsx",
    "list_regions",
    "Figure",
    "Heatmap",
    "ResolutionError",
]

_renderer = SvgRenderer()


def heatmap(
    values: dict[str, float | int],
    view: str = "anterior",
    body: str = "male",
    cmap: str = "reds",
    scale: str = "linear",
    lang: str = "pt",
    title: str | None = None,
    smooth: bool = False,
    legend: bool = False,
    region_map: dict[str, str] | None = None,
    assets_dir: str | None = None,
) -> Figure:
    """Gera uma figura de mapa de calor anatômico.

    Parameters
    ----------
    values:
        Mapeamento de rótulo de região (PT, EN, id canônico ou alias) para valor numérico.
    view:
        Vista do corpo a renderizar: "anterior" (frente) ou "posterior" (costas).
    body:
        Tipo de corpo: "male" (masculino) ou "female" (feminino).
    cmap:
        Nome do colormap: "reds", "heat", "viridis", "blues", "greens", "thermal".
    scale:
        Estratégia de escala: "linear" ou "log".
    lang:
        Idioma dos rótulos de região na figura: "pt" ou "en".
    title:
        Título opcional a embutir no SVG e na legenda.
    smooth:
        Se True, aplica degradê térmico contínuo com feGaussianBlur em vez de cores chapadas.
    legend:
        Se True, insere barra de cores com rótulos de intensidade (mínimo e máximo) na figura.
    region_map:
        Mapeamento opcional do usuário de rótulo customizado para id canônico.
    assets_dir:
        Substitui o caminho do diretório de assets (arquivos SVG + regions.json).

    Returns
    -------
    Figure
        Objeto Figure com suporte a .save(), .to_svg() e str().

    Raises
    ------
    ResolutionError
        Se algum rótulo em values não puder ser resolvido para um id de região conhecido.
    ValueError
        Se os nomes de view, body, cmap ou scale forem desconhecidos.
    """
    model = _loader.load(view, assets_dir, body)

    label_list = list(values.keys())
    resolved = resolve(label_list, model, region_map)

    canonical_values: dict[str, float] = {
        resolved[label]: float(val)
        for label, val in values.items()
    }

    colormap = get_colormap(cmap)
    scale_obj = get_scale(scale)

    heat = _build_heatmap(
        values=canonical_values,
        model=model,
        colormap=colormap,
        scale=scale_obj,
        lang=lang,
        title=title,
    )

    # Carrega o SVG base para o modo onto-svg (smooth ou não)
    base = assets_dir or _loader._ASSETS_DIR
    svg_path = os.path.join(base, f"body_{body}_{view}.svg")
    with open(svg_path, encoding="utf-8") as fh:
        base_svg = fh.read()

    return _renderer.render(
        heat,
        model,
        lang=lang,
        base_svg=base_svg,
        smooth=smooth,
        legend=legend,
        colormap=colormap,
    )


def list_regions(
    view: str = "anterior",
    lang: str = "pt",
    body: str = "male",
    assets_dir: str | None = None,
) -> list[dict[str, str | bool | None]]:
    """Lista todas as regiões anatômicas para a vista informada.

    Parameters
    ----------
    view:
        Vista do corpo: "anterior" ou "posterior".
    lang:
        Idioma do campo label: "pt" ou "en".
    body:
        Tipo de corpo: "male" ou "female".
    assets_dir:
        Substitui o caminho do diretório de assets.

    Returns
    -------
    list[dict]
        Lista ordenada de dicts com as chaves: id, label, bilateral, parent.
    """
    model = _loader.load(view, assets_dir, body)
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
