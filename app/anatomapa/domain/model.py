from __future__ import annotations

from dataclasses import dataclass

from anatomapa.domain.region import Region


@dataclass(frozen=True)
class AnatomicalModel:
    """Coleção de objetos Region indexados pelo id canônico."""

    _regions: tuple[Region, ...]

    def regions(self, view: str | None = None) -> tuple[Region, ...]:
        """Retorna todas as regiões, opcionalmente filtradas por vista."""
        return self._regions

    def get(self, region_id: str) -> Region | None:
        """Retorna a Region pelo id canônico, ou None se não encontrada."""
        for r in self._regions:
            if r.id == region_id:
                return r
        return None

    def ids(self) -> tuple[str, ...]:
        """Retorna os ids canônicos de todas as regiões em ordem estável."""
        return tuple(r.id for r in self._regions)
