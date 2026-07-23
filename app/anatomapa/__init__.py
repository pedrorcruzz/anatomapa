"""anatomapa - Biblioteca Python para geração de mapas de calor anatômicos da superfície corporal."""

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
from anatomapa.render.base import Figure
from anatomapa.render.svg import SvgRenderer
from anatomapa.resolver.resolver import ResolutionError, analyze, resolve
from anatomapa.usecases.build import build_heatmap as _build_heatmap

__version__ = "0.1.0"
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
    "Figure",
    "Heatmap",
    "ResolutionError",
]

_VALID_ON_UNKNOWN = ("error", "skip", "warn")


def _as_dict(values) -> dict:
    """Aceita dict ou iterável de pares (região, valor) e devolve sempre um dict."""
    if isinstance(values, dict):
        return values
    return dict(values)

_renderer = SvgRenderer()


def heatmap(
    values,
    view: str = "anterior",
    body: str = "male",
    cmap: str = "reds",
    scale: str = "linear",
    lang: str = "pt",
    title: str | None = None,
    smooth: bool = False,
    legend: bool = False,
    on_unknown: str = "error",
    region_map: dict[str, str] | None = None,
    assets_dir: str | None = None,
) -> Figure:
    """Gera uma figura de mapa de calor anatômico.

    Parameters
    ----------
    values:
        Mapeamento rótulo de região -> valor. Aceita nomes em PT ou EN, com acento,
        plural e lado ("mão direita", "left hand"). Também aceita um iterável de pares
        (região, valor), como o que os leitores from_csv/from_json/from_records devolvem.
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
    on_unknown:
        Política para rótulos não reconhecidos: "error" (padrão, levanta
        ResolutionError listando todos), "skip" (ignora em silêncio) ou "warn"
        (ignora emitindo um aviso).
    region_map:
        De-para do usuário: rótulo próprio -> id de região. Aceita ids canônicos
        ("hand") e lateralizados ("hand_left", "hand_right").
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
    if on_unknown not in _VALID_ON_UNKNOWN:
        raise ValueError(
            f"on_unknown inválido: {on_unknown!r}. Use um de {list(_VALID_ON_UNKNOWN)}."
        )

    values = _as_dict(values)
    model = _loader.load(view, assets_dir, body)

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


def validate(
    values,
    view: str = "anterior",
    body: str = "male",
    region_map: dict[str, str] | None = None,
    assets_dir: str | None = None,
) -> dict[str, dict]:
    """Confere (dry-run) quais rótulos seriam reconhecidos, SEM renderizar.

    Útil para validar uma planilha antes de gerar o mapa: mostra o que cada
    rótulo vira e quais não foram reconhecidos (com sugestões).

    Parameters
    ----------
    values:
        dict {rótulo: valor} ou iterável de pares (região, valor); os valores
        são ignorados aqui, importa apenas as chaves/rótulos.
    view, body:
        Vista e corpo usados para carregar as regiões válidas.
    region_map:
        De-para do usuário (mesmo formato do heatmap).
    assets_dir:
        Substitui o diretório de assets.

    Returns
    -------
    dict
        {"resolved": {rótulo: region_key}, "unresolved": {rótulo: {"reason", "suggestions"}}}.
    """
    values = _as_dict(values)
    model = _loader.load(view, assets_dir, body)
    return analyze(list(values.keys()), model, region_map)


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
