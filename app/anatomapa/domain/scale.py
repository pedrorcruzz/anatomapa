from __future__ import annotations

import math
from typing import Protocol, runtime_checkable


@runtime_checkable
class Scale(Protocol):
    """Protocolo para estratégias de normalização de valores."""

    def normalize(self, values: list[float]) -> list[float]:
        """Normaliza valores para o intervalo [0, 1]."""
        ...


class LinearScale:
    """Normalização linear min-max."""

    def normalize(self, values: list[float]) -> list[float]:
        """Mapeia valores para [0, 1] usando escala min-max.

        Entradas com valores iguais são mapeadas para 0.0.
        """
        if not values:
            return []
        lo = min(values)
        hi = max(values)
        if hi == lo:
            return [0.0] * len(values)
        span = hi - lo
        return [(v - lo) / span for v in values]


class LogScale:
    """Normalização log1p min-max, segura para zeros e negativos."""

    def normalize(self, values: list[float]) -> list[float]:
        """Mapeia valores para [0, 1] usando log1p seguido de escala min-max.

        Valores negativos são deslocados para que o mínimo mapeie para log1p(0).
        """
        if not values:
            return []

        # Desloca para garantir que todos os valores sejam >= 0 antes do log1p
        lo_raw = min(values)
        shift = max(0.0, -lo_raw)
        shifted = [v + shift for v in values]

        logged = [math.log1p(v) for v in shifted]

        lo = min(logged)
        hi = max(logged)
        if hi == lo:
            return [0.0] * len(logged)

        span = hi - lo
        return [(v - lo) / span for v in logged]
