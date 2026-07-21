from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Region:
    """Região anatômica com geometria e metadados."""

    id: str
    label_pt: str
    label_en: str
    aliases: tuple[str, ...]
    bilateral: bool
    parent: str | None
    geometry: dict[str, str]
    area: float | None = None
