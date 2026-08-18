from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Heatmap:
    """Result of build_heatmap: maps region ids to RGB colors.

    Parameters
    ----------
    colors:
        Mapping from the canonical region id to an (R, G, B) tuple.
    scale_name:
        Name of the scale used ("linear" or "log").
    value_min:
        Minimum input value before normalization.
    value_max:
        Maximum input value before normalization.
    lang:
        Language for labels ("pt" or "en").
    title:
        Optional title for the figure.
    """

    colors: dict[str, tuple[int, int, int]]
    scale_name: str
    value_min: float
    value_max: float
    lang: str
    title: str | None = None
