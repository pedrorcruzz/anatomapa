from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Region:
    """Anatomical region with its geometry and metadata."""

    id: str
    label_pt: str
    label_en: str
    bilateral: bool
    parent: str | None
    geometry: dict[str, str]
    area: float | None = None
    # Vistas em que a região tem desenho próprio; vazio = só agregadora (trunk)
    views: tuple[str, ...] = ()
