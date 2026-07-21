from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Heatmap:
    """Resultado de build_heatmap: mapeia ids de regiões para cores RGB.

    Parameters
    ----------
    colors:
        Mapeamento do id canônico de região para tupla (R, G, B).
    scale_name:
        Nome da escala utilizada ("linear" ou "log").
    value_min:
        Valor mínimo da entrada antes da normalização.
    value_max:
        Valor máximo da entrada antes da normalização.
    lang:
        Idioma para os rótulos ("pt" ou "en").
    title:
        Título opcional para a figura.
    """

    colors: dict[str, tuple[int, int, int]]
    scale_name: str
    value_min: float
    value_max: float
    lang: str
    title: str | None = None
