from __future__ import annotations

from dataclasses import dataclass

from anatomapa.domain.region import Region


@dataclass(frozen=True)
class AnatomicalModel:
    """Collection of Region objects indexed by canonical id."""

    _regions: tuple[Region, ...]

    def regions(self, view: str | None = None) -> tuple[Region, ...]:
        """Return every region, optionally filtered by view."""
        return self._regions

    def get(self, region_id: str) -> Region | None:
        """Return the Region with the given canonical id, or None if absent."""
        for r in self._regions:
            if r.id == region_id:
                return r
        return None

    def ids(self) -> tuple[str, ...]:
        """Return the canonical ids of every region in a stable order."""
        return tuple(r.id for r in self._regions)
